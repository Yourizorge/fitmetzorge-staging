"""Verify the exact endchain CI artifact; preserve already collected logs."""
import hashlib,io,json,os,pathlib,re,zipfile
MAX_FILES=1410
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def collect(folder,run,api,recover=False):
    meta=api('/actions/runs/'+str(run));blob=json.loads((folder/'blob.json').read_text())
    head=json.loads((folder/'dispatch.json').read_text())['head']
    if meta['status']!='completed' or meta['run_attempt']!=1 or meta['head_sha']!=head or blob['sha256'] not in meta['display_title']:
        raise RuntimeError('artifact_run_binding')
    matches=[x for x in api('/actions/runs/'+str(run)+'/artifacts')['artifacts']
             if x['name']=='phase6e11-endchain-'+str(run)+'-1']
    if len(matches)!=1 or matches[0]['expired'] or matches[0]['size_in_bytes']>30000000:raise RuntimeError('artifact_identity')
    artifact=matches[0];raw=api('/actions/artifacts/'+str(artifact['id'])+'/zip',raw=True)
    digest=hashlib.sha256(raw).hexdigest()
    if artifact.get('digest')!='sha256:'+digest:raise RuntimeError('artifact_archive_digest')
    original=disk(folder/('artifact-run-'+str(run)))
    if recover:
        if not original.is_dir() or sorted(p.name for p in original.iterdir())!=['evidence.zip']:
            raise RuntimeError('artifact_recovery_not_partial')
        if hashlib.sha256((original/'evidence.zip').read_bytes()).hexdigest()!=digest:
            raise RuntimeError('artifact_recovery_archive_changed')
    target=disk(folder/('artifact-run-'+str(run)+('-recovered' if recover else '')));target.mkdir(exist_ok=False)
    with (target/'evidence.zip').open('xb') as f:f.write(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        # Separate Auth before/after/pair receipts add bounded files; byte and
        # per-file limits remain unchanged. This does not expand SQL budgets.
        # The verified filter-check archive has1406 entries, including six new
        # per-stream bindings. SQL, byte, per-file and timeout caps are unchanged.
        if len(names)>MAX_FILES or len(names)!=len(set(names)) or any(not re.fullmatch('[a-zA-Z0-9_.-]+\\.(json|txt)',n) for n in names):
            raise RuntimeError('artifact_paths')
        # Immutable numeric before/after samples raise the measured 1,341-file
        # archive to 43.2 MB. Keep finite path, compressed and per-file limits.
        if sum(x.file_size for x in archive.infolist())>48000000 or any(x.file_size>2000000 for x in archive.infolist()):
            raise RuntimeError('artifact_size')
        manifest=json.loads(archive.read('artifact-manifest.json'))
        if set(names)!=set(manifest)|{'artifact-manifest.json'}:raise RuntimeError('artifact_files')
        for name,h in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=h:raise RuntimeError('artifact_file_digest')
        result=json.loads(archive.read('result.json'))
        if result['candidate_sha256']!=blob['sha256'] or result['commit']!=head or str(result['run_id'])!=str(run):
            raise RuntimeError('artifact_result_binding')
        for name in names:
            with (target/name).open('xb') as f:f.write(archive.read(name))
    record={'run':run,'head':head,'artifact_id':artifact['id'],'archive_sha256':digest,
            'files':len(manifest),'all_file_hashes_valid':True,'full_chain_admission':result.get('full_chain_admission')}
    with (target/'collection.json').open('x') as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
    print(json.dumps({'folder':str(target),'status':result['status'],**record}))
