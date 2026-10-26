import os,types,unittest
from unittest.mock import patch
from cli_meter import parse,invocation,bind_receipt,validate_output,source_commit,run

class MeterTests(unittest.TestCase):
    def test_protocol_and_multiline(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: statement: BEGIN;\nselect 1;\nCOMMIT;\n')
        self.assertEqual(len(rows),3)
        self.assertNotIn('sql',rows[0])
    def test_extended_and_other_connection(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: execute <unnamed>: select 1\nFMZSQL|other|2|1|LOG: statement: select 2\n')
        self.assertEqual(len(rows),1)
    def test_missing_or_malformed_not_zero(self):
        for raw in ('','FMZSQL|bad','FMZSQL|other|2|1|LOG: statement: select 2'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):parse(raw)
    def test_function_body_not_semicolon_split(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: statement: do $$begin perform 1; perform 2;end$$;\n')
        self.assertEqual(len(rows),1)
    def test_pinned_cli_and_unique_window(self):
        raw='FMZSQLold|@effect/sql-pg|1|1|LOG: statement: select 1\nFMZSQLnew|@effect/sql-pg|2|1|LOG: statement: BEGIN; COMMIT;\n'
        self.assertEqual(len(parse(raw,'FMZSQLnew|',('@effect/sql-pg',))),2)
        with self.assertRaises(ValueError):parse(raw,'FMZSQLabsent|',('@effect/sql-pg',))
    def mode(self,index=0,profile='endchain',dry=True):
        gate=types.SimpleNamespace(cli_protocol=[{}]*index,cli_profile=profile)
        args=('db','push','--local','--skip-vault')+(('--dry-run',) if dry else ('--yes',))
        return invocation(gate,args,120)
    def receipt(self,n):
        return dict(complete=True,protocol_commands=n,numeric_protocol_coverage=True,
                    observer_commands=[{'confirmed':True}]*8,total_commands=n+8)
    def test_endchain_dry_caps_28_and_29_without_refund(self):
        for index in (1,2):
            receipt=bind_receipt(self.receipt(28),self.mode(index),dict(all_protocol_visible=True,temp_written=0))
            self.assertEqual(receipt['charged_commands'],36)
            with self.assertRaisesRegex(ValueError,'local_protocol'):
                bind_receipt(self.receipt(29),self.mode(index),dict(all_protocol_visible=True,temp_written=0))
        self.assertEqual(self.mode(0,dry=False)['capacity_reserved'],64)
    def test_app_has_no_endchain_slots_or_cap(self):
        for index in range(6):
            for dry in (False,True):
                mode=self.mode(index,'local_app',dry)
                receipt=bind_receipt(self.receipt(75),mode,dict(all_protocol_visible=True,temp_written=0))
                self.assertEqual(receipt['slot'],'app_'+str(index))
                self.assertEqual(receipt['dry_run'],dry)
                self.assertEqual(receipt['total_commands'],83)
                self.assertNotIn('capacity_reserved',receipt)
                self.assertNotIn('charged_commands',receipt)
                self.assertFalse(receipt['hosted_admitted'])
    def test_bad_mode_or_fourth_slot_rejected_before_any_io(self):
        args=('db','push','--local','--dry-run','--skip-vault')
        gate=types.SimpleNamespace(cli_protocol=[{}]*3,cli_profile='endchain')
        with patch.dict(os.environ,GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging'),patch('cli_meter.subprocess.run') as child:
            with self.assertRaisesRegex(ValueError,'slot_exhausted'):run(gate,args,45)
            child.assert_not_called()
        with self.assertRaisesRegex(ValueError,'readonly_slot'):self.mode(1,dry=False)
        with self.assertRaisesRegex(ValueError,'profile'):self.mode(profile='other')
    def test_default_profile_is_endchain_and_timeout_never_increases(self):
        mode=invocation(types.SimpleNamespace(),('db','push','--local','--yes'),120)
        self.assertEqual((mode['profile'],mode['slot'],mode['timeout_seconds']),('endchain','quota',45))
    def test_app_still_requires_exact_numeric_and_temp_zero(self):
        for numeric in (dict(all_protocol_visible=False,temp_written=0),dict(all_protocol_visible=True,temp_written=1)):
            with self.assertRaises(ValueError):bind_receipt(self.receipt(2),self.mode(4,'local_app'),numeric)
    def test_empty_dry_is_endchain_policy_not_generic_app_policy(self):
        pending='Would push 20261018070231_candidate.sql'
        validate_output(self.mode(4,'local_app'),0,pending,'')
        validate_output(self.mode(1),0,'Remote database is up to date.','')
        for output in ('',pending,'up to date; would be pushed','up to date; 20261018070231_candidate.sql'):
            with self.assertRaisesRegex(ValueError,'not_empty'):validate_output(self.mode(1),0,output,'')
    def test_app_and_endchain_cli_exit_failure_is_never_complete(self):
        for profile in ('local_app','endchain'):
            with self.assertRaisesRegex(ValueError,'cli_failed'):validate_output(self.mode(profile=profile),1,'up to date','')
    def test_secret_arguments_rejected_before_receipt_or_log(self):
        for args in [('db','push','--db-url','postgres://private'),('db','push','--local','--password','private')]:
            with self.assertRaisesRegex(ValueError,'local_arguments'):invocation(types.SimpleNamespace(),args,45)
    def test_source_bound_mode_saved_before_first_setup_command(self):
        events=[]
        def save(name,value):events.append((name,value))
        def command(*args,**kw):
            events.append(('setup',None));raise RuntimeError('test_no_database')
        gate=types.SimpleNamespace(cli_profile='endchain',cli_protocol=[{}],result={'commit':'a'*40},
            save=save,container='unused',binary=types.SimpleNamespace(read_bytes=lambda:b'pinned-ci-fixture'),command=command)
        with patch.dict(os.environ,GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging'),patch('cli_meter.subprocess.run') as child:
            with self.assertRaisesRegex(RuntimeError,'test_no_database'):
                run(gate,('db','push','--local','--dry-run','--skip-vault'),45)
            child.assert_not_called()
        self.assertEqual(events[0][0],'cli-preregister-1.json')
        mode=events[0][1]
        self.assertEqual((mode['source_commit'],mode['slot'],mode['capacity_reserved']),('a'*40,'pre_auth',28))
        self.assertEqual(events[1][0],'setup')
    def test_canonical_local_commit_and_agreeing_alias(self):
        self.assertEqual(source_commit({'commit':'a'*40}),'a'*40)
        self.assertEqual(source_commit({'commit':'a'*40,'head':'a'*40}),'a'*40)
    def test_no_head_or_environment_fallback_for_missing_or_invalid_commit(self):
        for result in (None,{}, {'head':'a'*40}, {'commit':None,'head':'a'*40},
                       {'commit':'a'*39}, {'commit':'A'*40}, {'commit':1}):
            with self.subTest(result=result),patch.dict(os.environ,GITHUB_SHA='a'*40):
                with self.assertRaisesRegex(ValueError,'source_commit'):source_commit(result)
    def test_any_present_disagreeing_head_fails_closed(self):
        for head in ('b'*40,None,'',1):
            with self.subTest(head=head),self.assertRaisesRegex(ValueError,'source_conflict'):
                source_commit({'commit':'a'*40,'head':head})
    def test_missing_or_conflicting_source_stops_before_preregistration_and_setup(self):
        for profile in ('endchain','local_app'):
            for result in ({},{'head':'a'*40},{'commit':'a'*40,'head':'b'*40}):
                gate=types.SimpleNamespace(cli_profile=profile,cli_protocol=[],result=result)
                with patch.dict(os.environ,GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging'),patch('cli_meter.subprocess.run') as child:
                    with self.assertRaisesRegex(ValueError,'source_'):
                        run(gate,('db','push','--local','--dry-run','--skip-vault'),45)
                    child.assert_not_called()

if __name__=='__main__':unittest.main()
