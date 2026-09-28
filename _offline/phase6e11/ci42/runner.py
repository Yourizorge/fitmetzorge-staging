"""Clean 1..42 admission, reusing the immutable CI41 gate and real extensions."""
import base64,hashlib,json,os,pathlib,re,sys,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'ci41'))
import runner as old
M42='20260928120846_phase6e11_request_binding.sql'
class Gate42(old.Gate):
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
        if len(migrations)!=42 or len({pathlib.Path(p).name.split('_')[0] for p in migrations})!=42 or pathlib.Path(migrations[-1]).name!=M42:
            raise RuntimeError('exactly_42_unique')
        for name,encoded in bundle['files'].items():
            if not old.allowed(name):raise RuntimeError('candidate_path_denied')
            raw=base64.b64decode(encoded,validate=True);path=self.sources/name
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);manifest[name]=old.sha(raw)
        if manifest['supabase/migrations/'+old.M41]!=old.M41_SHA:raise RuntimeError('migration41_changed')
        self.save('candidate.json',{'blob':blob,'sha256':expected,'sources':manifest})
        self.result['candidate_sha256']=expected
        return migrations
    def rebuild(self,migrations):
        super().rebuild(migrations)
        self.result['clean_rebuild']='42/42_PASS'
        if self.result['platform']['server'][0]['num']!='170006':raise RuntimeError('exact_PG17_6_required')
    def check_bridge(self):
        super().check_bridge()
        s='fmz6e11_request_private'
        funcs=self.rows("select proname,prosecdef,proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='"+s+"'")
        if len(funcs)!=5 or any(f['prosecdef'] or f['proconfig']!=['search_path=pg_catalog, pg_temp'] for f in funcs):raise RuntimeError('request_function_boundary')
        if self.rows('select enabled,expires_at from '+s+'.control')!=[{'enabled':False,'expires_at':None}]:raise RuntimeError('request_default_off')
        if self.rows("select table_name from fmz6e11_audit_private.relations where table_name ~ '^(auth|storage|realtime)\\.'"):raise RuntimeError('managed_observers')
        missing=self.rows("select n.nspname,c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname in ('public','fmz6e11_private') and not exists(select 1 from fmz6e11_audit_private.relations r where r.rel=c.oid)")
        if missing:raise RuntimeError('application_write_coverage')
        denied=[]
        for role in ('anon','authenticated','service_role','fmz_ci_unprivileged'):
            for target in ('select * from '+s+'.receipts','select '+s+".call('{}',gen_random_uuid())",'select '+s+'.seal(gen_random_uuid())'):
                p=self.sql('begin;set local role '+role+';'+target+';rollback;',False)
                if not p.returncode or 'permission denied' not in p.stderr:raise RuntimeError('request_acl_failure')
                denied.append({'role':role,'target':target,'denied':True})
        self.save('request-security.json',{'functions':funcs,'denials':denied,'managed_observers':0,'missing_application_observers':0,'default_off':True})
        self.result['request_security']='PASS'
if __name__=='__main__':sys.exit(Gate42().run())
