"""Recover a complete CI receipt without replacing an earlier collection.

No network, database or runtime access. The normal collector verified the
GitHub archive digest before its older 1,000-file bound rejected this bundle.
This export repeats manifest/source checks under a finite 1,400-file bound.
"""
import hashlib,json,os,pathlib,re,sys,uuid,zipfile

def digest(raw):return hashlib.sha256(raw).hexdigest()

def export(folder,run,expected_archive_sha):
    folder=pathlib.Path(folder).resolve()
    if os.name=='nt' and not str(folder).startswith('\\\\?\\'):folder=pathlib.Path('\\\\?\\'+str(folder))
    if not folder.name.startswith('phase6e11-endchain-ci-'):raise ValueError('scope')
    original=folder/('artifact-run-'+str(run))/'evidence.zip'
    raw=original.read_bytes()
    if len(raw)>30000000:raise ValueError('archive_size')
    if not re.fullmatch('[0-9a-f]{64}',expected_archive_sha) or digest(raw)!=expected_archive_sha:
        raise ValueError('archive_digest')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        if len(names)>1400 or len(names)!=len(set(names)) or any(not re.fullmatch(r'[A-Za-z0-9_.-]+\.(json|txt)',n) for n in names):
            raise ValueError('archive_paths')
        if sum(x.file_size for x in archive.infolist())>30000000 or any(x.file_size>2000000 for x in archive.infolist()):
            raise ValueError('archive_expansion')
        manifest=json.loads(archive.read('artifact-manifest.json'))
        if set(names)!=set(manifest)|{'artifact-manifest.json'}:raise ValueError('manifest_set')
        for name,expected in manifest.items():
            if digest(archive.read(name))!=expected:raise ValueError('manifest_hash')
        result=json.loads(archive.read('result.json'))
        blob=json.loads((folder/'blob.json').read_text())
        dispatch=json.loads((folder/'dispatch.json').read_text())
        if str(result['run_id'])!=str(run) or result['candidate_sha256']!=blob['sha256'] or result['commit']!=dispatch['head']:
            raise ValueError('source_binding')
        if digest((folder/'candidate.json').read_bytes())!=blob['sha256']:raise ValueError('candidate_hash')
        target=folder/('verified-run-'+str(run)+'-'+uuid.uuid4().hex)
        target.mkdir(exist_ok=False)
        for name in names:
            with (target/name).open('xb') as f:f.write(archive.read(name));f.flush();os.fsync(f.fileno())
        receipt={'run':run,'head':dispatch['head'],'candidate_sha256':blob['sha256'],
            'archive_sha256':digest(raw),'files':len(manifest),'all_file_hashes_valid':True,
            'original_archive_preserved':True,'status':result['status'],'hosted_calls':0,
            'full_chain_admission':result.get('full_chain_admission'),
            'expected_archive_digest_matches':True}
        with (target/'collection.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
    return {'folder':str(target),**receipt}

if __name__=='__main__':print(json.dumps(export(sys.argv[1],int(sys.argv[2]),sys.argv[3])))
