"""Mocked transport/source tests only. No actual PG17 terminality claim."""
import copy
import hashlib
import json
import os
import pathlib
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

import fixture_db_terminality as module
import fixture_cleanup_runtime_ci as ci
from fixture_cleanup_runtime import Blocked, digest
from fixture_cleanup_runtime_test import CONTEXT, Cursor, row
from test_fixture_parent_closure import ENV, IDS


class Server:
    def __init__(self):
        self.sessions, self.calls, self.runtimes = [], [], []
        self.fail = None
        self.retain_closed = False
        self.inventory = []
        self.server_id = 'cluster-1'
        self.invalid = {}

    def runtime(self, gate):
        server = self
        class Runtime:
            environment = 'disposable_ci'
            def __init__(self): self.closed = False
            def clear(self): self.closed = True
            def connect(self):
                if self.closed: raise AssertionError('native factory closed')
                raw = Raw(server)
                server.sessions.append(raw)
                return raw
        runtime = Runtime()
        self.runtimes.append(runtime)
        return runtime


class Raw:
    autocommit = True
    def __init__(self, server):
        self.server, self.closed, self.readonly = server, False, False
        self.info = types.SimpleNamespace(backend_pid=100 + len(server.sessions))
        self.started = '2026-11-03 12:00:%02d+00' % len(server.sessions)
        self.tag = ''
    def close(self): self.closed = True
    def execute(self, text, args=None):
        self.server.calls.append((self.info.backend_pid, text, args))
        if self.server.fail and self.server.fail in text: raise TimeoutError('injected '+self.server.fail)
        if text.startswith('BEGIN'): self.readonly = True; return Cursor([])
        if text == 'ROLLBACK': self.readonly = False; return Cursor([])
        if 'from pg_stat_activity where pid=pg_backend_pid()' in text:
            if 'set_config(' in text: self.tag = args[0]
            return Cursor([{**dict.fromkeys(module.CHECKS, True), 'pid': self.info.backend_pid,
                'backend_start': self.started, 'datid': '5', 'postmaster_start': '2026-11-03 11:00:00+00',
                'cluster_id': self.server.server_id, 'application_name': self.tag,
                'readonly': self.readonly, **self.server.invalid}])
        if 'jsonb_to_recordset' in text:
            owned, prefix = json.loads(args[0]), args[1]
            return Cursor([{'pid': r.info.backend_pid, 'backend_start': r.started, 'application_name': r.tag}
                for r in self.server.sessions if (not r.closed or self.server.retain_closed)
                and (r.tag.startswith(prefix) or any(x == {'pid': r.info.backend_pid,
                    'backend_start': r.started} for x in owned))][:65])
        if "'rows',coalesce" in text:
            return Cursor([{'value': {'rows': copy.deepcopy(self.server.inventory), 'xid': None}}])
        return Cursor([])


class Tests(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.saved = {}
        self.gate = types.SimpleNamespace(container='supabase_db_fmz-db41-ci', out=pathlib.Path.cwd())
        self.env = patch.dict(os.environ, ENV); self.env.start(); self.addCleanup(self.env.stop)
        self.native = patch.object(module.NativeRuntime, 'disposable', side_effect=self.server.runtime)
        self.native.start(); self.addCleanup(self.native.stop)
        self.factory = module.TrackedRuntime.disposable(self.gate, self.save)
        self.original = {'preparation_run': module.NEW_RUN, 'case': CONTEXT['window'],
            'scope_sha256': digest([CONTEXT['window'], [CONTEXT['a'], CONTEXT['b']]]),
            'component_only': True, 'status': 'NO_GO', 'commit_unknown': True,
            'commit_confirmed': False, 'cleanup_complete': False, 'deletion_proven': False}
        self.ref = {'path': 'original.json', 'sha256': 'a'*64}

    def save(self, name, value):
        if name in self.saved: raise FileExistsError(name)
        self.saved[name] = copy.deepcopy(value)

    def terminal(self):
        handle = self.factory.connect()
        handle.execute('BEGIN')
        self.factory.clear()
        return self.factory.terminal()

    def zero(self):
        with patch.object(module, 'reference', return_value=copy.deepcopy(self.original)):
            return self.factory.physical_zero(CONTEXT, self.ref)

    def test_registration_is_durable_before_business_query_and_uses_real_pid(self):
        handle = self.factory.connect()
        receipts = [v for k, v in self.saved.items() if 'session-' in k]
        self.assertEqual(receipts[0]['pid'], self.server.sessions[0].info.backend_pid)
        self.assertEqual(len(self.server.calls), 1)
        self.assertTrue(receipts[0]['application_name'].startswith('fmz-fixture-'))
        handle.execute('BEGIN')
        self.assertEqual(len(self.server.calls), 2)

    def test_clear_closes_actual_handles_and_seals_mint_and_old_handle(self):
        handle = self.factory.connect()
        self.factory.clear()
        self.assertTrue(self.server.sessions[0].closed)
        self.assertTrue(self.server.runtimes[0].closed)
        before = len(self.server.calls)
        for action in (self.factory.connect, lambda: handle.execute('BEGIN')):
            with self.assertRaisesRegex(Blocked, 'factory_closed'): action()
        self.assertEqual(len(self.server.calls), before)

    def test_cross_thread_connect_and_execute_cannot_race_seal(self):
        handle = self.factory.connect()
        errors = []
        def worker():
            for action in (self.factory.connect, lambda: handle.execute('BEGIN'), self.factory.clear):
                try: action()
                except Blocked as error: errors.append(str(error))
        thread = threading.Thread(target=worker); thread.start(); thread.join()
        self.assertEqual(errors, ['db_terminal_nonowner_thread']*3)
        self.assertEqual(len(self.server.calls), 1)

    def test_terminal_uses_independent_native_observer_and_two_commands(self):
        terminal = self.terminal()
        self.assertEqual(len(self.server.runtimes), 2)
        self.assertEqual(terminal['terminal_commands'], 2)
        self.assertTrue(terminal['db_terminality_proven'])
        self.assertFalse(terminal['external_producers_covered'])
        self.assertFalse(terminal['auth_mint_barrier_proven'])
        self.assertEqual(terminal['status'], 'NO_GO')
        self.assertTrue(all(r.closed for r in self.server.sessions))

    def test_client_close_does_not_prove_server_absence_and_no_poll_retry(self):
        self.server.retain_closed = True
        with self.assertRaisesRegex(Blocked, 'backend_still_present'): self.terminal()
        before = len(self.server.calls)
        with self.assertRaisesRegex(Blocked, 'duplicate_observation'): self.factory.terminal()
        self.assertEqual(len(self.server.calls), before)
        self.assertFalse(any(k.endswith('terminal.json') for k in self.saved))

    def test_pid_reuse_does_not_target_or_block_unrelated_backend(self):
        self.factory.connect(); self.factory.clear()
        stranger = self.server.runtime(self.gate).connect()
        stranger.info.backend_pid = self.server.sessions[0].info.backend_pid
        stranger.started = '2026-11-03 13:00:00+00'
        self.assertTrue(self.factory.terminal()['db_terminality_proven'])
        self.assertFalse(stranger.closed)

    def test_owned_pid_with_changed_application_name_still_blocks(self):
        self.factory.connect(); self.factory.clear()
        self.server.sessions[0].closed = False
        self.server.sessions[0].tag = 'renamed'
        with self.assertRaisesRegex(Blocked, 'backend_still_present'): self.factory.terminal()

    def test_unregistered_same_tag_session_blocks_instead_of_becoming_owned(self):
        self.factory.connect(); self.factory.clear()
        stranger = self.server.runtime(self.gate).connect()
        stranger.tag = self.server.sessions[0].tag
        with self.assertRaisesRegex(Blocked, 'backend_still_present'): self.factory.terminal()
        self.assertFalse(stranger.closed)

    def test_no_registration_or_no_seal_cannot_be_filled_in_by_boolean(self):
        with self.assertRaisesRegex(Blocked, 'complete_registration'): self.factory.terminal()
        with self.assertRaises(TypeError): self.factory.terminal(worker_joined=True)

    def test_identity_pid_mismatch_blocks_before_handle_escapes(self):
        self.server.invalid['pid'] = 999
        with self.assertRaisesRegex(Blocked, 'identity_or_limits'): self.factory.connect()
        self.assertTrue(self.server.sessions[0].closed)
        self.factory.clear()
        with self.assertRaisesRegex(Blocked, 'complete_registration'): self.factory.terminal()

    def test_prepared_transactions_or_untracked_stats_or_timeout_relaxation_block(self):
        for field in ('no_prepared', 'tracked', 'bounded_statement', 'bounded_lock', 'fresh_snapshots'):
            with self.subTest(field=field):
                server = Server(); server.invalid[field] = False
                with patch.object(module.NativeRuntime, 'disposable', side_effect=server.runtime):
                    factory = module.TrackedRuntime.disposable(self.gate, self.save)
                    with self.assertRaisesRegex(Blocked, 'identity_or_limits'): factory.connect()

    def test_server_restart_or_other_cluster_blocks_observer(self):
        self.factory.connect(); self.factory.clear()
        self.server.server_id = 'other-cluster'
        with self.assertRaisesRegex(Blocked, 'server_changed'): self.factory.terminal()

    def test_registration_storage_failure_closes_handle_and_poisons_factory(self):
        factory = module.TrackedRuntime.disposable(self.gate, lambda n, v:
            (_ for _ in ()).throw(OSError('registration storage')) if 'session-' in n else self.save(n, v))
        with self.assertRaises(OSError): factory.connect()
        self.assertTrue(self.server.sessions[-1].closed)
        with self.assertRaisesRegex(Blocked, 'factory_closed'): factory.connect()

    def test_charge_failure_prevents_actual_registration_query(self):
        factory = module.TrackedRuntime.disposable(self.gate, lambda n, v:
            (_ for _ in ()).throw(OSError('charge storage')) if '-charge-' in n else self.save(n, v))
        with self.assertRaises(OSError): factory.connect()
        self.assertEqual(self.server.calls, [])

    def test_connection_cap_is_before_connect_and_never_increased(self):
        for _ in range(64): self.factory.connect().close()
        with self.assertRaisesRegex(Blocked, 'connection_limit'): self.factory.connect()
        self.assertEqual(len(self.server.sessions), 64)
        self.assertEqual(len(self.server.calls), 64)

    def test_zero_has_five_commands_preserves_original_no_go_and_never_deletes(self):
        self.terminal()
        original = copy.deepcopy(self.original)
        start = len(self.server.calls)
        result = self.zero()
        texts = [c[1] for c in self.server.calls[start:]]
        self.assertEqual(len(texts), 5)
        self.assertEqual(texts[-1], 'ROLLBACK')
        self.assertFalse(any('DELETE' in t.upper() or t == 'COMMIT' for t in texts))
        self.assertEqual(result['classification'], 'physical_zero_original_commit_unknown')
        self.assertEqual(result['status'], 'NO_GO')
        self.assertTrue(result['physical_zero'])
        self.assertFalse(result['deletion_proven'])
        self.assertFalse(result['original_claims_released'])
        self.assertEqual(self.original, original)
        with self.assertRaisesRegex(Blocked, 'duplicate'): self.zero()

    def test_real_original_file_hash_is_checked_before_and_after_observation(self):
        self.terminal()
        with tempfile.TemporaryDirectory(prefix='fmz-db-terminal-') as directory:
            self.gate.out = pathlib.Path(directory)
            raw = json.dumps(self.original).encode()
            path = self.gate.out/'original.json'; path.write_bytes(raw)
            import hashlib
            ref = {'path': 'original.json', 'sha256': hashlib.sha256(raw).hexdigest()}
            result = self.factory.physical_zero(CONTEXT, ref)
            self.assertTrue(result['physical_zero'])
            self.assertEqual(path.read_bytes(), raw)

    def test_wrong_scope_or_unknown_claim_binding_stops_before_sql(self):
        self.terminal()
        self.original['scope_sha256'] = 'bad'
        before = len(self.server.calls)
        with self.assertRaisesRegex(Blocked, 'original_unknown_commit_binding'): self.zero()
        self.assertEqual(len(self.server.calls), before)

    def test_nonzero_or_foreign_rows_do_not_get_zero_receipt(self):
        self.terminal(); self.server.inventory = [row()]
        before = len(self.server.calls)
        with self.assertRaisesRegex(Blocked, 'scoped_rows_remain'): self.zero()
        self.assertEqual(len(self.server.calls)-before, 5)
        self.assertEqual(self.server.calls[-1][1], 'ROLLBACK')
        self.assertFalse(any('-zero-' in k and k.endswith('-result.json') for k in self.saved))

    def test_zero_session_failure_rolls_back_within_three_commands(self):
        self.terminal(); self.server.fail = 'from pg_stat_activity where'
        before = len(self.server.calls)
        with self.assertRaises(TimeoutError): self.zero()
        self.assertEqual(len(self.server.calls)-before, 3)
        self.assertEqual(self.server.calls[-1][1], 'ROLLBACK')

    def test_live_backend_recheck_prevents_stale_terminal_receipt_use(self):
        self.terminal()
        self.server.sessions[0].closed = False
        before = len(self.server.calls)
        with self.assertRaisesRegex(Blocked, 'backend_still_present'): self.zero()
        self.assertEqual(len(self.server.calls)-before, 4)
        self.assertEqual(self.server.calls[-1][1], 'ROLLBACK')

    def test_rollback_error_no_retry_and_no_zero_receipt(self):
        self.terminal(); self.server.fail = 'ROLLBACK'
        before = len(self.server.calls)
        with self.assertRaises(TimeoutError): self.zero()
        self.assertEqual(len(self.server.calls)-before, 5)
        with self.assertRaisesRegex(Blocked, 'duplicate'): self.zero()
        self.assertFalse(any('-zero-' in k and k.endswith('-result.json') for k in self.saved))

    def test_inventory_failure_keeps_rollback_within_five(self):
        self.terminal(); self.server.fail = "'rows',coalesce"
        before = len(self.server.calls)
        with self.assertRaises(TimeoutError): self.zero()
        self.assertEqual(len(self.server.calls)-before, 5)
        self.assertEqual(self.server.calls[-1][1], 'ROLLBACK')

    def test_lost_begin_and_failed_rollback_keep_original_error_and_close(self):
        self.terminal()
        primary = ConnectionError('lost BEGIN')
        original_execute = Raw.execute
        def execute(raw, text, args=None):
            if text == 'ROLLBACK': raise OSError('rollback error')
            result = original_execute(raw, text, args)
            if text.startswith('BEGIN'): raise primary
            return result
        with patch.object(Raw, 'execute', execute):
            with self.assertRaises(ConnectionError) as caught: self.zero()
        self.assertIs(caught.exception, primary)
        self.assertIn('rollback failed: OSError', primary.__notes__[0])
        self.assertTrue(self.server.sessions[-1].closed)
        charges = [v for k, v in self.saved.items() if '-zero-' in k and '-charge-' in k]
        self.assertEqual(len(charges), 2)
        self.assertFalse(any('-zero-' in k and k.endswith('-result.json') for k in self.saved))

    def test_terminal_primary_backend_error_survives_observer_close_failure(self):
        self.factory.connect(); self.factory.clear()
        self.server.retain_closed = True
        with patch.object(Raw, 'close', side_effect=OSError('observer close')):
            with self.assertRaisesRegex(Blocked, 'backend_still_present') as caught:
                self.factory.terminal()
        self.assertIn('close failed: OSError', caught.exception.__notes__[0])

    def test_zero_maximum_eleven_distinct_cases_then_no_dispatch(self):
        self.terminal()
        import uuid
        for _ in range(11):
            context = {k: str(uuid.uuid4()) for k in ('window', 'a', 'b')}
            original = {**self.original, 'case': context['window'],
                        'scope_sha256': digest([context['window'], [context['a'], context['b']]])}
            with patch.object(module, 'reference', return_value=original):
                self.assertTrue(self.factory.physical_zero(context, self.ref)['physical_zero'])
        before = len(self.server.calls)
        with self.assertRaisesRegex(Blocked, 'case_limit'): self.zero()
        self.assertEqual(len(self.server.calls), before)

    def test_terminal_receipt_save_failure_never_authorizes_zero(self):
        def save(name, value):
            if name.endswith('terminal.json'): raise OSError('terminal receipt storage')
            self.save(name, value)
        factory = module.TrackedRuntime.disposable(self.gate, save)
        factory.connect(); factory.clear()
        with self.assertRaises(OSError): factory.terminal()
        with self.assertRaisesRegex(Blocked, 'observation_required'):
            factory.physical_zero(CONTEXT, self.ref)

    def test_poisoned_zero_charge_storage_preserves_error_and_does_not_bypass_ledger(self):
        primary = OSError('poisoned zero store')
        def save(name, value):
            if '-zero-' in name and '-charge-' in name and value['phase'] != 'zero_begin':
                raise primary
            self.save(name, value)
        factory = module.TrackedRuntime.disposable(self.gate, save)
        factory.connect(); factory.clear(); factory.terminal()
        before = len(self.server.calls)
        with patch.object(module, 'reference', return_value=self.original):
            with self.assertRaises(OSError) as caught: factory.physical_zero(CONTEXT, self.ref)
        self.assertIs(caught.exception, primary)
        self.assertEqual([t for _, t, _ in self.server.calls[before:]], ['BEGIN TRANSACTION READ ONLY'])
        self.assertIn('rollback failed: OSError', primary.__notes__[0])
        self.assertTrue(self.server.sessions[-1].closed)

    def test_non_ci_gate_is_rejected_before_new_native_factory(self):
        before = len(self.server.runtimes)
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'}):
            with self.assertRaisesRegex(Blocked, 'disposable_required'):
                module.TrackedRuntime.disposable(self.gate, self.save)
        self.assertEqual(len(self.server.runtimes), before)

    def test_sql_is_single_statement_and_activity_has_bounded_identity_predicate(self):
        from sql_protocol import parser, statements
        for text in (module.REGISTER, module.SESSION, module.ACTIVITY):
            self.assertEqual(len(statements(text)), 1)
            self.assertEqual(len(parser().parse_sql(text)), 1)
        self.assertIn('a.backend_start=e.backend_start::timestamptz', module.ACTIVITY)
        self.assertIn('limit 65', module.ACTIVITY)
        self.assertNotIn('pg_terminate_backend', module.ACTIVITY)


class RunnerBindingTests(unittest.TestCase):
    """Invoke the real runner and tracker; fault only the native SQL transport."""
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='fmz-fixture-runner-')
        self.addCleanup(self.directory.cleanup)
        self.out = pathlib.Path(self.directory.name).resolve()
        self.root = pathlib.Path(__file__).resolve().parents[3]
        self.saved = {}
        self.gate = types.SimpleNamespace(container='supabase_db_fmz-db41-ci', out=self.out,
            sources=self.root, save=self.save, fixture_cleanup_ids=IDS)
        self.manifest = {'sources': {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in pathlib.Path(__file__).resolve().parent.glob('*.py')}}
        (self.out/'candidate.json').write_text(json.dumps(self.manifest))
        self.server = Server()
        native = patch.object(module.NativeRuntime, 'disposable', side_effect=self.server.runtime)
        native.start(); self.addCleanup(native.stop)
        self.native = native
        env = patch.dict(os.environ, {**ENV, 'GITHUB_WORKSPACE': str(self.root)})
        env.start(); self.addCleanup(env.stop)
        original = Raw.execute
        def execute(raw, text, args=None):
            if text == module.sql.CHECK:
                raw.server.calls.append((raw.info.backend_pid, text, args))
                return Cursor([{**dict.fromkeys(('pg17', 'bounded_statement', 'bounded_lock',
                    'privileged', 'origin', 'unbound'), True), 'readonly': raw.readonly}])
            if text.startswith('select role,user_id::text id'):
                raw.server.calls.append((raw.info.backend_pid, text, args))
                return Cursor([{'role': r, 'id': value} for r, value in IDS.items()])
            if text.startswith('select * from ('):
                raw.server.calls.append((raw.info.backend_pid, text, args))
                return Cursor([])
            if text.startswith('insert into fmz6e11_private.windows'):
                raw.server.calls.append((raw.info.backend_pid, text, args))
                raise ConnectionError('injected writer response loss')
            return original(raw, text, args)
        wire = patch.object(Raw, 'execute', execute)
        wire.start(); self.addCleanup(wire.stop)

    def save(self, name, value):
        if name in self.saved: raise FileExistsError(name)
        self.saved[name] = copy.deepcopy(value)

    def test_injected_real_tracker_surrounds_actual_partial_writer_path(self):
        tracked = module.TrackedRuntime.disposable(self.gate, self.save)
        result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['error_class'], 'ConnectionError')
        self.assertTrue(result['fixture_mutation_attempted'])
        self.assertTrue(result['tracked_db_terminality_proven'])
        self.assertFalse(result['full_endchain_pass'])
        self.assertFalse(result['registry_cleanup_admitted'])
        self.assertFalse(result['server_global_quiescence'])
        self.assertEqual(len(self.server.runtimes), 2)  # Injected producer + independent observer only.
        terminal = self.saved['fixture-cleanup-db-terminal.json']
        self.assertEqual(terminal['component_status'], 'NO_GO')
        self.assertEqual(len(terminal['fixture_case_ids']), 1)
        self.assertEqual(terminal['terminal']['registered_sessions'], 3)
        self.assertEqual(result['tracked_runtime_additional_sql_count'], 5)
        self.assertTrue(all(s.closed for s in self.server.sessions))
        self.assertTrue(self.server.runtimes[0].closed)
        self.assertIn('jsonb_to_recordset', self.server.calls[-1][1])
        self.assertIn('fixture_db_terminality', [x['module'] for x in
            terminal['tracked_runtime_binding']['source_binding']['modules']])
        self.assertLess(list(self.saved).index('fixture-cleanup-runtime-binding.json'),
                        next(i for i, k in enumerate(self.saved) if 'session-' in k))

    def test_default_path_does_not_create_tracker_or_observe_terminal(self):
        result = ci.run(self.gate)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['error_class'], 'ConnectionError')
        self.assertNotIn('tracked_db_terminality_proven', result)
        self.assertEqual(len(self.server.runtimes), 1)
        self.assertNotIn('fixture-cleanup-db-terminal.json', self.saved)
        self.assertFalse(any('set_config(' in text for _, text, _ in self.server.calls))

    def test_terminal_failure_preserves_component_primary_and_original_receipts(self):
        tracked = module.TrackedRuntime.disposable(self.gate, self.save)
        self.server.retain_closed = True
        result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['error_class'], 'ConnectionError')
        self.assertEqual(result['reason'], 'cleanup_component_execution_error')
        self.assertFalse(result['tracked_db_terminality_proven'])
        self.assertIsNone(result['tracked_runtime_terminal_receipt'])
        self.assertIn('tracked_terminal_error_class', self.saved['fixture-cleanup-component-detail.json'])
        self.assertNotIn('fixture-cleanup-db-terminal.json', self.saved)

    def test_missing_candidate_helper_blocks_before_native_query(self):
        tracked = module.TrackedRuntime.disposable(self.gate, self.save)
        del self.manifest['sources']['_offline/phase6e11/endchain_v1/fixture_db_terminality.py']
        (self.out/'candidate.json').write_text(json.dumps(self.manifest))
        result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['error_class'], 'ModuleBindingError')
        self.assertEqual(self.server.calls, [])
        self.assertFalse(result['tracked_db_terminality_proven'])
        tracked.clear()  # Binding failed before ownership transfer to the runner.

    def test_external_same_basename_module_origin_blocks_before_query(self):
        tracked = module.TrackedRuntime.disposable(self.gate, self.save)
        external = self.out/'fixture_db_terminality.py'
        external.write_bytes(pathlib.Path(module.__file__).read_bytes())
        with patch.object(module, '__file__', str(external)):
            result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(self.server.calls, [])
        tracked.clear()

    def test_factory_for_another_gate_is_not_accepted(self):
        other = types.SimpleNamespace(**vars(self.gate))
        tracked = module.TrackedRuntime.disposable(other, self.save)
        result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['reason'], 'db_terminal_component_gate_changed')
        self.assertEqual(self.server.calls, [])
        tracked.clear()

    def test_early_component_prerequisite_failure_still_closes_bound_bootstrap_handles(self):
        tracked = module.TrackedRuntime.disposable(self.gate, self.save)
        handle = tracked.connect()
        del self.gate.fixture_cleanup_ids
        result = ci.run(self.gate, runtime=tracked)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertTrue(result['tracked_db_terminality_proven'])
        self.assertTrue(self.server.sessions[0].closed)
        self.assertEqual(result['tracked_runtime_additional_sql_count'], 2)  # Prior bootstrap registration excluded.
        with self.assertRaisesRegex(Blocked, 'factory_closed'): handle.execute('BEGIN')

    def test_caller_boolean_or_untracked_runtime_cannot_claim_terminality(self):
        untracked = self.server.runtime(self.gate)
        result = ci.run(self.gate, runtime=untracked)
        self.assertEqual(result['reason'], 'cleanup_explicit_tracked_runtime_required')
        self.assertEqual(self.server.calls, [])
        self.assertFalse(result['tracked_db_terminality_proven'])


if __name__ == '__main__': unittest.main()
