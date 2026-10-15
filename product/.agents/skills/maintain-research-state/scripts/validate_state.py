"""Validate research relationships in complete native-document fetch snapshots."""
from pathlib import Path
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from feishu_bridge import parse_xml, ID_RE

def validate(snapshots, changed=None):
    issues, entries, documents = [], {}, {}
    for snapshot in snapshots:
        document = snapshot['data']['document']
        doc_id = document['document_id']
        if doc_id in documents:
            issues.append({'code': 'duplicate-document-snapshot', 'document': doc_id})
            continue
        try:
            tree = parse_xml(document['content'])
        except (ValueError, ET.ParseError) as error:
            issues.append({'code': 'invalid-native-content', 'document': doc_id, 'detail': str(error)})
            continue
        if tree.find('fragment') is not None:
            issues.append({'code': 'partial-snapshot', 'document': doc_id})
            continue
        title = ''.join(tree.find('title').itertext()) if tree.find('title') is not None else doc_id
        key = next((name for name in ['CURRENT_STATE', 'RESEARCH_QUESTIONS', 'PROJECT_STORY'] if name in title), None) or title
        target = not changed or any(name in key or name == doc_id for name in changed)
        documents[doc_id] = key
        current = None
        for node in tree:
            text = ''.join(node.itertext()).strip()
            heading = re.fullmatch(r'h[1-6]|title', node.tag)
            match = ID_RE.match(text) if heading else None
            if match:
                entry_id = match[0]
                if entry_id.endswith('-000'): issues.append({'code': 'zero-id', 'entry': entry_id})
                if entry_id in entries: issues.append({'code': 'duplicate-research-id', 'entry': entry_id})
                current = {'id': entry_id, 'doc_id': doc_id, 'block_id': node.get('block-id') or node.get('id'), 'nodes': [node], 'target': target, 'level': int(node.tag[1:]) if node.tag != 'title' else 0}
                entries[entry_id] = current
            elif heading and current and node.tag != 'title' and int(node.tag[1:]) <= current['level']:
                current = None
            elif current:
                current['nodes'].append(node)
    if changed and not any(any(name in key or name == doc_id for name in changed) for doc_id, key in documents.items()):
        issues.append({'code': 'changed-document-not-in-snapshots'})
    for entry_id, entry in entries.items():
        links = []
        text = ' '.join(''.join(node.itertext()) for node in entry['nodes'])
        for node in entry['nodes']:
            for link in node.iter('a'):
                label = ''.join(link.itertext()).strip()
                if ID_RE.fullmatch(label): links.append((label, link.get('href', '')))
        linked_ids = {label for label, _ in links}
        entry['linked_ids'] = linked_ids
        if not entry['target']: continue
        for label, href in links:
            if label not in entries:
                issues.append({'code': 'unresolved-research-link', 'entry': entry_id, 'target': label})
                continue
            target = entries[label]
            if not href.startswith('https://'):
                issues.append({'code': 'invalid-native-link', 'entry': entry_id, 'target': label})
                continue
            if '/docx/' in href and href.split('/docx/', 1)[1].split('#')[0].split('?')[0] != target['doc_id']:
                issues.append({'code': 'wrong-document-link', 'entry': entry_id, 'target': label})
            if '#' in href and target['block_id'] and href.rsplit('#', 1)[1] != target['block_id']:
                issues.append({'code': 'stale-block-link', 'entry': entry_id, 'target': label})
        if entry_id.startswith('CON-'):
            if not any(value.startswith('OBS-') for value in linked_ids): issues.append({'code': 'con-without-obs', 'entry': entry_id})
            if not any(level in text for level in ['初步', '中等', '较强', '充分']): issues.append({'code': 'con-without-evidence-level', 'entry': entry_id})
        if entry_id.startswith('HYP-'):
            if not any(word in text.lower() for word in ['未验证', '待验证', '假设', 'unverified', 'hypothesis']): issues.append({'code': 'hyp-without-unverified-label', 'entry': entry_id})
            if not any(value.startswith(('OBS-', 'RQ-')) for value in linked_ids): issues.append({'code': 'hyp-without-target', 'entry': entry_id})
        if entry_id.startswith('SOL-'):
            if len([value for value in linked_ids if value.startswith('RQ-')]) != 1: issues.append({'code': 'sol-primary-rq', 'entry': entry_id})
            for field in ['related_rq', 'status', 'date', 'core_route']:
                if field not in text: issues.append({'code': 'sol-missing-field', 'entry': entry_id, 'field': field})
    for entry_id, entry in entries.items():
        if not entry['target'] or not entry_id.startswith('SOL-'): continue
        for rq in entry.get('linked_ids', set()):
            if rq.startswith('RQ-') and rq in entries and entry_id not in entries[rq].get('linked_ids', set()):
                issues.append({'code': 'missing-rq-sol-backlink', 'entry': entry_id, 'rq': rq})
    return {'ok': not issues, 'entries': len(entries), 'documents': len(documents), 'issues': issues, 'limits': 'Structural checks only; source coverage and scientific evidence require review'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, action='append', required=True)
    parser.add_argument('--changed', action='append')
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--registry', type=Path, default=Path('.agents/config/feishu-documents.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.full and not args.changed: parser.error('Select --changed logical-key(s), or --full with complete coverage')
    try:
        snapshots = [json.loads(path.read_text(encoding='utf-8-sig')) for path in args.snapshot]
        report = validate(snapshots, None if args.full else set(args.changed))
        if args.full:
            registry = json.loads(args.registry.read_text(encoding='utf-8-sig'))
            required = {entry['document_id'] for key, entry in registry['documents'].items() if key in {'CURRENT_STATE', 'RESEARCH_QUESTIONS', 'PROJECT_STORY'} or key.startswith('SOL-')}
            supplied = {snapshot['data']['document']['document_id'] for snapshot in snapshots}
            if not required or not required.issubset(supplied):
                report['issues'].append({'code': 'full-audit-coverage-not-established'})
                report['ok'] = False
    except (KeyError, ValueError, OSError, ET.ParseError) as error:
        report = {'ok': False, 'issues': [{'code': 'invalid-snapshot', 'detail': str(error)}]}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + '\n', encoding='utf-8')
    print(text)
    return 0 if report['ok'] else 1

if __name__ == '__main__': sys.exit(main())
