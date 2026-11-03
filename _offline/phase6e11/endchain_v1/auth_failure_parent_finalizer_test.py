"""Actual loopback Auth HTTP; C receipts and every SQL observation are MOCKS."""
import copy
import json
import os
import pathlib
import types
import unittest
import uuid
from unittest.mock import patch

import admission_journal as durable
import auth_failure as af
import auth_failure_parent_finalizer as finalizer
import auth_failure_tracked as tracked
import auth_failure_tracked_test as fixtures
import fixture_db_terminality as db_terminal
import fixture_parent_closure as cparent
from admission_binding import NEW_RUN

ENV = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
       'GITHUB_REF': 'refs/heads/main'}


def events(pairs):
    return [{'ordinal': n, 'phase': phase, 'sql_sha256': tracked.sha(sql.encode()), 'confirmed': True}
            for n, (phase, sql) in enumerate(pairs, 1)]


class Tests(unittest.TestCase):
    def stop_server(self): fixtures.WiringTests.stop_server(self)

    def setUp(self):
        fixtures.WiringTests.setUp(self)
        origin = patch.object(af, 'ORIGINS', (self.origin,))
        origin.start(); self.addCleanup(origin.stop)
        self.registry = tracked.Registry(self.root / 'parent-registry', run_id=NEW_RUN)
        plan = [{'method': method, 'route': route, 'units': 128} for _ in range(3)
                for method, route in (('POST', '/admin/users'),
                                      ('POST', '/token?grant_type=password'), ('GET', '/user'))]
        budget = tracked.ParentBudget(self.root / 'parent-budget', plan, run_id=NEW_RUN)
        self.auth = tracked.Factory(self.registry, budget)(self.origin, self.base, 'LOCAL_TEST_ADMIN', ValueError)
        self.ctx = {'auth': self.auth, 'auth_request_registry': self.registry,
                    'dsn': 'MOCK_DSN', 'test_admin_token': 'LOCAL_TEST_ADMIN', 'claims': {}, 'accounts': {}}
        for role in finalizer.ROLES:
            account = {'email': role + '@example.invalid', 'password': 'LOCAL_TEST_PASSWORD'}
            user = self.auth.call('/admin/users', 'LOCAL_TEST_ADMIN', {**account, 'email_confirm': True})
            login = self.auth.call('/token?grant_type=password', data=account)
            claim = self.auth.verify(login['access_token'])
            claim['session_id'] = next(s for s, actor in self.backend.sessions.items() if actor == user['id'])
            self.ctx['claims'][role], self.ctx['accounts'][role] = claim, account
            self.auth.bind_owner(role, user['id'])
            # This test server uses a placeholder marker; the actual bootstrap has none.
            self.backend.users[user['id']]['marker'] = None
        self.seal = self.auth.close_and_drain()
        self.saved = {}
        self.gate = types.SimpleNamespace(out=self.root, container='supabase_db_fmz-db41-ci', save=self.publish)
        self.backend.autocommit = True
        self.backend.close = lambda: None
        self.backend.evidence_kind = 'MOCK_SQL_NOT_PG'
        self.native_keys = []
        original_snapshot = self.backend.snapshot
        self.before_count = 0
        def snapshot(email, marker, actor, sessions):
            self.native_keys.append('snapshot')
            # Match SQL `marker = NULL` (never true), not Python None == None.
            return original_snapshot(email, 'SQL_NULL_NEVER_EQUALS' if marker is None else marker, actor, sessions)
        self.backend.snapshot = snapshot
        original_stats = self.backend.stats
        def stats():
            self.native_keys.append('stats')
            return original_stats()
        self.backend.stats = stats
        self.fk_counts = {'identities': 0, 'operators': 0}
        def execute(sql, args=None):
            self.native_keys.append(sql)
            if sql == finalizer.BOUNDARY:
                value = dict.fromkeys(('pg17', 'tls', 'bounded_statement', 'bounded_lock', 'privileged', 'fresh'), True)
            elif sql == finalizer.FK: value = copy.deepcopy(self.fk_counts)
            else: raise AssertionError('unregistered SQL')
            return types.SimpleNamespace(fetchone=lambda: {'value': value})
        self.backend.execute = execute
        self.costs = dict.fromkeys(finalizer.ROLES, 128)
        self.env = patch.dict(os.environ, ENV)
        self.env.start(); self.addCleanup(self.env.stop)

    def publish(self, name, value):
        raw = durable.raw(value)
        with (self.root / name).open('xb') as f: f.write(raw)
        self.saved[name] = copy.deepcopy(value)

    def ref(self, path):
        return {'path': path, 'sha256': tracked.sha((self.root / path).read_bytes())}

    def c_receipts(self, *, unresolved=False, unknown=False, wrong_actor=False,
                   fake_terminal=False, bad_protocol=False):
        # Source-shaped immutable C receipts are deliberate test doubles, not C execution.
        owners = finalizer.owners(self.ctx, self.auth, self.seal)
        hashes = {finalizer.C_ROLES[r]: tracked.sha(v['actor'].encode()) for r, v in owners.items()}
        if wrong_actor: hashes['a_member'] = '0' * 64
        closed_name, closed_hash = self.registry._close_ref
        close_ref = {'path': (self.registry.records.folder / closed_name).relative_to(self.root).as_posix(),
                     'sha256': closed_hash}
        db = {'classification': 'TRACKED_DB_BACKENDS_TERMINAL', 'preparation_run': NEW_RUN,
              'registered_sessions': 3, 'db_terminality_proven': True, 'terminal_commands': 2,
              'protocol': events((('observer_identity', db_terminal.SESSION), ('backend_absence', db_terminal.ACTIVITY)))}
        if fake_terminal: db = {'worker_joined': True, 'writers_closed': True, 'mint_barrier': True}
        self.publish('mock-db-terminal.json', db)
        db_ref = self.ref('mock-db-terminal.json')
        terminal = {'preparation_run': NEW_RUN, 'actor_hashes': hashes, 'evidence_refs': [close_ref, db_ref]}
        registry = {'status': 'SCOPED_CLOSURE_CONFIRMED', 'commit_confirmed': True, 'commit_unknown': unknown,
            'absence_confirmed': True, 'deletion_proven': True, 'deleted_identities': 3, 'deleted_operators': 1,
            'remaining_counts': {'identities': 0, 'operators': 0}, 'protocol': events((
                ('registry_begin', 'BEGIN'), ('registry_check', cparent.sql.CHECK),
                ('registry_lock', cparent.REGISTRY_LOCK), ('registry_before', cparent.REGISTRY),
                ('registry_delete_operator', cparent.DELETE_OPERATOR),
                ('registry_delete_identities', cparent.DELETE_IDENTITIES), ('registry_commit', 'COMMIT'),
                ('registry_absence_begin', 'BEGIN TRANSACTION READ ONLY'), ('registry_check', cparent.sql.CHECK),
                ('registry_absence', cparent.REGISTRY), ('registry_absence_rollback', 'ROLLBACK')))}
        if bad_protocol: registry['protocol'][6]['confirmed'] = False
        result = {'status': 'NO_GO', 'preparation_run': NEW_RUN,
                  'suffix_status': 'SCOPED_PARENT_CLOSURE_CONFIRMED',
                  'unresolved_case_ids': ['unresolved'] if unresolved else [],
                  'original_receipts_unchanged': True, 'auth_objects_touched': False, 'registry': registry}
        intent = {'bootstrap': {'actor_hashes': hashes, 'commit_confirmed': True}, 'unresolved_cases': [],
                  'original_hashes': {r['path']: r['sha256'] for r in (close_ref, db_ref)},
                  'terminal_barrier': terminal}
        journal = durable.Journal(self.root / 'fixture-parent-closure-private', self.publish, 'fixture-parent-closure-journal')
        for label, record in (('intent', intent), ('registry-result', registry), ('result', result)):
            journal.save('fixture-parent-closure-' + label + '.json', record)
        journal.seal()
        return self.ref('fixture-parent-closure-private/fixture-parent-closure-result.json')

    def run_finalizer(self, ref):
        with patch.object(af, 'RealBackend', return_value=self.backend) as constructor:
            try:
                return finalizer.finalize(self.gate, self.ctx, self.auth, self.seal, ref, delete_costs=self.costs)
            finally: self.connections = constructor.call_count

    def result(self): return self.saved['auth-parent-finalizer.json']

    def test_exact_three_deletes_measured_scoped_zero_and_402_prepaid(self):
        ref = self.c_receipts()
        original = {p: tracked.sha(p.read_bytes()) for p in self.root.rglob('*.json')}
        report = self.run_finalizer(ref)
        self.assertEqual(report['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertEqual(report['status'], 'NO_GO')
        self.assertEqual(report['http_attempts'], 3)
        self.assertEqual(report['native_dispatches'], 18)
        self.assertEqual(len(self.native_keys), 18)
        self.assertEqual(report['prepaid_consumed'], 402)
        self.assertEqual(report['plan']['reserved_units'], 402)
        self.assertEqual(self.server.count, 12)
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.backend.sessions, {})
        self.assertFalse(report['global_auth_zero_claim'])
        self.assertFalse(report['full_auth_cleanup_proven'])
        self.assertFalse(report['original_claims_released'])
        self.assertTrue(all(tracked.sha(p.read_bytes()) == h for p, h in original.items()))
        exported = json.dumps(report)
        for account in self.ctx['accounts'].values():
            self.assertNotIn(account['email'], exported)
            self.assertNotIn(account['password'], exported)
        self.assertNotIn('LOCAL_TEST_ADMIN', exported)
        with self.assertRaises(FileExistsError): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 12)

    def blocked_c(self, **kwargs):
        with self.assertRaises(Exception): self.run_finalizer(self.c_receipts(**kwargs))
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.result()['prepaid_consumed'], 0)
        self.assertEqual(self.result()['suffix_status'], 'NO_GO')

    def test_missing_c_blocks_before_observer_or_delete(self):
        with self.assertRaises(tracked.Blocked): self.run_finalizer(None)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)

    def assert_invalid_c_reference(self, ref):
        with self.assertRaisesRegex(cparent.Blocked, 'parent_receipt_reference'):
            self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.native_keys, [])
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.result()['prepaid_consumed'], 0)
        self.assertEqual(self.result()['suffix_status'], 'NO_GO')

    def test_c_reference_missing_hash_blocks_before_observer(self):
        ref = self.c_receipts()
        del ref['sha256']
        self.assert_invalid_c_reference(ref)

    def test_c_reference_null_hash_blocks_before_observer(self):
        self.assert_invalid_c_reference({**self.c_receipts(), 'sha256': None})

    def test_c_reference_nonhex_hash_blocks_before_observer(self):
        self.assert_invalid_c_reference({**self.c_receipts(), 'sha256': 'z' * 64})

    def test_c_reference_short_hash_blocks_before_observer(self):
        self.assert_invalid_c_reference({**self.c_receipts(), 'sha256': 'a' * 63})

    def test_c_reference_nonstring_hash_blocks_before_observer(self):
        self.assert_invalid_c_reference({**self.c_receipts(), 'sha256': True})

    def test_c_reference_extra_field_blocks_before_observer(self):
        self.assert_invalid_c_reference({**self.c_receipts(), 'trusted': True})

    def test_c_unresolved_is_not_parent_delete_authority(self): self.blocked_c(unresolved=True)
    def test_c_unknown_commit_is_not_parent_delete_authority(self): self.blocked_c(unknown=True)
    def test_c_other_actors_are_not_parent_delete_authority(self): self.blocked_c(wrong_actor=True)
    def test_c_boolean_barrier_is_not_terminal_evidence(self): self.blocked_c(fake_terminal=True)
    def test_c_unconfirmed_protocol_is_not_terminal_evidence(self): self.blocked_c(bad_protocol=True)

    def test_c_changed_record_is_rejected(self):
        ref = self.c_receipts()
        (self.root / ref['path']).write_bytes(b'{}\n')
        with self.assertRaises(Exception): self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)

    def test_fake_auth_seal_blocks_before_observer(self):
        ref = self.c_receipts()
        self.seal = {'closed': True}
        with self.assertRaisesRegex(tracked.Blocked, 'live_terminal_seal'): self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)

    def test_c_record_change_after_observation_blocks_before_delete(self):
        ref = self.c_receipts()
        original = self.backend.snapshot
        def snapshot(*args):
            value = original(*args)
            if args[0] == 'b@example.invalid':
                (self.root / 'mock-db-terminal.json').write_bytes(b'{}\n')
            return value
        self.backend.snapshot = snapshot
        with self.assertRaises(Exception): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.result()['http_attempts'], 0)

    def test_missing_partial_bootstrap_owner_stays_no_go(self):
        ref = self.c_receipts()
        del self.auth._owners['b']
        with self.assertRaisesRegex(tracked.Blocked, 'complete_original_bootstrap'): self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)

    def test_wrong_original_email_hash_blocks(self):
        ref = self.c_receipts()
        self.ctx['accounts']['a']['email'] = 'other@example.invalid'
        with self.assertRaisesRegex(tracked.Blocked, 'owner_changed'): self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)

    def test_observed_unknown_session_blocks_all_deletes(self):
        ref = self.c_receipts()
        actor = self.ctx['claims']['b']['sub']
        self.backend.sessions['12340000-0000-4000-8000-000000000001'] = actor
        with self.assertRaisesRegex(tracked.Blocked, 'owner_or_session_changed'): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 9)

    def test_remaining_fk_blocks_parent_delete(self):
        ref = self.c_receipts()
        self.fk_counts['identities'] = 1
        with self.assertRaisesRegex(tracked.Blocked, 'fixture_fk_remains'): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.result()['native_dispatches'], 2)

    def test_real_truncated_delete_stops_further_deletes_no_replay_or_ack(self):
        ref = self.c_receipts()
        self.server.truncate_at = 10
        with self.assertRaises(af.UnknownOutcome): self.run_finalizer(ref)
        report = self.result()
        self.assertEqual(self.server.count, 10)
        self.assertEqual(report['http_attempts'], 1)
        self.assertFalse(report['deletes']['a']['acknowledged'])
        self.assertEqual(report['snapshots']['a:after']['counts']['users'], 0)
        self.assertEqual(report['suffix_status'], 'NO_GO')
        self.assertFalse(report['original_claims_released'])
        self.assertEqual(len(self.backend.users), 2)

    def test_primary_unknown_survives_secondary_observer_failure(self):
        ref = self.c_receipts()
        self.server.truncate_at = 10
        original = self.backend.stats
        calls = []
        def stats():
            calls.append(1)
            if len(calls) == 2: raise OSError('PRIVATE_OBSERVER_FAILURE')
            return original()
        self.backend.stats = stats
        with self.assertRaises(af.UnknownOutcome): self.run_finalizer(ref)
        self.assertEqual(self.result()['primary_failure']['class'], 'UnknownOutcome')
        self.assertTrue(any(x['phase'] == 'a:measure' for x in self.result()['secondary_errors']))
        self.assertNotIn('PRIVATE_OBSERVER_FAILURE', json.dumps(self.result()))

    def test_primary_unknown_survives_unknown_receipt_storage_failure(self):
        ref = self.c_receipts()
        self.server.truncate_at = 10
        original = finalizer.Ledger.event
        def event(ledger, value):
            if value.get('phase') == 'unknown' and value.get('key') == 'a:delete':
                raise OSError('PRIVATE_JOURNAL_FAILURE')
            return original(ledger, value)
        with patch.object(finalizer.Ledger, 'event', event):
            with self.assertRaises(af.UnknownOutcome): self.run_finalizer(ref)
        self.assertEqual(self.result()['primary_failure']['class'], 'UnknownOutcome')
        self.assertTrue(any(x['phase'] == 'delete_unknown_receipt' for x in self.result()['secondary_errors']))
        self.assertGreaterEqual(self.result()['prepaid_consumed'], 128)
        self.assertEqual(self.server.count, 10)
        self.assertNotIn('PRIVATE_JOURNAL_FAILURE', json.dumps(self.result()))

    def test_original_journal_corruption_refuses_next_precharge(self):
        ledger = finalizer.Ledger(self.root / 'ledger-probe', self.costs)
        ledger.before('boundary')
        spent = ledger.spent
        (ledger.folder / 'claim.json').write_bytes(b'{}\n')
        with self.assertRaises(ValueError): ledger.before('a:delete')
        self.assertEqual(ledger.spent, spent)
        self.assertTrue(ledger.storage.poisoned)
        with self.assertRaises(tracked.Blocked): ledger.receipt()

    def test_overspend_stops_before_second_delete_no_refund(self):
        ref = self.c_receipts()
        self.backend.difference = lambda *_: {'commands': 129}
        with self.assertRaisesRegex(tracked.Blocked, 'cost_exceeded'): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 10)
        self.assertEqual(self.result()['http_attempts'], 1)
        self.assertGreaterEqual(self.result()['prepaid_consumed'], 128)

    def test_snapshot_residue_prevents_success_and_remaining_deletes(self):
        ref = self.c_receipts()
        original = self.backend.snapshot
        def snapshot(*args):
            value = original(*args)
            if not value['users']: value['counts']['refresh_tokens'] = 1
            return value
        self.backend.snapshot = snapshot
        with self.assertRaisesRegex(tracked.Blocked, 'scoped_auth_residual'): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 10)

    def test_no_hosted_environment_admission(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'}):
            with self.assertRaisesRegex(tracked.Blocked, 'disposable_only'): self.run_finalizer(None)
        self.assertFalse((self.root / 'auth-parent-finalizer-private').exists())
        self.assertEqual(self.server.count, 9)


class PhysicalTests(unittest.TestCase):
    setUp = Tests.setUp
    stop_server = Tests.stop_server
    publish = Tests.publish
    ref = Tests.ref
    run_finalizer = Tests.run_finalizer
    result = Tests.result

    def physical_receipts(self, *, eligible=False, bad_terminal=False, copied_auth=False):
        import fixture_parent_physical_zero as physical
        import fixture_producer_scope as producer
        import test_fixture_parent_physical_zero as ctests
        from fixture_cleanup_runtime_test import row
        self.physical = physical
        root = pathlib.Path(__file__).resolve().parents[3]
        self.gate.sources = root
        workspace = patch.dict(os.environ, {'GITHUB_WORKSPACE': str(root)})
        workspace.start(); self.addCleanup(workspace.stop)
        sources = {p.relative_to(root).as_posix(): tracked.sha(p.read_bytes())
                   for p in [*pathlib.Path(__file__).parent.glob('*.py'), *root.joinpath('supabase/migrations').glob('*.sql')]}
        self.publish('candidate.json', {'sources': sources})
        contract = producer.source_contract(self.gate)  # Actual source/PG17 parser, no SQL execution.
        ids = {finalizer.C_ROLES[r]: self.ctx['claims'][r]['sub'] for r in finalizer.ROLES}
        self.gate.fixture_cleanup_ids = ids
        with patch.object(ctests, 'IDS', ids): database = ctests.Database(contract)
        terminal = {'status': 'NO_GO', 'classification': 'TRACKED_DB_BACKENDS_TERMINAL',
            'preparation_run': NEW_RUN, 'db_terminality_proven': True,
            'registered_sessions': 3, 'registered_sessions_sha256': '1' * 64,
            'terminal_commands': 2, 'registration_commands': 3, 'auth_mint_barrier_proven': False,
            'external_producers_covered': False, 'full_cleanup_proven': False,
            'protocol': events((('observer_identity', db_terminal.SESSION), ('backend_absence', db_terminal.ACTIVITY)))}
        if bad_terminal: terminal['protocol'][1]['sql_sha256'] = '0' * 64
        self.publish('mock-db-terminal.json', terminal)
        terminal_ref = self.ref('mock-db-terminal.json')
        close_name, close_hash = self.registry._close_ref
        close_ref = {'path': (self.registry.records.folder / close_name).relative_to(self.root).as_posix(), 'sha256': close_hash}
        if copied_auth:
            self.publish('copied-auth-close.json', json.loads((self.root / close_ref['path']).read_bytes()))
            close_ref = self.ref('copied-auth-close.json')
        hashes = {r: tracked.sha(v.encode()) for r, v in ids.items()}
        bootstrap = {'status': 'DISPOSABLE_BOOTSTRAP_PASS', 'commit_confirmed': True,
            'registered_accounts': 3, 'existing_rows_overwritten': False, 'after_registry_confirmed': True,
            'before': {'identities': 0, 'operators': 0}, 'actor_hashes': hashes}
        self.publish('admission-fixture-bootstrap.json', bootstrap)
        contexts = [{k: str(uuid.uuid4()) for k in ('window', 'a', 'b')} for _ in range(2 if eligible else 1)]
        original = durable.Journal(self.root / 'admission-fixture-private-journal', self.publish, 'admission-fixture-journal')
        cases = []
        for n, context in enumerate(contexts):
            uid = context['window']
            prefix = 'fixture-cleanup-' + uid + '-'
            bound = {'preparation_run': NEW_RUN, 'case': uid, 'scope_sha256': physical.digest(physical.parameters(context)),
                     'component_only': True}
            original.save(prefix + 'parent-setup.json', {**bound, 'context': context,
                          'actor_hashes': hashes, 'before_writer_begin': True})
            original.save(prefix + 'baseline.json', {**bound, 'rows': [], 'source': 'actual_empty_inventory'})
            if n == 0:
                receipt = {**bound, 'status': 'NO_GO', 'commit_unknown': True, 'commit_confirmed': False,
                           'cleanup_complete': False, 'deletion_proven': False}
                original.save(prefix + 'result.json', receipt)
                name = 'lost_commit'
            else:
                receipt = {'status': 'BLOCKED', 'reason': 'cleanup_writer_barrier_required', 'deletion_proven': False}
                original.save(prefix + 'writer-0000.json', {**bound, 'rows': [row('windows')],
                              'xid': '41', 'before_commit': True, 'previous': physical.digest([])})
                database.rows[uid] = [row('windows')]
                name = 'missing_barrier'
            cases.append({'case': name, 'fixture_case': uid, 'receipt': receipt})
        original.save('fixture-cleanup-component-detail.json', {'status': 'COMPONENT_PASS',
                      'preparation_run': NEW_RUN, 'cases': cases})
        original.save('fixture-cleanup-db-terminal.json', {'terminal': terminal,
                      'fixture_case_ids': [c['window'] for c in contexts], 'component_status': 'COMPONENT_PASS'})
        original.seal()
        self.original_files = {p: tracked.sha(p.read_bytes()) for p in (self.root / 'admission-fixture-private-journal').glob('*.json')}
        # Run actual C validators/writers against MOCK native SQL, not actual PG.
        def zero(context, original_ref):
            return {'status': 'NO_GO', 'classification': 'physical_zero_original_commit_unknown',
                'preparation_run': NEW_RUN, 'case': context['window'],
                'scope_sha256': physical.digest(physical.parameters(context)), 'original_ref': original_ref,
                'original_commit_unknown': True, 'physical_zero': True, 'delete_replayed': False,
                'deletion_proven': False, 'original_claims_released': False, 'full_cleanup_proven': False,
                'external_producers_covered': False, 'registry_cleanup_admitted': False,
                'terminal_sha256': physical.digest(terminal), 'protocol_limit': 5, 'admitted_attempts': 5,
                'protocol': events((('zero_begin', 'BEGIN TRANSACTION READ ONLY'), ('zero_session', db_terminal.SESSION),
                    ('backend_absence', db_terminal.ACTIVITY), ('zero_inventory', physical.sql.INVENTORY), ('zero_rollback', 'ROLLBACK')))}
        with patch.object(physical.NativeRuntime, 'disposable', return_value=database), patch.object(
                db_terminal.TrackedRuntime, 'physical_zero', side_effect=zero):
            scope = producer.Scope(self.gate)
            scope.before_bootstrap()
            result = physical.run(self.gate, scope=scope, tracked=object.__new__(db_terminal.TrackedRuntime),
                                  terminal_ref=terminal_ref, auth_close_ref=close_ref)
        self.assertEqual(result['classification'], 'REGISTRY_CLOSED_WITH_ORIGINAL_COMMIT_UNKNOWN', result.get('reason'))
        self.c_result = result
        return self.ref('fixture-parent-physical-zero-private/result.json')

    def resign(self, name, mutate):
        # Deliberately reseal TEST evidence to test semantics, not only stale hashes.
        folder = self.root / 'fixture-parent-physical-zero-private'
        value = json.loads((folder / name).read_bytes())
        mutate(value)
        (folder / name).write_bytes(durable.raw(value))
        def publish(name, value): (self.root / name).write_bytes(durable.raw(value))
        journal = durable.Journal(self.root / ('test-reseal-' + uuid.uuid4().hex), publish, 'fixture-parent-physical-zero-journal')
        for p in folder.glob('*.json'): journal.save(p.name, json.loads(p.read_bytes()))
        journal.seal()
        return self.ref('fixture-parent-physical-zero-private/result.json')

    def reject(self, ref):
        with self.assertRaises(Exception): self.run_finalizer(ref)
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.native_keys, [])
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.result()['prepaid_consumed'], 0)

    def test_physical_n1_e0_allows_parent_cleanup_without_historical_promotion(self):
        report = self.run_finalizer(self.physical_receipts())
        self.assertEqual(report['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertEqual(report['status'], 'NO_GO')
        self.assertTrue(report['original_fixture_commit_unknown'])
        self.assertFalse(report['original_commit_reclassified'])
        self.assertFalse(report['original_claims_released'])
        self.assertEqual(report['prepaid_consumed'], 402)
        self.assertEqual(self.server.count, 12)
        self.assertTrue(all(tracked.sha(p.read_bytes()) == h for p, h in self.original_files.items()))

    def test_physical_n2_e1_uses_source_defined_38_command_plan(self):
        ref = self.physical_receipts(eligible=True)
        self.assertEqual(self.c_result['emitted_attempts'], 38)
        self.assertEqual(self.run_finalizer(ref)['http_attempts'], 3)

    def test_forged_terminal_protocol_is_not_accepted_from_sealed_original(self):
        self.reject(self.physical_receipts(bad_terminal=True))

    def test_copied_auth_close_is_not_the_live_registry_reference(self):
        self.reject(self.physical_receipts(copied_auth=True))

    def test_physical_source_binding_cannot_be_caller_boolean(self):
        self.physical_receipts()
        self.reject(self.resign('result.json', lambda r: r.update(source_binding={'bound': True})))

    def test_physical_plan_cannot_omit_lock_or_sql_confirmation(self):
        self.physical_receipts()
        self.reject(self.resign('result.json', lambda r: r['protocol'][1].update(confirmed=False)))

    def test_physical_scope_cannot_select_only_unknown_case(self):
        self.physical_receipts(eligible=True)
        self.reject(self.resign('result.json', lambda r: r.update(case_ids=r['unknown_case_ids'])))

    def test_physical_eligible_count_cannot_be_relabelled_zero(self):
        self.physical_receipts(eligible=True)
        self.reject(self.resign('result.json', lambda r: r.update(eligible_case_ids=[])))

    def test_physical_original_hash_cannot_be_null(self):
        self.physical_receipts()
        self.reject(self.resign('intent.json', lambda r: r['original_hashes'].update({'admission-fixture-bootstrap.json': None})))

    def test_physical_terminal_ref_cannot_omit_hash(self):
        self.physical_receipts()
        self.reject(self.resign('result.json', lambda r: r['terminal_ref'].pop('sha256')))

    def test_physical_zero_cannot_promote_unknown_commit(self):
        self.physical_receipts()
        self.reject(self.resign('result.json', lambda r: r.update(original_commit_reclassified=True)))

    def test_unknown_new_registry_commit_still_refuses_auth_cleanup(self):
        self.physical_receipts()
        self.reject(self.resign('result.json', lambda r: r.update(registry_commit_unknown=True)))

    def test_physical_zero_observer_protocol_cannot_be_forged(self):
        self.physical_receipts()
        name = self.c_result['cases'][0]['physical_zero_record']
        self.resign(name, lambda r: r.update(protocol=[]))
        raw = json.loads((self.root / 'fixture-parent-physical-zero-private' / name).read_bytes())
        self.reject(self.resign('result.json', lambda r: r['cases'][0].update(zero_sha256=self.physical.digest(raw))))

    def test_producer_after_observation_cannot_be_replaced_by_terminal_flag(self):
        self.physical_receipts()
        path = self.root / 'fixture-producer-scope-after-result.json'
        value = json.loads(path.read_bytes()); value['status'] = 'TERMINAL'
        path.write_bytes(durable.raw(value))
        self.reject(self.resign('intent.json', lambda r: r.update(scope_sha256=self.physical.digest(value))))

    def test_physical_receipt_without_hash_refuses_before_observer(self):
        ref = self.physical_receipts(); del ref['sha256']
        self.reject(ref)

    def test_physical_original_changed_after_observation_blocks_before_delete(self):
        ref = self.physical_receipts()
        snapshot = self.backend.snapshot
        def change(*args):
            value = snapshot(*args)
            if args[0] == 'b@example.invalid':
                next(iter(self.original_files)).write_bytes(b'{}\n')
            return value
        self.backend.snapshot = change
        with self.assertRaises(Exception): self.run_finalizer(ref)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.result()['http_attempts'], 0)


if __name__ == '__main__': unittest.main()
