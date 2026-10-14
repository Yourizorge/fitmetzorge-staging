import types,unittest,uuid
from registered_runner import IdentitySession,execute
from native_runtime import ALIASES

class Connection:
    def __init__(self):self.calls=[];self.info=types.SimpleNamespace(transaction_status=0);self.closed=False
    def execute(self,q,args=None):
        self.calls.append((q,args))
        return types.SimpleNamespace(description=True,fetchall=lambda:[])
    def close(self):self.closed=True

class Tests(unittest.TestCase):
    def setup_session(self):
        db=Connection();runtime=types.SimpleNamespace(connect=lambda:db)
        ids={r:str(uuid.uuid4()) for r in ALIASES}
        c=types.SimpleNamespace(before_sql=lambda *a:None,after_sql=lambda *a:None)
        return IdentitySession(runtime,c,str(uuid.uuid4()),ids),db,ids
    def test_exact_query_and_exact_identity(self):
        s,db,ids=self.setup_session()
        s.query(s.lock,[ids['a_member'],ALIASES['a_member']])
        self.assertEqual(len(db.calls),1)
        self.assertNotIn(ids['a_member'],db.calls[0][0])
        s.close();self.assertTrue(db.closed)
    def test_comment_prefix_cannot_authorize_appended_sql(self):
        s,db,ids=self.setup_session()
        with self.assertRaises(ValueError):s.query(s.lock+'; select 1',[ids['a_member'],ALIASES['a_member']])
        self.assertEqual(db.calls,[])
    def test_swapped_identity_or_guard_blocked_before_connection(self):
        s,db,ids=self.setup_session()
        for q,args in [(s.lock,[ids['a_member'],ALIASES['b_member']]),(s.attest,['unrelated.guard()']),('BEGIN',['secret'])]:
            with self.assertRaises(ValueError):s.query(q,args)
        self.assertIsNone(s.connection);self.assertEqual(db.calls,[])
    def test_open_transaction_rollback_counted_before_close(self):
        s,db,ids=self.setup_session();s.query('BEGIN',[]);db.info.transaction_status=2
        s.close();self.assertEqual([x[0] for x in db.calls],['BEGIN','ROLLBACK']);self.assertTrue(db.closed)
    def test_worker_not_started_without_registered_context(self):
        with self.assertRaises(ValueError):execute(None,None,None,{'mode':'browser','environment':'staging'})
        with self.assertRaises(ValueError):execute(None,None,None,{'mode':'registered_synthetic','environment':'staging'})

if __name__=='__main__':unittest.main()
