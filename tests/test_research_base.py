"""Synthetic native-doc/Base scenarios; fixtures are not research evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'product/.agents/skills/research-docs-to-base/scripts'))
import research_base as rb

class WorkspaceBoundaryTests(unittest.TestCase):
    def test_development_source_rejected_before_cache_or_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / 'tools').mkdir()
            (repository / 'tools/build_release.py').write_text('fixture', encoding='utf-8')
            (repository / 'product').mkdir()
            for root in (repository, repository / 'product'):
                with self.subTest(root=root), patch.object(rb, 'call') as operation:
                    with self.assertRaisesRegex(ValueError, 'Development source'):
                        rb.Sync(root)
                    operation.assert_not_called()
                    self.assertFalse((root / '.work').exists())

def fixture(xml, doc, revision=1):
    return {'ok': True, 'data': {'document': {'document_id': doc, 'revision_id': revision,
            'url': f'https://example.feishu.cn/docx/{doc}', 'content': xml}}}

def sources():
    return {
        rb.DOCS[0]: fixture('<title>State</title><h1 id="scope">研究范围与实验体系</h1><p>合成数据，非实际实验。</p>'
            '<h1 id="obs">OBS-001 — 测量</h1><p>合成观察，包含阴性结果。</p><img token="synthetic-only" />'
            '<h1 id="con">CON-001 — 有限结论</h1><table><tr><td>证据等级</td><td>初步</td></tr></table>'
            '<p>依据：<a href="https://example.feishu.cn/docx/state#obs">OBS-001</a></p>'
            '<h1 id="hyp">HYP-001 — 待验证</h1><p>未验证；RQ-001</p>', 'state'),
        rb.DOCS[1]: fixture('<title>Questions</title><h1 id="p1">优先级 1</h1><h2 id="rq">RQ-001 — 如何判别？</h2>'
            '<p>状态：进行中</p><p>关联 OBS-001、CON-001；SOL-001 尚未导入。</p>', 'questions'),
        rb.DOCS[2]: fixture('<title>Story</title><h1 id="abstract">摘要式故事</h1><p>目标叙事成功结果，不是实际事实。</p>'
            '<h1 id="refs">文献定位与创新点</h1><p>间接证据：<a href="https://doi.org/10.1234/fixture">Synthetic paper</a></p>'
            '<p>边界：<a href="https://dx.doi.org/10.1234/fixture">重复引用</a></p>'
            '<h1 id="foundation">本项目的独特基础</h1><p>不能当作参考文献目录。</p>'
            '<h1 id="tasks">近期优先事项</h1><ul><li>TASK-001 核对 RQ-001，保留阴性结果。</li></ul>', 'story')}

def compiled():
    return rb.compile_dataset(sources(), {k: '' for k in rb.DOCS})

def empty_tables():
    return {t: [] for t in rb.TABLES}

def seeded(dataset, owner='test-project'):
    current, state = empty_tables(), {'tables': {}}
    n = 0
    for table, rows in dataset['tables'].items():
        state['tables'][table] = {}
        for row in rows:
            n += 1
            fields = {**row, '同步项目': owner}
            current[table].append({**fields, 'record_id': f'rec{n}', '人工备注': 'Keep my note', '核心发现': 'AI only'})
            state['tables'][table][row['同步键']] = {'record_id': f'rec{n}', 'fields': copy.deepcopy(fields)}
    return current, state

class DocumentMappingTests(unittest.TestCase):
    def test_observation_evidence_priority_story_and_reference_identity(self):
        data = compiled()
        obs = data['tables'][rb.TABLES[1]][0]
        self.assertIn('阴性结果', obs['原文'])
        self.assertEqual(obs['概要'], '测量')
        self.assertNotIn('OBS-001', obs['原文'])
        self.assertIn('图片：请查看来源文档', obs['原文'])
        self.assertNotIn('synthetic-only', obs['原文'])
        self.assertEqual(obs['来源链接'], 'https://example.feishu.cn/docx/state#obs')
        cons = data['tables'][rb.TABLES[2]]
        self.assertEqual(cons[0]['源证据等级'], '初步')
        self.assertEqual(cons[0]['概要'], '有限结论')
        self.assertNotIn('证据等级', cons[0]['原文'])
        self.assertIn('OBS-001', cons[0]['引用'])
        self.assertEqual(cons[1]['源类型'], '工作假设')
        self.assertEqual(cons[1]['源证据等级'], '')
        self.assertEqual(data['tables'][rb.TABLES[3]][0]['优先级'], ['P1'])
        refs = data['tables'][rb.TABLES[4]]
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['同步键'], 'DOI:10.1234/fixture')
        self.assertIn('边界', refs[0]['定位与边界'])
        self.assertEqual(data['tables'][rb.TABLES[5]][0]['同步键'], 'TASK-001')
        self.assertTrue(all(row['来源语义'] == '目标论文叙事' for row in data['tables'][rb.TABLES[0]] if row['来源文档'] == rb.DOCS[2]))
        self.assertIn('SOL-001', data['warnings'])
        self.assertTrue(all(not rb.PROTECTED.intersection(row) for rows in data['tables'].values() for row in rows))

    def test_readable_body_separates_metadata_citations_and_source_ids(self):
        data = sources()
        data[rb.DOCS[0]]['data']['document']['content'] = (
            '<title>项目现状</title><h1 id="obs">OBS-002 — 光刺激后延迟增强</h1>'
            '<p>编号：OBS-002</p><p>来源：第 3 页</p><p>刺激停止后仍检测到增强。</p>'
            '<p>证据等级：初步</p><p>引用：<a href="https://doi.org/10.1234/example">相关论文</a></p>')
        result = rb.compile_dataset(data, {k: '' for k in rb.DOCS})
        obs = result['tables'][rb.TABLES[1]][0]
        self.assertEqual(obs['概要'], '光刺激后延迟增强')
        self.assertEqual(obs['原文'], '刺激停止后仍检测到增强。')
        self.assertIn('https://doi.org/10.1234/example', obs['引用'])
        self.assertTrue(set(rb.VISIBLE[rb.TABLES[1]]) <= {f['name'] for f in rb.schema(rb.TABLES[1], True)})
        self.assertFalse(set(rb.COMMON) & set(rb.VISIBLE[rb.TABLES[1]]))

    def test_id_only_heading_uses_body_for_summary_without_repeating_id(self):
        data = sources()
        data[rb.DOCS[0]]['data']['document']['content'] = (
            '<title>项目现状</title><h1 id="obs">OBS-002</h1>'
            '<p>OBS-002</p><p>光刺激结束后持续增强。仍需重复验证。</p>')
        obs = rb.compile_dataset(data, {k: '' for k in rb.DOCS})['tables'][rb.TABLES[1]][0]
        self.assertEqual(obs['概要'], '光刺激结束后持续增强')
        self.assertEqual(obs['原文'], '光刺激结束后持续增强。仍需重复验证。')

    def test_partial_missing_duplicate_and_wrong_document_rejected(self):
        cases = []
        data = sources(); del data[rb.DOCS[2]]; cases.append(data)
        data = sources(); data[rb.DOCS[0]]['data']['document']['content'] = '<fragment><p>partial</p></fragment>'; cases.append(data)
        data = sources(); data[rb.DOCS[0]]['data']['document']['content'] = '<title>State</title><synced_reference src-token="other" />'; cases.append(data)
        data = sources(); data[rb.DOCS[0]]['data']['document']['content'] += '<h1>OBS-001 duplicate</h1>'; cases.append(data)
        data = sources(); data[rb.DOCS[1]]['data']['document']['content'] += '<h1>OBS-002 misplaced</h1>'; cases.append(data)
        data = sources(); data[rb.DOCS[2]]['data']['document']['document_id'] = 'state'; cases.append(data)
        for snapshots in cases:
            with self.subTest(snapshots=snapshots), self.assertRaises(ValueError):
                rb.compile_dataset(snapshots, {k: '' for k in rb.DOCS})

    def test_unstructured_entry_needs_exact_selector_and_stale_selector_fails(self):
        data = sources()
        data[rb.DOCS[0]]['data']['document']['content'] = '<title>State</title><p id="entry">OBS-005 — 实际段落编号</p>'
        with self.assertRaises(ValueError):
            rb.compile_dataset(data, {k: '' for k in rb.DOCS})
        result = rb.compile_dataset(data, {k: '' for k in rb.DOCS}, {rb.DOCS[0]: {'entry': {'role': 'entry', 'key': 'OBS-005', 'title': '实际段落编号'}}})
        self.assertEqual(result['tables'][rb.TABLES[1]][0]['编号'], 'OBS-005')
        with self.assertRaises(ValueError):
            rb.compile_dataset(data, {k: '' for k in rb.DOCS}, {rb.DOCS[0]: {'stale-block': {'role': 'entry', 'key': 'OBS-005'}}})

    def test_priority_not_inferred_from_ambiguous_parent_or_scientific_prose(self):
        self.assertEqual(rb.priority('初步推测较强效应；另一个问题 P1。', ['已解决或暂缓问题']), [])
        self.assertEqual(rb.label('初步推测较强效应', ['证据等级']), '')
        with self.assertRaises(ValueError): rb.priority('优先级：紧急', [])

class IncrementalPlanTests(unittest.TestCase):
    def test_source_revision_alone_does_not_update_and_manual_ai_fields_preserved(self):
        data = compiled(); current, state = seeded(data)
        for rows in data['tables'].values():
            for row in rows: row['来源版本'] = '9'
        plan = rb.prepare_plan(data, current, state, 'test-project')
        self.assertFalse(plan['conflicts'])
        self.assertTrue(all(not p['operations'] for p in plan['tables'].values()))

    def test_create_update_archive_and_return_keep_permanent_identity(self):
        data = compiled(); current, state = seeded(data)
        changed = copy.deepcopy(data)
        changed['tables'][rb.TABLES[1]][0]['原文'] += '\n可靠新观察'
        changed['tables'][rb.TABLES[2]] = changed['tables'][rb.TABLES[2]][:1]
        new = copy.deepcopy(changed['tables'][rb.TABLES[3]][0]); new.update(同步键='RQ-002', 编号='RQ-002')
        changed['tables'][rb.TABLES[3]].append(new)
        plan = rb.prepare_plan(changed, current, state, 'test-project')
        self.assertFalse(plan['conflicts'])
        self.assertEqual(plan['tables'][rb.TABLES[1]]['counts']['update'], 1)
        self.assertEqual(plan['tables'][rb.TABLES[2]]['counts']['archive'], 1)
        archived = plan['tables'][rb.TABLES[2]]['operations'][0]
        self.assertTrue(archived['fields']['归档'])
        self.assertIn('未验证', archived['fields']['原文'])
        self.assertEqual(plan['tables'][rb.TABLES[3]]['counts']['create'], 1)
        current[rb.TABLES[2]][1]['归档'] = True
        state['tables'][rb.TABLES[2]]['HYP-001']['fields']['归档'] = True
        restored = rb.prepare_plan(data, current, state, 'test-project')
        self.assertFalse(restored['tables'][rb.TABLES[2]]['operations'][0]['fields']['归档'])

    def test_managed_manual_edits_unmanaged_legacy_and_deleted_records_block(self):
        data = compiled()
        current, state = seeded(data); current[rb.TABLES[1]][0]['原文'] = 'human change'
        self.assertTrue(rb.prepare_plan(data, current, state, 'test-project')['conflicts'])
        current, state = seeded(data); current[rb.TABLES[1]] = []
        self.assertTrue(rb.prepare_plan(data, current, state, 'test-project')['conflicts'])
        current = empty_tables(); current[rb.TABLES[1]].append({'record_id': 'legacy', '编号': 'OBS-001', '原文': 'old'})
        self.assertTrue(rb.prepare_plan(data, current, {}, 'test-project')['conflicts'])

    def test_duplicate_keys_and_relation_edits_are_detected(self):
        data = compiled(); current, state = seeded(data)
        current[rb.TABLES[1]].append({**current[rb.TABLES[1]][0], 'record_id': 'second'})
        with self.assertRaises(ValueError): rb.prepare_plan(data, current, state, 'test-project')
        current, state = seeded(data)
        state['tables'][rb.TABLES[2]]['CON-001']['fields']['关联OBS'] = [{'id': 'real-existing-id'}]
        current[rb.TABLES[2]][0]['关联OBS'] = [{'id': 'manual-other-id'}]
        self.assertTrue(rb.prepare_plan(data, current, state, 'test-project')['conflicts'])

class ArtifactTests(unittest.TestCase):
    def run_pages(self, pages):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / 'path-alias').mkdir()
        root = root / 'path-alias' / '..'
        cache = root / '.work/research-base'; cache.mkdir(parents=True)
        offsets = []
        def export(args, workroot):
            offsets.append(int(args[args.index('--offset') + 1]))
            manifest, rows = pages[len(offsets) - 1]
            target = root / args[args.index('--output') + 1]
            target.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            return {'manifest_version': 'v1', 'format': 'ndjson', 'base_token': 'fixtureBase', 'table_id': 'tblFixture',
                    'query_context': {'record_scope': 'all_records'}, 'rev': 3, 'records_count': len(rows), **manifest}
        with patch.object(rb, 'artifact_call', side_effect=export):
            rows = rb.read_records(root, 'fixtureBase', 'tblFixture', cache)
        return rows, offsets

    def test_pagination_uses_returned_offset_and_checks_complete_revision(self):
        rows, offsets = self.run_pages([({'has_more': True, 'next_offset': 10}, [{'record_id': 'rec1', '编号': 'OBS-001'}]),
                                       ({'has_more': False}, [{'record_id': 'rec2', '编号': 'OBS-002'}])])
        self.assertEqual(offsets, [0, 10]); self.assertEqual(len(rows), 2)
        for second in [{'has_more': False, 'rev': 4}, {'has_more': True}]:
            with self.assertRaises(ValueError):
                self.run_pages([({'has_more': True, 'next_offset': 10}, [{'record_id': 'rec1'}]),
                                (second, [{'record_id': 'rec2'}])])

    def test_duplicate_rows_and_count_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.run_pages([({'has_more': True, 'next_offset': 2}, [{'record_id': 'same'}]),
                            ({'has_more': False}, [{'record_id': 'same'}])])
        with self.assertRaises(ValueError):
            self.run_pages([({'has_more': False, 'records_count': 7}, [{'record_id': 'one'}])])

class OperationSafetyTests(unittest.TestCase):
    def runner(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        runner = rb.Sync(Path(directory.name))
        runner.config.update(base_token='fixtureBase', base_url='https://example.feishu.cn/base/fixtureBase', project_id='project', source_ids={'fixture': 'source'})
        runner.state['identity'] = {k: runner.config[k] for k in ['base_token', 'project_id', 'source_ids']}
        return runner

    def test_ambiguous_create_never_retries_and_recovery_requires_actual_row(self):
        runner = self.runner()
        op = {'key': 'OBS-001', 'action': 'create', 'record_id': None, 'expected': None,
              'fields': {'同步键': 'OBS-001', '同步项目': 'project', '原文': 'fixture'}}
        with patch.object(rb, 'read_records', return_value=[]), patch.object(runner, 'command', side_effect=RuntimeError('uncertain failure')) as write:
            with self.assertRaises(RuntimeError): runner.write(rb.TABLES[1], 'tblFixture', op)
            with self.assertRaises(ValueError): runner.write(rb.TABLES[1], 'tblFixture', op)
            self.assertEqual(write.call_count, 1)
            with self.assertRaises(ValueError): runner.recover()
        self.assertTrue(runner.pending.exists())
        with patch.object(rb, 'read_records', return_value=[{'record_id': 'actualRecord', **op['fields']}]):
            self.assertTrue(runner.recover()['recovered'])
        self.assertFalse(runner.pending.exists())
        self.assertEqual(runner.state['tables'][rb.TABLES[1]]['OBS-001']['record_id'], 'actualRecord')

    def test_changed_row_before_write_stops_without_pending_or_external_update(self):
        runner = self.runner()
        op = {'key': 'OBS-001', 'action': 'update', 'record_id': 'actualRecord', 'expected': {'原文': 'old'}, 'fields': {'原文': 'new'}}
        with patch.object(rb, 'read_records', return_value=[{'record_id': 'actualRecord', '原文': 'human changed'}]), patch.object(runner, 'command') as write:
            with self.assertRaises(ValueError): runner.write(rb.TABLES[1], 'tblFixture', op)
        write.assert_not_called(); self.assertFalse(runner.pending.exists())

    def test_ai_managed_field_and_wrong_link_table_fail_validation(self):
        runner = self.runner(); tables = {t: 'tbl' + str(i) for i, t in enumerate(rb.TABLES)}
        found = {f['name']: f for f in rb.schema(rb.TABLES[2], True)}
        found['原文']['__has_field_extension'] = 'builtin_llm_completion'
        with self.assertRaises(ValueError): runner.validate_fields(rb.TABLES[2], found, tables)
        del found['原文']['__has_field_extension']
        found['关联OBS']['link_table'] = 'wrong'
        with self.assertRaises(ValueError): runner.validate_fields(rb.TABLES[2], found, tables)

    def test_relations_use_verified_ids_not_business_ids_and_keep_sol_unresolved(self):
        runner = self.runner(); data = compiled(); _, state = seeded(data, owner='project')
        runner.state['tables'] = state['tables']
        captured = []
        with patch.object(runner, 'write', side_effect=lambda table, tid, op: captured.append((table, op))):
            runner.relations(data, {t: 'tbl' + str(i) for i, t in enumerate(rb.TABLES)})
        con = next(op for table, op in captured if table == rb.TABLES[2] and op['key'] == 'CON-001')
        target = runner.state['tables'][rb.TABLES[1]]['OBS-001']['record_id']
        self.assertEqual(con['fields']['关联OBS'], [{'id': target}])
        self.assertNotIn('SOL-001', json.dumps(con['fields']['关联OBS']))


class ReadingViewTests(unittest.TestCase):
    def test_new_base_hides_sync_columns_in_its_grid_view(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = rb.Sync(Path(directory))
            runner.config.update(base_token='fixtureBase', base_origin='new')
            writes = []
            def command(verb, *args):
                if verb == '+view-list':
                    return {'total': 1, 'views': [{'id': 'view1', 'name': '默认视图', 'type': 'grid'}]}
                if verb == '+view-set-visible-fields':
                    writes.append((args[args.index('--view-id') + 1], json.loads(args[args.index('--json') + 1])))
                    return {}
                raise AssertionError(verb)
            with patch.object(runner, 'command', side_effect=command):
                runner.configure_reading_view(rb.TABLES[1], 'tblObservation')
            self.assertEqual(writes[0][0], 'view1')
            self.assertEqual(writes[0][1]['visible_fields'], rb.VISIBLE[rb.TABLES[1]])
            self.assertFalse(set(rb.COMMON) & set(writes[0][1]['visible_fields']))
            self.assertEqual(runner.config['configured_views'][rb.TABLES[1]], 'view1')

    def test_existing_base_gets_separate_reading_view(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = rb.Sync(Path(directory))
            runner.config['base_token'] = 'fixtureBase'
            views = [{'id': 'custom1', 'name': '同事视图', 'type': 'grid'}]
            writes = []
            def command(verb, *args):
                if verb == '+view-list':
                    return {'total': len(views), 'views': list(views)}
                if verb == '+view-create':
                    views.append({'id': 'reading1', 'name': '科研阅读', 'type': 'grid'})
                    return {}
                if verb == '+view-set-visible-fields':
                    writes.append(args[args.index('--view-id') + 1])
                    return {}
                raise AssertionError(verb)
            with patch.object(runner, 'command', side_effect=command):
                runner.configure_reading_view(rb.TABLES[2], 'tblConclusion')
            self.assertEqual(writes, ['reading1'])
            self.assertEqual(views[0]['name'], '同事视图')

    def test_new_base_moves_to_registered_wiki_once_and_verifies_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = rb.Sync(Path(directory))
            runner.config.update(base_token='base123', wiki_space_id='space123')
            calls = []
            def operation(args, root, content=None):
                calls.append(args[:2])
                if args[:2] == ['wiki', '+move']:
                    return {'ok': True, 'data': {'ready': True, 'node_token': 'wiki123'}}
                if args[:2] == ['wiki', '+node-get']:
                    return {'ok': True, 'data': {'node_token': 'wiki123', 'space_id': 'space123',
                                                 'obj_type': 'bitable', 'obj_token': 'base123'}}
                raise AssertionError(args)
            with patch.object(rb, 'call', side_effect=operation):
                runner.ensure_wiki_placement()
                runner.ensure_wiki_placement()
            self.assertEqual(calls.count(['wiki', '+move']), 1)
            self.assertEqual(runner.config['wiki_node_token'], 'wiki123')

    def test_uncertain_wiki_move_requires_readback_before_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = rb.Sync(Path(directory))
            runner.config.update(base_token='base123', wiki_space_id='space123')
            calls = []
            def operation(args, root, content=None):
                calls.append(args[:2])
                raise RuntimeError('synthetic uncertain move result')
            with patch.object(rb, 'call', side_effect=operation):
                with self.assertRaises(RuntimeError): runner.ensure_wiki_placement()
                with self.assertRaises(RuntimeError): runner.ensure_wiki_placement()
            self.assertEqual(calls.count(['wiki', '+move']), 1)
            self.assertTrue(runner.config['wiki_move_attempted_at'])

class WorkflowTests(unittest.TestCase):
    def test_full_sync_idempotence_archive_relations_and_human_notes(self):
        """Run the public orchestration against a synthetic CLI with native response shapes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = rb.Sync(root)
            snapshots = sources()
            runner.config.update(documents={k: v['data']['document']['url'] for k, v in snapshots.items()},
                                 project_id='synthetic', base_token='fixtureBase',
                                 base_url='https://example.feishu.cn/base/fixtureBase')
            table_ids = {t: f'tbl{i}' for i, t in enumerate(rb.TABLES)}
            field_defs = {tid: {f['name']: f for f in rb.schema(t, True)} for t, tid in table_ids.items()}
            remote = {tid: [] for tid in table_ids.values()}
            revisions = {tid: 1 for tid in remote}
            mutations = []
            class FakeBridge:
                def __init__(self, root): self.registry = {'documents': {}}
                def fetch(self, key, doc): return copy.deepcopy(snapshots[key])
            def command(args, workroot):
                verb = args[1]
                if verb == '+table-list':
                    data = {'total': len(table_ids), 'tables': [{'id': tid, 'name': name} for name, tid in table_ids.items()]}
                elif verb == '+field-list':
                    tid = args[args.index('--table-id') + 1]
                    data = {'total': len(field_defs[tid]), 'fields': list(field_defs[tid].values())}
                elif verb == '+record-upsert':
                    tid = args[args.index('--table-id') + 1]
                    fields = json.loads(args[args.index('--json') + 1])
                    self.assertFalse(rb.PROTECTED.intersection(fields))
                    if '--record-id' in args:
                        rid = args[args.index('--record-id') + 1]
                        row = next(r for r in remote[tid] if r['record_id'] == rid)
                    else:
                        rid = 'rec' + str(sum(map(len, remote.values())) + 1)
                        row = {'record_id': rid, '人工备注': 'Keep this note'}
                        remote[tid].append(row)
                    row.update(fields)
                    revisions[tid] += 1
                    mutations.append((tid, rid, fields))
                    data = {'record': {'id': rid}}
                else:
                    raise AssertionError(f'Unexpected operation: {verb}')
                return {'ok': True, 'data': data}
            def artifact(args, workroot):
                tid = args[args.index('--table-id') + 1]
                rows = copy.deepcopy(remote[tid])
                if '--record-id' in args:
                    rows = [r for r in rows if r['record_id'] == args[args.index('--record-id') + 1]]
                path = root / args[args.index('--output') + 1]
                path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
                return {'manifest_version': 'v1', 'format': 'ndjson', 'base_token': 'fixtureBase', 'table_id': tid,
                        'rev': revisions[tid], 'records_count': len(rows), 'has_more': False,
                        'query_context': {'record_scope': 'all_records'}}
            with patch.object(rb, 'Bridge', FakeBridge), patch.object(rb, 'call', side_effect=command), patch.object(rb, 'artifact_call', side_effect=artifact):
                first = runner.sync()
                self.assertTrue(first['ok']); self.assertGreater(first['relation_updates'], 0)
                count = len(mutations)
                second = runner.sync()
                self.assertEqual(len(mutations), count)
                self.assertEqual(second['relation_updates'], 0)
                state_xml = snapshots[rb.DOCS[0]]['data']['document']['content']
                snapshots[rb.DOCS[0]]['data']['document']['content'] = state_xml[:state_xml.index('<h1 id="hyp">')]
                snapshots[rb.DOCS[0]]['data']['document']['revision_id'] = 2
                third = runner.sync()
                self.assertEqual(third['counts'][rb.TABLES[2]]['archive'], 1)
                hyp = next(r for r in remote[table_ids[rb.TABLES[2]]] if r['同步键'] == 'HYP-001')
                self.assertTrue(hyp['归档']); self.assertIn('未验证', hyp['原文'])
                self.assertTrue(all(row['人工备注'] == 'Keep this note' for rows in remote.values() for row in rows))
                self.assertTrue((root / 'outputs/reports/research-base-sync.json').exists())

    def test_changed_source_between_preview_and_apply_prevents_all_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = rb.Sync(Path(directory))
            data = compiled()
            altered = copy.deepcopy(data); altered['sources'][rb.DOCS[0]]['revision_id'] = 2
            plan = {'conflicts': [], 'tables': {t: {'counts': {}, 'operations': []} for t in rb.TABLES}}
            with patch.object(runner, 'preview', return_value=(data, {t: t for t in rb.TABLES}, plan)), \
                 patch.object(runner, 'fetch', return_value=altered), patch.object(runner, 'write') as write:
                with self.assertRaises(ValueError): runner.sync()
                write.assert_not_called()

if __name__ == '__main__':
    unittest.main()
