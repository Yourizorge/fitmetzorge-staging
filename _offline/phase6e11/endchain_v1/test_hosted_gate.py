import json,pathlib,tempfile,types,unittest
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
