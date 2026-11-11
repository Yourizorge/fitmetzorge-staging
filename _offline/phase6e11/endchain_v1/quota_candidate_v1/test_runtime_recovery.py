"""Offline fault-driver tests, never evidence of actual DB/Auth revocation."""
import time
import types
import unittest
from unittest import mock

from quota_candidate_v1 import runtime_recovery as r


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.saved={};self.calls=[];self.closed=[]
        self.meter=types.SimpleNamespace(setup_connection_owned=True,
            confirm_controls_restored=mock.Mock())
        self.c=types.SimpleNamespace(meter=self.meter,commands=[],events=[],started=time.monotonic(),
            fault=None,injected=False,safety_label=None,abort=mock.Mock())
        self.g=types.SimpleNamespace(save=lambda n,v:self.saved.__setitem__(n,v))
        self.connections={name:types.SimpleNamespace(info=types.SimpleNamespace(transaction_status=2),
            close=lambda n=name:self.closed.append(n)) for name in r.CHANNELS}
        self.runtime=types.SimpleNamespace(connect=mock.Mock(return_value=types.SimpleNamespace(close=lambda:None)))
        def query(channel,phase,text,args=()):
            self.calls.append((channel,phase,text,args))
            self.c.commands.append(dict(phase=phase,confirmed=True))
            if phase=='safety_control_before':return [{'value':r.recover.__globals__['CLOSED']}]
            if phase=='safety_control_after':return [{'value':r.recover.__globals__['CLOSED']}]
            return []
        self.query=query
        self.kw=dict(process=None,timer=None,enable_attempted=False,original=None,enabled=None,
                     restored=None,primary=RuntimeError('original_failed_call'))

    def run_finish(self):
        return r.finish(self.c,self.g,self.runtime,self.connections,self.query,self.query,**self.kw)

    def test_exact_four_owned_rollback_commands_no_retries(self):
        value=self.run_finish()
        self.assertEqual([x[:3] for x in self.calls],[(n,'safety_rollback','ROLLBACK') for n in r.CHANNELS])
        self.assertEqual(self.closed,list(r.CHANNELS))
        self.assertTrue(value['complete'])
        self.assertFalse(value['fixtures_removed'])
        self.assertFalse(value['token_revocation_claim'])
        self.assertFalse(self.meter.setup_connection_owned)

    def test_idle_connections_dispatch_zero(self):
        for c in self.connections.values():c.info.transaction_status=0
        self.run_finish()
        self.assertEqual(self.calls,[])

    def test_observed_reap_failure_keeps_original_and_prevents_sql(self):
        observed=types.SimpleNamespace(close=mock.Mock(),reaped=False,known=False,
            receipt=lambda:{'unit':True,'wait_completed':False})
        self.kw.update(process=object(),worker_evidence=observed)
        with mock.patch('quota_candidate_v1.runtime_worker_evidence.save',return_value={'unit_ref':True}):
            value=self.run_finish()
        observed.close.assert_called_once()
        self.assertFalse(value['complete']);self.assertFalse(value['worker_terminated'])
        self.assertEqual(self.calls,[])
        self.assertIn('workflow_recovery_secondary:worker_wait:RuntimeError',self.kw['primary'].__notes__)

    def test_timeout_even_if_reaped_is_not_complete_but_safe_rollback_continues(self):
        observed=types.SimpleNamespace(close=mock.Mock(),reaped=True,known=False,
            receipt=lambda:{'unit':True,'wait_error_class':'TimeoutExpired'})
        self.kw.update(process=object(),worker_evidence=observed)
        with mock.patch('quota_candidate_v1.runtime_worker_evidence.save',return_value={'unit_ref':True}):
            value=self.run_finish()
        self.assertFalse(value['complete']);self.assertTrue(value['worker_terminated'])
        self.assertEqual(len(self.calls),4)

    def test_observation_save_failure_cannot_return_success(self):
        observed=types.SimpleNamespace(close=mock.Mock(),reaped=True,known=True,receipt=lambda:{'unit':True})
        self.kw.update(process=object(),worker_evidence=observed,primary=None)
        with mock.patch('quota_candidate_v1.runtime_worker_evidence.save',side_effect=OSError('unit save')):
            with self.assertRaisesRegex(RuntimeError,'workflow_recovery_incomplete'):self.run_finish()
        self.assertEqual(len(self.calls),4)

    def test_save_failure_preserves_original_and_continues_closeout(self):
        self.g.save=mock.Mock(side_effect=OSError('private_value_not_exported'))
        value=self.run_finish()
        self.assertEqual(len(self.calls),4)
        self.assertEqual(self.closed,list(r.CHANNELS))
        self.assertFalse(value['complete'])
        self.assertTrue(self.kw['primary'].__notes__)
        self.assertNotIn('private_value',str(value))

    def test_close_failure_does_not_hide_later_closes_or_original(self):
        self.connections['setup'].close=mock.Mock(side_effect=OSError())
        value=self.run_finish()
        self.assertEqual(self.closed,['writer','reader','workflow'])
        self.assertFalse(value['complete'])
        self.assertTrue(self.meter.setup_connection_owned)

    def test_failed_reap_forbids_sql_and_control_recovery(self):
        self.kw['process']=types.SimpleNamespace(poll=lambda:None,kill=lambda:None,
            communicate=mock.Mock(side_effect=TimeoutError()))
        self.kw.update(enable_attempted=True,original={},enabled={})
        value=self.run_finish()
        self.assertFalse(value['worker_terminated'])
        self.assertFalse(value['complete'])
        self.assertEqual(self.calls,[])
        self.runtime.connect.assert_not_called()

    def test_recovery_failure_cannot_make_normal_return_successful(self):
        self.kw['primary']=None
        self.connections['reader'].close=mock.Mock(side_effect=OSError())
        with self.assertRaisesRegex(RuntimeError,'workflow_recovery_incomplete'):self.run_finish()

    def test_control_compare_restore_is_exact_four_and_releases_only_confirmed(self):
        from control_recovery import CLOSED,intent
        _,enabled=intent(CLOSED,'7a755c39-f845-4348-a880-31d43d9914d8','2026-11-03T12:00:00+00:00')
        self.kw.update(enable_attempted=True,original=CLOSED,enabled=enabled)
        value=self.run_finish()
        self.assertEqual(len(self.calls),8)
        self.assertEqual([x[1] for x in self.calls[4:]],
            ['safety_control_before','safety_control_restore','safety_control_restore','safety_control_after'])
        self.meter.confirm_controls_restored.assert_called_once_with()
        self.assertTrue(value['controls_confirmed'])
        self.runtime.connect.assert_called_once_with()

    def test_unknown_control_result_keeps_state_and_no_replay(self):
        self.kw.update(enable_attempted=True,original={},enabled={})
        with mock.patch.object(r,'recover',side_effect=RuntimeError('lost_result')) as recover:
            value=self.run_finish()
        recover.assert_called_once()
        self.meter.confirm_controls_restored.assert_not_called()
        self.assertFalse(value['controls_confirmed'])
        self.assertFalse(value['complete'])

    def test_abort_failure_never_replaces_primary_or_skips_owned_closes(self):
        self.c.abort.side_effect=RuntimeError('unit abort')
        value=self.run_finish()
        self.assertFalse(value['complete'])
        self.assertEqual(self.closed,list(r.CHANNELS))
        self.assertTrue(self.kw['primary'].__notes__)

    def test_workflow_http_receipt_after_reap_failure_retains_unknown(self):
        self.c.workflow_dispatch=object()
        self.kw['process']=types.SimpleNamespace(poll=lambda:None,kill=lambda:None,
            communicate=mock.Mock(side_effect=TimeoutError()))
        with mock.patch('quota_candidate_v1.runtime_http.workflow_receipt',return_value={'unit':True}) as witness:
            self.run_finish()
        witness.assert_called_once_with(self.c,worker_terminated=False)
        self.assertEqual(self.saved['case-workflow-http-terminal.json'],{'unit':True})
        self.assertEqual(self.calls,[])

    def test_workflow_http_receipt_failure_keeps_primary_and_no_retry(self):
        self.c.workflow_dispatch=object()
        with mock.patch('quota_candidate_v1.runtime_http.workflow_receipt',side_effect=ValueError('unit source')) as witness:
            value=self.run_finish()
        witness.assert_called_once()
        self.assertFalse(value['complete'])
        self.assertEqual(self.closed,list(r.CHANNELS))
        self.assertTrue(any(x['stage']=='workflow_http_terminal' for x in value['secondary']))


if __name__=='__main__':unittest.main()
