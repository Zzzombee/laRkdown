"""Check the separation between the user package and repository resources."""
from __future__ import annotations

import unittest

from tools import build_release


class PackageBoundaryTests(unittest.TestCase):
    def test_package_selects_runtime_files_only(self):
        required = {name: b'fixture' for name in build_release.PACKAGE_EXACT}
        candidates = {
            **required,
            '.agents/instructions/project-layout.md': b'runtime instruction',
            '.agents/skills/upgrade-larkdown/SKILL.md': b'runtime skill',
            '.agents/config/project-layout.json': b'runtime schema',
            '.agents/config/feishu.example.json': b'public example',
            '.agents/config/feishu.json': b'private configuration',
            '.agents/config/publisher-notes.md': b'publisher notes',
            '.github/workflows/release-contract.yml': b'publisher workflow',
            '.gitignore': b'git configuration',
            'tools/build_release.py': b'build script',
            'tools/RELEASING.md': b'publisher specification',
            'USER_GUIDE.md': b'reader guide',
            'tests/test_release.py': b'test code',
            '.planning/plan.md': b'private plan',
        }
        selected = build_release.package_files(candidates)
        self.assertEqual(set(selected), set(required) | {
            '.agents/instructions/project-layout.md',
            '.agents/skills/upgrade-larkdown/SKILL.md',
            '.agents/config/project-layout.json',
            '.agents/config/feishu.example.json',
        })

    def test_package_requires_user_entrypoints(self):
        with self.assertRaisesRegex(ValueError, 'missing required files'):
            build_release.package_files({'README.md': b'fixture'})


    def test_package_requires_version_notes(self):
        files = {name: b'fixture' for name in build_release.PACKAGE_EXACT
                 if name != build_release.VERSION_NOTES}
        with self.assertRaisesRegex(ValueError, 'version-notes.md'):
            build_release.package_files(files)

    def test_repository_guide_is_not_packaged_or_upgrade_managed(self):
        self.assertFalse(build_release.managed('USER_GUIDE.md'))
        files = {name: b'fixture' for name in build_release.PACKAGE_EXACT}
        files['USER_GUIDE.md'] = b'repository guide'
        self.assertNotIn('USER_GUIDE.md', build_release.package_files(files))


class UserGuideReleaseTests(unittest.TestCase):
    def guide(self):
        return ('# laRkdown 使用指南（v1.2.3）\n\n'
                '[发布页](https://github.com/Zzzombee/laRkdown/releases/tag/v1.2.3)\n'
                '[下载](https://github.com/Zzzombee/laRkdown/releases/download/v1.2.3/laRkdown-v1.2.3.zip)\n'
                '上游 [maRkdown v0.1.0](https://github.com/Zzzombee/maRkdown/releases/tag/v0.1.0)\n')

    def check_guide(self, text, version='1.2.3'):
        build_release.check_user_guide({'USER_GUIDE.md': text.encode('utf-8')}, version)

    def test_matching_guide_preserves_independent_upstream_version(self):
        self.check_guide(self.guide())

    def test_release_version_bump_requires_guide_update(self):
        with self.assertRaisesRegex(ValueError, 'title is stale'):
            self.check_guide(self.guide(), version='1.2.4')

    def test_missing_guide_or_download_link_blocks_release(self):
        with self.assertRaisesRegex(ValueError, 'USER_GUIDE.md'):
            build_release.check_user_guide({}, '1.2.3')
        with self.assertRaisesRegex(ValueError, 'download link'):
            self.check_guide(self.guide().replace('/download/', '/old-download/'))

    def test_stale_extra_links_or_archive_names_block_release(self):
        for stale in ('https://github.com/Zzzombee/laRkdown/releases/tag/v1.2.2',
                      'https://github.com/Zzzombee/laRkdown/releases/download/v1.2.2/laRkdown-v1.2.2.zip',
                      'laRkdown-v1.2.2.zip'):
            with self.subTest(stale=stale), self.assertRaisesRegex(ValueError, 'stale'):
                self.check_guide(self.guide() + stale)


class VersionNotesReleaseTests(unittest.TestCase):
    def test_matching_version_notes_are_accepted(self):
        notes = '# laRkdown 版本说明（v1.2.3）\n\n相较上一版的实际变化。\n'
        build_release.check_version_notes({build_release.VERSION_NOTES: notes.encode('utf-8')}, '1.2.3')

    def test_missing_stale_or_empty_version_notes_block_release(self):
        cases = [({}, 'Stage version-notes.md'),
                 ({build_release.VERSION_NOTES: '# laRkdown 版本说明（v1.2.2）\n旧版内容'.encode('utf-8')}, 'stale'),
                 ({build_release.VERSION_NOTES: '# laRkdown 版本说明（v1.2.3）\n\n'.encode('utf-8')}, 'no release explanation')]
        for files, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                build_release.check_version_notes(files, '1.2.3')


if __name__ == '__main__':
    unittest.main()
