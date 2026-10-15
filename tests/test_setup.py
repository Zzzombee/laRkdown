"""Installation tests use synthetic directories, fake help and mock downloads only."""
from pathlib import Path
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import setup_larkdown as setup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('research_runner', ROOT / 'product/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EnvironmentTests(unittest.TestCase):
    def project(self, folder):
        root = (Path(folder) / '科研 project').resolve()
        (root / '.agents/config').mkdir(parents=True)
        (root / '.agents/config/project-layout.json').write_text('{"workspace_kind":"personal-research"}')
        (root / 'run.py').write_text('fixture')
        return root

    def test_core_reuses_python_and_cli_without_pip_download_or_auth(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            native = Path(folder) / 'lark-cli.exe'
            native.write_bytes(b'fixture')
            calls = []
            def invoke(args, **kwargs):
                calls.append(args)
                if '-c' in args:
                    return json.dumps({'executable': sys.executable, 'version': [3, 13, 13]})
                if args[-1] == '--version':
                    return 'lark-cli version 1.0.93'
                return ' '.join(flag for _, flags in setup.CORE for flag in flags)
            with patch.object(setup, 'run', side_effect=invoke), patch.object(setup.shutil, 'which', return_value=str(native)), patch.object(setup, 'download') as download:
                first = setup.prepare(root, Path(folder) / 'cache')
                self.assertTrue(first['ok'])
                self.assertEqual(first['features'], ['core'])
                self.assertFalse(any('auth' in c or 'pip' in c or 'base' in c for c in calls))
                download.assert_not_called()
                calls.clear()
                setup.prepare(root, Path(folder) / 'cache')
                self.assertEqual(len(calls), 1)  # Only interpreter validation; unchanged CLI help is cached.

    def test_cli_compatibility_depends_on_flags_not_version(self):
        def invoke(args, **kwargs):
            if args[-1] == '--version': return 'lark-cli version 1.0.93'
            return ' '.join(f for _, flags in setup.CORE for f in flags)
        with patch.object(setup, 'run', side_effect=invoke):
            self.assertTrue(setup.cli_compatible(['fixture'], 'core'))
            self.assertFalse(setup.cli_compatible(['fixture'], 'base'))

    def test_incompatible_discovered_cli_gets_isolated_fallback(self):
        with patch.object(setup.shutil, 'which', return_value=None), patch.object(setup, 'host', return_value='windows-amd64'), patch.object(setup, 'install_asset', return_value=Path('/private/lark-cli.exe')) as install, patch.object(setup, 'cli_compatible', return_value=True):
            result = setup.choose_cli({}, Path('/cache'), 'base')
        self.assertEqual(result, [str(Path('/private/lark-cli.exe'))])
        self.assertEqual(install.call_count, 1)

    def test_source_checkout_is_rejected_before_download_or_mutation(self):
        with patch.object(setup, 'download') as download:
            for root in (ROOT, ROOT / 'product'):
                with self.assertRaisesRegex(ValueError, 'Development'):
                    setup.prepare(root, ROOT / '.work/unused-cache')
            download.assert_not_called()

    def test_actual_python_standard_library_probe(self):
        result = setup.python_probe(sys.executable)
        self.assertEqual(Path(result['executable']).resolve(), Path(sys.executable).resolve())
        self.assertFalse(setup.python_probe('/missing/python'))

    def test_missing_venv_does_not_block_core_but_pptx_prepares_private_python(self):
        probe = {'executable':sys.executable, 'version':[3,13,13]}
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(setup, 'python_probe', return_value=probe), patch.object(setup, 'run') as invoke, patch.object(setup, 'install_asset') as install:
                self.assertEqual(setup.choose_python({}, Path(folder), None, 'core'), probe)
                invoke.assert_not_called(); install.assert_not_called()
            def invoke(args, **kwargs):
                if '-c' in args: raise RuntimeError('ensurepip missing')
                if 'find' in args: return sys.executable
                return ''
            with patch.object(setup, 'python_probe', return_value=probe), patch.object(setup, 'run', side_effect=invoke) as command, patch.object(setup, 'host', return_value='windows-amd64'), patch.object(setup, 'install_asset', return_value=Path(folder)/'uv.exe'):
                self.assertEqual(setup.choose_python({}, Path(folder), None, 'pptx'), probe)
                install_call = next(c for c in command.call_args_list if 'install' in c.args[0])
                self.assertIn('--no-registry', install_call.args[0])
                self.assertEqual(install_call.kwargs['env']['UV_PYTHON_INSTALL_DIR'], str(Path(folder)/'python'))

    def test_pptx_is_isolated_and_failure_retains_resumable_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            calls = []
            def invoke(args, **kwargs):
                calls.append(args)
                if 'venv' in args:
                    target = Path(args[-1]) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b'fixture')
                if 'pip' in args: raise RuntimeError('simulated interrupted dependency install')
                return ''
            with patch.object(setup, 'run', side_effect=invoke):
                with self.assertRaises(RuntimeError): setup.pptx_environment(root, sys.executable, {})
            pending = json.loads((root / '.work/setup/pptx-pending.json').read_text(encoding='utf-8'))
            environment = Path(pending['directory'])
            self.assertTrue(environment.is_relative_to(root / '.work/setup/environments'))
            with patch.object(setup, 'run', return_value='') as invoke:
                python, _ = setup.pptx_environment(root, sys.executable, {})
                self.assertEqual(Path(python).parent.parent, environment)
                command = invoke.call_args_list[0].args[0]
                self.assertIn('--require-hashes', command)
                self.assertIn('--only-binary=:all:', command)
                self.assertNotIn('venv', command)
            self.assertFalse((root / '.work/setup/pptx-pending.json').exists())
            self.assertTrue(all(c[0] != sys.executable for c in calls if 'pip' in c))

    def test_checksum_failure_never_publishes_download(self):
        with tempfile.TemporaryDirectory() as folder:
            row = {'url': 'https://example.invalid/archive', 'sha256': '0' * 64}
            with patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(b'bad')):
                with self.assertRaisesRegex(ValueError, 'checksum'): setup.download(row, Path(folder))
            self.assertEqual(list((Path(folder) / 'downloads').iterdir()), [])

    def test_archive_paths_are_not_extracted_and_modified_cache_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('../../lark-cli.exe', b'fixture executable')
                package.writestr('../../unknown.txt', b'never extracted')
                package.writestr('LICENSE', b'fixture license')
            row = {'component':'lark-cli', 'version':'1.0.97', 'platform':'windows-amd64', 'sha256':setup.digest(archive.read_bytes()), 'url':'https://example.invalid/native.zip'}
            cache = Path(folder) / 'cache'
            with patch.object(setup, 'download', return_value=archive):
                executable = setup.install_asset(row, cache)
                self.assertEqual(executable.read_bytes(), b'fixture executable')
                self.assertEqual((executable.parent / 'LICENSE').read_bytes(), b'fixture license')
                self.assertFalse((cache / 'unknown.txt').exists())
                executable.write_bytes(b'user modified')
                with self.assertRaisesRegex(ValueError, 'changed'): setup.install_asset(row, cache)
                self.assertEqual(executable.read_bytes(), b'user modified')

    def test_runner_selects_own_environment_and_passes_cli_without_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            native = Path(folder) / 'cli with spaces.exe'
            native.write_bytes(b'fixture')
            state = {'schema_version':1,'python':sys.executable,'cli':[str(native)],'features':['core']}
            setup.save(root / setup.STATE, state)
            script = root / '.agents/skills' / runner.SCRIPTS['feishu']
            script.parent.mkdir(parents=True)
            script.write_text('fixture')
            command, env = runner.invocation('feishu', ['--root', str(root), 'preflight'], root)
            self.assertEqual(command[0], sys.executable)
            self.assertEqual(json.loads(env['LARKDOWN_CLI']), [str(native)])
            with self.assertRaisesRegex(ValueError, 'PPTX'): runner.invocation('pptx-extract', [], root)
            with self.assertRaisesRegex(ValueError, 'base feature'): runner.invocation('base', [], root)
            with self.assertRaisesRegex(ValueError, 'Unknown'): runner.invocation('../../outside', [], root)

    def test_real_runner_keeps_arguments_literal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            native = Path(folder) / 'fake-cli'
            native.write_bytes(b'fixture')
            (root / 'run.py').write_bytes((ROOT / 'product/run.py').read_bytes())
            setup.save(root / setup.STATE, {'schema_version':1,'python':sys.executable,'cli':[str(native)],'features':['core']})
            script = root / '.agents/skills' / runner.SCRIPTS['feishu']
            script.parent.mkdir(parents=True)
            script.write_text('import json,sys; print(json.dumps(sys.argv[1:]))')
            value = 'literal ; & $() 中文'
            proc = subprocess.run([sys.executable, str(root / 'run.py'), 'feishu', value], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), [value])

    def test_native_npm_binary_does_not_require_node(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            shim = path / 'lark-cli.cmd'
            shim.write_bytes(b'fixture')
            native = path / 'node_modules/@larksuite/cli/bin/lark-cli.exe'
            native.parent.mkdir(parents=True)
            native.write_bytes(b'fixture')
            with patch.object(setup.shutil, 'which', return_value=None):
                self.assertEqual(setup.cli_command(shim), [str(native)])

    def test_selected_cli_change_invalidates_cached_capabilities(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            native = Path(folder) / 'cli.exe'
            native.write_bytes(b'fixture')
            old = {'schema_version':1, 'python':sys.executable, 'cli':[str(native)], 'cli_fingerprint':setup.fingerprint([str(native)]), 'features':['core','base']}
            setup.save(root / setup.STATE, old)
            native.write_bytes(b'changed fixture')
            with patch.object(setup, 'cli_compatible', return_value=True) as compatible, patch.object(setup.shutil, 'which', return_value=None):
                result = setup.prepare(root, Path(folder) / 'cache')
            self.assertEqual(result['features'], ['core'])
            compatible.assert_called_once()

    def test_download_refuses_linked_subdirectory(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / 'cache'
            target = Path(folder) / 'private'
            cache.mkdir(); target.mkdir()
            try: (cache / 'downloads').symlink_to(target, target_is_directory=True)
            except OSError: self.skipTest('Symlink creation is unavailable')
            with patch.object(setup.urllib.request, 'urlopen') as fetch:
                with self.assertRaisesRegex(ValueError, 'Linked'):
                    setup.download({'url':'https://example.invalid/x','sha256':'0'*64}, cache)
                fetch.assert_not_called()
            self.assertEqual(list(target.iterdir()), [])

    def test_invalid_settings_are_preserved_without_installing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            path = root / setup.STATE
            path.write_text('["unrecognized state"]')
            before = path.read_bytes()
            with patch.object(setup, 'download') as download:
                with self.assertRaisesRegex(ValueError, 'Unknown runtime'):
                    setup.prepare(root, Path(folder)/'cache')
                download.assert_not_called()
            self.assertEqual(path.read_bytes(), before)

    @unittest.skipUnless(os.name == 'nt', 'Windows bootstrap')
    def test_powershell_entry_reuses_explicit_python_and_forwards_paths(self):
        powershell = shutil.which('powershell')
        if not powershell: self.skipTest('Windows PowerShell unavailable')
        with tempfile.TemporaryDirectory() as folder:
            root = self.project(folder)
            maintenance = Path(folder) / 'maintenance'
            maintenance.mkdir()
            (maintenance / 'bootstrap.ps1').write_bytes((ROOT / 'tools/bootstrap.ps1').read_bytes())
            (maintenance / 'setup_larkdown.py').write_text('import json,sys; print(json.dumps(sys.argv[1:]))')
            proc = subprocess.run([powershell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(maintenance / 'bootstrap.ps1'), '-Project', str(root), '-Python', sys.executable, '-Feature', 'base', '-Cache', str(Path(folder) / 'cache')], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            args = json.loads(proc.stdout)
            self.assertEqual(args[args.index('--project')+1], str(root))
            self.assertEqual(args[args.index('--feature')+1], 'base')
            self.assertEqual(Path(args[args.index('--python')+1]).resolve(), Path(sys.executable).resolve())


if __name__ == '__main__':
    unittest.main()
