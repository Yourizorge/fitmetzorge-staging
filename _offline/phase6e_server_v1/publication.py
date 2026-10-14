"""Verify candidate isolation on staging Pages; never accesses Supabase."""
import importlib.util,json,pathlib,sys,urllib.error,urllib.request,uuid
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('local_candidate_github',HERE/'ops.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ops.ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):raise RuntimeError('scope')
    head=ops.g.git('rev-parse','HEAD');remote=ops.g.git('ls-remote','origin','refs/heads/main').split()[0]
    if head!=remote or ops.g.git('branch','--show-current')!='main':raise RuntimeError('git_binding')
    names=ops.g.git('ls-files','--','_offline/phase6e_server_v1').splitlines()
    names+=['.github/workflows/phase6e-server-local-ci.yml']
    if not names or any(not n.startswith(('_offline/phase6e_server_v1/','.github/')) for n in names):raise RuntimeError('path_binding')
    result={'head':head,'remote_head':remote,'status':'INCOMPLETE','private':[],'supabase_calls':0}
    try:
        opener=urllib.request.build_opener(NoRedirect())
        for name in sorted(names):
            req=urllib.request.Request('https://yourizorge.github.io/fitmetzorge-staging/'+name+'?local-candidate='+head,method='HEAD')
            try:
                with opener.open(req,timeout=15) as r:status=r.status
            except urllib.error.HTTPError as e:status=e.code
            result['private'].append({'path':name,'status':status})
            if status!=404:raise RuntimeError('candidate_public')
        runs=ops.g.api('/actions/runs?per_page=50')['workflow_runs']
        result['pages']=[{k:r[k] for k in ('id','head_sha','status','conclusion','html_url')} for r in runs if r['head_sha']==head and 'pages' in r['name'].lower()]
        if not any(r['conclusion']=='success' for r in result['pages']):raise RuntimeError('pages_not_success')
        result['status']='PAGES_ISOLATION_PASS'
    finally:
        ops.g.write(ops.disk(folder/('local-candidate-pages-'+uuid.uuid4().hex+'.json')),result)
    print(json.dumps({'status':result['status'],'head':head,'private404':len(result['private']),'pages':result['pages']}))
if __name__=='__main__':main()
