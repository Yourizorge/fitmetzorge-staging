import pathlib,sys,tempfile,types,unittest
from unittest.mock import patch
from native_runtime import NativeRuntime

class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ca=pathlib.Path(self.tmp.name)/'synthetic.crt';self.ca.write_text('synthetic test CA')
        self.calls=[]
        self.driver=types.SimpleNamespace(connect=lambda **kw:self.calls.append(kw) or object())
        self.modules=patch.dict(sys.modules,{'psycopg':self.driver,'psycopg.rows':types.SimpleNamespace(dict_row=object())})
        self.modules.start();self.addCleanup(self.modules.stop)
    def parameters(self):
        return {'host':'127.0.0.1','port':5432,'dbname':'postgres','user':'postgres','password':'synthetic-only',
          'sslmode':'verify-full','sslrootcert':str(self.ca),'connect_timeout':5,
          'options':'-c statement_timeout=5000 -c lock_timeout=1000'}
    def test_private_parameters_never_enter_child_context(self):
        r=NativeRuntime(self.parameters(),'http://127.0.0.1:59999',environment='disposable_ci')
        c=r.context({'a_member':'synthetic-id'},{'a_member':'synthetic@example.invalid'})
        self.assertNotIn('password',str(c));self.assertNotIn('synthetic-only',repr(r))
        r.connect();self.assertEqual(len(self.calls),1)
        self.assertEqual(self.calls[0]['sslmode'],'verify-full')
        self.assertTrue(self.calls[0]['autocommit']);self.assertIsNone(self.calls[0]['prepare_threshold'])
    def test_fail_closed_modes_tls_and_limits(self):
        changes=[('sslmode','require'),('sslrootcert','absent'),('connect_timeout',10),('dbname','other'),('host','example.com')]
        for key,value in changes:
            with self.subTest(key=key):
                p=self.parameters();p[key]=value
                with self.assertRaises(ValueError):NativeRuntime(p,'http://127.0.0.1:59999',environment='disposable_ci')
        self.assertEqual(self.calls,[])
    def test_staging_must_use_existing_dashboard_validator(self):
        def validator(connect,token,ca):raise ValueError('dashboard_connect_binding')
        with self.assertRaisesRegex(ValueError,'dashboard_connect_binding'):
            NativeRuntime.staging({},'synthetic',self.ca,validator)
        self.assertEqual(self.calls,[])
    def test_explicit_staging_session_options_without_readonly_leak(self):
        p=self.parameters();p.update(host='aws-0-eu-test-1.pooler.supabase.com',user='postgres.mokxyyullfhkfalopbzd',
          options='-c jit=true -c statement_timeout=5000 -c lock_timeout=1000')
        r=NativeRuntime(p,'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',environment='staging')
        r.connect();self.assertNotIn('default_transaction_read_only',self.calls[0]['options'])
        for key,value in [('port',6543),('user','postgres'),('options','-c jit=true')]:
            q={**p,key:value}
            with self.assertRaises(ValueError):NativeRuntime(q,r.auth_base,environment='staging')

if __name__=='__main__':unittest.main()
