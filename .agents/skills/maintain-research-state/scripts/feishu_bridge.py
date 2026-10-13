"""Native Feishu document operations via the official lark-cli, without shell interpolation."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ID_RE = re.compile(r'^(OBS|CON|HYP|RQ|SOL)-\d{3}\b')

def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def local(root: Path, name: str | Path) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path must remain within the specified project root')
    return path

def parse_xml(text: str):
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('External entities and DOCTYPE are not document content')
    if '[[' in text or re.search(r'\^(?:obs|con|hyp|rq|sol)-\d{3}', text, re.I) or '[!warning]' in text:
        raise ValueError('Unsupported editor-specific document syntax')
    return ET.fromstring('<document>' + text + '</document>')

def text_blocks(text: str):
    return [''.join(e.itertext()).strip() for e in parse_xml(text) if e.tag in {'title', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} and ''.join(e.itertext()).strip()]

def cli_prefix():
    executable = shutil.which('lark-cli')
    if not executable:
        raise RuntimeError('Official lark-cli is not installed; follow the project Feishu workflow')
    if os.name == 'nt' and Path(executable).suffix.lower() in {'.cmd', '.bat', '.ps1'}:
        runner = Path(executable).parent / 'node_modules/@larksuite/cli/scripts/run.js'
        node = shutil.which('node')
        if not runner.is_file() or not node:
            raise RuntimeError('Cannot resolve the official npm CLI runner; configure an executable installation')
        return [node, str(runner)]
    return [executable]

def call(args: list[str], root: Path, content: str | None = None):
    env = dict(os.environ, LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1')
    process = subprocess.run(cli_prefix() + args, cwd=root, input=content, text=True, encoding='utf-8',
                             capture_output=True, env=env, timeout=180)
    stream = process.stdout if process.returncode == 0 else process.stderr
    try:
        response = json.loads(stream)
    except json.JSONDecodeError:
        raise RuntimeError(f'CLI returned non-JSON output (exit {process.returncode}); inspect the operation locally')
    if process.returncode or response.get('ok') is not True:
        error = response.get('error', {})
        # Never log token-bearing raw errors or auto-retry a write.
        raise RuntimeError(f"CLI operation stopped (exit {process.returncode}, {error.get('type', 'unknown')}/{error.get('subtype', 'unknown')}): {error.get('message', 'see current CLI help')}")
    return response

class Bridge:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.registry_path = local(self.root, '.agents/config/feishu-documents.json')
        self.cache = local(self.root, '.work/feishu')
        self.registry = json.loads(self.registry_path.read_text(encoding='utf-8')) if self.registry_path.exists() else {'schema_version': 1, 'documents': {}, 'reserved_ids': []}
        config_path = self.root / '.agents/config/feishu.json'
        self.config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}

    def save(self):
        dump(self.registry_path, self.registry)

    def fetch(self, key: str, doc: str | None = None, scope: str | None = None, keyword: str | None = None, block_id: str | None = None):
        doc = doc or self.registry['documents'][key]['document_id']
        args = ['docs', '+fetch', '--as', 'user', '--doc', doc, '--doc-format', 'xml', '--detail', 'full']
        if scope:
            args += ['--scope', scope]
        if keyword:
            args += ['--keyword', keyword]
        if block_id:
            args += ['--start-block-id', block_id]
        response = call(args, self.root)
        document = response['data']['document']
        suffix = '.partial' if scope else ''
        dump(self.cache / (key + suffix + '.fetch.json'), response)
        content = document['content']
        local(self.root, self.cache / (key + suffix + '.xml')).write_text(content, encoding='utf-8')
        if not scope:
            blocks = {}
            for element in parse_xml(content).iter():
                if re.fullmatch(r'h[1-6]|title', element.tag):
                    match = ID_RE.match(''.join(element.itertext()).strip())
                    if match:
                        blocks[match[0]] = element.get('block-id') or element.get('id')
            # Preserve server-provided URLs only, or a previously verified URL for the same ID.
            old = self.registry['documents'].get(key, {})
            same = old.get('document_id') == document.get('document_id')
            url = document.get('url') or (old.get('url') if same else None)
            if not url and doc.startswith('https://'):
                url = doc.split('#')[0]
            self.registry['documents'][key] = {**old,
                'document_id': document['document_id'], 'url': url,
                'revision_id': document['revision_id'], 'fetched_at': timestamp(),
                'snapshot': (self.cache / (key + '.fetch.json')).relative_to(self.root).as_posix(), 'entries': blocks,
            }
            self.registry['reserved_ids'] = sorted(set(self.registry.get('reserved_ids', [])) | set(blocks))
            self.save()
        return response

    def create(self, key: str, xml_path: Path, parent_token: str | None = None, dry_run: bool = False):
        if key in self.registry['documents']:
            raise ValueError(f'{key} is already registered; use fetch/patch, not create')
        pending = self.cache / 'pending' / (key + '.json')
        if pending.exists():
            raise ValueError(f'{key} has an unresolved create attempt; find and bind the existing document or verify no document was created before clearing pending')
        xml_path = local(self.root, xml_path)
        content = xml_path.read_text(encoding='utf-8-sig')
        tree = parse_xml(content)
        if len(tree.findall('title')) != 1 or tree[0].tag != 'title':
            raise ValueError('A new native document must start with exactly one title')
        file_arg = '@' + xml_path.relative_to(self.root).as_posix()
        preview = call(['docs', '+script', '--command', 'parse', '--as', 'user', '--content', file_arg], self.root)
        assessment = preview.get('data', {}).get('assessment', {})
        if assessment.get('status') not in {None, 'passed'}:
            raise ValueError('CLI draft assessment did not pass')
        args = ['docs', '+create', '--as', 'user', '--doc-format', 'xml', '--content', file_arg]
        parent = parent_token or self.config.get('parent_token')
        if parent:
            args += ['--parent-token', parent]
        if dry_run:
            return call(args + ['--dry-run'], self.root)
        pending.parent.mkdir(parents=True, exist_ok=True)
        with pending.open('x', encoding='utf-8') as guard:
            json.dump({'key': key, 'started_at': timestamp(), 'xml_sha256': hashlib.sha256(content.encode()).hexdigest()}, guard)
        response = call(args, self.root)
        # Save the actual response before readback: an uncertain read must never trigger another create.
        dump(self.cache / 'operations' / (uuid.uuid4().hex + '.create.json'), response)
        document = response['data']['document']
        self.registry['documents'][key] = {'document_id': document['document_id'], 'url': document['url'], 'revision_id': document['revision_id'], 'created_at': timestamp(), 'authored_sha256': hashlib.sha256(content.encode()).hexdigest()}
        self.save()
        warnings = response.get('data', {}).get('warnings', [])
        pending.unlink()
        readback = self.fetch(key)
        actual_tree = parse_xml(readback['data']['document']['content'])
        actual = ''.join(actual_tree.itertext())
        missing = [block for block in text_blocks(content) if block not in actual]
        if missing:
            raise RuntimeError(f'Document {key} exists but {len(missing)} authored text blocks were not verified; repair that document')
        if len(list(actual_tree.iter('img'))) < len(list(tree.iter('img'))):
            raise RuntimeError(f'Document {key} exists but authored image blocks were not all verified; repair that document')
        if warnings:
            raise RuntimeError(f'Document {key} exists with {len(warnings)} server warnings; inspect saved response and repair that document')
        return {'ok': True, 'document': self.registry['documents'][key]}

    def patch(self, key: str, command: str, xml_path: Path, revision: int, block_id: str | None, pattern: str | None, dry_run: bool):
        current = self.fetch(key)['data']['document']
        if current['revision_id'] != revision:
            raise ValueError('Revision changed; merge the current Feishu document before editing')
        content = local(self.root, xml_path).read_text(encoding='utf-8-sig')
        if command != 'str_replace':
            parse_xml(content)
        if command in {'block_replace', 'block_insert_after'} and not block_id:
            raise ValueError('Block operation requires a freshly fetched block ID')
        if command == 'str_replace' and not pattern:
            raise ValueError('str_replace requires the observed existing pattern')
        args = ['docs', '+update', '--as', 'user', '--doc', current['document_id'], '--doc-format', 'xml',
                '--command', command, '--revision-id', str(revision), '--content', '-']
        if block_id:
            args += ['--block-id', block_id]
        if pattern:
            args += ['--pattern', pattern]
        if dry_run:
            return call(args + ['--dry-run'], self.root, content)
        response = call(args, self.root, content)
        dump(self.cache / 'operations' / (uuid.uuid4().hex + '.patch.json'), response)
        self.fetch(key)
        if response.get('data', {}).get('warnings'):
            raise RuntimeError('Update returned warnings; inspect saved response and fetched content')
        return {'ok': True, 'document': self.registry['documents'][key], 'verification_required': 'Review affected content and resource blocks in saved full snapshot'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('preflight')
    for action in ['create', 'bind', 'fetch', 'patch']:
        sub = commands.add_parser(action)
        sub.add_argument('--key', required=True)
        if action == 'bind': sub.add_argument('--doc', required=True)
        if action == 'fetch':
            sub.add_argument('--scope', choices=['outline', 'keyword', 'section'])
            sub.add_argument('--keyword')
            sub.add_argument('--block-id')
        if action in {'create', 'patch'}:
            sub.add_argument('--xml', required=True, type=Path)
            sub.add_argument('--dry-run', action='store_true')
        if action == 'create': sub.add_argument('--parent-token')
        if action == 'patch':
            sub.add_argument('--command', required=True, choices=['append', 'str_replace', 'block_replace', 'block_insert_after'])
            sub.add_argument('--revision', required=True, type=int)
            sub.add_argument('--block-id')
            sub.add_argument('--pattern')
    args = parser.parse_args()
    bridge = Bridge(args.root)
    try:
        if args.action == 'preflight':
            process = subprocess.run(cli_prefix() + ['auth', 'status', '--json'], capture_output=True, text=True, encoding='utf-8', timeout=30)
            status = json.loads(process.stdout)
            user = status.get('identities', {}).get('user', {})
            result = {'ok': process.returncode == 0 and user.get('available') is True, 'identity': 'user', 'user_status': user.get('status'), 'token_status': user.get('tokenStatus')}
        else:
            if not re.fullmatch(r'[A-Za-z0-9_-]+', args.key): raise ValueError('Invalid document key')
            if args.action == 'create': result = bridge.create(args.key, args.xml, args.parent_token, args.dry_run)
            elif args.action == 'bind':
                if args.key in bridge.registry['documents']: raise ValueError('Key already bound; preserve its existing resource identity')
                bridge.fetch(args.key, args.doc)
                pending = bridge.cache / 'pending' / (args.key + '.json')
                if pending.exists(): pending.unlink()
                result = {'ok': True, 'document': bridge.registry['documents'][args.key]}
            elif args.action == 'fetch':
                response = bridge.fetch(args.key, scope=args.scope, keyword=args.keyword, block_id=args.block_id)
                result = {'ok': True, 'document_id': response['data']['document']['document_id'], 'snapshot_dir': str(bridge.cache)}
            else: result = bridge.patch(args.key, args.command, args.xml, args.revision, args.block_id, args.pattern, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('ok') else 1
    except (ValueError, KeyError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
