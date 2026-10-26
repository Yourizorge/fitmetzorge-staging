import json,pathlib,tempfile,types,unittest
from unittest.mock import patch
from hosted_gate import ScalarSession,Gate,save,admission,assert_unused,RUN_ID

class Cursor:
    def __init__(self,sets):self.sets=list(sets);self.index=0
    @property
    def description(self):return self.sets[self.index] is not None
    def fetchall(self):return self.sets[self.index]
    def nextset(self):
        self.index+=1
        return self.index<len(self.sets)

class Tests(unittest.TestCase):
    def test_failed_cli_still_saves_direct_after_without_retry(self):
        from test_cli_stat_reader import snap
        g=object.__new__(Gate);g.cli_protocol=[];g.runtime=object();g.result={'head':'a'*40};saved={}
        calls=[]
        def fail(dry):calls.append(dry);raise TimeoutError('secret must not leak')
        g.cli_executor=fail;g.save=lambda n,v:saved.update({n:v})
        with patch('hosted_gate.snapshot',side_effect=[(snap(),[]),(snap(8),[])]) as reader:
            with self.assertRaisesRegex(ValueError,'execution_failed'):g.metered_cli(False)
        self.assertEqual(calls,[False]);self.assertEqual(reader.call_count,2)
        self.assertEqual(saved['hosted-cli-after-0.json']['error_class'],'TimeoutError')
        self.assertNotIn('secret',json.dumps(saved));self.assertEqual(g.cli_protocol,[])
        self.assertEqual(saved['hosted-cli-before-0.json']['slot'],'quota')
        self.assertEqual(saved['hosted-cli-before-0.json']['capacity_reserved'],64)
        self.assertEqual(saved['hosted-cli-before-0.json']['run_id'],RUN_ID)
    def test_hosted_dry_run_keeps_unknown_commands_unknown(self):
        from test_cli_stat_reader import snap
        g=object.__new__(Gate);g.cli_protocol=[];g.runtime=object();g.result={'head':'a'*40};g.save=lambda *a:None
        g.cli_executor=lambda dry:dict(exit_code=0,up_to_date=True,migration_files=[])
        trace=[{'confirmed':True}]*4
        with patch('hosted_gate.snapshot',side_effect=[(snap(),trace),(snap(13),trace)]):
            r=g.metered_cli(True)
        self.assertIsNone(r['protocol_commands']);self.assertEqual(r['commands'],[])
        self.assertEqual(r['charged_commands'],72);self.assertEqual(r['attribution']['unattributed_calls'],7)
    def test_used_receipt_blocks_even_without_temporary_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);assert_unused(root)
            (root/'_offline/phase6e11/endchain_v1/receipts'/('reserved-'+RUN_ID)).mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'attempt_consumed'):assert_unused(root)
    def test_partial_local_attempt_also_blocks_reopening(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/'supabase/.temp'/('phase6e11-reserved-hosted-'+RUN_ID)).mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'attempt_consumed'):assert_unused(root)
    def scalar(self,sets):
        self.events=[]
        conn=types.SimpleNamespace(info=types.SimpleNamespace(transaction_status=0),
            execute=lambda text,**kw:Cursor(sets),close=lambda:self.events.append('closed'))
        c=types.SimpleNamespace(current_phase='metadata_install',
            before_sql=lambda p,s:self.events.append(('before',p)),after_sql=lambda p,s:self.events.append(('after',p)))
        return ScalarSession(types.SimpleNamespace(connect=lambda:conn),c)
    def test_multi_statement_protocol_is_drained_before_confirmation(self):
        s=self.scalar([None,[{'value':'metadata'}],None])
        self.assertEqual(s.query('BEGIN; SELECT 1; COMMIT'),'metadata')
        self.assertEqual(self.events,[('before','metadata_install'),('after','metadata_install')])
        s.close();self.assertEqual(self.events[-1],'closed')
    def test_unexpected_shape_never_confirms(self):
        s=self.scalar([[{'one':'x','two':'y'}]])
        with self.assertRaisesRegex(ValueError,'scalar_metadata'):s.query('SELECT 1')
        self.assertEqual(len(self.events),1)
    def test_unexpected_cli_operation_is_never_dispatched(self):
        g=object.__new__(Gate)
        g.metered_cli=lambda *a:self.fail('unexpected dispatch')
        for args in [('db','reset'),('db','push'),('migration','repair')]:
            with self.assertRaises(ValueError):g.cli(*args)
    def test_immutable_receipts_and_secret_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);save(root,'before.json',{'safe':True})
            with self.assertRaises(FileExistsError):save(root,'before.json',{'changed':True})
            with self.assertRaises(ValueError):save(root,'../escape.json',{})
            with self.assertRaises(ValueError):save(root,'unsafe.json',{'token':'sbp_'+'x'*32})
            self.assertFalse((root/'unsafe.json').exists())
    def test_old_or_partial_ci_never_grants_hosted_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)
            for n,v in [('result.json',{'status':'CLEAN_CI_PASS','migrations_applied':44}),('collection.json',{}),('candidate.json',{'sources':{}})]:
                (p/n).write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'full_ci_missing'):admission(p)

if __name__=='__main__':unittest.main()
