import json,unittest
import lease_trace as m

class LeaseTrace(unittest.TestCase):
    def test_reads_never_grant(self):
        calls=[];saved=[]
        def api(path,method,body):
            calls.append(method);return {'state':'disabled'} if path.endswith('jit-access') else {'items':[]}
        self.assertEqual(m.inspect_closed(api,lambda n,v:saved.append(v))['remaining_mappings'],0)
        self.assertEqual(calls,['GET','GET'])
    def test_active_access_not_taken_over(self):
        with self.assertRaises(m.LeaseFailure):m.inspect_closed(lambda *args:{'state':'enabled','items':[{}]},lambda *args:None)
    def test_each_phase_preserves_different_failure(self):
        for position,phase in enumerate(['jit_enable','jit_role_grant','jit_mapping_confirm']):
            with self.subTest(phase=phase):
                saved=[];calls=[]
                def api(*args):
                    calls.append(args)
                    if len(calls)==position+1:raise RuntimeError('management_http_406')
                    return {}
                with self.assertRaises(m.LeaseFailure) as caught:m.grant_once(api,lambda n,v:saved.append(v),'synthetic-owner',123)
                self.assertEqual(caught.exception.phase,phase);self.assertEqual(caught.exception.status,406)
                self.assertEqual(len(calls),position+1);self.assertEqual(saved[-1]['phase'],phase)
                self.assertNotIn('synthetic-owner',json.dumps(saved))
    def test_secret_error_text_never_saved(self):
        saved=[]
        def api(*args):raise RuntimeError('postgres://password@secret-host')
        with self.assertRaises(m.LeaseFailure):m.grant_once(api,lambda n,v:saved.append(v),'synthetic-owner',123)
        self.assertNotIn('password',json.dumps(saved));self.assertNotIn('secret-host',json.dumps(saved));self.assertIsNone(saved[-1]['http_status'])
    def test_no_success_on_wrong_mapping(self):
        with self.assertRaises(m.LeaseFailure):m.grant_once(lambda *args:{'user_id':'other','user_roles':[]},lambda *args:None,'synthetic-owner',123)
    def test_success_does_not_export_mapping(self):
        saved=[]
        self.assertTrue(m.grant_once(lambda *args:{'user_id':'synthetic-owner','user_roles':[{'role':'postgres','expires_at':123}]},lambda n,v:saved.append(v),'synthetic-owner',123))
        self.assertNotIn('synthetic-owner',json.dumps(saved));self.assertNotIn('user_roles',json.dumps(saved))

if __name__=='__main__':unittest.main()
