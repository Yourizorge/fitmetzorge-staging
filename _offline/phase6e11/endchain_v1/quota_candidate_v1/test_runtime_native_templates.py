"""Static template analysis only. No query, import of inspected code or live proof."""
import argparse
import ast
import json
import pathlib
import sys
import tempfile
import unittest

from quota_candidate_v1 import runtime_native_templates as t

ROOT=None


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.runtime=self.root/t.OWN_PREFIX
        self.runtime.mkdir(parents=True)
        self.name=t.PREFIX+'sample.py'

    def extract(self, text, *, name=None):
        name=name or self.name
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        model=t.SourceCatalog(self.root,self.runtime)
        module=model.module(name)
        model.block(module['tree'].body,name,'',(),{})
        return model

    def test_comment_and_sql_string_semicolon_do_not_create_commands(self):
        model=self.extract('''
# query('reader','fake','DROP TABLE public.never')
def run():
    query('reader','read',"select ';'::text")
''')
        self.assertEqual(len(model.sites),1)
        self.assertEqual(model.sites[0]['protocol_commands'],1)
        self.assertNotIn("select ';'",json.dumps(model.sites))

    def test_resolves_only_static_literals_without_importing_inspected_code(self):
        model=self.extract('''
raise RuntimeError('must_never_execute')
SQL='SELECT 1'
def run():
    query('reader','read',SQL)
''')
        # The unreachable function still has a source definition, but the top-level
        # raise must not execute. Analyze the named definition independently.
        node=next(n for n in model.module(self.name)['tree'].body if isinstance(n,ast.FunctionDef))
        model.block([node],self.name,'',(),{})
        self.assertEqual(model.sites[0]['sql_sha256'],t.sha(b'SELECT 1'))

    def test_dynamic_sql_and_parameter_shadowing_remain_unknown(self):
        model=self.extract('''
SQL='SELECT 1'
def run(SQL):
    query('reader','read',SQL)
''')
        row=model.sites[0]
        self.assertIsNone(row['protocol_commands'])
        self.assertIsNone(row['sql_sha256'])
        self.assertEqual(row['unresolved_inputs'],['SQL'])

    def test_phase_text_callback_is_not_misread_as_channel_phase_sql(self):
        model=self.extract('''
def run():
    def query(phase,text,args=()):
        return connection.execute(text,args)
    query('metadata','SELECT 1',[])
''')
        row=next(x for x in model.sites if x['symbol']=='run')
        self.assertIsNone(row['channel'])
        self.assertEqual(row['phase'],'metadata')
        self.assertEqual(row['sql_sha256'],t.sha(b'SELECT 1'))

    def test_cold_bind_after_early_return_has_negative_branch_condition(self):
        model=self.extract('''
def bind(cached):
    if cached:
        return 7
    query('reader','io_bind','EXPLAIN SELECT 1')
''')
        self.assertEqual(model.sites[0]['scope'][0]['branch'],'false_after_terminal_true_branch')

    def test_try_except_finally_are_distinct_not_one_observed_sequence(self):
        model=self.extract('''
def run():
    try:
        query('reader','before','BEGIN READ ONLY')
    except Exception:
        query('reader','failure','SELECT 1')
    finally:
        query('reader','close','ROLLBACK')
''')
        self.assertEqual([x['scope'][0]['branch'] for x in model.sites],['body','except_0','finally'])
        self.assertEqual([x['transaction_boundary'] for x in model.sites],
            ['TransactionStmt',None,'TransactionStmt'])
        self.assertTrue(all(x['execution_observed'] is False for x in model.sites))

    def test_branch_assignment_is_not_reused_as_unconditional_sql(self):
        model=self.extract('''
def run(flag):
    text='SELECT 1'
    if flag:
        text='SELECT 2'
    query('reader','read',text)
''')
        self.assertTrue(model.sites[0]['dynamic_sql'])
        self.assertIsNone(model.sites[0]['sql_sha256'])

    def test_multiple_statements_counted_by_pg17_parser(self):
        model=self.extract("def run():\n    query('reader','x','BEGIN READ ONLY; SELECT 1; ROLLBACK')\n")
        self.assertEqual(model.sites[0]['protocol_commands'],3)

    def test_historical_match_never_claims_order_or_execution_equivalence(self):
        model=self.extract("def run():\n    query('reader','x','SELECT 1')\n")
        digest=model.sites[0]['statements'][0]['sha256']
        rows=[dict(id='old1',action='read',kind='native',sql_sha256=digest),
            dict(id='old2',action='other',kind='native',sql_sha256='f'*64)]
        result=t.reconcile_historical(rows,model.sites)
        self.assertEqual(result[0]['classification'],'exact_template_hash_only')
        self.assertEqual(result[1]['classification'],'unresolved_template_or_binding')
        self.assertTrue(all(not x['ordered_execution_equivalence_proven'] for x in result))

    def test_current_actual_sources_preserve_unknowns_and_queryio_calls(self):
        if ROOT is None:self.skipTest('explicit --source-root required for real source inspection')
        value=t.export_native_templates(ROOT,runtime_dir=t.HERE)
        sites=value['sites']
        start=[s for s in sites if s['source']==t.PREFIX+'integral_io.py' and s['symbol']=='QueryIO.start']
        self.assertEqual(start[0]['phase'],'io_bind')
        self.assertEqual(start[0]['protocol_commands'],1)
        self.assertTrue(any(s['callee']=='self.sample' for s in start))
        self.assertTrue(any(s['symbol']=='WorkflowBridge.workflow.raw_query' for s in sites))
        self.assertTrue(value['unresolved_dispatches'])
        self.assertTrue(value['missing_sources_or_dispatchers'])
        self.assertFalse(value['native_template_reconciliation_complete'])
        self.assertEqual(value['sql_executed'],0)
        self.assertFalse(value['full_chain_admission'])

    def test_actual_node_builders_emit_hashes_without_sql_or_network(self):
        if ROOT is None:self.skipTest('explicit --source-root required for real source inspection')
        catalog=t.SourceCatalog(ROOT,t.HERE)
        result=t.export_node_factories(catalog)
        self.assertEqual(result['profile_count'],13)
        profiles={}
        for row in result['sites']:
            profiles.setdefault(row['profile'],[]).append(row)
            self.assertEqual(row['protocol_commands'],1)
            self.assertNotIn('sql',row)
            self.assertFalse(row['execution_observed'])
        self.assertEqual([r['phase'] for r in profiles['invoke_cold']],
            ['begin','identity','binding','call','commit','seal'])
        self.assertEqual([r['phase'] for r in profiles['invoke_warm']],
            ['begin','binding','call','commit','seal'])
        self.assertEqual([r['phase'] for r in profiles['read_cold']],
            ['read_begin','identity','read_binding','read_call','rollback'])
        self.assertEqual([r['phase'] for r in profiles['read_warm']],
            ['read_begin','read_binding','read_call','rollback'])
        self.assertEqual(len(profiles['durable_stop']),1)
        self.assertEqual(result['sql_executed'],0)
        self.assertTrue(result['admission_not_exercised'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root',type=pathlib.Path)
    args,rest=parser.parse_known_args()
    ROOT=args.source_root
    unittest.main(argv=[sys.argv[0],*rest])
