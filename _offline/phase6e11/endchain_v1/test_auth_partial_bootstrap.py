"""Isolated candidate source; actual localhost HTTP, mocked PG/Docker only.

AUTH_PARTIAL_SOURCE_ROOT supplies the unchanged checkout. Tests copy its Python
helpers/migrations into an ephemeral candidate and overlay only the proposal.
No hosted connections; source binding and C catalog validation remain real.
"""
import contextlib
import copy
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = pathlib.Path(os.environ.get('AUTH_PARTIAL_SOURCE_ROOT', pathlib.Path(__file__).resolve().parents[3]))
DELIVERY = pathlib.Path(__file__).resolve().parent
SNAPSHOT = tempfile.TemporaryDirectory()
ROOT = pathlib.Path(SNAPSHOT.name)
for relative in ('_offline/phase6e11/endchain_v1', '_offline/phase6e_server_v1', 'supabase/migrations'):
    target = ROOT / relative
    target.mkdir(parents=True)
    for path in (SOURCE / relative).iterdir():
        if path.suffix in ('.py', '.sql'):
            shutil.copyfile(path, target / path.name)
for path in (DELIVERY / '_offline').rglob('*.py'):
    shutil.copyfile(path, ROOT / path.relative_to(DELIVERY))
sys.path.insert(0, str(ROOT / '_offline/phase6e11/endchain_v1'))
import auth_failure as af
import auth_failure_tracked as tracked
import auth_failure_tracked_test as fixtures
import auth_failure_parent_finalizer as parent
import auth_partial_bootstrap as part
import admission_journal as durable
import fixture_producer_scope as producer
import test_fixture_producer_scope as catalogs
from admission_binding import NEW_RUN


class PartialTests(unittest.TestCase):
    stop_server = fixtures.WiringTests.stop_server
    environment_module = fixtures.WiringTests.environment_module

    def setUp(self):
        fixtures.WiringTests.setUp(self)
        self.registry = tracked.Registry(self.root / 'partial-registry', run_id=NEW_RUN)
        self.run_id = NEW_RUN
        self.env = patch.dict(os.environ, {
            'GITHUB_WORKSPACE': str(ROOT), 'GITHUB_ACTIONS': 'true',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.origins = patch.object(af, 'ORIGINS', (self.origin,))
        self.origins.start(); self.addCleanup(self.origins.stop)
        self.primary = RuntimeError('original bootstrap failure')
        self.auth = None
        self.calls, self.natives = 0, []
        self.fail_at, self.failure_mode = 2, 'before'
        self.fk = {'identities': 0, 'operators': 0}
        self.contract = None
        self.backend.autocommit = True
        self.backend.close = lambda: None
        original_snapshot = self.backend.snapshot
        def snapshot(email, marker, actor, sessions):
            self.natives.append('snapshot')
            for user in self.backend.users.values(): user['marker'] = None
            return original_snapshot(email, 'SQL_NULL_NEVER_EQUALS', actor, sessions)
        self.backend.snapshot = snapshot
        self.backend.execute = self.execute
        self.real_backend = patch.object(af, 'RealBackend', return_value=self.backend)
        self.real_backend.start(); self.addCleanup(self.real_backend.stop)
        def runtime(gate):
            self.assertTrue(self.registry.valid_proof(self.registry.proof))
            self.assertTrue(self.admin_connections[-1].closed)
            return self.wire
        self.native = patch.object(producer.NativeRuntime, 'disposable', side_effect=runtime)
        self.native.start(); self.addCleanup(self.native.stop)
        self.admin_connections = []

    def execute(self, sql, args=None):
        self.natives.append(sql)
        if sql == parent.BOUNDARY:
            value = dict.fromkeys(('pg17', 'tls', 'bounded_statement', 'bounded_lock', 'privileged', 'fresh'), True)
        elif sql == parent.FK: value = self.fk
        else: raise AssertionError('unexpected SQL')
        return types.SimpleNamespace(fetchone=lambda: {'value': copy.deepcopy(value)})

    def publish(self, name, value):
        with (self.root / name).open('xb') as stream: stream.write(durable.raw(value))
        self.saved[name] = copy.deepcopy(value)

    def factory(self, url, base, token, denied):
        plan = [{'method': method, 'route': route, 'units': 128} for _ in range(3)
                for method, route in (('POST', '/admin/users'), ('POST', '/token?grant_type=password'), ('GET', '/user'))]
        budget = tracked.ParentBudget(self.root / 'partial-budget', plan, run_id=NEW_RUN)
        self.auth = tracked.Factory(self.registry, budget)(self.origin, base, token, denied)
        original = self.auth.call
        def call(*args, **kw):
            self.calls += 1
            if self.calls == self.fail_at and self.failure_mode == 'before':
                raise self.primary
            value = original(*args, **kw)
            if self.calls == self.fail_at and self.failure_mode == 'after':
                raise self.primary
            return value
        self.auth.call = call
        return self.auth

    @contextlib.contextmanager
    def environment(self):
        path = ROOT / '_offline/phase6e_server_v1/ci_auth.py'
        with self.environment_module(source=path) as (module, gate):
            gate.out, gate.sources = self.root, ROOT
            gate.container, gate.save = 'supabase_db_fmz-db41-ci', self.publish
            self.gate = gate
            self.publish('candidate.json', {'sources': {
                p.relative_to(ROOT).as_posix(): durable.sha(p.read_bytes()) for p in ROOT.rglob('*') if p.is_file()}})
            self.contract = producer.source_contract(gate)
            self.wire = catalogs.Wire(catalogs.samples(self.contract))
            outer = self
            class Connection:
                closed = False
                def __enter__(self): return self
                def __exit__(self, *_): self.close()
                def close(self): self.closed = True
                def execute(self, *_): return self
                def fetchone(self): return {'value': 0}
            def connect(*_, **__):
                conn = Connection(); outer.admin_connections.append(conn); return conn
            class Session:
                def __init__(self, connection, observer, role):
                    self.connection, self.observer = connection, observer
                def execute(self, *_): return self.connection
            with patch.dict(sys.modules, {module.__name__: module}), patch.object(module.psycopg, 'connect', connect), patch.object(module, 'Session', Session):
                yield module, gate

    def run_failure(self, setup=None):
        with self.environment() as (module, gate):
            if setup: setup()
            with self.assertRaises(BaseException) as caught:
                with module.environment(gate, roles=parent.ROLES, include_test_admin=True,
                        tracked_auth_factory=self.factory, partial_bootstrap=True,
                        partial_delete_costs=dict.fromkeys(parent.ROLES, 128)):
                    self.fail('partial bootstrap yielded')
            self.error = caught.exception
        return self.saved.get(part.PREFIX + '.json')

    def assert_clean(self, owners):
        result = self.run_failure()
        self.assertIs(self.error, self.primary)
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED', result)
        self.assertEqual(result['known_owners'], owners)
        self.assertEqual(result['local_diagnostic_prepaid'], 13 + 133 * owners)
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.backend.sessions, {})
        self.assertFalse(result['full_auth_cleanup_proven'])
        self.assertFalse(result['global_auth_zero_claim'])
        engine = self.saved['auth-partial-bootstrap-engine.json']
        self.assertEqual(engine['native_dispatches'], 3 + 5 * owners)
        self.assertEqual(engine['http_attempts'], owners)
        self.assertIn('integration-managed-auth-protocol.json', self.saved)
        self.assertIn('integration-auth-tracked-protocol.json', self.saved)
        exported = json.dumps(self.saved)
        self.assertNotIn('LOCAL_TEST_ADMIN', exported)
        self.assertNotIn('@example.invalid', exported)
        self.assertNotIn('PRIVATE_TOKEN_', exported)
        return result

    def test_create_confirmed_login_not_dispatched_one_owner(self):
        self.assert_clean(1)

    def test_login_confirmed_verify_not_dispatched_discovers_owned_session(self):
        self.fail_at = 3
        self.assert_clean(1)

    def test_two_completed_then_third_create_not_dispatched(self):
        self.fail_at = 7
        self.assert_clean(2)

    def test_second_create_not_dispatched(self):
        self.fail_at = 4
        self.assert_clean(1)

    def test_second_login_not_dispatched(self):
        self.fail_at = 5
        self.assert_clean(2)

    def test_second_verify_not_dispatched(self):
        self.fail_at = 6
        self.assert_clean(2)

    def test_third_verify_not_dispatched(self):
        self.fail_at = 9
        self.assert_clean(3)

    def test_third_login_failure_all_three_owners(self):
        self.fail_at = 8
        self.assert_clean(3)

    def test_before_first_create_empty_subset_no_delete(self):
        self.fail_at = 1
        self.assert_clean(0)

    def test_terminal_login_reply_then_local_error_cleans_scoped_sessions(self):
        self.fail_at, self.failure_mode = 2, 'after'
        self.assert_clean(1)

    def test_unknown_create_body_not_adopted_even_when_user_exists(self):
        self.fail_at, self.failure_mode = 1, 'after'
        report = self.run_failure()
        self.assertIs(self.error, self.primary)
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertTrue(report['unknown_create'])
        self.assertEqual(len(self.backend.users), 1)
        self.assertEqual(self.natives, [])

    def test_truncated_login_retains_user_and_session_no_fake_barrier(self):
        self.fail_at = -1
        self.server.truncate_at = 2
        report = self.run_failure()
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertEqual(len(self.backend.users), 1)
        self.assertEqual(len(self.backend.sessions), 1)
        self.assertEqual(self.natives, [])
        self.assertIsNone(self.registry.proof)

    def test_truncated_create_retains_unknown_subject_without_delete(self):
        self.fail_at = -1
        self.server.truncate_at = 1
        report = self.run_failure()
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertTrue(report['unknown_create'])
        self.assertEqual(len(self.backend.users), 1)
        self.assertEqual(self.natives, [])
        self.assertIsNone(self.registry.proof)

    def test_terminal_login_rejection_cleans_confirmed_owner(self):
        self.fail_at = -1
        original = fixtures.Backend.http
        def http(backend, method, path, data=None, token=None):
            if path == '/token?grant_type=password':
                return {'body': {'error': 'synthetic_rejection'}, 'status': 401, 'terminal': True}
            return original(backend, method, path, data, token)
        with patch.object(fixtures.Backend, 'http', http):
            report = self.run_failure()
        self.assertIsInstance(self.error, ValueError)
        self.assertEqual(report['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED', report)
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.server.count, 3)

    def test_unknown_trigger_catalog_blocks_before_parent_engine(self):
        def setup():
            self.wire.data['triggers'].append({'schema': 'auth', 'relation': 'users', 'name': 'unknown'})
        report = self.run_failure(setup)
        self.assertIs(self.error, self.primary)
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertEqual(self.natives, [])
        self.assertEqual(len(self.backend.users), 1)

    def test_private_fk_not_zero_blocks_deletes(self):
        self.fk['identities'] = 1
        report = self.run_failure()
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertEqual(len(self.backend.users), 1)

    def test_unregistered_source_blocks_before_first_auth(self):
        def setup():
            path = self.root / 'candidate.json'
            value = json.loads(path.read_bytes())
            value['sources']['_offline/phase6e11/endchain_v1/auth_partial_bootstrap.py'] = '0' * 64
            path.write_bytes(durable.raw(value))
        self.run_failure(setup)
        self.assertEqual(self.server.count, 0)
        self.assertIsNotNone(self.registry.proof)

    def test_fake_proof_cannot_enter_existing_engine(self):
        proof = object.__new__(part.Prerequisite)
        with self.assertRaises(tracked.Blocked): _ = proof.roles

    def test_no_direct_caller_boolean_entry(self):
        with self.assertRaisesRegex(tracked.Blocked, 'actual_environment_call'):
            part.run(None, {}, None, delete_costs=dict.fromkeys(parent.ROLES, 128))

    def test_no_direct_state_constructor_to_issue_capability(self):
        with self.assertRaisesRegex(tracked.Blocked, 'bootstrap_constructor_origin'):
            part._Bootstrap(None, {}, None, None, dict.fromkeys(parent.ROLES, 128))

    def test_default_environment_path_unchanged(self):
        with self.environment() as (module, gate):
            with module.environment(gate, roles=parent.ROLES, include_test_admin=True) as ctx:
                self.assertNotIn('auth_request_registry', ctx)
                self.assertEqual(set(ctx['claims']), set(parent.ROLES))
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.registry.next_id, 0)
        self.assertNotIn(part.PREFIX + '.json', self.saved)

    def test_successful_bootstrap_returns_to_existing_parent_finalizer(self):
        self.fail_at = -1
        with self.environment() as (module, gate):
            with module.environment(gate, roles=parent.ROLES, include_test_admin=True,
                    tracked_auth_factory=self.factory, partial_bootstrap=True,
                    partial_delete_costs=dict.fromkeys(parent.ROLES, 128)) as ctx:
                self.assertEqual(set(ctx['claims']), set(parent.ROLES))
                self.assertEqual(set(ctx['accounts']), set(parent.ROLES))
        self.assertEqual(self.server.count, 9)
        self.assertEqual(len(self.backend.users), 3)  # No finalizer configured in this fixture.
        self.assertNotIn(part.PREFIX + '.json', self.saved)
        self.assertIsNotNone(self.registry.proof)

    def test_unknown_admin_delete_never_retried_or_reclassified_by_zero(self):
        self.server.truncate_at = 2  # create, then cleanup DELETE (login fails pre-dispatch).
        report = self.run_failure()
        self.assertIs(self.error, self.primary)
        self.assertEqual(report['suffix_status'], 'NO_GO')
        engine = self.saved['auth-partial-bootstrap-engine.json']
        self.assertFalse(engine['deletes']['a']['acknowledged'])
        self.assertEqual(engine['http_attempts'], 1)
        self.assertEqual(self.server.count, 2)
        self.assertFalse(engine['original_claims_released'])

    def test_changed_original_owner_journal_blocks_delete(self):
        original = self.backend.snapshot
        def snapshot(*args):
            value = original(*args)
            (self.root / (part.PREFIX + '-private') / 'created-a.json').write_bytes(b'{}\n')
            return value
        self.backend.snapshot = snapshot
        report = self.run_failure()
        self.assertIs(self.error, self.primary)
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertEqual(len(self.backend.users), 1)
        self.assertEqual(self.server.count, 1)

    def test_future_mint_denied_after_partial_cleanup(self):
        self.assert_clean(1)
        with self.assertRaisesRegex(tracked.Blocked, 'future_request_denied'):
            self.auth.call('/token?grant_type=password', data={'email': 'unused@example.invalid'})
        self.assertEqual(self.server.count, 2)

    def test_receipt_storage_failure_preserves_original(self):
        storage_error = OSError('synthetic local receipt storage failure')
        def setup():
            original = self.gate.save
            def save(name, value):
                if name in ('integration-io-postgres-after.json', 'integration-io-stop.json'):
                    raise storage_error
                return original(name, value)
            self.gate.save = save
        result = self.run_failure(setup)
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertIs(self.error, self.primary)
        self.assertTrue(any('secondary_io_receipt_failure:OSError' in note
                            for note in self.primary.__notes__))

    def test_container_teardown_failure_preserves_original(self):
        original_environment = self.environment
        attempts = []
        @contextlib.contextmanager
        def environment():
            with original_environment() as (module, gate):
                original_run = module.subprocess.run
                def subprocess_run(args, **kw):
                    if args[:2] == ['docker', 'rm']:
                        attempts.append('rm')
                        return types.SimpleNamespace(returncode=1, stdout='')
                    return original_run(args, **kw)
                with patch.object(module.subprocess, 'run', subprocess_run):
                    yield module, gate
        self.environment = environment
        result = self.run_failure()
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertIs(self.error, self.primary)
        self.assertEqual(attempts, ['rm'])
        self.assertTrue(any('secondary_container_teardown_failure:RuntimeError' in note
                            for note in self.primary.__notes__))

    def test_rejected_existing_worker_closes_future_dispatch(self):
        original = self.factory
        def factory(*args, **kwargs):
            auth = original(*args, **kwargs)
            worker = self.registry.start_worker(lambda: None)
            worker.join(2)
            return auth
        self.factory = factory
        self.run_failure()
        self.assertIsInstance(self.error, tracked.Blocked)
        self.assertIn('fresh_exclusive_registry', str(self.error))
        self.assertEqual(self.server.count, 0)
        self.assertEqual(self.registry.phase, 'CLOSED')
        with self.assertRaisesRegex(tracked.Blocked, 'future_request_denied'):
            self.auth.call('/admin/users', 'LOCAL_TEST_ADMIN', {
                'email': 'review-only@example.invalid', 'password': 'SYNTHETIC_TEST_ONLY',
                'email_confirm': True})
        self.assertEqual(self.server.count, 0)
        self.assertNotIn('auth-partial-bootstrap-engine.json', self.saved)

    def test_rejected_worker_drain_failure_preserves_primary_no_retry(self):
        original = self.factory
        calls = []
        def factory(*args, **kwargs):
            auth = original(*args, **kwargs)
            def fail_worker():
                raise RuntimeError('synthetic registered worker failed')
            worker = self.registry.start_worker(fail_worker)
            worker.join(2)
            close = auth.close_and_drain
            def close_once():
                calls.append('close')
                return close()
            auth.close_and_drain = close_once
            return auth
        self.factory = factory
        self.run_failure()
        self.assertIsInstance(self.error, tracked.Blocked)
        self.assertIn('fresh_exclusive_registry', str(self.error))
        self.assertEqual(calls, ['close'])
        self.assertEqual(self.registry.phase, 'FAILED')
        self.assertIsNone(self.registry.proof)
        self.assertEqual(self.server.count, 0)
        self.assertTrue(any('secondary_partial_preflight_close:Blocked' in note
                            for note in self.error.__notes__))
        with self.assertRaisesRegex(tracked.Blocked, 'future_request_denied'):
            self.auth.call('/admin/users', 'LOCAL_TEST_ADMIN', {
                'email': 'review-only@example.invalid', 'email_confirm': True})
        self.assertEqual(calls, ['close'])
        self.assertNotIn('auth-partial-bootstrap-engine.json', self.saved)


if __name__ == '__main__':
    try: unittest.main()
    finally: SNAPSHOT.cleanup()

