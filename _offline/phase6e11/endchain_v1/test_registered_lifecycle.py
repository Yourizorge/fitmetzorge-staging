import copy,json,types,unittest
from unittest.mock import patch
from registered_lifecycle import RegisteredLifecycle

class RegisteredLifecycleTests(unittest.TestCase):
    def make(self):
        self.calls=[];self.saved={};self.ids={'a_member':'one','a_trainer':'two','b_member':'three'}
        def module(name):
            return types.SimpleNamespace(scope=lambda *a:name,install=lambda *a:name+'_install',inspect=lambda *a:name+'_inspect',
                validate=lambda state,*a,**kw:state,remove=lambda *a:name+'_remove')
        def sql(q):
            self.calls.append(q)
            if q.endswith('_inspect'):return json.dumps({'expires_at':'synthetic-expiry','object':q.split('_')[0]})
            return ''
        def save(name,value):self.saved[name]=value
        c=types.SimpleNamespace(fixture_context={},commands=[],current_phase=None,
            preservation=lambda *a:self.calls.append('preserve_'+a[-1]),
            workflow=lambda *a:dict(pairs=71,deletes=123),
            finalize=lambda *a:self.calls.append('final_dry'),
            close_receipt=lambda *a:'final',evidence_query=lambda *a:'evidence')
        contract=lambda actor:types.SimpleNamespace(step=0)
        r=RegisteredLifecycle(gate=types.SimpleNamespace(save=save),composition=c,run_id='synthetic-run',ids=self.ids,
            guard=module('guard'),audit=module('audit'),contract_type=contract,sql=sql,
            lock_query=lambda *a:[],independent_ci=False)
        return r
    def test_no_identity_creation_and_exact_install_binding(self):
        r=self.make()
        with self.assertRaisesRegex(ValueError,'install_binding'):r.dispatch({'op':'install','ids':{}})
        self.assertEqual(self.calls,[])
        with self.assertRaisesRegex(ValueError,'stopped'):r.dispatch({'op':'install','ids':self.ids})
    def test_guard_and_observer_are_exact_and_removed_after_stop(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        with self.assertRaises(ValueError):r.dispatch({'op':'workflow'})
        value=r.dispatch({'op':'remove','receipt':receipt,'stopped':True})
        self.assertTrue(value['removed'])
        self.assertEqual(self.calls[-2:],['audit_remove','guard_remove'])
        self.assertNotIn('preserve_after_cleanup',self.calls)
        self.assertFalse(any('delete' in q or 'users' in q for q in self.calls))
    def test_normal_close_requires_complete_auth_and_workflow(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        with self.assertRaisesRegex(ValueError,'chain_incomplete'):r.dispatch({'op':'remove','receipt':receipt})
        self.assertFalse(r.removed)
        self.assertNotIn('audit_remove',self.calls)
        with self.assertRaises(ValueError):r.dispatch({'op':'finalize'})
    def test_full_registered_path_preserves_after_only_when_complete(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        for contract in r.evidence.contracts.values():contract.step=4
        self.assertEqual(r.dispatch({'op':'workflow'})['pairs'],71)
        for contract in r.evidence.contracts.values():contract.step=6
        self.assertTrue(r.dispatch({'op':'remove','receipt':receipt})['removed'])
        self.assertEqual(self.calls[-5:],['preserve_after_cleanup','final_dry','audit_remove',
                                         'guard_remove','preserve_final_post'])
        self.assertEqual(r.dispatch({'op':'finalize'}),'final')
        self.assertEqual(self.calls.count('final_dry'),1)
    def test_failed_pre_keeps_guards_until_explicit_stop_cleanup(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        r.workflow_complete=True
        for contract in r.evidence.contracts.values():contract.step=6
        def failure(*args):raise ValueError('synthetic_pre_failure')
        r.composition.preservation=failure
        with self.assertRaisesRegex(ValueError,'synthetic_pre'):
            r.dispatch({'op':'remove','receipt':receipt})
        self.assertNotIn('audit_remove',self.calls)
        self.assertNotIn('final_dry',self.calls)
        self.assertTrue(r.dispatch({'op':'remove','receipt':receipt,'stopped':True})['removed'])
    def test_failed_final_dry_never_runs_post_or_closure(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        r.workflow_complete=True
        for contract in r.evidence.contracts.values():contract.step=6
        def failure(*args):raise ValueError('synthetic_dry_failure')
        r.composition.finalize=failure
        with self.assertRaisesRegex(ValueError,'synthetic_dry'):
            r.dispatch({'op':'remove','receipt':receipt})
        self.assertNotIn('audit_remove',self.calls)
        self.assertNotIn('preserve_final_post',self.calls)
        with self.assertRaises(ValueError):r.dispatch({'op':'finalize'})
    def test_unknown_operation_never_reaches_sql(self):
        r=self.make()
        for op in ['signup','create_account','cleanup_all','admin_delete']:
            with self.assertRaisesRegex(ValueError,'operation_denied'):r.dispatch({'op':op})
        self.assertEqual(self.calls,[])

    def test_stopped_worker_cannot_remove_parent_auth_evidence(self):
        r=self.make();r.own_worker();receipt=r.dispatch({'op':'install','ids':self.ids})
        r.failed=True
        result=r.dispatch({'op':'remove','receipt':receipt,'stopped':True})
        self.assertTrue(result['deferred_to_parent']);self.assertFalse(result['removed'])
        with self.assertRaisesRegex(ValueError,'parent_cleanup_pending'):r.close_temporary()
        self.assertNotIn('audit_remove',self.calls)
        with patch.object(r.safety_auth,'parent_finish',return_value={'status':'NO_GO','revocation_confirmed':False}):
            r.parent_auth_cleanup(worker_terminated=True)
        self.assertFalse(r.parent_auth_result['revocation_confirmed'])
        self.assertEqual(r.parent_auth_result['status'],'NO_GO')
        r.close_temporary()
        self.assertEqual(self.calls[-2:],['audit_remove','guard_remove'])
        self.assertTrue(r.removed)

    def test_unconfirmed_worker_cannot_revoke_or_remove(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        with patch.object(r.safety_auth,'parent_finish') as finish:
            result=r.parent_auth_cleanup(worker_terminated=False)
        finish.assert_not_called();self.assertFalse(result['revocation_confirmed'])
        self.assertEqual(result['reason'],'worker_termination_unconfirmed')
        with self.assertRaisesRegex(ValueError,'parent_cleanup_pending'):r.close_temporary()

    def test_parent_cleanup_is_one_shot_even_when_native_result_unknown(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        with patch.object(r.safety_auth,'parent_finish',side_effect=ValueError('lost_native_reply')) as finish:
            first=r.parent_auth_cleanup(worker_terminated=True)
            second=r.parent_auth_cleanup(worker_terminated=True)
        finish.assert_called_once_with(worker_terminated=True)
        self.assertEqual(first,second);self.assertFalse(first['revocation_confirmed'])
        self.assertFalse(first['global_zero_claim'])

    def test_proven_inactive_meter_does_not_claim_a_new_auth_zero(self):
        r=self.make();r.own_worker()
        r.composition.meter=types.SimpleNamespace(state={'auth_maybe_live':False})
        with patch.object(r.safety_auth,'parent_finish') as finish:
            result=r.parent_auth_cleanup(worker_terminated=True)
        finish.assert_not_called()
        self.assertEqual(result['reason'],'auth_safety_not_required_by_meter')
        self.assertFalse(result['revocation_confirmed'])
        self.assertTrue(result['safe_to_remove'])

    def test_parent_removes_after_confirmed_revocation_is_saved(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        r.composition.meter=types.SimpleNamespace(state={'auth_maybe_live':True})
        def revoke(**kw):
            self.calls.append('parent_native_revoke')
            r.composition.meter.state['auth_maybe_live']=False
            return {'status':'NO_GO','revocation_confirmed':True}
        with patch.object(r.safety_auth,'parent_finish',side_effect=revoke) as finish:
            result=r.parent_auth_cleanup(worker_terminated=True)
            r.parent_auth_cleanup(worker_terminated=True)
        finish.assert_called_once();self.assertTrue(result['safe_to_remove'])
        self.assertTrue(r.parent_auth_saved)
        r.close_temporary()
        self.assertEqual(self.calls[-3:],['parent_native_revoke','audit_remove','guard_remove'])

    def test_native_claim_without_meter_confirmation_stays_unknown_but_removes_owned_guards(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        r.composition.meter=types.SimpleNamespace(state={'auth_maybe_live':True})
        with patch.object(r.safety_auth,'parent_finish',return_value={'revocation_confirmed':True}):
            result=r.parent_auth_cleanup(worker_terminated=True)
        self.assertFalse(result['revocation_confirmed']);self.assertTrue(result['safe_to_remove'])
        r.close_temporary()
        self.assertEqual(self.calls[-2:],['audit_remove','guard_remove'])
        self.assertTrue(r.composition.meter.state['auth_maybe_live'])

    def test_parent_receipt_save_failure_keeps_guards_and_never_retries_suffix(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        r.composition.meter=types.SimpleNamespace(state={'auth_maybe_live':False})
        with patch.object(r.gate,'save',side_effect=RuntimeError('offline_save_failure')):
            with self.assertRaises(RuntimeError):r.parent_auth_cleanup(worker_terminated=True)
        self.assertFalse(r.parent_auth_saved)
        with self.assertRaisesRegex(ValueError,'parent_cleanup_evidence_pending'):r.close_temporary()

    def test_identity_lock_close_failure_blocks_exact_removal(self):
        from registered_runner import IdentitySession
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        r.lock_query=object.__new__(IdentitySession).query
        with patch.object(IdentitySession,'close',side_effect=RuntimeError('lock_close_unknown')), \
             patch.object(r.safety_auth,'parent_finish') as finish:
            result=r.parent_auth_cleanup(worker_terminated=True)
        finish.assert_not_called();self.assertFalse(result['child_mint_barrier'])
        with self.assertRaisesRegex(ValueError,'parent_cleanup_evidence_pending'):r.close_temporary()
        self.assertNotIn('audit_remove',self.calls)

    def test_unknown_auth_does_not_bypass_exact_removal_identity_or_retry(self):
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        with patch.object(r.safety_auth,'parent_finish',return_value={'status':'NO_GO','revocation_confirmed':False}):
            result=r.parent_auth_cleanup(worker_terminated=True)
        self.assertTrue(result['safe_to_remove']);self.assertTrue(r.parent_auth_saved)
        with patch.object(r.audit,'remove',side_effect=ValueError('metadata_removal_mismatch')) as remove:
            with self.assertRaisesRegex(ValueError,'removal_unconfirmed'):r.close_temporary()
            r.close_temporary()
        remove.assert_called_once();self.assertFalse(r.removed)
        self.assertNotIn('audit_remove',self.calls);self.assertEqual(self.calls.count('guard_remove'),1)
        self.assertFalse(result['revocation_confirmed'])

    def test_parent_closes_real_identity_session_before_native_cleanup(self):
        from registered_runner import IdentitySession
        r=self.make();r.own_worker();r.dispatch({'op':'install','ids':self.ids});r.failed=True
        r.composition.meter=types.SimpleNamespace(state={'auth_maybe_live':True})
        session=object.__new__(IdentitySession)
        r.lock_query=session.query
        with patch.object(IdentitySession,'close',side_effect=lambda:self.calls.append('lock_closed')), \
             patch.object(r.safety_auth,'parent_finish',side_effect=lambda **kw:self.calls.append('native') or {'revocation_confirmed':False}):
            r.parent_auth_cleanup(worker_terminated=True)
        self.assertEqual(self.calls[-2:],['lock_closed','native'])

if __name__=='__main__':unittest.main()
