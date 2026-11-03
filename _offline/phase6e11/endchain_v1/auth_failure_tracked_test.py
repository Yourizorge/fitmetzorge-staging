"""Actual loopback requests and proposed environment wiring; SQL/Docker remain mocks."""
import contextlib
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import time
import types
import unittest
import uuid
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import auth_failure as candidate
import auth_failure_tracked as tracked
import auth_failure_transport as transport
from auth_failure_test import StateTests, TransportTests  # Existing 42 regressions, candidate defaults.
import auth_failure as ap


class Backend:
    evidence_kind = 'MOCK_SQL_STATE_ONLY'

    def __init__(self):
        self.users, self.sessions, self.calls = {}, {}, []
        self.commands = 0
        self.registry = {'identities': 0, 'operators': 0}
        self.db = self
        self.native_calls = 0

    def stats(self):
        self.native_calls += 1
        return self.commands

    def difference(self, before, after):
        return {'commands': after - before, 'mock_only': True}

    def execute(self, sql, args):
        self.native_calls += 1
        self.query = sql
        self.args = args
        return self

    def fetchone(self):
        return {'value': self.registry.copy()}

    def snapshot(self, email, marker, actor, sessions):
        self.native_calls += 1
        users = [copy.deepcopy(u) for u in self.users.values()
                 if u['email'] == email or u['marker'] == marker or u['id'] == actor]
        ids = {u['id'] for u in users} | {actor}
        keys = [s for s, owner in self.sessions.items() if owner in ids]
        counts = dict.fromkeys(ap.SNAPSHOT_COUNTS, 0)
        counts.update(users=len(users), identities=len(users), sessions=len(keys), refresh_tokens=len(keys))
        return {'users': users, 'session_ids': keys, 'counts': counts}

    def http(self, method, path, data=None, token=None):
        self.calls.append((method, path))
        self.commands += 3
        body = {}
        if path == '/admin/users':
            actor = str(uuid.uuid4())
            self.users[actor] = {'id': actor, 'email': data['email'],
                                 'marker': data['app_metadata']['auth_failure_claim']}
            body = {'id': actor, 'email': data['email']}
        elif path.startswith('/token'):
            actor = next(u['id'] for u in self.users.values() if u['email'] == data['email'])
            self.sessions[str(uuid.uuid4())] = actor
            body = {'access_token': 'PRIVATE_TOKEN_' + actor}
        elif path.startswith('/logout'):
            self.sessions.clear()
        elif method == 'DELETE':
            actor = path.split('/')[-1]
            self.users.pop(actor)
            self.sessions = {s: u for s, u in self.sessions.items() if u != actor}
        return {'status': 200, 'body': body, 'terminal': True}


class RecordsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)

    def truncated_save(self, *, truthful_count):
        records = tracked.Records(self.root / 'records')
        original_open = pathlib.Path.open
        class ShortWriter:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def __getattr__(self, name): return getattr(self.stream, name)
            def write(self, raw):
                written = self.stream.write(raw[:-1])
                return written if truthful_count else len(raw)
        def opened(path, mode='r', *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return ShortWriter(stream) if mode == 'xb' else stream
        with patch.object(pathlib.Path, 'open', opened):
            with self.assertRaisesRegex(tracked.Blocked,
                    'short_write' if truthful_count else 'readback_mismatch'):
                records.save('first', {'value': 1})
        self.assertTrue(records.poisoned)
        self.assertEqual(records.n, 0)
        self.assertEqual(len(records._hashes), 1)
        with self.assertRaises(tracked.Blocked): records.save('retry', {})
        with self.assertRaises(tracked.Blocked): records.export()

    def test_short_write_count_invalidates_journal(self):
        self.truncated_save(truthful_count=True)

    def test_full_count_with_truncated_bytes_fails_readback(self):
        self.truncated_save(truthful_count=False)

    def test_original_hashes_preserved_and_export_uses_validated_bytes(self):
        records = tracked.Records(self.root / 'records')
        first = records.save('first', {'value': 1})
        second = records.save('second', {'value': 2})
        exported = records.export()
        self.assertEqual({k: v['sha256'] for k, v in exported.items()},
                         {ref['name']: ref['sha256'] for ref in (first, second)})
        original_hashes = dict(records._hashes)
        (records.folder / first['name']).write_bytes(b'{"changed":true}\n')
        with self.assertRaisesRegex(tracked.Blocked, 'record_changed'): records.export()
        self.assertEqual(records._hashes, original_hashes)
        self.assertTrue(records.poisoned)

    def test_previous_record_mutation_blocks_close(self):
        registry = tracked.Registry(self.root / 'registry', run_id=str(uuid.uuid4()))
        registry.records.save('later', {})
        first = next(iter(registry.records._hashes))
        (registry.records.folder / first).write_bytes(b'{}\n')
        with self.assertRaisesRegex(tracked.Blocked, 'record_changed'): registry.close_and_drain()
        self.assertEqual(registry.phase, 'FAILED')
        self.assertIsNone(registry.proof)
        self.assertTrue(registry.records.poisoned)

    def test_previous_record_mutation_revokes_live_proof_after_close(self):
        registry = tracked.Registry(self.root / 'registry', run_id=str(uuid.uuid4()))
        proof = registry.close_and_drain()
        self.assertTrue(registry.valid_proof(proof))
        closed_path = registry.records.folder / registry._close_ref[0]
        closed_bytes = closed_path.read_bytes()
        first = next(iter(registry.records._hashes))
        old = (registry.records.folder / first).read_bytes()
        (registry.records.folder / first).write_bytes(b'{}\n')
        self.assertFalse(registry.valid_proof(proof))
        self.assertEqual(closed_path.read_bytes(), closed_bytes)
        self.assertEqual(registry.phase, 'FAILED')
        self.assertIsNone(registry.proof)
        # Repairing bytes does not revive an invalidated journal or proof.
        (registry.records.folder / first).write_bytes(old)
        self.assertFalse(registry.valid_proof(proof))
        with self.assertRaises(tracked.Blocked): registry.records.export()

    def test_export_detects_prior_mutation_before_and_after_close(self):
        for closed in (False, True):
            with self.subTest(closed=closed):
                registry = tracked.Registry(self.root / str(closed), run_id=str(uuid.uuid4()))
                if closed: registry.close_and_drain()
                first = next(iter(registry.records._hashes))
                (registry.records.folder / first).write_bytes(b'{}\n')
                with self.assertRaisesRegex(tracked.Blocked, 'record_changed'): registry.records.export()
                self.assertTrue(registry.records.poisoned)
                self.assertIsNone(registry.proof)

    def test_recordset_deletion_and_unregistered_addition_fail_closed(self):
        for change in ('delete', 'add'):
            with self.subTest(change=change):
                records = tracked.Records(self.root / change)
                ref = records.save('first', {})
                if change == 'delete': (records.folder / ref['name']).unlink()
                else: (records.folder / 'unregistered.json').write_bytes(b'{}\n')
                with self.assertRaisesRegex(tracked.Blocked, 'recordset_changed'): records.export()
                self.assertTrue(records.poisoned)

    def test_save_refuses_prior_mutation_without_new_record(self):
        records = tracked.Records(self.root / 'records')
        ref = records.save('first', {})
        (records.folder / ref['name']).write_bytes(b'{}\n')
        with self.assertRaisesRegex(tracked.Blocked, 'record_changed'): records.save('second', {})
        self.assertEqual(records.n, 1)
        self.assertEqual(len(records._hashes), 1)

    def test_parent_budget_recordset_is_checked_at_close_proof_and_export(self):
        for boundary in ('close', 'proof', 'export'):
            with self.subTest(boundary=boundary):
                run_id = str(uuid.uuid4())
                registry = tracked.Registry(self.root / (boundary + '-registry'), run_id=run_id)
                budget = tracked.ParentBudget(self.root / (boundary + '-budget'),
                    [{'method': 'POST', 'route': '/admin/users', 'units': 128}], run_id=run_id)
                auth = tracked.Factory(registry, budget)(transport.ORIGINS[0], object, 'LOCAL_TEST_ADMIN', ValueError)
                proof = registry.close_and_drain() if boundary != 'close' else None
                claim_path = budget.records.folder / budget.claim['name']
                claim_path.write_bytes(b'{}\n')
                if boundary == 'proof': self.assertFalse(registry.valid_proof(proof))
                else:
                    with self.assertRaisesRegex(tracked.Blocked, 'record_changed'):
                        registry.close_and_drain() if boundary == 'close' else auth.evidence()
                self.assertTrue(budget.records.poisoned)
                self.assertEqual(registry.phase, 'FAILED')
                self.assertIsNone(registry.proof)


class WiringTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.backend = Backend()
        backend = self.backend
        self.entered, self.release = threading.Event(), threading.Event()
        entered, release = self.entered, self.release
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def serve(self):
                self.server.count += 1
                ordinal = self.server.count
                data = json.loads(self.rfile.read(int(self.headers['Content-Length']))) if self.headers.get('Content-Length') else None
                if ordinal == self.server.hold_at:
                    entered.set()
                    release.wait(5)
                if self.command == 'GET':
                    actor = self.headers.get('Authorization', '').removeprefix('Bearer PRIVATE_TOKEN_')
                    body = {'id': actor}
                    backend.commands += 3
                    status = 200
                else:
                    if self.path == '/admin/users' and 'app_metadata' not in data:
                        data = {**data, 'app_metadata': {'auth_failure_claim': 'MOCK_PARENT_ONLY'}}
                    response = Backend.http(backend, self.command, self.path, data)
                    body, status = response['body'], response['status']
                    if self.path.startswith('/logout'): status, body = 204, None
                raw = json.dumps(body).encode() if body is not None else b''
                self.send_response(status)
                self.send_header('Content-Length', str(len(raw) + (100 if ordinal == self.server.truncate_at else 0)))
                self.end_headers()
                self.wfile.write(raw)
            do_POST = do_DELETE = do_GET = serve
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.count, self.server.hold_at, self.server.truncate_at = 0, -1, -1
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.addCleanup(self.stop_server)
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)
        self.origin_patch = patch.object(transport, 'ORIGINS', (self.origin,))
        self.origin_patch.start()
        self.addCleanup(self.origin_patch.stop)
        self.run_id = str(uuid.uuid4())
        self.registry = tracked.Registry(self.root / 'registry', run_id=self.run_id)
        self.backend.transport = transport.LocalTransport(self.origin, 'LOCAL_TEST_ADMIN')
        self.backend.http = self.backend.transport.request
        self.trace, self.saved = [], {}
        outer = self
        class BaseAuth:
            def __init__(self, url): self.url = outer.origin
            def call(self, path, token=None, data=None, method=None):
                raw = None if data is None else json.dumps(data).encode()
                request = urllib.request.Request(self.url + path, data=raw, method=method,
                    headers={'Authorization': 'Bearer ' + (token or '')})
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(request, timeout=5) as response:
                    body = response.read()
                return json.loads(body) if body else {}
            def verify(self, token): return {'sub': self.call('/user', token)['id']}
        self.base = BaseAuth

    def stop_server(self):
        self.release.set()
        for worker in self.registry.workers: worker.join(6)
        self.server.shutdown()
        self.server_thread.join(6)
        self.server.server_close()

    def budget(self, extra=()):
        plan = [{'method': method, 'route': path, 'units': 128}
                for _ in range(3) for method, path in (
                    ('POST', '/admin/users'), ('POST', '/token?grant_type=password'), ('GET', '/user'))]
        plan += list(extra)
        return tracked.ParentBudget(self.root / 'parent-budget', plan, run_id=self.run_id)

    @contextlib.contextmanager
    def environment_module(self, source=None):
        outer = self
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def execute(self, *_): return self
            def fetchone(self): return {'value': 0}
        class Session:
            def __init__(self, connection, observer, role): self.observer = observer
            def execute(self, *_):
                self.observer({'phase': 'completed', 'confirmed': True, 'template_sha256': 'mock'})
                return Connection()
        def mod(name, **attrs):
            value = types.ModuleType(name)
            value.__dict__.update(attrs)
            return value
        modules = {'psycopg': mod('psycopg', connect=lambda *_args, **_kw: Connection()),
            'psycopg.rows': mod('psycopg.rows', dict_row=None),
            'psycopg.conninfo': mod('psycopg.conninfo', make_conninfo=lambda **_: 'MOCK_DSN'),
            'store': mod('store', LocalAuth=self.base, Denied=ValueError),
            'protocol': mod('protocol', Session=Session),
            'auth_protocol': mod('auth_protocol', STATS='MOCK_STATS', difference=lambda *_: {'commands': 0}),
            'application_io': mod('application_io', active_pair=lambda a, b: (a, b))}
        class Gate:
            container = 'test_pg'
            work = self.root
            def command(self, *_args, **_kwargs): outer.trace.append('image_command_mock')
            def save(self, name, value): outer.saved[name] = value
        def subprocess_run(args, **kwargs):
            if args[1] == 'exec': output = 'PRIVATE_TEST_PASSWORD'
            elif args[1] == 'inspect': output = 'test_network'
            elif args[1] == 'port': output = '127.0.0.1:54329'
            elif args[1:3] == ['image', 'inspect']: output = '["mock_digest"]'
            else:
                output = 'mock_container'
                if args[1] == 'rm': outer.trace.append('container_stop_mock')
            return types.SimpleNamespace(returncode=0, stdout=output)
        class Health:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_): pass
        if source is None:
            source = pathlib.Path(__file__).with_name('ci_auth.py')
            if not source.exists():
                source = pathlib.Path(__file__).resolve().parents[2] / 'phase6e_server_v1' / 'ci_auth.py'
        with patch.dict(sys.modules, modules), patch.dict('os.environ', {'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging'}):
            spec = importlib.util.spec_from_file_location('ci_auth_proposal_test', source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with patch.object(module.subprocess, 'run', subprocess_run), patch.object(module.urllib.request, 'urlopen', return_value=Health()):
                yield module, Gate()

    def factory(self, budget, finalizer=None):
        factory = tracked.Factory(self.registry, budget, finalizer=finalizer)
        def create(url, base_type, admin_token, denied_type):
            self.trace.append('factory_before_bootstrap')
            self.assertEqual(self.server.count, 0)
            return factory(self.origin, base_type, admin_token, denied_type)
        return create, factory

    def test_default_environment_does_not_construct_registry_or_change_request_count(self):
        with self.environment_module() as (module, gate):
            with module.environment(gate, roles=('a', 'trainer', 'b'), include_test_admin=True) as ctx:
                self.assertIsInstance(ctx['auth'], self.base)
                self.assertNotIn('auth_request_registry', ctx)
                self.assertEqual(set(ctx['claims']), {'a', 'trainer', 'b'})
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.registry.next_id, 0)
        self.assertEqual(self.trace[-1], 'container_stop_mock')

    @contextlib.contextmanager
    def workflow_driver(self, *, tracked_mode=True):
        import integral_failure_runtime_workflow as workflow
        self.backend.info = types.SimpleNamespace(host='MOCK_DB', port=5432, dbname='MOCK_DB')
        self.backend.close = lambda: None
        gate = types.SimpleNamespace(out=self.root, save=lambda name, value: self.saved.update({name: value}),
            auth_failure_context={'managed_costs': dict.fromkeys(candidate.OPERATIONS, 128)})
        driver = workflow.WorkflowDriver(gate, local_component_authorized=True,
            **({'transport_factory': self.registry.case_transport_factory} if tracked_mode else {}))
        driver.deadline = time.monotonic() + 120
        witness = types.SimpleNamespace(info=self.backend.info, close=lambda: None)
        runtime = types.SimpleNamespace(environment='disposable_ci', connect=lambda: witness)
        with patch.object(candidate, 'RealBackend', return_value=self.backend):
            yield workflow, driver, runtime

    def workflow_session(self, name):
        return types.SimpleNamespace(case=name, case_id=str(uuid.uuid4()), claims=set(), fail=lambda error: None)

    def test_workflow_all_aliases_and_both_delegates_have_no_untracked_http_escape(self):
        # Real HTTP through candidate WorkflowDriver; DB identity/snapshots remain mocks.
        with self.workflow_driver() as (_, driver, runtime):
            with patch.object(self.backend, 'http', side_effect=AssertionError('untracked_workflow_http')) as bypass:
                driver.open(runtime, ('mid_auth', 'lost_reply'))
                self.assertEqual(self.server.count, 6)
                self.assertEqual(self.registry.next_id, 6)
                self.assertEqual(len(driver.actors), 3)
                for name in ('mid_auth', 'lost_reply'):
                    session = self.workflow_session(name)
                    driver.run_case(name, session)
                    self.assertTrue(session.delegated_auth['component_case_pass'])
                    self.assertEqual(self.server.count, self.registry.next_id)
                self.assertEqual(self.server.count, 11)
                result = driver.close()
                self.assertTrue(result['all_component_owned_auth_zero'])
                self.assertEqual(self.server.count, 14)
                self.assertEqual(self.registry.next_id, 14)
                bypass.assert_not_called()
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.backend.sessions, {})
        self.registry.close_and_drain()
        self.assertTrue(any(not row['delivery_confirmed'] for row in self.registry.requests.values()))

    def test_workflow_retained_case_suffix_keeps_same_registry_and_original_claim(self):
        with self.workflow_driver() as (_, driver, runtime):
            with patch.object(self.backend, 'http', side_effect=AssertionError('untracked_suffix_http')) as bypass:
                driver.open(runtime, ('mid_auth',))
                cases = []
                original_case = candidate.Case
                def capture(*args, **kwargs):
                    case = original_case(*args, **kwargs)
                    cases.append(case)
                    return case
                with patch.object(candidate, 'Case', side_effect=capture):
                    driver.delegated_auth(self.workflow_session('suffix_probe'), 'cleanup_interrupted')
                case = cases[0]
                raw = (case.journal.folder / 'result.json').read_bytes()
                before = self.server.count
                suffix = candidate.reconcile_retained(case)
                self.assertTrue(suffix['reconciliation_confirmed'])
                self.assertFalse(suffix['original_claim_released'])
                self.assertEqual(suffix['http_dispatches'], 1)
                self.assertEqual(suffix['prepaid_consumed'], 132)
                self.assertEqual(self.server.count, before + 1)
                self.assertEqual(self.server.count, self.registry.next_id)
                self.assertEqual((case.journal.folder / 'result.json').read_bytes(), raw)
                driver.close()
                bypass.assert_not_called()
        self.assertEqual(self.server.count, self.registry.next_id)

    def test_workflow_optional_factory_default_preserves_backend_http(self):
        with self.workflow_driver(tracked_mode=False) as (_, driver, runtime):
            with patch.object(self.backend, 'http', wraps=self.backend.http) as default_http:
                driver.open(runtime, ('mid_auth', 'lost_reply'))
                for name in ('mid_auth', 'lost_reply'):
                    driver.run_case(name, self.workflow_session(name))
                result = driver.close()
                self.assertTrue(result['all_component_owned_auth_zero'])
                self.assertEqual(default_http.call_count, 14)
        self.assertEqual(self.server.count, 14)
        self.assertEqual(self.registry.next_id, 0)

    def test_parent_nine_call_plan_and_workflow_share_registry_not_budget(self):
        budget = self.budget()
        factory, _ = self.factory(budget)
        with self.environment_module() as (module, gate):
            with module.environment(gate, roles=('a', 'trainer', 'b'),
                                    tracked_auth_factory=factory):
                with self.workflow_driver() as (_, driver, runtime):
                    with patch.object(self.backend, 'http', side_effect=AssertionError('untracked_body_http')):
                        driver.open(runtime, ('mid_auth', 'lost_reply'))
                        for name in ('mid_auth', 'lost_reply'):
                            driver.run_case(name, self.workflow_session(name))
                        result = driver.close()
                        self.assertTrue(result['all_component_owned_auth_zero'])
                self.assertEqual(self.server.count, 23)
                self.assertEqual(self.registry.next_id, 23)
                self.assertEqual(budget.spent, 9 * 128)
                self.assertEqual(len(self.backend.users), 3)  # Parent subjects are NOT deleted.
        self.assertEqual(self.registry.phase, 'CLOSED')
        self.assertEqual(budget.spent, 9 * 128)
        self.assertEqual(len(self.backend.users), 3)

    def test_workflow_hook_retains_per_dispatch_deadline_and_no_refund(self):
        with self.workflow_driver() as (workflow, driver, runtime):
            driver.open(runtime, ('mid_auth',))
            case = driver.actors['member']
            before = self.server.count
            spent = case.journal.spent
            # Stats still fit (5s), but an HTTP request (15s) must not start.
            driver.backend.deadline = time.monotonic() + 10
            with self.assertRaisesRegex(workflow.rt.Blocked, 'failure_auth_component_deadline'):
                case.auth('delete')
            self.assertEqual(self.server.count, before)
            self.assertEqual(self.registry.next_id, before)
            self.assertIn('delete', case.journal.dispatched)
            self.assertGreaterEqual(case.journal.spent - spent, 128)
            self.assertFalse(case.terminals['delete'])
            driver.close()

    def test_workflow_cannot_mint_after_registry_close(self):
        with self.workflow_driver() as (_, driver, runtime):
            driver.open(runtime, ('mid_auth',))
            self.registry.close_and_drain()
            before = self.server.count
            session = self.workflow_session('mid_auth')
            driver.run_case('mid_auth', session)
            self.assertFalse(session.delegated_auth['component_case_pass'])
            self.assertFalse(session.delegated_auth['claim_released'])
            driver.close()
            self.assertEqual(self.server.count, before)
            self.assertEqual(self.registry.next_id, before)

    def test_workflow_invalid_factory_refuses_before_open(self):
        import integral_failure_runtime_workflow as workflow
        with self.assertRaisesRegex(ValueError, 'failure_auth_transport_factory'):
            workflow.WorkflowDriver(types.SimpleNamespace(), transport_factory=True)
        self.assertEqual(self.server.count, 0)

    def test_default_five_role_environment_remains_untracked(self):
        with self.environment_module() as (module, gate):
            with module.environment(gate) as ctx:
                self.assertIsInstance(ctx['auth'], self.base)
                self.assertEqual(set(ctx['claims']), {'a', 'trainer', 'b', 'owner', 'outsider'})
                self.assertNotIn('auth_request_registry', ctx)
                self.assertNotIn('test_admin_token', ctx)
        self.assertEqual(self.server.count, 15)
        self.assertEqual(self.registry.next_id, 0)
        self.assertNotIn('integration-auth-tracked-protocol.json', self.saved)
        self.assertEqual(self.trace[-1], 'container_stop_mock')

    def test_tracked_factory_rejects_default_roles_before_service_or_requests(self):
        factory, _ = self.factory(self.budget())
        with self.environment_module() as (module, gate):
            with self.assertRaises(ValueError):
                with module.environment(gate, tracked_auth_factory=factory):
                    self.fail('must refuse the default five-role tracked configuration')
        self.assertEqual(self.server.count, 0)
        self.assertEqual(self.registry.next_id, 0)
        self.assertEqual(self.trace, [])

    def test_factory_covers_bootstrap_gets_and_closes_before_explicit_finalizer(self):
        budget = self.budget()
        def finalize(ctx, auth, proof):
            self.trace.append('explicit_finalizer')
            self.assertEqual(self.registry.phase, 'CLOSED')
            self.assertIs(proof, self.registry.proof)
            self.assertIn('test_admin_token', ctx)
            before = self.server.count
            with self.assertRaises(tracked.Blocked): auth.call('/token?grant_type=password', data=ctx['accounts']['a'])
            self.assertEqual(self.server.count, before)
        factory, holder = self.factory(budget, finalize)
        with self.environment_module() as (module, gate):
            with module.environment(gate, roles=('a', 'trainer', 'b'), include_test_admin=True,
                                    tracked_auth_factory=factory) as ctx:
                self.assertEqual(self.registry.next_id, 9)
                self.assertIs(ctx['auth_request_registry'], self.registry)
        self.assertNotIn('test_admin_token', ctx)
        self.assertEqual(budget.spent, 1152)
        self.assertEqual(self.server.count, 9)
        self.assertLess(self.trace.index('explicit_finalizer'), self.trace.index('container_stop_mock'))
        self.assertEqual(set(holder.instance._owners), {'a', 'trainer', 'b'})

    def test_partial_bootstrap_unknown_never_finalizes_or_relabels_terminal(self):
        self.server.truncate_at = 2
        factory, _ = self.factory(self.budget(), lambda *_: self.fail('must not finalize'))
        with self.environment_module() as (module, gate):
            with self.assertRaisesRegex(ValueError, 'auth_denied'):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory):
                    self.fail('must not yield')
        self.assertEqual(self.registry.phase, 'FAILED')
        self.assertEqual(self.server.count, 2)
        self.assertEqual(self.trace[-1], 'container_stop_mock')

    def test_actual_worker_is_joined_after_known_request_drains(self):
        extra = [{'method': 'POST', 'route': '/token?grant_type=password', 'units': 128}]
        def finalize(*_):
            self.assertTrue(all(not w.is_alive() for w in self.registry.workers))
            self.trace.append('joined_finalizer')
        factory, _ = self.factory(self.budget(extra), finalize)
        self.server.hold_at = 10
        timer = None
        try:
            with self.environment_module() as (module, gate):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory) as ctx:
                    self.registry.start_worker(lambda: ctx['auth'].call('/token?grant_type=password', data=ctx['accounts']['a']))
                    self.assertTrue(self.entered.wait(5))
                    timer = threading.Timer(0.2, self.release.set)
                    timer.start()
            self.assertIn('joined_finalizer', self.trace)
            self.assertEqual(self.registry.next_id, 10)
        finally:
            self.release.set()
            if timer: timer.join(5)

    def test_drain_timeout_refuses_finalizer_and_future_mint(self):
        self.registry.drain_timeout = 0.05
        self.server.hold_at = 10
        extra = [{'method': 'POST', 'route': '/token?grant_type=password', 'units': 128}]
        factory, _ = self.factory(self.budget(extra), lambda *_: self.fail('must not finalize'))
        try:
            with self.environment_module() as (module, gate):
                with self.assertRaises(tracked.Blocked):
                    with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory) as ctx:
                        self.registry.start_worker(lambda: ctx['auth'].call('/token?grant_type=password', data=ctx['accounts']['a']))
                        self.assertTrue(self.entered.wait(5))
            self.assertEqual(self.registry.phase, 'FAILED')
            with self.assertRaises(tracked.Blocked): self.registry.start_worker(lambda: None)
        finally:
            self.release.set()
            for worker in self.registry.workers: worker.join(6)

    def test_body_primary_survives_finalizer_failure(self):
        def finalize(*_): raise OSError('PRIVATE_FINALIZER_ERROR')
        factory, _ = self.factory(self.budget(), finalize)
        with self.environment_module() as (module, gate):
            with self.assertRaisesRegex(ValueError, 'primary_body'):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory):
                    raise ValueError('primary_body')
        self.assertNotIn('PRIVATE_FINALIZER_ERROR', json.dumps(self.saved))

    def test_actual_eleven_case_requests_use_same_registry_without_double_charge(self):
        import uuid
        reports, cases = [], []
        for name in candidate.CASES:
            case = candidate.Case(self.backend, self.root / name, str(uuid.uuid4()), name,
                dict.fromkeys(candidate.OPERATIONS, 128), transport_factory=self.registry.case_transport_factory)
            cases.append(case)
            reports.append(case.execute())
        self.assertTrue(all(r['component_case_pass'] for r in reports),
                        [(r['case'], r['primary_failure'], r['cleanup']) for r in reports if not r['component_case_pass']])
        self.assertEqual(self.registry.next_id, 27)
        self.assertEqual(sum(r['prepaid_consumed'] for r in reports), 3551)
        self.assertEqual([r['case'] for r in reports if not r['claim_released']],
                         ['admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier'])
        suffixes = [candidate.reconcile_retained(c) for c, r in zip(cases, reports) if not r['claim_released']]
        self.assertEqual(self.registry.next_id, 28)
        self.assertEqual(sum(r['prepaid_consumed'] for r in suffixes), 134)
        self.registry.close_and_drain()
        self.assertTrue(all(r['terminal'] for r in self.registry.requests.values()))
        self.assertTrue(any(not r['delivery_confirmed'] for r in self.registry.requests.values()))
        self.assertEqual(reports[9]['case'], 'missing_mint_barrier')
        self.assertFalse(reports[9]['claim_released'])

    def test_unregistered_parent_request_never_reaches_socket(self):
        factory, holder = self.factory(self.budget())
        auth = factory(self.origin, self.base, 'LOCAL_ADMIN', ValueError)
        with self.assertRaises(tracked.Blocked): auth.call('/token?grant_type=password', data={})
        with self.assertRaises(tracked.Blocked): auth.call('/admin/users/00000000-0000-0000-0000-000000000000', method='DELETE')
        self.assertEqual(self.server.count, 0)

    def test_finalizer_failure_without_body_error_propagates(self):
        def fail(*_): raise OSError('PRIVATE_CLOSURE_ERROR')
        factory, _ = self.factory(self.budget(), fail)
        with self.environment_module() as (module, gate):
            with self.assertRaisesRegex(OSError, 'PRIVATE_CLOSURE_ERROR'):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory): pass
        self.assertNotIn('PRIVATE_CLOSURE_ERROR', json.dumps(self.saved))
        self.assertEqual(self.trace[-1], 'container_stop_mock')

    def test_old_run_refused_before_new_registry_files(self):
        path = self.root / 'old-registry'
        with self.assertRaises(ValueError):
            tracked.Registry(path, run_id=candidate.OLD_RUN)
        self.assertFalse(path.exists())

    def test_partial_bootstrap_plan_stop_drains_without_parent_cleanup(self):
        budget = tracked.ParentBudget(self.root / 'parent-budget', [
            {'method': 'POST', 'route': '/admin/users', 'units': 128}], run_id=self.run_id)
        factory, _ = self.factory(budget, lambda *_: self.fail('partial ownership must not finalize'))
        with self.environment_module() as (module, gate):
            with self.assertRaises(tracked.Blocked):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory): pass
        self.assertEqual(self.server.count, 1)
        self.assertEqual(self.registry.phase, 'CLOSED')
        self.assertFalse(self.saved['integration-auth-bootstrap-partial.json']['cleanup_admitted'])

    def test_changed_close_receipt_cannot_enable_cleanup(self):
        def finalizer(ctx, auth, proof):
            name, _ = self.registry._close_ref
            (self.registry.records.folder / name).write_text('{}')
            with self.assertRaises(tracked.Blocked): auth.finalize(ctx, proof)
        factory, _ = self.factory(self.budget(), finalizer)
        with self.environment_module() as (module, gate):
            with self.assertRaisesRegex(tracked.Blocked, 'lost_terminal_proof'):
                with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory): pass
        self.assertEqual(self.server.count, 9)

    def test_cleanup_requires_live_proof_owner_and_separate_prepaid_entry(self):
        import uuid
        class Costs:
            pass
        budget = self.budget()
        def finalize(ctx, auth, proof):
            subject = ctx['claims']['a']['sub']
            ledger = candidate.Journal(self.root / 'cleanup-charge', str(uuid.uuid4()),
                                       'separate-parent-delete', dict.fromkeys(candidate.OPERATIONS, 128))
            with self.assertRaises(tracked.Blocked): auth.delete_owned({'closed': True}, subject, ledger, 'delete')
            # Failed capability use is not resumed; select another exact owned subject.
            subject = ctx['claims']['trainer']['sub']
            with self.assertRaises(tracked.Blocked): auth.delete_owned(proof, subject, ledger, 'create')
            ledger.before('delete')
            response = auth.delete_owned(proof, subject, ledger, 'delete')
            self.assertEqual(response['status'], 200)
            self.assertEqual(ledger.spent, 128)
            with self.assertRaises(tracked.Blocked): auth.delete_owned(proof, subject, ledger, 'delete')
            with self.assertRaises(tracked.Blocked): auth.call('/admin/users', data={})
        factory, _ = self.factory(budget, finalize)
        with self.environment_module() as (module, gate):
            with module.environment(gate, roles=('a', 'trainer', 'b'), tracked_auth_factory=factory): pass
        self.assertEqual(self.server.count, 10)
        self.assertEqual(budget.spent, 1152)


if __name__ == '__main__':
    unittest.main()
