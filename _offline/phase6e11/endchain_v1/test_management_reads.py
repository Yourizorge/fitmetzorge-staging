import io,json,time,types,unittest
from management_reads import read

class Reads(unittest.TestCase):
    def journal(self,body):
        self.requests=[];self.saved={}
        def opened(request,timeout):
            self.requests.append((request,timeout))
            if isinstance(body,Exception):raise body
            result=io.BytesIO(body);result.status=200;return result
        return types.SimpleNamespace(calls=0,deadline=time.monotonic()+5,token='private-synthetic-value',
                                     opener=types.SimpleNamespace(open=opened))
    def save(self,name,value):self.saved[name]=value
    def test_secrets_only_returned_in_memory_and_both_reads_counted(self):
        j=self.journal(b'{"api_key":"private-synthetic-value"}')
        self.assertEqual(read(j,'api_keys',self.save)['api_key'],'private-synthetic-value')
        read(j,'auth_health',self.save,anon='synthetic-public-key')
        self.assertEqual(j.calls,2);self.assertEqual(len(self.saved),4)
        self.assertNotIn('private-synthetic-value',json.dumps(self.saved))
        self.assertEqual([x[1] for x in self.requests],[5,5])
    def test_failure_is_counted_no_response_or_retry(self):
        j=self.journal(TimeoutError('private-synthetic-value'))
        with self.assertRaisesRegex(ValueError,'transport_or_format'):read(j,'api_keys',self.save)
        self.assertEqual(j.calls,1);self.assertEqual(len(self.requests),1)
        self.assertNotIn('private-synthetic-value',json.dumps(self.saved))
        self.assertEqual(next(v for k,v in self.saved.items() if k.endswith('result.json'))['error_class'],'TimeoutError')
    def test_budget_and_scope_fail_before_network(self):
        j=self.journal(b'{}');j.calls=24
        with self.assertRaises(ValueError):read(j,'api_keys',self.save)
        j.calls=0
        with self.assertRaises(ValueError):read(j,'other_project',self.save)
        self.assertEqual(self.requests,[])

if __name__=='__main__':unittest.main()
