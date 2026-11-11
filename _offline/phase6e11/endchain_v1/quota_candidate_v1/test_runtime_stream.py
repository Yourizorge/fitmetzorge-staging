"""Offline scope regressions; no substitute for real preservation/WAL proof."""
import ast
import inspect
import unittest
import uuid
from unittest import mock
import integral_stream as original
from quota_candidate_v1 import runtime_stream as s
from quota_candidate_v1.compiler import CandidateStop


class StreamTests(unittest.TestCase):
    def setUp(self):
        self.scope=object.__new__(s.CaseStream)
        self.scope.run_id=str(uuid.uuid4());self.scope.version='20261103010203'
        self.scope.manifest_sha='a'*64;self.scope.attempts=['before']
        self.context=dict(quota_scope=self.scope,window=str(uuid.uuid4()),
            a=str(uuid.uuid4()),b=str(uuid.uuid4()),runs={'seed':str(uuid.uuid4())})
        self.ids={n:str(uuid.uuid4()) for n in ('a_member','a_trainer','b_member')}
        self.rows=[dict(schema='public',name='table_'+str(i),columns=['id']) for i in range(100)]

    def test_engine_ast_identical_to_original_except_function_name(self):
        old=ast.parse(inspect.getsource(original.run));new=ast.parse(inspect.getsource(s._run))
        new.body[0].name=old.body[0].name
        self.assertEqual(ast.dump(old),ast.dump(new))

    def test_all_legacy_controller_rows_protected_only_fresh_case_excluded(self):
        for table,key in [('runs','id'),('steps','run_id'),('evidence','run_id')]:
            value=s.predicates(dict(schema='fmz6e11_controller_private',name=table,columns=[key]),self.ids,self.context)
            self.assertEqual(value,key+"<>'"+self.scope.run_id+"'")
            self.assertNotIn(original.RUN_ID,value)

    def test_history_filter_excludes_only_local_append_not_m45(self):
        value=s.predicates(dict(schema='supabase_migrations',name='schema_migrations',columns=['version']),self.ids,self.context)
        self.assertEqual(value,"version<>'20261103010203'")
        self.assertNotIn('20261018070231',value)

    def test_other_table_predicates_unchanged(self):
        for schema,table,columns in [('auth','users',['id']),('public','profiles',['id']),
            ('fmz6e11_private','workspaces',['window_id']),('fmz6e11_audit_private','runs',['id'])]:
            row=dict(schema=schema,name=table,columns=columns)
            self.assertEqual(s.predicates(row,self.ids,self.context),original.predicates(row,self.ids,self.context))

    def test_new_catalog_has_exact_shape_and_presence_but_is_separate_gate(self):
        before=s.plan(self.rows,self.ids,self.context)
        self.scope.attempts=['before','before_cleanup']
        catalog=dict(schema='fmz6e11_controller_private',name='quota_candidate_v1_cases',columns=list(s.CATALOG_COLUMNS))
        after=s.plan(self.rows+[catalog],self.ids,self.context)
        self.assertEqual(before,after)
        for rows in [self.rows,self.rows+[catalog,catalog],self.rows+[{**catalog,'columns':['run_id']}]]:
            with self.assertRaises(CandidateStop):s.plan(rows,self.ids,self.context)

    def test_unrecognized_controller_table_is_never_blanket_excluded(self):
        with self.assertRaisesRegex(CandidateStop,'unknown_controller_table'):
            s.plan(self.rows+[dict(schema='fmz6e11_controller_private',name='unknown',columns=['id'])],self.ids,self.context)

    def test_exact_three_cycles_no_retry_or_fourth(self):
        self.scope.attempts=[]
        with mock.patch.object(s,'_run',return_value={'unit_only':True}) as run:
            for label in s.LABELS:self.scope.run(None,None,self.ids,self.context,label)
            with self.assertRaises(CandidateStop):self.scope.run(None,None,self.ids,self.context,'final_post')
        self.assertEqual(run.call_count,3)

    def test_failed_cycle_consumed_and_legacy_boundary_forbidden(self):
        self.scope.attempts=[]
        with mock.patch.object(s,'_run',side_effect=RuntimeError('unit_stop')):
            with self.assertRaises(RuntimeError):self.scope.run(None,None,self.ids,self.context,'before')
        with self.assertRaises(CandidateStop):self.scope.run(None,None,self.ids,self.context,'before')
        self.scope.attempts=[]
        with self.assertRaises(CandidateStop):
            self.scope.run(None,None,self.ids,{**self.context,'migration_boundary':True},'before')


if __name__=='__main__':unittest.main()
