"""Fault hook unit tests only; actual full-chain results require disposable CI."""
import copy
import json
import pathlib
import tempfile
import unittest
import uuid
from types import SimpleNamespace

from quota_candidate_v1 import runtime_faults as f
from quota_candidate_v1.compiler import binding as identity, canonical, sha
import scenario


class FaultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='quota-phase-unit-')
        self.addCleanup(self.temp.cleanup)
        self.out=pathlib.Path(self.temp.name)
        self.scenario=scenario.capture()['workflow_actions']
        self.binding={'run_id':str(uuid.uuid4()),'parent_id':identity.NEW_RUN,
            'source_commit':'a'*40,'candidate_sha':'b'*64,'ci_run':'123',
            'environment':'disposable_ci','hosted_permission':False,'execution_admitted':False}
        self.saved=[]

    def hooks(self,case):
        return f.PhaseFaults(case,self.binding,self.scenario,out=self.out,
                             save=lambda n,v:self.saved.append((n,copy.deepcopy(v))))

    def test_exact_fifteen_cases_and_real_scenario_locations(self):
        s=f.selectors(self.scenario)
        self.assertEqual(set(s),set(f.CASES))
        self.assertEqual(len(s),15)
        from admission_budget import CASES
        self.assertEqual(f.CASES,('normal',*CASES))
        self.assertEqual([s[x]['step'] for x in ('route_a','route_b','restore','duplicate')],[1,21,8,6])

    def test_unknown_and_legacy_cases_denied(self):
        with self.assertRaises(ValueError):self.hooks('invented')
        self.binding['run_id']=identity.OLD_RUN
        with self.assertRaises(ValueError):self.hooks('normal')

    def test_replay_requires_identical_preregistered_request(self):
        self.scenario[6]['request']['key']=str(uuid.uuid4())
        with self.assertRaisesRegex(ValueError,'fault_replay_not_same_payload'):self.hooks('duplicate')

    def test_route_restore_lost_reply_and_partial_cleanup_are_one_shot(self):
        for case,step in [('route_a',1),('route_b',21),('restore',8),('lost_response',0),('partial_fixture_cleanup',47)]:
            with self.subTest(case=case):
                h=self.hooks(case)
                h.native_after('workflow','call','private SQL',{'kind':'workflow','step':step})
                self.assertIsNone(h.fired)
                with self.assertRaisesRegex(f.InjectedFault,'case_injected_'+case):
                    h.native_after('workflow','commit','COMMIT',{'kind':'workflow','step':step})
                h.native_after('workflow','commit','COMMIT',{'kind':'workflow','step':step})
                self.assertTrue(h.fired['event']['dispatch_confirmed'])
                self.assertNotIn('private SQL',json.dumps(h.receipt()))

    def test_mid_auth_only_after_exact_known_refresh(self):
        h=self.hooks('mid_auth')
        h.auth_confirmed('a_member','issue')
        self.assertIsNone(h.fired)
        with self.assertRaises(f.InjectedFault):h.auth_confirmed('a_member','refresh')

    def test_controller_stops_before_pair_not_after_claimed_validation(self):
        h=self.hooks('controller')
        h.controller_before([self.binding['run_id'],2,'after_saved',{'secret':'never_export'}])
        with self.assertRaises(f.InjectedFault):
            h.controller_before([self.binding['run_id'],2,'pair_validated',{'secret':'never_export'}])
        self.assertFalse(h.fired['event']['dispatch_attempted'])
        self.assertNotIn('never_export',json.dumps(h.receipt()))

    def test_duplicate_requires_actual_validated_pair_callback(self):
        h=self.hooks('duplicate')
        h.pair_confirmed({'step':5,'phase':'pair_validated','pair_complete':True})
        with self.assertRaises(f.InjectedFault):
            h.pair_confirmed({'step':6,'phase':'pair_validated','pair_complete':True})

    def test_cleanup_final_and_closure_exact_sides(self):
        for case,side,phase in [('cleanup_failure','before','remove'),
            ('final_check_failure','after','gates_final_post_metadata'),
            ('closure_failure','before','final_closure')]:
            with self.subTest(case=case):
                h=self.hooks(case)
                h.outer('after' if side=='before' else 'before',phase,'not exported')
                self.assertIsNone(h.fired)
                with self.assertRaises(f.InjectedFault):h.outer(side,phase,'not exported')

    def test_timeout_replaces_only_one_real_call_and_requires_57014(self):
        h=self.hooks('timeout')
        action={'kind':'workflow','step':0}
        sql,args=h.prepare_native('workflow','call','product call',['private'],action)
        self.assertEqual((sql,args),(f.TIMEOUT_SQL,()))
        self.assertEqual(h.prepare_native('workflow','call','original',[],action),('original',[]))
        self.assertIsNone(h.fired)
        h.native_error('workflow','call',sql,action,'57014')
        self.assertTrue(h.receipt()['fault_observed'])
        self.assertEqual(h.fired['event']['statement_timeout_ms'],5000)

    def test_timeout_missing_cancel_never_passes_as_observed(self):
        h=self.hooks('timeout');action={'kind':'workflow','step':0}
        h.prepare_native('workflow','call','original',[],action)
        with self.assertRaisesRegex(ValueError,'fault_timeout_not_observed'):
            h.native_error('workflow','call',f.TIMEOUT_SQL,action,'08006')
        self.assertFalse(h.receipt()['fault_observed'])

    def snapshot(self,stage):
        names=['migration-boundary-pre.json'] if stage=='before45' else [
            'cli-predispatch-canonical-45.json','migration-boundary-post.json']
        refs=[]
        for name in names:
            raw=canonical({'unit_only':True})
            (self.out/name).write_bytes(raw)
            refs.append({'path':name,'sha256':sha(raw),'bytes':len(raw)})
        return {'stage':stage,'source_commit':self.binding['source_commit'],'ci_run':'123',
            'candidate_sha256':self.binding['candidate_sha'],'history_count':44 if stage=='before45' else 45,
            'evidence_refs':refs,'full_chain_admission':False,'hosted_admission':False}

    def test_canonical_hooks_validate_exact_source_and_immutable_receipt(self):
        for case,stage in [('pre_migration','before45'),('post_migration','after45')]:
            with self.subTest(case=case):
                h=self.hooks(case);snapshot=self.snapshot(stage)
                with self.assertRaises(f.InjectedFault):getattr(h,stage)(snapshot)
                self.assertEqual(h.fired['event']['history_count'],snapshot['history_count'])

    def test_migration_snapshot_tampering_does_not_fire(self):
        h=self.hooks('pre_migration');snapshot=self.snapshot('before45')
        snapshot['evidence_refs'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'fault_migration_evidence_hash'):h.before45(snapshot)
        self.assertFalse(h.receipt()['fault_observed'])

    def test_normal_has_no_fault_and_cannot_claim_matrix_pass(self):
        h=self.hooks('normal')
        h.outer('before','final_closure','not exported')
        self.assertFalse(h.receipt()['fault_observed'])
        self.assertFalse(h.receipt()['full_matrix_pass'])

    def test_original_fault_survives_evidence_save_failure(self):
        h=self.hooks('cleanup_failure')
        def fail(*_):raise OSError('private failure text')
        h.save=fail
        with self.assertRaisesRegex(f.InjectedFault,'case_injected_cleanup_failure') as caught:
            h.outer('before','remove','not exported')
        self.assertEqual(caught.exception.__notes__,['case_fault_receipt_secondary:OSError'])


if __name__=='__main__':unittest.main()
