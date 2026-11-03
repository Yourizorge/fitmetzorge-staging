"""Real localhost bootstrap; SQL and proposed wiring mocked unless stated.

Some cases use actual loaded main hooks and localhost HTTP deletes; none proves
real PG state. Catalog cases reuse C's actual Scope validator on mocked wire rows.
"""
import ast
import copy
import contextlib
import json
import importlib.util
import os
import pathlib
import sys
import threading
import unittest
from unittest.mock import patch

import auth_failure as af
import auth_failure_parent_finalizer_test as shared
import auth_pre_fixture_closure as module
import admission_cleanup_composition as composition
import fixture_producer_scope as producer
import test_fixture_producer_scope as catalog_tests


def catalog_fixture(test):
    root = pathlib.Path(module.__file__).resolve().parents[3]
    test.gate.sources = root
    files = list(pathlib.Path(module.__file__).resolve().parent.glob('*.py'))
    files += list((root / 'supabase/migrations').glob('*.sql'))
    test.publish('candidate.json', {'sources': {
        p.relative_to(root).as_posix(): module.durable.sha(p.read_bytes()) for p in files}})
    env = patch.dict(os.environ, {'GITHUB_WORKSPACE': str(root)})
    env.start(); test.addCleanup(env.stop)
    test.catalog_contract = producer.source_contract(test.gate)
    test.catalog_wire = catalog_tests.Wire(catalog_tests.samples(test.catalog_contract))
    test.admin_suspended = False
    test.suspensions = 0
    @contextlib.contextmanager
    def suspend():
        test.assertFalse(test.admin_suspended)
        test.admin_suspended = True
        test.suspensions += 1
        try: yield
        finally: test.admin_suspended = False
    test.ctx['suspend_admin'] = suspend
    def runtime(gate):
        test.assertIs(gate, test.closure.gate)
        test.assertTrue(test.admin_suspended)
        test.assertTrue(test.registry.valid_proof(test.seal))
        return test.catalog_wire
    patched = patch.object(producer.NativeRuntime, 'disposable', side_effect=runtime)
    patched.start(); test.addCleanup(patched.stop)


class Tests(unittest.TestCase):
    stop_server = shared.Tests.stop_server
    publish = shared.Tests.publish

    def setUp(self):
        shared.Tests.setUp(self)
        self.closure = composition.Closure(self.gate, self.publish)
        self.assertIs(module._GUARDS[self.closure], self.closure.pre_fixture)
        self.auth._finalizer = self.closure.finalize
        self.primary = RuntimeError('original body failure')
        self.binding = {'status': 'MOCK_WIRING_NOT_MAIN_INTEGRATION'}

    def run_observer(self, *, mock_wiring=True):
        with patch.object(af, 'RealBackend', return_value=self.backend) as constructor:
            try:
                if mock_wiring:
                    with patch.object(module, 'wiring', return_value=self.binding):
                        return module.observe(self.closure, self.ctx, self.auth, self.seal, primary=self.primary)
                return module.observe(self.closure, self.ctx, self.auth, self.seal, primary=self.primary)
            finally:
                self.connections = constructor.call_count

    def report(self):
        return self.saved[module.PREFIX + '.json']

    def rejected(self, *, connected=0, mock_wiring=True):
        with self.assertRaises(RuntimeError) as caught:
            self.run_observer(mock_wiring=mock_wiring)
        self.assertIs(caught.exception, self.primary)
        self.assertEqual(self.connections, connected)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(len(self.backend.users), 3)
        self.assertEqual(len(self.backend.sessions), 3)

    def test_readonly_six_prepaid_no_deletes_no_cleanup_claim(self):
        original = {p: p.read_bytes() for p in self.root.rglob('*.json')}
        result = self.run_observer()
        self.assertEqual(result['checkpoint'], 'SCOPED_READ_ONLY_PREFLIGHT_CONFIRMED_NOT_CLEANUP')
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['native_dispatches'], 6)
        self.assertEqual(result['prepaid_consumed'], 6)
        self.assertEqual(len(self.native_keys), 6)
        self.assertEqual(result['deletes'], 0)
        self.assertFalse(result['original_claims_released'])
        self.assertFalse(result['full_auth_cleanup_proven'])
        self.assertEqual(len(self.backend.users), 3)
        self.assertEqual(len(self.backend.sessions), 3)
        self.assertEqual(self.server.count, 9)
        self.assertTrue(all(p.read_bytes() == raw for p, raw in original.items()))
        with self.assertRaises(Exception): self.closure.pre_fixture.before_bootstrap_write()

    def test_failed_scope_baseline_started_is_not_mutation(self):
        self.closure.started = True
        self.closure.scope = object()
        self.assertEqual(self.run_observer()['prepaid_consumed'], 6)

    def test_current_unintegrated_gate_fails_before_observer(self):
        # Real verifier, deliberately no mocked source proof. Main's integration
        # is pending; a SimpleNamespace gate is never a source-bound capability.
        self.rejected(mock_wiring=False)
        self.assertEqual(self.report()['prepaid_consumed'], 0)

    def test_false_boolean_without_registered_guard_not_proof(self):
        del module._GUARDS[self.closure]
        self.closure.fixture_mutation_started = False
        self.rejected()

    def test_actual_gate_missing_candidate_registration_blocks(self):
        import admission_ci
        gate = admission_ci.Gate.__new__(admission_ci.Gate)
        gate.out, gate.container, gate.save = self.root, self.gate.container, self.publish
        gate.sources = pathlib.Path(module.__file__).resolve().parents[3]
        self.closure.gate = gate
        self.publish('candidate.json', {'sources': {}})
        with patch.dict(os.environ, {'GITHUB_WORKSPACE': str(gate.sources)}):
            self.rejected(mock_wiring=False)
        self.assertEqual(self.report()['secondary_errors'][0]['class'], 'ModuleBindingError')

    def test_disposable_boundary_preserves_original(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'}):
            self.rejected()
        self.assertEqual(self.report()['prepaid_consumed'], 0)

    def test_guard_from_other_closure_not_accepted(self):
        other = composition.Closure(self.gate, self.publish)
        self.closure.pre_fixture = other.pre_fixture
        self.rejected()

    def test_pre_dispatch_guard_remembers_even_if_public_flag_reset(self):
        self.closure.pre_fixture.before_bootstrap_write()
        self.closure.fixture_mutation_started = False
        self.rejected()

    def test_runtime_handed_out_is_not_adopted(self):
        self.closure.tracked = object()
        self.rejected()

    def test_foreign_auth_finalizer_not_adopted(self):
        self.auth._finalizer = lambda *_: None
        self.rejected()

    def test_fake_seal_not_adopted(self):
        self.seal = object()
        self.rejected()

    def test_incomplete_bootstrap_not_adopted(self):
        del self.ctx['accounts']['b']
        self.rejected()

    def test_changed_email_not_adopted(self):
        self.ctx['accounts']['a']['email'] = 'unknown@example.invalid'
        self.rejected()

    def test_unknown_session_not_adopted(self):
        self.backend.sessions['unexpected-session'] = self.ctx['claims']['a']['sub']
        with self.assertRaises(RuntimeError) as caught:
            self.run_observer()
        self.assertIs(caught.exception, self.primary)
        self.assertEqual(self.report()['prepaid_consumed'], 3)
        self.assertEqual(self.server.count, 9)

    def test_fk_before_nonzero_blocks(self):
        self.fk_counts['identities'] = 1
        self.rejected(connected=1)
        self.assertEqual(self.report()['prepaid_consumed'], 2)

    def test_fk_after_nonzero_blocks_without_deletion(self):
        original = self.backend.snapshot
        def snapshot(*args):
            result = original(*args)
            if args[0] == 'b@example.invalid': self.fk_counts['operators'] = 1
            return result
        self.backend.snapshot = snapshot
        self.rejected(connected=1)
        self.assertEqual(self.report()['prepaid_consumed'], 6)

    def test_observer_failure_preserves_primary_no_refund(self):
        self.backend.execute = lambda *_: (_ for _ in ()).throw(OSError('SQL unknown'))
        self.rejected(connected=1)
        self.assertEqual(self.report()['original_error_class'], 'RuntimeError')
        self.assertEqual(self.report()['secondary_errors'][0]['class'], 'OSError')
        self.assertEqual(self.report()['prepaid_consumed'], 1)

    def test_save_failure_preserves_primary(self):
        self.gate.save = lambda *_: (_ for _ in ()).throw(OSError('save failure'))
        self.rejected(connected=1)

    def test_receipt_has_no_raw_account_or_session_data(self):
        text = json.dumps(self.run_observer())
        for role in self.ctx['accounts']:
            for key in ('email', 'password'):
                self.assertNotIn(self.ctx['accounts'][role][key], text)
            for key in ('sub', 'session_id'):
                self.assertNotIn(self.ctx['claims'][role][key], text)
        self.assertNotIn('LOCAL_TEST_ADMIN', text)

    def test_source_changes_during_observation_block(self):
        original = self.backend.snapshot
        def snapshot(*args):
            result = original(*args)
            self.binding = {'status': 'CHANGED'}
            return result
        self.backend.snapshot = snapshot
        with patch.object(module, 'wiring', side_effect=lambda *_: copy.deepcopy(self.binding)):
            self.rejected(connected=1, mock_wiring=False)

    def test_duplicate_observation_does_not_replay(self):
        self.run_observer()
        self.rejected()
        self.assertEqual(len(self.native_keys), 6)

    def test_mutation_thread_rejected(self):
        errors = []
        def attempt():
            try: self.closure.pre_fixture.before_bootstrap_write()
            except BaseException as error: errors.append(error)
        worker = threading.Thread(target=attempt)
        worker.start(); worker.join()
        self.assertEqual(len(errors), 1)
        self.assertFalse(self.closure.pre_fixture._mutation)

    def test_registration_after_scope_start_rejected(self):
        other = composition.Closure(self.gate, self.publish)
        other.started = True
        other.fixture_mutation_started = False
        with self.assertRaises(Exception): module.Guard(other)


class CleanupTests(unittest.TestCase):
    stop_server = Tests.stop_server
    publish = Tests.publish

    def setUp(self):
        Tests.setUp(self)
        self.primary = FileNotFoundError('PRIVATE_ORIGINAL_MATRIX_PATH')
        catalog_fixture(self)
        self.binding['candidate_manifest_sha256'] = module.durable.sha((self.root / 'candidate.json').read_bytes())

    def run_cleanup(self, *, mock_wiring=True):
        with patch.object(af, 'RealBackend', return_value=self.backend) as constructor:
            try:
                try:
                    raise self.primary
                except FileNotFoundError:
                    if mock_wiring:
                        with patch.object(module, 'wiring', return_value=self.binding):
                            return module.cleanup(self.closure, self.ctx, self.auth, self.seal,
                                primary=self.primary, delete_costs=self.costs)
                    return module.cleanup(self.closure, self.ctx, self.auth, self.seal,
                        primary=self.primary, delete_costs=self.costs)
            finally:
                self.connections = constructor.call_count

    def rejected(self, *, mock_wiring=True):
        with self.assertRaises(FileNotFoundError) as caught:
            self.run_cleanup(mock_wiring=mock_wiring)
        self.assertIs(caught.exception, self.primary)

    def report(self):
        return self.saved['auth-parent-finalizer.json']

    def test_same_engine_three_real_http_deletes_402_scoped_zero(self):
        result = self.run_cleanup()
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertEqual(result['prerequisite_kind'], 'LIVE_PRE_FIXTURE_NO_DISPATCH')
        self.assertEqual(result['original_component_error_class'], 'FileNotFoundError')
        self.assertEqual(result['prepaid_consumed'], 402)
        self.assertEqual(result['pre_fixture_accounting']['local_diagnostic_reserved_units'], 412)
        self.assertEqual(result['pre_fixture_accounting']['local_diagnostic_prepaid_consumed'], 412)
        self.assertEqual(len(self.catalog_wire.calls), 10)
        self.assertEqual(self.suspensions, 1)
        self.assertFalse(self.admin_suspended)
        self.assertEqual(result['native_dispatches'], 18)
        self.assertEqual(len(self.native_keys), 18)
        self.assertEqual(result['http_attempts'], 3)
        self.assertEqual(self.server.count, 12)
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.backend.sessions, {})
        self.assertFalse(result['full_auth_cleanup_proven'])
        self.assertFalse(result['original_claims_released'])
        self.assertFalse(result['original_commit_reclassified'])
        self.assertFalse(result['global_auth_zero_claim'])
        self.assertNotIn('PRIVATE_ORIGINAL_MATRIX_PATH', json.dumps(self.saved))
        self.assertFalse((self.root / 'fixture-parent-closure-private').exists())
        self.assertFalse((self.root / 'auth-pre-fixture-closure-private').exists())
        with self.assertRaises(Exception): self.closure.pre_fixture.before_bootstrap_write()

    def test_scope_started_but_no_runtime_cannot_retry_or_cleanup(self):
        self.closure.started = True
        self.rejected()
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.catalog_wire.calls, [])
        self.assertEqual(self.server.count, 9)

    def test_truncated_admin_delete_preserves_original_and_unknown(self):
        self.server.truncate_at = 10
        self.rejected()
        report = self.report()
        self.assertEqual(report['primary_failure']['class'], 'UnknownOutcome')
        self.assertEqual(report['original_component_error_class'], 'FileNotFoundError')
        self.assertEqual(self.server.count, 10)
        self.assertEqual(len(self.backend.users), 2)
        self.assertEqual(len(self.backend.sessions), 2)
        self.assertFalse(report['deletes']['a']['acknowledged'])
        self.assertFalse(report['original_claims_released'])
        self.assertEqual(report['refunds'], 0)
        self.assertGreaterEqual(report['prepaid_consumed'], 128)

    def test_unknown_delete_then_observer_failure_keeps_both(self):
        self.server.truncate_at = 10
        original = self.backend.stats
        calls = []
        def stats():
            calls.append(1)
            if len(calls) == 2: raise OSError('PRIVATE_SECONDARY')
            return original()
        self.backend.stats = stats
        self.rejected()
        self.assertEqual(self.report()['primary_failure']['class'], 'UnknownOutcome')
        self.assertTrue(any(e['class'] == 'OSError' for e in self.report()['secondary_errors']))

    def test_residual_fk_stops_before_any_delete(self):
        self.fk_counts['identities'] = 1
        self.rejected()
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.report()['native_dispatches'], 2)

    def test_unknown_session_stops_all_deletes(self):
        self.backend.sessions['extra'] = self.ctx['claims']['b']['sub']
        self.rejected()
        self.assertEqual(self.server.count, 9)

    def test_partial_bootstrap_stops_before_connection(self):
        del self.auth._owners['b']
        self.rejected()
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)

    def test_fixture_dispatch_attempt_stops_before_connection(self):
        self.closure.pre_fixture.before_bootstrap_write()
        self.rejected()
        self.assertEqual(self.connections, 0)

    def test_source_gate_is_not_bypassed(self):
        self.rejected(mock_wiring=False)
        self.assertEqual(self.connections, 0)

    def test_changed_prerequisite_record_prevents_first_delete(self):
        original = self.backend.snapshot
        def snapshot(*args):
            result = original(*args)
            if args[0] == 'b@example.invalid':
                (self.root / 'auth-pre-fixture-prerequisite-private/intent.json').write_bytes(b'{}\n')
            return result
        self.backend.snapshot = snapshot
        self.rejected()
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.report()['http_attempts'], 0)

    def test_parent_cost_overrun_no_second_delete(self):
        self.backend.difference = lambda *_: {'commands': 129}
        self.rejected()
        self.assertEqual(self.server.count, 10)
        self.assertEqual(self.report()['http_attempts'], 1)

    def test_no_fabricated_primary_outside_active_exception(self):
        with patch.object(module, 'wiring', return_value=self.binding), patch.object(af, 'RealBackend') as backend:
            with self.assertRaises(FileNotFoundError) as caught:
                module.cleanup(self.closure, self.ctx, self.auth, self.seal,
                    primary=self.primary, delete_costs=self.costs)
            self.assertIs(caught.exception, self.primary)
            backend.assert_not_called()

    def test_no_replay_after_success(self):
        self.run_cleanup()
        self.rejected()
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 12)

    def test_publication_format_is_not_assumed_canonical(self):
        def pretty(name, value):
            with (self.root / name).open('x') as stream:
                json.dump(value, stream, indent=2)
            self.saved[name] = copy.deepcopy(value)
        self.gate.save = pretty
        self.assertEqual(self.run_cleanup()['http_attempts'], 3)

    def test_publication_corruption_blocks_before_connection(self):
        def corrupt(name, value):
            self.publish(name, {} if name.endswith('-index.json') else value)
        self.gate.save = corrupt
        self.rejected()
        self.assertEqual(self.connections, 0)

    def test_receipt_failure_does_not_replace_original(self):
        self.gate.save = lambda *_: (_ for _ in ()).throw(OSError('PRIVATE_STORAGE_ERROR'))
        self.rejected()
        self.assertEqual(self.connections, 0)
        self.assertTrue(any('secondary_pre_fixture_receipt:OSError' == n for n in self.primary.__notes__))


class CatalogAttestationTests(unittest.TestCase):
    stop_server = Tests.stop_server
    publish = Tests.publish
    setUp = CleanupTests.setUp
    run_cleanup = CleanupTests.run_cleanup
    rejected = CleanupTests.rejected
    report = CleanupTests.report

    def assert_no_parent_deletes(self):
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(len(self.backend.users), 3)
        self.assertEqual(len(self.backend.sessions), 3)
        self.assertFalse(self.admin_suspended)
        self.assertIs(self.gate.save.__self__, self)

    def test_actual_previously_failed_scope_is_not_retried(self):
        self.catalog_wire.data['triggers'][0]['name'] = 'unregistered_trigger'
        scope = producer.Scope(self.gate)
        self.closure.scope, self.closure.started = scope, True
        with self.ctx['suspend_admin']():
            with self.assertRaises(Exception): scope.before_bootstrap()
        original = {p: p.read_bytes() for p in self.root.rglob('*.json')}
        calls = list(self.catalog_wire.calls)
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.catalog_wire.calls, calls)
        self.assertTrue(all(p.read_bytes() == raw for p, raw in original.items()))
        self.assertFalse(any(p.name.startswith('auth-pre-fixture-scope-') for p in self.root.iterdir()))

    def test_existing_scope_even_without_started_flag_is_refused(self):
        self.closure.scope = producer.Scope(self.gate)
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.catalog_wire.calls, [])

    def test_actual_scope_rejects_unknown_recursive_auth_trigger(self):
        trigger = next(x for x in self.catalog_wire.data['triggers'] if x['schema'] == 'auth')
        trigger['function_name'] = 'unknown_auth_delete_side_effect'
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(len(self.catalog_wire.calls), 10)

    def test_actual_scope_rejects_changed_fk(self):
        self.catalog_wire.data['fks'][0]['on_delete'] = 'c'
        self.rejected()
        self.assert_no_parent_deletes()

    def test_actual_scope_rejects_extra_auth_write_grant(self):
        self.catalog_wire.data['privileges'][0]['direct_write'] = True
        self.rejected()
        self.assert_no_parent_deletes()

    def test_actual_scope_rejects_changed_function_body(self):
        self.catalog_wire.data['functions'][0]['body_sha256'] = '0' * 64
        self.rejected()
        self.assert_no_parent_deletes()

    def test_unknown_catalog_query_rolls_back_and_keeps_exact_prepaid_prefix(self):
        self.catalog_wire.failure = 'triggers'
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.catalog_wire.calls[-1], 'ROLLBACK')
        result = self.saved['auth-pre-fixture-cleanup-failure.json']
        self.assertEqual(result['additional_catalog_admitted_attempts'], len(self.catalog_wire.calls))
        self.assertEqual(result['cleanup_error_class'], 'TimeoutError')
        self.assertEqual(result['original_error_class'], 'FileNotFoundError')
        self.assertEqual(result['refunds'], 0)

    def test_lost_catalog_begin_charges_rollback_without_delete(self):
        self.catalog_wire.failure = 'BEGIN TRANSACTION READ ONLY'
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.catalog_wire.calls, ['BEGIN TRANSACTION READ ONLY', 'ROLLBACK'])
        self.assertEqual(self.saved['auth-pre-fixture-cleanup-failure.json']['additional_catalog_admitted_attempts'], 2)

    def test_catalog_rollback_unknown_cannot_attest(self):
        self.catalog_wire.failure = 'ROLLBACK'
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.saved['auth-pre-fixture-scope-before-result.json']['status'], 'NO_GO')

    def test_caller_dict_cannot_replace_actual_scope_execution(self):
        with patch.object(producer.Scope, 'before_bootstrap', return_value={'status':'SCOPE_METADATA_CONFIRMED_NOT_A_BARRIER'}):
            self.rejected()
        self.assert_no_parent_deletes()

    def test_charge_save_corruption_retains_prepaid_units_and_blocks_dispatch(self):
        def corrupt(name, value):
            self.publish(name, {} if name == 'auth-pre-fixture-scope-before-charge-003.json' else value)
        self.gate.save = corrupt
        self.rejected()
        self.assertEqual(self.connections, 0)
        self.assertEqual(self.server.count, 9)
        self.assertEqual(len(self.catalog_wire.calls), 2)
        self.assertEqual(self.saved['auth-pre-fixture-cleanup-failure.json']['additional_catalog_admitted_attempts'], 3)
        self.assertIs(self.gate.save, corrupt)

    def test_original_scope_record_mutation_blocks_first_delete(self):
        original = self.backend.snapshot
        def snapshot(*args):
            value = original(*args)
            if args[0] == 'b@example.invalid':
                (self.root / 'auth-pre-fixture-scope-before-charge-001.json').write_bytes(b'{}\n')
            return value
        self.backend.snapshot = snapshot
        self.rejected()
        self.assertEqual(self.server.count, 9)
        self.assertEqual(self.report()['http_attempts'], 0)

    def test_failed_admin_suspension_no_scope_or_delete(self):
        @contextlib.contextmanager
        def failure():
            raise OSError('private admin close failure')
            yield
        self.ctx['suspend_admin'] = failure
        self.rejected()
        self.assert_no_parent_deletes()
        self.assertEqual(self.catalog_wire.calls, [])

    def test_success_binds_all_twelve_prefixed_records_and_source_contract(self):
        result = self.run_cleanup()
        names = [n for n in self.saved if n.startswith('auth-pre-fixture-scope-before-')]
        self.assertEqual(len(names), 12)
        self.assertFalse(any(n.startswith('fixture-producer-scope-') for n in self.saved))
        binding = json.loads((self.root / 'auth-parent-finalizer-private/pre-fixture-binding.json').read_bytes())
        for name in names:
            self.assertEqual(binding['original_hashes'][name], module.durable.sha((self.root/name).read_bytes()))
        self.assertEqual(result['pre_fixture_accounting']['local_diagnostic_prepaid_consumed'], 412)
        self.assertEqual(result['pre_fixture_accounting']['additional_catalog_admitted_attempts'], 10)
        self.assertFalse(self.saved['auth-pre-fixture-scope-before-result.json']['global_auth_barrier'])


class ActualWiringTests(unittest.TestCase):
    stop_server = Tests.stop_server
    publish = Tests.publish

    def setUp(self):
        import admission_ci
        shared.Tests.setUp(self)
        gate = admission_ci.Gate.__new__(admission_ci.Gate)
        gate.out, gate.container, gate.save = self.root, self.gate.container, self.publish
        gate.sources = pathlib.Path(module.__file__).resolve().parents[3]
        self.gate = gate
        self.closure = composition.Closure(gate, self.publish)
        self.auth._finalizer = self.closure.finalize
        self.primary = FileNotFoundError('PRIVATE_ORIGINAL_MATRIX_PATH')
        catalog_fixture(self)

    def test_actual_loaded_compositor_source_and_finally_cleanup(self):
        # Real source binding, actual callback, registry and localhost HTTP.
        # Only SQL is a test double. No application Gate.run or DB is invoked.
        previous = lambda *_: self.fail('prefixed save must be suspended')
        self.gate.save = previous
        with patch.object(af, 'RealBackend', return_value=self.backend):
            with self.assertRaises(FileNotFoundError) as caught:
                try:
                    raise self.primary
                finally:
                    result = self.auth.finalize(self.ctx, self.seal)
        self.assertIs(caught.exception, self.primary)
        self.assertIs(self.gate.save, previous)
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED')
        self.assertEqual(result['original_component_error_class'], 'FileNotFoundError')
        self.assertEqual(result['prepaid_consumed'], 402)
        self.assertEqual(len(self.native_keys), 18)
        self.assertEqual(self.server.count, 12)
        self.assertEqual(self.backend.users, {})
        self.assertEqual(self.backend.sessions, {})
        intent = json.loads((self.root / 'auth-pre-fixture-prerequisite-private/intent.json').read_bytes())
        self.assertEqual(intent['source_binding']['status'], 'SELECTED_MODULE_SOURCE_BINDING_PASS')
        self.assertFalse(result['original_claims_released'])
        self.assertFalse(result['full_chain_admission'])
        with self.assertRaises(Exception): self.closure.before_bootstrap_write()

    def test_actual_hook_prevents_pre_fixture_adoption(self):
        self.closure.before_bootstrap_write()
        with patch.object(af, 'RealBackend') as backend:
            with self.assertRaises(FileNotFoundError) as caught:
                try: raise self.primary
                except FileNotFoundError:
                    module.cleanup(self.closure, self.ctx, self.auth, self.seal,
                        primary=self.primary, delete_costs=self.costs)
            self.assertIs(caught.exception, self.primary)
            backend.assert_not_called()
        self.assertEqual(self.server.count, 9)

    def test_actual_candidate_hash_change_blocks_before_connection(self):
        path = self.root / 'candidate.json'
        manifest = json.loads(path.read_bytes())
        key = next(k for k in manifest['sources'] if k.endswith('/auth_pre_fixture_closure.py'))
        manifest['sources'][key] = '0' * 64
        path.write_bytes(module.durable.raw(manifest))
        with patch.object(af, 'RealBackend') as backend:
            with self.assertRaises(FileNotFoundError) as caught:
                try: raise self.primary
                except FileNotFoundError:
                    module.cleanup(self.closure, self.ctx, self.auth, self.seal,
                        primary=self.primary, delete_costs=self.costs)
            self.assertIs(caught.exception, self.primary)
            backend.assert_not_called()
        self.assertEqual(self.server.count, 9)

    def test_actual_gate_loaded_as_script_module_not_second_import_class(self):
        import admission_ci
        name = 'pre_fixture_test_script_entry'
        spec = importlib.util.spec_from_file_location(name, admission_ci.__file__)
        entry = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {name: entry}):
            spec.loader.exec_module(entry)
            gate = entry.Gate.__new__(entry.Gate)
            gate.out, gate.sources, gate.container, gate.save = (
                self.gate.out, self.gate.sources, self.gate.container, self.publish)
            self.assertIsNot(type(gate), admission_ci.Gate)
            self.closure = composition.Closure(gate, self.publish)
            self.auth._finalizer = self.closure.finalize
            with patch.object(af, 'RealBackend', return_value=self.backend):
                try: raise self.primary
                except FileNotFoundError:
                    result = self.auth.finalize(self.ctx, self.seal)
            self.assertEqual(result['http_attempts'], 3)
            self.assertEqual(result['prepaid_consumed'], 402)


class WiringContractTests(unittest.TestCase):
    INIT = ('def __init__(self):\n'
            '    self.fixture_mutation_started = False\n'
            '    self.pre_fixture = auth_pre_fixture_closure.Guard(self)\n')
    HOOK = ('def before_bootstrap_write(self):\n'
            '    self.pre_fixture.before_bootstrap_write()\n'
            '    self.fixture_mutation_started = True\n')
    BODY = ('closure.before_bootstrap_write()\n'
            'admission_fixture_context.run(self, ctx, runtime=tracked)\n')

    def validate(self, init=None, hook=None, body=None):
        module._validate_wiring(ast.parse(init or self.INIT), ast.parse(hook or self.HOOK),
                                ast.parse(body or self.BODY))

    def test_exact_proposed_syntax_only_not_actual_integration(self):
        self.validate()

    def test_boolean_only_hook_rejected(self):
        with self.assertRaises(Exception):
            self.validate(hook='def before_bootstrap_write(self):\n    self.fixture_mutation_started = True\n')

    def test_guard_replaced_by_boolean_rejected(self):
        with self.assertRaises(Exception):
            self.validate(init=self.INIT.replace('auth_pre_fixture_closure.Guard(self)', 'True'))

    def test_unhooked_fixture_dispatch_rejected(self):
        with self.assertRaises(Exception):
            self.validate(body='admission_fixture_context.run(self, ctx, runtime=tracked)\n')

    def test_nonadjacent_hook_rejected(self):
        with self.assertRaises(Exception):
            self.validate(body=self.BODY.replace('admission_fixture_context.run', 'other()\nadmission_fixture_context.run'))

    def test_second_fixture_dispatch_rejected(self):
        with self.assertRaises(Exception): self.validate(body=self.BODY + self.BODY)

    def test_different_runtime_rejected(self):
        with self.assertRaises(Exception): self.validate(body=self.BODY.replace('runtime=tracked', 'runtime=other'))


if __name__ == '__main__':
    unittest.main()
