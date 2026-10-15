"""Build one release ZIP with isolated research and maintenance directories."""
from __future__ import annotations
import argparse
import copy
from functools import lru_cache
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.upgrade_larkdown import (LEGACY, METADATA, MANIFEST, Release, encoded, sha,
                                  RESEARCH_SKILLS, RESEARCH_INSTRUCTIONS, PUBLIC_CONFIG, research_path, MAINTENANCE_FILES)

BOOTSTRAP_TAGS = ('v0.1.0', 'v0.2.0')
USER_GUIDE = 'USER_GUIDE.md'
VERSION_NOTES = 'tools/release/version-notes.md'
PROVENANCE = 'tools/release/upstream.json'
RELEASE_MANIFEST = 'tools/release/release-manifest.json'
LEGACY_SOURCE = 'tools/release/' + LEGACY
PACKAGE_EXACT = {'AGENTS.md', 'README.md', 'requirements.txt', 'run.py', 'run.ps1'} | {
    '.agents/config/' + name for name in PUBLIC_CONFIG} | {
    '.agents/instructions/' + name for name in RESEARCH_INSTRUCTIONS} | {
    f'.agents/skills/{skill}/SKILL.md' for skill in RESEARCH_SKILLS}
MAINTENANCE_SOURCES = {'tools/' + name for name in MAINTENANCE_FILES}
PRIVATE_ROOTS = ('outputs/', 'sources/', '.work/', '.planning/')
FORBIDDEN_PRODUCT_TEXT = ('upgrade_larkdown', 'upgrade-larkdown', 'release-manifest',
    'legacy-release-baselines', 'upstream.json', 'version-notes', 'UPGRADING.md',
    'USER_GUIDE.md', 'tools/RELEASING', '发布维护', '版本管理', '版本升级',
    '发行清单', 'git tag', 'git push', '六个技能')


def managed(name):
    return research_path(name)


def package_files(files):
    """Accept repository paths and map only product/ to installed project paths."""
    selected = {}
    for source, blob in files.items():
        if not source.startswith('product/'):
            continue
        name = source[len('product/'):]
        if not managed(name):
            raise ValueError(f'Unexpected file in personal research product: {source}')
        selected[name] = blob
    missing = PACKAGE_EXACT - selected.keys()
    if missing:
        raise ValueError(f'Research package is missing required files: {sorted(missing)}')
    return selected


def check_boundaries(files):
    product = package_files(files)
    if any(name.startswith('.agents/skills/') for name in files):
        raise ValueError('Development root contains a research skill discovery entrypoint')
    developer = files.get('AGENTS.md', b'').decode('utf-8-sig')
    if not developer or 'SKILL.md' in developer or any(skill in developer for skill in RESEARCH_SKILLS):
        raise ValueError('Development AGENTS contains research routing or is missing')
    if product['AGENTS.md'] == files['AGENTS.md']:
        raise ValueError('Development and personal research AGENTS must be distinct')
    for name, blob in product.items():
        if name.endswith(('.md', '.json')):
            text = blob.decode('utf-8-sig')
            for forbidden in FORBIDDEN_PRODUCT_TEXT:
                if forbidden in text:
                    raise ValueError(f'Maintenance instruction leaked into research product: {name}: {forbidden}')
    layout = json.loads(product['.agents/config/project-layout.json'])
    if layout.get('workspace_kind') != 'personal-research':
        raise ValueError('Personal research workspace marker is missing')
    return product


def check_user_guide(files, version):
    if USER_GUIDE not in files:
        raise ValueError('Missing USER_GUIDE.md before checking a release')
    guide = files[USER_GUIDE].decode('utf-8-sig')
    if not guide.splitlines() or guide.splitlines()[0] != f'# laRkdown 使用指南（v{version}）':
        raise ValueError('USER_GUIDE.md title is stale; update the guide before release')
    base = 'https://github.com/Zzzombee/laRkdown/releases/'
    required = (f'{base}tag/v{version}', f'{base}download/v{version}/laRkdown-v{version}.zip')
    if any(link not in guide for link in required):
        raise ValueError('USER_GUIDE.md lacks the matching release page or ZIP download link')
    references = re.findall(re.escape(base) + r'(?:tag|download)/v(\d+\.\d+\.\d+)', guide)
    references += re.findall(r'laRkdown(?:-maintenance)?-v(\d+\.\d+\.\d+)\.zip', guide)
    if any(reference != version for reference in references):
        raise ValueError('USER_GUIDE.md contains stale laRkdown release links or ZIP filenames')


def check_version_notes(files, version):
    if VERSION_NOTES not in files:
        raise ValueError('Missing version-notes.md before checking a release')
    lines = files[VERSION_NOTES].decode('utf-8-sig').splitlines()
    if not lines or lines[0] != f'# laRkdown 版本说明（v{version}）':
        raise ValueError('version-notes.md title is stale; update the notes before release')
    if not any(line.strip() for line in lines[1:]):
        raise ValueError('version-notes.md has no release explanation')


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True).stdout


@lru_cache(maxsize=None)
def committed_files(ref):
    names = [n for n in git('ls-tree', '-r', '--name-only', '-z', ref).decode().split('\0') if n]
    return {name: git('show', f'{ref}:{name}') for name in names}


def working_files():
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
    result = {}
    for name in set(names):
        if not name or not (ROOT / name).is_file():
            continue
        blob = (ROOT / name).read_bytes()
        if (PurePosixPath(name).suffix in {'.md', '.py', '.json', '.txt', '.ps1', '.sh', '.tsv', '.lock', '.yml', '.yaml'}
                or PurePosixPath(name).name == 'LICENSE'):
            blob = blob.replace(b'\r\n', b'\n')
        result[name] = blob
    return result


def historical_managed(name):
    if name in {'AGENTS.md', 'UPGRADING.md', 'requirements.txt', 'upgrade_larkdown.py'}:
        return True
    parts = PurePosixPath(name).parts
    if '__pycache__' in parts or name.endswith(('.pyc', '.pyo', '.local.json')):
        return False
    if name.startswith('.agents/config/'):
        return len(parts) == 3 and parts[-1] in PUBLIC_CONFIG | {'upstream.json', LEGACY}
    return name.startswith(('.agents/instructions/', '.agents/skills/'))


@lru_cache(maxsize=None)
def bootstrap_files(tag):
    # These two ZIPs were published with Windows CRLF bytes. Reproduce that
    # immutable contract explicitly, including when CI runs on Linux.
    archive_bytes = git('-c', 'core.autocrlf=true', '-c', 'core.eol=crlf',
                        'archive', '--format=zip', tag)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        return {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}


def tree(tag):
    files = committed_files(tag)
    if 'product/AGENTS.md' in files:
        return package_files(files)
    if tag in BOOTSTRAP_TAGS:
        return {name: blob for name, blob in bootstrap_files(tag).items() if historical_managed(name)}
    return {name: blob for name, blob in files.items() if historical_managed(name)}


def version_tuple(value):
    if not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError(f'Only stable semantic release versions are supported: {value}')
    return tuple(int(part) for part in value.split('.'))


def historical_tags():
    current = json.loads((ROOT / PROVENANCE).read_bytes())['version']
    prior = [t for t in git('tag', '--list', 'v*').decode().splitlines()
             if re.fullmatch(r'v\d+\.\d+\.\d+', t) and version_tuple(t[1:]) < version_tuple(current)]
    if not set(BOOTSTRAP_TAGS) <= set(prior):
        raise ValueError('Published v0.1.0 and v0.2.0 tag baselines are required')
    return sorted(prior, key=lambda t: version_tuple(t[1:]))


def previous_releases():
    catalog = {}
    pinned = json.loads((ROOT / LEGACY_SOURCE).read_bytes())['releases']
    for tag in historical_tags():
        committed = committed_files(tag)
        if tag in BOOTSTRAP_TAGS:
            entry = copy.deepcopy(pinned.get(tag[1:]))
            if not entry or sha(entry['merge_base']['AGENTS.md'].encode()) != entry['managed_files']['AGENTS.md']:
                raise ValueError(f'Published Windows baseline is missing or invalid: {tag}')
        else:
            files = tree(tag)
            entry = {'project_schema_version': json.loads(files['.agents/config/project-layout.json'])['schema_version'],
                     'managed_files': {name: sha(blob) for name, blob in sorted(files.items())},
                     'merge_base': {'AGENTS.md': files['AGENTS.md'].decode('utf-8-sig')}}
        if 'product/AGENTS.md' not in committed and 'README.md' in committed:
            blob = committed['README.md']
            if tag in BOOTSTRAP_TAGS:
                blob = bootstrap_files(tag)['README.md']
            entry['unmanaged_files'] = {'README.md': sha(blob)}
        catalog[tag[1:]] = entry
    return {'schema_version': 1, 'releases': catalog}


def desired_manifest(files=None, legacy=None):
    files = files if files is not None else working_files()
    product = check_boundaries(files)
    legacy = legacy if legacy is not None else previous_releases()
    maintenance = {name[len('tools/'):]: files[name] for name in MAINTENANCE_SOURCES
                   if name != RELEASE_MANIFEST}
    return {'schema_version': 1, 'distribution_schema_version': 4, 'project': 'laRkdown',
            'version': json.loads(files[PROVENANCE])['version'],
            'project_schema_version': json.loads(product['.agents/config/project-layout.json'])['schema_version'],
            'supported_from': sorted(legacy['releases']),
            'managed_files': {name: sha(blob) for name, blob in sorted(product.items())},
            'maintenance_files': {name: sha(blob) for name, blob in sorted(maintenance.items())}}


def prepare():
    legacy = previous_releases()
    (ROOT / LEGACY_SOURCE).write_bytes(encoded(legacy))
    (ROOT / RELEASE_MANIFEST).write_bytes(encoded(desired_manifest(legacy=legacy)))
    return ROOT / RELEASE_MANIFEST


def check(files=None):
    files = files if files is not None else working_files()
    for name in files:
        relative = name.removeprefix('product/')
        path = PurePosixPath(relative)
        if (relative.startswith(PRIVATE_ROOTS) or path.name in {'feishu.json', 'feishu-documents.json', '.env'}
                or path.name.endswith('.local.json') or '__pycache__' in path.parts
                or path.suffix in {'.pyc', '.pyo'}):
            raise ValueError(f'Private or generated file is tracked for public release: {name}')
    legacy = previous_releases()
    if files.get(LEGACY_SOURCE) != encoded(legacy):
        raise ValueError('Legacy baseline catalog is stale; run --prepare')
    info = desired_manifest(files, legacy)
    if files.get(RELEASE_MANIFEST) != encoded(info):
        raise ValueError('Release manifest is stale; run --prepare')
    check_user_guide(files, info['version'])
    check_version_notes(files, info['version'])
    if not MAINTENANCE_SOURCES <= files.keys():
        raise ValueError('Release maintenance directory is incomplete')
    if info['project_schema_version'] != 1:
        raise ValueError('Project schema changed: supply and test a migration before release')
    if historical_tags()[-1][1:] not in info['supported_from']:
        raise ValueError('Release does not support the previous published version')
    return {'ok': True, 'version': info['version'], 'managed_files': len(info['managed_files']),
            'supported_from': info['supported_from'], 'maintenance_delivery': 'sibling-directory'}


def write_zip(output, root_name, files):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, blob in sorted(files.items()):
            archive.writestr((root_name + '/' if root_name else '') + name, blob)
    digest = sha(output.read_bytes())
    checksum = output.with_name(output.name + '.sha256')
    checksum.write_text(f'{digest}  {output.name}\n', encoding='ascii')
    return {'asset': str(output), 'sha256': digest, 'checksum_asset': str(checksum), 'archive_members': len(files)}


def build(output: Path, preview=False):
    if not preview and git('status', '--porcelain').strip():
        raise ValueError('Commit all public release changes before creating a release ZIP; use --preview-build for review')
    files = working_files() if preview else committed_files('HEAD')
    result = check(files)
    product = package_files(files)
    maintenance = {name[len('tools/'):]: files[name] for name in MAINTENANCE_SOURCES}
    members = {'laRkdown/' + name: blob for name, blob in product.items()}
    members.update({'maintenance/' + name: blob for name, blob in maintenance.items()})
    bundle = write_zip(output, '', members)
    Release(output)
    return {**result, 'preview': preview, 'bundle': bundle,
            'research_files': len(product), 'maintenance_files': len(maintenance)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--build', type=Path, metavar='ZIP_PATH')
    mode.add_argument('--preview-build', type=Path, metavar='ZIP_PATH')
    args = parser.parse_args()
    try:
        if args.prepare:
            result = {'prepared': str(prepare())}
        elif args.check:
            result = check()
        else:
            result = build(args.preview_build or args.build, preview=bool(args.preview_build))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
