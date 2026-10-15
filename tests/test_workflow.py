"""Offline regression checks; fixture numbers are synthetic, never research evidence."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import io
from PIL import Image

def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'product/.agents/skills/maintain-research-state/scripts'
sys.path.insert(0, str(SCRIPTS))
import feishu_bridge as fb
import initialize_project as initializer
import validate_state as validator
media = load_script('larkdown_media', ROOT / 'product/.agents/skills/pptx-to-research-state/scripts/prepare_media_preview.py')

def snapshot(doc, xml):
    return {'ok': True, 'data': {'document': {'document_id': doc, 'revision_id': 1, 'content': xml}}}

class NativeStateTests(unittest.TestCase):
    def fixtures(self):
        state = '<title>CURRENT_STATE</title><h1 id="bOBS">OBS-001 — Synthetic observation</h1><p>Fixture only.</p><h1 id="bCON">CON-001 — Synthetic conclusion</h1><p>初步；<a href="https://example.feishu.cn/docx/state#bOBS">OBS-001</a>；not actual research evidence.</p><h1 id="bHYP">HYP-001 — Synthetic hypothesis</h1><p>未验证；<a href="https://example.feishu.cn/docx/state#bOBS">OBS-001</a></p>'
        return snapshot('state', state)

    def test_links_and_evidence_labels(self):
        self.assertTrue(validator.validate([self.fixtures()])['ok'])

    def test_stale_link_and_missing_evidence(self):
        data = self.fixtures()
        data['data']['document']['content'] = data['data']['document']['content'].replace('#bOBS', '#old').replace('初步', '')
        codes = {item['code'] for item in validator.validate([data])['issues']}
        self.assertIn('stale-block-link', codes)
        self.assertIn('con-without-evidence-level', codes)

    def test_partial_and_duplicate_snapshots_rejected(self):
        self.assertFalse(validator.validate([snapshot('state', '<fragment><p>partial</p></fragment>')])['ok'])
        data = self.fixtures()
        self.assertFalse(validator.validate([data, data])['ok'])

    def test_reserved_syntax_rejected(self):
        for content in ['<p>[[note]]</p>', '<p>label ^obs-001</p>', '<!DOCTYPE x><p>text</p>']:
            with self.assertRaises(ValueError): fb.parse_xml(content)

class PictureTests(unittest.TestCase):
    def test_png_jpeg_and_multiframe_tiff_originals_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            for format_, suffix in [('PNG', '.png'), ('JPEG', '.jpg'), ('TIFF', '.tiff')]:
                buffer = io.BytesIO()
                first = Image.new('RGB', (32, 24), 'red')
                if format_ == 'TIFF': first.save(buffer, format=format_, save_all=True, append_images=[Image.new('RGB', (32, 24), 'blue')])
                else: first.save(buffer, format=format_)
                blob = buffer.getvalue()
                record = media.asset_record(blob, 'fixture' + suffix, Path(directory))
                self.assertEqual((Path(directory) / record['original']).read_bytes(), blob)
                self.assertEqual(record['sha256'], hashlib.sha256(blob).hexdigest())
                self.assertEqual(record['frame_count'], 2 if format_ == 'TIFF' else 1)
                self.assertTrue(all(not frame['preview_transform']['quantitative_use'] for frame in record['frames']))

    def test_scalar_tiff_preview_keeps_original_values(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Image.new('I', (2, 2))
            original.putdata([100, 1000, 10000, 50000])
            buffer = io.BytesIO()
            original.save(buffer, format='TIFF')
            record = media.asset_record(buffer.getvalue(), 'fixture.tif', Path(directory))
            with Image.open(Path(directory) / record['original']) as restored:
                self.assertEqual([restored.getpixel((x, y)) for y in range(2) for x in range(2)], [100, 1000, 10000, 50000])
            self.assertEqual(record['frames'][0]['preview_transform']['mapping'], 'linear-minmax')

class BridgeTests(unittest.TestCase):
    def test_development_source_is_rejected_before_any_research_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / 'tools').mkdir()
            (repository / 'tools/build_release.py').write_text('fixture', encoding='utf-8')
            (repository / 'product').mkdir()
            for root in (repository, repository / 'product'):
                with self.subTest(root=root), patch.object(fb, 'call') as operation:
                    with self.assertRaisesRegex(ValueError, 'Development source'):
                        initializer.prepare(root, 'Fixture', 'Synthetic only', '2026-10-14')
                    operation.assert_not_called()
                    self.assertFalse((root / '.work').exists())

    def test_initialization_requires_personal_research_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.agents/config').mkdir(parents=True)
            (root / 'AGENTS.md').write_text('Local developer rules', encoding='utf-8')
            (root / '.agents/config/project-layout.json').write_text('{"directories": [".work"]}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'personal research preset'):
                initializer.prepare(root, 'Fixture', 'Synthetic only', '2026-10-14')
            self.assertFalse((root / '.work').exists())

    def test_new_research_system_creates_wiki_space_and_fills_docx_node(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'draft.xml').write_text('<title>项目现状</title><p>研究范围：合成测试。</p>', encoding='utf-8')
            bridge = fb.Bridge(root)
            observed = []
            filled = False
            def operation(args, workroot, content=None):
                nonlocal filled
                observed.append(args[:2])
                if args[:2] == ['wiki', '+space-list']:
                    return {'ok': True, 'data': {'spaces': [], 'has_more': False}}
                if args[:2] == ['wiki', '+space-create']:
                    return {'ok': True, 'data': {'space_id': 'space123', 'name': '合成研究体系'}}
                if args[:2] == ['wiki', '+node-create']:
                    self.assertIn('space123', args)
                    return {'ok': True, 'data': {'node_token': 'wikiNode', 'obj_token': 'docxNode',
                                                 'obj_type': 'docx', 'resolved_space_id': 'space123'}}
                if args[:2] == ['docs', '+script']:
                    return {'ok': True, 'data': {'assessment': {'status': 'passed'}}}
                if args[:2] == ['docs', '+fetch']:
                    body = '<p>研究范围：合成测试。</p>' if filled else ''
                    return {'ok': True, 'data': {'document': {'document_id': 'docxNode',
                        'url': 'https://example.feishu.cn/docx/docxNode', 'revision_id': 2 if filled else 1,
                        'content': '<title>项目现状</title>' + body}}}
                if args[:2] == ['docs', '+update']:
                    self.assertEqual(args[args.index('--command') + 1], 'append')
                    self.assertIn('<p>研究范围：合成测试。</p>', content)
                    filled = True
                    return {'ok': True, 'data': {'result': 'success', 'warnings': []}}
                raise AssertionError(args)
            with patch.object(fb, 'call', side_effect=operation):
                space = bridge.wiki_space('合成研究体系')
                result = bridge.create_in_wiki('CURRENT_STATE', Path('draft.xml'), space['space_id'])
            self.assertTrue(result['ok'])
            self.assertEqual(bridge.registry['wiki_space']['space_id'], 'space123')
            self.assertEqual(bridge.registry['documents']['CURRENT_STATE']['wiki_node_token'], 'wikiNode')
            self.assertEqual(bridge.registry['documents']['CURRENT_STATE']['url'], 'https://example.feishu.cn/docx/docxNode')
            self.assertNotIn(['docs', '+create'], observed)

    def test_ambiguous_wiki_space_create_never_repeats(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = fb.Bridge(Path(directory))
            def operation(args, root, content=None):
                if args[:2] == ['wiki', '+space-list']:
                    return {'ok': True, 'data': {'spaces': [], 'has_more': False}}
                raise RuntimeError('synthetic uncertain create result')
            with patch.object(fb, 'call', side_effect=operation):
                with self.assertRaises(RuntimeError): bridge.wiki_space('合成研究体系')
                with self.assertRaises(ValueError): bridge.wiki_space('合成研究体系')
            self.assertTrue((Path(directory) / '.work/feishu/pending/wiki-space.json').is_file())

    def test_ambiguous_create_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'draft.xml').write_text('<title>Fixture</title><p>Body</p>', encoding='utf-8')
            bridge = fb.Bridge(root)
            def call(args, root, content=None):
                if '+script' in args: return {'ok': True, 'data': {'assessment': {'status': 'passed'}}}
                raise RuntimeError('synthetic uncertain network failure')
            with patch.object(fb, 'call', side_effect=call):
                with self.assertRaises(RuntimeError): bridge.create('fixture', Path('draft.xml'))
                with self.assertRaises(ValueError): bridge.create('fixture', Path('draft.xml'))
            self.assertTrue((root / '.work/feishu/pending/fixture.json').is_file())

    def test_created_doc_remains_bound_on_failed_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'draft.xml').write_text('<title>Fixture</title><p>Body</p>', encoding='utf-8')
            bridge = fb.Bridge(root)
            def call(args, root, content=None):
                if '+script' in args: return {'ok': True, 'data': {'assessment': {'status': 'passed'}}}
                if '+create' in args: return {'ok': True, 'data': {'document': {'document_id': 'fixtureDoc', 'url': 'https://example.feishu.cn/docx/fixtureDoc', 'revision_id': 1}, 'warnings': []}}
                raise RuntimeError('synthetic readback failure')
            with patch.object(fb, 'call', side_effect=call):
                with self.assertRaises(RuntimeError): bridge.create('fixture', Path('draft.xml'))
                self.assertEqual(bridge.registry['documents']['fixture']['document_id'], 'fixtureDoc')
                with self.assertRaises(ValueError): bridge.create('fixture', Path('draft.xml'))

    def test_revision_conflict_prevents_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = fb.Bridge(Path(directory))
            with patch.object(bridge, 'fetch', return_value={'data': {'document': {'revision_id': 2}}}), patch.object(fb, 'call') as operation:
                with self.assertRaises(ValueError): bridge.patch('x', 'append', Path('none.xml'), 1, None, None, False)
                operation.assert_not_called()

    def test_paths_stay_in_project(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError): fb.local(Path(directory), '../outside')

    def test_blank_init_and_existing_state_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.agents/config').mkdir(parents=True)
            (root / 'AGENTS.md').write_text('User rules', encoding='utf-8')
            (root / '.agents/config/project-layout.json').write_text(json.dumps({'workspace_kind': 'personal-research', 'directories': ['.work', 'outputs/reports']}), encoding='utf-8')
            manifest = initializer.prepare(root, 'Synthetic project', 'Fixture only', '2026-10-13')
            self.assertEqual(len(manifest['documents']), 3)
            self.assertEqual([fb.parse_xml((root / path).read_text(encoding='utf-8'))[0].text
                              for path in manifest['documents'].values()],
                             ['项目现状', '项目故事', '研究问题'])
            self.assertEqual((root / 'AGENTS.md').read_text(), 'User rules')
            for path in manifest['documents'].values():
                self.assertNotIn('OBS-001', (root / path).read_text(encoding='utf-8'))
            fb.dump(root / '.agents/config/feishu-documents.json', {'documents': {'CURRENT_STATE': {'document_id': 'existing'}}})
            with self.assertRaises(ValueError): initializer.prepare(root, 'Synthetic project', 'Fixture only', '2026-10-13')

if __name__ == '__main__': unittest.main()
