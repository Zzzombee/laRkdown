"""Behavioral upgrade checks using synthetic user projects and a real package manifest."""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import upgrade_larkdown as up
from tools import build_release


def package(archive: Path, overrides=None):
    sources = build_release.working_files()
    files = build_release.package_files(sources)
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name, blob in files.items():
            if overrides and name in overrides:
                blob = overrides[name]
            output.writestr('laRkdown/' + name, blob)
        for name in build_release.MAINTENANCE_SOURCES:
            output.writestr('maintenance/' + name[len('tools/'):], sources[name])
    return up.Release(archive)


def project(directory: Path, release, version='0.1.0', customized=False):
    old_agents = b'# Synthetic old laRkdown rules\n'
    old_upstream = up.encoded({'version': version, 'project': 'laRkdown'})
    (directory / '.agents/config').mkdir(parents=True)
    (directory / 'AGENTS.md').write_bytes(old_agents + (b'User custom rule\n' if customized else b''))
    (directory / '.agents/config/upstream.json').write_bytes(old_upstream)
    release.legacy['releases'][version] = {'project_schema_version': 1, 'managed_files': {
        'AGENTS.md': up.sha(old_agents), '.agents/config/upstream.json': up.sha(old_upstream)},
        'merge_base': {'AGENTS.md': old_agents.decode('utf-8')}}
    private = {
        '.agents/config/feishu-documents.json': b'{"documents":{"CURRENT_STATE":{"document_id":"fixture"}}}',
        '.agents/config/research-base.local.json': b'{"base_token":"private-fixture","project_id":"owner"}',
        '.work/research-base/state.json': b'{"tables":{"fixture":{}}}',
        'sources/presentations/experiment.pptx': b'fixture raw bytes',
        'outputs/reports/previous.json': b'{"status":"user result"}',
    }
    for name, blob in private.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    return private


class UpgradeTests(unittest.TestCase):
    def test_default_summary_is_bounded_and_hides_file_operations(self):
        result = {'ok': True, 'from_version': '0.2.5', 'to_version': '0.2.6',
                  'operations': [{'path': f'file-{i}', 'action': 'update'} for i in range(1000)], 'conflicts': []}
        summary = up.compact_result(result)
        self.assertEqual(summary['changes'], 1000)
        self.assertNotIn('operations', summary)
        self.assertLess(len(json.dumps(summary)), 150)
        result['ok'] = False
        result['conflicts'] = [{'path': f'file-{i}', 'reason': 'modified'} for i in range(20)]
        summary = up.compact_result(result)
        self.assertEqual(summary['conflict_count'], 20)
        self.assertEqual(len(summary['conflicts']), 5)

    def test_authorized_apply_computes_plan_once_without_a_separate_preview(self):
        release, user, _ = self.fixture()
        real_plan = up.make_plan
        with patch.object(up, 'Release', return_value=release), patch.object(up, 'make_plan', wraps=real_plan) as planning:
            with patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(up.main(['--project', str(user), '--package', str(release.archive), '--apply']), 0)
            self.assertEqual(planning.call_count, 1)
            summary = json.loads(output.getvalue())
            self.assertTrue(summary['ok'])
            self.assertNotIn('operations', summary)
            self.assertNotIn('plan', summary)
            report = json.loads((user / summary['report']).read_bytes())
            self.assertTrue(report['plan']['operations'])

    def test_cli_conflict_returns_only_bounded_actionable_details(self):
        release, user, _ = self.fixture()
        (user / 'AGENTS.md').write_bytes(b'User rewrote this file')
        with patch.object(up, 'Release', return_value=release), patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(up.main(['--project', str(user), '--package', str(release.archive), '--apply']), 2)
        summary = json.loads(output.getvalue())
        self.assertEqual(summary['conflict_count'], 1)
        self.assertNotIn('operations', summary)
        self.assertEqual((user / 'AGENTS.md').read_bytes(), b'User rewrote this file')

    def test_optional_verbose_preview_keeps_full_plan_without_applying(self):
        release, user, _ = self.fixture()
        with patch.object(up, 'Release', return_value=release), patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(up.main(['--project', str(user), '--package', str(release.archive), '--verbose']), 0)
        self.assertTrue(json.loads(output.getvalue())['plan']['operations'])
        self.assertFalse((user / up.MANIFEST).exists())

    def test_fresh_isolated_install_is_identified_without_product_version_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = package(root / 'research.zip')
            user = root / 'personal-research'
            for name, blob in release.files.items():
                if name == up.MANIFEST:
                    continue
                path = user / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(blob)
            plan = up.make_plan(user, release)
            self.assertEqual(plan['from_version'], release.manifest['version'])
            self.assertFalse(plan['conflicts'])
            self.assertEqual([op['path'] for op in plan['operations']], [up.MANIFEST])
            self.assertTrue(up.apply_plan(user, release, plan)['ok'])
            self.assertEqual(up.make_plan(user, release)['operations'], [])
            self.assertFalse((user / up.OLD_MANIFEST).exists())
            self.assertFalse((user / '.agents/config/upstream.json').exists())

    def test_unrecognized_install_fingerprint_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = package(root / 'research.zip')
            user = root / 'unknown-project'
            user.mkdir()
            (user / 'AGENTS.md').write_text('Unknown local instructions', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                up.make_plan(user, release)
            self.assertFalse((user / '.work').exists())

    def test_modified_retired_maintenance_file_blocks_cleanup(self):
        release, user, _ = self.fixture()
        old = b'Published old upgrade script'
        entry = release.legacy['releases']['0.1.0']
        entry['managed_files']['upgrade_larkdown.py'] = up.sha(old)
        (user / 'upgrade_larkdown.py').write_bytes(old + b'\nHuman modification')
        plan = up.make_plan(user, release)
        self.assertIn('upgrade_larkdown.py', [c['path'] for c in plan['conflicts']])
        with self.assertRaises(ValueError):
            up.apply_plan(user, release, plan)
        self.assertIn(b'Human modification', (user / 'upgrade_larkdown.py').read_bytes())

    def test_development_repository_and_product_source_are_not_upgrade_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = package(root / 'research.zip')
            for target in (ROOT, ROOT / 'product'):
                with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'development source'):
                    up.make_plan(target, release)

    def fixture(self, version='0.1.0', customized=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        release = package(root / 'release.zip')
        user = root / 'my-research-project'
        user.mkdir()
        private = project(user, release, version, customized)
        return release, user, private

    def test_v01_existing_project_upgrades_in_place_and_preserves_data(self):
        release, user, private = self.fixture()
        before = {name: up.sha((user / name).read_bytes()) for name in private}
        plan = up.make_plan(user, release)
        self.assertFalse(plan['conflicts'])
        self.assertEqual(plan['from_version'], '0.1.0')
        self.assertEqual(up.existing_hash(user / up.MANIFEST), None)
        self.assertTrue(up.apply_plan(user, release, plan)['ok'])
        self.assertEqual(json.loads((user / up.MANIFEST).read_text(encoding='utf-8'))['version'], release.manifest['version'])
        self.assertFalse((user / '.agents/skills/upgrade-larkdown/SKILL.md').exists())
        self.assertFalse((user / 'upgrade_larkdown.py').exists())
        self.assertFalse((user / '.agents/instructions/version-notes.md').exists())
        self.assertFalse((user / '.agents/config/upstream.json').exists())
        self.assertFalse((user / 'USER_GUIDE.md').exists())
        self.assertEqual(before, {name: up.sha((user / name).read_bytes()) for name in private})
        self.assertEqual(up.make_plan(user, release)['operations'], [])

    def test_v02_nonoverlapping_custom_rule_is_merged(self):
        release, user, private = self.fixture('0.2.0', customized=True)
        old_agents = b'# Synthetic old laRkdown rules\n'
        incoming = old_agents + b'\n## New release rule\nUse the new skill.\n'
        release.files['AGENTS.md'] = incoming
        release.manifest['managed_files']['AGENTS.md'] = up.sha(incoming)
        release.files[up.MANIFEST] = up.encoded(release.manifest)
        before = {name: up.sha((user / name).read_bytes()) for name in private}
        plan = up.make_plan(user, release)
        self.assertFalse(plan['conflicts'])
        self.assertEqual([x['action'] for x in plan['operations'] if x['path'] == 'AGENTS.md'], ['merge'])
        self.assertTrue(up.apply_plan(user, release, plan)['ok'])
        self.assertIn(b'New release rule', (user / 'AGENTS.md').read_bytes())
        self.assertIn(b'User custom rule', (user / 'AGENTS.md').read_bytes())
        self.assertFalse(up.pending_path(user).exists())
        self.assertEqual(up.make_plan(user, release)['operations'], [])
        self.assertEqual(before, {name: up.sha((user / name).read_bytes()) for name in private})

    def test_overlapping_custom_rule_blocks_every_write(self):
        release, user, _ = self.fixture('0.2.0')
        (user / 'AGENTS.md').write_bytes(b'# My changed rules\n')
        self.assertIn('AGENTS.md', [c['path'] for c in up.make_plan(user, release)['conflicts']])
        self.assertFalse((user / up.MANIFEST).exists())

    def test_unrelated_local_upgrade_script_is_preserved(self):
        release, user, _ = self.fixture()
        (user / 'upgrade_larkdown.py').write_text('my own unrelated script', encoding='utf-8')
        plan = up.make_plan(user, release)
        self.assertNotIn('upgrade_larkdown.py', [x['path'] for x in plan['operations']])
        self.assertTrue(up.apply_plan(user, release, plan)['ok'])
        self.assertEqual((user / 'upgrade_larkdown.py').read_text(), 'my own unrelated script')

    def test_local_user_guide_is_preserved_outside_upgrade_management(self):
        release, user, _ = self.fixture()
        custom_guide = b'My research project guide\n'
        (user / 'USER_GUIDE.md').write_bytes(custom_guide)
        plan = up.make_plan(user, release)
        self.assertFalse(plan['conflicts'])
        self.assertNotIn('USER_GUIDE.md', [x['path'] for x in plan['operations']])
        self.assertTrue(up.apply_plan(user, release, plan)['ok'])
        self.assertEqual((user / 'USER_GUIDE.md').read_bytes(), custom_guide)

    def test_controlled_failure_restores_package_files(self):
        release, user, _ = self.fixture()
        plan = up.make_plan(user, release)
        original = up.write_atomic
        calls = 0
        def fail_second(path, blob):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('synthetic disk failure')
            return original(path, blob)
        with patch.object(up, 'write_atomic', side_effect=fail_second):
            with self.assertRaises(RuntimeError): up.apply_plan(user, release, plan)
        self.assertEqual((user / 'AGENTS.md').read_bytes(), b'# Synthetic old laRkdown rules\n')
        self.assertFalse(up.pending_path(user).exists())
        self.assertEqual(up.make_plan(user, release)['from_version'], '0.1.0')

    def test_interrupted_upgrade_recovery_never_reinitializes_project(self):
        release, user, private = self.fixture()
        plan = up.make_plan(user, release)
        original = up.write_atomic
        calls = 0
        def interrupt(path, blob):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt('synthetic process interruption')
            return original(path, blob)
        with patch.object(up, 'write_atomic', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): up.apply_plan(user, release, plan)
        self.assertTrue(up.pending_path(user).exists())
        recovered = up.recover(user)
        self.assertTrue(recovered['rolled_back'])
        self.assertFalse(up.pending_path(user).exists())
        self.assertEqual((user / '.agents/config/feishu-documents.json').read_bytes(), private['.agents/config/feishu-documents.json'])

    def test_changed_file_after_interruption_prevents_rollback(self):
        release, user, _ = self.fixture()
        plan = up.make_plan(user, release)
        original = up.write_atomic
        calls = 0
        def interrupt(path, blob):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return original(path, blob)
        with patch.object(up, 'write_atomic', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): up.apply_plan(user, release, plan)
        first = plan['operations'][0]['path']
        (user / first).write_text('human wrote here after interruption', encoding='utf-8')
        with self.assertRaises(ValueError): up.recover(user)
        self.assertTrue(up.pending_path(user).exists())

    def test_release_payload_or_traversal_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError): package(root / 'tampered.zip', {'AGENTS.md': b'changed'})
            with zipfile.ZipFile(root / 'traversal.zip', 'w') as output:
                output.writestr('laRkdown/../outside.txt', 'bad')
            with self.assertRaises(ValueError): up.Release(root / 'traversal.zip')

    def test_latest_download_uses_checksum_asset_when_api_is_rate_limited(self):
        archive = b'synthetic release bytes'
        tag = 'v0.2.3'
        asset = f'laRkdown-{tag}.zip'
        base = f'https://github.com/{up.REPOSITORY}/releases/download/{tag}/{asset}'

        class Response(io.BytesIO):
            def __init__(self, content, url=''):
                super().__init__(content)
                self.url = url
            def geturl(self):
                return self.url

        def open_url(request, timeout):
            url = request.full_url
            if url.startswith('https://api.github.com/'):
                raise urllib.error.HTTPError(url, 403, 'rate limit', {}, None)
            if url.endswith('/releases/latest'):
                return Response(b'', f'https://github.com/{up.REPOSITORY}/releases/tag/{tag}')
            if url == base + '.sha256':
                return Response(f'{hashlib.sha256(archive).hexdigest()}  {asset}\n'.encode('ascii'))
            if url == base:
                return Response(archive)
            raise AssertionError(url)

        with tempfile.TemporaryDirectory() as directory, patch.object(up.urllib.request, 'urlopen', side_effect=open_url):
            destination = Path(directory) / 'release.zip'
            self.assertEqual(up.fetch_latest(destination), destination)
            self.assertEqual(destination.read_bytes(), archive)

    def test_unsupported_project_schema_or_version_is_rejected(self):
        release, user, _ = self.fixture()
        altered = copy.deepcopy(release)
        altered.manifest['project_schema_version'] = 2
        with self.assertRaises(ValueError): up.make_plan(user, altered)
        altered = copy.deepcopy(release)
        altered.manifest['supported_from'] = ['0.2.0']
        with self.assertRaises(ValueError): up.make_plan(user, altered)

    def test_published_projects_upgrade_without_reinitialization(self):
        release, _, _ = self.fixture()
        release = up.Release(release.archive)
        for version in release.manifest['supported_from']:
            result = subprocess.run(['git', '-c', 'core.autocrlf=false', 'archive', '--format=zip', 'v' + version], cwd=ROOT,
                                    capture_output=True)
            if result.returncode:
                self.skipTest('Published Git tags are unavailable in a downloaded source ZIP')
            with tempfile.TemporaryDirectory() as directory, zipfile.ZipFile(io.BytesIO(result.stdout)) as archive:
                root = Path(directory)
                for name in archive.namelist():
                    if name in {'AGENTS.md', 'README.md', 'requirements.txt', 'UPGRADING.md', 'upgrade_larkdown.py'} or name.startswith('.agents/'):
                        path = root / name
                        if name.endswith('/'):
                            path.mkdir(parents=True, exist_ok=True)
                        else:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            blob = archive.read(name)
                            entry = release.legacy['releases'][version]
                            wanted = entry['managed_files'].get(name, entry.get('unmanaged_files', {}).get(name))
                            if wanted and up.sha(blob) != wanted:
                                windows_blob = blob.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                                if up.sha(windows_blob) == wanted:
                                    blob = windows_blob
                            path.write_bytes(blob)
                candidate = up.Release(release.archive)
                if version != '0.1.0':
                    with (root / 'AGENTS.md').open('ab') as stream:
                        stream.write(b'\n## Colleague-specific research rules\nKeep my local instructions.\n')
                plan = up.make_plan(root, candidate)
                self.assertFalse(plan['conflicts'], f'{version}: {plan["conflicts"]}')
                self.assertEqual(plan['from_version'], version)
                private = root / '.agents/config/feishu-documents.json'
                private.write_bytes(b'{"documents":{"CURRENT_STATE":{"document_id":"real-project-fixture"}}}')
                source = root / 'sources/presentations/raw.pptx'
                source.parent.mkdir(parents=True)
                source.write_bytes(b'keep raw presentation')
                self.assertTrue(up.apply_plan(root, candidate, plan)['ok'])
                self.assertEqual(json.loads((root / up.MANIFEST).read_text(encoding='utf-8'))['version'], release.manifest['version'])
                self.assertIn(b'real-project-fixture', private.read_bytes())
                self.assertEqual(source.read_bytes(), b'keep raw presentation')
                if version != '0.1.0':
                    self.assertIn(b'Keep my local instructions.', (root / 'AGENTS.md').read_bytes())


if __name__ == '__main__':
    unittest.main()
