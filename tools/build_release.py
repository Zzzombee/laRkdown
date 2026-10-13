"""Prepare and validate laRkdown's upgrade contract before packaging a release."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from upgrade_larkdown import LEGACY, MANIFEST, Release, encoded, sha

BOOTSTRAP_TAGS = ('v0.1.0', 'v0.2.0')
EXACT = {'AGENTS.md', 'UPGRADING.md', 'requirements.txt', 'upgrade_larkdown.py'}
ROOTS = ('.agents/instructions/', '.agents/skills/', '.agents/config/')
PRIVATE = {'feishu.json', 'feishu-documents.json', 'release-manifest.json'}
PRIVATE_ROOTS = ('outputs/', 'sources/', '.work/', '.planning/')


def managed(name):
    if name in EXACT:
        return True
    if not name.startswith(ROOTS):
        return False
    parts = Path(name).parts
    return (parts[-1] not in PRIVATE and not parts[-1].endswith('.local.json')
            and '__pycache__' not in parts and not name.endswith(('.pyc', '.pyo')))


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True)
    return result.stdout


def tree(tag):
    if tag not in BOOTSTRAP_TAGS:
        return {name: blob for name, blob in committed_files(tag).items() if managed(name)}
    # The two already published Windows ZIPs contain CRLF archive bytes.
    result = git('archive', '--format=zip', tag)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        return {item.filename: archive.read(item) for item in archive.infolist()
                if not item.is_dir() and managed(item.filename)}


def committed_files(ref):
    names = [name for name in git('ls-tree', '-r', '--name-only', '-z', ref).decode('utf-8').split('\0') if name]
    return {name: git('show', f'{ref}:{name}') for name in names}


def version_tuple(value):
    if not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError(f'Only stable semantic release versions are supported: {value}')
    return tuple(int(part) for part in value.split('.'))


def historical_tags():
    current = json.loads((ROOT / '.agents/config/upstream.json').read_text(encoding='utf-8'))['version']
    prior = [t for t in git('tag', '--list', 'v*').decode().splitlines()
             if re.fullmatch(r'v\d+\.\d+\.\d+', t) and version_tuple(t[1:]) < version_tuple(current)]
    if not set(BOOTSTRAP_TAGS) <= set(prior):
        raise ValueError('Published v0.1.0 and v0.2.0 tag baselines are required')
    return sorted(prior, key=lambda t: version_tuple(t[1:]))


def previous_releases():
    catalog = {}
    pinned = json.loads((ROOT / LEGACY).read_text(encoding='utf-8'))['releases']
    for tag in historical_tags():
        if tag in BOOTSTRAP_TAGS:
            entry = pinned.get(tag[1:])
            if not entry or sha(entry['merge_base']['AGENTS.md'].encode('utf-8')) != entry['managed_files']['AGENTS.md']:
                raise ValueError(f'Published Windows baseline is missing or invalid: {tag}')
            catalog[tag[1:]] = entry
            continue
        files = tree(tag)
        schema = json.loads(files['.agents/config/project-layout.json'])['schema_version']
        catalog[tag[1:]] = {'project_schema_version': schema,
                            'managed_files': {name: sha(blob) for name, blob in sorted(files.items())},
                            'merge_base': {'AGENTS.md': files['AGENTS.md'].decode('utf-8-sig')}}
    return {'schema_version': 1, 'releases': catalog}


def current_files():
    # Git archive publishes index blobs, which may differ from Windows working
    # bytes under core.autocrlf. Stage edits before preparing the manifest.
    tracked = [name for name in git('ls-files', '-z').decode('utf-8').split('\0') if name]
    result = {name: git('show', ':' + name) for name in tracked if managed(name) and name != LEGACY}
    result[LEGACY] = encoded(previous_releases())
    if not EXACT <= set(result):
        raise ValueError('Stage all required release files before preparing the manifest')
    return result


def desired_manifest():
    files = current_files()
    version = json.loads(files['.agents/config/upstream.json'])['version']
    schema = json.loads(files['.agents/config/project-layout.json'])['schema_version']
    legacy = previous_releases()
    return {'schema_version': 1, 'project': 'laRkdown', 'version': version,
            'project_schema_version': schema,
            'supported_from': sorted(legacy['releases']),
            'managed_files': {name: sha(blob) for name, blob in sorted(files.items())}}


def prepare():
    target = ROOT / LEGACY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded(previous_releases()))
    manifest = ROOT / MANIFEST
    manifest.write_bytes(encoded(desired_manifest()))
    return manifest


def check():
    tracked = git('ls-files', '-z').decode('utf-8').split('\0')
    for name in filter(None, tracked):
        path = Path(name)
        if (name.startswith(PRIVATE_ROOTS) or path.name in {'feishu.json', 'feishu-documents.json', '.env'}
                or path.name.endswith('.local.json') or '__pycache__' in path.parts
                or path.suffix in {'.pyc', '.pyo'}):
            raise ValueError(f'Private or generated file is tracked for public release: {name}')
    expected_legacy = encoded(previous_releases())
    if (ROOT / LEGACY).read_bytes() != expected_legacy:
        raise ValueError('Legacy baseline catalog is stale; run --prepare')
    expected_manifest = encoded(desired_manifest())
    if (ROOT / MANIFEST).read_bytes() != expected_manifest:
        raise ValueError('Release manifest is stale; run --prepare')
    info = json.loads(expected_manifest)
    if not {'upgrade_larkdown.py', '.agents/skills/upgrade-larkdown/SKILL.md'} <= info['managed_files'].keys():
        raise ValueError('Automatic upgrader is missing from release-managed files')
    if info['project_schema_version'] != 1:
        raise ValueError('Project schema changed: supply and test a migration before release')
    if historical_tags()[-1][1:] not in info['supported_from']:
        raise ValueError('Release does not support the previous published version')
    return {'ok': True, 'version': info['version'], 'managed_files': len(info['managed_files']),
            'supported_from': info['supported_from'], 'upgrader_included': True}


def build(output: Path):
    result = check()
    if git('status', '--porcelain').strip():
        raise ValueError('Commit all public release changes before creating a ZIP')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, blob in sorted(committed_files('HEAD').items()):
            archive.writestr('laRkdown/' + name, blob)
    release = Release(output)
    if release.manifest['version'] != result['version']:
        raise ValueError('Committed release version differs from working tree')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_name(output.name + '.sha256')
    checksum.write_text(f'{digest}  {output.name}\n', encoding='ascii')
    return {**result, 'asset': str(output), 'bytes': output.stat().st_size,
            'sha256': digest, 'checksum_asset': str(checksum),
            'archive_members': len(release.files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--build', type=Path, metavar='ZIP_PATH')
    args = parser.parse_args()
    try:
        result = {'prepared': str(prepare())} if args.prepare else check() if args.check else build(args.build)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
