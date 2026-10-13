"""Read-only GitHub Pages isolation receipt for the endchain candidate."""
import hashlib,importlib.util,json,pathlib,sys,urllib.error,urllib.request,uuid
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('endchain_pages_ops',HERE.parent/'controller_v1/ops.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)

def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=o.ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-endchain-'):
        raise RuntimeError('publication_output_scope')
    head=o.g.git('rev-parse','HEAD');remote=o.g.git('ls-remote','origin','refs/heads/main').split()[0]
    if head!=remote or o.g.git('branch','--show-current')!='main':raise RuntimeError('git_scope')
    # Include nested evidence as well as top-level test sources.
    paths=o.g.git('ls-files','--','_offline/phase6e11/endchain_v1').splitlines()
    if not paths or any(not p.startswith('_offline/phase6e11/endchain_v1/') for p in paths):
        raise RuntimeError('publication_path_scope')
    paths+=['.github/workflows/phase6e11-endchain-ci.yml',
        'supabase/migrations/20261012185121_phase6e11_single_endchain_budget.sql']
    result={'head':head,'remote_head':remote,'hidden':[],'supabase_calls':0}
    for path in sorted(paths):
        req=urllib.request.Request('https://yourizorge.github.io/fitmetzorge-staging/'+path+'?endchain='+head,method='HEAD')
        try:
            with urllib.request.urlopen(req,timeout=15) as res:status=res.status
        except urllib.error.HTTPError as error:status=error.code
        result['hidden'].append({'path':path,'status':status})
        if status!=404:raise RuntimeError('private_path_not_404')
    runs=o.g.api('/actions/runs?per_page=20')['workflow_runs']
    result['pages']=[{k:x.get(k) for k in ['id','head_sha','status','conclusion','html_url']}
        for x in runs if x['head_sha']==head and 'pages' in x['name'].lower()]
    result['status']='PUBLICATION_PASS' if any(x['conclusion']=='success' for x in result['pages']) else 'PAGES_PENDING'
    o.g.write(o.disk(folder/('endchain-publication-'+uuid.uuid4().hex+'.json')),result)
    print(json.dumps({k:result[k] for k in ['status','head','remote_head','pages']}|{'private404':len(result['hidden'])}))
if __name__=='__main__':main()
