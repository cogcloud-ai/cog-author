"""Feedback cannot migrate between candidates or widen the accepted contract."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import cog_core as core
import task_logic as logic


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads((ROOT / 'examples/author-bundle.json').read_text())
        self.source = json.loads((ROOT / 'examples/authored-payload.json').read_text())
        self.author = core._envelope('ask', True, payload=copy.deepcopy(self.source), binding={'source': 'synthetic-test'})
        self.review_request = {'operation': 'review', 'contract': self.source['contract'], 'files': self.source['files'], 'evidence': []}
        self.review = {'envelope': 1, 'ok': True, 'error': None, 'problems': [],
                       'cog': {'id': 'openteams/cog-build-evaluator', 'version': '0.1.0'},
                       'task': 'ask-composed', 'payload': {'classification': 'insufficient_evidence', 'abstained': False, 'reason': 'Cases have not been run.', 'test_cases': [], 'assessments': [], 'findings': []}, 'binding': {'source': 'synthetic-test'}}
        self.scope = {'paths': ['src/task_logic.py'], 'criterion_ids': [self.source['contract']['acceptance_criteria'][0]['id']]}

    def prepare(self):
        return logic.prepare_revision(self.original, self.author, self.review_request, self.review, self.scope)

    def test_durable_request_keeps_full_contract_source_and_review(self):
        request = self.prepare()
        self.assertEqual(core.validate_input(request), [])
        self.assertEqual(request['contract'], self.original['contract'])
        self.assertEqual(len(request['materials']), len(self.source['files']))
        self.assertEqual(request['revision']['candidate_sha256'], logic.candidate_digest(request['contract'], self.source['files']))
        self.assertEqual(request['revision']['review_envelope'], self.review)

    def test_different_candidate_or_contract_and_tampered_review_are_rejected(self):
        mutations = [lambda r: r['review_request']['files'][0].update(content='different source'),
                     lambda r: r['review_request']['contract'].update(purpose='different contract'),
                     lambda r: r['review_envelope']['payload'].update(reason='changed after preparation'),
                     lambda r: r.update(candidate_sha256='0' * 64)]
        for mutate in mutations:
            request = copy.deepcopy(self.prepare())
            mutate(request['revision'])
            with self.subTest(mutation=mutate):
                self.assertTrue(core.validate_input(request))

    def test_bound_evidence_from_another_candidate_cannot_be_reused(self):
        self.review_request['evidence'] = [{'id': 'old', 'criterion_id': self.scope['criterion_ids'][0], 'candidate_sha256': '0' * 64, 'kind': 'execution', 'status': 'passed', 'text': 'Old candidate'}]
        with self.assertRaisesRegex(ValueError, 'different candidate'):
            self.prepare()

    def test_changes_outside_scope_and_unrelated_requirement_removal_fail(self):
        request = self.prepare()
        changed = copy.deepcopy(self.source)
        next(row for row in changed['files'] if row['path'] == 'src/task_logic.py')['content'] += '\n# Scoped repair\n'
        self.assertEqual(core.validate_output(changed, request), [])
        next(row for row in changed['files'] if row['path'] == 'tests/test_cog.py')['content'] += '\n# Unrelated edit\n'
        self.assertTrue(any('outside' in p['detail'] for p in core.validate_output(changed, request)))
        changed = copy.deepcopy(self.source)
        changed['contract']['acceptance_criteria'].pop()
        self.assertTrue(any('preserve' in p['detail'] for p in core.validate_output(changed, request)))

    def test_original_and_revised_material_references_are_hydrated_before_identity_checks(self):
        for row in self.author['payload']['files']:
            if row['path'].endswith('.json') and row['path'].startswith('context/'):
                content = row['content']; sha = hashlib.sha256(content.encode()).hexdigest()
                self.original['materials'].append({'path': row['path'], 'content': content, 'sha256': sha})
                row.pop('content'); row.update(material_ref=row['path'], material_sha256=sha)
        request = self.prepare()
        revised = copy.deepcopy(self.author['payload'])
        self.assertEqual(core.validate_output(revised, request), [])
        self.assertEqual(logic.hydrate(revised, request)['files'], self.review_request['files'])

    def test_declared_lifecycle_cli_emits_the_validated_request(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'request.json'
            path.write_text(json.dumps({'author_request': self.original, 'author_envelope': self.author, 'review_request': self.review_request, 'review_envelope': self.review, 'allowed_change_scope': self.scope}))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/prepare_revision.py'), '--request', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            envelope = json.loads(result.stdout)
            self.assertTrue(envelope['ok'])
            self.assertEqual(core.validate_input(envelope['payload']['request']), [])
