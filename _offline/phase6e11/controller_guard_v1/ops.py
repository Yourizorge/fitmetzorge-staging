"""Exact staging CI sources and receipts. No Supabase calls or hosted secrets."""
import base64,hashlib,importlib.util,io,json,os,pathlib,re,sys,uuid,zipfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard_ci',HERE/'ci.py');ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
spec=importlib.util.spec_from_file_location('guard_github',HERE.parent/'ci41/ops.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROOT=g.ROOT
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p

def collect_artifact(folder,run):
    meta=g.api('/actions/runs/'+str(run));blob=json.loads((folder/'blob.json').read_text())
    if meta['status']!='completed' or meta['run_attempt']!=1 or blob['sha256'] not in meta['display_title']:raise RuntimeError('artifact_run_binding')
    head=json.loads((folder/'dispatch.json').read_text())['head']
    if meta['head_sha']!=head:raise RuntimeError('artifact_head_binding')
    rows=g.api('/actions/runs/'+str(run)+'/artifacts')['artifacts']
    rows=[a for a in rows if a['name']=='phase6e11-guard-'+str(run)+'-1']
    if len(rows)!=1 or rows[0]['expired'] or rows[0]['size_in_bytes']>30000000:raise RuntimeError('artifact_identity')
    artifact=rows[0];raw=g.api('/actions/artifacts/'+str(artifact['id'])+'/zip',raw=True)
    digest=hashlib.sha256(raw).hexdigest()
    if artifact.get('digest')!='sha256:'+digest:raise RuntimeError('artifact_archive_digest')
    target=disk(folder/('run-'+str(run)));target.mkdir(exist_ok=False)
    with (target/'evidence.zip').open('xb') as f:f.write(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        if len(names)>1000 or len(names)!=len(set(names)) or any(not re.fullmatch('[a-zA-Z0-9_.-]+\\.(json|txt)',n) for n in names):raise RuntimeError('artifact_paths')
        if sum(x.file_size for x in archive.infolist())>30000000 or any(x.file_size>2000000 for x in archive.infolist()):raise RuntimeError('artifact_size')
        manifest=json.loads(archive.read('artifact-manifest.json'))
        if set(names)!=set(manifest)|{'artifact-manifest.json'}:raise RuntimeError('artifact_files')
        for name,h in manifest.items():
            data=archive.read(name)
            if hashlib.sha256(data).hexdigest()!=h:raise RuntimeError('artifact_file_digest')
        result=json.loads(archive.read('result.json'))
        if result['candidate_sha256']!=blob['sha256'] or result['commit']!=head or str(result['run_id'])!=str(run):raise RuntimeError('artifact_result_binding')
        for name in names:
            with (target/name).open('xb') as f:f.write(archive.read(name))
    g.write(target/'collection.json',{'run':run,'head':head,'artifact_id':artifact['id'],'archive_sha256':digest,'files':len(manifest),'all_file_hashes_valid':True})
    print(json.dumps({'run':run,'files':len(manifest),'status':result['status'],'all_hashes_valid':True}))
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
    if action=='artifact':return collect_artifact(folder,int(sys.argv[3]))
    raise RuntimeError('mode')
if __name__=='__main__':main()
