"""Pure validation and failure regressions; subprocess doubles are not PG proof."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pg_auth_component import worker as m


def result(case='readonly'):
    return {'case': case, 'pg17_tls_readonly': True, 'query_confirmed': case == 'readonly',
        'sqlstate': '57014' if case == 'statement_timeout' else None, 'rollback_confirmed': True,
        'explicit_commands': 4, 'connection_closed': True, 'libpq_version': 170005,
        'implicit_native_sql_bound': None, 'full_chain_admission': False}


class ResultTests(unittest.TestCase):
    def test_child_environment_is_closed_allowlist(self):
        parent = dict(GITHUB_ACTIONS='true', GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging',
            GITHUB_SHA='1'*40, GITHUB_RUN_ID='123', GH_READ_TOKEN='PRIVATE_REVIEW_SENTINEL',
            PGPASSWORD='PRIVATE_REVIEW_SENTINEL', PGHOST='db.invalid',
            PYTHONPATH='/untrusted', LD_PRELOAD='/untrusted', PATH='/untrusted', HOME='/untrusted')
        value = m.child_environment(parent)
        self.assertEqual(set(value), {'GITHUB_ACTIONS','GITHUB_REPOSITORY','GITHUB_SHA',
            'GITHUB_RUN_ID','PATH','LANG','LC_ALL'})
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL', json.dumps(value))
        self.assertEqual(value['PATH'], '/usr/bin:/bin')

    def test_exact_observation(self):
        for case in ('readonly', 'statement_timeout'):
            value = result(case)
            self.assertEqual(m.checked_result(m.compiler.canonical(value), case), value)

    def test_lost_result_not_reconstructed(self):
        self.assertIsNone(m.checked_result(b'', 'lost_result'))
        with self.assertRaises(ValueError): m.checked_result(b'{}', 'lost_result')

    def test_missing_result_no_pass(self):
        with self.assertRaises(ValueError): m.checked_result(b'', 'readonly')

    def test_unknown_native_cost_not_zero(self):
        value = result(); value['implicit_native_sql_bound'] = 0
        with self.assertRaisesRegex(ValueError, 'observation'):
            m.checked_result(m.compiler.canonical(value), 'readonly')

    def test_missing_rollback_no_pass(self):
        value = result(); value['rollback_confirmed'] = False
        with self.assertRaisesRegex(ValueError, 'observation'):
            m.checked_result(m.compiler.canonical(value), 'readonly')

    def test_bool_count_rejected(self):
        value = result(); value['explicit_commands'] = True
        with self.assertRaisesRegex(ValueError, 'observation'):
            m.checked_result(m.compiler.canonical(value), 'readonly')

    def test_unapproved_field_rejected(self):
        value = result(); value['private'] = 'PRIVATE_REVIEW_SENTINEL'
        with self.assertRaisesRegex(ValueError, 'fields'):
            m.checked_result(m.compiler.canonical(value), 'readonly')

    def test_not_original_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, 'original_bytes'):
            m.checked_result(json.dumps(result()).encode(), 'readonly')


class Process:
    """Explicit unit double; never exported as a live worker receipt."""
    pid = 123
    stdin = stdout = stderr = None
    returncode = None
    def __init__(self, fault=None): self.fault = fault
    def communicate(self, *, input, timeout):
        if self.fault in ('timeout', 'terminate', 'reap'):
            raise subprocess.TimeoutExpired('unit', timeout)
        case = json.loads(input)['case']
        self.returncode = 1 if self.fault == 'nonzero' else 0
        return (b'' if case == 'lost_result' else m.compiler.canonical(result(case))), None
    def wait(self, timeout):
        if self.fault == 'reap': raise subprocess.TimeoutExpired('unit', timeout)
        if self.returncode is None: self.returncode = -9
        return self.returncode
    def poll(self): return self.returncode
    def kill(self):
        if self.fault == 'terminate': raise OSError('PRIVATE_REVIEW_SENTINEL')
        self.returncode = -9


class LifetimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.saved = {}
        self.gate = types.SimpleNamespace(out=pathlib.Path(self.temp.name))
        def save(gate, name, value):
            self.saved[name] = copy.deepcopy(value)
            return {'path': name, 'sha256': '1'*64, 'bytes': 1, 'unit_only': True}
        patches = (
            patch.object(m, 'preflight', return_value={'unit_only': True}),
            patch.object(m.module_binding, 'verify', return_value={'unit_only': True}),
            patch.object(m.evidence, 'save', side_effect=save),
            patch.object(m.subprocess, 'Popen', side_effect=lambda *a, **k: Process()),
            patch.dict(m.os.environ, {'GITHUB_SHA': '1'*40, 'GITHUB_RUN_ID': '123',
                'GITHUB_ACTIONS':'true', 'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging'}))
        self.mocks = [p.start() for p in patches]
        for p in patches: self.addCleanup(p.stop)

    def call(self):
        return m.run(self.gate, {'dsn': 'PRIVATE_REVIEW_SENTINEL'}, run_id='f366e341-56a3-42b6-bd9f-a6c73fcbf9ec')

    def test_three_cases_not_fullmatrix(self):
        value = self.call()
        self.assertEqual(len(value['cases']), 3)
        self.assertIsNone(value['implicit_native_sql_bound'])
        self.assertFalse(value['full_chain_admission'])
        self.assertIsNone(value['cases'][-1]['result_ref'])
        self.assertTrue(value['cases'][-1]['lost_result_remains_no_go'])
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL', json.dumps(self.saved))

    def test_popen_does_not_inherit_parent_credentials(self):
        with patch.dict(m.os.environ, {'GH_READ_TOKEN':'PRIVATE_REVIEW_SENTINEL',
                                      'PGOPTIONS':'PRIVATE_REVIEW_SENTINEL'}):
            self.call()
        for call in self.mocks[3].call_args_list:
            self.assertNotIn('GH_READ_TOKEN', call.kwargs['env'])
            self.assertNotIn('PGOPTIONS', call.kwargs['env'])
            self.assertNotIn('PRIVATE_REVIEW_SENTINEL', json.dumps(call.kwargs['env']))

    def test_timeout_is_sticky_after_reap(self):
        self.mocks[3].side_effect = lambda *a, **k: Process('timeout')
        with self.assertRaises(subprocess.TimeoutExpired): self.call()
        wait = self.saved['pg-worker-readonly-wait.json']
        self.assertTrue(wait['reaped'])
        self.assertEqual(wait['wait_error_class'], 'TimeoutExpired')
        self.assertNotIn('pg-worker-component-result.json', self.saved)

    def test_terminate_failure_retained(self):
        self.mocks[3].side_effect = lambda *a, **k: Process('terminate')
        with self.assertRaises(subprocess.TimeoutExpired): self.call()
        wait = self.saved['pg-worker-readonly-wait.json']
        self.assertFalse(wait['reaped'])
        self.assertEqual(wait['termination_error_class'], 'OSError')
        self.assertFalse(self.saved['pg-worker-readonly-export.json']['cleanup_authorized'])

    def test_reap_failure_retained(self):
        self.mocks[3].side_effect = lambda *a, **k: Process('reap')
        with self.assertRaises(subprocess.TimeoutExpired): self.call()
        self.assertFalse(self.saved['pg-worker-readonly-wait.json']['reaped'])

    def test_complete_payload_nonzero_exit_denied(self):
        self.mocks[3].side_effect = lambda *a, **k: Process('nonzero')
        with self.assertRaisesRegex(ValueError, 'worker_exit'): self.call()
        self.assertNotIn('pg-worker-readonly-result.json', self.saved)
        self.assertNotIn('pg-worker-component-result.json', self.saved)

    def test_original_timeout_not_masked_by_save_failure(self):
        self.mocks[3].side_effect = lambda *a, **k: Process('timeout')
        self.mocks[2].side_effect = OSError('PRIVATE_REVIEW_SENTINEL')
        with self.assertRaises(subprocess.TimeoutExpired) as caught: self.call()
        self.assertEqual(caught.exception.__notes__, ['component_worker_export_secondary:OSError'])


if __name__ == '__main__': unittest.main()
