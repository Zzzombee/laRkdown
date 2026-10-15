"""Derive six Feishu Base tables from three native documents; never write source docs."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'maintain-research-state/scripts'))
from feishu_bridge import Bridge, call, cli_prefix, dump, local, parse_xml, timestamp, research_workspace

DOCS = ('CURRENT_STATE', 'RESEARCH_QUESTIONS', 'PROJECT_STORY')
TABLES = ('项目概览', '实验观察OBS', '结论与假设', '研究问题RQ', '关键参考文献', '近期优先事项')
ID = re.compile(r'^(OBS|CON|HYP|RQ)-\d{3}\b')
REF = re.compile(r'\b(?:OBS|CON|HYP|RQ|SOL)-\d{3}\b')
TASK_HEAD = re.compile(r'^(?:\d+[.、\s]*)?(近期优先事项|近期优先实验|近期任务|下一步)$')
PROTECTED = {'核心发现', '层级', '类型', '分类', '证据强度'}
COMMON = ['同步键', '同步项目', '来源文档', '来源链接', '来源版本', '源内容哈希', '来源语义', '关联编号']
SCALAR = {
    TABLES[0]: ['概要', '原文', '引用', '条目', '内容'],
    TABLES[1]: ['概要', '原文', '引用', '编号', '标题'],
    TABLES[2]: ['概要', '原文', '引用', '编号', '内容', '依据', '源类型', '源证据等级'],
    TABLES[3]: ['概要', '原文', '引用', '编号', '问题', '状态'],
    TABLES[4]: ['概要', '原文', '引用', '文献', '链接', '定位与边界'],
    TABLES[5]: ['概要', '原文', '引用', '优先事项', '关联'],
}
VISIBLE = {
    TABLES[0]: ['概要', '原文', '引用', '归档'],
    TABLES[1]: ['概要', '编号', '原文', '引用', '归档'],
    TABLES[2]: ['概要', '编号', '源类型', '源证据等级', '原文', '引用', '依据', '关联OBS', '关联RQ', '归档'],
    TABLES[3]: ['概要', '编号', '状态', '优先级', '原文', '引用', '关联OBS', '关联结论假设', '归档'],
    TABLES[4]: ['概要', '文献', '链接', '原文', '引用', '序号', '归档'],
    TABLES[5]: ['概要', '原文', '引用', '关联RQ', '序号', '归档'],
}
LINKS = {
    TABLES[2]: {'关联OBS': TABLES[1], '关联RQ': TABLES[3]},
    TABLES[3]: {'关联OBS': TABLES[1], '关联结论假设': TABLES[2]},
    TABLES[5]: {'关联RQ': TABLES[3]},
}

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default

def node_text(node):
    """Keep block boundaries, links and resource markers instead of inventing image contents."""
    if node.tag in {'img', 'source', 'file', 'attachment', 'whiteboard', 'sheet', 'bitable', 'cite', 'synced_reference', 'equation'}:
        return f'[{node.tag}: ' + json.dumps(node.attrib, ensure_ascii=False, sort_keys=True) + ']'
    if node.tag == 'br':
        return '\n'
    text = node.text or ''
    for child in node:
        text += node_text(child)
        text += child.tail or ''
        if child.tag in {'p', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            text += '\n'
        elif child.tag in {'td', 'th'}:
            text += ' | '
    if node.tag == 'a' and node.get('href'):
        text = f'{text} ({node.get("href")})'
    return text.strip() if node.tag not in {'a', 'span', 'b', 'strong', 'em'} else text

META_LINE = re.compile(r'^\s*(?:编号|来源(?:文档|链接|版本)?|引用|参考文献|证据(?:等级|强度)|依据|支持\s*OBS|状态|优先级)\s*(?:[:：]|\|)')
RESOURCE_NAMES = {'img': '图片', 'source': '附件', 'file': '文件', 'attachment': '附件',
                  'whiteboard': '画板', 'sheet': '表格', 'bitable': '多维表格'}


def reading_text(node):
    """Render readable source text without inline URLs or opaque resource tokens."""
    if node.tag in RESOURCE_NAMES:
        return f'〔{RESOURCE_NAMES[node.tag]}：请查看来源文档〕'
    if node.tag in {'cite', 'synced_reference', 'equation'}:
        return f'〔{node.tag}：请查看来源文档〕'
    if node.tag == 'br':
        return '\n'
    text = node.text or ''
    for child in node:
        text += reading_text(child) + (child.tail or '')
        if child.tag in {'p', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            text += '\n'
        elif child.tag in {'td', 'th'}:
            text += ' | '
    return text.strip() if node.tag not in {'a', 'span', 'b', 'strong', 'em'} else text


def clean_content(nodes):
    lines = '\n'.join(reading_text(node) for node in nodes).splitlines()
    return '\n'.join(line.strip(' |\t') for line in lines
                     if line.strip(' |\t') and not META_LINE.match(line)
                     and not re.fullmatch(r'\s*(?:OBS|CON|HYP|RQ|SOL|TASK)-\d{3}\s*', line)).strip()


def citations(nodes):
    items = []
    for node in nodes:
        for element in node.iter():
            if element.tag == 'a' and element.get('href'):
                title = ''.join(element.itertext()).strip()
                items.append(f'{title} — {element.get("href")}' if title else element.get('href'))
        for line in reading_text(node).splitlines():
            if re.match(r'^\s*(?:引用|参考文献)\s*[:：]', line):
                items.append(re.sub(r'^\s*(?:引用|参考文献)\s*[:：]\s*', '', line).strip())
            for found in re.findall(r'\b10\.\d{4,9}/[^\s<>；，。]+', line):
                items.append('DOI: ' + found.rstrip('.,;'))
    return '\n'.join(dict.fromkeys(item for item in items if item))

def label(text, names):
    found = []
    pattern = r'(?:^|\n|\|)\s*(?:' + '|'.join(map(re.escape, names)) + r')\s*(?:[:：]|\|)\s*([^\n|]+)'
    for match in re.finditer(pattern, text):
        found.append(match[1].strip().strip('；;'))
    if len(set(found)) > 1:
        raise ValueError(f'Conflicting explicit metadata: {names}')
    return found[0] if found else ''

def priority(text, ancestors):
    value = label(text, ['优先级', 'priority'])
    if value:
        match = re.fullmatch(r'(P[1-5]|暂缓)', value)
        if not match:
            raise ValueError('Priority must be an explicit P1–P5 or 暂缓; do not coerce source values')
        return [value]
    for ancestor in reversed(ancestors):
        match = re.search(r'(?:^|\s|[：:])P([1-5])\b|^优先级\s*([1-5])(?:\s|$)', ancestor)
        if match:
            return ['P' + (match[1] or match[2])]
        if ancestor.strip() == '暂缓':
            return ['暂缓']
    return []

def normalize_url(url):
    parts = urlsplit(url)
    if parts.scheme not in {'https', 'http'} or not parts.netloc:
        raise ValueError('References need actual HTTP(S) URLs')
    # Never remove semantically meaningful query parameters from non-DOI publisher URLs.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ''))

def ref_key(url):
    normalized = normalize_url(url)
    parts = urlsplit(normalized)
    if parts.netloc in {'doi.org', 'dx.doi.org'}:
        return 'DOI:' + parts.path.strip('/').lower()
    return 'URL:' + normalized

def sections(xml, selectors):
    tree = parse_xml(xml)
    if any(n.tag == 'fragment' for n in tree.iter()):
        raise ValueError('Partial document cannot support synchronization')
    if any(n.tag in {'synced_reference', 'excerpt'} for n in tree.iter()):
        raise ValueError('Unresolved synchronized content/excerpts cannot support complete extraction or archive decisions')
    # DocxXML can contain blockquote/list/table children; headings are normally top-level.
    if any(re.fullmatch(r'h[1-6]', n.tag) for top in tree for n in list(top.iter())[1:]):
        raise ValueError('Nested headings need an explicit native-document extraction adapter')
    nodes = list(tree)
    groups, stack, used = [], [], set()
    leading = []
    for node in nodes:
        if re.fullmatch(r'h[1-6]', node.tag):
            break
        if node.tag != 'title' and not selectors.get(node.get('id') or node.get('block-id')):
            leading.append(node)
    if leading:
        groups.append({'title': '文档说明', 'ancestors': [], 'nodes': leading,
                       'block': leading[0].get('block-id') or leading[0].get('id') or '',
                       'selector': {'role': 'overview'}, 'heading': False})
    i = 0
    while i < len(nodes):
        node = nodes[i]
        block = node.get('block-id') or node.get('id') or ''
        heading = re.fullmatch(r'h([1-6])', node.tag)
        selected = selectors.get(block)
        if node.tag == 'title':
            i += 1
            continue
        if not heading and not selected:
            # Leading metadata is not a research entry; detect hidden IDs rather than dropping them.
            if ID.match(''.join(node.itertext()).strip()):
                raise ValueError(f'Research ID outside a heading needs selector for block {block}')
            i += 1
            continue
        title = ''.join(node.itertext()).strip()
        if heading:
            level = int(heading[1])
            while stack and stack[-1][0] >= level:
                stack.pop()
            ancestors = [x[1] for x in stack]
            end = i + 1
            while end < len(nodes):
                nxt = re.fullmatch(r'h([1-6])', nodes[end].tag)
                if nxt and int(nxt[1]) <= level:
                    break
                end += 1
            # Each ordinary section contains only its own body. Research entries include subheadings.
            direct_end = i + 1
            while direct_end < end and not re.fullmatch(r'h[1-6]', nodes[direct_end].tag):
                direct_end += 1
            is_entry = ID.match(title) or (selected and selected.get('role') == 'entry')
            body = nodes[i:end if is_entry else direct_end]
            stack.append((level, title))
        else:
            ancestors, end, body = [], i + 1, [node]
            is_entry = selected and selected.get('role') == 'entry'
        if selected:
            used.add(block)
        groups.append({'title': title, 'ancestors': ancestors, 'nodes': body,
                       'block': block, 'selector': selected or {}, 'heading': bool(heading)})
        if is_entry:
            # A research entry nested within another entry is invalid, not silently swallowed.
            for sub in body[1:]:
                if re.fullmatch(r'h[1-6]', sub.tag) and ID.match(''.join(sub.itertext()).strip()):
                    raise ValueError('Nested research entries must be separate sibling headings')
            i = end
        else:
            i += 1
    if set(selectors) - used:
        raise ValueError('Selector block IDs are stale or do not identify top-level source blocks')
    return groups

def compile_dataset(snapshots, bindings, selectors=None):
    if set(snapshots) != set(DOCS):
        raise ValueError('All three complete source documents are required')
    result = {'schema_version': 1, 'sources': {}, 'tables': {t: [] for t in TABLES}, 'warnings': []}
    seen_ids, doc_ids = set(), set()
    for key in DOCS:
        envelope = snapshots[key]
        doc = envelope.get('data', {}).get('document', {})
        if envelope.get('ok') is not True or not all(x in doc for x in ('document_id', 'revision_id', 'content')):
            raise ValueError('Fetch did not return a complete versioned native document')
        if envelope.get('data', {}).get('warnings') or doc.get('has_more') or doc.get('is_partial'):
            raise ValueError('Source fetch has warnings or partial content; inspect before sync')
        if doc['document_id'] in doc_ids:
            raise ValueError('Three source bindings must identify different documents')
        doc_ids.add(doc['document_id'])
        url = doc.get('url') or bindings[key]
        if not url.startswith('https://'):
            raise ValueError('A verified native document URL is required')
        url = url.split('#')[0]
        result['sources'][key] = {'document_id': doc['document_id'], 'revision_id': doc['revision_id'], 'url': url}
        groups = sections(doc['content'], (selectors or {}).get(key, {}))
        for group in groups:
            chosen = group['selector']
            role = chosen.get('role', '')
            if role and role not in {'entry', 'overview', 'task', 'references', 'ignore'}:
                raise ValueError('Unknown selector role')
            if role == 'ignore':
                continue
            nodes, title = group['nodes'], group['title']
            text = '\n'.join(node_text(n) for n in nodes).strip()
            body_text = '\n'.join(node_text(n) for n in nodes[1:]).strip() if group['heading'] else text
            body_nodes = nodes[1:] if group['heading'] else nodes
            readable = clean_content(body_nodes)
            references = citations(body_nodes)
            identity = chosen.get('key') or (ID.match(title)[0] if ID.match(title) else '')
            match = ID.fullmatch(identity)
            if role == 'entry' and not match:
                raise ValueError('Entry selector requires an existing stable research ID')
            source_link = url + ('#' + group['block'] if group['block'] else '')
            base = {'来源文档': key, '来源链接': source_link, '来源版本': str(doc['revision_id']),
                    '归档': False, '关联编号': '\n'.join(sorted(set(REF.findall(text)) - {identity}))}
            if match:
                if identity in seen_ids:
                    raise ValueError(f'Duplicate stable research ID: {identity}')
                seen_ids.add(identity)
                prefix = match[1]
                if (key == DOCS[0] and prefix not in {'OBS', 'CON', 'HYP'}) or (key == DOCS[1] and prefix != 'RQ') or key == DOCS[2]:
                    raise ValueError('Research entry appears in the wrong authority document')
                table = TABLES[1] if prefix == 'OBS' else TABLES[3] if prefix == 'RQ' else TABLES[2]
                short_title = chosen.get('title') or re.sub(r'^(?:OBS|CON|HYP|RQ)-\d{3}\s*[—–:：-]?\s*', '', title)
                if not short_title:
                    short_title = readable.split('\n', 1)[0].split('。', 1)[0][:100] or identity
                fields = {**base, '同步键': identity, '编号': identity, '概要': short_title,
                          '原文': readable, '引用': references,
                          '来源语义': '研究问题原文' if prefix == 'RQ' else '科研状态摘录'}
                if prefix == 'OBS':
                    fields['标题'] = short_title
                elif prefix == 'RQ':
                    fields.update(问题=short_title, 状态=label(body_text, ['状态', 'status']),
                                  优先级=priority(body_text, group['ancestors']))
                else:
                    fields.update(内容=short_title, 依据=label(body_text, ['依据', '支持OBS', '支持 OBS']),
                                  源类型='结论' if prefix == 'CON' else '工作假设',
                                  源证据等级=label(body_text, ['证据等级', '证据强度']))
                result['tables'][table].append(fields)
            elif role == 'task' or TASK_HEAD.fullmatch(title):
                task_nodes = nodes[1:] if group['heading'] else nodes
                for node in task_nodes:
                    items = list(node) if node.tag in {'ul', 'ol'} else [node]
                    for item in items:
                        original = node_text(item).strip()
                        if not original:
                            continue
                        task_id = re.match(r'^TASK-\d{3}\b', original)
                        task_key = chosen.get('key')
                        if task_key and (len(task_nodes) != 1 or len(items) != 1):
                            raise ValueError('A task selector with a fixed key must identify a single task block')
                        fields = {**base, '同步键': task_key or (task_id[0] if task_id else 'TASK:' + digest(original)),
                                  '概要': re.sub(r'^TASK-\d{3}\s*', '', original).split('。', 1)[0][:100],
                                  '原文': re.sub(r'^TASK-\d{3}\s*', '', clean_content([item])),
                                  '引用': citations([item]),
                                  '优先事项': original, '关联': '\n'.join(sorted(set(REF.findall(original)))),
                                  '关联编号': '\n'.join(sorted(set(REF.findall(original)))), '来源语义': '原文任务'}
                        result['tables'][TABLES[5]].append(fields)
            elif body_text and role != 'references':
                # Group headings such as OBS are containers, not separate summaries.
                if key == DOCS[0] and re.search(r'\b(?:OBS|CON|HYP)\b', title) and role != 'overview':
                    raise ValueError(f'Unstructured content under {title}; use source block selectors')
                fields = {**base, '同步键': chosen.get('key') or 'SECTION:' + key + ':' + '/'.join(group['ancestors'] + [title]),
                          '概要': chosen.get('title') or title, '原文': readable, '引用': references,
                          '条目': chosen.get('title') or title, '内容': body_text,
                          '来源语义': '目标论文叙事' if key == DOCS[2] else '研究问题原文' if key == DOCS[1] else '科研状态摘录'}
                result['tables'][TABLES[0]].append(fields)
            if key == DOCS[2] or role == 'references':
                ref_nodes = [sub for n in nodes for sub in n.iter() if sub.tag in {'p', 'li', 'td'}]
                for paragraph in ref_nodes:
                    context = node_text(paragraph)
                    urls = [(a.get('href', ''), ''.join(a.itertext()).strip()) for a in paragraph.iter('a')]
                    urls += [('https://doi.org/' + m[0].rstrip('.,;；。)'), m[0]) for m in re.finditer(r'\b10\.\d{4,9}/[^\s<>]+', ''.join(paragraph.itertext()))]
                    for href, name in urls:
                        if not href.startswith(('https://', 'http://')):
                            continue
                        host = urlsplit(href).netloc.lower()
                        if host.endswith(('feishu.cn', 'larkoffice.com', 'larksuite.com')):
                            continue
                        literature_context = role == 'references' or any('文献' in x or '参考' in x for x in group['ancestors'] + [title])
                        if host not in {'doi.org', 'dx.doi.org'} and not literature_context:
                            continue
                        rkey = ref_key(href)
                        existing = next((f for f in result['tables'][TABLES[4]] if f['同步键'] == rkey), None)
                        if existing:
                            if context not in existing['定位与边界'].split('\n\n'):
                                existing['定位与边界'] += '\n\n' + context
                            continue
                        result['tables'][TABLES[4]].append({**base, '同步键': rkey, '概要': name or href,
                            '原文': clean_content([paragraph]), '引用': normalize_url(href),
                            '文献': name or href, '链接': normalize_url(href),
                            '定位与边界': context, '来源语义': '原文引文'})
    for table, rows in result['tables'].items():
        if len({r['同步键'] for r in rows}) != len(rows):
            raise ValueError(f'Duplicate synchronization key in {table}')
        for index, row in enumerate(rows, 1):
            if table in {TABLES[4], TABLES[5]}:
                row['序号'] = index
            row['源内容哈希'] = digest({k: v for k, v in row.items() if k not in {'来源版本', '序号'}})
    known = seen_ids
    result['warnings'] = sorted({ref for rows in result['tables'].values() for row in rows
                                 for ref in REF.findall(row['关联编号']) if ref not in known})
    return result

def schema(table, links=False):
    fields = [{'name': name, 'type': 'text'} for name in SCALAR[table] + COMMON]
    fields.append({'name': '归档', 'type': 'checkbox'})
    if table == TABLES[3]:
        fields.append({'name': '优先级', 'type': 'select', 'multiple': False,
                       'options': [{'name': n} for n in ['P1', 'P2', 'P3', 'P4', 'P5', '暂缓']]})
    if table in {TABLES[4], TABLES[5]}:
        fields.append({'name': '序号', 'type': 'number'})
    if links:
        fields += [{'name': name, 'type': 'link', 'link_table': target, 'bidirectional': False}
                   for name, target in LINKS.get(table, {}).items()]
    return fields

def canon(value):
    if isinstance(value, list):
        return sorted(({'id': x['id']} if isinstance(x, dict) and 'id' in x else x for x in value), key=str)
    return '' if value is None else value

def same(actual, expected):
    return all(canon(actual.get(k)) == canon(v) for k, v in expected.items())

def prepare_plan(dataset, current, state, owner):
    plan = {'tables': {}, 'conflicts': []}
    for table in TABLES:
        live, by_id = {}, {}
        desired = {r['同步键']: {**r, '同步项目': owner} for r in dataset['tables'][table]}
        for row in current[table]:
            rid, key = row['record_id'], row.get('同步键')
            if rid in by_id:
                raise ValueError('Duplicate record_id in a complete table read')
            by_id[rid] = row
            if key:
                if key in live:
                    raise ValueError(f'Duplicate synchronization key in target {table}')
                live[key] = row
            legacy_collision = row.get('编号') in desired
            if table == TABLES[4] and row.get('链接'):
                legacy_collision = ref_key(row['链接']) in desired
            if table == TABLES[0]:
                legacy_collision = any(row.get('条目') == f['条目'] for f in desired.values())
            if table == TABLES[5]:
                legacy_collision = any(row.get('优先事项') == f['优先事项'] for f in desired.values())
            if row.get('同步项目') != owner and (key in desired or legacy_collision):
                plan['conflicts'].append(f'{table}: unmanaged record collides with source key')
        baseline = state.get('tables', {}).get(table, {})
        operations, counts = [], dict(create=0, update=0, archive=0, unchanged=0)
        for key, fields in desired.items():
            row, old = live.get(key), baseline.get(key)
            if old:
                fields = {**{k: v for k, v in old['fields'].items() if k in LINKS.get(table, {})}, **fields}
            if row and (not old or row['record_id'] != old['record_id'] or row.get('同步项目') != owner):
                plan['conflicts'].append(f'{table}/{key}: existing record has no matching verified baseline')
                continue
            if old and not row:
                plan['conflicts'].append(f'{table}/{key}: managed record was removed or synchronization key edited')
                continue
            if row and not same(row, old['fields']):
                plan['conflicts'].append(f'{table}/{key}: managed fields edited in Base')
                continue
            comparison = {k: v for k, v in fields.items() if k != '来源版本'}
            if row and same(row, comparison):
                counts['unchanged'] += 1
                continue
            action = 'update' if row else 'create'
            counts[action] += 1
            operations.append({'key': key, 'action': action, 'record_id': row['record_id'] if row else None,
                               'fields': fields, 'expected': old['fields'] if old else None})
        for key, old in baseline.items():
            if key in desired:
                continue
            row = by_id.get(old['record_id'])
            if not row or not same(row, old['fields']):
                plan['conflicts'].append(f'{table}/{key}: missing/changed record cannot be archived')
                continue
            if row.get('归档'):
                counts['unchanged'] += 1
                continue
            counts['archive'] += 1
            operations.append({'key': key, 'action': 'archive', 'record_id': row['record_id'],
                               'fields': {**old['fields'], '归档': True}, 'expected': old['fields']})
        plan['tables'][table] = {'counts': counts, 'operations': operations}
    return plan

def artifact_call(args, root):
    env = dict(os.environ, LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1')
    proc = subprocess.run(cli_prefix(root) + args, cwd=root, capture_output=True, text=True,
                          encoding='utf-8', env=env, timeout=180)
    if proc.returncode:
        raise RuntimeError(f'Base read failed (exit {proc.returncode}); inspect local CLI permissions/help')
    result = json.loads(proc.stdout)
    if result.get('manifest_version') != 'v1' or result.get('format') != 'ndjson':
        raise ValueError('Official CLI changed NDJSON manifest contract; stop before writes')
    return result

def read_records(root, token, table_id, cache, record_id=None):
    root = root.resolve()
    rows, seen, offset, context, revision = [], set(), 0, None, None
    while True:
        output = local(root, cache / (uuid.uuid4().hex + '.ndjson'))
        args = ['base', '+record-get' if record_id else '+record-list', '--as', 'user',
                '--base-token', token, '--table-id', table_id, '--format', 'ndjson',
                '--output', output.relative_to(root).as_posix()]
        args += ['--record-id', record_id] if record_id else ['--offset', str(offset), '--limit', '2000']
        manifest = artifact_call(args, root)
        if manifest.get('base_token') != token or manifest.get('table_id') != table_id:
            raise ValueError('Record artifact belongs to a different target')
        if not record_id and manifest.get('query_context', {}).get('record_scope') != 'all_records':
            raise ValueError('Record read is not a complete table scope')
        if context is None:
            context, revision = manifest.get('query_context'), manifest.get('rev')
        if revision is None or context != manifest.get('query_context') or revision != manifest.get('rev'):
            raise ValueError('Table revision/query scope changed during pagination; restart full read')
        chunk = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines() if line.strip()]
        if len(chunk) != manifest.get('records_count'):
            raise ValueError('Record file count does not match manifest')
        for row in chunk:
            rid = row.get('record_id')
            if not rid or rid in seen:
                raise ValueError('Missing/duplicate record ID in paginated read')
            seen.add(rid)
        rows.extend(chunk)
        if manifest.get('has_more') is False:
            return rows
        next_offset = manifest.get('next_offset')
        if record_id or not isinstance(next_offset, int) or next_offset <= offset:
            raise ValueError('Incomplete record artifact with invalid next offset')
        offset = next_offset

@contextmanager
def locked(cache):
    cache.mkdir(parents=True, exist_ok=True)
    lock = cache / 'run.lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink()

class Sync:
    def __init__(self, root):
        research_workspace(root)
        self.root = root.resolve()
        self.cache = local(self.root, '.work/research-base')
        self.cache.mkdir(parents=True, exist_ok=True)
        self.config_path = local(self.root, '.agents/config/research-base.local.json')
        self.config = read(self.config_path, {'schema_version': 1, 'documents': {}, 'selectors': {}})
        self.config.setdefault('project_id', uuid.uuid4().hex)
        self.state_path = self.cache / 'state.json'
        self.state = read(self.state_path, {'tables': {}})
        self.pending = self.cache / 'pending.json'

    def save_config(self):
        dump(self.config_path, self.config)

    def fetch(self):
        bridge = Bridge(self.root)
        snapshots, bindings = {}, {}
        for key in DOCS:
            supplied = self.config.get('documents', {}).get(key)
            entry = bridge.registry.get('documents', {}).get(key, {})
            if not supplied and not entry.get('document_id'):
                raise ValueError(f'{key}: provide its actual Feishu URL or bind the existing document')
            snapshots[key] = bridge.fetch(key, (supplied.split('#')[0] if supplied else entry['document_id']))
            bindings[key] = supplied or entry.get('url') or ''
        dataset = compile_dataset(snapshots, bindings, self.config.get('selectors', {}))
        source_ids = {k: v['document_id'] for k, v in dataset['sources'].items()}
        if self.config.get('source_ids') and self.config['source_ids'] != source_ids:
            raise ValueError('Source bindings changed: use a new workspace/config instead of reusing synchronization identity')
        self.config['source_ids'] = source_ids
        self.save_config()
        dump(self.cache / 'dataset.json', dataset)
        return dataset

    def command(self, verb, *args):
        response = call(['base', verb, '--as', 'user', *args], self.root)
        dump(self.cache / (uuid.uuid4().hex + '.operation.json'), response)
        data = response['data']
        if response.get('warnings') or data.get('warnings') or data.get('ignored_fields'):
            raise ValueError('Base response warnings/ignored fields require inspection; write was not accepted as verified')
        return data

    def tables(self):
        data = self.command('+table-list', '--base-token', self.config['base_token'])
        rows = data['tables']
        if data.get('has_more') or (data.get('total') is not None and data['total'] != len(rows)):
            raise ValueError('Table list is incomplete')
        if len({r['name'] for r in rows}) != len(rows):
            raise ValueError('Ambiguous duplicate table names')
        return {r['name']: r['id'] for r in rows}

    def fields(self, table_id):
        data = self.command('+field-list', '--base-token', self.config['base_token'], '--table-id', table_id)
        fields = data['fields']
        if data.get('has_more') or (data.get('total') is not None and data['total'] != len(fields)):
            raise ValueError('Field list is incomplete')
        if len({f['name'] for f in fields}) != len(fields):
            raise ValueError('Ambiguous duplicate field names')
        return {f['name']: f for f in fields}

    def validate_fields(self, table, found, tables):
        missing = []
        for wanted in schema(table, True):
            field = found.get(wanted['name'])
            if not field:
                missing.append(wanted)
                continue
            if field.get('__has_field_extension') or field['name'] in PROTECTED or field.get('type') != wanted['type']:
                raise ValueError(f'{table}/{field["name"]}: protected or incompatible managed field')
            if wanted['type'] == 'select':
                if field.get('multiple') is not False or not {o['name'] for o in wanted['options']} <= {o['name'] for o in field.get('options', [])}:
                    raise ValueError('Priority option schema is incompatible; do not modify existing options')
            if wanted['type'] == 'link' and field.get('link_table') not in {wanted['link_table'], tables[wanted['link_table']]}:
                raise ValueError('Link field targets a different table')
        return missing

    def views(self, table_id):
        data = self.command('+view-list', '--base-token', self.config['base_token'], '--table-id', table_id)
        views = data['views']
        if data.get('has_more') or (data.get('total') is not None and data['total'] != len(views)):
            raise ValueError('View list is incomplete; do not change visibility')
        return views

    def configure_reading_view(self, table, table_id):
        if table in self.config.get('configured_views', {}):
            return
        views = self.views(table_id)
        if self.config.get('base_origin') == 'new':
            target = next((view for view in views if view.get('type') == 'grid'), None)
            if not target:
                self.command('+view-create', '--base-token', self.config['base_token'], '--table-id', table_id,
                             '--json', json.dumps({'name': '科研阅读', 'type': 'grid'}, ensure_ascii=False))
                target = next((view for view in self.views(table_id) if view.get('name') == '科研阅读'), None)
        else:
            if any(view.get('name') == '科研阅读' for view in views):
                raise ValueError(f'{table}: an existing 科研阅读 view is not registered as managed; inspect before changing it')
            self.command('+view-create', '--base-token', self.config['base_token'], '--table-id', table_id,
                         '--json', json.dumps({'name': '科研阅读', 'type': 'grid'}, ensure_ascii=False))
            target = next((view for view in self.views(table_id) if view.get('name') == '科研阅读'), None)
        if not target or not (target.get('id') or target.get('view_id')):
            raise ValueError(f'{table}: cannot identify the reading view')
        view_id = target.get('id') or target['view_id']
        visible = VISIBLE[table]
        self.command('+view-set-visible-fields', '--base-token', self.config['base_token'],
                     '--table-id', table_id, '--view-id', view_id,
                     '--json', json.dumps({'visible_fields': visible}, ensure_ascii=False))
        self.config.setdefault('configured_views', {})[table] = view_id
        self.save_config()

    def ensure_wiki_placement(self):
        """Move a newly created Base into its research Wiki once, then verify the node."""
        space_id = self.config.get('wiki_space_id')
        if not space_id:
            return
        token = self.config['base_token']
        if not self.config.get('wiki_move_attempted_at'):
            self.config['wiki_move_attempted_at'] = timestamp()
            self.save_config()
            response = call(['wiki', '+move', '--as', 'user', '--obj-type', 'bitable',
                             '--obj-token', token, '--target-space-id', space_id], self.root)
            dump(self.cache / (uuid.uuid4().hex + '.wiki-move.json'), response)
            moved = response['data']
            if moved.get('task_id'):
                self.config['wiki_move_task_id'] = moved['task_id']
                self.save_config()
            if moved.get('ready') is False:
                raise ValueError('Base move into Wiki is pending; check the recorded task before continuing')
        response = call(['wiki', '+node-get', '--as', 'user', '--node-token', token,
                         '--space-id', space_id], self.root)
        node = response['data'].get('node', response['data'])
        if (str(node.get('space_id')) != str(space_id) or node.get('obj_type') != 'bitable'
                or node.get('obj_token') != token or not node.get('node_token')):
            raise ValueError('Base Wiki node does not match the registered Base and research space')
        self.config['wiki_node_token'] = node['node_token']
        self.config.pop('wiki_move_task_id', None)
        self.save_config()

    def init(self, name, base_url=None, template_url=None):
        self.fetch()  # Resolve input first, so missing docs never cause a stray Base.
        guard = self.cache / 'init-pending.json'
        if base_url and template_url:
            raise ValueError('Choose an existing Base or a template, not both')
        if base_url:
            token = self.command('+url-resolve', '--url', base_url)['base_token']
            if self.config.get('base_token') and self.config['base_token'] != token:
                raise ValueError('Target is already bound; use another project configuration')
            self.config['base_token'] = token
            self.save_config()
        elif not self.config.get('base_token'):
            if guard.exists():
                raise ValueError('Unresolved Base creation: locate and bind the actual created URL')
            if not name:
                raise ValueError('A new Base requires a user-visible name')
            dump(guard, {'name': name, 'started_at': timestamp()})
            if template_url:
                source = self.command('+url-resolve', '--url', template_url)['base_token']
                data = self.command('+base-copy', '--base-token', source, '--name', name, '--without-content')
            else:
                data = self.command('+base-create', '--name', name, '--time-zone', 'Asia/Shanghai',
                                    '--table-name', TABLES[0], '--fields', json.dumps(schema(TABLES[0]), ensure_ascii=False))
            created = data['base']
            self.config.update(base_token=created['base_token'], base_url=created['url'], base_origin='new' if not template_url else 'template')
            space = Bridge(self.root).registry.get('wiki_space')
            if space:
                if not space.get('space_id'):
                    raise ValueError('Registered research Wiki space has no ID')
                self.config['wiki_space_id'] = space['space_id']
            self.save_config()
            if template_url and created['base_token'] == source:
                raise ValueError('Template copy did not yield a distinct target; stop')
        self.ensure_wiki_placement()
        meta = self.command('+base-get', '--base-token', self.config['base_token'])['base']
        self.config['base_url'] = meta['url']
        self.save_config()
        if guard.exists():
            guard.unlink()
        tables = self.tables()
        for table in TABLES:
            if table not in tables:
                self.command('+table-create', '--base-token', self.config['base_token'], '--name', table,
                             '--fields', json.dumps(schema(table), ensure_ascii=False))
                tables = self.tables()
        for table in TABLES:
            found = self.fields(tables[table])
            for wanted in self.validate_fields(table, found, tables):
                self.command('+field-create', '--base-token', self.config['base_token'], '--table-id', tables[table],
                             '--json', json.dumps(wanted, ensure_ascii=False))
            if self.validate_fields(table, self.fields(tables[table]), tables):
                raise ValueError('Missing managed fields after schema creation')
            self.configure_reading_view(table, tables[table])
        self.save_config()
        return {'ok': True, 'base_url': self.config['base_url'], 'wiki_space_id': self.config.get('wiki_space_id'),
                'wiki_node_token': self.config.get('wiki_node_token'), 'tables': tables, 'records_imported': False}

    def current(self):
        tables = self.tables()
        if not all(t in tables for t in TABLES):
            raise ValueError('Target does not contain all six tables; run authorized init first')
        current = {}
        for table in TABLES:
            if self.validate_fields(table, self.fields(tables[table]), tables):
                raise ValueError('Missing managed fields; run authorized init to add them')
            current[table] = read_records(self.root, self.config['base_token'], tables[table], self.cache)
        return tables, current

    def preview(self):
        dataset = self.fetch()
        if not self.config.get('base_token'):
            return dataset, None, {'ok': True, 'target_bound': False, 'source_counts': {t: len(r) for t, r in dataset['tables'].items()}}
        tables, current = self.current()
        identity = {'base_token': self.config['base_token'], 'project_id': self.config['project_id'], 'source_ids': self.config['source_ids']}
        if self.state.get('identity') and self.state['identity'] != identity:
            raise ValueError('Journal belongs to another target/source/project')
        plan = prepare_plan(dataset, current, self.state, self.config['project_id'])
        plan.update(base_url=self.config['base_url'], sources=dataset['sources'], warnings=dataset['warnings'])
        dump(self.cache / 'plan.json', plan)
        return dataset, tables, plan

    def write(self, table, table_id, operation):
        if self.pending.exists():
            raise ValueError('Unresolved write exists: run recover instead of retrying a create')
        if operation['record_id']:
            before = read_records(self.root, self.config['base_token'], table_id, self.cache, operation['record_id'])
            if len(before) != 1 or not same(before[0], operation['expected']):
                raise ValueError('Managed fields changed immediately before write')
        else:
            before = read_records(self.root, self.config['base_token'], table_id, self.cache)
            if any(r.get('同步键') == operation['key'] or r.get('编号') == operation['key'] for r in before):
                raise ValueError('Key appeared before create; re-preview instead of creating duplicate')
        pending = {'table': table, 'table_id': table_id, 'operation': operation, 'started_at': timestamp(),
                   'identity': self.state['identity']}
        dump(self.pending, pending)
        args = ['--base-token', self.config['base_token'], '--table-id', table_id,
                '--json', json.dumps(operation['fields'], ensure_ascii=False)]
        if operation['record_id']:
            args += ['--record-id', operation['record_id']]
        self.command('+record-upsert', *args)
        # Retrieve by business key after create rather than assuming undocumented response ID nesting.
        self.recover()

    def recover(self):
        pending = read(self.pending)
        if not pending:
            return {'ok': True, 'pending': False}
        identity = {'base_token': self.config.get('base_token'), 'project_id': self.config['project_id'], 'source_ids': self.config.get('source_ids')}
        if pending['identity'] != identity or self.state.get('identity') != identity:
            raise ValueError('Pending operation belongs to another synchronization target')
        op, table = pending['operation'], pending['table']
        rows = read_records(self.root, self.config['base_token'], pending['table_id'], self.cache)
        matches = [r for r in rows if r.get('同步键') == op['key'] and r.get('同步项目') == self.config['project_id']]
        if len(matches) != 1 or (op['record_id'] and matches[0]['record_id'] != op['record_id']) or not same(matches[0], op['fields']):
            raise ValueError('Pending operation cannot be verified uniquely; inspect target and preserve guard')
        self.state.setdefault('tables', {}).setdefault(table, {})[op['key']] = {'record_id': matches[0]['record_id'], 'fields': op['fields']}
        dump(self.state_path, self.state)
        self.pending.unlink()
        return {'ok': True, 'recovered': True, 'table': table, 'key': op['key']}

    def sync(self):
        if self.pending.exists():
            raise ValueError('Unresolved write exists: recover before running sync')
        dataset, tables, plan = self.preview()
        if not tables:
            raise ValueError('No target Base: run authorized init first')
        if plan['conflicts']:
            raise ValueError('Synchronization conflicts; inspect .work/research-base/plan.json before any write')
        latest = self.fetch()
        if latest['sources'] != dataset['sources'] or latest['tables'] != dataset['tables']:
            raise ValueError('Source version/content changed during preview; regenerate plan')
        self.state['identity'] = {'base_token': self.config['base_token'], 'project_id': self.config['project_id'], 'source_ids': self.config['source_ids']}
        dump(self.state_path, self.state)
        for table in TABLES:
            for operation in plan['tables'][table]['operations']:
                self.write(table, tables[table], operation)
        relation_counts = self.relations(dataset, tables)
        final_sources = self.fetch()
        if final_sources['sources'] != dataset['sources'] or final_sources['tables'] != dataset['tables']:
            raise ValueError('Source changed during writes; verified partial progress is journaled, re-preview and sync the latest revision')
        # Final verification covers unchanged rows too, without creating a second facts layer.
        _, live = self.current()
        for table in TABLES:
            indexed = {r['record_id']: r for r in live[table]}
            for old in self.state.get('tables', {}).get(table, {}).values():
                if not same(indexed.get(old['record_id'], {}), old['fields']):
                    raise ValueError('Final readback failed; inspect local journal and current target')
        report = {'ok': True, 'base_url': self.config['base_url'], 'sources': dataset['sources'],
                  'counts': {t: p['counts'] for t, p in plan['tables'].items()},
                  'relation_updates': relation_counts, 'unresolved_mentions': dataset['warnings'], 'completed_at': timestamp()}
        dump(local(self.root, 'outputs/reports/research-base-sync.json'), report)
        return report

    def relations(self, dataset, tables):
        updates = 0
        for table, relations in LINKS.items():
            for row in dataset['tables'][table]:
                old = self.state['tables'][table][row['同步键']]
                fields = dict(old['fields'])
                for field, target in relations.items():
                    baseline = self.state['tables'].get(target, {})
                    references = REF.findall(row['关联编号'])
                    fields[field] = [{'id': baseline[r]['record_id']} for r in sorted(set(references))
                                     if r in baseline and not baseline[r]['fields'].get('归档')]
                if not same(old['fields'], fields):
                    self.write(table, tables[table], {'key': row['同步键'], 'action': 'update',
                               'record_id': old['record_id'], 'fields': fields, 'expected': old['fields']})
                    updates += 1
        return updates

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    subs = parser.add_subparsers(dest='mode', required=True)
    for mode in ['extract', 'preview', 'sync', 'recover']:
        subs.add_parser(mode)
    init = subs.add_parser('init')
    init.add_argument('--name')
    init.add_argument('--base-url')
    init.add_argument('--template-url')
    args = parser.parse_args()
    try:
        runner = Sync(args.root)
        with locked(runner.cache):
            if args.mode == 'init':
                result = runner.init(args.name, args.base_url, args.template_url)
            elif args.mode == 'extract':
                dataset = runner.fetch()
                result = {'ok': True, 'source_counts': {t: len(r) for t, r in dataset['tables'].items()},
                          'warnings': dataset['warnings'], 'dataset': '.work/research-base/dataset.json'}
            elif args.mode == 'preview':
                _, _, plan = runner.preview()
                result = {k: v for k, v in plan.items() if k != 'tables'}
                result['counts'] = {t: p['counts'] for t, p in plan.get('tables', {}).items()}
            else:
                result = getattr(runner, args.mode)()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
