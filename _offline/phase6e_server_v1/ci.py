"""Clean 44 preserved migrations + one isolated candidate; zero hosted access."""
import hashlib,importlib.util,json,pathlib,re,shutil,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('integration_prior_ci',HERE.parent/'phase6e11/endchain_v1/ci.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
base=previous.prior.old.old
M45='20261014105919_phase6e_synthetic_server_candidate.sql'
M46='20261014160019_phase6e_local_outbox.sql'
NEW=['domain.cjs','domain.test.cjs','presentation.cjs','presentation.test.cjs','panels.js','composed_store.py','windows.cjs','windows.test.cjs','worker.cjs','store.py','database_tests.py','ci.py','ci_auth.py',
     'server.py','ui.html','ui.js','ui.css','browser_checks.cjs','composed_browser.cjs','protocol.py','test_protocol.py',
     'size_diagnosis.py','size_pg17.py','test_size_diagnosis.py',
     'display.js','display.test.cjs',
     'draft_queue.js','draft_queue.test.cjs','queue_ui.js','ui_session.test.cjs',
     'account_center.cjs','account_center.js','account_center.test.cjs','account_center_browser.cjs',
     'offline_shell.html','offline_shell.css','offline_shell.js','offline_sw.js','offline_queue_ui.test.cjs',
     'offline_shell_browser.cjs','offline_shell_local.cjs','offline_shell_INTEGRATION.md',
     'stream_size_fixture.json','stream_size_pg17.py','capacity_proposal.py','test_capacity_proposal.py',
     'sync_contract.cjs','access_policy.cjs','prepared_contracts.test.cjs','work_register.json','check_work_register.py',
     'release_packet.py','test_release_packet.py','outbox.py','test_outbox.py','planning.py','test_planning.py',
     'workday_release.py','test_workday_release.py','receipt_accounting.py','test_receipt_accounting.py',
     'release_selection.py','test_release_selection.py','release_selection_http.py',
     'registration12.cjs','registration12.test.cjs','workout12.cjs','workout12.test.cjs','registration_store.py','registration_database.py','registration_browser.cjs',
     'registration_release.py','test_registration_release.py',
     'registration_scope.py','test_registration_scope.py','registration_transport.py','test_registration_transport.py',
     'registration_proof.py','test_registration_proof.py','registration_accounting.py','test_registration_accounting.py',
     'application_io.py','test_application_io.py','cli_isolation.py','test_cli_isolation.py',
     'cli_url_probe.py','test_cli_url_probe.py',
     'supabase/migrations/'+M45,'supabase/migrations/'+M46]
EXTRA={'_offline/phase6e_server_v1/'+p for p in NEW}
EXTRA.add('assets/fit-met-zorge-logo-cropped.png')
EXTRA.add('assets/training-workout-model.js')
EXTRA.add('_offline/phase6e11/utility_diagnosis_v1/probe.py')
pending=[HERE/'domain.cjs',HERE/'registration12.cjs'];seen=set()
while pending:
    path=pending.pop().resolve()
    if path in seen:continue
    seen.add(path)
    name=path.relative_to(ROOT).as_posix()
    if not name.startswith('_offline/phase6e_server_v1/'):EXTRA.add(name)
    for ref in re.findall(r'require\([\"\'](\.[^\"\']+)[\"\']\)',path.read_text()):
        pending.append(path.parent/ref)
previous.prior.old.EXTRA|=EXTRA

class Gate(previous.Gate):
    cli_namespace=''
    def browser_dependencies(self):
        deps=self.work/'browser-deps'
        if not (deps/'node_modules/playwright').exists():
            self.command('integration-playwright',['npm','install','--prefix',str(deps),'--no-audit','--no-fund','playwright@1.56.1'],timeout=120)
            self.command('integration-chromium',['node',str(deps/'node_modules/playwright/cli.js'),'install','--with-deps','chromium'],timeout=180)
        return str(deps/'node_modules/playwright')
    def fetch(self):
        migrations=super().fetch()
        files=json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA<=set(files):raise RuntimeError('integration_sources_missing')
        for name in files:
            if not name.startswith(('_offline/','supabase/')) and name.endswith('.js'):
                if (ROOT/name).read_bytes()!=(self.sources/name).read_bytes():raise RuntimeError('frozen_model_changed')
        return migrations
    def cli(self,*args,timeout=120):
        candidate=args[:2]==('migration','up') and self.result.get('phase')=='local_candidate_45'
        dry=args[:2]==('db','push') and '--dry-run' in args
        if candidate or dry:
            import cli_meter
            actual=('db','push','--local','--skip-vault','--yes') if candidate else args
            from cli_isolation import measured
            return measured(self,actual,timeout,cli_meter.run)
        return base.Gate.cli(self,*args,timeout=timeout)
    def rebuild(self,migrations):
        super().rebuild(migrations)
        path=self.sources/'_offline/phase6e_server_v1/supabase/migrations'/M45
        shutil.copyfile(path,self.work/'supabase/migrations'/M45)
        self.result['phase']='local_candidate_45'
        self.cli('migration','up','--local')
        folder=self.sources/'_offline/phase6e_server_v1';sys.path.insert(0,str(folder))
        import ci_auth,registration_database
        self.save('registration12-minimal-history.json',{'history':self.rows('select version from supabase_migrations.schema_migrations order by version'),
            'migration_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'hosted_applied':False})
        dry=self.cli('db','push','--local','--dry-run','--skip-vault')
        combined=(dry.stdout+dry.stderr).lower()
        if 'up to date' not in combined or 'would push' in combined:raise RuntimeError('registration12_pending_migration')
        self.save('registration12-dry-run.json',{'output_sha256':hashlib.sha256((dry.stdout+dry.stderr).encode()).hexdigest(),
            'pending':False,'local_only':True})
        # Capture the complete minimal slice independently before optional M46.
        old_save=self.save
        self.save=lambda name,value:old_save('registration12-'+name,value)
        try:
            with ci_auth.environment(self) as ctx:
                def browser(store,workspace):
                    import server,subprocess,threading
                    app=server.Application(store,[workspace],enabled=True);http=server.serve(app,0)
                    thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                    try:
                        data={'url':'http://127.0.0.1:'+str(http.server_port),'account':ctx['accounts']['a'],
                            'playwright':self.browser_dependencies(),'screenshots':str(self.out)}
                        p=subprocess.run(['node',str(folder/'registration_browser.cjs')],input=json.dumps(data),capture_output=True,text=True,timeout=90)
                        result=json.loads(p.stdout);self.save('browser.json',result)
                        if p.returncode or result['status']!='PASS':raise RuntimeError('registration12_browser')
                    finally:http.shutdown();http.server_close();thread.join(timeout=5)
                result=registration_database.run(ctx,browser)
                self.save('database.json',result)
                self.result['registration12_tests']=result['count']
                self.save('auth.json',ci_auth.auth_checks(ctx))
        finally:self.save=old_save
        # Exercise the new private transport against real local GoTrue/PG,
        # not mocked /user replies and not a synthetic hosted admission.
        self.save=lambda name,value:old_save('registration12-transport-'+name,value)
        try:
            from registration_transport import Candidate
            from registration_proof import MeasuredRegistration
            from native_runtime import NativeRuntime
            with ci_auth.environment(self,roles=('a','trainer','b')) as ctx:
                identities={role:ctx['claims'][role]['sub'] for role in ('a','trainer','b')}
                def factory(bindings,observer):
                    return MeasuredRegistration(Candidate.disposable(NativeRuntime.disposable(self),ctx['auth'],bindings,identities,observer),self.save)
                proofs=[]
                for member in ('a','b'):
                    proof=registration_database.run(ctx,transport_factory=factory,member=member)
                    self.save('database-'+member+'.json',proof);proofs.append(proof)
                self.save('auth.json',ci_auth.auth_checks(ctx))
                self.result['registration12_transport_database_tests']=sum(p['count'] for p in proofs)
                self.result['registration12_transport_auth_tests']=4
                self.result['registration12_transport_hosted']=False
        finally:self.save=old_save
        shutil.copyfile(self.sources/'_offline/phase6e_server_v1/supabase/migrations'/M46,self.work/'supabase/migrations'/M46)
        self.cli('migration','up','--local')
        history=self.rows('select version from supabase_migrations.schema_migrations order by version')
        if len(history)!=46 or history[-1]['version']!=M46.split('_')[0]:raise RuntimeError('candidate_history')
        self.save('candidate-46-history.json',{'history':history,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'outbox_sha256':hashlib.sha256((self.sources/'_offline/phase6e_server_v1/supabase/migrations'/M46).read_bytes()).hexdigest(),'hosted_applied':False})
        self.result['clean_rebuild']='46/46_PASS_LOCAL_CANDIDATE';self.result['migrations_applied']=46
    def regressions(self):
        # Existing SQL/audit regressions remain mandatory; no second 6E-11 run.
        base.Gate.regressions(self)
        folder=self.sources/'_offline/phase6e_server_v1';sys.path.insert(0,str(folder))
        self.command('integration-protocol',[sys.executable,'-B',str(folder/'test_protocol.py')])
        self.command('integration-release-packet',[sys.executable,'-B',str(folder/'test_release_packet.py')])
        self.command('registration-release-packet',[sys.executable,'-B',str(folder/'test_registration_release.py')])
        self.command('registration-scope',[sys.executable,'-B',str(folder/'test_registration_scope.py')])
        # The pinned driver is installed into the isolated dependency directory,
        # not global site-packages; the fresh test process needs that same path.
        self.command('registration-transport',['env','PYTHONPATH='+str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),
            sys.executable,'-B',str(folder/'test_registration_transport.py')])
        self.result['registration_candidate_unit_tests']=18
        self.result['registration_candidate_hosted_admitted']=False
        self.command('registration-proof',['env','PYTHONPATH='+str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),
            sys.executable,'-B',str(folder/'test_registration_proof.py')])
        self.command('registration-accounting',[sys.executable,'-B',str(folder/'test_registration_accounting.py')])
        self.command('integration-outbox',[sys.executable,'-B',str(folder/'test_outbox.py')])
        self.command('integration-planning',[sys.executable,'-B',str(folder/'test_planning.py')])
        self.command('integration-application-io',[sys.executable,'-B',str(folder/'test_application_io.py')])
        self.command('integration-cli-isolation',[sys.executable,'-B',str(folder/'test_cli_isolation.py')])
        self.command('cli-url-evidence-replay',['env','PYTHONPATH='+str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),sys.executable,'-B',str(folder/'test_cli_url_probe.py')])
        output=self.command('integration-domain',['node','--test',str(folder/'domain.test.cjs'),str(folder/'windows.test.cjs'),str(folder/'registration12.test.cjs'),str(folder/'presentation.test.cjs'),str(folder/'workout12.test.cjs')])
        count=re.search(r'# tests (\d+)',output.stdout)
        if not count:raise RuntimeError('domain_count')
        self.result['integration_domain_tests']=int(count[1])
        prepared=self.command('prepared-contracts',['node','--test','--test-reporter=tap',str(folder/'prepared_contracts.test.cjs')])
        self.result['prepared_contract_tests']=int(re.search(r'# tests (\d+)',prepared.stdout)[1])
        self.command('display-regression',['node','--test',str(folder/'display.test.cjs')])
        self.command('draft-queue-regression',['node','--test',str(folder/'draft_queue.test.cjs')])
        self.command('account-center-regression',['node','--test',str(folder/'account_center.test.cjs')])
        self.command('offline-queue-ui-regression',['node','--test',str(folder/'offline_queue_ui.test.cjs')])
        self.command('ui-session-regression',['node','--test',str(folder/'ui_session.test.cjs')])
        self.command('work-register',[sys.executable,'-B',str(folder/'check_work_register.py')])
        self.command('workday-release-packets',[sys.executable,'-B',str(folder/'test_workday_release.py')])
        self.command('release-selection',[sys.executable,'-B',str(folder/'test_release_selection.py')])
        import workday_release
        packets=workday_release.build(root=self.sources,archive=self.sources/'absent-historical-receipts')
        workday_release.verify(packets,root=self.sources,archive=self.sources/'absent-historical-receipts')
        self.save('workday-release-packets.json',packets)
        from stream_filter_check import run as stream_filter_check
        self.result['stream_filter_pg17_checks']=stream_filter_check(self)
        import size_pg17
        self.result['numeric_size_pg17_checks']=size_pg17.run(self)
        import stream_size_pg17
        self.result['proposed_capacity_pg17']=stream_size_pg17.run(self)['status']
        self.command('capacity-proposal',['env','PYTHONPATH='+str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),sys.executable,'-B',str(folder/'test_capacity_proposal.py')])
        self.command('numeric-size-unit',['env','PYTHONPATH='+str(self.sources/'supabase/.temp/phase6e11-pg17-parser'),sys.executable,'-B',str(folder/'test_size_diagnosis.py')])
        import ci_auth,database_tests,server,subprocess,threading
        with ci_auth.environment(self) as ctx:
            row=ctx['admin'].execute("select relrowsecurity,relforcerowsecurity from pg_class where oid='auth.sessions'::regclass").fetchone()
            self.save('integration-auth-table-security.json',{'auth_sessions':row,'auth_objects_changed':False,
                'session_check':'server verifies exact token sub/session before restricted app role; no new Auth grant or policy'})
            def browser(store,workspaces):
                import release_selection_http
                selected=release_selection_http.run(store,workspaces,ctx['accounts'])
                self.save('release-selection-http.json',selected)
                self.result['release_selection_http_checks']=selected['checks']
                playwright=self.browser_dependencies()
                app=server.Application(store,[workspaces['A'],workspaces['B']],enabled=True)
                http=server.serve(app,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                try:
                    data={'url':'http://127.0.0.1:'+str(http.server_port),'accounts':ctx['accounts'],
                          'playwright':playwright,'screenshots':str(self.out)}
                    p=subprocess.run(['node',str(folder/'account_center_browser.cjs')],input=json.dumps(data),text=True,capture_output=True,timeout=120)
                    result=json.loads(p.stdout);self.save('account-center-browser.json',result)
                    if p.returncode or result['status']!='PASS':raise RuntimeError('account_center_browser')
                    self.result['account_center_browser_checks']=result['checks']
                    p=subprocess.run(['node',str(folder/'browser_checks.cjs')],input=json.dumps(data),text=True,capture_output=True,timeout=120)
                    result=json.loads(p.stdout)
                    self.save('integration-browser.json',result)
                    if p.returncode or result['status']!='PASS':raise RuntimeError('integration_browser')
                    self.result['integration_browser_checks']=result['checks']
                finally:http.shutdown();http.server_close();thread.join(timeout=5)
                from composed_store import ComposedStore
                from registration_store import RegistrationStore
                from store import Store
                primary=Store(ctx['dsn'],ctx['auth'],enabled=True,full_day21=False)
                historical=RegistrationStore(ctx['dsn'],ctx['auth'],{workspaces['historical']:ctx['claims']['b']['sub']},enabled=True,journey=True)
                joined=ComposedStore(primary,[workspaces['joinedB']],historical)
                joined_app=server.Application(joined,[workspaces['joinedB'],workspaces['historical']],enabled=True)
                http=server.serve(joined_app,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                try:
                    data={'url':'http://127.0.0.1:'+str(http.server_port),'accounts':ctx['accounts'],
                          'playwright':playwright,'screenshots':str(self.out)}
                    p=subprocess.run(['node',str(folder/'composed_browser.cjs')],input=json.dumps(data),text=True,capture_output=True,timeout=180)
                    result=json.loads(p.stdout);self.save('composed-browser.json',result)
                    if p.returncode or result['status']!='PASS':raise RuntimeError('composed_browser')
                    self.result['composed_browser_checks']=result['checks']
                    p=subprocess.run(['node',str(folder/'offline_shell_browser.cjs')],input=json.dumps(data),text=True,capture_output=True,timeout=180)
                    result=json.loads(p.stdout);self.save('offline-shell-browser.json',result)
                    if p.returncode or result['status']!='PASS':raise RuntimeError('offline_shell_browser')
                    self.result['offline_shell_browser_checks']=result['checks']
                finally:http.shutdown();http.server_close();thread.join(timeout=5)
            result=database_tests.run(ctx['dsn'],ctx['auth'],ctx['tokens'],ctx['claims'],ctx['admin'],'real_local_GoTrue',browser)
            self.save('integration-database.json',result);self.result['integration_database_tests']=result['tests']
            auth=ci_auth.auth_checks(ctx);self.save('integration-auth.json',auth)
            self.result['integration_auth_tests']=len(auth['checks'])
        self.result['integration_scope']='LOCAL_CI_ONLY; no hosted admission; no owner acceptance'
    def advisors(self):
        base.Gate.advisors(self)
        funcs=self.rows("select proname,prosecdef,proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e_integration_private'")
        if len(funcs)!=3 or any(f['prosecdef'] or f['proconfig']!=['search_path=pg_catalog, pg_temp'] for f in funcs):raise RuntimeError('candidate_functions')
        roles=self.rows("select rolcanlogin,rolsuper,rolbypassrls from pg_roles where rolname='fmz6e_integration_server'")
        if roles!=[{'rolcanlogin':False,'rolsuper':False,'rolbypassrls':False}]:raise RuntimeError('candidate_role')
        memberships=self.rows("select member::regrole::text member,grantor::regrole::text grantor,admin_option,inherit_option,set_option from pg_auth_members where roleid='fmz6e_integration_server'::regrole")
        self.save('integration-role-memberships.json',memberships)
        # PG17 retains the creator's ADMIN-only grant from supabase_admin.
        # It is separate from the explicit SET-only local server membership.
        expected={('postgres','postgres',False,False,True),
                  ('postgres','supabase_admin',True,False,False)}
        actual={(x['member'],x['grantor'],x['admin_option'],x['inherit_option'],x['set_option']) for x in memberships}
        if actual!=expected or len(memberships)!=2:raise RuntimeError('candidate_membership')
        self.save('integration-security.json',{'functions':funcs,'roles':roles,'memberships':memberships,'Data_API_exposed':False})

if __name__=='__main__':sys.exit(Gate().run())
