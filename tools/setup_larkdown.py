"""Prepare an external research directory; local help only, never Feishu data calls."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
STATE = '.agents/config/runtime.local.json'
ENV = dict(os.environ, PYTHONUTF8='1', LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1',
           LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1', PIP_DISABLE_PIP_VERSION_CHECK='1',
           PIP_NO_INPUT='1', PIP_CONFIG_FILE=os.devnull)
PROBE = "import sys,json,ssl,subprocess,xml.etree.ElementTree; from pathlib import Path; assert (3,11)<=sys.version_info[:2]<(3,15); assert hasattr(Path,'is_relative_to'); print(json.dumps({'executable':sys.executable,'version':list(sys.version_info[:3])}))"
CORE = [(['docs', '+fetch', '--help'], ['--doc', '--detail']),
        (['docs', '+update', '--help'], ['--revision-id', '--command', '--block-id']),
        (['docs', '+script', '--help'], ['--command', '--content']),
        (['wiki', '+space-create', '--help'], ['--name']),
        (['wiki', '+node-create', '--help'], ['--space-id', '--obj-type'])]
BASE = [(['base', '+record-list', '--help'], ['--output', '--format', 'ndjson', '--offset']),
        (['base', '+record-get', '--help'], ['--output', '--record-id']),
        (['base', '+record-upsert', '--help'], ['--json', '--record-id']),
        (['base', '+view-set-visible-fields', '--help'], ['--view-id'])]


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('Refusing linked local state')
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def directory(path):
    """Do not create managed state through user-created links/junctions."""
    path = path.absolute()
    for candidate in [*reversed(path.parents), path]:
        if candidate.is_symlink() or (candidate.exists() and candidate.resolve() != candidate):
            raise ValueError('Linked environment paths are unsupported')
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(command, timeout=30, env=None):
    proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout, env=env or ENV)
    if proc.returncode:
        # Do not echo token-bearing tool responses, proxy credentials or pip configuration.
        error = RuntimeError(f'Local command failed (exit {proc.returncode}): {Path(command[0]).name}')
        error.details = re.sub(r'(https?://)[^/@\s]+:[^/@\s]+@', r'\1<redacted>@',
                               (proc.stderr or proc.stdout)[-4000:])
        raise error
    return proc.stdout


def workspace(root):
    root = root.resolve()
    for candidate in (root, root.parent if root.name == 'product' else root):
        if (candidate / 'tools/build_release.py').is_file() and (candidate / 'product').is_dir():
            raise ValueError('Development source is not an installation target')
    if not (root / '.agents/config/project-layout.json').is_file():
        raise ValueError('Open an extracted research directory first')
    layout = json.loads((root / '.agents/config/project-layout.json').read_text(encoding='utf-8'))
    if layout.get('workspace_kind') != 'personal-research' or not (root / 'run.py').is_file():
        raise ValueError('Unsupported research directory')
    for relative in ('.agents', '.agents/config', '.work', '.work/setup'):
        path = root / relative
        if path.is_symlink() or (path.exists() and path.resolve() != path.absolute()):
            raise ValueError('Linked setup paths are unsupported')
    return root


@contextmanager
def locked(root):
    path = root / '.work/setup/lock'
    directory(path.parent)
    if path.is_symlink():
        raise ValueError('Linked preparation lock is unsupported')
    with path.open('a+b') as stream:
        stream.seek(0)
        stream.write(b'0')
        stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError('Another environment preparation is running')
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def host():
    machine = platform.machine().lower()
    arch = {'amd64': 'amd64', 'x86_64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(machine)
    system = platform.system().lower()
    if not arch or system not in {'windows', 'darwin', 'linux'}:
        raise ValueError('No reviewed runtime asset for this system/architecture')
    return system + '-' + arch


def assets():
    with (HERE / 'runtime-assets.tsv').open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def download(row, cache):
    if not row['url'].startswith('https://') or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
        raise ValueError('Invalid reviewed download source')
    target = cache / 'downloads' / row['sha256']
    directory(target.parent)
    if target.exists():
        if target.is_symlink() or digest(target.read_bytes()) != row['sha256']:
            raise ValueError('Cached archive was modified; inspect it before retrying')
        return target
    for attempt in range(2):
        temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.part')
        try:
            started = time.monotonic()
            with urllib.request.urlopen(row['url'], timeout=15) as response, temporary.open('xb') as output:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 200 * 1024 * 1024 or time.monotonic() - started > 120:
                        raise RuntimeError('Runtime download exceeded its bound')
                    output.write(chunk)
            if digest(temporary.read_bytes()) != row['sha256']:
                raise ValueError('Runtime archive checksum mismatch')
            os.replace(temporary, target)
            return target
        except (OSError, TimeoutError):
            if attempt:
                raise RuntimeError('Runtime download failed after two bounded attempts') from None
        finally:
            temporary.unlink(missing_ok=True)


def install_asset(row, cache):
    archive = download(row, cache)
    binary = row['component'] + ('.exe' if row['platform'].startswith('windows') else '')
    destination = cache / 'components' / (row['component'] + '-' + row['version'] + '-' + row['platform'])
    directory(destination.parent)
    if destination.exists():
        receipt = json.loads((destination / 'artifact.json').read_text(encoding='utf-8'))
        if destination.is_symlink() or receipt.get('archive_sha256') != row['sha256']:
            raise ValueError('Unknown component directory; preserve and inspect it')
        for name, expected in receipt['files'].items():
            path = destination / name
            if Path(name).name != name or path.is_symlink() or digest(path.read_bytes()) != expected:
                raise ValueError('Cached component changed; preserve and inspect it')
        return destination / binary
    with tempfile.TemporaryDirectory(prefix='stage-', dir=destination.parent) as temporary:
        stage = Path(temporary)
        selected = {}
        if row['url'].endswith('.zip'):
            with zipfile.ZipFile(archive) as package:
                for item in package.infolist():
                    name = Path(item.filename).name
                    if name in {binary, 'LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE'}:
                        if name in selected or item.file_size > 200 * 1024 * 1024 or (item.external_attr >> 16) & 0o170000 == 0o120000:
                            raise ValueError('Unexpected component archive member')
                        selected[name] = package.read(item)
        else:
            with tarfile.open(archive, 'r:gz') as package:
                for item in package:
                    name = Path(item.name).name
                    if name in {binary, 'LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE'}:
                        if not item.isfile() or name in selected or item.size > 200 * 1024 * 1024:
                            raise ValueError('Unexpected component archive member')
                        selected[name] = package.extractfile(item).read()
        if binary not in selected:
            raise ValueError('Component archive has no expected executable')
        for name, blob in selected.items():
            (stage / name).write_bytes(blob)
        (stage / binary).chmod(0o755)
        save(stage / 'artifact.json', {'archive_sha256': row['sha256'], 'files': {n: digest(b) for n, b in selected.items()}})
        # Atomic publication; do not replace an existing directory or user files.
        try:
            stage.rename(destination)
        except FileExistsError:
            return install_asset(row, cache)
    return destination / binary


def python_probe(executable):
    try:
        return json.loads(run([str(executable), '-I', '-c', PROBE], timeout=10))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return None


def cli_command(executable):
    executable = Path(executable).resolve()
    if executable.suffix.lower() in {'.cmd', '.bat', '.ps1'}:
        runner = executable.parent / 'node_modules/@larksuite/cli/scripts/run.js'
        native = executable.parent / 'node_modules/@larksuite/cli/bin/lark-cli.exe'
        if native.is_file():
            return [str(native)]
        node = shutil.which('node')
        if runner.is_file() and node:
            return [str(Path(node).resolve()), str(runner)]
        raise ValueError('Cannot resolve this CLI launcher without a shell')
    return [str(executable)]


def choose_python(old, cache, requested, feature):
    candidates = list(dict.fromkeys(p for p in (requested, old.get('python'), sys.executable) if p))
    for candidate in candidates:
        probe = python_probe(candidate)
        if not probe:
            continue
        if feature == 'pptx':
            try:
                run([probe['executable'], '-I', '-c', 'import venv,ensurepip'])
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                continue
        return probe
    # A standard-library-only system Python can prepare the reviewed full runtime
    # when its optional venv/ensurepip support is missing. No system packages change.
    row = next(r for r in assets() if r['component'] == 'uv' and r['platform'] == host())
    uv = str(install_asset(row, cache))
    version = next(r['version'] for r in assets() if r['component'] == 'python')
    env = dict(ENV, UV_PYTHON_INSTALL_DIR=str(cache / 'python'), UV_PYTHON_INSTALL_BIN='0',
               UV_PYTHON_INSTALL_REGISTRY='0', UV_NO_CONFIG='1', UV_NO_PROGRESS='1')
    directory(cache / 'python')
    run([uv, 'python', 'install', version, '--no-bin', '--no-registry'], timeout=300, env=env)
    executable = run([uv, 'python', 'find', '--managed-python', version], env=env).strip()
    probe = python_probe(executable)
    if not probe:
        raise RuntimeError('Managed Python did not pass the local capability check')
    return probe


def fingerprint(command):
    return [{'path': str(Path(p).resolve()), 'size': Path(p).stat().st_size,
             'mtime_ns': Path(p).stat().st_mtime_ns} for p in command]


def cli_compatible(command, feature):
    try:
        version = run(command + ['--version']).strip()
        if not re.search(r'lark-cli.*\d+\.\d+\.\d+', version):
            return False
        for args, required in CORE + (BASE if feature == 'base' else []):
            help_text = run(command + args)
            if any(flag not in help_text for flag in required):
                return False
        return True
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return False


def choose_cli(old, cache, feature):
    candidates = []
    if old.get('cli'):
        try:
            if feature in old.get('features', []) and fingerprint(old['cli']) == old.get('cli_fingerprint'):
                return old['cli']
        except OSError:
            pass
        candidates.append(old['cli'])
    discovered = shutil.which('lark-cli')
    if discovered:
        try:
            candidates.append(cli_command(discovered))
        except ValueError:
            pass
    for command in candidates:
        if cli_compatible(command, feature):
            return command
    row = next(r for r in assets() if r['component'] == 'lark-cli' and r['platform'] == host())
    command = [str(install_asset(row, cache))]
    if not cli_compatible(command, feature):
        raise RuntimeError('Reviewed CLI did not satisfy the required local help contract')
    return command


def pptx_environment(root, interpreter, old):
    root = root.resolve()
    lock_hash = digest((HERE / 'pptx-requirements.lock').read_bytes())
    versions = dict(re.findall(r'^([A-Za-z0-9_-]+)==([^\s]+)', (HERE / 'pptx-requirements.lock').read_text(), re.M))
    check = ('import importlib.metadata as m; from pptx import Presentation; from PIL import Image,features; '
             'assert features.check("libtiff"); expected=' + repr(versions) +
             '; assert all(m.version(k)==v for k,v in expected.items())')
    if old.get('pptx_lock') == lock_hash and old.get('pptx_python'):
        try:
            run([old['pptx_python'], '-I', '-c', check])
            return old['pptx_python'], lock_hash
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass
    pending_path = root / '.work/setup/pptx-pending.json'
    folder = None
    if pending_path.exists():
        if pending_path.is_symlink():
            raise ValueError('Linked dependency state is unsupported')
        pending = json.loads(pending_path.read_text(encoding='utf-8'))
        candidate = Path(pending['directory'])
        if (candidate.parent == root / '.work/setup/environments' and not candidate.is_symlink()
                and pending.get('lock') == lock_hash and pending.get('python') == interpreter):
            folder = candidate
    if folder is None:
        folder = root / '.work/setup/environments' / uuid.uuid4().hex
        directory(folder.parent)
        save(pending_path, {'directory': str(folder), 'lock': lock_hash, 'python': interpreter})
    directory(folder)
    # Do not move a venv after creation: executable paths may be embedded in it.
    python = folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        run([interpreter, '-m', 'venv', str(folder)], timeout=120)
    run([str(python), '-m', 'pip', 'install', '--index-url', 'https://pypi.org/simple',
         '--only-binary=:all:', '--require-hashes', '--timeout', '20', '--retries', '1',
         '-r', str(HERE / 'pptx-requirements.lock')], timeout=600)
    run([str(python), '-I', '-c', check])
    pending_path.unlink(missing_ok=True)
    return str(python), lock_hash


def prepare(root, cache, feature='core', interpreter=None):
    root = workspace(root)
    if cache.is_symlink():
        raise ValueError('Linked runtime caches are unsupported')
    cache = directory(cache.resolve())
    if (root / STATE).is_symlink():
        raise ValueError('Linked runtime settings are unsupported')
    old = json.loads((root / STATE).read_text(encoding='utf-8')) if (root / STATE).exists() else {}
    if not isinstance(old, dict) or (old and old.get('schema_version') != 1):
        raise ValueError('Unknown runtime settings; preserve and inspect them')
    if old and (not isinstance(old.get('python'), str) or not isinstance(old.get('cli'), list)
                or not old['cli'] or any(not isinstance(p, str) for p in old['cli'])
                or not isinstance(old.get('features'), list)):
        raise ValueError('Invalid runtime settings; preserve and inspect them')
    probe = choose_python(old, cache, interpreter, feature)
    interpreter = str(Path(probe['executable']).resolve())
    feature = feature or 'core'
    cli_feature = 'base' if feature == 'base' else 'core'
    command = choose_cli(old, cache, cli_feature)
    current_fingerprint = fingerprint(command)
    features = set(old.get('features', [])) if old.get('cli_fingerprint') == current_fingerprint else set()
    features.update({'core', feature})
    data = {'schema_version': 1, 'python': interpreter, 'python_version': probe['version'],
            'python_fingerprint': fingerprint([interpreter]),
            'cli': command, 'cli_fingerprint': current_fingerprint, 'features': sorted(features)}
    if feature == 'pptx':
        data['pptx_python'], data['pptx_lock'] = pptx_environment(root, interpreter, old)
    elif old.get('pptx_python') and old.get('python') == interpreter:
        data.update({k: old[k] for k in ('pptx_python', 'pptx_lock') if k in old})
    if not data.get('pptx_python'):
        features.discard('pptx')
        data['features'] = sorted(features)
    save(root / STATE, data)
    return {'ok': True, 'features': sorted(features), 'settings': STATE,
            'authorization': 'not_checked', 'report': '.work/setup/report.json'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=HERE.parent / 'laRkdown')
    parser.add_argument('--feature', choices=['core', 'base', 'pptx'], default='core')
    parser.add_argument('--python', dest='interpreter')
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('LOCALAPPDATA', Path.home() / '.cache')) / 'laRkdown')
    args = parser.parse_args()
    started = time.monotonic()
    root = None
    try:
        root = workspace(args.project)
        with locked(root):
            result = prepare(root, args.cache, args.feature, args.interpreter)
            save(root / '.work/setup/report.json', {**result, 'seconds': round(time.monotonic() - started, 3)})
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, StopIteration, subprocess.TimeoutExpired) as error:
        result = {'ok': False, 'stage': 'environment', 'message': 'Environment preparation stopped; preserve local state and inspect component compatibility/network.',
                  'feature': args.feature, 'seconds': round(time.monotonic() - started, 3)}
        if root:
            diagnostic = re.sub(r'(https?://)[^/@\s]+:[^/@\s]+@', r'\1<redacted>@',
                                getattr(error, 'details', str(error)))[:4000]
            save(root / '.work/setup/report.json', {**result, 'error_type': type(error).__name__, 'diagnostic': diagnostic})
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
