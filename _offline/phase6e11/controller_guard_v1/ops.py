"""Exact staging CI sources and receipts. No Supabase calls or hosted secrets."""
import base64,hashlib,importlib.util,json,os,pathlib,re,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard_ci',HERE/'ci.py');ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
spec=importlib.util.spec_from_file_location('guard_github',HERE.parent/'ci41/ops.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROOT=g.ROOT
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def prepare():
    if g.git('branch','--show-current')!='main':raise RuntimeError('branch')
    folder=ROOT/'supabase/.temp'/('phase6e11-guard-ci-'+uuid.uuid4().hex);folder.mkdir()
    paths=set(ci.old.old.EXTRAS)|ci.old.EXTRA
    paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/migrations').glob('*.sql')}
    paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/tests').glob('*.sql')}
    files={}
    for name in sorted(paths):
        if not ci.old.old.allowed(name) and name not in ci.old.EXTRA:raise RuntimeError('candidate_path')
        raw=disk(ROOT/name).read_bytes()
        if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',raw):raise RuntimeError('secret_pattern')
        files[name]=base64.b64encode(raw).decode()
    digest=g.write(disk(folder/'candidate.json'),{'format':1,'files':files})
    g.write(disk(folder/'before.json'),{'head':g.git('rev-parse','HEAD'),'branch':'main','hosted_calls':0})
    print(json.dumps({'folder':str(folder),'sha256':digest,'files':len(files)}))
def main():
    action=sys.argv[1]
    if action=='prepare':return prepare()
    folder=pathlib.Path(sys.argv[2]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-guard-ci-'):raise RuntimeError('scope')
    if action=='upload':return g.upload(folder)
    if action=='dispatch':
        blob=json.loads((folder/'blob.json').read_text());inputs={'candidate_blob':blob['blob'],'candidate_sha256':blob['sha256']}
        g.write(folder/'dispatch.json',{'head':g.git('rev-parse','HEAD'),'inputs':inputs})
        g.api('/actions/workflows/phase6e11-guard-ci.yml/dispatches','POST',{'ref':'main','inputs':inputs});print('DISPATCHED_ONCE');return
    if action=='status':
        digest=json.loads((folder/'blob.json').read_text())['sha256']
        r=g.api('/actions/workflows/phase6e11-guard-ci.yml/runs?per_page=10&event=workflow_dispatch')['workflow_runs']
        print(json.dumps([{k:x[k] for k in ['id','status','conclusion','head_sha','html_url']} for x in r if digest in x['display_title']]));return
    if action=='collect':return g.collect(disk(folder),int(sys.argv[3]))
    raise RuntimeError('mode')
if __name__=='__main__':main()
