import copy,unittest
from registration_accounting import build

class Tests(unittest.TestCase):
    def fixture(self):
        p='registration12-transport-';row={'confirmed':True,'operation':'registration12_cleanup_a','template_sha256':'a'*64,'call_id':'synthetic','ordinal':1,'duration_ms':0}
        files={p+'integration-native-admin-protocol.json':{'synthetic_roles':['a','trainer','b'],'register':[row]},
               p+'integration-managed-auth-protocol.json':{'commands':5,'statements':[{'calls':5,'queryid':'1','temp_written':0,'exec_ms':0}]}}
        for role in ('a','b'):files[p+'database-'+role+'.json']={'route':role.upper(),'transport':'private_candidate_actual_local_GoTrue_and_verified_TLS','commands':1,'register':[row]}
        for n,count in enumerate((0,3)):
            name=p+'pair-'+str(n);binding={'action':'synthetic'+str(n)}
            files[name+'-before.json']={'binding':binding};files[name+'-after.json']={'binding':binding}
            files[name+'-validated.json']={'binding':binding,'complete':True,'expected_count':count,'writes':[{}]*count,'error_class':None}
        return files
    def test_exact_native_and_managed_count_without_hosted_allowance(self):
        f=self.fixture();v=build(f.__getitem__,f)
        self.assertEqual(v['observed_commands'],8);self.assertEqual(v['pair_count'],2)
        self.assertFalse(v['hosted_authorized']);self.assertIsNone(v['hosted_maximum'])
    def test_missing_after_binding_extra_identity_and_incomplete_terminal(self):
        for fault in ('after','identity','terminal','managed'):
            f=self.fixture();p='registration12-transport-'
            if fault=='after':f[p+'pair-0-after.json']['binding']={}
            if fault=='identity':f[p+'integration-native-admin-protocol.json']['synthetic_roles'].append('owner')
            if fault=='terminal':f[p+'database-a.json']['register'][0]['confirmed']=False
            if fault=='managed':f[p+'integration-managed-auth-protocol.json']['commands']=6
            with self.assertRaises(ValueError):build(f.__getitem__,f)

if __name__=='__main__':unittest.main()
