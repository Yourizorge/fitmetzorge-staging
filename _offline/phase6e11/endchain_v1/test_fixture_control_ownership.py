"""Offline negative-control ownership tests; no actual PG/GoTrue evidence."""
import ast
import copy
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import fixture_control_ownership as control
import fixture_parent_closure as parent
from admission_binding import NEW_RUN
from admission_journal import Journal
from fixture_cleanup_runtime import Blocked, Cleanup, Protocol, digest
from fixture_cleanup_runtime_ci import inserts
from fixture_cleanup_runtime_test import CONTEXT, row
from test_fixture_parent_closure import Runtime, IDS, ENV


class Tests(unittest.TestCase):
    def setUp(self):
        self.db = Runtime()
        self.events = []
        self.setup = Protocol(lambda event: self.events.append(copy.deepcopy(event)))
        self.cleanup = Cleanup(self.db, CONTEXT, self.db.save, lambda event: None)
        self.cleanup.prepare()
        self.intent = control.retain_context(self.cleanup, 'foreign_row', inserts(CONTEXT, IDS), IDS)
        self.negative = control.NegativeControl(self.cleanup, self.intent)
        self.rows = [row(table, n) for table, count in control.COUNTS.items() for n in range(1, count + 1)]
        self.db.rows = copy.deepcopy(self.rows)

    def execute_case(self):
        writer = self.db.connect()
        self.negative.capture(writer, self.setup.execute)
        writer.close()
        self.receipt = self.cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
        self.checked = self.negative.check_after_case(self.receipt, self.setup.execute)
        return control.validate_ownership(self.intent, self.negative.owned, self.checked,
                                          self.receipt, self.intent['actor_hashes'])

    def rejected_fixture(self):
        writer = self.db.connect()
        self.negative.capture(writer, self.setup.execute)
        writer.close()
        return self.cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)

    def assert_no_witness_or_retry(self, receipt):
        self.assertNotIn(self.cleanup.prefix+'parent-negative-checked.json', self.db.saved)
        before = len(self.db.calls)
        with self.assertRaisesRegex(Blocked, 'duplicate_check'):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(len(self.db.calls), before)
        self.assertLessEqual(self.negative.admitted_attempts, control.CONTROL_LIMIT)

    def test_separate_prewrite_intent_retains_exact_context_not_claimed_rows(self):
        self.assertEqual(self.intent['context'], CONTEXT)
        self.assertTrue(self.intent['before_writer_begin'])
        self.assertFalse(self.intent['row_ownership_proven'])
        self.assertEqual(len(self.intent['planned_writes']), 13)
        self.assertEqual(self.db.saved[self.cleanup.prefix+'parent-setup.json'], self.intent)
        self.assertEqual(self.cleanup.snapshots, [])

    def test_case_remains_foreign_and_new_evidence_costs_exactly_five_queries(self):
        owned = self.execute_case()
        self.assertEqual(self.receipt['status'], 'NO_GO')
        self.assertEqual(self.receipt['reason'], 'cleanup_unowned_or_changed_row')
        self.assertEqual(self.cleanup.snapshots, [])
        self.assertEqual(self.cleanup._rows, [])
        self.assertFalse(any(e['phase'].startswith('delete_') for e in self.receipt['protocol']))
        self.assertEqual(len(owned['rows']), 16)
        self.assertEqual(len(self.events), 5)
        self.assertEqual(self.checked['protocol_limit'], 5)
        self.assertEqual(self.checked['admitted_attempts'], 5)
        self.assertTrue(self.checked['unchanged'])
        self.assertFalse(self.checked['original_claim_promoted'])

    def test_exact_parent_cleanup_does_not_rewrite_case_ownership_or_claim(self):
        owned = self.execute_case()
        originals = copy.deepcopy(self.db.saved)
        cleanup = parent.NegativeControlClosure(self.db, CONTEXT, self.db.save, lambda event: None)
        cleanup.prepared, cleanup.snapshots = True, [owned]
        cleanup.prefix = 'distinct-parent-negative-'
        result = cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
        self.assertEqual(result['status'], 'COMPONENT_PASS')
        self.assertEqual(result['delete_count'], 16)
        self.assertEqual(self.db.rows, [])
        self.assertEqual(self.cleanup.snapshots, [])
        self.assertEqual(self.receipt['status'], 'NO_GO')
        self.assertTrue(all(self.db.saved[k] == v for k, v in originals.items()))

    def test_changed_or_missing_rows_before_parent_delete_block_entire_suffix(self):
        owned = self.execute_case()
        self.db.rows.pop()
        before = len(self.db.calls)
        cleanup = parent.NegativeControlClosure(self.db, CONTEXT, self.db.save, lambda event: None)
        cleanup.prepared, cleanup.snapshots, cleanup.prefix = True, [owned], 'distinct-parent-negative-'
        result = cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
        self.assertEqual(result['reason'], 'parent_negative_changed_before_delete')
        self.assertFalse(any('with removed as' in s for s in self.db.calls[before:]))
        self.assertFalse(result['deletion_proven'])

    def test_changed_control_during_case_cannot_get_parent_witness(self):
        self.negative.capture(self.db.connect(), self.setup.execute)
        receipt = self.cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
        self.db.rows[0] = dict(self.db.rows[0], xmin='42')
        with self.assertRaisesRegex(Blocked, 'changed_during_case'):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertNotIn(self.cleanup.prefix+'parent-negative-checked.json', self.db.saved)

    def test_additional_foreign_row_is_not_adopted_as_negative_control(self):
        self.negative.capture(self.db.connect(), self.setup.execute)
        self.db.rows.append(row('windows', 99))
        receipt = self.cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
        with self.assertRaisesRegex(Blocked, 'changed_during_case'):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.cleanup.snapshots, [])

    def test_capture_requires_all_rows_from_the_actual_writer_transaction(self):
        self.db.rows[0] = dict(self.db.rows[0], xmin='42')
        with self.assertRaisesRegex(Blocked, 'writer_ownership'):
            self.negative.capture(self.db.connect(), self.setup.execute)
        self.assertIsNone(self.negative.owned)
        self.assertEqual(self.cleanup.snapshots, [])

    def test_duplicate_capture_has_no_second_query(self):
        self.negative.capture(self.db.connect(), self.setup.execute)
        before = len(self.db.calls)
        with self.assertRaisesRegex(Blocked, 'duplicate_capture'):
            self.negative.capture(self.db.connect(), self.setup.execute)
        self.assertEqual(len(self.db.calls), before)

    def test_capture_storage_failure_never_gives_case_ownership(self):
        self.cleanup.save = lambda name, value: (_ for _ in ()).throw(OSError('test storage'))
        with self.assertRaises(OSError): self.negative.capture(self.db.connect(), self.setup.execute)
        self.assertIsNone(self.negative.owned)
        self.assertEqual(self.cleanup.snapshots, [])
        before = len(self.db.calls)
        with self.assertRaisesRegex(Blocked, 'duplicate_capture'):
            self.negative.capture(self.db.connect(), self.setup.execute)
        self.assertEqual(len(self.db.calls), before)
        self.assertEqual(self.negative.admitted_attempts, 1)

    def test_check_failure_rolls_back_in_finally_within_four_slots(self):
        receipt = self.rejected_fixture()
        self.db.fail = control.sql.CHECK
        with self.assertRaises(TimeoutError):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.negative.admitted_attempts, 4)
        self.assertEqual(self.db.calls[-1], 'ROLLBACK')
        self.assertTrue(self.db.connections[-1].closed)
        self.assert_no_witness_or_retry(receipt)

    def test_invalid_check_result_rolls_back_and_preserves_primary_error(self):
        receipt = self.rejected_fixture()
        def execute(connection, phase, text, args=()):
            result = self.setup.execute(connection, phase, text, args)
            return [] if text == control.sql.CHECK else result
        with self.assertRaisesRegex(Blocked, 'readonly_limits'):
            self.negative.check_after_case(receipt, execute)
        self.assertEqual(self.negative.admitted_attempts, 4)
        self.assertEqual(self.db.calls[-1], 'ROLLBACK')
        self.assert_no_witness_or_retry(receipt)

    def test_inventory_failure_consumes_reserved_rollback_fifth_slot(self):
        receipt = self.rejected_fixture()
        self.db.fail = "'rows',coalesce"
        with self.assertRaises(TimeoutError):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.negative.admitted_attempts, 5)
        self.assertEqual(self.db.calls[-1], 'ROLLBACK')
        self.assertTrue(self.db.connections[-1].closed)
        self.assert_no_witness_or_retry(receipt)

    def test_lost_begin_response_still_has_one_counted_rollback(self):
        receipt = self.rejected_fixture()
        connection = self.db.connect()
        original = connection.execute
        def lost_begin(text, args=None):
            value = original(text, args)
            if text.startswith('BEGIN'): raise ConnectionError('lost BEGIN response')
            return value
        with patch.object(self.db, 'connect', return_value=connection), patch.object(connection, 'execute', lost_begin), \
                patch.object(connection, 'close', wraps=connection.close) as close:
            with self.assertRaisesRegex(ConnectionError, 'lost BEGIN'):
                self.negative.check_after_case(receipt, self.setup.execute)
            close.assert_called_once_with()
        self.assertEqual(self.negative.admitted_attempts, 3)
        self.assertEqual(self.db.calls[-1], 'ROLLBACK')
        self.assertTrue(self.db.connections[-1].closed)
        self.assert_no_witness_or_retry(receipt)

    def test_rollback_failure_is_not_retried_and_never_writes_witness(self):
        receipt = self.rejected_fixture()
        self.db.fail = 'ROLLBACK'
        with self.assertRaises(TimeoutError):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.negative.admitted_attempts, 5)
        self.assertEqual(self.negative.rollback_error_class, 'TimeoutError')
        self.assertEqual(sum(e['phase'].endswith('_rollback') for e in self.events), 1)
        self.assertTrue(self.db.connections[-1].closed)
        self.assert_no_witness_or_retry(receipt)

    def test_primary_failure_survives_both_rollback_and_close_failures(self):
        receipt = self.rejected_fixture()
        connection = self.db.connect()
        original = connection.execute
        primary = ValueError('primary CHECK failure')
        def failed(text, args=None):
            if text == control.sql.CHECK: raise primary
            if text == 'ROLLBACK': raise ConnectionError('rollback lost')
            return original(text, args)
        with patch.object(self.db, 'connect', return_value=connection), patch.object(connection, 'execute', failed), \
                patch.object(connection, 'close', side_effect=OSError('close lost')):
            with self.assertRaises(ValueError) as caught:
                self.negative.check_after_case(receipt, self.setup.execute)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.negative.admitted_attempts, 4)
        self.assertEqual(self.negative.rollback_error_class, 'ConnectionError')
        self.assertEqual(self.negative.close_error_class, 'OSError')
        self.assertEqual(len(primary.__notes__), 2)
        self.assert_no_witness_or_retry(receipt)

    def test_witness_storage_failure_occurs_after_counted_rollback_and_close(self):
        receipt = self.rejected_fixture()
        def fail_save(name, value):
            self.assertEqual(self.db.calls[-1], 'ROLLBACK')
            self.assertTrue(self.db.connections[-1].closed)
            raise OSError('witness storage')
        self.cleanup.save = fail_save
        with self.assertRaisesRegex(OSError, 'witness storage'):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.negative.admitted_attempts, 5)
        self.assert_no_witness_or_retry(receipt)

    def test_pre_dispatch_charge_failure_never_emits_check_and_reserves_rollback(self):
        receipt = self.rejected_fixture()
        def charge(event):
            if event['phase'].endswith('_limits'): raise OSError('charge storage')
            self.events.append(copy.deepcopy(event))
        self.setup.charge = charge
        before = len(self.db.calls)
        with self.assertRaisesRegex(OSError, 'charge storage'):
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertEqual(self.db.calls[before:], ['BEGIN TRANSACTION READ ONLY', 'ROLLBACK'])
        self.assertEqual(self.negative.admitted_attempts, 4)
        self.assert_no_witness_or_retry(receipt)

    def test_poisoned_storage_blocks_rollback_dispatch_without_masking_primary(self):
        receipt = self.rejected_fixture()
        primary = OSError('poisoned charge store')
        def charge(event):
            if not event['phase'].endswith('_begin'): raise primary
        self.setup.charge = charge
        before = len(self.db.calls)
        with self.assertRaises(OSError) as caught:
            self.negative.check_after_case(receipt, self.setup.execute)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.db.calls[before:], ['BEGIN TRANSACTION READ ONLY'])
        self.assertEqual(self.negative.admitted_attempts, 4)
        self.assertEqual(self.negative.rollback_error_class, 'OSError')
        self.assertTrue(self.db.connections[-1].closed)
        self.assert_no_witness_or_retry(receipt)

    def test_partial_remaining_cap_refuses_before_connect_or_begin(self):
        receipt = self.rejected_fixture()
        self.negative.admitted_attempts = 2
        before = len(self.db.calls)
        with patch.object(self.db, 'connect') as connect:
            with self.assertRaisesRegex(Blocked, 'protocol_limit'):
                self.negative.check_after_case(receipt, self.setup.execute)
            connect.assert_not_called()
        self.assertEqual(len(self.db.calls), before)
        self.assertEqual(self.negative.admitted_attempts, 2)
        self.assert_no_witness_or_retry(receipt)

    def test_last_slot_is_rollback_only_and_sixth_dispatch_is_refused(self):
        self.negative.admitted_attempts = 4
        emitted = []
        def execute(connection, phase, text, args): emitted.append(text)
        with self.assertRaisesRegex(Blocked, 'protocol_limit'):
            self.negative._execute(execute, None, 'inventory', control.sql.INVENTORY)
        self.assertEqual(emitted, [])
        self.negative._execute(execute, None, 'rollback', 'ROLLBACK', rollback=True)
        self.assertEqual(self.negative.admitted_attempts, 5)
        with self.assertRaisesRegex(Blocked, 'protocol_limit'):
            self.negative._execute(execute, None, 'rollback', 'ROLLBACK', rollback=True)
        self.assertEqual(emitted, ['ROLLBACK'])

    def test_local_and_durable_charges_precede_every_dispatch(self):
        admitted = []
        def charge(event):
            admitted.append(self.negative.admitted_attempts)
            self.assertEqual(self.negative.admitted_attempts, len(admitted))
            self.assertLessEqual(len(admitted), 5)
            self.events.append(copy.deepcopy(event))
        self.setup.charge = charge
        self.execute_case()
        self.assertEqual(admitted, [1, 2, 3, 4, 5])

    def test_planned_or_changed_case_success_cannot_be_promoted_into_valid_control(self):
        self.execute_case()
        changed = copy.deepcopy(self.receipt); changed['status'] = 'COMPONENT_PASS'
        before = len(self.db.calls)
        with self.assertRaisesRegex(Blocked, 'must_still_reject'):
            self.negative.check_after_case(changed, self.setup.execute)
        self.assertEqual(len(self.db.calls), before)

    def test_wrong_actor_intent_or_changed_ownership_reference_rejected(self):
        self.execute_case()
        with self.assertRaisesRegex(Blocked, 'intent_binding'):
            control.validate_ownership(self.intent, self.negative.owned, self.checked, self.receipt, {})
        changed = copy.deepcopy(self.checked); changed['ownership_sha256'] = '0'*64
        with self.assertRaisesRegex(Blocked, 'unchanged_proof'):
            control.validate_ownership(self.intent, self.negative.owned, changed,
                                       self.receipt, self.intent['actor_hashes'])

    def test_case_without_confirmed_inventory_or_rollback_is_not_cleanup_authority(self):
        self.execute_case()
        for phase in ('inventory', 'rollback'):
            receipt = copy.deepcopy(self.receipt)
            receipt['protocol'] = [e for e in receipt['protocol'] if e['phase'] != phase]
            with self.assertRaisesRegex(Blocked, 'observation_missing'):
                control.rejected_case(receipt)

    def test_wrong_scope_intent_cannot_capture_a_different_control(self):
        intent = copy.deepcopy(self.intent)
        intent['context']['a'] = '78000000-0000-4000-8000-000000000099'
        with self.assertRaisesRegex(Blocked, 'intent_required'):
            control.NegativeControl(self.cleanup, intent)

    def test_prewrite_intent_storage_failure_stops_before_any_new_dispatch(self):
        cleanup = Cleanup(self.db, CONTEXT, self.db.save, lambda event: None)
        cleanup.prepared = True
        cleanup.save = lambda name, value: (_ for _ in ()).throw(OSError('test intent storage'))
        before = len(self.db.calls)
        with self.assertRaises(OSError):
            control.retain_context(cleanup, 'foreign_row', inserts(CONTEXT, IDS), IDS)
        self.assertEqual(len(self.db.calls), before)

    def test_source_harness_intent_precedes_writer_and_capture_precedes_commit(self):
        path = pathlib.Path(__file__).with_name('fixture_cleanup_runtime_ci.py')
        tree = ast.parse(path.read_text())
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        calls = [n for n in ast.walk(run) if isinstance(n, ast.Call)]
        intent = next(n for n in calls if ast.unparse(n.func) == 'retain_context')
        capture = next(n for n in calls if ast.unparse(n.func) == 'negative.capture')
        begin = next(n for n in calls if ast.unparse(n.func) == 'execute' and len(n.args) > 2
                     and isinstance(n.args[2], ast.Constant) and n.args[2].value == 'BEGIN')
        commit = next(n for n in calls if ast.unparse(n.func) == 'execute'
                      and len(n.args) > 2 and isinstance(n.args[2], ast.Constant)
                      and n.args[2].value == 'COMMIT' and ast.unparse(n.args[0]) == 'writer')
        self.assertLess(intent.lineno, begin.lineno)
        self.assertLess(begin.lineno, capture.lineno)
        self.assertLess(capture.lineno, commit.lineno)
        self.assertIn('gate.fixture_parent_contexts[cleanup.case] = copy.deepcopy(context)', path.read_text())

    def test_real_journal_parent_api_resolves_retained_context_and_keeps_original_no_go(self):
        self.execute_case()
        with tempfile.TemporaryDirectory(prefix='fmz-negative-parent-') as tmp:
            out = pathlib.Path(tmp).resolve()
            def publish(name, value):
                with (out/name).open('xb') as stream:
                    stream.write((json.dumps(value, sort_keys=True)+'\n').encode())
                    stream.flush(); os.fsync(stream.fileno())
            journal = Journal(out/'admission-fixture-private-journal', publish, 'admission-fixture-journal')
            for name, value in self.db.saved.items(): journal.save(name, value)
            detail = {'status': 'COMPONENT_PASS', 'preparation_run': NEW_RUN, 'cases': [
                {'case': 'foreign_row', 'fixture_case': CONTEXT['window'], 'expectation_pass': True,
                 'receipt': self.receipt}]}
            journal.save('fixture-cleanup-component-detail.json', detail); journal.seal()
            original_hashes = {p: parent.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
            bootstrap = {'status': 'DISPOSABLE_BOOTSTRAP_PASS', 'registered_accounts': 3,
                'existing_rows_overwritten': False, 'commit_confirmed': True, 'after_registry_confirmed': True,
                'before': {'identities': 0, 'operators': 0}, 'actor_hashes': self.intent['actor_hashes']}
            publish('admission-fixture-bootstrap.json', bootstrap)
            publish('terminal-unit-proof.json', {'unit_only': True})
            terminal = {'preparation_run': NEW_RUN, 'actor_hashes': self.intent['actor_hashes'],
                'fixture_case_ids': [CONTEXT['window']], 'worker_joined': True, 'writers_closed': True,
                'mint_barrier': True, 'evidence_refs': [{'path': 'terminal-unit-proof.json',
                    'sha256': parent.sha((out/'terminal-unit-proof.json').read_bytes())}]}
            publish('terminal.json', terminal)
            gate = types.SimpleNamespace(out=out, save=publish, fixture_cleanup_ids=IDS,
                                         container='supabase_db_fmz-db41-ci')
            with patch.dict(os.environ, ENV), patch.object(parent.NativeRuntime, 'disposable', return_value=self.db):
                result = parent.run(gate, barrier={'path': 'terminal.json',
                                    'sha256': parent.sha((out/'terminal.json').read_bytes())})
            self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_CLOSURE_CONFIRMED')
            self.assertEqual(result['status'], 'NO_GO')
            self.assertFalse(result['original_claims_released'])
            self.assertEqual(result['protocol_attempts'], 33)
            self.assertTrue(all(parent.sha(p.read_bytes()) == h for p, h in original_hashes.items()))
            self.assertEqual(self.db.rows, [])
            self.assertEqual(self.db.registry, {'identities': [], 'operators': []})


if __name__ == '__main__': unittest.main()
