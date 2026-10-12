import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
import jit_diagnose as d


class Reply:
    status = 200
    headers = {}
    def __init__(self, value): self.raw = json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, n): return self.raw[:n]


class Opener:
    def __init__(self, *replies): self.replies=list(replies); self.requests=[]
    def open(self, req, timeout):
        self.requests.append(req)
        value=self.replies.pop(0)
        if isinstance(value, Exception): raise value
        return Reply(value)


class Diagnose(unittest.TestCase):
    def journal(self, opener):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        return d.Journal('synthetic-secret-never-export', Path(temp.name), opener)

    def test_error_redaction(self):
        raw=json.dumps({'message':'secret postgres://x:y@host', 'token':'private', 'code':'PGRST116', 'details':'The result contains 0 rows'}).encode()
        value=d.classify(raw)
        self.assertEqual(value['condition'],'mapping_absent')
        self.assertNotIn('secret',json.dumps(value));self.assertNotIn('private',json.dumps(value))

    def test_unknown_never_echoed(self):
        for value in [{'message':'sbp_SECRET','code':'sbp_SECRET'},['private'],None,'private']:
            self.assertNotIn('private',json.dumps(d.classify(json.dumps(value).encode())))
            self.assertNotIn('sbp_',json.dumps(d.classify(json.dumps(value).encode())))

    def test_non_json_is_not_logged(self):
        self.assertEqual(d.classify(b'<secret>')['condition'],'non_json_response')

    def test_known_conditions(self):
        for message, expected in [('SSL enforcement is required','ssl_required'),('JIT is not enabled','jit_disabled'),
            ('Configuration has not been applied','configuration_not_applied'),('permission denied','permission_denied'),
            ('rate limit exceeded','request_throttled')]:
            self.assertEqual(d.classify(json.dumps({'message':message}).encode())['condition'],expected)

    def test_request_ids_only(self):
        self.assertEqual(d.headers_metadata({'cf-ray':'abc123456789abcd-AMS','authorization':'secret','x-request-id':'secret'}), {'cf-ray':'abc123456789abcd-AMS'})

    def test_denial_phase_and_no_retry(self):
        error=urllib.error.HTTPError('https://secret',406,'secret',{},io.BytesIO(b'{"message":"JIT not enabled"}'))
        opener=Opener(error);j=self.journal(opener)
        with self.assertRaises(d.Rejected) as caught:j.request('grant',d.BASE+'/database/jit')
        self.assertEqual(caught.exception.phase,'grant');self.assertEqual(len(opener.requests),1)
        value=json.loads(next(j.folder.glob('*-result.json')).read_text())
        self.assertEqual(value['http_status'],406);self.assertNotIn('secret',json.dumps(value))

    def test_reads_do_not_mutate(self):
        opener=Opener({'gotrue_id':'fixture'},{'id':d.jit.PROJECT,'status':'ACTIVE_HEALTHY'},
            {'appliedSuccessfully':True,'currentConfig':{'database':True}}, {'state':'disabled','appliedSuccessfully':True},{'items':[]})
        j=self.journal(opener)
        with patch.object(d.jit,'OWNER_HASH',d.hashlib.sha256(b'fixture').hexdigest()):self.assertEqual(j.inspect()['mappings'],0)
        self.assertTrue(all(r.method=='GET' for r in opener.requests))

    def test_other_project_and_new_role_blocked_before_request(self):
        opener=Opener();j=self.journal(opener);j.owner='fixture'
        for path,method,body in [(d.BASE+'/reset','PUT',{}),('/v1/projects/other','GET',None),
            (d.BASE+'/database/jit','PUT',{'user_id':'fixture','roles':[{'role':'superuser','expires_at':int(d.time.time()*1000)+10000}]})]:
            with self.assertRaises(d.Rejected):j.request('blocked',path,method,body)
        self.assertEqual(len(opener.requests),0)

    def test_cannot_take_over_existing_mapping(self):
        opener=Opener({'gotrue_id':'fixture'},{'id':d.jit.PROJECT,'status':'ACTIVE_HEALTHY'},
            {'appliedSuccessfully':True,'currentConfig':{'database':True}}, {'state':'enabled','appliedSuccessfully':True},{'items':[{}]})
        j=self.journal(opener)
        with patch.object(d.jit,'OWNER_HASH',d.hashlib.sha256(b'fixture').hexdigest()):
            with self.assertRaises(d.Rejected):j.inspect()
        self.assertTrue(all(r.method=='GET' for r in opener.requests))

    def test_not_applied_never_grants(self):
        opener=Opener({'state':'enabled','appliedSuccessfully':False},{'state':'enabled','appliedSuccessfully':False})
        j=self.journal(opener);j.owner='fixture'
        with self.assertRaises(d.Rejected) as caught:j.grant()
        self.assertEqual(caught.exception.phase,'enable_applied')
        self.assertEqual(len(opener.requests),2)

    def test_grant_failure_keeps_exact_phase(self):
        error=urllib.error.HTTPError('https://secret',406,'secret',{},io.BytesIO(b'{"message":"mapping not found"}'))
        opener=Opener({'state':'enabled','appliedSuccessfully':True},{'state':'enabled','appliedSuccessfully':True},error)
        j=self.journal(opener);j.owner='fixture'
        with self.assertRaises(d.Rejected) as caught:j.grant()
        self.assertEqual(caught.exception.phase,'role_grant');self.assertEqual(len(opener.requests),3)

    def test_close_checks_effective_state(self):
        opener=Opener({}, {}, {'state':'disabled','appliedSuccessfully':True}, {'items':[]},
            {'appliedSuccessfully':True,'currentConfig':{'database':True}})
        j=self.journal(opener);j.owner='fixture';j.close()
        self.assertEqual([r.method for r in opener.requests],['DELETE','PUT','GET','GET','GET'])
        self.assertTrue(json.loads((j.folder/'closed.json').read_text())['confirmed'])


if __name__=='__main__':unittest.main()
