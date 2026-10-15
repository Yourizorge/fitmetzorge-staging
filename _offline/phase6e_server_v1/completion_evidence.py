"""Preserve sanitized verified receipts without rewriting any earlier receipt."""
import hashlib,json,os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if not folder.is_relative_to(ROOT/'supabase/.temp') or not folder.name.startswith('verified-'):raise ValueError('scope')
    read=lambda n:json.loads(disk(folder/n).read_bytes())
    result,collection,manifest=read('result.json'),read('collection.json'),read('artifact-manifest.json')
    if result['status']!='CLEAN_CI_PASS' or not collection['verified'] or str(collection['run'])!=result['run_id'] or collection['head']!=result['commit']:raise ValueError('ci_required')
    if read('candidate.json')['sha256']!=result['candidate_sha256']:raise ValueError('candidate_binding')
    names=['result.json','collection.json','candidate-46-history.json','registration12-minimal-history.json',
        'registration12-dry-run.json','registration12-database.json','registration12-browser.json',
        'registration12-auth.json','registration12-integration-native-admin-protocol.json','registration12-integration-managed-auth-protocol.json',
        'registration12-integration-application-io.json','integration-application-io.json',
        'integration-auth.json','integration-auth-table-security.json','integration-database.json','integration-browser.json','integration-security.json','integration-role-memberships.json',
        'integration-native-admin-protocol.json','integration-managed-auth-protocol.json']
    if 'stream-filter-pg17.json' in manifest:names.append('stream-filter-pg17.json')
    if 'stream-capacity-pg17.json' in manifest:names.append('stream-capacity-pg17.json')
    for name in ('composed-browser.json','account-center-browser.json','offline-shell-browser.json','release-selection-http.json','workday-release-packets.json','numeric-size-pg17.json','proposed-size-pg17.json'):
        if name in manifest:names.append(name)
    names += [n for n in manifest if n.startswith('registration12-transport-') and n.endswith('.json')]
    names += [n for n in manifest if n.startswith(('cli-protocol-','cli-numeric-coverage-','cli-isolation-')) or n.endswith('.png')]
    names += [n for n in manifest if n.startswith(('integration-io-','registration12-integration-io-')) and n.endswith('.json')]
    sys.path.insert(0,str(ROOT/'_offline/phase6e11/endchain_v1'));from source_scan import check
    from registration_release import build
    from receipt_accounting import meter_controls
    dossier=build(folder);controls=meter_controls(manifest,read)
    dossier['phases'].append(controls);dossier['observed_sql_total']+=controls['commands']
    dossier['post_verification_accounting']={'generator_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'accounting_sha256':hashlib.sha256((HERE/'receipt_accounting.py').read_bytes()).hexdigest(),
        'scope':'independently tested receipt arithmetic; does not change or admit CI runtime sources'}
    all_controls=meter_controls(manifest,read,4)
    names += [x['file'] for x in all_controls['evidence']]
    extras={'registration12-release-dossier.json':dossier,'source-hashes.json':read('candidate.json')['sources']}
    if 'registration12-transport-database-a.json' in manifest:
        from registration_accounting import build as transport_register
        extras['registration12-transport-register.json']=transport_register(read,manifest)
    target=disk(HERE/'receipts'/('ci-'+result['run_id']+'-completion'));target.mkdir(parents=True,exist_ok=False);saved={}
    for name in sorted(set(names)):
        raw=disk(folder/name).read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if name!='collection.json' and manifest[name]!=sha:raise ValueError('artifact_hash')
        if not name.endswith('.png'):check(name,raw)
        with (target/name).open('xb') as f:f.write(raw)
        saved[name]=sha
    for name,value in extras.items():
        raw=json.dumps(value,indent=2,sort_keys=True).encode();check(name,raw)
        with (target/name).open('xb') as f:f.write(raw)
        saved[name]=hashlib.sha256(raw).hexdigest()
    with (target/'MANIFEST.json').open('x') as f:json.dump({'files':saved,'head':result['commit'],
        'candidate_sha256':result['candidate_sha256'],'archive_sha256':collection['archive_sha256'],'hosted':False,'owner_acceptance':False},f,indent=2,sort_keys=True)
    print(json.dumps({'files':len(saved),'directory':str(target),'scope':'local_CI_only'}))
if __name__=='__main__':main()
