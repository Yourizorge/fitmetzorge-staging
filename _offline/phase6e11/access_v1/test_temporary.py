import contextlib,io,json,os,pathlib,tempfile,unittest
from unittest.mock import patch
import temporary
class Tests(unittest.TestCase):
    def run_metadata_case(self,readonly='on',client_tls=True):
        seen=[]
        class DB:
            client_tls_verified=client_tls
            terminal_count=0
            queries=0
            bytes_received=0
            def query(self,sql,timeout):
                seen.append(sql);self.queries+=1
                if sql==temporary.META_SQL:
                    self.terminal_count=1
                    return [[json.dumps({'database':'postgres','pg_version_num':'170006',
                        'read_only':readonly,'ssl':False})]]
                self.terminal_count=0
                return []
            def close(self):seen.append('closed')
        with tempfile.TemporaryDirectory() as path,patch.object(temporary,'issue_readonly',return_value={
            'role':'cli_login_supabase_read_only_user','password':'synthetic-only','ttl_seconds':300}),patch.object(
            temporary,'TemporaryReadOnly',return_value=DB()),contextlib.redirect_stdout(io.StringIO()):
            ok=temporary.check(pathlib.Path(path))
            result=json.loads((pathlib.Path(path)/'temporary-connection.json').read_text())
        return ok,result,seen
    def test_explicit_readonly_and_upstream_tls_are_separate(self):
        ok,result,seen=self.run_metadata_case()
        self.assertTrue(ok)
        self.assertEqual(seen,['begin read only',temporary.META_SQL,'rollback','closed'])
        self.assertFalse(result['metadata']['ssl'])
        self.assertTrue(result['client_tls_verified'])
        self.assertEqual(result['metadata_stream_terminal_count'],1)
    def test_failed_metadata_is_retained_without_secret(self):
        ok,result,seen=self.run_metadata_case(readonly='off')
        self.assertFalse(ok)
        self.assertEqual(result['metadata']['read_only'],'off')
        self.assertEqual(seen[-1],'closed')
        self.assertNotIn('synthetic-only',json.dumps(result))
    def test_upstream_ssl_cannot_replace_verified_client_tls(self):
        ok,result,_=self.run_metadata_case(client_tls=False)
        self.assertFalse(ok)
        self.assertEqual(result['status'],'NO_GO')
    def test_rejects_wrong_role_before_reading_secret_or_ca(self):
        with self.assertRaisesRegex(temporary.Stop,"unexpected_managed_login_role"):
            temporary.parameters("postgres","synthetic",pathlib.Path("absent"))
    def test_missing_credential(self):
        with self.assertRaisesRegex(temporary.Stop,"temporary_credential_missing"):
            temporary.parameters("cli_login_supabase_read_only_user","",pathlib.Path("absent"))
    def test_changed_ca(self):
        with tempfile.TemporaryDirectory() as p:
            ca=pathlib.Path(p)/"ca";ca.write_bytes(b"synthetic")
            with self.assertRaisesRegex(temporary.Stop,"ca_changed"):
                temporary.parameters("cli_login_supabase_read_only_user","synthetic",ca)
    def test_tls_parameters_are_strict_and_project_bound(self):
        class CA:
            def read_bytes(self):return b"synthetic"
            def resolve(self):return pathlib.Path("synthetic-ca")
        with patch.object(temporary,"CA_SHA",temporary.hashlib.sha256(b"synthetic").hexdigest()),patch.dict(os.environ,{},clear=True):
            p=temporary.parameters("cli_login_supabase_read_only_user","synthetic",CA())
        self.assertEqual(p["sslmode"],"verify-full")
        self.assertEqual(p["user"],"cli_login_supabase_read_only_user.mokxyyullfhkfalopbzd")
        self.assertEqual(p["port"],"5432")
        self.assertIn("default_transaction_read_only=on",p["options"])
    def test_environment_fallback_denied(self):
        class CA:
            def read_bytes(self):return b"synthetic"
        with patch.object(temporary,"CA_SHA",temporary.hashlib.sha256(b"synthetic").hexdigest()),patch.dict(os.environ,{"PGPASSWORD":"synthetic"}):
            with self.assertRaisesRegex(temporary.Stop,"implicit_pg_environment"):
                temporary.parameters("cli_login_supabase_read_only_user","synthetic",CA())
if __name__=="__main__":unittest.main()
