import io,json,subprocess,types,unittest,uuid
from unittest.mock import Mock,patch
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

class CompletionTests(unittest.TestCase):
    def run_worker(self,*,checks=18,exit_code=0,wait_error=None,removed=True):
        saved={};events=[]
        def save(name,value):
            self.assertNotIn(name,saved)
            saved[name]=json.loads(json.dumps(value))
        gate=types.SimpleNamespace(save=save)
        composition=types.SimpleNamespace(runner='unused.mjs',commands=[],
            confirm_closure=Mock(side_effect=lambda *args:events.append('confirm')),abort=Mock())
        lifecycle=types.SimpleNamespace(removed=removed,close_temporary=Mock(),dispatch=Mock())
        request={'op':'complete','result':{'checks':checks}}
        worker=Mock(stdin=io.StringIO(),stdout=io.StringIO(json.dumps(request)+'\n'),
            returncode=None)
        def wait(timeout):
            self.assertEqual(timeout,5)
            events.append('wait')
            if wait_error:raise wait_error
            worker.returncode=exit_code
            return exit_code
        worker.wait.side_effect=wait
        worker.poll.side_effect=lambda:worker.returncode
        worker.kill.side_effect=lambda:setattr(worker,'returncode',-9)
        timer=Mock()
        config={'mode':'registered_synthetic','environment':'disposable_ci',
            'identityBinding':{'preexisting':True},'admin':'private-admin','anon':'private-anon'}
        result=None;error=None
        with patch('registered_runner.subprocess.Popen',return_value=worker), \
             patch('registered_runner.threading.Timer',return_value=timer) as make_timer, \
             patch('registered_runner.time.monotonic',return_value=0):
            try:result=execute(gate,composition,lifecycle,config)
            except Exception as caught:error=caught
        make_timer.assert_called_once_with(180,worker.kill)
        timer.start.assert_called_once_with();timer.cancel.assert_called_once_with()
        self.assertIsNone(config['admin']);self.assertIsNone(config['anon'])
        for private in ('private-admin','private-anon'):
            self.assertNotIn(private,json.dumps(saved))
        return types.SimpleNamespace(saved=saved,composition=composition,lifecycle=lifecycle,
            worker=worker,result=result,error=error,events=events)

    def assert_incomplete(self,run):
        self.assertIsNotNone(run.error)
        self.assertFalse(run.saved['registered-worker-terminal.json']['complete'])
        self.assertFalse(run.saved['registered-incomplete-protocol-trace.json']['complete'])
        run.composition.confirm_closure.assert_not_called()
        run.composition.abort.assert_called_once_with('registered_worker_incomplete')
        self.assertNotIn('integral-complete-protocol-trace.json',run.saved)

    def test_complete_payload_requires_successful_child_exit(self):
        run=self.run_worker(exit_code=1)
        self.assert_incomplete(run)
        self.assertEqual(str(run.error),'registered_worker_incomplete')
        run.lifecycle.close_temporary.assert_not_called()

    def test_complete_payload_then_wait_timeout_is_incomplete(self):
        failure=subprocess.TimeoutExpired('node',5)
        run=self.run_worker(wait_error=failure)
        self.assert_incomplete(run)
        self.assertIs(run.error,failure)
        run.worker.kill.assert_called_once_with()
        run.worker.communicate.assert_called_once_with(timeout=5)

    def test_complete_payload_requires_all_checks(self):
        run=self.run_worker(checks=17)
        self.assert_incomplete(run)
        self.assertEqual(str(run.error),'registered_worker_incomplete')
        run.lifecycle.close_temporary.assert_not_called()

    def test_complete_payload_requires_confirmed_removal(self):
        run=self.run_worker(removed=False)
        self.assert_incomplete(run)
        self.assertEqual(str(run.error),'registered_worker_incomplete')
        run.lifecycle.close_temporary.assert_called_once_with()

    def test_success_confirms_after_wait(self):
        run=self.run_worker()
        self.assertIsNone(run.error);self.assertEqual(run.result,{'checks':18})
        run.composition.confirm_closure.assert_called_once()
        self.assertEqual(run.events,['wait','confirm'])
        run.composition.abort.assert_not_called()
        self.assertTrue(run.saved['registered-worker-terminal.json']['complete'])
        self.assertNotIn('registered-incomplete-protocol-trace.json',run.saved)
        run.lifecycle.close_temporary.assert_not_called()

if __name__=='__main__':unittest.main()
