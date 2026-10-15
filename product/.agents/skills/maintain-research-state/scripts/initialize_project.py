"""Prepare blank native Feishu state documents; publish only when requested."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
from html import escape
import json
import sys
from feishu_bridge import Bridge, dump, local, parse_xml, text_blocks

DOC_TITLES = {'CURRENT_STATE': '项目现状', 'PROJECT_STORY': '项目故事',
              'RESEARCH_QUESTIONS': '研究问题'}

def prepare(root: Path, name: str, scope: str, date: str):
    if dt.date.fromisoformat(date).isoformat() != date:
        raise ValueError('Use a YYYY-MM-DD date in the user timezone')
    bridge = Bridge(root)
    root = bridge.root
    name = name.strip()
    if not name:
        raise ValueError('Provide the research-system name for the Wiki space')
    if any(key in bridge.registry['documents'] for key in ['CURRENT_STATE', 'RESEARCH_QUESTIONS', 'PROJECT_STORY']) or any(key.startswith('SOL-') for key in bridge.registry['documents']):
        raise ValueError('Existing research documents are registered; use incremental updates')
    for filename in ['CURRENT_STATE.md', 'RESEARCH_QUESTIONS.md', 'PROJECT_STORY.md']:
        if (root / filename).exists():
            raise ValueError('Existing legacy research state detected; do not replace it with blank documents')
    layout = root / '.agents/config/project-layout.json'
    if not layout.is_file() or not (root / 'AGENTS.md').is_file():
        raise ValueError('Copy laRkdown rules and skills to the specified research workspace first')
    contract = json.loads(layout.read_text(encoding='utf-8'))
    if contract.get('workspace_kind') != 'personal-research':
        raise ValueError('Target lacks the personal research preset; do not initialize a development directory')
    for folder in contract['directories']:
        local(root, folder).mkdir(parents=True, exist_ok=True)
    headings = {
        'CURRENT_STATE': ['研究范围与实验体系', '直接观察 OBS', '证据结论 CON', '待验证假设 HYP', '矛盾、阴性与缺失信息'],
        'PROJECT_STORY': ['故事框架（待填写）'],
        'RESEARCH_QUESTIONS': ['优先级 1', '优先级 2', '优先级 3', '已解决或暂缓问题'],
    }
    work = local(root, '.work/initialization')
    work.mkdir(parents=True, exist_ok=True)
    manifest = {'project': name, 'scope': scope, 'date': date, 'documents': {}}
    for key, sections in headings.items():
        text = f'<title>{DOC_TITLES[key]}</title><p>更新日期：{escape(date)}</p><p>研究体系：{escape(name)}</p><p>研究范围：{escape(scope or "待用户填写")}</p><p>空白框架，尚未创建科研条目。</p>'
        if key == 'PROJECT_STORY': text += '<p>本文档用于目标论文叙事；真实支持程度与成立条件由实际科研记录限定。</p>'
        text += ''.join(f'<h1>{escape(heading)}</h1>' for heading in sections)
        path = work / (key + '.xml')
        if path.exists() and path.read_text(encoding='utf-8') != text:
            raise ValueError('Existing initialization draft differs; preserve and inspect it before replacing')
        path.write_text(text, encoding='utf-8')
        manifest['documents'][key] = path.relative_to(root).as_posix()
    dump(work / 'manifest.json', manifest)
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--date', required=True)
    parser.add_argument('--system-name', '--project-name', dest='system_name', required=True)
    parser.add_argument('--scope', default='')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    args.system_name = args.system_name.strip()
    try:
        bridge = Bridge(root)
        # Recover a partial published batch only through its matching retained manifest.
        manifest_path = root / '.work/initialization/manifest.json'
        if args.publish and manifest_path.is_file() and bridge.registry['documents']:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if (manifest['project'], manifest['scope'], manifest['date']) != (args.system_name, args.scope, args.date):
                raise ValueError('Retained initialization manifest belongs to a different request')
        else:
            manifest = prepare(root, args.system_name, args.scope, args.date)
        if args.publish:
            space = bridge.wiki_space(args.system_name)
            for key, path in manifest['documents'].items():
                if key in bridge.registry['documents']:
                    if bridge.registry['documents'][key].get('wiki_space_id') != space['space_id']:
                        raise ValueError(f'{key} is registered outside this research-system Wiki space')
                    expected = hashlib.sha256(local(root, path).read_bytes()).hexdigest()
                    if bridge.registry['documents'][key].get('authored_sha256') != expected:
                        raise ValueError('Registered document does not belong to this initialization draft; preserve it and use incremental maintenance')
                    current = bridge.fetch(key)['data']['document']['content']
                    authored = local(root, path).read_text(encoding='utf-8')
                    actual_text = ''.join(parse_xml(current).itertext())
                    if any(block not in actual_text for block in text_blocks(authored)[1:]):
                        raise ValueError(f'{key} was created but its body is incomplete; repair it instead of creating another')
                else:
                    bridge.create_in_wiki(key, Path(path), space['space_id'])
            print(json.dumps({'ok': True, 'wiki_space': space, 'documents': bridge.registry['documents']}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({'ok': True, 'published': False, 'manifest': manifest}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(json.dumps({'ok': False, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
