import base64,json,time,unittest
from registration_transport import VerifiedAuth,NoRedirect,AUTH,Candidate
from store import Denied

ID=lambda n:'79000000-0000-4000-8000-'+str(n).zfill(12)
def token(**more):
    c={'sub':ID(1),'session_id':ID(2),'role':'authenticated','aud':'authenticated','iss':AUTH,'exp':time.time()+60,**more}
    return 'synthetic.'+base64.urlsafe_b64encode(json.dumps(c).encode()).decode().rstrip('=')+'.synthetic'

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.auth=VerifiedAuth('synthetic-publishable',[ID(1)],lambda:self.calls.append('lease'),lambda t:{'id':ID(1)})
    def test_server_verified_identity_and_exact_session(self):
        self.assertEqual(self.auth.verify(token()),{'sub':ID(1),'session_id':ID(2)})
        self.assertEqual(self.calls,['lease'])
    def test_wrong_issuer_role_audience_subject_expiry(self):
        for change in ({'iss':'https://other.invalid/auth/v1'},{'role':'service_role'},{'aud':'other'},{'sub':ID(3)},{'exp':0},{'session_id':None}):
            with self.assertRaises(Denied):self.auth.verify(token(**change))
    def test_user_metadata_cannot_grant_access(self):
        self.auth.allowed=frozenset([ID(3)])
        with self.assertRaises(Denied):self.auth.verify(token(user_metadata={'role':'member','allowed':True}))
    def test_failed_verification_cannot_use_decoded_claims(self):
        def denied(_):raise Denied('synthetic_denial')
        self.auth._request=denied
        with self.assertRaisesRegex(Denied,'synthetic_denial'):self.auth.verify(token())
    def test_expired_lease_precedes_http(self):
        def expired():raise Denied('release_expired')
        self.auth.lease=expired
        self.auth._request=lambda _:self.fail('HTTP must not start')
        with self.assertRaisesRegex(Denied,'release_expired'):self.auth.verify(token())
    def test_redirects_never_forward_token(self):
        with self.assertRaisesRegex(Denied,'redirect'):NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_secret_not_in_repr_and_close_clears_key(self):
        self.assertNotIn('synthetic-publishable',repr(self.auth));self.auth.close();self.assertIsNone(self.auth._key)
    def test_disposable_factory_cannot_use_staging_runtime_or_endpoint(self):
        import types
        from unittest.mock import patch
        with patch.dict('os.environ',{'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging'}):
            with self.assertRaisesRegex(Denied,'disposable_transport_boundary'):
                Candidate.disposable(types.SimpleNamespace(environment='staging',auth_base=AUTH),None,{}, {},lambda e:None)
            with self.assertRaisesRegex(Denied,'disposable_auth_boundary'):
                VerifiedAuth.disposable([],lambda:None,types.SimpleNamespace(url=AUTH))
    def test_disposable_factory_denied_outside_exact_ci(self):
        import types
        from unittest.mock import patch
        with patch.dict('os.environ',{'GITHUB_REPOSITORY':'elsewhere'}):
            with self.assertRaises(Denied):Candidate.disposable(None,None,{}, {},None)
            with self.assertRaises(Denied):VerifiedAuth.disposable([],lambda:None,types.SimpleNamespace(url='http://127.0.0.1:59999'))
    def test_minimal_candidate_never_enables_local_workout_lifecycle(self):
        import types
        from unittest.mock import patch
        from registration_store import RegistrationStore
        self.assertFalse(object.__new__(RegistrationStore).journey)
        self.assertFalse(object.__new__(Candidate).journey)
        runtime=types.SimpleNamespace(environment='disposable_ci',auth_base='http://127.0.0.1:59999')
        auth=types.SimpleNamespace(url=runtime.auth_base)
        with patch.dict('os.environ',{'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging'}):
            candidate=Candidate.disposable(runtime,auth,{ID(4):ID(1)},{'a':ID(1),'trainer':ID(2),'b':ID(3)},lambda e:None)
        self.assertFalse(candidate.journey)
        self.assertFalse(candidate.full_day21)

if __name__=='__main__':unittest.main()
