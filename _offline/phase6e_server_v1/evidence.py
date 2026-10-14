"""Archive selected verified synthetic CI outcomes without credentials or logs."""
import hashlib,json,os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FILES=('result.json','collection.json','candidate-45-history.json',
       'integration-auth.json','integration-auth-table-security.json',
       'integration-database.json','integration-browser.json',
       'integration-security.json','integration-role-memberships.json')
PROTOCOL=('integration-native-admin-protocol.json','integration-managed-auth-protocol.json',
          'integration-database.json','cli-protocol-0.json','cli-protocol-1.json',
          'cli-numeric-coverage-0.json','cli-numeric-coverage-1.json')
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    source=pathlib.Path(sys.argv[1]).resolve()
    if not source.is_relative_to(ROOT/'supabase/.temp') or not source.name.startswith('verified-'):
        raise RuntimeError('evidence_scope')
    read=lambda name:json.loads(disk(source/name).read_bytes())
    result=read('result.json');collection=read('collection.json')
    if result['status']!='CLEAN_CI_PASS' or not collection['verified'] or str(collection['run'])!=result['run_id']:
        raise RuntimeError('evidence_not_admitted')
    manifest=read('artifact-manifest.json');candidate=read('candidate.json')
    addendum=len(sys.argv)==3 and sys.argv[2]=='--protocol-addendum'
    if len(sys.argv)>2 and not addendum:raise RuntimeError('evidence_mode')
    target=disk(HERE/'receipts'/('ci-'+result['run_id']+('-protocol' if addendum else '')));target.mkdir(parents=True,exist_ok=False)
    names=list(PROTOCOL if addendum else FILES)
    if not addendum:names += [n for n in manifest if n.startswith('integration-') and n.endswith('.png')]
    hashes={}
    for name in names:
        raw=disk(source/name).read_bytes()
        if name!='collection.json' and manifest.get(name)!=sha(raw):raise RuntimeError('evidence_digest')
        with (target/name).open('xb') as out:out.write(raw)
        hashes[name]=sha(raw)
    if addendum:
        from release_packet import build
        dossier=build(source)
        if read('release-dossier.json')!=dossier:raise RuntimeError('dossier_source_binding')
        raw=(json.dumps(dossier,sort_keys=True,indent=2)+'\n').encode()
        with (target/'release-dossier.json').open('xb') as out:out.write(raw)
        hashes['release-dossier.json']=sha(raw)
    raw=(json.dumps(candidate['sources'],sort_keys=True,indent=2)+'\n').encode()
    with (target/'source-hashes.json').open('xb') as out:out.write(raw)
    hashes['source-hashes.json']=sha(raw)
    value={'scope':'LOCAL_CI_ONLY','hosted_admitted':False,'head':result['commit'],
           'candidate_sha256':result['candidate_sha256'],'archive_sha256':collection['archive_sha256'],
           'files':hashes,'history_preserved':True,'owner_acceptance':False}
    with (target/'MANIFEST.json').open('xb') as out:out.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({'directory':str(target),'files':len(hashes),'scope':'LOCAL_CI_ONLY'}))
if __name__=='__main__':main()
