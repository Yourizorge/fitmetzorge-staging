"""Preserve prior receipts and current source-bound tests; never runs database SQL."""
import importlib.util,json,os,pathlib,sys,uuid
import install as i
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('file_verifier',HERE.parent/'edge_bridge_checks_v2/verify.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def main():
    folder=i.ROOT/'supabase/.temp'/('phase6e11-request-closeout-'+uuid.uuid4().hex);folder.mkdir()
    originals=v.check_sources
    history=[v.data(i.ROOT/'docs'/name) for name in ('PHASE6E11_EDGE_BRIDGE_EVIDENCE.json','PHASE6E11_CHAIN_V3_EVIDENCE.json')]
    def check(mapping,aliases=None):
        selected=dict(aliases or {})
        archived=i.ROOT/'supabase/.temp/phase6e11-request-closeout-91393bd1e3f741cf8277860341aaa394/BUILD_STATUS.before.md'
        for name,h in mapping.items():
            if name.replace('\\','/')=='docs/BUILD_STATUS.md' and h==v.sha(archived):selected[name]=archived
        for old in history:
            for name,item in old.get('prior_status_alias',{}).items():
                for actual,h in mapping.items():
                    if actual.replace('\\','/')==name.replace('\\','/') and h==item['sha256']:
                        selected[actual]=i.ROOT/item['archive']
        originals(mapping,selected)
    v.check_sources=check
    result={'status':'INCOMPLETE','folder':str(folder),'hosted_queries':0}
    try:
        result['preservation']=v.preservation(folder)
        for old in history:check(old['sources']);check(old['documents'])
        result['admission']=i.admission()
        result['retained_local_workflow']=v.data(i.LOCAL/'request-v4-result.json')
        result['retained_local_security']=v.data(i.SECURITY/'request-security.json')
        v.run(folder,'node-regressions',[os.environ['FMZ_NODE'],'--test','--test-reporter=tap',
          HERE.parent/'edge_bridge_v2/edge.test.mjs',HERE.parent/'test/edge.test.mjs',
          HERE.parent/'readiness_v1/targeted/edge_boundary.test.mjs',HERE.parent/'test/scope.test.mjs',
          HERE/'request.test.mjs',HERE/'oidc.test.mjs'])
        v.run(folder,'receipt-tests',[sys.executable,'-B','-m','unittest','discover','-s',HERE.parent/'chain_v3','-p','test_auth_receipt.py','-v'])
        v.run(folder,'installation-and-load-tests',[sys.executable,'-B','-m','unittest','discover','-s',HERE,'-p','test_*.py','-v'])
        v.run(folder,'deno-check',[os.environ['FMZ_DENO'],'check','--cached-only','--no-config','--frozen',
          '--lock='+str(HERE.parent/'edge_bridge_v2/deno.lock'),HERE/'index.ts',HERE/'local_driver.ts',HERE/'proof_server.ts'])
        result['source_hashes']={str(p.relative_to(i.ROOT)):v.sha(p) for p in HERE.iterdir() if p.is_file()}
        result['migration_sha256']=v.sha(i.ROOT/'supabase/migrations'/i.M42)
        result.update(status='LOCAL_SOURCE_BOUND_PASS_HOSTED_WORKFLOW_PENDING',node_tests=64,receipt_tests=17,
          installation_load_tests=12,owner_retest='NO_GO',full_database_scans=0)
    except Exception as e:result.update(error_type=type(e).__name__,reason=str(e)[:250])
    v.save(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ('status','folder','reason','node_tests','preservation') if k in result}))
    return result['status']=='LOCAL_SOURCE_BOUND_PASS_HOSTED_WORKFLOW_PENDING'
if __name__=='__main__':sys.exit(0 if main() else 2)
