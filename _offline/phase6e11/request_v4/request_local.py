"""V4 request transaction through the real PG driver. Disposable local stubs only."""
import json,os,pathlib,subprocess,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'edge_bridge_v2'))
from local_driver import enable_local_tls
sys.path.insert(0,str(HERE.parent/'readiness_v1/workflow_audit_v1'))
import workflow_local as existing
from workflow_local import Workflow,ServerBoundary,uid,lit,js,digest,sha,save,ROOT,A,Stop,Journal
M42=ROOT/'supabase/migrations/20260928120846_phase6e11_request_binding.sql'
M41=ROOT/'supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql'
M40=ROOT/'supabase/migrations/20260924130052_phase6e11_private_transaction_audit.sql'
LAST=None
class Requests(Workflow):
    def __init__(self,folder):
        global LAST
        LAST=self;self.folder=folder;self.serial=0;self.pairs=[];self.sql=ServerBoundary.sql;self.run=str(uuid.uuid4())
        for path in (M40,M41,M42):
            p=self.sql(path.read_text(encoding='utf-8-sig'),success=False)
            if p.returncode:raise Stop('install:'+path.name+':'+p.stderr[:600])
        self.sql("update fmz6e11_request_private.control set enabled=true,expires_at=now()+interval '1 hour';")
        self.tables=self.rows("select n.nspname||'.'||c.relname name from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname in ('fmz6e11_private','auth','public') order by 1")
        self.w=ServerBoundary.window;self.x=ServerBoundary.workspaces['A'];self.b=ServerBoundary.workspaces['B']
        self.ca=enable_local_tls(self)
        self.m41_sha=sha(M41)
        self.m42_sha=sha(M42)
    def invoke(self,request,role,rid):
        i={'member':1,'trainer':2,'b':3}[role]
        claims={'sub':uid(i),'session_id':uid(i+100),'iss':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',
                'aud':'authenticated','role':'authenticated','exp':int(time.time())+3600}
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        p=subprocess.run([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(HERE.parent/'edge_bridge_v2/deno.lock'),'--allow-net=127.0.0.1:'+str(ServerBoundary.cluster.port),
          '--allow-read='+str(self.ca),'--allow-env=PGHOST,PGPORT,PGDATABASE,PGUSERNAME,PGUSER,PGPASSWORD,PGSSLMODE,PGTARGETSESSIONATTRS,PGTARGET_SESSION_ATTRS,PGAPPNAME,PGCONNECT_TIMEOUT,PGIDLE_TIMEOUT,PGMAX_LIFETIME,PGMAX_PIPELINE,PGBACKOFF,PGKEEP_ALIVE,PGDEBUG,PGPUBLICATIONS,PGOPTIONS,USERNAME,USER,LOGNAME,NODE_DEBUG,NODE_EXTRA_CA_CERTS',
          str(HERE/'local_driver.ts')],input=json.dumps({'input':request,'claims':claims,'request_id':rid,'ca':str(self.ca),'port':ServerBoundary.cluster.port}),
          env=env,encoding='utf8',capture_output=True,timeout=25,creationflags=0x08000000 if os.name=='nt' else 0)
        if p.returncode:
            save(self.folder/('driver-error-'+str(self.serial)+'.json'),{'stdout':p.stdout,'stderr':p.stderr,'local_synthetic_only':True})
            raise Stop('request_driver:'+p.stdout[:400]+p.stderr[:200])
        return json.loads(p.stdout)['receipt']
    def perform(self,label,role,q,effects=(),outcome='committed',input_body=None,expected_http=200,inject=None):
        self.serial+=1;rid=str(uuid.uuid4());before=self.snapshot();vb=self.revisions()
        folder=self.folder/f'action-{self.serial:03d}';folder.mkdir()
        journal=Journal(folder/'journal',{'run':self.run,'action':rid})
        journal.record('before_saved',{'snapshot':before,'versions':vb,'expected_workflow_effects':self.base_contract(role,q,outcome,effects)})
        request=input_body or (self.b_input(q) if q['action'].startswith('b_') else q)
        journal.record('action_started',{'request_id':rid,'auth':'local stub, no hosted authorization claim'})
        try:receipt=self.invoke(request,role,rid)
        except BaseException as e:
            save(folder/'after-error.json',{'snapshot':self.snapshot(),'versions':self.revisions()})
            journal.halt('driver',str(e));raise
        journal.record('action_confirmed',{'receipt':receipt})
        after=self.snapshot();va=self.revisions()
        r=self.rows('select to_jsonb(r) r from fmz6e11_request_private.receipts r where request_id='+lit(rid))[0]['r']
        writes=self.rows('select * from '+A+'.writes where action_id='+lit(r['action_id'])+' order by ordinal')
        journal.record('after_saved',{'snapshot':after,'versions':va,'receipt':r,'writes':writes})
        if receipt.get('http_status',200)!=expected_http:raise Stop('http:'+label+':'+str(receipt))
        expected=r['branches'][outcome]
        actual=[{'table':v['table_name'],'op':v['operation'],'old':v['old_key_sha'],'new':v['new_key_sha']} for v in writes]
        if sorted(expected,key=digest)!=sorted(actual,key=digest):raise Stop('write_multiset:'+label)
        # Independently compare the existing, preregistered 45-action contract.
        independently=[]
        for t,op,key in self.base_contract(role,q,outcome,effects):
            h=self.sql('select '+A+'.pk_hash('+lit(r['run_id'])+','+lit('fmz6e11_private.'+t)+','+js(key)+');').stdout.strip()
            independently.append({'table':'fmz6e11_private.'+t,'op':op,'old':h if op!='INSERT' else None,'new':h if op!='DELETE' else None})
        if sorted(independently,key=digest)!=sorted(actual,key=digest):raise Stop('independent_contract:'+label)
        if any(str(v['xid'])!=str(r['xid']) or v['backend']!=r['backend'] or v['actor']!=r['actor'] for v in writes):raise Stop('xid_binding')
        allowed={v['table'] for v in actual}
        if any(before[t]!=after[t] for t in before if t not in allowed):raise Stop('protected_drift')
        if r['state']!='pair_validated' or sha(M41)!=self.m41_sha or sha(M42)!=self.m42_sha:raise Stop('receipt_or_frozen')
        proof={'label':label,'request_id':rid,'receipt':r,'expected':independently,'actual':actual,'versions_before':vb,'versions_after':va,
               'forbidden_table_writes':0,'committed_operations':{op:sum(v['op']==op for v in actual) for op in ('INSERT','UPDATE','DELETE')}}
        journal.record('pair_validated',proof);seal=save(folder/'receipt.json',proof)
        journal.record('next_step_allowed',{'sha256':seal,'hosted_admission':False});self.pairs.append(proof)
        print(json.dumps({'pair':self.serial,'label':label,'writes':len(actual),'status':'LOCAL_REQUEST_PASS'}),flush=True)
        return receipt
def main():
    existing.Workflow=Requests
    code=existing.main()
    if code==0:
        save(LAST.folder/'request-v4-result.json',{'status':'LOCAL_REQUEST_45_PASS','pairs':len(LAST.pairs),'m42':sha(M42),'m41':sha(M41),
              'driver':'postgres@3.4.7','postgres':'17.6','auth':'local stubs only','hosted_admission':False})
    return code
if __name__=='__main__':sys.exit(main())
