"""C10: real preflight and meter with memory-only driver faults; no hosted IO."""
import copy
import json
import types
import unittest
from unittest.mock import Mock, patch

import lifecycle_gates as gates
from integral_stream import GUARD
from metered_composition import MeteredComposition, capacity
from runtime_budget import BudgetStop


class PreflightFailureTests(unittest.TestCase):
    def make(self, *, fail_at=None, rollback_error=False, close_error=False,
             save_error=False, connect_error=False, invalid_identity=False,
             environment='disposable_ci', fetch_error_at=None):
        self.calls=[];self.saved={};self.order=[];self.dispatch_bookings=[]
        self.failure=RuntimeError('private-driver-message-must-not-be-exported')
        self.rollback_failure=RuntimeError('private-rollback-message')
        self.close_failure=RuntimeError('private-close-message')
        self.save_failure=RuntimeError('private-save-message')
        self.connection=Mock()
        self.runtime=types.SimpleNamespace(environment=environment)
        self.c=MeteredComposition(runtime=self.runtime)
        self.now=[0]
        self.c.meter.clock=lambda:self.now[0]
        self.c.meter.started=0
        self.runtime=self.c.native_runtime(None)
        self.identity={'ro':'off' if invalid_identity else 'on','db':'postgres',
                       'role':'postgres','ssl':True,
                       'instance_sha':'d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15'}
        self.migrations=[{'version':str(i),'name':'synthetic','sql_sha':'a'*64}
                         for i in range(43)]+[{'version':'20261012185121','name':'synthetic','sql_sha':'b'*64}]
        def execute(sql):
            event=self.c.meter.events[-1]
            self.assertFalse(event['confirmed'])
            self.assertEqual(event['commands'],1)
            self.assertEqual(self.c.meter.used,len(self.calls)+1)
            self.dispatch_bookings.append(copy.deepcopy(event))
            self.calls.append(sql);self.order.append('dispatch')
            if sql=='ROLLBACK' and rollback_error:raise self.rollback_failure
            if len(self.calls)==fail_at:raise self.failure
            rows=[self.identity] if sql==GUARD else self.migrations if sql==gates.MIGRATIONS else []
            def fetch():
                if len(self.calls)==fetch_error_at:raise self.failure
                return rows
            return types.SimpleNamespace(description=bool(rows),fetchall=fetch)
        self.connection.execute.side_effect=execute
        def close():
            self.order.append('close')
            if close_error:raise self.close_failure
        self.connection.close.side_effect=close
        self.runtime.connect=Mock(side_effect=self.failure if connect_error else None,
                                  return_value=self.connection)
        def save(name,value):
            self.order.append('save')
            if save_error:raise self.save_failure
            self.saved[name]=copy.deepcopy(value)
        self.save=save
        self.history=patch('history_pin.validate')
        self.history.start();self.addCleanup(self.history.stop)

    def run_preflight(self):return gates.preflight(self.runtime,self.save)

    def receipt(self):return self.saved['integral-preflight.json']

    def assert_failed(self, count):
        self.assertEqual(self.c.meter.used,count)
        self.assertEqual(len(self.calls),count)
        self.assertTrue(self.c.meter.stopped)
        self.assertFalse(self.receipt()['complete'])
        self.assertEqual(len(self.receipt()['commands']),count)
        self.assertEqual(self.order[-2:],['close','save'])
        self.assertNotIn('private-',json.dumps(self.receipt()))
        self.assertEqual(self.c.meter._reserve(self.c.meter.phases,self.c.meter.state),731)
        with self.assertRaises(BudgetStop):
            self.c.meter.charge('migration',1,action='dependent_mutation',mutation=True)

    def test_normal_four_native_commands_precharged_and_not_double_counted(self):
        self.make()
        value=self.run_preflight()
        self.assertEqual(self.calls,['BEGIN TRANSACTION READ ONLY',GUARD,gates.MIGRATIONS,'ROLLBACK'])
        self.assertTrue(value['complete'])
        self.assertEqual(self.c.meter.phases,{'preflight':4})
        self.assertTrue(all(e['kind']=='native' for e in self.dispatch_bookings))
        self.c.admit_preflight(value)
        self.assertTrue(self.c.preflight_admitted)
        self.assertEqual(self.c.meter.used,4)
        self.assertEqual(len(self.c.commands),0)  # Separate existing preflight receipt.
        with self.assertRaisesRegex(ValueError,'preflight_missing'):self.c.admit_preflight(value)

    def test_every_query_failure_stays_charged_and_saves_incomplete_receipt(self):
        for position in range(1,5):
            with self.subTest(position=position):
                self.make(fail_at=position)
                with self.assertRaises(RuntimeError) as caught:self.run_preflight()
                self.assertIs(caught.exception,self.failure)
                self.assert_failed(position+1 if position<4 else 4)
                self.assertEqual(self.calls.count('ROLLBACK'),1)
                self.assertFalse(self.receipt()['commands'][position-1]['confirmed'])

    def test_lost_begin_reply_still_attempts_one_precharged_safety_rollback(self):
        self.make(fail_at=1)
        with self.assertRaises(RuntimeError):self.run_preflight()
        self.assert_failed(2)
        self.assertTrue(self.receipt()['begin_attempted'])
        self.assertTrue(self.receipt()['rollback_confirmed'])
        self.assertEqual(self.c.meter.phases,{'preflight':1})
        self.assertEqual(self.c.meter.safety_spent,{'rollback_reader':1})
        self.assertFalse(self.c.meter.receipt()['complete'])

    def test_lost_begin_and_rollback_error_still_close_and_save_original_error(self):
        self.make(fail_at=1,rollback_error=True)
        with self.assertRaises(RuntimeError) as caught:self.run_preflight()
        self.assertIs(caught.exception,self.failure)
        self.assert_failed(2)
        self.assertFalse(self.receipt()['rollback_confirmed'])
        self.assertEqual([e['stage'] for e in self.receipt()['errors']],['query_or_validation','rollback'])
        self.assertFalse(any(r['confirmed'] for r in self.receipt()['commands']))

    def test_rollback_error_alone_is_not_retried_and_does_not_skip_close_save(self):
        self.make(rollback_error=True)
        with self.assertRaises(RuntimeError) as caught:self.run_preflight()
        self.assertIs(caught.exception,self.rollback_failure)
        self.assert_failed(4)
        self.assertEqual(self.calls.count('ROLLBACK'),1)
        self.assertTrue(self.receipt()['connection_closed'])

    def test_identity_validation_failure_books_three_dispatches(self):
        self.make(invalid_identity=True)
        with self.assertRaisesRegex(ValueError,'preflight_identity'):self.run_preflight()
        self.assert_failed(3)
        self.assertEqual(self.c.meter.phases,{'preflight':2})
        self.assertEqual(self.c.meter.safety_spent,{'rollback_reader':1})

    def test_fetch_failure_remains_unknown_and_rollback_is_counted(self):
        self.make(fetch_error_at=2)
        with self.assertRaises(RuntimeError):self.run_preflight()
        self.assert_failed(3)
        self.assertFalse(self.receipt()['commands'][1]['confirmed'])

    def test_migration_validation_failure_cannot_admit(self):
        self.make()
        self.migrations[-1]['version']='unexpected'
        with self.assertRaisesRegex(ValueError,'preflight_quota_history'):self.run_preflight()
        self.assert_failed(4)
        with self.assertRaises(ValueError):self.c.admit_preflight(self.receipt())

    def test_connection_failure_saves_zero_commands(self):
        self.make(connect_error=True)
        with self.assertRaises(RuntimeError):self.run_preflight()
        self.assertEqual(self.calls,[])
        self.assertEqual(self.c.meter.used,0)
        self.assertFalse(self.receipt()['connection_closed'])
        self.assertFalse(self.receipt()['complete'])
        self.connection.close.assert_not_called()

    def test_close_failure_still_saves_and_fails_closed(self):
        self.make(close_error=True)
        with self.assertRaises(RuntimeError) as caught:self.run_preflight()
        self.assertIs(caught.exception,self.close_failure)
        self.assert_failed(4)
        self.assertFalse(self.receipt()['connection_closed'])

    def test_save_failure_propagates_after_close(self):
        self.make(save_error=True)
        with self.assertRaises(RuntimeError) as caught:self.run_preflight()
        self.assertIs(caught.exception,self.save_failure)
        self.assertEqual(self.order[-2:],['close','save'])
        self.assertTrue(self.c.meter.stopped)

    def test_cleanup_errors_do_not_replace_primary_error(self):
        self.make(fail_at=1,rollback_error=True,close_error=True,save_error=True)
        with self.assertRaises(RuntimeError) as caught:self.run_preflight()
        self.assertIs(caught.exception,self.failure)
        self.assertEqual(self.order[-2:],['close','save'])

    def test_pre_dispatch_denial_emits_nothing_but_closes_and_saves(self):
        self.make()
        self.now[0]=540
        with self.assertRaisesRegex(BudgetStop,'ordinary_deadline'):self.run_preflight()
        self.assert_failed(0)
        self.assertFalse(self.receipt()['begin_attempted'])

    def test_rollback_at_ordinary_deadline_uses_existing_safety_window(self):
        self.make()
        self.history.stop()
        with patch('history_pin.validate',side_effect=lambda *a:self.now.__setitem__(0,540)):
            with self.assertRaisesRegex(ValueError,'preflight_incomplete'):self.run_preflight()
        self.assert_failed(4)
        self.assertEqual(self.c.meter.phases,{'preflight':3})
        self.assertEqual(self.c.meter.safety_spent,{'rollback_reader':1})

    def test_safety_deadline_never_extends_to_force_rollback(self):
        self.make()
        with patch('history_pin.validate',side_effect=lambda *a:self.now.__setitem__(0,600)):
            with self.assertRaisesRegex(BudgetStop,'safety_deadline'):self.run_preflight()
        self.assert_failed(3)
        self.assertFalse(self.receipt()['rollback_confirmed'])
        self.assertEqual(self.calls.count('ROLLBACK'),0)

    def test_unmetered_staging_fails_before_connect(self):
        self.make(environment='staging')
        del self.runtime.preflight_meter
        with self.assertRaisesRegex(ValueError,'meter_required'):self.run_preflight()
        self.runtime.connect.assert_not_called()

    def test_staging_path_uses_same_four_precharged_commands(self):
        self.make(environment='staging')
        value=self.run_preflight()
        self.c.admit_preflight(value)
        self.assertEqual(self.c.meter.used,4)
        self.assertEqual(value['hosted_calls'],1)  # Label only; memory driver.

    def test_runtime_cannot_be_rebound_to_another_meter(self):
        self.make()
        other=MeteredComposition(runtime=self.runtime)
        with self.assertRaisesRegex(ValueError,'runtime_rebound'):other.native_runtime(None)

    def test_registered_lifecycle_binds_meter_before_preflight_and_admits_once(self):
        from registered_lifecycle import RegisteredLifecycle
        self.make()
        del self.runtime.preflight_meter
        lifecycle=object.__new__(RegisteredLifecycle)
        lifecycle.composition=self.c
        lifecycle.gate=types.SimpleNamespace(save=self.save,apply_endchain_migration=Mock())
        lifecycle.run_id='synthetic';lifecycle.ids={};lifecycle.installed=False;lifecycle.failed=False
        lifecycle.guard=types.SimpleNamespace(scope=lambda *a:'synthetic_guard')
        lifecycle.audit=types.SimpleNamespace(scope=lambda *a:'synthetic_observer')
        def stop_after_admission(*args):
            self.assertTrue(self.c.preflight_admitted)
            self.assertEqual(self.c.meter.used,4)
            self.assertIs(self.runtime.preflight_meter,self.c.meter)
            raise RuntimeError('offline_stop_before_preservation')
        with patch.object(self.c,'preservation',side_effect=stop_after_admission):
            with self.assertRaisesRegex(RuntimeError,'offline_stop_before_preservation'):
                lifecycle.dispatch({'op':'install','ids':{}})
        lifecycle.gate.apply_endchain_migration.assert_not_called()
        self.assertEqual(self.calls.count('ROLLBACK'),1)

    def test_success_receipt_cannot_be_forged_or_replayed(self):
        for edit in ('ticket','hash','confirmed','complete','metered'):
            with self.subTest(edit=edit):
                self.make();receipt=self.run_preflight()
                if edit=='ticket':receipt['commands'][1]['meter_ticket']=receipt['commands'][0]['meter_ticket']
                if edit=='hash':receipt['commands'][0]['sql_sha256']='0'*64
                if edit=='confirmed':receipt['commands'][0]['confirmed']=False
                if edit=='complete':receipt['complete']=False
                if edit=='metered':receipt['metered_before_dispatch']=False
                with self.assertRaises(ValueError):self.c.admit_preflight(receipt)
                self.assertEqual(self.c.meter.used,4)

    def test_second_preflight_never_connects_or_recharges(self):
        self.make();self.run_preflight()
        with self.assertRaisesRegex(ValueError,'meter_not_fresh'):self.run_preflight()
        self.runtime.connect.assert_called_once_with()
        self.assertEqual(self.c.meter.used,4)

    def test_authorized_limits_unchanged(self):
        plan=capacity()
        self.assertEqual((plan['normal_capacity'],plan['worst_including_safety'],plan['approved_limit']),
                         (2338,2349,2349))
        self.assertEqual(sum(plan['phase_budgets'][k] for k in ('cleanup','final','closure')),731)


if __name__=='__main__':unittest.main()
