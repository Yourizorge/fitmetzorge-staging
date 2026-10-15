import json,types,unittest
from browser_evidence import result

class Tests(unittest.TestCase):
    def test_success(self):
        p=types.SimpleNamespace(stdout='{"status":"PASS","checks":80}',stderr='',returncode=0)
        self.assertEqual(result(p),{'status':'PASS','checks':80})
    def test_named_failure(self):
        p=types.SimpleNamespace(stdout='',stderr=json.dumps({'status':'FAIL','error':'ordinary_missing_source: keyboard_enters_panel'}),returncode=1)
        self.assertEqual(result(p)['stage'],'ordinary_missing_source')
        self.assertEqual(result(p)['error'],'keyboard_enters_panel')
    def test_structured_no_go_is_not_lost(self):
        p=types.SimpleNamespace(stdout='{"status":"NO_GO","stage":"real_auth","checks":62,"error":"logout_unconfirmed"}',stderr='',returncode=2)
        self.assertEqual(result(p)['stage'],'real_auth')
        self.assertEqual(result(p)['status'],'NO_GO')
    def test_timeout_without_log(self):
        p=types.SimpleNamespace(stdout='',stderr=json.dumps({'error':'member_settings: locator.waitFor: Timeout 30000ms exceeded.\nprivate call log'}),returncode=1)
        self.assertEqual(result(p)['error'],'browser_timeout')
        self.assertNotIn('private',json.dumps(result(p)))
    def test_arbitrary_output_never_retained(self):
        for output in ('secret@example.invalid','https://private.invalid?token=secret','not-json'):
            p=types.SimpleNamespace(stdout='',stderr=output,returncode=1)
            self.assertNotIn(output,json.dumps(result(p)))
    def test_arbitrary_detail_never_retained(self):
        p=types.SimpleNamespace(stdout='',stderr=json.dumps({'error':'login: private password=secret'}),returncode=1)
        self.assertEqual(result(p)['stage'],'login')
        self.assertNotIn('secret',json.dumps(result(p)))
    def test_malformed(self):
        for value in ({'error':None},[],{'error':123},{'error':'login: '}):
            p=types.SimpleNamespace(stdout='',stderr=json.dumps(value),returncode=1)
            self.assertEqual(result(p)['status'],'FAIL')
if __name__=='__main__':unittest.main()
