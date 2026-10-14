"""Source-only GitHub CI bundle; no Supabase operation or credential."""
import base64,hashlib,importlib.util,io,json,os,pathlib,re,sys,uuid,zipfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('server_ci',HERE/'ci.py');ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
spec=importlib.util.spec_from_file_location('server_github',HERE.parent/'phase6e11/ci41/ops.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROOT=g.ROOT
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def main():
    mode=sys.argv[1]
    if mode=='prepare':
        if g.git('branch','--show-current')!='main':raise RuntimeError('branch')
        folder=ROOT/'supabase/.temp'/('phase6e-server-ci-'+uuid.uuid4().hex);folder.mkdir()
        paths=set(ci.previous.prior.old.old.EXTRAS)|ci.previous.prior.old.EXTRA
        paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/migrations').glob('*.sql')}
        paths|={p.relative_to(ROOT).as_posix() for p in (ROOT/'supabase/tests').glob('*.sql')}
        files={}
        for name in sorted(paths):
            raw=disk(ROOT/name).read_bytes()
            if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',raw):raise RuntimeError('secret_pattern')
            files[name]=base64.b64encode(raw).decode()
        digest=g.write(disk(folder/'candidate.json'),{'format':1,'files':files})
        g.write(disk(folder/'before.json'),{'head':g.git('rev-parse','HEAD'),'branch':'main','hosted_calls':0})
        print(json.dumps({'folder':str(folder),'sha256':digest,'files':len(files)}));return
    folder=pathlib.Path(sys.argv[2]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):raise RuntimeError('scope')
    if mode=='upload':return g.upload(folder)
    workflow='phase6e-server-local-ci.yml'
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
    if mode=='artifact':
        run=int(sys.argv[3]);meta=g.api('/actions/runs/'+str(run));blob=json.loads((folder/'blob.json').read_text());head=json.loads((folder/'dispatch.json').read_text())['head']
        if meta['status']!='completed' or meta['run_attempt']!=1 or meta['head_sha']!=head or blob['sha256'] not in meta['display_title']:raise RuntimeError('run_binding')
        artifacts=g.api('/actions/runs/'+str(run)+'/artifacts')['artifacts'];matches=[a for a in artifacts if a['name']=='phase6e-server-'+str(run)+'-1']
        if len(matches)!=1 or matches[0]['expired'] or matches[0]['size_in_bytes']>30000000:raise RuntimeError('artifact_binding')
        raw=g.api('/actions/artifacts/'+str(matches[0]['id'])+'/zip',raw=True);sha=hashlib.sha256(raw).hexdigest()
        if matches[0]['digest']!='sha256:'+sha:raise RuntimeError('archive_digest')
        target=disk(folder/('verified-'+str(run)));target.mkdir(exist_ok=False)
        with (target/'evidence.zip').open('xb') as f:f.write(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names=archive.namelist()
            if len(names)>1100 or len(set(names))!=len(names) or any(not re.fullmatch(r'[A-Za-z0-9_.-]+\.(json|txt|png)',n) for n in names):raise RuntimeError('archive_paths')
            if sum(i.file_size for i in archive.infolist())>30000000 or any(i.file_size>2000000 for i in archive.infolist()):raise RuntimeError('archive_size')
            manifest=json.loads(archive.read('artifact-manifest.json'))
            if set(names)!=set(manifest)|{'artifact-manifest.json'}:raise RuntimeError('manifest_paths')
            for name,expected in manifest.items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=expected:raise RuntimeError('file_digest')
            result=json.loads(archive.read('result.json'))
            if result['commit']!=head or result['candidate_sha256']!=blob['sha256']:raise RuntimeError('result_binding')
            for name in names:
                with (target/name).open('xb') as f:f.write(archive.read(name))
        g.write(target/'collection.json',{'run':run,'head':head,'archive_sha256':sha,'files':len(manifest),'verified':True})
        print(json.dumps({'path':str(target),'status':result['status'],'sha256':sha,'files':len(manifest)}));return
    raise RuntimeError('mode')
if __name__=='__main__':main()
