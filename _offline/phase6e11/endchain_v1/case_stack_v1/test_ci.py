"""Matrix entry contracts, without any actual transport or subprocess."""
import contextlib
import importlib
import io
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
c = importlib.import_module('case_stack_v1.ci')


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.env = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1',
            'GITHUB_SHA': 'a'*40, 'GITHUB_RUN_ID': '123456789',
            'CANDIDATE_BLOB': 'not-printed-fixture', 'CANDIDATE_SHA256': 'b'*64,
            'CASE_NAME': 'normal', 'GITHUB_WORKSPACE': '/fixture'}
        self.adapter = types.SimpleNamespace(READY=True,
            CASE_NAMES=('normal',) + tuple('fault_' + str(i) for i in range(14)),
            SOURCES=('_offline/phase6e11/endchain_v1/quota_candidate_v1/case_ci.py',),
            run=lambda *a, **k: None)

    def test_same_run_candidate_no_rewrite(self):
        original = dict(self.env)
        name, sources = c._environment(self.env, self.adapter)
        self.assertEqual(name, 'normal')
        self.assertEqual(self.env, original)
        self.assertTrue(set(c.SOURCES) <= sources)

    def test_unknown_case_rejected(self):
        self.env['CASE_NAME'] = '../secret'
        with self.assertRaises(ValueError): c._environment(self.env, self.adapter)

    def test_missing_candidate_and_retry_rejected(self):
        for key, value in [('CANDIDATE_BLOB', ''), ('CANDIDATE_SHA256', 'bad'),
                           ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_SHA', 'bad')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                c._environment({**self.env, key: value}, self.adapter)

    def test_not_ready_has_no_harness_import(self):
        self.adapter.READY = False
        output = io.StringIO()
        with patch.object(c, '_adapter', return_value=self.adapter), patch.dict(os.environ, self.env), \
             patch.dict(sys.modules, {'admission_ci': None}), contextlib.redirect_stdout(output):
            self.assertEqual(c.main([]), 1)
        self.assertEqual(json.loads(output.getvalue())['status'], 'ADAPTER_NOT_READY')
        self.assertNotIn(self.env['CANDIDATE_BLOB'], output.getvalue())

    def test_help_does_not_import_adapter(self):
        with patch.object(c, '_adapter', side_effect=AssertionError('import')), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
            c.main(['--help'])
        self.assertEqual(error.exception.code, 0)

    def test_exact_fifteen_and_explicit_source_inventory(self):
        self.adapter.CASE_NAMES = ('normal',)
        with self.assertRaises(ValueError): c._environment(self.env, self.adapter)
        self.adapter.CASE_NAMES = ('normal',) + tuple('fault_' + str(i) for i in range(14))
        self.adapter.SOURCES += ('_offline/../outside.py',)
        with self.assertRaises(ValueError): c._environment(self.env, self.adapter)

    def test_entry_same_gate_actual_adapter_and_no_suite(self):
        events = []
        with tempfile.TemporaryDirectory() as folder:
            out = pathlib.Path(folder)
            (out/'candidate.json').write_text(json.dumps({'sources': {}}))
            class Gate:
                def __init__(self):
                    self.out, self.sources, self.result = out, out, {}
                    events.append('construct')
                def fetch(self): events.append('fetch'); return ['fixture']
                def bind_modules(self, *args): events.append('bind')
                def install(self): events.append('install')
                def save(self, name, value):
                    with (out/name).open('x') as stream: json.dump(value, stream)
            def run(gate, migrations, name, *, bootstrap):
                events.append('actual_adapter')
                self.assertIsInstance(gate, Gate)
                self.assertIs(bootstrap, c.bootstrap)
                self.assertEqual(migrations, ['fixture'])
                return {'status': 'CASE_PASS', 'case_name': name, 'source_commit': 'a'*40,
                        'ci_run': '123456789', 'candidate_sha256': 'b'*64}
            self.adapter.run = run
            legacy = types.SimpleNamespace(EXTRA=set())
            admission = types.SimpleNamespace(EXTRA=set(), Gate=Gate,
                app=types.SimpleNamespace(previous=types.SimpleNamespace(
                    prior=types.SimpleNamespace(old=legacy))))
            binding = types.SimpleNamespace(verify_all=lambda *a: {'checked': True})
            with patch.object(c, '_adapter', return_value=self.adapter), \
                 patch.dict(os.environ, self.env), patch.dict(sys.modules, {
                    'admission_ci': admission, 'ci_source_binding': binding}), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(c.main([]), 0)
            self.assertLess(events.index('fetch'), events.index('install'))
            self.assertLess(events.index('install'), events.index('actual_adapter'))
            result = json.loads((out/'result.json').read_text())
            self.assertFalse(result['full_chain_admission'])
            self.assertTrue(result['matrix_aggregation_required'])
            self.assertTrue(set(c.SOURCES) <= legacy.EXTRA)

    def test_matrix_result_write_failure_keeps_primary_and_never_passes(self):
        for failed_run in (False, True):
            with self.subTest(failed_run=failed_run), tempfile.TemporaryDirectory() as folder:
                out = pathlib.Path(folder)
                (out/'candidate.json').write_text(json.dumps({'sources': {}}))
                writes = []
                class Gate:
                    def __init__(self):
                        self.out, self.sources, self.result = out, out, {}
                    def fetch(self): return ['fixture']
                    def bind_modules(self, *args): pass
                    def install(self): pass
                    def save(self, name, value):
                        writes.append(name)
                        if name == 'result.json':
                            raise OSError('PRIVATE_MATRIX_RESULT')
                def run(gate, migrations, name, *, bootstrap):
                    if failed_run:
                        raise ValueError('PRIVATE_ADAPTER_PRIMARY')
                    return {'status': 'CASE_PASS', 'case_name': name, 'source_commit': 'a'*40,
                            'ci_run': '123456789', 'candidate_sha256': 'b'*64}
                self.adapter.run = run
                admission = types.SimpleNamespace(EXTRA=set(), Gate=Gate,
                    app=types.SimpleNamespace(previous=types.SimpleNamespace(
                        prior=types.SimpleNamespace(old=types.SimpleNamespace(EXTRA=set())))))
                binding = types.SimpleNamespace(verify_all=lambda *a: {'checked': True})
                output = io.StringIO()
                with patch.object(c, '_adapter', return_value=self.adapter), \
                     patch.dict(os.environ, self.env), patch.dict(sys.modules, {
                        'admission_ci': admission, 'ci_source_binding': binding}), \
                     contextlib.redirect_stdout(output):
                    self.assertEqual(c.main([]), 1)
                value = json.loads(output.getvalue())
                self.assertEqual(value['status'], 'NO_GO')
                self.assertEqual(value['error_type'], 'ValueError' if failed_run else 'OSError')
                self.assertEqual(value['result_write_error_type'], 'OSError')
                self.assertFalse(value['full_chain_admission'])
                self.assertEqual(writes.count('result.json'), 1)
                self.assertNotIn('PRIVATE', output.getvalue())


if __name__ == '__main__':
    unittest.main()
