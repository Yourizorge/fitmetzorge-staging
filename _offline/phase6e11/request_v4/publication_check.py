"""Read-only post-push closure for new private paths and exact staging Git state."""
import hashlib,json,os,pathlib,subprocess,urllib.request,urllib.error,uuid
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def main():
    def git(*args):return subprocess.check_output([os.environ['FMZ_GIT'],*args],cwd=ROOT).decode().strip()
    head=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/main').split()[0]
    if head!=remote or git('branch','--show-current')!='main':raise RuntimeError('git_scope')
    paths=[p.relative_to(ROOT).as_posix() for p in HERE.iterdir() if p.is_file()]
    paths+=['supabase/migrations/20260928120846_phase6e11_request_binding.sql','.github/workflows/phase6e11-proof.yml']
    results=[]
    for path in sorted(paths):
        req=urllib.request.Request('https://yourizorge.github.io/fitmetzorge-staging/'+path,method='HEAD')
        try:
            with urllib.request.urlopen(req,timeout=15) as r:status=r.status
        except urllib.error.HTTPError as e:status=e.code
        if status!=404:raise RuntimeError('private_path_status_'+str(status)+':'+path)
        results.append({'path':path,'status':status})
    files=git('status','--porcelain').splitlines()
    result={'head':head,'remote_head':remote,'private_paths':results,'worktree_clean':not files,
      'retained_dirty_entries':len(files),'supabase_calls':0,'new_own_window':False}
    folder=ROOT/'supabase/.temp'/('phase6e11-request-publication-final-'+uuid.uuid4().hex);folder.mkdir()
    raw=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    with (folder/'result.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    print(json.dumps({'folder':str(folder),'sha256':hashlib.sha256(raw).hexdigest(),
      'head':head,'remote':remote,'private_paths_404':len(results),'worktree_clean':not files}))
if __name__=='__main__':main()
