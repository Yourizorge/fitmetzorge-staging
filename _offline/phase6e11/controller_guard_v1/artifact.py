"""Pure injected artifact validation; no credential or CI-runner imports."""
import hashlib,io,json,os,pathlib,re,zipfile

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p

def collect_artifact(folder,run,api):
    meta=api('/actions/runs/'+str(run));blob=json.loads((folder/'blob.json').read_text())
    if meta['status']!='completed' or meta['run_attempt']!=1 or blob['sha256'] not in meta['display_title']:raise RuntimeError('artifact_run_binding')
    head=json.loads((folder/'dispatch.json').read_text())['head']
    if meta['head_sha']!=head:raise RuntimeError('artifact_head_binding')
    rows=api('/actions/runs/'+str(run)+'/artifacts')['artifacts']
    rows=[a for a in rows if a['name']=='phase6e11-guard-'+str(run)+'-1']
    if len(rows)!=1 or rows[0]['expired'] or rows[0]['size_in_bytes']>30000000:raise RuntimeError('artifact_identity')
    artifact=rows[0];raw=api('/actions/artifacts/'+str(artifact['id'])+'/zip',raw=True)
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
    with (target/'collection.json').open('x') as f:
        json.dump({'run':run,'head':head,'artifact_id':artifact['id'],'archive_sha256':digest,'files':len(manifest),'all_file_hashes_valid':True},f)
        f.flush();os.fsync(f.fileno())
    print(json.dumps({'run':run,'files':len(manifest),'status':result['status'],'all_hashes_valid':True}))
