"""C06 offline evidence regressions; no actual database cleanup or PASS claim."""
import copy,json,unittest
from unittest.mock import Mock
import fixture_cleanup_evidence as cleanup

CONTEXT={name:'69000000-0000-4000-8000-%012d'%i for i,name in enumerate(('window','a','b'),1)}


class CleanupEvidenceTests(unittest.TestCase):
    def sample(self):
        window,workspaces=cleanup.parameters(CONTEXT)
        return {'window':window,'workspaces':workspaces,'readonly':True,'statement_timeout':'5s',
                'lock_timeout':'1s','counts':dict.fromkeys(cleanup.TABLE_SCOPE,0)}

    def classify(self,row,**changes):
        args={'worker_terminated':True,'writer_transactions_closed':True,**changes}
        return cleanup.classify_sample(row,CONTEXT,**args)

    def test_zero_sample_never_becomes_proven_delete_or_cleanup(self):
        result=self.classify(self.sample())
        self.assertEqual(result['status'],'SCOPED_ZERO_SAMPLE_ONLY')
        self.assertTrue(result['all_sampled_counts_zero'])
        self.assertFalse(result['cleanup_proven']);self.assertFalse(result['deletion_proven'])
        self.assertIsNone(result['delete_count']);self.assertFalse(result['transport_and_io_verified'])
        self.assertFalse(result['ownership_for_delete_proven']);self.assertFalse(result['hosted_admitted'])

    def test_each_remaining_table_blocks_absence_including_orphan_workspace_events(self):
        self.assertEqual(len(cleanup.TABLE_SCOPE),13)
        for table in cleanup.TABLE_SCOPE:
            with self.subTest(table=table):
                row=self.sample();row['counts'][table]=1
                result=self.classify(row)
                self.assertEqual(result['status'],'SCOPED_FIXTURES_REMAIN')
                self.assertEqual(result['sampled_rows'],1);self.assertIsNone(result['delete_count'])
        self.assertIn('window_id=$1::uuid or workspace_id=any($2::uuid[])',cleanup.TABLE_SCOPE['events'])

    def test_lost_response_timeout_partial_cleanup_or_live_writer_cannot_claim_zero(self):
        for worker,writer in ((False,False),(False,True),(True,False)):
            with self.subTest(worker=worker,writer=writer):
                result=self.classify(self.sample(),worker_terminated=worker,writer_transactions_closed=writer)
                self.assertEqual(result['status'],'INCOMPLETE_WRITER_BARRIER')
                self.assertFalse(result['cleanup_proven']);self.assertIsNone(result['delete_count'])

    def test_missing_or_extra_table_and_invalid_counts_are_rejected(self):
        for mode in ('missing','extra','boolean','negative','float','string','null'):
            row=self.sample()
            if mode=='missing':del row['counts']['events']
            elif mode=='extra':row['counts']['auth.users']=0
            else:row['counts']['windows']={'boolean':False,'negative':-1,'float':0.0,'string':'0','null':None}[mode]
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'coverage'):self.classify(row)

    def test_wrong_scope_collision_and_sql_values_are_rejected_before_rendering(self):
        for value in (None,"'; DELETE FROM auth.users; --",CONTEXT['window'],CONTEXT['a'].upper().replace('690','A90')):
            context={**CONTEXT,'b':value}
            with self.subTest(value=value),self.assertRaises(ValueError):cleanup.parameters(context)
        row=self.sample();row['workspaces'].reverse()
        with self.assertRaisesRegex(ValueError,'sample_scope'):self.classify(row)

    def test_readonly_time_limits_and_explicit_barriers_are_required(self):
        for key,value in (('readonly',False),('statement_timeout','30s'),('lock_timeout','5s')):
            row=self.sample();row[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'readonly_limits'):self.classify(row)
        for value in (None,1,'true'):
            with self.assertRaisesRegex(ValueError,'barrier_shape'):self.classify(self.sample(),worker_terminated=value)

    def test_input_evidence_is_not_rewritten_or_relabelled_as_sealed(self):
        row=self.sample();before=copy.deepcopy(row)
        result=self.classify(row);result['counts']['windows']=5
        self.assertEqual(row,before)
        self.assertFalse(result['historical_evidence_modified'])

    def test_inventory_is_one_read_statement_and_never_reads_account_or_history_rows(self):
        from sql_protocol import parser,statements
        parsed=parser().parse_sql(cleanup.INVENTORY_SQL)
        self.assertEqual(len(statements(cleanup.INVENTORY_SQL)),1)
        self.assertEqual(type(parsed[0].stmt).__name__,'SelectStmt')
        for forbidden in ('DELETE','INSERT','UPDATE','FOR UPDATE','auth.','public.profiles',
                          'fmz6e11_audit_private.','fmz6e11_request_private.','fmz6e11_controller_private.'):
            self.assertNotIn(forbidden,cleanup.INVENTORY_SQL)

    def test_inventory_covers_current_fixture_schema_not_only_root_absence(self):
        from sql_protocol import parser
        path=cleanup.ROOT/'supabase/migrations/20260916162120_phase6e11_final_app_integration.sql'
        nodes=parser().parse_sql(path.read_text())
        tables={node.stmt.relation.relname for node in nodes
                if type(node.stmt).__name__=='CreateStmt' and node.stmt.relation.schemaname=='fmz6e11_private'}
        self.assertEqual(tables-set(('config','identities','operators')),set(cleanup.TABLE_SCOPE))
        self.assertNotIn('config',cleanup.TABLE_SCOPE)
        self.assertNotIn('identities',cleanup.TABLE_SCOPE)
        self.assertNotIn('operators',cleanup.TABLE_SCOPE)

    def test_missing_suffix_registration_fails_before_any_memory_transport(self):
        from metered_composition import MeteredComposition
        from runtime_budget import BudgetStop
        for action in ('fixture_cleanup_inventory','fixture_cleanup_delete','fixture_cleanup_absence'):
            c=MeteredComposition();c.abort('partial_fixture_stop');transport=Mock()
            before=c.meter.used
            with self.subTest(action=action),self.assertRaises(BudgetStop):
                ticket=c.meter.safety(action,1)
                transport();c.meter.confirm_safety(ticket)
            transport.assert_not_called();self.assertEqual(c.meter.used,before)

    def test_source_report_keeps_budget_and_unresolved_gaps_explicit(self):
        report=cleanup.source_gaps()
        self.assertEqual(report['status'],'NO_GO_PARTIAL_FIXTURE_SUFFIX_UNPROVEN')
        self.assertEqual(len(report['missing_safety_actions']),3)
        self.assertEqual((report['normal_capacity'],report['approved_limit'],report['normal_cleanup_final_closure_reserve']),
                         (2338,2349,731))
        self.assertFalse(report['runtime_wired']);self.assertFalse(report['all_prefix_bound_proven'])
        self.assertIsNone(report['new_suffix_command_count']);self.assertEqual(report['sql_emitted'],0)
        self.assertTrue(all(len(value)==64 for value in report['source_hashes'].values()))
        self.assertTrue(all(row['line']>0 for row in report['source_gates']))
        json.dumps(report)


if __name__=='__main__':unittest.main()
