"""Source-only CI preparation. No hosted credentials or Supabase calls."""
import base64,hashlib,importlib.util,json,os,pathlib,re,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
import ci
from source_scan import check as check_source
spec=importlib.util.spec_from_file_location('endchain_github',HERE.parent/'ci41/ops.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROOT=g.ROOT
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def main():
    mode=sys.argv[1]
    if mode=='prepare':
        if g.git('branch','--show-current')!='main':raise RuntimeError('branch')
        folder=ROOT/'supabase/.temp'/('phase6e11-endchain-ci-'+uuid.uuid4().hex);folder.mkdir()
        paths=set(ci.prior.old.old.EXTRAS)|ci.prior.old.EXTRA
        paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/migrations').glob('*.sql')}
        paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/tests').glob('*.sql')}
        files={}
        for name in sorted(paths):
            raw=disk(ROOT/name).read_bytes()
            check_source(name,raw)
            files[name]=base64.b64encode(raw).decode()
        digest=g.write(disk(folder/'candidate.json'),{'format':1,'files':files})
        g.write(disk(folder/'before.json'),{'head':g.git('rev-parse','HEAD'),'branch':'main','hosted_calls':0})
        print(json.dumps({'folder':str(folder),'sha256':digest,'files':len(files)}));return
    folder=pathlib.Path(sys.argv[2]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-endchain-ci-'):raise RuntimeError('scope')
    if mode=='upload':return g.upload(folder)
    workflow='phase6e11-endchain-ci.yml'
    if mode=='dispatch':
        if (folder/'dispatch.json').exists():raise RuntimeError('no_retry')
        blob=json.loads((folder/'blob.json').read_text());inputs={'candidate_blob':blob['blob'],'candidate_sha256':blob['sha256']}
        g.write(folder/'dispatch.json',{'head':g.git('rev-parse','HEAD'),'inputs':inputs})
        g.api('/actions/workflows/'+workflow+'/dispatches','POST',{'ref':'main','inputs':inputs})
        print('DISPATCHED_ONCE');return
    if mode=='status':
        digest=json.loads((folder/'blob.json').read_text())['sha256']
        runs=g.api('/actions/workflows/'+workflow+'/runs?per_page=10&event=workflow_dispatch')['workflow_runs']
        print(json.dumps([{k:x[k] for k in ['id','status','conclusion','head_sha','html_url']} for x in runs if digest in x['display_title']]));return
    if mode=='collect':return g.collect(disk(folder),int(sys.argv[3]))
    if mode in ('artifact','artifact-recover'):
        from artifact import collect
        return collect(folder,int(sys.argv[3]),g.api,recover=mode=='artifact-recover')
    raise RuntimeError('mode')
if __name__=='__main__':main()
