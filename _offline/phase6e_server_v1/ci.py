"""Clean 44 preserved migrations + one isolated candidate; zero hosted access."""
import hashlib,importlib.util,json,pathlib,re,shutil,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('integration_prior_ci',HERE.parent/'phase6e11/endchain_v1/ci.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
base=previous.prior.old.old
M45='20261014105919_phase6e_synthetic_server_candidate.sql'
NEW=['domain.cjs','domain.test.cjs','worker.cjs','store.py','database_tests.py','ci.py','ci_auth.py',
     'server.py','ui.html','ui.js','ui.css','browser_checks.cjs','protocol.py','test_protocol.py','supabase/migrations/'+M45]
EXTRA={'_offline/phase6e_server_v1/'+p for p in NEW}
EXTRA.add('assets/fit-met-zorge-logo-cropped.png')
pending=[HERE/'domain.cjs'];seen=set()
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
            return cli_meter.run(self,actual,timeout)
        return base.Gate.cli(self,*args,timeout=timeout)
    def rebuild(self,migrations):
        super().rebuild(migrations)
        path=self.sources/'_offline/phase6e_server_v1/supabase/migrations'/M45
        shutil.copyfile(path,self.work/'supabase/migrations'/M45)
        self.result['phase']='local_candidate_45'
        self.cli('migration','up','--local')
        history=self.rows('select version from supabase_migrations.schema_migrations order by version')
        if len(history)!=45 or history[-1]['version']!=M45.split('_')[0]:raise RuntimeError('candidate_history')
        self.save('candidate-45-history.json',{'history':history,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'hosted_applied':False})
        self.result['clean_rebuild']='45/45_PASS_LOCAL_CANDIDATE';self.result['migrations_applied']=45
    def regressions(self):
        # Existing SQL/audit regressions remain mandatory; no second 6E-11 run.
        base.Gate.regressions(self)
        folder=self.sources/'_offline/phase6e_server_v1';sys.path.insert(0,str(folder))
        self.command('integration-protocol',[sys.executable,'-B',str(folder/'test_protocol.py')])
        output=self.command('integration-domain',['node','--test',str(folder/'domain.test.cjs')])
        count=re.search(r'# tests (\d+)',output.stdout)
        if not count:raise RuntimeError('domain_count')
        self.result['integration_domain_tests']=int(count[1])
        import ci_auth,database_tests,server,subprocess,threading
        with ci_auth.environment(self) as ctx:
            row=ctx['admin'].execute("select relrowsecurity,relforcerowsecurity from pg_class where oid='auth.sessions'::regclass").fetchone()
            self.save('integration-auth-table-security.json',{'auth_sessions':row,'auth_objects_changed':False,
                'session_check':'server verifies exact token sub/session before restricted app role; no new Auth grant or policy'})
            def browser(store,workspaces):
                deps=self.work/'browser-deps'
                self.command('integration-playwright',['npm','install','--prefix',str(deps),'--no-audit','--no-fund','playwright@1.56.1'],timeout=120)
                self.command('integration-chromium',['node',str(deps/'node_modules/playwright/cli.js'),'install','--with-deps','chromium'],timeout=180)
                app=server.Application(store,[workspaces['A'],workspaces['B']],enabled=True)
                http=server.serve(app,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                try:
                    data={'url':'http://127.0.0.1:'+str(http.server_port),'accounts':ctx['accounts'],
                          'playwright':str(deps/'node_modules/playwright'),'screenshots':str(self.out)}
                    p=subprocess.run(['node',str(folder/'browser_checks.cjs')],input=json.dumps(data),text=True,capture_output=True,timeout=120)
                    result=json.loads(p.stdout)
                    self.save('integration-browser.json',result)
                    if p.returncode or result['status']!='PASS':raise RuntimeError('integration_browser')
                    self.result['integration_browser_checks']=result['checks']
                finally:http.shutdown();http.server_close();thread.join(timeout=5)
            result=database_tests.run(ctx['dsn'],ctx['auth'],ctx['tokens'],ctx['claims'],ctx['admin'],'real_local_GoTrue',browser)
            self.save('integration-database.json',result);self.result['integration_database_tests']=result['tests']
            auth=ci_auth.auth_checks(ctx);self.save('integration-auth.json',auth)
            self.result['integration_auth_tests']=len(auth['checks'])
        self.result['integration_scope']='LOCAL_CI_ONLY; no hosted admission; no owner acceptance'
    def advisors(self):
        base.Gate.advisors(self)
        funcs=self.rows("select proname,prosecdef,proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e_integration_private'")
        if len(funcs)!=2 or any(f['prosecdef'] or f['proconfig']!=['search_path=pg_catalog, pg_temp'] for f in funcs):raise RuntimeError('candidate_functions')
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
