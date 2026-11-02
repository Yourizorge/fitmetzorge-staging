"""Lost-response safety contract tests; hosted behavior is not inferred."""
import ast,copy,hashlib,json,pathlib,re,time,types,unittest
from unittest.mock import Mock
from control_recovery import CLOSED,intent,recover

RUN='69000000-0000-4000-8000-000000000099'
EXPIRY='2026-11-02T12:03:00+00:00'

class Tests(unittest.TestCase):
    def test_identity_and_expiry_precede_mutation(self):
        proof,expected=intent(CLOSED,RUN,EXPIRY)
        other=intent(CLOSED,'69000000-0000-4000-8000-000000000098',EXPIRY)[1]
        self.assertNotEqual(expected['config']['proof_hash'],other['config']['proof_hash'])
        self.assertIn(RUN,proof);self.assertEqual(expected['request']['expires_at'],EXPIRY)
        for expiry in ('2026-11-02T12:03:00','invalid'):
            with self.assertRaises(ValueError):intent(CLOSED,RUN,expiry)
        with self.assertRaises(RuntimeError):intent(expected,RUN,EXPIRY)

    def test_all_partial_enable_outcomes_restore_in_four_commands(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        for config in (False,True):
            for request in (False,True):
                state=copy.deepcopy(CLOSED);calls=[]
                if config:state['config']=copy.deepcopy(expected['config'])
                if request:state['request']=copy.deepcopy(expected['request'])
                def query(channel,phase,sql,args=()):
                    calls.append((channel,phase,sql,args))
                    if phase in ('safety_control_before','safety_control_after'):
                        return [{'value':copy.deepcopy(state)}]
                    if 'fmz6e11_request_private' in sql:
                        self.assertEqual(args,[EXPIRY]);state['request']=copy.deepcopy(CLOSED['request'])
                    else:
                        self.assertEqual(args,[expected['config']['proof_hash']]);state['config']=copy.deepcopy(CLOSED['config'])
                    return []
                value=recover(query,CLOSED,expected)
                self.assertTrue(value['original_restored']);self.assertEqual(len(calls),4)
                self.assertEqual(state,CLOSED)

    def test_foreign_value_never_overwritten(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1];state=copy.deepcopy(expected)
        state['config']['proof_hash']='not-this-run';calls=[]
        def query(*args):calls.append(args);return [{'value':state}]
        with self.assertRaisesRegex(RuntimeError,'foreign_state'):recover(query,CLOSED,expected)
        self.assertEqual(len(calls),1)

    def test_failed_after_read_never_claims_restoration(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        def query(channel,phase,sql,args=()):
            if phase=='safety_control_after':raise TimeoutError('not exported')
            return [{'value':expected}]
        with self.assertRaises(TimeoutError):recover(query,CLOSED,expected)

    def test_no_false_success_on_unrestored_state(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        with self.assertRaisesRegex(RuntimeError,'not_restored'):
            recover(lambda *args:[{'value':expected}],CLOSED,expected)


class CurrentFinallyTests(unittest.TestCase):
    def exercise(self,lost_enable=1,*,connect_error=False,old_close_error=False,recovery_error=False,
                 reader_rollback_error=False,save_rebind_error=False):
        from integral_ci import bind_parameters
        from metered_composition import MeteredComposition
        from native_runtime import NativeRuntime
        path=pathlib.Path(__file__).with_name('integral_ci.py')
        tree=ast.parse(path.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Composition')
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='workflow')
        owner=next(n for n in fn.body if isinstance(n,ast.Try) and n.finalbody)
        first=next(i for i,n in enumerate(owner.body) if isinstance(n,ast.ImportFrom) and n.module=='control_recovery')
        last=next(i for i,n in enumerate(owner.body) if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id=='times' for t in n.targets))
        functions=[n for n in fn.body if isinstance(n,ast.FunctionDef) and n.name in ('raw_query','query')]
        body=functions+[ast.Try(body=owner.body[first:last],handlers=[],orelse=[],finalbody=owner.finalbody)]
        source=compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),'exec')
        state=copy.deepcopy(CLOSED);events=[];saved={};enable_calls=[];fresh_calls=[]
        class DatabaseError(Exception):sqlstate=None
        def cursor(rows):return types.SimpleNamespace(description=bool(rows),fetchall=lambda:copy.deepcopy(rows))
        class Connection:
            def __init__(self,name):
                self.name=name;self.dead=False;self.closed=False
                self.info=types.SimpleNamespace(transaction_status=0)
            def execute(connection,sql,args=None):
                events.append((connection.name,'query',sql))
                if connection.dead:raise DatabaseError('private_dead_connection')
                if connection.name=='old':
                    enable_calls.append(sql)
                    key='request' if 'fmz6e11_request_private' in sql else 'config'
                    value=args[0] if key=='request' else hashlib.sha256(args[0].encode()).hexdigest()
                    state[key].update(enabled=True,**{('expires_at' if key=='request' else 'proof_hash'):value})
                    if len(enable_calls)==lost_enable:
                        connection.dead=True;connection.info.transaction_status=4
                        if reader_rollback_error:reader.dead=True;reader.info.transaction_status=1
                        raise DatabaseError('commit_succeeded_response_connection_lost')
                    return cursor([{'id':True}])
                if connection.name=='fresh':
                    fresh_calls.append(sql)
                    if recovery_error:raise DatabaseError('private_recovery_response_lost')
                    if sql.startswith('update'):
                        key='request' if 'fmz6e11_request_private' in sql else 'config'
                        field='expires_at' if key=='request' else 'proof_hash'
                        if state[key][field]==args[0]:state[key]=copy.deepcopy(CLOSED[key])
                        return cursor([])
                return cursor([{'value':copy.deepcopy(state),'expires_at':EXPIRY}])
            def close(connection):
                events.append((connection.name,'close'))
                if connection.name=='old' and old_close_error:raise DatabaseError('private_close_unknown')
                connection.closed=True
        old=Connection('old');fresh=Connection('fresh');reader=Connection('reader')
        def connect(**parameters):
            events.append(('runtime','connect'))
            self.assertEqual(parameters['connect_timeout'],5)
            self.assertEqual(parameters['options'],'-c statement_timeout=5000 -c lock_timeout=1000')
            self.assertTrue(parameters['autocommit'])
            self.assertIsNone(parameters['prepare_threshold'])
            if connect_error:raise DatabaseError('private_connect_failure')
            return fresh
        # Exercise the real NativeRuntime.connect forwarding, with a memory
        # driver and pre-bound synthetic parameters. No TLS/hosted proof claim.
        runtime=object.__new__(NativeRuntime)
        runtime._NativeRuntime__parameters={'connect_timeout':5,'options':'-c statement_timeout=5000 -c lock_timeout=1000'}
        runtime._NativeRuntime__driver=types.SimpleNamespace(connect=Mock(side_effect=connect))
        runtime._NativeRuntime__row_factory=None
        c=MeteredComposition();c.action={'kind':'lifecycle','operation':'workflow'}
        def save(name,value):
            if save_rebind_error and name=='integral-safety-control-connection.json':
                raise OSError('private_receipt_write_failed')
            self.assertNotIn(name,saved);saved[name]=copy.deepcopy(value)
            events.append(('save',name))
        scope=dict(self=c,connections={'setup':old,'reader':reader},runtime=runtime,
            gate=types.SimpleNamespace(save=save),monitor=None,timer=None,process=None,
            enabled=None,controls=None,restored=None,enable_attempted=False,run_id=RUN,
            bind_parameters=bind_parameters,Jsonb=lambda value:value,
            psycopg=types.SimpleNamespace(Error=DatabaseError),re=re,json=json,hashlib=hashlib,time=time)
        with self.assertRaisesRegex(RuntimeError,'ci_sql_unknown'):exec(source,scope)
        runtime._NativeRuntime__driver.connect.assert_called_once()
        self.assertEqual(len(enable_calls),lost_enable)
        self.assertLess(events.index(('old','close')),events.index(('runtime','connect')))
        rollback=saved['integral-safety-rollback.json']['connections'][0]
        self.assertEqual(rollback['channel'],'setup');self.assertTrue(rollback['requested'])
        self.assertFalse(rollback['confirmed'])
        self.assertEqual(rollback['dispatched_commands'],0)
        self.assertEqual(rollback['exception_class'],'BudgetStop')
        self.assertTrue(c.meter.stopped)
        unknown=[event for event in c.meter.events if event['action']=='control_enable' and not event['confirmed']]
        self.assertEqual(len(unknown),1)
        self.assertEqual(unknown[0]['stop_reason'],'workflow_database_command_failed')
        self.assertEqual(c.meter.safety_spent['rollback_setup'],0)
        self.assertFalse(any(event[0]=='old' and len(event)>2 and event[2]=='ROLLBACK' for event in events))
        self.assertNotIn('private_',json.dumps(saved))
        self.assertFalse(saved['integral-protocol-trace.json']['full_chain_admission'])
        return types.SimpleNamespace(state=state,events=events,saved=saved,old=old,fresh=fresh,
            fresh_calls=fresh_calls,meter=c.meter)

    def test_actual_finally_recovers_both_committed_lost_enable_replies_on_fresh_transport(self):
        for position in (1,2):
            with self.subTest(position=position):
                result=self.exercise(position)
                self.assertEqual(result.state,CLOSED);self.assertEqual(len(result.fresh_calls),4)
                self.assertTrue(result.fresh.closed);self.assertTrue(result.old.closed)
                self.assertTrue(result.saved['integral-safety-control-pair.json']['original_restored'])
                self.assertEqual({k:v for k,v in result.meter.safety_spent.items() if k.startswith('control_')},
                    {'control_before':1,'control_compare_restore':2,'control_after':1})

    def test_old_close_unknown_is_recorded_without_retrying_enable_or_rollback(self):
        result=self.exercise(old_close_error=True)
        self.assertEqual(result.state,CLOSED)
        self.assertFalse(result.saved['integral-safety-control-connection.json']['old_closed'])
        self.assertEqual(result.saved['integral-safety-control-connection.json']['old_close_error_class'],'DatabaseError')
        self.assertEqual(result.events.count(('old','close')),1)

    def test_reconnect_failure_emits_no_recovery_queries_and_preserves_unknown(self):
        result=self.exercise(connect_error=True)
        self.assertEqual(result.fresh_calls,[]);self.assertNotEqual(result.state,CLOSED)
        self.assertNotIn('integral-safety-control-pair.json',result.saved)
        self.assertFalse(result.saved['integral-safety-control-connection.json']['fresh_connected'])
        self.assertIn('integral-safety-control-stop.json',result.saved)

    def test_fresh_query_failure_never_reconnects_or_retries_recovery(self):
        result=self.exercise(recovery_error=True)
        self.assertEqual(len(result.fresh_calls),1);self.assertTrue(result.fresh.closed)
        self.assertNotIn('integral-safety-control-pair.json',result.saved)
        self.assertIn('integral-safety-control-stop.json',result.saved)

    def test_lost_reader_rollback_remains_one_metered_unknown_after_control_recovery(self):
        result=self.exercise(reader_rollback_error=True)
        reader=next(row for row in result.saved['integral-safety-rollback.json']['connections'] if row['channel']=='reader')
        self.assertTrue(reader['requested']);self.assertFalse(reader['confirmed'])
        self.assertEqual(reader['dispatched_commands'],1)
        self.assertEqual(result.meter.safety_spent['rollback_reader'],1)
        self.assertEqual(len(result.meter.safety_pending),1)
        self.assertEqual(result.state,CLOSED);self.assertEqual(len(result.fresh_calls),4)

    def test_rebind_receipt_failure_prevents_recovery_dispatch_and_closes_fresh_connection(self):
        result=self.exercise(save_rebind_error=True)
        self.assertEqual(result.fresh_calls,[]);self.assertTrue(result.fresh.closed)
        self.assertNotIn('integral-safety-control-pair.json',result.saved)
        self.assertIn('integral-safety-control-stop.json',result.saved)

if __name__=='__main__':unittest.main()
