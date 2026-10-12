"""Complete the existing 45-step local fixture with exact bounded delete batches.
Disposable PG17 only. Does not connect to staging or authorize a hosted run.
"""
import collections,hashlib,json,pathlib,sys,uuid
from local_native import EndchainRequests,n,r
from scenario import capture

TABLES=('inbox_state','events','proposals','source_heads','source_versions',
        'plans','b_versions','b_states','audit','requests','participants','workspaces')
class CleanupRequests(EndchainRequests):
    cleaning=False
    def __init__(self,folder):
        super().__init__(folder)
        self.bound_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [pathlib.Path(__file__),pathlib.Path(__file__).with_name('local_native.py'),
             pathlib.Path(__file__).with_name('request_transport.mjs'),
             pathlib.Path(__file__).with_name('native_local_driver.ts'),r.M40,r.M41,r.M42]}
        r.save(folder/'cleanup-sources.json',self.bound_sources)
    def body(self,action,data=None,x=None):
        if not self.cleaning:return super().body(action,data,x)
        rows=self.rows('select revision from fmz6e11_private.windows where id='+r.lit(self.w))
        if len(rows)!=1 or not isinstance(rows[0]['revision'],int):raise r.Stop('cleanup_window_revision_missing')
        return {'op':'command','window':self.w,'workspace':x or self.x,'key':str(uuid.uuid4()),
            'expected':rows[0]['revision'],'action':action,'data':data or {}}
    def revisions(self):
        if not self.cleaning:return super().revisions()
        return self.rows("select coalesce(fmz6e11_workflow_audit.versions("+r.lit(self.w)+"),'{}') value")[0]['value']
    def base_contract(self,role,q,outcome='committed',effects=()):
        if q['action']=='cleanup_batch':return list(effects)
        if q['action']=='revoke':
            return [('windows','UPDATE',[self.w]),('windows','UPDATE',[self.w]),
                ('audit','INSERT',[self.w,r.uid(2),'revoke']),
                ('requests','INSERT',[r.uid(2),q['key']])]
        return super().base_contract(role,q,outcome,effects)
    def perform(self,*args,**kwargs):
        if any(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()!=h for p,h in self.bound_sources.items()):
            raise r.Stop('cleanup_source_changed')
        value=super().perform(*args,**kwargs)
        if self.serial==45 and not self.cleaning:self.cleanup()
        return value
    def cleanup(self):
        self.cleaning=True
        protected={t:v for t,v in self.snapshot().items() if t.startswith(('auth.','public.'))}
        initial=self.rows("select name,count(*) n from ("+
            " union all ".join("select "+r.lit(t)+" name from fmz6e11_private."+t for t in TABLES)+
            ") x group by name order by name")
        self.cleanup_manifest=[]
        self.perform('revoke own synthetic window','trainer',self.body('revoke'))
        for t in TABLES:
            by_window=t in ('audit','requests','participants')
            for x in ([self.x] if by_window else [self.b,self.x]):
                column='window_id' if by_window else 'id' if t=='workspaces' else 'workspace_id'
                value=self.w if by_window else x
                # Same locked selection order/limit as M42; never guess surrogate keys.
                rows=self.rows("select fmz6e11_audit_private.project_key(t,r.pk_columns) key "
                    "from fmz6e11_private."+t+" t cross join fmz6e11_audit_private.relations r "
                    "where r.table_name="+r.lit('fmz6e11_private.'+t)+" and t."+column+"="+r.lit(value)+
                    " order by t.ctid")
                for offset in range(0,len(rows),8):
                    batch=rows[offset:offset+8]
                    effects=[(t,'DELETE',v['key']) for v in batch]
                    q=self.body('cleanup_batch',{'table':t},x=x)
                    before=len(self.pairs)
                    result=self.perform('cleanup '+t+' '+str(offset),'trainer',q,effects)
                    if result.get('deleted')!=len(batch):raise r.Stop('cleanup_delete_count')
                    proof=self.pairs[before]
                    if proof['committed_operations']!={'INSERT':0,'UPDATE':0,'DELETE':len(batch)}:
                        raise r.Stop('cleanup_extra_write')
                    self.cleanup_manifest.append({'table':t,'workspace':x,'rows':len(batch),
                        'request_id':proof['request_id'],'xid':str(proof['receipt']['xid'])})
        remaining=self.rows("select name from ("+" union all ".join(
            "select "+r.lit(t)+" name from fmz6e11_private."+t for t in TABLES)+") x")
        if remaining:raise r.Stop('cleanup_rows_remaining')
        if protected!={t:v for t,v in self.snapshot().items() if t.startswith(('auth.','public.'))}:
            raise r.Stop('cleanup_protected_drift')
        r.save(self.folder/'endchain-cleanup-result.json',{
            'status':'LOCAL_EXISTING_CLEANUP_PASS','product_pairs':45,
            'revoke_pairs':1,'delete_batch_pairs':len(self.cleanup_manifest),
            'deleted_rows':sum(x['rows'] for x in self.cleanup_manifest),
            'batches':self.cleanup_manifest,'initial_counts':initial,
            'remaining_app_fixture_rows':0,'protected_equal':True,
            'request_commands':6*self.serial,'hosted_calls':0,'hosted_admitted':False,
            'remaining':['window lifecycle delete','Auth lifecycle','controller evidence overhead','IO ledger'],
            'scope':'local PG17 synthetic rows with local Auth stubs; window intentionally retained for local lifecycle tests'})
        print(json.dumps({'status':'LOCAL_EXISTING_CLEANUP_PASS',
            'batches':len(self.cleanup_manifest),'directory':str(self.folder)}),flush=True)

def main():
    r.enable_local_tls=n.local_ca_and_leaf;r.existing.Workflow=CleanupRequests
    return r.existing.main()
if __name__=='__main__':sys.exit(main())
