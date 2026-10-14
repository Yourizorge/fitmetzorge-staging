import unittest
from protocol import transaction

class Connection:
    def __init__(self,fail=()):self.calls=[];self.fail=fail;self.closed=False
    def execute(self,query,parameters=None):
        self.calls.append(query)
        if query in self.fail:raise RuntimeError('synthetic_failure')
        return object()
    def close(self):self.closed=True

class Tests(unittest.TestCase):
    def test_commit_and_no_parameter_logging(self):
        db=Connection();events=[]
        with transaction(lambda:db,events.append,'execute') as session:
            session.execute('select %s',['private-synthetic-value'])
        self.assertEqual(db.calls,['BEGIN','select %s','COMMIT'])
        self.assertNotIn('private-synthetic-value',str(events))
        self.assertNotIn('select %s',str(events))
        self.assertEqual(len({x['call_id'] for x in events}),1)
        self.assertTrue(db.closed)
    def test_sql_failure_rolls_back_once(self):
        db=Connection(['select broken']);events=[]
        with self.assertRaises(RuntimeError):
            with transaction(lambda:db,events.append,'execute') as session:session.execute('select broken')
        self.assertEqual(db.calls,['BEGIN','select broken','ROLLBACK'])
        self.assertFalse(events[3]['confirmed']);self.assertTrue(db.closed)
    def test_domain_failure_rolls_back(self):
        db=Connection()
        with self.assertRaises(ValueError):
            with transaction(lambda:db,None,'execute'):raise ValueError('synthetic')
        self.assertEqual(db.calls,['BEGIN','ROLLBACK']);self.assertTrue(db.closed)
    def test_failed_commit_or_begin_attempts_rollback(self):
        for fault in ('BEGIN','COMMIT'):
            db=Connection([fault]);events=[]
            with self.assertRaises(RuntimeError):
                with transaction(lambda:db,events.append,'execute'):pass
            self.assertEqual(db.calls[-1],'ROLLBACK');self.assertTrue(db.closed)
    def test_failed_rollback_remains_unconfirmed(self):
        db=Connection(['ROLLBACK']);events=[]
        with self.assertRaisesRegex(ValueError,'original'):
            with transaction(lambda:db,events.append,'execute'):raise ValueError('original')
        self.assertFalse(events[-1]['confirmed']);self.assertTrue(db.closed)

if __name__=='__main__':unittest.main()
