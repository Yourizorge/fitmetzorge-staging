"""Offline state tests plus real loopback HTTP relay tests; not GoTrue evidence."""
import copy
import json
import pathlib
import tempfile
import threading
import unittest
import uuid
from email.message import Message
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import auth_failure as af
import auth_failure_transport as transport

COSTS = dict.fromkeys(af.OPERATIONS, 10)


class FakeBackend:
    evidence_kind = 'MOCK_STATE_MACHINE_ONLY'

    def __init__(self):
        self.user = None
        self.sessions = []
        self.commands = 0
        self.calls = []
        self.unknown_terminal = True
        self.delete_effect = True

    def stats(self):
        return self.commands

    def close(self):
        pass

    def difference(self, before, after):
        return {'commands': after - before, 'mock_only': True}

    def http(self, method, path, data=None, token=None, fault=None):
        self.calls.append((method, path))
        self.commands += 3
        body = {}
        if path == '/admin/users':
            self.user = {'id': str(uuid.uuid4()), 'email': data['email'],
                         'marker': data['app_metadata']['auth_failure_claim']}
        elif path.startswith('/token'):
            self.sessions.append(str(uuid.uuid4()))
            body['access_token'] = 'TEST_PRIVATE_TOKEN'
        elif path.startswith('/logout'):
            self.sessions = []
        elif method == 'DELETE' and self.delete_effect:
            self.user = None
            self.sessions = []
        if fault:
            raise transport.UnknownOutcome(self.unknown_terminal)
        return {'status': 200, 'body': body, 'terminal': True}

    def snapshot(self, email, marker, actor, session_ids):
        return {'users': [copy.deepcopy(self.user)] if self.user else [],
                'session_ids': list(self.sessions),
                'counts': {'users': int(self.user is not None), 'identities': int(self.user is not None),
                           'sessions': len(self.sessions), 'refresh_tokens': len(self.sessions),
                           'mfa_amr_claims': len(self.sessions), 'mfa_factors': 0,
                           'one_time_tokens': 0, 'flow_state': 0}}


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def case(self, name, backend=None, costs=None):
        return af.Case(backend or FakeBackend(), self.root / name, str(uuid.uuid4()), name, costs or COSTS)

    def test_all_eleven_failure_paths_state_only(self):
        results = []
        for name in af.CASES:
            with self.subTest(name=name):
                case = self.case(name)
                result = case.execute()
                results.append(result)
                self.assertTrue(result['component_case_pass'], result)
                self.assertEqual(result['execution_status'], 'NO_GO')
                self.assertEqual(result['evidence_kind'], 'MOCK_STATE_MACHINE_ONLY')
                self.assertFalse(result['full_chain_admission'])
                self.assertEqual(result['refunds'], 0)
                self.assertLessEqual(result['native_sql_dispatches'], 12)
                before = [e for e in case.journal.entries if e['phase'] == 'before_dispatch']
                self.assertEqual(len(before), len({e['key'] for e in before}))
                self.assertEqual(sum(e['units'] for e in before), result['prepaid_consumed'])
        self.assertEqual(sum(r['native_sql_dispatches'] for r in results), 95)
        self.assertEqual(sum(len(r['http_dispatches']) for r in results), 27)

    def test_old_uuid_refused_before_claim_or_calls(self):
        backend = FakeBackend()
        with self.assertRaises(ValueError):
            af.Case(backend, self.root / 'old', af.OLD_RUN, 'partial_user', COSTS)
        self.assertFalse((self.root / 'old').exists())
        self.assertEqual(backend.calls, [])

    def test_no_auth_when_complete_reserve_missing(self):
        with self.assertRaises(ValueError):
            self.case('partial_user', costs={'create': 3})
        self.assertFalse((self.root / 'partial_user').exists())

    def test_unknown_mint_retains_claim_no_cleanup(self):
        backend = FakeBackend()
        backend.unknown_terminal = False
        result = self.case('partial_session', backend).execute()
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])
        self.assertEqual(result['http_dispatches'], ['create', 'login'])
        self.assertFalse(result['mint_barrier'])
        self.assertIsNotNone(backend.user)

    def test_zero_after_lost_delete_never_releases_claim(self):
        result = self.case('admin_unknown').execute()
        self.assertTrue(result['cleanup']['zero_observed'])
        self.assertFalse(result['cleanup']['delete_confirmed'])
        self.assertFalse(result['claim_released'])
        self.assertIn('delete', result['http_dispatches'])
        self.assertEqual(result['observed_managed_sql']['delete'], 3)

    def test_residual_rows_prevent_cleanup_confirmation(self):
        backend = FakeBackend()
        backend.delete_effect = False
        result = self.case('partial_user', backend).execute()
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])

    def test_foreign_identity_never_deleted(self):
        backend = FakeBackend()
        backend.user = {'id': str(uuid.uuid4()), 'email': 'unrelated@example.invalid', 'marker': 'foreign'}
        result = self.case('partial_user', backend).execute()
        self.assertFalse(result['claim_released'])
        self.assertEqual(backend.calls, [])

    def test_managed_overrun_stops_further_http_no_refund(self):
        result = self.case('partial_user', costs=dict.fromkeys(af.OPERATIONS, 1)).execute()
        self.assertEqual(result['http_dispatches'], ['create'])
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['managed_within_prepaid'])
        self.assertEqual(result['refunds'], 0)

    def test_crash_claim_cannot_be_reopened(self):
        case = self.case('partial_user')
        with self.assertRaises(FileExistsError):
            af.Case(FakeBackend(), case.journal.folder, case.run_id, 'partial_user', COSTS)

    def test_journal_write_failure_blocks_dispatch(self):
        case = self.case('partial_user')
        case.baseline_absent = True
        original = case.journal.event
        def fail(row):
            if row.get('key') == 'create' and row['phase'] == 'before_dispatch':
                raise OSError('disk_full')
            original(row)
        with patch.object(case.journal, 'event', side_effect=fail):
            with self.assertRaises(OSError):
                case.auth('create')
        self.assertEqual(case.backend.calls, [])

    def test_sensitive_values_not_exported(self):
        case = self.case('duplicate_request')
        password, email = case.password, case.email
        case.execute()
        raw = ''.join(p.read_text() for p in case.journal.folder.iterdir())
        for private in (password, email, 'TEST_PRIVATE_TOKEN', case.actor):
            self.assertNotIn(private, raw)

    def test_prerequisites_block_without_backend(self):
        class Gate:
            def save(self, name, value):
                self.result = value
        gate = Gate()
        with patch.object(af, 'RealBackend', side_effect=AssertionError('must not connect')):
            result = af.run(gate)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result['mutation_started'])

    def test_mint_closed_refuses_login_without_spending(self):
        case = self.case('partial_user')
        case.mint_closed = True
        with self.assertRaises(ValueError):
            case.auth('login')
        self.assertEqual(case.journal.spent, 0)

    def test_failed_final_read_retains_primary_and_claim(self):
        case = self.case('partial_user')
        original = case.snapshot
        def fail(key):
            if key == 'final':
                raise OSError('lost_final_read')
            return original(key)
        with patch.object(case, 'snapshot', side_effect=fail):
            result = case.execute()
        self.assertEqual(result['primary_failure'], 'auth_failure_stop_after_user')
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])

    def test_no_post_dispatch_measurement_never_releases_claim(self):
        case = self.case('partial_user')
        original = case.native
        def fail(key, call):
            if key == 'stats_after_delete':
                case.journal.before(key)
                raise OSError('lost_observer')
            return original(key, call)
        with patch.object(case, 'native', side_effect=fail):
            result = case.execute()
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['http_sql_measurements_complete'])
        self.assertEqual(result['refunds'], 0)

    def test_http_failure_survives_secondary_stats_failure_with_prepaid_events(self):
        backend = FakeBackend()
        calls = 0
        def stats():
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError('PRIVATE_OBSERVER_ERROR')
            return backend.commands
        backend.stats = stats
        case = self.case('login_timeout', backend)
        result = case.execute()
        self.assertEqual(result['primary_failure'], 'auth_failure_http_unknown')
        self.assertEqual(result['primary_failure_detail'], {
            'operation': 'login', 'phase': 'http_dispatch', 'error_class': 'UnknownOutcome'})
        self.assertEqual(result['observer_failures'], [{
            'operation': 'login', 'phase': 'stats_after', 'error_class': 'OSError', 'secondary_to_http': True}])
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])
        self.assertEqual(result['refunds'], 0)
        for key, units in (('login', 10), ('stats_after_login', 1)):
            entries = [e for e in case.journal.entries if e['phase'] == 'before_dispatch' and e['key'] == key]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]['units'], units)
        self.assertTrue(any(e['phase'] == 'unknown' and e['key'] == 'stats_after_login'
                            for e in case.journal.entries))
        self.assertNotIn('PRIVATE_OBSERVER_ERROR', json.dumps(result))

    def test_unknown_journal_failure_preserves_http_primary_claim_and_charge(self):
        for terminal in (True, False):
            with self.subTest(upstream_terminal=terminal):
                backend = FakeBackend()
                backend.unknown_terminal = terminal
                case = af.Case(backend, self.root / str(terminal), str(uuid.uuid4()), 'create_lost_reply', COSTS)
                original_event = case.journal.event
                def fail_unknown(row):
                    if row['phase'] == 'unknown' and row['key'] == 'create':
                        raise OSError('PRIVATE_JOURNAL_FAILURE')
                    original_event(row)
                with patch.object(case.journal, 'event', side_effect=fail_unknown):
                    result = case.execute()
                self.assertEqual(result['primary_failure'], 'auth_failure_http_unknown')
                self.assertEqual(result['primary_failure_detail'], {
                    'operation': 'create', 'phase': 'http_dispatch', 'error_class': 'UnknownOutcome'})
                self.assertEqual(result['journal_failures'], [{
                    'operation': 'create', 'phase': 'http_unknown_receipt', 'error_class': 'OSError',
                    'secondary_to_http': True}])
                self.assertFalse(result['journal_complete'])
                self.assertFalse(result['claim_released'])
                self.assertFalse(result['component_case_pass'])
                self.assertEqual(result['execution_status'], 'NO_GO')
                self.assertEqual(result['refunds'], 0)
                prepaid = [e for e in case.journal.entries if e['phase'] == 'before_dispatch']
                self.assertEqual(sum(e['units'] for e in prepaid), result['prepaid_consumed'])
                self.assertEqual([e['units'] for e in prepaid if e['key'] == 'create'], [10])
                self.assertEqual(sum(path == '/admin/users' for _, path in backend.calls), 1)
                self.assertNotIn('PRIVATE_JOURNAL_FAILURE', json.dumps(result))
                saved = json.loads((case.journal.folder / 'result.json').read_text())
                self.assertEqual(saved['journal_failures'], result['journal_failures'])
                self.assertFalse(saved['claim_released'])
                self.assertFalse(af.reconcile_retained(case)['reconciliation_confirmed'])

    def test_http_failure_survives_secondary_difference_failure(self):
        backend = FakeBackend()
        def difference(before, after):
            raise ValueError('PRIVATE_COUNTER_ERROR')
        backend.difference = difference
        result = self.case('create_lost_reply', backend).execute()
        self.assertEqual(result['primary_failure'], 'auth_failure_http_unknown')
        self.assertEqual(result['primary_failure_detail']['phase'], 'http_dispatch')
        self.assertEqual(result['observer_failures'][0], {
            'operation': 'create', 'phase': 'managed_difference', 'error_class': 'ValueError',
            'secondary_to_http': True})
        self.assertFalse(result['claim_released'])
        self.assertNotIn('PRIVATE_COUNTER_ERROR', json.dumps(result))

    def test_observer_failure_is_primary_when_http_succeeded(self):
        backend = FakeBackend()
        calls = 0
        def stats():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('observer_unavailable')
            return backend.commands
        backend.stats = stats
        result = self.case('partial_user', backend).execute()
        self.assertEqual(result['primary_failure_detail'], {
            'operation': 'create', 'phase': 'stats_after', 'error_class': 'OSError', 'secondary_to_http': False})
        self.assertEqual(result['http_failures'], [])
        self.assertFalse(result['claim_released'])

    def test_unrelated_prerequisite_error_is_blocked_before_backend(self):
        class Gate:
            auth_failure_context = {'dsn': 'not-used', 'auth_url': transport.ORIGINS[0],
                'admin_token': 'not-used', 'run_id': af.OLD_RUN, 'managed_costs': COSTS,
                'environment': 'disposable_ci', 'exclusive_local_auth': True}
            def save(self, name, value):
                pass
        with patch.object(af, 'RealBackend', side_effect=AssertionError('must not connect')):
            self.assertEqual(af.run(Gate())['status'], 'BLOCKED')

    def test_parent_flat_receipt_and_fresh_case_bindings(self):
        class Gate:
            auth_failure_context = {'dsn': 'not-used', 'auth_url': transport.ORIGINS[0],
                'admin_token': 'TEST_PRIVATE_ADMIN', 'run_id': str(uuid.uuid4()), 'managed_costs': COSTS,
                'environment': 'disposable_ci', 'exclusive_local_auth': True}
            def save(self, name, value):
                self.result = value
        gate = Gate()
        gate.out = self.root
        with patch.object(af, 'RealBackend', return_value=FakeBackend()):
            # Separate disposable backend states: unresolved cases must not be
            # silently swept. FakeBackend only models one user, so reset that
            # model between cases; this test checks orchestration, not isolation.
            original = af.Case.execute
            def execute(case):
                case.backend.user = None
                case.backend.sessions = []
                return original(case)
            with patch.object(af.Case, 'execute', execute):
                result = af.run(gate)
        self.assertEqual(result['status'], 'LOCAL_AUTH_FAILURE_COMPONENT_PASS')
        ids = [r['run_id'] for r in result['cases']]
        self.assertEqual(len(set(ids)), 11)
        self.assertNotIn(gate.auth_failure_context['run_id'], ids)
        self.assertEqual(result['retained_claims'], ['admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier'])
        for row in result['cases']:
            journal = row['retained_journal']['files']
            self.assertIn('claim.json', journal)
            self.assertIn('result.json', journal)
            for name, item in journal.items():
                path = self.root / ('auth_failure_' + result['preparation_run_id']) / row['case'] / name
                self.assertEqual(af.hashlib.sha256(path.read_bytes()).hexdigest(), item['sha256'])
        self.assertNotIn('TEST_PRIVATE_ADMIN', json.dumps(result))
        self.assertFalse(result['global_auth_zero_claim'])
        self.assertFalse(result['full_auth_cleanup_proven'])
        self.assertEqual(len(result['retained_object_audit']), 3)

    def test_explicit_reconciliation_preserves_original_and_confirms_owned_zero(self):
        case = self.case('cleanup_interrupted')
        original = case.execute()
        path = case.journal.folder / 'result.json'
        raw = path.read_bytes()
        suffix = af.reconcile_retained(case)
        self.assertTrue(suffix['reconciliation_confirmed'])
        self.assertTrue(suffix['scoped_zero_observed'])
        self.assertTrue(suffix['delete_confirmed'])
        self.assertEqual(suffix['native_sql_dispatches'], 4)
        self.assertEqual(suffix['http_dispatches'], 1)
        self.assertEqual(suffix['prepaid_consumed'], 14)
        self.assertLessEqual(suffix['combined_prepaid_consumed'], original['reserved'])
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(original['execution_status'], 'NO_GO')
        self.assertFalse(original['claim_released'])
        self.assertFalse(suffix['original_claim_released'])
        self.assertFalse(suffix['full_auth_cleanup_proven'])
        self.assertIsNone(case.backend.user)
        before_calls = len(case.backend.calls)
        with self.assertRaises(FileExistsError):
            af.reconcile_retained(case)
        self.assertEqual(len(case.backend.calls), before_calls)

    def test_reconciliation_never_retires_missing_mint_barrier(self):
        case = self.case('missing_mint_barrier')
        original = case.execute()
        suffix = af.reconcile_retained(case)
        self.assertFalse(suffix['reconciliation_confirmed'])
        self.assertEqual(suffix['http_dispatches'], 0)
        self.assertEqual(suffix['native_sql_dispatches'], 1)
        self.assertEqual(suffix['owned_counts_before']['users'], 1)
        self.assertEqual(suffix['owned_counts_before']['sessions'], 1)
        self.assertIn('missing_mint_barrier', suffix['reason'])
        self.assertFalse(original['claim_released'])

    def test_reconciliation_zero_after_unknown_delete_not_retroactive_ack(self):
        case = self.case('admin_unknown')
        case.execute()
        calls = len(case.backend.calls)
        suffix = af.reconcile_retained(case)
        self.assertTrue(suffix['scoped_zero_observed'])
        self.assertFalse(suffix['reconciliation_confirmed'])
        self.assertFalse(suffix['delete_confirmed'])
        self.assertEqual(suffix['http_dispatches'], 0)
        self.assertEqual(len(case.backend.calls), calls)
        self.assertIn('no_replay', suffix['reason'])

    def test_reconciliation_changed_owned_snapshot_blocks_delete(self):
        case = self.case('cleanup_interrupted')
        case.execute()
        case.backend.sessions.append(str(uuid.uuid4()))
        suffix = af.reconcile_retained(case)
        self.assertFalse(suffix['reconciliation_confirmed'])
        self.assertEqual(suffix['http_dispatches'], 0)
        self.assertEqual(suffix['reason'], 'owned_snapshot_changed_or_absence_without_delete_proof')

    def test_reconciliation_uncertain_delete_retains_original_and_charge(self):
        case = self.case('cleanup_interrupted')
        case.execute()
        original = case.backend.http
        def lost(*args, **kwargs):
            original(*args, **kwargs)
            raise transport.UnknownOutcome(False)
        case.backend.http = lost
        suffix = af.reconcile_retained(case)
        self.assertTrue(suffix['scoped_zero_observed'])
        self.assertFalse(suffix['delete_confirmed'])
        self.assertFalse(suffix['reconciliation_confirmed'])
        self.assertEqual(suffix['prepaid_consumed'], 14)
        self.assertEqual(suffix['refunds'], 0)
        self.assertTrue(suffix['original_result_unchanged'])

    def test_reconciliation_foreign_user_never_deleted(self):
        case = self.case('cleanup_interrupted')
        case.execute()
        case.backend.user['marker'] = 'foreign'
        suffix = af.reconcile_retained(case)
        self.assertFalse(suffix['reconciliation_confirmed'])
        self.assertEqual(suffix['http_dispatches'], 0)

    def test_reconciliation_receipt_failure_never_confirms_cleanup(self):
        for phase in ('confirmed', 'managed_observed'):
            with self.subTest(phase=phase):
                case = af.Case(FakeBackend(), self.root / phase, str(uuid.uuid4()),
                               'cleanup_interrupted', COSTS)
                case.execute()
                raw = (case.journal.folder / 'result.json').read_bytes()
                original_event = af.ReconciliationJournal.event
                def fail(journal, row):
                    if row['phase'] == phase and row.get('key') == 'delete':
                        raise OSError('PRIVATE_RECEIPT_ERROR')
                    original_event(journal, row)
                with patch.object(af.ReconciliationJournal, 'event', fail):
                    suffix = af.reconcile_retained(case)
                self.assertFalse(suffix['reconciliation_confirmed'])
                self.assertEqual(suffix['status'], 'BLOCKED')
                self.assertEqual(suffix['refunds'], 0)
                self.assertEqual(suffix['prepaid_consumed'], 14)
                self.assertEqual((case.journal.folder / 'result.json').read_bytes(), raw)
                self.assertNotIn('PRIVATE_RECEIPT_ERROR', json.dumps(suffix))

    def test_incomplete_final_snapshot_never_releases_claim(self):
        case = self.case('partial_user')
        original_snapshot = case.backend.snapshot
        def incomplete(*args):
            value = original_snapshot(*args)
            if any(method == 'DELETE' for method, _ in case.backend.calls):
                del value['counts']['refresh_tokens']
            return value
        case.backend.snapshot = incomplete
        result = case.execute()
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])

    def test_reconciliation_incomplete_or_inconsistent_zero_never_confirms(self):
        for mode in ('missing_counter', 'remaining_session'):
            with self.subTest(mode=mode):
                case = af.Case(FakeBackend(), self.root / mode, str(uuid.uuid4()),
                               'cleanup_interrupted', COSTS)
                case.execute()
                original_snapshot = case.backend.snapshot
                def invalid(*args):
                    value = original_snapshot(*args)
                    if case.backend.user is None:
                        if mode == 'missing_counter':
                            del value['counts']['refresh_tokens']
                        else:
                            value['session_ids'] = [str(uuid.uuid4())]
                    return value
                case.backend.snapshot = invalid
                suffix = af.reconcile_retained(case)
                self.assertFalse(suffix['reconciliation_confirmed'])
                self.assertEqual(suffix['refunds'], 0)

    def test_reconciliation_insufficient_reserve_stops_before_observation(self):
        case = self.case('cleanup_interrupted')
        case.execute()
        # The real journal cannot be rewritten. A higher current delete tariff
        # is not silently admitted against the original retained allocation.
        case.journal.plan['managed_sql_prepaid']['delete'] = 100
        with patch.object(case.backend, 'snapshot', side_effect=AssertionError('must not query')):
            suffix = af.reconcile_retained(case)
        self.assertEqual(suffix['reason'], 'no_complete_reconciliation_reserve')
        self.assertEqual(suffix['prepaid_consumed'], 0)
        self.assertFalse((case.journal.folder / 'safety-reconciliation').exists())


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        requests = self.requests
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                requests.append(self.path)
                self.rfile.read(int(self.headers.get('Content-Length', '0')))
                body = b'{"id":"fixture"}'
                mode = getattr(self.server, 'wire_mode', 'normal')
                if mode == 'no_content':
                    self.send_response(204)
                    self.end_headers()
                    return
                self.send_response(200)
                if mode.startswith('chunked'):
                    self.send_header('Transfer-Encoding', 'chunked')
                    body = b'2\r\n{}\r\n'
                    if mode != 'chunked_no_end':
                        body += b'0\r\n'
                    if mode == 'chunked_valid':
                        body += b'\r\n'
                elif mode == 'truncated_length':
                    self.send_header('Content-Length', '100')
                    body = b'{}'
                elif mode == 'over_limit':
                    self.send_header('Content-Length', str(transport.BODY_LIMIT + 1))
                    body = b''
                else:
                    self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        self.server = HTTPServer(('127.0.0.1', 0), Handler)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.close)
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)

    def close(self):
        self.server.shutdown()
        self.worker.join(2)
        self.server.server_close()

    def client(self):
        with patch.object(transport, 'ORIGINS', (self.origin,)):
            return transport.LocalTransport(self.origin, 'TEST_LOCAL_ADMIN')

    def test_actual_lost_http_reply_after_upstream(self):
        with self.assertRaises(transport.UnknownOutcome) as caught:
            self.client().request('POST', '/admin/users', {}, fault='lost_reply')
        self.assertTrue(caught.exception.terminal)
        self.assertEqual(self.requests, ['/admin/users'])

    def test_actual_client_timeout_after_upstream(self):
        with self.assertRaises(transport.UnknownOutcome) as caught:
            self.client().request('POST', '/token?grant_type=password', {}, fault='timeout')
        self.assertTrue(caught.exception.terminal)
        self.assertEqual(self.requests, ['/token?grant_type=password'])

    def test_ambient_proxy_ignored(self):
        with patch.dict('os.environ', {'HTTP_PROXY': 'http://192.0.2.1:9', 'NO_PROXY': ''}):
            response = self.client().request('POST', '/admin/users', {})
        self.assertEqual(response['status'], 200)

    def test_hosted_origin_refused(self):
        with self.assertRaises(ValueError):
            transport.LocalTransport('https://example.supabase.co/auth/v1', 'unused')
        self.assertEqual(self.requests, [])

    def test_redirect_handler_refuses(self):
        with self.assertRaises(transport.UnknownOutcome):
            transport.NoRedirect().redirect_request(None, None, 302, '', {}, self.origin)

    def test_networkless_short_content_length_is_not_complete(self):
        class Response:
            status = 200
            headers = Message()
            headers['Content-Length'] = '100'
            def read(self, size):
                return b'{}'
        with self.assertRaises(transport.UnknownOutcome) as caught:
            transport.complete_body(Response())
        self.assertFalse(caught.exception.terminal)

    def test_actual_truncated_content_length_retains_claim(self):
        self.server.wire_mode = 'truncated_length'
        backend = FakeBackend()
        fake_http = backend.http
        def http(method, path, data=None, token=None, fault=None):
            fake_http(method, path, data, token=token)
            return self.client().request(method, path, data, token=token, fault=fault)
        backend.http = http
        with tempfile.TemporaryDirectory() as root:
            case = af.Case(backend, pathlib.Path(root) / 'truncated', str(uuid.uuid4()), 'partial_user', COSTS)
            result = case.execute()
        self.assertEqual(result['primary_failure'], 'auth_failure_http_unknown')
        self.assertFalse(result['mint_barrier'])
        self.assertFalse(result['claim_released'])
        self.assertFalse(result['component_case_pass'])
        self.assertEqual(result['http_dispatches'], ['create'])
        self.assertEqual(result['refunds'], 0)
        self.assertEqual(self.requests, ['/admin/users'])

    def test_actual_chunked_truncation_never_terminal(self):
        for mode in ('chunked_no_end', 'chunked_missing_trailer'):
            with self.subTest(mode=mode):
                self.server.wire_mode = mode
                with self.assertRaises(transport.UnknownOutcome) as caught:
                    self.client().request('POST', '/admin/users', {})
                self.assertFalse(caught.exception.terminal)

    def test_actual_complete_chunked_response_terminal(self):
        self.server.wire_mode = 'chunked_valid'
        result = self.client().request('POST', '/admin/users', {})
        self.assertTrue(result['terminal'])
        self.assertEqual(result['body'], {})

    def test_actual_oversized_response_never_terminal(self):
        self.server.wire_mode = 'over_limit'
        with self.assertRaises(transport.UnknownOutcome) as caught:
            self.client().request('POST', '/admin/users', {})
        self.assertFalse(caught.exception.terminal)

    def test_actual_bodyless_logout_terminal(self):
        self.server.wire_mode = 'no_content'
        result = self.client().request('POST', '/logout?scope=global', {}, token='TEST_TOKEN')
        self.assertEqual(result['status'], 204)
        self.assertTrue(result['terminal'])


if __name__ == '__main__':
    unittest.main()
