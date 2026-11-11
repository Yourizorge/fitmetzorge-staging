"""Pure adapter regressions. These tests are NOT real PG/Auth evidence."""
import copy
import hashlib
import io
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from pg_auth_component import runner as m


def report():
    return {'status': 'LOCAL_AUTH_FAILURE_COMPONENT_PASS',
            'cases': [{'case': name, 'component_case_pass': True} for name in m.CASES],
            'diagnostic_totals': {'all_managed_observations_complete': True},
            'full_chain_admission': False, 'global_auth_zero_claim': False,
            'full_auth_cleanup_proven': False}


class ContractTests(unittest.TestCase):
    def test_exact_eleven(self):
        m.checked_report(report())

    def test_subset_rejected(self):
        value = report(); value['cases'].pop()
        with self.assertRaisesRegex(ValueError, 'case_set'): m.checked_report(value)

    def test_duplicate_rejected(self):
        value = report(); value['cases'][-1] = value['cases'][0]
        with self.assertRaisesRegex(ValueError, 'case_set'): m.checked_report(value)

    def test_failed_case_rejected(self):
        value = report(); value['cases'][0]['component_case_pass'] = False
        with self.assertRaisesRegex(ValueError, 'case_failed'): m.checked_report(value)

    def test_numeric_unknown_rejected(self):
        value = report(); value['diagnostic_totals']['all_managed_observations_complete'] = False
        with self.assertRaisesRegex(ValueError, 'numeric_incomplete'): m.checked_report(value)

    def test_overclaim_rejected(self):
        for key in ('full_chain_admission', 'global_auth_zero_claim', 'full_auth_cleanup_proven'):
            with self.subTest(key=key):
                value = report(); value[key] = True
                with self.assertRaisesRegex(ValueError, 'overclaim'): m.checked_report(value)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.ca = self.root / 'fmz-ci-ca.crt'; self.ca.write_text('PRIVATE_REVIEW_SENTINEL')
        self.gate = types.SimpleNamespace(out=self.root, work=self.root)
        from psycopg.conninfo import make_conninfo
        self.ctx = {'dsn': make_conninfo(host='127.0.0.1', dbname='postgres', sslmode='verify-full', sslrootcert=str(self.ca)),
                    'auth': types.SimpleNamespace(url='http://127.0.0.1:59999'), 'test_admin_token': 'PRIVATE_REVIEW_SENTINEL'}
        self.run_id = 'f366e341-56a3-42b6-bd9f-a6c73fcbf9ec'
        self.env = patch.dict(os.environ, {'GITHUB_ACTIONS': 'true',
            'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging', 'GITHUB_SHA': '1'*40, 'GITHUB_RUN_ID': '123'}, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        self.platform = patch.object(m.sys, 'platform', 'linux')
        self.platform.start(); self.addCleanup(self.platform.stop)
        self.bind = patch.object(m.module_binding, 'verify', return_value={'unit_only': True})
        self.verify = self.bind.start(); self.addCleanup(self.bind.stop)

    def test_local_preflight_does_no_sql(self):
        self.assertEqual(m.preflight(self.gate, self.ctx, self.run_id), {'unit_only': True})

    def test_remote_denied_before_binding(self):
        self.ctx['dsn'] = self.ctx['dsn'].replace('127.0.0.1', 'db.invalid')
        with self.assertRaisesRegex(ValueError, 'local_tls'): m.preflight(self.gate, self.ctx, self.run_id)
        self.verify.assert_not_called()

    def test_hosted_origin_denied(self):
        self.ctx['auth'].url = 'https://example.invalid'
        with self.assertRaisesRegex(ValueError, 'private_context'): m.preflight(self.gate, self.ctx, self.run_id)

    def test_old_uuid_denied(self):
        with self.assertRaisesRegex(ValueError, 'fresh_uuid'): m.preflight(self.gate, self.ctx, m.engine.OLD_RUN)

    def test_existing_claim_no_retry(self):
        (self.root / ('auth_failure_' + self.run_id)).mkdir()
        with self.assertRaisesRegex(ValueError, 'no_retry'): m.preflight(self.gate, self.ctx, self.run_id)

    def test_missing_ci_denied(self):
        os.environ.pop('GITHUB_ACTIONS')
        with self.assertRaisesRegex(ValueError, 'ci_linux_only'): m.preflight(self.gate, self.ctx, self.run_id)

    def test_archive_collision_denied_before_mutation(self):
        (self.root / 'case-original-index.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'output_collision'): m.preflight(self.gate, self.ctx, self.run_id)

    def test_service_environment_denied(self):
        os.environ['PGSERVICE'] = 'PRIVATE_REVIEW_SENTINEL'
        with self.assertRaisesRegex(ValueError, 'local_tls'): m.preflight(self.gate, self.ctx, self.run_id)

    def test_source_failure_before_sql(self):
        self.verify.side_effect = ValueError('source_changed')
        self.ctx['admin'] = types.SimpleNamespace(execute=lambda *_: self.fail('SQL before source binding'))
        with self.assertRaisesRegex(ValueError, 'source_changed'): m.run(self.gate, self.ctx, run_id=self.run_id)


class OriginalTests(unittest.TestCase):
    def test_changed_original_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            original = {'cases': [], 'safety_reconciliations': [], 'preparation_run_id': 'x'}
            (root / 'auth-failure-component.json').write_text(json.dumps(original))
            registry = types.SimpleNamespace(_recordsets=[])
            changed = copy.deepcopy(original); changed['preparation_run_id'] = 'different'
            with self.assertRaisesRegex(ValueError, 'engine_original_changed'):
                m.originals(types.SimpleNamespace(out=root), registry, changed)

    def test_exact_nested_originals_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            private = root / 'private'; private.mkdir()
            raw = b'{"kind":"closed"}'
            (private / '0000-closed.json').write_bytes(raw)
            records = types.SimpleNamespace(folder=private,
                _hashes={'0000-closed.json': hashlib.sha256(raw).hexdigest()},
                validate=lambda: {'0000-closed.json': raw})
            (root / 'unrelated.json').write_text('PRIVATE_REVIEW_SENTINEL')
            refs = m.originals(types.SimpleNamespace(out=root), types.SimpleNamespace(_recordsets=[records]), None)
            self.assertEqual([ref['path'] for ref in refs], ['private/0000-closed.json'])


class LifetimeTests(unittest.TestCase):
    """Control-flow mocks only; every produced object stays in a temp folder."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.saved = {}; self.events = []
        self.gate = types.SimpleNamespace(out=pathlib.Path(self.temp.name),
            save=lambda name, value: self.saved.__setitem__(name, value))
        self.ctx = {'admin': types.SimpleNamespace(execute=lambda sql:
            types.SimpleNamespace(fetchone=lambda: {'version': 170006, 'ssl': True}))}
        self.registry = types.SimpleNamespace(case_transport_factory=lambda *_: None,
            close_and_drain=lambda: self.events.append('drain') or object(), valid_proof=lambda proof: True)
        self.value = report(); self.value['retained_claims'] = ['admin_unknown']
        def execute(*args, **kwargs):
            self.events.append('engine')
            self.assertIs(kwargs['safety_reconciliation'], False)
            return self.value
        patches = (
            patch.object(m, 'preflight', return_value={'unit_only': True}),
            patch.object(m.engine, 'context_from_ci', return_value={'private': 'PRIVATE_REVIEW_SENTINEL'}),
            patch.object(m.engine, 'run', side_effect=execute),
            patch.object(m.tracked, 'Registry', return_value=self.registry),
            patch.object(m, 'originals', return_value=[]),
            patch.object(m.archive, 'pack', side_effect=lambda *_: self.events.append('export') or {'unit_only': True}),
            patch.dict(os.environ, {'GITHUB_SHA': '1'*40, 'GITHUB_RUN_ID': '123'}))
        self.mocks = [p.start() for p in patches]
        for p in patches: self.addCleanup(p.stop)

    def call(self):
        return m.run(self.gate, self.ctx, run_id='f366e341-56a3-42b6-bd9f-a6c73fcbf9ec')

    def test_drain_before_export_never_cleanup_promotion(self):
        result = self.call()
        self.assertEqual(self.events, ['engine', 'drain', 'export'])
        self.assertFalse(hasattr(self.gate, 'auth_failure_context'))
        self.assertEqual(result['retained_claims'], ['admin_unknown'])
        self.assertFalse(result['parent_cleanup_authorized'])
        self.assertFalse(result['full_chain_admission'])
        self.assertFalse(result['worker_exit_coverage'])
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL', json.dumps(self.saved))

    def test_drain_timeout_no_component_success(self):
        def timeout(): raise TimeoutError('PRIVATE_REVIEW_SENTINEL')
        self.registry.close_and_drain = timeout
        with self.assertRaises(TimeoutError): self.call()
        self.assertEqual(self.saved['pg-auth-component-result.json']['status'], 'NO_GO')
        self.assertFalse(self.saved['pg-auth-component-result.json']['registered_requests_closed'])

    def test_original_failure_survives_drain_failure(self):
        original = RuntimeError('original_dispatch_unknown')
        self.mocks[2].side_effect = original
        def timeout(): raise TimeoutError('PRIVATE_REVIEW_SENTINEL')
        self.registry.close_and_drain = timeout
        with self.assertRaises(RuntimeError) as caught: self.call()
        self.assertIs(caught.exception, original)
        self.assertEqual(original.__notes__, ['component_drain_secondary:TimeoutError'])

    def test_original_failure_survives_export_failure(self):
        original = RuntimeError('original_dispatch_unknown')
        self.mocks[2].side_effect = original
        self.mocks[5].side_effect = OSError('PRIVATE_REVIEW_SENTINEL')
        with self.assertRaises(RuntimeError) as caught: self.call()
        self.assertIs(caught.exception, original)
        self.assertIn('component_export_secondary:OSError', original.__notes__)

    def test_export_failure_never_success(self):
        self.mocks[5].side_effect = OSError('PRIVATE_REVIEW_SENTINEL')
        with self.assertRaises(OSError): self.call()
        self.assertNotIn('pg-auth-component-result.json', self.saved)

    def test_failed_case_report_no_partial_pass(self):
        self.value['cases'][0]['component_case_pass'] = False
        with self.assertRaisesRegex(ValueError, 'case_failed'): self.call()
        self.assertEqual(self.saved['pg-auth-component-result.json']['status'], 'NO_GO')

    def test_artifact_bound_before_packing(self):
        self.mocks[4].return_value = [{'bytes': 1}] * 1025
        with self.assertRaisesRegex(ValueError, 'component_artifact_bound'): self.call()
        self.mocks[5].assert_not_called()

    def test_artifact_size_before_packing(self):
        self.mocks[4].return_value = [{'bytes': 8_000_001}]
        with self.assertRaisesRegex(ValueError, 'component_artifact_bound'): self.call()
        self.mocks[5].assert_not_called()


if __name__ == '__main__':
    unittest.main()
