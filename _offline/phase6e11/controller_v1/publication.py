"""Staging GitHub/Pages inspection only. Never connects to Supabase."""
import hashlib,importlib.util,json,pathlib,sys,urllib.request,urllib.error,uuid
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controller_publication_ops',HERE/'ops.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)

def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=o.ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-controller-'):raise RuntimeError('scope')
    head=o.g.git('rev-parse','HEAD');remote=o.g.git('ls-remote','origin','refs/heads/main').split()[0]
    if head!=remote or o.g.git('branch','--show-current')!='main':raise RuntimeError('git_scope')
    names=[p.relative_to(o.ROOT).as_posix() for p in HERE.iterdir() if p.is_file()]
    for folder_name in ('controller_guard_v1','auth_metadata_v1'):
        names += [p.relative_to(o.ROOT).as_posix() for p in (HERE.parent/folder_name).iterdir() if p.is_file()]
    names += ['.github/workflows/phase6e11-guard-ci.yml']
    names+=['supabase/migrations/'+o.ci.M43,'.github/workflows/phase6e11-controller-ci.yml']
    result={'head':head,'remote_head':remote,'hidden':[],'supabase_calls':0}
    for name in sorted(names):
        req=urllib.request.Request('https://yourizorge.github.io/fitmetzorge-staging/'+name+'?controller='+head,method='HEAD')
        try:
            with urllib.request.urlopen(req,timeout=15) as response:status=response.status
        except urllib.error.HTTPError as e:status=e.code
        result['hidden'].append({'path':name,'status':status})
        if status!=404:raise RuntimeError('private_path_not_404')
    runs=o.g.api('/actions/runs?per_page=20')['workflow_runs']
    result['pages']=[{k:r.get(k) for k in ['id','name','head_sha','status','conclusion','html_url']} for r in runs if r['head_sha']==head and 'pages' in r['name'].lower()]
    result['git_status']=o.g.git('status','--short');result['worktree_clean']=not result['git_status']
    result['status']='PUBLICATION_PASS' if any(r['conclusion']=='success' for r in result['pages']) else 'PAGES_PENDING'
    o.g.write(o.disk(folder/('publication-'+uuid.uuid4().hex+'.json')),result)
    print(json.dumps({k:result[k] for k in ['head','remote_head','status','pages','worktree_clean']}|{'private404':len(result['hidden'])}))
if __name__=='__main__':main()
