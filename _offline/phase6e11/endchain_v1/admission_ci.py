"""One disposable 47-migration source, independent checks, no hosted admission."""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
APP = HERE.parents[1] / 'phase6e_server_v1'
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location('admission_application_ci', APP/'ci.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# Explicit source list; never ship unrelated dirty or historical evidence files.
LOCAL_SOURCES = ('admission_ci.py', 'admission_ops.py', 'admission_binding.py',
    'test_admission_binding.py', 'test_admission_ci.py', 'auth_failure.py',
    'auth_failure_transport.py', 'auth_failure_test.py', 'auth_failure_contract.md',
    'auth_failure_tracked.py', 'auth_failure_tracked_test.py',
    'auth_failure_parent_finalizer.py', 'auth_failure_parent_finalizer_test.py',
    'auth_pre_fixture_closure.py', 'auth_pre_fixture_closure_test.py',
    'admission_cleanup_composition.py', 'test_admission_cleanup_composition.py',
    'admission_fixture_context.py', 'test_admission_fixture_context.py',
    'admission_journal.py', 'test_admission_journal.py',
    'admission_failure.py', 'test_admission_failure.py',
    'admission_tools.py', 'test_admission_tools.py',
    'admission_module_binding.py', 'test_admission_module_binding.py',
    'admission_quota_readonly.py', 'test_admission_quota_readonly.py',
    'admission_budget.py', 'admission_budget_test.py',
    'admission_budget_register.py', 'admission_budget_register_test.py',
    'admission_budget_graph.py', 'admission_budget_receipts.py', 'admission_budget_receipts_test.py',
    'integral_failure_runtime.py', 'integral_failure_runtime_workflow.py',
    'integral_failure_runtime_worker.mjs',
    'migration_failure_boundaries.py', 'test_migration_failure_boundaries.py',
    'fixture_cleanup_evidence.py', 'test_fixture_cleanup_evidence.py',
    'fixture_cleanup_runtime.py', 'fixture_cleanup_runtime_sql.py',
    'fixture_cleanup_runtime_ci.py', 'fixture_cleanup_runtime_test.py',
    'fixture_parent_closure.py', 'test_fixture_parent_closure.py',
    'fixture_db_terminality.py', 'test_fixture_db_terminality.py',
    'fixture_producer_scope.py', 'test_fixture_producer_scope.py',
    'fixture_parent_physical_zero.py', 'test_fixture_parent_physical_zero.py',
    'fixture_control_ownership.py', 'test_fixture_control_ownership.py')
EXTRA = {'_offline/phase6e11/endchain_v1/' + name for name in LOCAL_SOURCES}
EXTRA |= {'_offline/phase6e11/endchain_v1/cli_predispatch/'+name for name in (
    'ci.py','entry.mjs','hook.cjs','package.json','pnpm-lock.yaml','pnpm-workspace.yaml',
    'policy.cjs','prepare.py','README.md','smoke.py','test_ci.py','test_canonical.py','test_hook.cjs','test_policy.cjs')}
EXTRA |= {'_offline/phase6e11/endchain_v1/cli_predispatch/'+name for name in ('pending.py','test_pending.py')}
EXTRA.add('.github/workflows/phase6e-admission-local-ci.yml')
EXTRA.add('_offline/phase6e_server_v1/ops.py')
EXTRA.add('_offline/phase6e_server_v1/offline_shell_browser.test.cjs')
EXTRA.add('docs/PHASE6E11_ADMISSION_PREREGISTRATION_20261102.md')
EXTRA.add('_offline/phase6e11/endchain_v1/receipts/reserved-ci-39109482869/complete-command-register.json')
app.previous.prior.old.EXTRA |= EXTRA


class Gate(app.Gate):
    def bind_modules(self, *modules):
        import admission_module_binding
        checked = admission_module_binding.verify(self, [admission_module_binding, *modules])
        self.result.setdefault('admission_module_bindings', []).append(checked)

    def instrumented_cli(self):
        module=getattr(self,'_instrumented_cli',None)
        if module is None:
            spec=importlib.util.spec_from_file_location('admission_cli_predispatch',
                self.sources/'_offline/phase6e11/endchain_v1/cli_predispatch/ci.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            self.bind_modules(module)
            self._instrumented_cli=module
        return module

    def cli(self,*args,timeout=120):
        phase=self.result.get('phase')
        if args==('migration','up','--local') and phase in ('local_app_schema','local_app_outbox'):
            name=app.M45 if phase=='local_app_schema' else app.M46
            expected=self.sources/'_offline/phase6e_server_v1/supabase/migrations'/name
            return self.instrumented_cli().run_pending(self,args,expected)
        if self.result.get('phase')=='migration_45' and args==('migration','up','--local'):
            import migration_failure_boundaries as boundary
            self.bind_modules(boundary, boundary.rt)
            token=boundary.before(self)
            result=self.instrumented_cli().run_canonical(self,args,self.sources/boundary.M45)
            boundary.after(self,token,result)
            return result
        return super().cli(*args,timeout=timeout)

    def install(self):
        super().install()
        import admission_tools
        self.bind_modules(admission_tools)
        admission_tools.install(self)

    def check_bridge(self):
        # Preserve actual ACL/RLS checks without executing the old October identity.
        app.previous.prior.old.Gate.check_bridge(self)
        import admission_quota_readonly
        self.bind_modules(admission_quota_readonly)
        result = admission_quota_readonly.run(self)
        self.result['admission_components']['quota'] = result['status']

    def fetch(self):
        if (os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
                or os.environ.get('GITHUB_REF') != 'refs/heads/main'
                or os.environ.get('GITHUB_RUN_ATTEMPT') != '1'):
            raise RuntimeError('admission_ci_scope_or_retry')
        migrations = super().fetch()
        sources = json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA <= sources.keys():
            raise RuntimeError('admission_source_missing')
        self.result['full_chain_admission'] = False
        self.result['hosted_admitted'] = False
        self.result['package21_released'] = False
        self.result['admission_components'] = {}
        return migrations

    def admission_units(self):
        folder = self.sources/'_offline/phase6e11/endchain_v1'
        self.command('admission-browser-bootstrap-unit', ['node','--test',
            str(self.sources/'_offline/phase6e_server_v1/offline_shell_browser.test.cjs')])
        self.command('admission-binding-unit', ['python3', '-B', '-m', 'unittest',
            'discover', '-s', str(folder), '-p', 'test_admission_binding.py'])
        self.command('admission-ci-unit', ['python3', '-B', '-m', 'unittest',
            'discover', '-s', str(folder), '-p', 'test_admission_ci.py'])
        self.command('admission-auth-unit', ['python3', '-B', str(folder/'auth_failure_test.py')])
        self.command('admission-auth-tracked-unit', ['python3', '-B', str(folder/'auth_failure_tracked_test.py')])
        self.command('admission-auth-parent-unit', ['python3', '-B', str(folder/'auth_failure_parent_finalizer_test.py')])
        self.command('admission-auth-prefixture-unit', ['python3', '-B', str(folder/'auth_pre_fixture_closure_test.py')])
        self.command('admission-fixture-bootstrap-unit', ['python3', '-B', str(folder/'test_admission_fixture_context.py')])
        self.command('admission-journal-unit', ['python3', '-B', str(folder/'test_admission_journal.py')])
        self.command('admission-fixture-unit', ['python3', '-B', str(folder/'fixture_cleanup_runtime_test.py')])
        for name in ('test_admission_failure.py','test_admission_tools.py',
                     'test_admission_module_binding.py',
                     'test_admission_quota_readonly.py','admission_budget_test.py',
                     'admission_budget_register_test.py','admission_budget_receipts_test.py','test_integral_failures.py',
                     'test_migration_failure_boundaries.py','test_fixture_parent_closure.py',
                     'test_fixture_control_ownership.py','test_fixture_db_terminality.py',
                     'test_fixture_producer_scope.py','test_fixture_parent_physical_zero.py',
                     'test_admission_cleanup_composition.py'):
            self.command('admission-'+name[:-3],['python3','-B',str(folder/name)])
        self.result['admission_components']['binding'] = 'OFFLINE_TESTED_NOT_AUTHORITY'

    def regressions(self):
        # Reject cheap local contract errors before the slower app/browser matrix.
        self.admission_units()
        super().regressions()
        try:
            self.run_components()
        finally:
            primary = sys.exc_info()[1]
            try:
                import admission_budget
                budget = admission_budget.run(self)
                self.result['admission_components']['command_budget'] = budget['status']
            except Exception as error:
                from admission_failure import secondary
                secondary(self,'budget_packaging',error,primary)
                if primary is None:raise

    def run_components(self):
        # This local diagnostic prepayment is not an observed hosted Auth cost.
        import auth_failure
        import admission_fixture_context
        import fixture_cleanup_runtime_ci
        from admission_journal import Journal
        from admission_failure import package_journal
        import integral_failure_runtime
        import integral_failure_runtime_workflow
        import ci_auth
        from admission_binding import NEW_RUN
        import admission_journal
        import admission_failure
        import native_runtime
        import auth_failure_transport
        import auth_failure_tracked
        import fixture_cleanup_runtime
        import fixture_cleanup_runtime_sql
        import fixture_cleanup_evidence
        import fixture_control_ownership
        import fixture_db_terminality
        import fixture_parent_closure
        import fixture_producer_scope
        import fixture_parent_physical_zero
        import auth_failure_parent_finalizer
        import admission_cleanup_composition
        import sql_protocol
        import admission_binding
        self.bind_modules(auth_failure, admission_fixture_context, fixture_cleanup_runtime_ci,
            admission_journal, admission_failure, integral_failure_runtime,
            integral_failure_runtime_workflow, ci_auth, native_runtime,
            auth_failure_transport, auth_failure_tracked, fixture_cleanup_runtime, fixture_cleanup_runtime_sql,
            fixture_cleanup_evidence, fixture_control_ownership, fixture_db_terminality,
            fixture_parent_closure, fixture_producer_scope, fixture_parent_physical_zero,
            auth_failure_parent_finalizer, admission_cleanup_composition,
            sql_protocol, admission_binding)
        original_save = self.save
        closure = admission_cleanup_composition.Closure(self, original_save)
        request_registry = auth_failure_tracked.Registry(self.out/'admission-auth-request-registry', run_id=NEW_RUN)
        bootstrap_plan = [entry for _ in range(3) for entry in (
            {'method':'POST','route':'/admin/users','units':128},
            {'method':'POST','route':'/token?grant_type=password','units':128},
            {'method':'GET','route':'/user','units':128})]
        parent_budget = auth_failure_tracked.ParentBudget(self.out/'admission-auth-parent-budget',
            bootstrap_plan,run_id=NEW_RUN)
        tracked_auth = auth_failure_tracked.Factory(request_registry,parent_budget,
            finalizer=closure.finalize)
        self.save = lambda name, value: original_save('admission-auth-' + name, value)
        try:
            with ci_auth.environment(self, roles=('a','trainer','b'), include_test_admin=True,
                                     tracked_auth_factory=tracked_auth) as ctx:
                self.auth_failure_context = auth_failure.context_from_ci(ctx, run_id=NEW_RUN,
                    managed_costs={name:128 for name in auth_failure.OPERATIONS}, exclusive_local_auth=True)
                try:
                    receipt = auth_failure.run(self,safety_reconciliation=True,
                        transport_factory=request_registry.case_transport_factory)
                    self.result['admission_components']['auth_failures'] = receipt['status']
                    if receipt['status'] != 'LOCAL_AUTH_FAILURE_COMPONENT_PASS':
                        raise RuntimeError('admission_auth_component_failed')
                    self.save = original_save
                    self.integral_failure_driver = integral_failure_runtime_workflow.WorkflowDriver(
                        self,local_component_authorized=True,
                        transport_factory=request_registry.case_transport_factory)
                    matrix = integral_failure_runtime.run(self,
                        selection=integral_failure_runtime_workflow.SUPPORTED,diagnostic_only=True)
                    self.result['admission_components']['fault_matrix'] = matrix['status']
                    if (matrix.get('bootstrap_or_runner_failure')
                            or matrix.get('diagnostic_subset_verified') is not True):
                        raise RuntimeError('admission_fault_component_failed')
                    tracked = closure.begin(ctx)
                    try:
                        closure.before_bootstrap_write()
                        admission_fixture_context.run(self, ctx, runtime=tracked)
                        fixture_save = self.save
                        journal = Journal(self.out/'admission-fixture-private-journal', original_save,
                            'admission-fixture-journal')
                        self.save = journal.save
                        try:
                            fixture_receipt = fixture_cleanup_runtime_ci.run(self, runtime=tracked)
                        finally:
                            primary = sys.exc_info()[1]
                            self.save = fixture_save
                            package_journal(self,journal,original_save,primary)
                    finally:
                        primary = sys.exc_info()[1]
                        try: tracked.clear()
                        except BaseException as error:
                            admission_failure.secondary(self,'fixture_tracked_close',error,primary)
                            if primary is None: raise
                    self.result['admission_components']['fixture_cleanup'] = fixture_receipt['status']
                    if fixture_receipt['status'] != 'COMPONENT_PASS':
                        raise RuntimeError('admission_fixture_component_failed')
                    closure.bind_terminal()
                finally:
                    self.auth_failure_context.clear()
                    self.save = lambda name, value: original_save('admission-auth-' + name, value)
        finally:
            self.save = original_save
        receipt = self.instrumented_cli().run(self)
        self.result['admission_components']['cli_predispatch'] = (
            'LOCAL_EMPTY_DRY_RUN_PASS' if receipt.get('complete') is True
            and receipt.get('actual_empty_dry_run') is True else 'NO_GO')
        self.save('admission-component-coverage.json', {
            'status': 'NO_GO', 'source_commit': os.environ['GITHUB_SHA'],
            'run_id': os.environ['GITHUB_RUN_ID'],
            'components': self.result['admission_components'],
            'strict_wal': 'BLOCKED_RETAINED_INCOMPLETE_EVIDENCE',
            'exhausted_wal_diagnostic_reexecuted': False,
            'hosted_calls': 0, 'full_chain_admission': False})

    def advisors(self):
        super().advisors()
        self.result['application_component'] = 'CLEAN_CI_PASS'
        self.result['full_chain_admission'] = False
        self.result['hosted_admitted'] = False
        self.result['admission_blockers'] = ['strict_wal_not_proven',
            'integral_components_not_yet_admitted', 'independent_review_required']
        self.save('admission-terminal.json', {
            'source_commit': os.environ['GITHUB_SHA'], 'ci_run': os.environ['GITHUB_RUN_ID'],
            'application_component': self.result['application_component'],
            'blockers': self.result['admission_blockers'],
            'hosted_calls': 0, 'owner_window_allowed': False,
            'full_chain_admission': False, 'status': 'NO_GO'})
        raise RuntimeError('complete_admission_blocked_not_component_failure')


if __name__ == '__main__':
    sys.exit(Gate().run())
