"""Upgrade an initialized laRkdown research project from a verified release ZIP.

The project keeps its Feishu documents and private files. This tool only manages
the public package paths declared by a release manifest.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile

MANIFEST = '.agents/config/release-manifest.json'
LEGACY = '.agents/config/legacy-release-baselines.json'
PENDING = '.work/upgrades/pending.json'
REPOSITORY = 'Zzzombee/laRkdown'
MAX_ARCHIVE = 200 * 1024 * 1024
PUBLIC_CONFIG = {'feishu.example.json', 'official-sources.json', 'project-layout.json',
                 'upstream.json', 'legacy-release-baselines.json'}


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or path.is_absolute() or any(p in {'', '.', '..'} for p in path.parts):
        raise ValueError(f'Unsafe package path: {name}')
    if name != path.as_posix():
        raise ValueError(f'Noncanonical package path: {name}')
    return name


def project_path(root: Path, name: str) -> Path:
    safe_name(name)
    path = root
    for component in PurePosixPath(name).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError(f'Symbolic-link project path is outside the upgrade contract: {name}')
    if not path.resolve(strict=False).is_relative_to(root.resolve()):
        raise ValueError('Project path escapes its root')
    return path


def existing_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'Expected a regular package file: {path}')
    return sha(path.read_bytes())


def merge_project_rules(base: str, user_bytes: bytes, incoming_bytes: bytes) -> bytes:
    """Three-way line merge for AGENTS.md; overlapping replacements stay conflicts."""
    user_text = user_bytes.decode('utf-8-sig')
    incoming_text = incoming_bytes.decode('utf-8-sig')
    crlf = b'\r\n' in user_bytes and b'\n' not in user_bytes.replace(b'\r\n', b'')
    base_lines = base.replace('\r\n', '\n').splitlines(keepends=True)
    user_lines = user_text.replace('\r\n', '\n').splitlines(keepends=True)
    incoming_lines = incoming_text.replace('\r\n', '\n').splitlines(keepends=True)

    def changes(new_lines, side):
        return [(a, b, new_lines[c:d], side)
                for action, a, b, c, d in difflib.SequenceMatcher(None, base_lines, new_lines, autojunk=False).get_opcodes()
                if action != 'equal']

    user_changes = changes(user_lines, 'user')
    incoming_changes = changes(incoming_lines, 'release')
    for a, b, content, _ in user_changes:
        for c, d, other, _ in incoming_changes:
            if a == b and c == d:
                continue  # Append both insertions, release first and user second.
            if a == b:
                overlap = c < a < d
            elif c == d:
                overlap = a < c < b
            else:
                overlap = max(a, c) < min(b, d)
            if overlap and (a, b, content) != (c, d, other):
                raise ValueError('AGENTS.md contains overlapping user and release edits')
    insertions = {}
    replacements = {}
    for a, b, content, side in incoming_changes + user_changes:
        if a == b:
            insertions.setdefault(a, []).append((side, content))
        else:
            if a in replacements and replacements[a][:2] != (b, content):
                raise ValueError('AGENTS.md contains divergent replacements at the same position')
            replacements[a] = (b, content, side)
    merged = []
    index = 0
    while index <= len(base_lines):
        additions = insertions.get(index, [])
        if additions:
            release_part = next((x for side, x in additions if side == 'release'), [])
            user_part = next((x for side, x in additions if side == 'user'), [])
            merged.extend(release_part)
            if user_part != release_part:
                merged.extend(user_part)
        if index == len(base_lines):
            break
        replacement = replacements.get(index)
        if replacement:
            stop, content, _ = replacement
            merged.extend(content)
            index = stop
        else:
            merged.append(base_lines[index])
            index += 1
    result = ''.join(merged).encode('utf-8')
    return result.replace(b'\n', b'\r\n') if crlf else result


def write_atomic(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.upgrade-' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Release:
    def __init__(self, archive: Path):
        self.archive = archive.resolve()
        if self.archive.stat().st_size > MAX_ARCHIVE:
            raise ValueError('Release ZIP exceeds the supported size')
        self.files = {}
        with zipfile.ZipFile(self.archive) as package:
            names = [item for item in package.infolist() if not item.is_dir()]
            total = 0
            seen = set()
            for item in names:
                if item.file_size > MAX_ARCHIVE:
                    raise ValueError('Release member exceeds the supported size')
                total += item.file_size
                if total > MAX_ARCHIVE:
                    raise ValueError('Release expands beyond the supported size')
                # Unix mode 0120000 marks a symlink. Do not unpack through one.
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Release contains a symbolic link')
                full = safe_name(item.filename)
                if not full.startswith('laRkdown/'):
                    raise ValueError('Release has an unexpected root directory')
                name = safe_name(full[len('laRkdown/'):])
                folded = name.casefold()
                if folded in seen:
                    raise ValueError('Release contains duplicate case-insensitive paths')
                seen.add(folded)
                self.files[name] = package.read(item)
        if MANIFEST not in self.files or LEGACY not in self.files:
            raise ValueError('Release lacks the upgrade manifest or legacy baseline')
        self.manifest = json.loads(self.files[MANIFEST])
        self.legacy = json.loads(self.files[LEGACY])
        self._verify()

    def _verify(self):
        info = self.manifest
        if info.get('schema_version') != 1 or info.get('project') != 'laRkdown':
            raise ValueError('Unsupported release manifest')
        if not isinstance(info.get('version'), str) or not isinstance(info.get('project_schema_version'), int):
            raise ValueError('Release version/schema is missing')
        layout = json.loads(self.files['.agents/config/project-layout.json'])
        if layout.get('schema_version') != info['project_schema_version']:
            raise ValueError('Release project layout and schema declaration differ')
        files = info.get('managed_files')
        if not isinstance(files, dict) or not files or MANIFEST in files:
            raise ValueError('Invalid managed-file list')
        for name, wanted in files.items():
            safe_name(name)
            if name.startswith(('.work/', 'outputs/', 'sources/', '.planning/')) or name.endswith('.local.json'):
                raise ValueError('Private/user-owned path declared as managed')
            if name.startswith('.agents/config/') and PurePosixPath(name).name not in PUBLIC_CONFIG:
                raise ValueError('Unrecognized config declared as managed')
            if name not in {'AGENTS.md', 'USER_GUIDE.md', 'UPGRADING.md', 'requirements.txt', 'upgrade_larkdown.py'} and not name.startswith(('.agents/config/', '.agents/instructions/', '.agents/skills/')):
                raise ValueError('Path outside the release-managed tool surface')
            if name not in self.files or sha(self.files[name]) != wanted:
                raise ValueError(f'Release file failed manifest verification: {name}')
        required = {'AGENTS.md', 'UPGRADING.md', 'requirements.txt', 'upgrade_larkdown.py',
                    '.agents/skills/upgrade-larkdown/SKILL.md', LEGACY}
        if not required <= set(files):
            raise ValueError('Release lacks its upgrade entrypoint or required resources')
        if json.loads(self.files['.agents/config/upstream.json'])['version'] != info['version']:
            raise ValueError('Release version differs from upstream provenance config')
        if self.legacy.get('schema_version') != 1 or not isinstance(self.legacy.get('releases'), dict):
            raise ValueError('Invalid legacy baseline catalog')


def source_state(root: Path, release: Release):
    current = project_path(root, MANIFEST)
    if current.exists():
        manifest = json.loads(current.read_text(encoding='utf-8'))
        if manifest.get('schema_version') != 1 or manifest.get('project') != 'laRkdown':
            raise ValueError('Existing project manifest is invalid')
        version = manifest['version']
        baseline = manifest['managed_files']
        schema = manifest['project_schema_version']
        manifest_hash = existing_hash(current)
        published = release.legacy['releases'].get(version)
        if published and (baseline != published['managed_files'] or schema != published['project_schema_version']):
            raise ValueError('Installed release manifest differs from its published baseline')
        if version == release.manifest['version'] and (baseline != release.manifest['managed_files']
                                                       or schema != release.manifest['project_schema_version']):
            raise ValueError('Installed current-version manifest differs from the target release')
    else:
        upstream = project_path(root, '.agents/config/upstream.json')
        if not upstream.is_file():
            raise ValueError('Existing project has no laRkdown version marker')
        version = json.loads(upstream.read_text(encoding='utf-8'))['version']
        known = release.legacy['releases'].get(version)
        if not known:
            raise ValueError(f'No trusted baseline for installed version {version}')
        baseline, schema, manifest_hash = known['managed_files'], known['project_schema_version'], None
    if version != release.manifest['version'] and version not in release.manifest.get('supported_from', []):
        raise ValueError(f'Unsupported upgrade from {version} to {release.manifest["version"]}')
    if schema != release.manifest['project_schema_version']:
        raise ValueError('Research project schema change needs an explicit migration; this release only upgrades code')
    return version, baseline, manifest_hash


def make_plan(root: Path, release: Release):
    root = root.resolve(strict=True)
    if not root.is_dir() or not project_path(root, 'AGENTS.md').is_file():
        raise ValueError('Target is not an initialized laRkdown project')
    version, old, old_manifest_hash = source_state(root, release)
    new = release.manifest['managed_files']
    operations, conflicts = [], []
    for name in sorted(set(old) | set(new)):
        path = project_path(root, name)
        actual = existing_hash(path)
        before = old.get(name)
        after = new.get(name)
        if actual == after:
            continue
        if actual is not None and before == after:
            continue  # Current release is installed; keep local edits on a repeat check.
        if actual is None:
            if after is not None:
                operations.append({'path': name, 'action': 'add', 'before': None, 'after': after})
            continue
        if before is not None and actual == before:
            operations.append({'path': name, 'action': 'remove' if after is None else 'update',
                               'before': before, 'after': after})
        elif name == 'AGENTS.md' and before and after:
            base = release.legacy['releases'].get(version, {}).get('merge_base', {}).get('AGENTS.md')
            if not base or sha(base.encode('utf-8')) != before:
                conflicts.append({'path': name, 'reason': 'published merge base unavailable'})
                continue
            try:
                combined = merge_project_rules(base, path.read_bytes(), release.files[name])
            except (UnicodeError, ValueError) as error:
                conflicts.append({'path': name, 'reason': str(error)})
                continue
            if sha(combined) != actual:
                operations.append({'path': name, 'action': 'merge', 'before': actual, 'after': sha(combined)})
        else:
            conflicts.append({'path': name, 'reason': 'user-modified or unrecognized managed path'})
    actual_manifest = existing_hash(project_path(root, MANIFEST))
    if actual_manifest != old_manifest_hash:
        conflicts.append({'path': MANIFEST, 'reason': 'installed release manifest changed'})
    else:
        wanted = sha(release.files[MANIFEST])
        if actual_manifest != wanted:
            operations.append({'path': MANIFEST, 'action': 'add' if actual_manifest is None else 'update',
                               'before': actual_manifest, 'after': wanted})
    return {'project': str(root), 'from_version': version, 'to_version': release.manifest['version'],
            'project_schema_version': release.manifest['project_schema_version'],
            'operations': operations, 'conflicts': conflicts}


def transaction_dir(root: Path, token: str):
    return project_path(root, f'.work/upgrades/{token}')


def pending_path(root: Path):
    return project_path(root, PENDING)


def apply_plan(root: Path, release: Release, plan):
    root = root.resolve()
    pending = pending_path(root)
    if pending.exists():
        raise ValueError('A previous upgrade is pending; run recover before another upgrade')
    if plan['conflicts']:
        raise ValueError('Managed-file conflicts must be resolved before applying the upgrade')
    if not plan['operations']:
        return {'ok': True, 'from_version': plan['from_version'], 'version': plan['to_version'], 'changed': 0}
    token = uuid.uuid4().hex
    directory = transaction_dir(root, token)
    backup = project_path(root, f'.work/upgrades/{token}/backup')
    backup.mkdir(parents=True, exist_ok=False)
    for operation in plan['operations']:
        name = operation['path']
        if operation['before'] is None:
            continue
        source = project_path(root, name)
        if existing_hash(source) != operation['before']:
            raise ValueError(f'Project changed while preparing upgrade: {name}')
        destination = project_path(backup, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if existing_hash(destination) != operation['before']:
            raise ValueError('Backup verification failed')
    transaction = {'schema_version': 1, 'token': token, 'from_version': plan['from_version'],
                   'to_version': plan['to_version'], 'operations': plan['operations']}
    pending.parent.mkdir(parents=True, exist_ok=True)
    with pending.open('xb') as stream:
        stream.write(encoded(transaction))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        for operation in plan['operations']:
            name = operation['path']
            target = project_path(root, name)
            if existing_hash(target) != operation['before']:
                raise ValueError(f'Project file changed during upgrade: {name}')
            if operation['action'] == 'remove':
                target.unlink()
            else:
                if operation['action'] == 'merge':
                    base = release.legacy['releases'][plan['from_version']]['merge_base']['AGENTS.md']
                    payload = merge_project_rules(base, target.read_bytes(), release.files[name])
                else:
                    payload = release.files[name]
                if sha(payload) != operation['after']:
                    raise ValueError('Release content changed after planning')
                write_atomic(target, payload)
            if existing_hash(target) != operation['after']:
                raise ValueError(f'Write verification failed: {name}')
        pending.unlink()
        return {'ok': True, 'from_version': plan['from_version'], 'version': plan['to_version'],
                'changed': len(plan['operations']), 'project': str(root),
                'doubao_skill_refresh_required': True}
    except Exception as error:
        try:
            recover(root)
        except Exception as recovery_error:
            raise RuntimeError(f'Upgrade stopped: {error}; recovery pending: {recovery_error}') from error
        raise RuntimeError(f'Upgrade stopped and local package files were restored: {error}') from error


def recover(root: Path):
    root = root.resolve(strict=True)
    pending = pending_path(root)
    if not pending.exists():
        return {'ok': True, 'pending': False}
    transaction = json.loads(pending.read_text(encoding='utf-8'))
    token = transaction['token']
    if not isinstance(token, str) or len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('Invalid upgrade transaction identifier')
    backup = transaction_dir(root, token) / 'backup'
    operations = transaction['operations']
    current = {}
    for operation in operations:
        name = operation['path']
        value = existing_hash(project_path(root, name))
        if value not in {operation['before'], operation['after']}:
            raise ValueError(f'Project file changed after interruption: {name}')
        if operation['before'] is not None and existing_hash(project_path(backup, name)) != operation['before']:
            raise ValueError(f'Backup missing or altered: {name}')
        current[name] = value
    if all(current[op['path']] == op['after'] for op in operations):
        pending.unlink()
        return {'ok': True, 'completed': True, 'version': transaction['to_version']}
    for operation in reversed(operations):
        name = operation['path']
        if current[name] == operation['before']:
            continue
        target = project_path(root, name)
        if operation['before'] is None:
            target.unlink()
        else:
            write_atomic(target, project_path(backup, name).read_bytes())
        if existing_hash(target) != operation['before']:
            raise ValueError(f'Rollback verification failed: {name}')
    pending.unlink()
    return {'ok': True, 'rolled_back': True, 'version': transaction['from_version']}


def fetch_latest(destination: Path) -> Path:
    endpoint = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
    request = urllib.request.Request(endpoint, headers={'User-Agent': 'laRkdown-upgrader', 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code not in {403, 429}:
            raise
        release = None
    if release is None:
        page = f'https://github.com/{REPOSITORY}/releases/latest'
        request = urllib.request.Request(page, headers={'User-Agent': 'laRkdown-upgrader'})
        with urllib.request.urlopen(request, timeout=30) as response:
            final = response.geturl()
        prefix = f'https://github.com/{REPOSITORY}/releases/tag/'
        if not final.startswith(prefix):
            raise ValueError('GitHub latest-release redirect is unexpected')
        tag = final[len(prefix):]
        asset_name = f'laRkdown-{tag}.zip'
        asset_url = f'https://github.com/{REPOSITORY}/releases/download/{tag}/{asset_name}'
        checksum_request = urllib.request.Request(asset_url + '.sha256', headers={'User-Agent': 'laRkdown-upgrader'})
        with urllib.request.urlopen(checksum_request, timeout=30) as response:
            checksum = response.read(200).decode('ascii').strip()
        if not re.fullmatch(r'[0-9a-f]{64}  ' + re.escape(asset_name), checksum):
            raise ValueError('Latest release checksum asset is invalid')
        expected_digest = checksum[:64]
        url = asset_url
    else:
        tag = release.get('tag_name', '')
        asset_name = f'laRkdown-{tag}.zip'
        assets = [a for a in release.get('assets', []) if a.get('name') == asset_name]
        if len(assets) != 1 or not assets[0].get('digest', '').startswith('sha256:'):
            raise ValueError('Latest release lacks a single SHA256-verifiable package asset')
        url = assets[0].get('browser_download_url', '')
        expected_digest = assets[0]['digest'][7:]
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Latest GitHub release has an unexpected tag')
    if not url.startswith(f'https://github.com/{REPOSITORY}/releases/download/{tag}/'):
        raise ValueError('Unexpected release asset address')
    request = urllib.request.Request(url, headers={'User-Agent': 'laRkdown-upgrader'})
    hasher = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open('xb') as output:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_ARCHIVE:
                raise ValueError('Downloaded release exceeds the supported size')
            hasher.update(chunk)
            output.write(chunk)
    if hasher.hexdigest() != expected_digest:
        raise ValueError('GitHub asset SHA256 verification failed')
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path, help='existing initialized research project directory')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--package', type=Path, help='new laRkdown release ZIP')
    group.add_argument('--latest', action='store_true', help='download latest public GitHub release with SHA256 verification')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--apply', action='store_true', help='apply the verified plan; default is preview only')
    modes.add_argument('--recover', action='store_true', help='verify/rollback an interrupted local upgrade')
    args = parser.parse_args(argv)
    try:
        if args.recover:
            result = recover(args.project)
        else:
            if not args.package and not args.latest:
                parser.error('provide --package or --latest')
            if pending_path(args.project.resolve()).exists():
                raise ValueError('Previous upgrade is pending; run --recover first')
            if args.latest:
                with tempfile.TemporaryDirectory(prefix='larkdown-release-') as directory:
                    archive = fetch_latest(Path(directory) / 'release.zip')
                    release = Release(archive)
                    plan = make_plan(args.project, release)
                    result = apply_plan(args.project, release, plan) if args.apply else {'ok': not plan['conflicts'], **plan}
            else:
                release = Release(args.package)
                plan = make_plan(args.project, release)
                result = apply_plan(args.project, release, plan) if args.apply else {'ok': not plan['conflicts'], **plan}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('ok') else 2
    except (OSError, KeyError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
