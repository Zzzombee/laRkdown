"""Run a research script with the locally selected Python and CLI; no installation."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RECEIPT = '.agents/config/runtime.local.json'
SCRIPTS = {
    'feishu': 'maintain-research-state/scripts/feishu_bridge.py',
    'initialize': 'maintain-research-state/scripts/initialize_project.py',
    'validate-state': 'maintain-research-state/scripts/validate_state.py',
    'base': 'research-docs-to-base/scripts/research_base.py',
    'pptx-check': 'pptx-to-research-state/scripts/preflight.py',
    'pptx-extract': 'pptx-to-research-state/scripts/extract_pptx.py',
    'pptx-media': 'pptx-to-research-state/scripts/prepare_media_preview.py',
    'pptx-sheets': 'pptx-to-research-state/scripts/make_contact_sheet.py',
    'pptx-validate': 'pptx-to-research-state/scripts/validate_extraction.py',
}


def settings(root=ROOT):
    path = root / RECEIPT
    if path.is_symlink():
        raise ValueError('Runtime settings must be a regular local file')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('cli'), list):
        raise ValueError('Invalid runtime settings; repeat environment preparation')
    for entry in [data.get('python'), *data['cli']]:
        if not isinstance(entry, str) or not Path(entry).is_absolute() or not Path(entry).is_file():
            raise ValueError('Selected runtime changed; repeat environment preparation')
    if not data['cli']:
        raise ValueError('No selected CLI')
    if Path(data['cli'][0]).suffix.lower() in {'.cmd', '.bat', '.ps1'}:
        raise ValueError('Prepare a native CLI or explicit Node runner; shell shims are unsupported')
    for key in ('python_fingerprint', 'cli_fingerprint'):
        for item in data.get(key, []):
            path = Path(item['path'])
            if path.stat().st_size != item['size'] or path.stat().st_mtime_ns != item['mtime_ns']:
                raise ValueError('Selected runtime changed; repeat environment preparation')
    return data


def invocation(name, arguments, root=ROOT):
    for candidate in (root, root.parent if root.name == 'product' else root):
        if (candidate / 'tools/build_release.py').is_file() and (candidate / 'product').is_dir():
            raise ValueError('Development source is not a research workspace')
    if name not in SCRIPTS and name != 'cli':
        raise ValueError('Unknown research command: ' + name)
    data = settings(root)
    env = dict(os.environ, LARKDOWN_CLI=json.dumps(data['cli']), PYTHONUTF8='1',
               LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1')
    if name == 'cli':
        return data['cli'] + arguments, env
    interpreter = data['python']
    if name.startswith('pptx-'):
        interpreter = data.get('pptx_python')
        if not interpreter or not Path(interpreter).is_file():
            raise ValueError('PPTX environment is not ready; prepare the pptx feature first')
    if name == 'base' and 'base' not in data.get('features', []):
        raise ValueError('Prepare the base feature before using the Base script')
    script = (root / '.agents/skills' / SCRIPTS[name]).resolve()
    if not script.is_relative_to(root.resolve()) or not script.is_file():
        raise ValueError('Research script is missing or outside this project')
    return [interpreter, str(script), *arguments], env


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv == ['--help']:
        print('python run.py <cli|' + '|'.join(SCRIPTS) + '> [arguments]')
        return 0
    try:
        command, env = invocation(argv[0], argv[1:])
        return subprocess.run(command, cwd=ROOT, env=env).returncode
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
