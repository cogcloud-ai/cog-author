import copy
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import cog_core as core
import task_logic as logic

def read(path):
    return json.loads((ROOT / path).read_text())

class SharedChecks(unittest.TestCase):
    def setUp(self):
        self.bundle = read('examples/sample-bundle.json')
        self.payload = read('context/output-example.json')

    def test_examples_agree(self):
        self.assertEqual(core.validate_input(self.bundle), [])
        self.assertEqual(core.validate_output(self.payload, self.bundle), [])

    def test_fixtures_have_valid_inputs(self):
        manifest = yaml.safe_load((ROOT / 'cog.yaml').read_text())
        self.assertGreaterEqual(len(manifest['evaluation']['fixtures']), 4)
        for path in manifest['evaluation']['fixtures']:
            fixture = yaml.safe_load((ROOT / path).read_text())
            self.assertEqual(core.validate_input(read(fixture['bundle'])), [], path)

    def test_bad_shapes_report_problems(self):
        for key in self.bundle:
            for bad in [None, 17, [], {'bad': []}]:
                bundle = copy.deepcopy(self.bundle); bundle[key] = bad
                if key in ('identity', 'contract') and bad is None:
                    continue
                if bundle != self.bundle:
                    self.assertTrue(core.validate_input(bundle), (key, bad))
        for key in self.payload:
            bad = copy.deepcopy(self.payload); bad[key] = 17
            self.assertTrue(core.validate_output(bad, self.bundle), key)

    def test_invocation_envelope_and_prompt(self):
        body = {'model': core.MODEL, 'choices': [{'message': {'content': json.dumps(self.payload)}}]}
        response = io.BytesIO(json.dumps(body).encode())
        with patch.object(core, 'health', return_value=(True, 'mock')), patch.object(core.urllib.request, 'urlopen', return_value=response) as call:
            result = core.invoke(self.bundle)
        self.assertTrue(result['ok'])
        self.assertEqual(result['envelope'], 1)
        self.assertEqual(result['payload'], self.payload)
        self.assertEqual(result['problems'], [])
        self.assertEqual(result['binding']['model_identity'], 'verified')
        sent = json.loads(call.call_args.args[0].data)
        self.assertIn(self.bundle['operation'], sent['messages'][1]['content'])

    def test_problem_envelope_is_not_silent_success(self):
        bad = copy.deepcopy(self.payload); bad['classification'] = 'pass' if ROOT.name == 'cog-author' else 'revise'
        body = {'model': core.MODEL, 'choices': [{'message': {'content': json.dumps(bad)}}]}
        with patch.object(core, 'health', return_value=(True, 'mock')), patch.object(core.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(body).encode())):
            result = core.invoke(self.bundle)
        self.assertTrue(result['ok'])
        self.assertTrue(result['problems'])

    def test_invalid_input_never_calls_model(self):
        with patch.object(core.urllib.request, 'urlopen') as call:
            result = core.invoke({})
        self.assertFalse(result['ok'])
        call.assert_not_called()

    def test_abstention_requires_reason(self):
        p = copy.deepcopy(self.payload); p.update(abstained=True, classification='abstained', reason='')
        self.assertTrue(core.validate_output(p, self.bundle))

class AuthorChecks(unittest.TestCase):
    def setUp(self):
        self.bundle = read('examples/author-bundle.json')
        self.payload = read('examples/authored-payload.json')

    def test_complete_authored_source(self):
        self.assertEqual(core.validate_output(self.payload, self.bundle), [])

    def test_author_requires_accepted_contract(self):
        self.bundle['contract'] = None
        self.assertTrue(core.validate_input(self.bundle))

    def test_changed_contract_rejected(self):
        self.payload['contract']['purpose'] = 'Different job'
        self.assertTrue(core.validate_output(self.payload, self.bundle))

    def test_source_paths_and_machinery_protected(self):
        for path in ['../outside.py', '/tmp/owned', '.git/config', 'src/cog_core.py', 'tests/../outside', 'tests\\escape.py', 'tests//x.py']:
            p = copy.deepcopy(self.payload); p['files'].append({'path': path, 'content': 'x'})
            self.assertTrue(core.validate_output(p, self.bundle), path)

    def test_duplicate_and_missing_files(self):
        self.payload['files'].append(self.payload['files'][0])
        self.assertTrue(core.validate_output(self.payload, self.bundle))
        self.payload['files'] = []
        self.assertTrue(core.validate_output(self.payload, self.bundle))

    def test_bad_generated_code_and_example(self):
        for path, content in [('src/task_logic.py', 'invalid python :'), ('context/output-example.json', '{}'), ('context/input-schema.json', '{"$ref":"https://example.invalid/schema"}')]:
            p = copy.deepcopy(self.payload)
            next(f for f in p['files'] if f['path'] == path)['content'] = content
            self.assertTrue(core.validate_output(p, self.bundle), path)

    def test_design_does_not_emit_files(self):
        p = read('context/output-example.json'); p['files'] = [{'path': 'README.md', 'content': 'surprise'}]
        self.assertTrue(core.validate_output(p, read('examples/sample-bundle.json')))

    def test_export_and_refuse_overwrite(self):
        import tempfile
        sys.path.insert(0, str(ROOT / 'scripts'))
        from export_draft import export
        env = {'envelope': 1, 'cog': core.SELF_ID, 'ok': True, 'error': None, 'problems': [], 'payload': self.payload}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'draft'
            export(self.bundle, env, out)
            self.assertTrue((out/'source/src/task_logic.py').exists())
            req = json.loads((out/'smith-request.json').read_text())
            self.assertIsInstance(req['evals']['smoke_fixture'], str)
            self.assertEqual(req['context']['input_schema'], self.bundle['contract']['input_schema'])
            with self.assertRaises(ValueError): export(self.bundle, env, out)
            env['problems'] = [{'severity': 'error'}]
            with self.assertRaises(ValueError): export(self.bundle, env, Path(tmp)/'other')
