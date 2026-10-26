"""Mock-only entry tests. No Docker, database, Auth or hosted requests."""
import copy,importlib.util,json,os,pathlib,sys,tempfile,types,unittest
from unittest.mock import patch
import diagnostic_ci as d

ENV={'FMZ6E11_LOCAL_WAL_DIAGNOSTIC':'1','GITHUB_ACTIONS':'true',
     'GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging','GITHUB_REF':'refs/heads/main',
     'GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,'EXPECTED_SOURCE_COMMIT':'a'*40}
def receipt():
    return dict(status='DIAGNOSTIC_ONLY',full_chain_admission=False,wal_zero_pass=False,
        commands=16,rollback_confirmed=True,limitations=[],
        queries=[{'complete':True} for _ in range(4)])

class FakeGate(d.DiagnosticGate):
    def __init__(self):
        self.result={'commit':'a'*40};self.saved={};self.calls=[];self.bootstrap=[]
        self.stack_attempted=False;self.fail=None;self.value=receipt()
        self.work=pathlib.Path('/mock');self.sources=pathlib.Path('/candidate')
    def touch(self,name):
        self.calls.append(name)
        if self.fail==name:raise RuntimeError('secret must not leave exception')
    def fetch(self):self.touch('fetch');return list(range(45))
    def install(self):
        self.stack_attempted=True;self.touch('install')
        self.result['platform']={'image':d.IMAGE,'repository_digests':[d.DIGEST]}
    def rebuild(self,migrations):self.touch('rebuild');self.result['migrations_applied']=len(migrations)
    def probe(self):self.touch('probe');return self.value
    def postcheck(self):self.touch('postcheck')
    def cleanup(self):self.touch('cleanup');return {'attempted':self.stack_attempted,'confirmed':True}
    def save(self,name,value):self.saved[name]=copy.deepcopy(value)

class Tests(unittest.TestCase):
    def run_gate(self,g):
        with patch.dict(os.environ,ENV,clear=True),patch('builtins.print'):
            return g.run()
    def test_default_off_before_base_constructor(self):
        with patch.dict(os.environ,{},clear=True),patch.object(d.ci.Gate,'__init__') as parent:
            with self.assertRaises(ValueError):d.DiagnosticGate()
            parent.assert_not_called()
    def test_wrong_branch_repo_attempt_or_sha_rejected(self):
        for key,value in [('GITHUB_REF','refs/heads/other'),('GITHUB_REPOSITORY','other/repo'),
                          ('GITHUB_RUN_ATTEMPT','2'),('EXPECTED_SOURCE_COMMIT','b'*40)]:
            env={**ENV,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):d.enabled(env)
    def test_exact_bootstrap_probe_cleanup_only(self):
        g=FakeGate();self.assertEqual(self.run_gate(g),0)
        self.assertEqual(g.calls,['fetch','install','rebuild','probe','postcheck','cleanup'])
        self.assertEqual(g.result['status'],'DIAGNOSTIC_ONLY')
        for field in ('full_chain_admission','hosted_admitted','wal_zero_pass','causal_attribution'):
            self.assertIs(g.result[field],False)
        self.assertEqual(g.result['diagnostic_commands'],16)
        self.assertFalse(g.saved['diagnostic-bootstrap.json']['exact_total_sql_claim'])
    def test_each_failure_closes_stack_without_secret_output(self):
        for stage in ('fetch','install','rebuild','probe','postcheck'):
            g=FakeGate();g.fail=stage
            self.assertEqual(self.run_gate(g),1)
            self.assertEqual(g.calls[-1],'cleanup')
            self.assertNotIn('secret',str(g.saved))
            self.assertEqual(g.result['status'],'DIAGNOSTIC_ONLY')
    def test_permission_limitation_is_not_success(self):
        g=FakeGate();g.value['limitations']=['pg_walinspect_install_unavailable']
        self.assertEqual(self.run_gate(g),1)
        self.assertFalse(g.result['diagnostic_completed'])
        self.assertFalse(g.result['full_chain_admission'])
    def test_cleanup_failure_cannot_exit_success(self):
        g=FakeGate();g.fail='cleanup'
        self.assertEqual(self.run_gate(g),1)
        self.assertFalse(g.result['disposable_cleanup']['confirmed'])
    def test_exact_image_required_before_rebuild(self):
        g=FakeGate()
        def install():
            g.stack_attempted=True
            g.result['platform']={'image':d.IMAGE,'repository_digests':['wrong']}
        g.install=install
        self.assertEqual(self.run_gate(g),1);self.assertNotIn('rebuild',g.calls)
    def test_cli_is_bootstrap_not_endchain_meter(self):
        g=FakeGate()
        with patch.object(d.BASE,'cli',return_value='mock') as cli:
            self.assertEqual(d.DiagnosticGate.cli(g,'migration','up','--local'),'mock')
            self.assertIsNone(g.bootstrap[-1]['internal_sql_commands'])
            cli.assert_called_once()
            with self.assertRaises(ValueError):d.DiagnosticGate.cli(g,'db','push','--linked')
    def test_exact_disposable_cleanup(self):
        g=FakeGate();g.stack_attempted=True
        with patch.object(g,'cli') as cli:
            self.assertTrue(d.DiagnosticGate.cleanup(g)['confirmed'])
            cli.assert_called_once_with('stop','--no-backup',timeout=120)
    def test_probe_closes_connection_and_clears_private_runtime(self):
        import native_runtime
        for bad in (False,True):
            g=FakeGate();connection=unittest.mock.Mock();runtime=unittest.mock.Mock()
            runtime.connect.return_value=connection
            r=receipt()
            if bad:r['commands']=17
            helper=types.SimpleNamespace(run=unittest.mock.Mock(return_value=r))
            with patch.dict(sys.modules,{'ci_wal_diagnostic':helper}),patch.object(
                    native_runtime.NativeRuntime,'disposable',return_value=runtime):
                if bad:
                    with self.assertRaises(ValueError):d.DiagnosticGate.probe(g)
                else:d.DiagnosticGate.probe(g)
            connection.close.assert_called_once();runtime.clear.assert_called_once()
            args=helper.run.call_args.kwargs
            self.assertEqual(args['environment'],'disposable_ci')
            self.assertEqual(args['ids'],d.IDS)
    def test_subprocess_outputs_are_hashed_not_exported(self):
        g=FakeGate()
        with patch.object(d.ci.Gate,'save') as save:
            d.DiagnosticGate.save(g,'command.json',{'stdout':'password secret','stderr':'url secret','phase':'bootstrap'})
            output=save.call_args.args[1]
            self.assertNotIn('secret',str(output));self.assertNotIn('stdout',output)
            self.assertIn('stdout_sha256',output)
    def test_explicit_extra_contains_helper_entry_and_workflow(self):
        self.assertIn('.github/workflows/phase6e11-wal-diagnostic.yml',d.EXTRA)
        for name in ('diagnostic_ci.py','diagnostic_ops.py','ci_wal_diagnostic.py'):
            self.assertIn('_offline/phase6e11/endchain_v1/'+name,d.EXTRA)
    def test_ops_rejects_default_full_chain_dispatch(self):
        import diagnostic_ops
        with patch.object(sys,'argv',['diagnostic_ops.py','dispatch']),patch.object(
                diagnostic_ops.ops,'main') as main:
            with self.assertRaises(ValueError):diagnostic_ops.main()
            main.assert_not_called()
    def test_ops_prepare_wraps_existing_prepare(self):
        import diagnostic_ops
        with patch.object(sys,'argv',['diagnostic_ops.py','prepare']),patch.object(
                diagnostic_ops.ops,'main') as main,patch.object(d,'activate_sources') as activate:
            diagnostic_ops.main();activate.assert_called_once();main.assert_called_once()
    def test_dispatch_binds_dedicated_workflow_and_consumes_once(self):
        import diagnostic_ops as ops
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);folder=root/'supabase/.temp/phase6e11-endchain-ci-mock'
            folder.mkdir(parents=True)
            (folder/'before.json').write_text(json.dumps({'head':'a'*40}))
            (folder/'blob.json').write_text(json.dumps({'blob':'b'*40,'sha256':'c'*64}))
            def write(path,value):path.write_text(json.dumps(value))
            with patch.object(sys,'argv',['diagnostic_ops.py','dispatch',str(folder),'--enable']),patch.object(
                    ops.ops,'ROOT',root),patch.object(ops.ops.g,'git',side_effect=['a'*40,'main']),patch.object(
                    ops.ops.g,'write',side_effect=write),patch.object(ops.ops.g,'api') as api,patch('builtins.print'):
                ops.main()
                api.assert_called_once_with('/actions/workflows/phase6e11-wal-diagnostic.yml/dispatches',
                    'POST',{'ref':'main','inputs':{'candidate_blob':'b'*40,'candidate_sha256':'c'*64,'enabled':True}})
                with self.assertRaisesRegex(ValueError,'no_retry'):ops.main()
                self.assertEqual(api.call_count,1)
            self.assertEqual(json.loads((folder/'dispatch.json').read_text())['head'],'a'*40)

if __name__=='__main__':unittest.main()
