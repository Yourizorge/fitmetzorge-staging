"""Fresh source-bound clean Supabase CI. No hosted access or staging secrets."""
import contextlib,hashlib,importlib.util,json,pathlib,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard_previous_controller_ci',HERE.parent/'controller_v1/ci.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
CONTROLLER_NAMES=['core.mjs','core.test.mjs','oidc.mjs','oidc.test.mjs','store.mjs','auth.mjs','auth.test.mjs',
 'auth_guard.mjs','auth_guard.test.mjs','manifest.mjs','manifest.test.mjs','workflow_evidence.mjs',
 'workflow_evidence.test.mjs','forensic.test.mjs']
GUARD_NAMES=['guard.py','checks.py','issuance.mjs','issuance.test.mjs','ci.py','local.py']
EXTRA={'_offline/phase6e11/controller_v1/'+n for n in CONTROLLER_NAMES}
EXTRA|={'_offline/phase6e11/controller_guard_v1/'+n for n in GUARD_NAMES}
EXTRA|={'_offline/phase6e11/edge_bridge_v2/handler.mjs',*('_offline/phase6e11/edge/'+n for n in ['handler.mjs','core.mjs','frozen.mjs'])}
old.EXTRA|=EXTRA

class Gate(old.Gate):
    def fetch(self):
        migrations=super().fetch()
        files=json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA<=set(files):raise RuntimeError('full_guard_composition_missing')
        self.save('guard-composition.json',{'sources':{n:files[n] for n in sorted(EXTRA)},
            'controller_full_source_bound':True,'hosted_auth_proven':False})
        return migrations
    def regressions(self):
        super().regressions()
        tests=sorted((self.sources/'_offline/phase6e11/controller_v1').glob('*.test.mjs'))
        tests+=sorted((self.sources/'_offline/phase6e11/controller_guard_v1').glob('*.test.mjs'))
        output=self.command('full-controller-guard-tests',['node','--test','--test-reporter=tap',*map(str,tests)])
        import re
        count=re.search(r'# tests (\d+)',output.stdout)
        if not count or int(count[1])!=186:raise RuntimeError('full_node_count')
        self.result['full_controller_guard_node_tests']=186
        folder=self.sources/'_offline/phase6e11/controller_guard_v1'
        spec=importlib.util.spec_from_file_location('guard',folder/'guard.py')
        g=importlib.util.module_from_spec(spec);sys.modules['guard']=g;spec.loader.exec_module(g)
        spec=importlib.util.spec_from_file_location('guard_database_checks',folder/'checks.py')
        checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
        def args(actor):
            if actor=='supabase_auth_admin':
                # This is the disposable container's own local credential, not
                # a staging secret. Peer/socket auth is intentionally denied.
                return ['docker','exec','-i',self.container,'sh','-c',
                    'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X -h 127.0.0.1 -U supabase_auth_admin -d postgres -qAt -v ON_ERROR_STOP=1']
            return ['docker','exec','-i',self.container,'psql','-X','-U',actor,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
        def sql(q,actor='postgres'):
            if actor in ('anon','authenticated','service_role'):
                q='set role '+actor+';'+q;actor='postgres'
            return self.command('guard-check',args(actor),sql="set lock_timeout='200ms';set statement_timeout='5s';"+q,timeout=15,check=False)
        @contextlib.contextmanager
        def hold(q):
            p=subprocess.Popen(args('postgres'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                p.stdin.write(q+"\nselect 'fmz_guard_held';\n");p.stdin.flush()
                while p.stdout.readline().strip()!='fmz_guard_held':
                    if p.poll() is not None:raise RuntimeError('hold_failed')
                yield
            finally:
                try:p.communicate('rollback;\n',timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.communicate()
        result=checks.run(sql,hold)
        self.save('temporary-guard-database.json',result)
        if result['checks']!=26 or result['guard_objects_remaining']!=0:raise RuntimeError('guard_database_incomplete')
        self.result['temporary_guard_database']=result['status'];self.result['temporary_guard_checks']=result['checks']
if __name__=='__main__':sys.exit(Gate().run())
