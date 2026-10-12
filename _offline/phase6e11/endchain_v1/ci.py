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
 'component_trace.mjs','admission.py','test_admission.py','test_sequence.py']
EXTRA={'_offline/phase6e11/endchain_v1/'+n for n in NAMES}
EXTRA|={'_offline/phase6e11/request_v4/'+n for n in ['transport.mjs','connection_options.mjs','config_shape.mjs']}
EXTRA|={'_offline/phase6e11/resume_v1/read_only.mjs','_offline/phase6e11/transport_v1/contract.mjs',
 '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'}
EXTRA|=set(SOURCES)
prior.EXTRA|=EXTRA;prior.old.EXTRA|=EXTRA
class Gate(prior.Gate):
    migration_count=44
    migration_last=M44
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
    def regressions(self):
        folder=self.sources/'_offline/phase6e11/endchain_v1'
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
        result=check_budget(lambda q:self.sql(q,False))
        self.save('endchain-budget-database.json',result)
        self.result['endchain_budget_database_checks']=result['checks']
        self.command('endchain-arm-unit',['python3',str(folder/'test_auth_arm.py')])
        self.result['endchain_arm_unit_tests']=4
        self.command('endchain-python-unit',['python3','-m','unittest','discover','-s',str(folder),'-p','test_*.py'])
        self.result['endchain_python_tests']=37
        self.command('endchain-command-trace',['node',str(folder/'component_trace.mjs')])
        self.result['hosted_admitted']=False
        self.result['full_chain_admission']=False
        self.result['scope']='CI component checks only; complete bound orchestration remains a separate gate.'
if __name__=='__main__':sys.exit(Gate().run())
