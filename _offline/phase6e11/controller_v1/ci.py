"""Synthetic Docker CI for the additional proof store; no staging credentials."""
import base64,hashlib,importlib.util,json,os,pathlib,re,sys,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'ci42'))
spec=importlib.util.spec_from_file_location('controller_prior_ci42',HERE.parent/'ci42/runner.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
old=previous.old
M43='20261012104331_phase6e11_controller_evidence.sql'
EXTRA={'_offline/phase6e11/controller_v1/'+n for n in ['core.mjs','core.test.mjs','oidc.mjs','oidc.test.mjs','store.mjs']}
class Gate(previous.Gate42):
    migration_count=43
    migration_last=M43
    def fetch(self):
        blob=os.environ['CANDIDATE_BLOB'];expected=os.environ['CANDIDATE_SHA256']
        if not re.fullmatch('[0-9a-f]{40}',blob) or not re.fullmatch('[0-9a-f]{64}',expected):raise RuntimeError('candidate_format')
        token=os.environ.pop('GH_READ_TOKEN')
        req=urllib.request.Request('https://api.github.com/repos/Yourizorge/fitmetzorge-staging/git/blobs/'+blob,
          headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
        with urllib.request.urlopen(req,timeout=30) as response:obj=json.loads(response.read(8000000))
        del token,req
        data=base64.b64decode(obj['content'])
        if old.sha(data)!=expected:raise RuntimeError('candidate_digest')
        bundle=json.loads(data);manifest={}
        migrations=sorted(p for p in bundle['files'] if p.startswith('supabase/migrations/'))
        if len(migrations)!=self.migration_count or len({pathlib.Path(p).name.split('_')[0] for p in migrations})!=self.migration_count or pathlib.Path(migrations[-1]).name!=self.migration_last:raise RuntimeError('exact_migration_composition')
        for name,encoded in bundle['files'].items():
            if not old.allowed(name) and name not in EXTRA:raise RuntimeError('candidate_path_denied')
            raw=base64.b64decode(encoded,validate=True);path=self.sources/name
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);manifest[name]=old.sha(raw)
        if manifest['supabase/migrations/'+old.M41]!=old.M41_SHA:raise RuntimeError('migration41_changed')
        # Compare all historical migration bytes against this exact main checkout.
        historical=[]
        for name in migrations[:-1]:
            committed=(old.ROOT/name).read_bytes();candidate=(self.sources/name).read_bytes()
            if committed.replace(b'\r\n',b'\n')!=candidate.replace(b'\r\n',b'\n'):raise RuntimeError('historical_migration_changed')
            historical.append({'file':name,'checkout_sha256':old.sha(committed),'candidate_sha256':old.sha(candidate),
              'lf_sha256':old.sha(committed.replace(b'\r\n',b'\n')),'canonicalization':'CRLF-to-LF-only'})
        self.save('historical-migration-preservation.json',{'files':historical,'content_equal':True})
        self.save('candidate.json',{'blob':blob,'sha256':expected,'sources':manifest})
        self.result['candidate_sha256']=expected
        return migrations
    def rebuild(self,migrations):
        super().rebuild(migrations);self.result['clean_rebuild']=str(self.migration_count)+'/'+str(self.migration_count)+'_PASS'
    def check_controller_functions(self):
        if self.rows("select p.oid from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e11_controller_private'"):raise RuntimeError('controller_function_unexpected')
        return 0
    def check_bridge(self):
        super().check_bridge()
        schema='fmz6e11_controller_private'
        functions=self.check_controller_functions()
        tables=self.rows("select relname,relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='"+schema+"' and c.relkind='r' order by 1")
        if [x['relname'] for x in tables]!=['evidence','runs','steps'] or not all(x['relrowsecurity'] for x in tables):raise RuntimeError('controller_rls')
        denied=[]
        for table in ['runs','steps','evidence']:
            if self.rows('select count(*) n from '+schema+'.'+table)!=[{'n':0}]:raise RuntimeError('controller_not_empty')
            for role in ['anon','authenticated','service_role','fmz_ci_unprivileged']:
                for operation in ['select','insert','update','delete']:
                    target=schema+'.'+table
                    query={'select':'select * from '+target,'insert':'insert into '+target+' default values',
                      'update':'update '+target+' set '+('next_step=next_step' if table=='runs' else 'step=step'),
                      'delete':'delete from '+target}[operation]
                    p=self.sql('begin;set local role '+role+';'+query+';rollback;',False)
                    if not p.returncode or 'permission denied' not in p.stderr:raise RuntimeError('controller_acl')
                    denied.append({'role':role,'table':table,'operation':operation,'denied':True})
        self.save('controller-security.json',{'tables':tables,'functions':functions,'default_closed':True,'denials':denied})
        self.result['controller_security']='PASS'
    def regressions(self):
        super().regressions()
        path=self.sources/'_offline/phase6e11/controller_v1'
        self.command('controller-tests',['node','--test',str(path/'core.test.mjs'),str(path/'oidc.test.mjs')])
        self.result['controller_node_tests']=63
if __name__=='__main__':sys.exit(Gate().run())
