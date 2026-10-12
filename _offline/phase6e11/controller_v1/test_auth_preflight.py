import copy,json,unittest
import auth_preflight as a

class Preflight(unittest.TestCase):
    def rig(self):
        keys=('id_matches','registered_role_matches','enabled','auth_present','email_matches','confirmed','profile_matches','trainer_matches','operator_matches')
        v={'identities':[{'role':r,**{k:True for k in keys}} for r in ['a_member','a_trainer','b_member']],
           'history_count':43,'incomplete_requests':0,'managed_audit_observers':0,'windows':{'live':0}}
        c={'sessions_single_per_user':False,'hook_custom_access_token_enabled':False}
        return v,c
    def test_allow_registered_only(self):self.assertTrue(a.validate(*self.rig()))
    def test_duplicate_role_denied(self):
        v,c=self.rig();v['identities'][1]['role']='a_member'
        with self.assertRaises(a.m.Stop):a.validate(v,c)
    def test_each_missing_identity_fact_denied(self):
        for key in self.rig()[0]['identities'][0]:
            if key=='role':continue
            with self.subTest(key=key):
                v,c=self.rig();v['identities'][0][key]=False
                with self.assertRaises(a.m.Stop):a.validate(v,c)
    def test_cross_session_policy_denied(self):
        for setting in (True,None,'unrecognized_format'):
            v,c=self.rig();c['sessions_single_per_user']=setting
            with self.assertRaises(a.m.Stop):a.validate(v,c)
    def test_unknown_hooks_denied(self):
        for setting in (True,None):
            v,c=self.rig();c['hook_custom_access_token_enabled']=setting
            with self.assertRaises(a.m.Stop):a.validate(v,c)
    def test_existing_window_and_incomplete_request_denied(self):
        for flag in ('window','incomplete','managed','history'):
            v,c=self.rig()
            if flag=='window':v['windows']['live']=1
            elif flag=='incomplete':v['incomplete_requests']=1
            elif flag=='managed':v['managed_audit_observers']=1
            else:v['history_count']=42
            with self.assertRaises(a.m.Stop):a.validate(v,c)
    def test_secret_settings_are_not_exported(self):
        value=a.settings({'smtp_pass':'never-export','jwt_secret':'never-export','sessions_single_per_user':False,'sessions_timebox':'never-export'})
        self.assertNotIn('never-export',json.dumps(value));self.assertNotIn('smtp_pass',value)
    def test_documented_refresh_field_is_not_an_invented_alias(self):
        value=a.settings({'refresh_token_rotation_enabled':True,'security_refresh_token_rotation_enabled':False})
        self.assertIs(value['refresh_token_rotation_enabled'],True)
        self.assertNotIn('security_refresh_token_rotation_enabled',value)
    def test_only_exact_ids_and_no_auth_mutation_query(self):
        ids=a.identifiers();sql=a.query(ids)
        for v in ids.values():self.assertIn(v,sql)
        self.assertNotRegex(sql.lower(),r'\b(insert|update|delete|alter|create)\b')
        self.assertNotIn('user_metadata',sql)

if __name__=='__main__':unittest.main()
