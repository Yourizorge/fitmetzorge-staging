"""Pure in-memory final sequencing tests: no PostgreSQL/CLI/hosted execution."""
import copy,types,unittest
from unittest.mock import patch
import integral_io,lifecycle_gates as gates
from integral_ci import Composition,bind_parameters
from sql_protocol import statements

SCHEMAS=['fmz6e11_guard_'+'1'*32,'fmz6e11_am_'+'1'*32]
ABSENCE=dict.fromkeys(('temporary_schemas','sessions','refresh_tokens','windows','workspaces',
    'participants','all_test_windows','all_test_workspaces','all_test_participants',
    'all_registered_sessions','all_registered_refresh_tokens'),0)
ACCESS=dict.fromkeys(('database_ok','role_ok','pg17','ssl','registered','private_functions_safe'),True)
MIGRATIONS=[dict(version=str(i),name='synthetic',sql_sha='a'*64) for i in range(44)]+[
    dict(version='20261018070231',name='synthetic',sql_sha='b'*64)]

def metadata(stage):
    return dict(access=ACCESS.copy(),migrations=copy.deepcopy(MIGRATIONS),
        catalog={'functions':{'protected':'same'},'m44':{'current':'ignored here; stream-bound'}},
        absence={**ABSENCE,'temporary_schemas':2 if stage=='pre' else 0},
        temporary_schema_names=sorted(SCHEMAS) if stage=='pre' else [],
        readonly=True,statement_timeout='5s',lock_timeout='1s')

class FinalGatesTests(unittest.TestCase):
    def setUp(self):
        self.c=Composition(runtime=types.SimpleNamespace(environment='disposable_ci'))
        self.c.fixture_context.update(temporary_schemas=SCHEMAS,window='1'*32)
        self.c.gate_baseline={'migrations':MIGRATIONS,'catalog':metadata('pre')['catalog']}
        self.saved={};self.gate=types.SimpleNamespace(save=lambda n,v:self.saved.update({n:v}),sources='candidate')
        self.ids={'a_member':'a','a_trainer':'b','b_member':'c'}
    def test_final_is_one_read_only_statement_and_parameters_stay_separate(self):
        self.assertEqual([s['kind'] for s in statements(gates.FINAL)],['SelectStmt'])
        pre=gates.final_parameters(self.ids,self.c.fixture_context,'pre')
        post=gates.final_parameters(self.ids,self.c.fixture_context,'post')
        self.assertEqual(pre[0],SCHEMAS);self.assertEqual(post[0],[])
        self.assertEqual(post[3],SCHEMAS)
        query,params=bind_parameters(gates.FINAL,pre)
        self.assertNotIn('$',query)
        self.assertIn(SCHEMAS,params)
        self.assertIn('f.nspname<>all',query)
    def test_exact_schemas_not_prefix_exclusion(self):
        for schemas in ([],SCHEMAS[:1],SCHEMAS*2,[SCHEMAS[0],SCHEMAS[0]],
                        [SCHEMAS[0],'auth'],[SCHEMAS[0],'fmz6e11_am_'+'2'*32]):
            with self.assertRaises(ValueError):
                gates.final_parameters(self.ids,{'temporary_schemas':schemas,'window':'x'},'pre')
    def test_pre_keeps_only_expected_objects_and_post_requires_absence(self):
        for stage in ('pre','post'):
            value=metadata(stage);gates.check_final(value,self.c.gate_baseline,SCHEMAS,stage)
            for field in ABSENCE:
                bad=copy.deepcopy(value);bad['absence'][field]+=1
                with self.assertRaises(ValueError):gates.check_final(bad,self.c.gate_baseline,SCHEMAS,stage)
            for field in ('readonly','statement_timeout','lock_timeout'):
                bad=copy.deepcopy(value);bad[field]='wrong'
                with self.assertRaises(ValueError):gates.check_final(bad,self.c.gate_baseline,SCHEMAS,stage)
            bad=copy.deepcopy(value);bad['catalog']['functions']['protected']='changed'
            with self.assertRaisesRegex(ValueError,'drift'):gates.check_final(bad,self.c.gate_baseline,SCHEMAS,stage)
    def exercise(self,stage,wal=0,history_error=None):
        c=self.c;seen=[];value=metadata(stage)
        def query(phase,text,args=()):
            c.before_sql(phase,text);seen.append(phase);c.after_sql(phase,text)
            if phase.endswith('_readonly'):return [{'readonly':True}]
            return [{'value':value}]
        class IO:
            def __init__(self,query):self.query=query
            def start(self):
                self.query('reader','io_bind','SELECT 1')
                self.query('reader','io_sample','SELECT 1')
            def bind(self,text,args,*,read_only=False):
                if read_only is not True:raise AssertionError('metadata must be zero-WAL bound')
                self.query('reader','io_bind','SELECT 1')
                self.query('reader','io_sample','SELECT 1')
                return 'qid'
            def executed(self,qid):pass
            def close(self):
                self.query('reader','io_sample','SELECT 1')
                self.query('reader','io_closing_witness','SELECT 1')
                return {'last_pair':{'own_wal_bytes':wal},'closing_wal_bytes':0}
        with patch.object(integral_io,'QueryIO',IO),patch('history_pin.validate',side_effect=history_error) as history:
            c.final_metadata(self.gate,self.ids,stage,query)
            history.assert_called_once_with(MIGRATIONS,'disposable_ci','candidate')
        return seen
    def test_pre11_post9_and_total_final97(self):
        self.assertEqual(len(self.exercise('pre')),11)
        self.assertTrue(self.c.final_pre_complete)
        self.assertIsNone(self.c.closing_receipt)
        self.assertFalse(self.c.final_post_complete)
        self.assertEqual(len(self.exercise('post')),9)
        self.assertTrue(self.c.final_post_complete)
        self.assertTrue(self.c.commands[-1]['final_cleanup_validated'])
        self.assertTrue(next(r for r in self.c.commands if r['phase']=='gates_final_post_metadata')['temporary_absence_validated'])
        self.assertEqual(41+11+36+9,97)
        self.assertEqual(self.saved['integral-gates-after_cleanup.json']['catalog_excluded_schemas'],[])
    def test_own_wal_never_confirms_post_or_saves_pass(self):
        with self.assertRaisesRegex(ValueError,'io_read_wal'):self.exercise('post',wal=1)
        self.assertFalse(self.c.final_post_complete)
        self.assertNotIn('integral-gates-after_cleanup.json',self.saved)
        self.assertNotIn('final_cleanup_validated',self.c.commands[-1])
        # Failed IO is still NO_GO; it cannot make an already confirmed absent
        # object present again or authorize repeating the removal.
        self.assertTrue(next(r for r in self.c.commands if r['phase']=='gates_final_post_metadata')['temporary_absence_validated'])
    def test_history_pin_failure_never_confirms_post(self):
        with self.assertRaisesRegex(ValueError,'historical_migration_drift'):
            self.exercise('post',history_error=ValueError('historical_migration_drift'))
        self.assertFalse(self.c.final_post_complete)
        self.assertNotIn('integral-gates-after_cleanup.json',self.saved)
        self.assertFalse(any(r.get('temporary_absence_validated') for r in self.c.commands))
    def test_one_final_stream_and_no_stream_in_post(self):
        connection=types.SimpleNamespace(info=types.SimpleNamespace(transaction_status=0),close=lambda:None)
        self.c.runtime.connect=lambda:connection
        stream={'protocol_commands':41,'tables':[],'protected_equal':True}
        def metadata_only(gate,ids,stage,query):
            if stage=='pre':self.c.final_pre_complete=True
            else:self.c.final_post_complete=True
        with patch('integral_stream.run',return_value=stream) as full,patch.object(self.c,'final_metadata',side_effect=metadata_only):
            self.c.preservation(self.gate,self.ids,'after_cleanup')
            self.c.final_dry_complete=True
            self.c.preservation(self.gate,self.ids,'final_post')
            self.assertEqual(full.call_count,1)
            with self.assertRaisesRegex(RuntimeError,'sequence'):self.c.preservation(self.gate,self.ids,'after_cleanup')
    def test_final_dry_once_before_closure_intent(self):
        from cli_envelope import local
        receipt=local(dict(complete=True,protocol_commands=2,numeric_protocol_coverage=True,
                          observer_commands=[{'confirmed':True}]*8,dry_run=True),'final')
        calls=[]
        def cli(*args,**kwargs):calls.append((args,kwargs));return 'empty'
        self.gate.cli=cli;self.gate.cli_protocol=[{}, {},receipt]
        with self.assertRaisesRegex(RuntimeError,'sequence'):self.c.finalize(self.gate,{})
        self.c.final_pre_complete=True
        self.assertEqual(self.c.finalize(self.gate,{}),'empty')
        self.assertEqual(calls[0][1]['timeout'],45)
        self.assertIsNone(self.c.closing_receipt)
        self.assertTrue(self.c.final_dry_complete)
        with self.assertRaisesRegex(RuntimeError,'sequence'):self.c.finalize(self.gate,{})
        with self.assertRaisesRegex(RuntimeError,'post_required'):self.c.close_receipt(self.gate,{})
        self.assertEqual(len(calls),1)
    def test_existing_metered_hook_charges36_at_dry_not_closure(self):
        from metered_composition import MeteredComposition
        from cli_envelope import local
        with patch('metered_composition.scenario_source.capture',return_value={'workflow_actions':[]}):
            c=MeteredComposition()
        c.final_pre_complete=True
        final=local(dict(complete=True,protocol_commands=2,numeric_protocol_coverage=True,
                         observer_commands=[{'confirmed':True}]*8,dry_run=True),'final')
        self.gate.cli_protocol=[{}, {},final]
        self.gate.cli=lambda *args,**kw:'empty'
        c.finalize(self.gate,{})
        self.assertEqual(c.meter.used,36)
        self.assertEqual(c.meter.phases['final'],36)
        self.assertIsNone(c.meter.pending)
        self.assertIsNone(c.closing_receipt)

if __name__=='__main__':unittest.main()
