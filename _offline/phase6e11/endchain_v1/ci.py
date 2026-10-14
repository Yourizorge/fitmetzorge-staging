"""Clean CI candidate gate. Never authorizes or executes a hosted run."""
import importlib.util,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from database_checks import M44,run as check_budget
from sequence import SOURCES
spec=importlib.util.spec_from_file_location('endchain_prior_guard_ci',HERE.parent/'controller_guard_v1/ci.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
NAMES=['budget.mjs','budget.test.mjs','database_checks.py','ci.py','scoped_cycle.mjs',
 'scoped_cycle.test.mjs','request_transport.mjs','request_transport.test.mjs','auth_arm.py',
 'test_auth_arm.py','scenario.py','sequence.py','command_ledger.py','test_command_ledger.py',
 'component_trace.mjs','admission.py','test_admission.py','test_sequence.py','artifact.py','test_artifact.py',
 'cleanup_manifest.test.mjs','command_register.mjs','command_register.test.mjs',
 'session_transport.mjs','session_transport.test.mjs','native_store.mjs','native_store.test.mjs',
 'composed_handler.mjs','composed_handler.test.mjs','workflow_composition.mjs','composition_local.ts',
 'local_composition.py','local_failure_matrix.py','sql_protocol.py','test_sql_protocol.py',
 'capacity_check.py','test_capacity_check.py','integral_auth.mjs','integral_workflow.mjs','integral_ci.py',
 'cli_meter.py','test_cli_meter.py','integral_io.py','test_integral_io.py','fixture_lifecycle.py','test_fixture_lifecycle.py',
 'auth_protocol.py','test_auth_protocol.py','integral_stream.py','test_integral_stream.py',
 'lifecycle_gates.py','test_lifecycle_gates.py','complete_register.py','test_complete_register.py','integral_failures.py',
 'closure.py','test_closure.py','execution_context.mjs','execution_context.test.mjs',
 'native_runtime.py','test_native_runtime.py','runtime_budget.py','test_runtime_budget.py','auth_evidence.py','test_auth_evidence.py']
EXTRA={'_offline/phase6e11/endchain_v1/'+n for n in NAMES}
EXTRA|={'_offline/phase6e11/request_v4/'+n for n in ['transport.mjs','connection_options.mjs','config_shape.mjs']}
EXTRA|={'_offline/phase6e11/resume_v1/read_only.mjs','_offline/phase6e11/transport_v1/contract.mjs',
 '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'}
EXTRA|=set(SOURCES)
EXTRA|={'_offline/phase6e11/cursor_v1/transfer.py'}
prior.EXTRA|=EXTRA;prior.old.EXTRA|=EXTRA
class Gate(prior.Gate):
    controller_node_count=198
    migration_count=44
    migration_last=M44
    def install(self):
        self.command('pg17-parser-install',['python3','-m','pip','install','--disable-pip-version-check',
            '--only-binary=:all:','--target',str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),
            'pglast==7.20','psycopg[binary]==3.2.10'],timeout=120)
        sys.path.insert(0,str(self.sources/'supabase/.temp/phase6e11-pg17-parser'))
        sys.path.insert(0,str(self.sources/'_offline/phase6e11/endchain_v1'))
        super().install()
        import integral_ci
        integral_ci.configure_local_tls(self)
    def cli(self,*args,timeout=120):
        migration=args[:2]==('migration','up') and self.result.get('phase')=='migration_44'
        dry=args[:2]==('db','push') and '--dry-run' in args
        if dry and getattr(self,'final_dry_run',None) is not None:return self.final_dry_run
        if migration or dry:
            import cli_meter
            if migration:
                from lifecycle_gates import ci_preflight
                ci_preflight(self)
            exact=('db','push','--local','--skip-vault','--yes') if migration else args
            return cli_meter.run(self,exact,timeout)
        return super().cli(*args,timeout=timeout)
    def fetch(self):
        migrations=super().fetch()
        files=json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA<=set(files):raise RuntimeError('endchain_composition_missing')
        self.save('endchain-sources.json',{'sources':{p:files[p] for p in sorted(EXTRA)},
                   'hosted_admitted':False,'full_chain_admission':False})
        return migrations
    def check_controller_functions(self):
        p=self.rows("select proname,prosecdef,proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e11_controller_private'")
        if p!=[{'proname':'single_endchain_receipt','prosecdef':False,'proconfig':['search_path=pg_catalog, pg_temp']}]:
            raise RuntimeError('endchain_function_boundary')
        for role in ('anon','authenticated','service_role','fmz_ci_unprivileged'):
            value=self.rows("select has_function_privilege('"+role+"','fmz6e11_controller_private.single_endchain_receipt()','EXECUTE') allowed")
            if value!=[{'allowed':False}]:raise RuntimeError('endchain_execute_grant')
        return 1
    def check_bridge(self):
        super().check_bridge()
        result=check_budget(lambda q:self.sql(q,False))
        self.save('endchain-budget-database.json',result)
        self.result['endchain_budget_database_checks']=result['checks']
    def regressions(self):
        folder=self.sources/'_offline/phase6e11/endchain_v1'
        # Disposable runner dependency only. PostgreSQL-17 parser, fixed release.
        sys.path.insert(0,str(folder))
        sys.path.insert(0,str(self.sources/'supabase/.temp/phase6e11-pg17-parser'))
        import integral_ci
        self.auth_composition=integral_ci.Composition()
        # Bind the real GoTrue and observer tests to the candidate renderer,
        # while preserving the original audit module on disk.
        sys.path.insert(0,str(self.sources/'_offline/phase6e11/auth_metadata_v1'))
        import audit
        arm_spec=importlib.util.spec_from_file_location('endchain_candidate_arm',folder/'auth_arm.py')
        arm=importlib.util.module_from_spec(arm_spec);arm_spec.loader.exec_module(arm)
        original=audit.arm
        try:
            audit.arm=arm.render
            super().regressions()
        finally:
            audit.arm=original
        self.result['compact_arm_real_auth_contracts']=18
        output=self.command('endchain-unit',['node','--test','--test-reporter=tap',*map(str,sorted(folder.glob('*.test.mjs')))])
        import re
        count=re.search(r'# tests (\d+)',output.stdout)
        if not count or int(count[1])<46:raise RuntimeError('endchain_node_incomplete')
        self.result['endchain_node_tests']=int(count[1])
        self.command('endchain-arm-unit',['python3',str(folder/'test_auth_arm.py')])
        self.result['endchain_arm_unit_tests']=4
        py=self.command('endchain-python-unit',['python3','-m','unittest','discover','-s',str(folder),'-p','test_*.py'])
        n=re.search(r'Ran (\d+) tests',py.stdout+'\n'+py.stderr)
        if not n or int(n[1])<47:raise RuntimeError('endchain_python_incomplete')
        self.result['endchain_python_tests']=int(n[1])
        self.command('endchain-command-trace',['node',str(folder/'component_trace.mjs')])
        self.result['hosted_admitted']=False
        self.result['full_chain_admission']=False
        self.result['scope']='CI component checks only; complete bound orchestration remains a separate gate.'
    def advisors(self):
        super().advisors()
        self.result['cli_protocol_complete']=bool(getattr(self,'cli_protocol',[])) and all(x['complete'] for x in self.cli_protocol)
        if not self.result['cli_protocol_complete']:raise RuntimeError('integral_cli_accounting_not_admitted')
        from complete_register import build
        register=build(self.out)
        paths={}
        for prefix in register['prefixes']:
            import hashlib
            path=prefix.pop('path');key=hashlib.sha256(json.dumps(path,sort_keys=True).encode()).hexdigest()
            if key in paths and paths[key]!=path:raise RuntimeError('safety_path_key_collision')
            paths[key]=path;prefix['path_id']=key
        self.save('register-prefix-reserves.json',{'prefixes':register['prefixes'],'safety_paths':paths})
        for phase in register['phase_budgets']:
            self.save('register-phase-'+phase+'.json',{'rows':[r for r in register['rows'] if r['phase']==phase]})
        self.save('complete-command-register.json',{k:v for k,v in register.items() if k not in ('rows','prefixes','ci_only_bootstrap')})
        self.result['integral_capacity_register']={k:register[k] for k in
            ('complete_register','normal_capacity','worst_including_safety','phase_budgets','recommended_maximum','fits')}
        if register['fits'] is not True:raise RuntimeError('integral_budget_not_admitted')
        self.result['full_chain_admission']=True
        self.result['scope']='Integral local GoTrue/controller/workflow/cleanup/IO and confirmed closure; hosted identity and source admission remain separate.'
        from integral_failures import run as failure_matrix
        self.result['integral_real_failure_cases']=len(failure_matrix(self))
if __name__=='__main__':sys.exit(Gate().run())
