"""Verify source, content and artifact boundaries between research and maintenance."""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import build_release as build
from tools import upgrade_larkdown as up


class LegacyArchiveTests(unittest.TestCase):
    def test_bootstrap_readme_baseline_is_independent_of_git_autocrlf(self):
        pinned = json.loads((build.ROOT / build.LEGACY_SOURCE).read_bytes())['releases']
        def minimal_committed(tag):
            return {'README.md': build.git('show', f'{tag}:README.md')}
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.autocrlf',
                                     'GIT_CONFIG_VALUE_0': 'false'}):
            with patch.object(build, 'historical_tags', return_value=build.BOOTSTRAP_TAGS), \
                 patch.object(build, 'committed_files', side_effect=minimal_committed):
                catalog = build.previous_releases()['releases']
        for tag in build.BOOTSTRAP_TAGS:
            with self.subTest(tag=tag):
                self.assertEqual(up.sha(up.encoded(catalog[tag[1:]])), up.sha(up.encoded(pinned[tag[1:]])))

    def test_bootstrap_tree_matches_published_windows_bytes_under_lf_settings(self):
        pinned = json.loads((build.ROOT / build.LEGACY_SOURCE).read_bytes())['releases']
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.autocrlf',
                                     'GIT_CONFIG_VALUE_0': 'false'}):
            with patch.object(build, 'committed_files', return_value={}):
                for tag in build.BOOTSTRAP_TAGS:
                    files = build.tree(tag)
                    actual = {name: up.sha(blob) for name, blob in files.items()}
                    with self.subTest(tag=tag):
                        self.assertEqual(up.sha(up.encoded(actual)),
                                         up.sha(up.encoded(pinned[tag[1:]]['managed_files'])))


class PackageBoundaryTests(unittest.TestCase):
    def sources(self):
        return build.working_files()

    def test_product_mapping_uses_user_agents_and_excludes_development(self):
        files = self.sources()
        selected = build.package_files(files)
        self.assertEqual(selected['AGENTS.md'], files['product/AGENTS.md'])
        self.assertNotEqual(selected['AGENTS.md'], files['AGENTS.md'])
        self.assertTrue(build.PACKAGE_EXACT <= selected.keys())
        for name in ('USER_GUIDE.md', 'upgrade_larkdown.py', 'UPGRADING.md', up.OLD_MANIFEST,
                     '.agents/config/upstream.json', '.agents/instructions/version-notes.md'):
            self.assertNotIn(name, selected)
        self.assertEqual({Path(n).parts[2] for n in selected if n.startswith('.agents/skills/')}, up.RESEARCH_SKILLS)

    def test_product_requires_each_research_entrypoint(self):
        for name in build.PACKAGE_EXACT:
            files = self.sources()
            del files['product/' + name]
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'missing required'):
                build.package_files(files)

    def test_unknown_maintenance_and_private_paths_in_product_are_rejected(self):
        for name in ('upgrade_larkdown.py', 'UPGRADING.md', '.agents/config/upstream.json',
                     '.agents/instructions/version-notes.md', '.agents/skills/upgrade-larkdown/SKILL.md',
                     '.agents/config/feishu-documents.json', 'tools/publisher.py'):
            files = self.sources()
            files['product/' + name] = b'leaked file'
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unexpected file'):
                build.package_files(files)

    def test_content_leaks_are_rejected_inside_legal_paths(self):
        for name in ('AGENTS.md', 'README.md', '.agents/instructions/project-layout.md',
                     '.agents/skills/maintain-research-state/SKILL.md'):
            files = self.sources()
            files['product/' + name] += b'\npython upgrade_larkdown.py --apply\n'
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'leaked'):
                build.check_boundaries(files)

    def test_development_skill_discovery_or_routing_is_rejected(self):
        files = self.sources()
        files['.agents/skills/example/SKILL.md'] = b'root skill'
        with self.assertRaisesRegex(ValueError, 'discovery'):
            build.check_boundaries(files)
        files = self.sources()
        files['AGENTS.md'] += b'\nRead .agents/skills/maintain-research-state/SKILL.md\n'
        with self.assertRaisesRegex(ValueError, 'routing'):
            build.check_boundaries(files)

    def test_receipt_hashes_use_research_agents_only(self):
        files = self.sources()
        manifest = build.desired_manifest(files)
        self.assertEqual(manifest['managed_files']['AGENTS.md'], up.sha(files['product/AGENTS.md']))
        self.assertNotEqual(manifest['managed_files']['AGENTS.md'], up.sha(files['AGENTS.md']))
        files['AGENTS.md'] += b'\nLocal development rule.\n'
        self.assertEqual(build.desired_manifest(files), manifest)

    def test_single_archive_has_disjoint_siblings_and_supports_one_step_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'research.zip'
            result = build.build(output, preview=True)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                expected = {'laRkdown/' + n for n in build.package_files(self.sources())}
                expected |= {'maintenance/' + n[len('tools/'):] for n in build.MAINTENANCE_SOURCES}
                self.assertEqual(names, expected)
                self.assertEqual(archive.read('laRkdown/AGENTS.md'), self.sources()['product/AGENTS.md'])
                maintenance = {n for n in names if n.startswith('maintenance/')}
                self.assertFalse(any('AGENTS.md' in n or '/.agents/' in n for n in maintenance))
                archive.extractall(Path(directory) / 'installed')
            self.assertEqual(result['bundle']['asset'], str(output))
            self.assertEqual(list(Path(directory).glob('*.zip')), [output])
            tool = Path(directory) / 'installed/maintenance/upgrade_larkdown.py'
            user = Path(directory) / 'installed/laRkdown'
            process = subprocess.run([sys.executable, str(tool), '--project', str(user), '--apply'], capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr.decode('utf-8', errors='replace'))
            self.assertLess(len(process.stdout), 400)
            self.assertNotIn('operations', json.loads(process.stdout))
            self.assertTrue((user / up.MANIFEST).is_file())
            self.assertFalse((user / 'upgrade_larkdown.py').exists())
            self.assertFalse((user / '.agents/config/upstream.json').exists())

    def test_release_build_requires_clean_commit(self):
        with patch.object(build, 'git', return_value=b' M AGENTS.md'):
            with self.assertRaisesRegex(ValueError, 'Commit'):
                build.build(Path('unused.zip'))


class UserGuideReleaseTests(unittest.TestCase):
    def guide(self):
        return ('# laRkdown 使用指南（v1.2.3）\n\n'
                '[发布页](https://github.com/Zzzombee/laRkdown/releases/tag/v1.2.3)\n'
                '[下载](https://github.com/Zzzombee/laRkdown/releases/download/v1.2.3/laRkdown-v1.2.3.zip)\n'
                '上游仍为 maRkdown v0.1.0。\n')

    def test_matching_guide_preserves_independent_upstream_version(self):
        build.check_user_guide({'USER_GUIDE.md': self.guide().encode()}, '1.2.3')

    def test_missing_or_stale_guide_and_links_block_release(self):
        for guide in ('', self.guide().replace('/download/', '/old-download/'),
                      self.guide() + 'laRkdown-maintenance-v1.2.2.zip'):
            with self.subTest(guide=guide), self.assertRaises(ValueError):
                build.check_user_guide({'USER_GUIDE.md': guide.encode()}, '1.2.3')
        with self.assertRaisesRegex(ValueError, 'USER_GUIDE'):
            build.check_user_guide({}, '1.2.3')


class VersionNotesReleaseTests(unittest.TestCase):
    def test_matching_maintenance_notes_are_accepted(self):
        build.check_version_notes({build.VERSION_NOTES: '# laRkdown 版本说明（v1.2.3）\n实际变化。'.encode()}, '1.2.3')

    def test_missing_stale_or_empty_notes_block_release(self):
        for notes in (None, '# laRkdown 版本说明（v1.2.2）\n旧版内容', '# laRkdown 版本说明（v1.2.3）\n\n'):
            files = {} if notes is None else {build.VERSION_NOTES: notes.encode()}
            with self.subTest(notes=notes), self.assertRaises(ValueError):
                build.check_version_notes(files, '1.2.3')


if __name__ == '__main__':
    unittest.main()
