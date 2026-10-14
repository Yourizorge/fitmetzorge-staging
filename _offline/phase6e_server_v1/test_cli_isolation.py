import os,unittest
from unittest.mock import patch
from cli_isolation import measured

class Fake:
    def __init__(self):self.setting='on';self.cli_protocol=[];self.receipts={};self.active=0;self.container='supabase_db_fmz-db41-ci'
    def rows(self,sql):return [{'setting':self.setting}] if 'current_setting' in sql else [{'n':self.active}]
    def command(self,label,args,sql):
        assert args[:4]==['docker','exec','-i','supabase_db_fmz-db41-ci'] and args[args.index('-U')+1]=='supabase_admin'
        if 'alter system' in sql:self.setting='off' if "'off'" in sql else 'on'
    def save(self,name,value):self.receipts[name]=value

class Tests(unittest.TestCase):
    def run_case(self,gate,complete=True,fail=False):
        def meter(g,args,timeout):
            self.assertEqual(g.setting,'off')
            if fail:raise ValueError('original')
            g.cli_protocol.append({'complete':complete,'numeric_protocol_coverage':complete});return 'done'
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging'}):return measured(gate,('db','push'),120,meter)
    def test_complete_and_counted_restore(self):
        g=Fake();self.assertEqual(self.run_case(g),'done');self.assertEqual(g.setting,'on')
        self.assertEqual(g.receipts['cli-isolation-0.json']['commands'],8)
        self.assertTrue(g.receipts['cli-isolation-0.json']['restored'])
    def test_incomplete_cli_is_a_ci_failure(self):
        g=Fake()
        with self.assertRaisesRegex(RuntimeError,'cli_incomplete_evidence'):self.run_case(g,False)
        self.assertEqual(g.setting,'on')
    def test_original_failure_and_busy_worker_stop(self):
        for busy in (False,True):
            g=Fake();g.active=int(busy)
            with self.assertRaises((ValueError,RuntimeError)):self.run_case(g,fail=True)
            self.assertEqual(g.setting,'on');self.assertTrue(g.receipts['cli-isolation-0.json']['restored'])
    def test_only_target_disposable_ci(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'other'}),self.assertRaisesRegex(RuntimeError,'ci_only'):
            measured(Fake(),(),120,lambda *a:None)
        g=Fake();g.container='other'
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging'}),self.assertRaisesRegex(RuntimeError,'ci_only'):
            measured(g,(),120,lambda *a:None)
if __name__=='__main__':unittest.main()
