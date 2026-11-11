"""Unit dispatch sequencing, not a live Auth or SQL evidence claim."""
import copy
import types
import unittest
from quota_candidate_v1.runtime_dispatch import WorkflowDispatch, export_dispatch_contract
from quota_candidate_v1.compiler import CandidateStop
import scenario


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.events=[dict(kind='managed_auth',commands=5,confirmed=False,
            action='gotrue_fixture_identity' if i==0 else 'gotrue_workflow_identity_'+str(i-1)) for i in range(72)]
        self.meter=types.SimpleNamespace(events=self.events,managed_pending={i+1:v for i,v in enumerate(self.events)},
            stopped=False,closed=False,used=360,state={'auth_maybe_live':True})
        self.trace=WorkflowDispatch(self.meter,list(range(1,73)))

    def test_reservations_alone_are_not_dispatch(self):
        self.assertEqual(self.trace.receipt()['observed_attempts'],0)
        self.assertFalse(self.trace.receipt()['aggregate_protocol_confirmed'])

    def test_72_actual_positions_join_without_any_refund(self):
        for index in range(72):
            if index==0:self.trace.before(index);self.trace.after(index,'response_received',200)
            else:
                self.trace.worker_message(dict(op='workflow_auth',stage='before',index=index))
                self.trace.worker_message(dict(op='workflow_auth',stage='response_received',index=index,status=200))
        result=self.trace.validated(dict(verified_calls=72,commands=360,statements=[dict(temp_written=0)]))
        self.assertTrue(result['aggregate_protocol_confirmed'])
        self.assertEqual([r['ticket'] for r in result['rows']],list(range(1,73)))
        self.assertEqual(len(self.meter.managed_pending),72)
        self.assertFalse(result['individual_sql_cost_observed'])
        self.assertFalse(any(r['identity_verified'] for r in result['rows']))

    def test_before_requires_exact_next_position_and_no_overlap(self):
        with self.assertRaises(CandidateStop):self.trace.before(1)
        self.trace.before(0)
        with self.assertRaises(CandidateStop):self.trace.before(1)

    def test_lost_http_keeps_capacity_and_unknown_is_not_zero(self):
        self.trace.before(0);self.trace.after(0,'lost_response')
        self.assertEqual(self.trace.rows[0]['outcome'],'lost_response')
        self.assertEqual(self.meter.used,360);self.assertEqual(len(self.meter.managed_pending),72)
        with self.assertRaises(CandidateStop):self.trace.validated(dict(verified_calls=72,commands=360,statements=[]))

    def test_stopped_meter_forbids_any_later_http(self):
        self.meter.stopped=True
        with self.assertRaises(CandidateStop):self.trace.before(0)
        self.assertEqual(self.trace.rows,[])

    def test_wrong_precharge_and_missing_ticket_rejected(self):
        for alter in (lambda:self.events[0].update(commands=4),lambda:self.meter.managed_pending.pop(1)):
            saved=copy.deepcopy(self.events[0]);alter()
            with self.assertRaises(CandidateStop):WorkflowDispatch(self.meter,list(range(1,73)))
            self.events[0].update(saved)

    def test_ipc_rejects_secrets_unknown_fields_and_parent_index(self):
        for value in (dict(op='workflow_auth',stage='before',index=0),
                      dict(op='workflow_auth',stage='before',index=1,token='secret')):
            with self.assertRaises(CandidateStop):self.trace.worker_message(value)

    def test_export_does_not_fabricate_full_native_or_recovery_join(self):
        contract=export_dispatch_contract({'plan_sha256':'a'*64},scenario.capture()['workflow_actions'])
        self.assertEqual(len(contract['events']),144)
        self.assertEqual(sum(e.get('managed_workflow_identity',False) for e in contract['events']),72)
        self.assertFalse(contract['recovery_edges_complete'])
        self.assertTrue(contract['missing_hooks'])
        self.assertEqual(contract['normal_event_ids'],[])


if __name__=='__main__':unittest.main()
