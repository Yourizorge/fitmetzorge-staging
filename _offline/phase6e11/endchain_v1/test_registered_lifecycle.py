import copy,json,types,unittest
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
            finalize=lambda *a:'final',evidence_query=lambda *a:'evidence')
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
        self.assertTrue(r.removed)
        with self.assertRaises(ValueError):r.dispatch({'op':'finalize'})
    def test_full_registered_path_preserves_after_only_when_complete(self):
        r=self.make();receipt=r.dispatch({'op':'install','ids':self.ids})
        for contract in r.evidence.contracts.values():contract.step=4
        self.assertEqual(r.dispatch({'op':'workflow'})['pairs'],71)
        for contract in r.evidence.contracts.values():contract.step=6
        self.assertTrue(r.dispatch({'op':'remove','receipt':receipt})['removed'])
        self.assertIn('preserve_after_cleanup',self.calls)
        self.assertEqual(r.dispatch({'op':'finalize'}),'final')
    def test_unknown_operation_never_reaches_sql(self):
        r=self.make()
        for op in ['signup','create_account','cleanup_all','admin_delete']:
            with self.assertRaisesRegex(ValueError,'operation_denied'):r.dispatch({'op':op})
        self.assertEqual(self.calls,[])

if __name__=='__main__':unittest.main()
