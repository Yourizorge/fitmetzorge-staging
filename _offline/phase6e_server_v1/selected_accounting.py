"""Verify and summarize actual eight-slice CI protocol costs, without SQL."""
import collections, hashlib, json, pathlib, sys
from registration_release import disk
from release_selection import SLICES
from receipt_accounting import meter_controls
import ci_profile


def register(rows, count):
    if len(rows)!=count or any(r.get('phase')!='completed' or r.get('confirmed') is not True for r in rows):
        raise ValueError('selected_protocol_incomplete')
    keys=[(r['call_id'],r['ordinal']) for r in rows]
    if len(set(keys))!=len(keys):raise ValueError('selected_protocol_duplicate')
    return dict(collections.Counter(r['operation'] for r in rows))


def build(folder):
    manifest=json.loads(disk(folder/'artifact-manifest.json').read_bytes())
    used={}
    def read(name):
        raw=disk(folder/name).read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if name!='collection.json' and manifest.get(name)!=sha:raise ValueError('selected_artifact_hash')
        used[name]=sha;return json.loads(raw)
    result,collection=read('result.json'),read('collection.json')
    if result['status']!='CLEAN_CI_PASS' or collection.get('verified') is not True or str(collection['run'])!=result['run_id'] or collection['head']!=result['commit']:
        raise ValueError('selected_current_ci_required')
    matrix=read('selected-release-matrix.json');slices=[]
    if matrix['status']!='EIGHT_SELECTED_LOCAL_PASS' or [s['slice'] for s in matrix['slices']]!=[s['id'] for s in SLICES]:
        raise ValueError('selected_eight_required')
    for spec in SLICES:
        r=read('selected-release-matrix-'+spec['id']+'.json')
        if r['status']!='PASS_LOCAL_HTTP_AUTH_PG' or r['full_day21'] is not False or r['hosted_admission'] is not False:
            raise ValueError('selected_boundary')
        runtime=register(r['runtime_register'],r['native_runtime_commands'])
        admin=register(r['admin_register'],r['native_admin_commands'])
        auth=r['managed_auth']
        if auth['temp_written'] or auth['commands']!=sum(q['calls'] for q in auth['statements']):raise ValueError('selected_auth_load')
        expected={k:v for k,v in r['delete_counts'].items() if v}
        observed=dict(collections.Counter(e['table_name'] for e in r['delete_evidence']))
        if expected!=observed or any(e['operation']!='DELETE' for e in r['delete_evidence']) or len({e['xid'] for e in r['delete_evidence']})!=1:
            raise ValueError('selected_cleanup_evidence')
        slices.append(dict(id=spec['id'],checks=r['checks'],runtime=r['native_runtime_commands'],
            admin=r['native_admin_commands'],managed_auth=auth['commands'],runtime_by_operation=runtime,
            admin_by_operation=admin,retained_delete_records=len(r['delete_evidence']),
            measured_commands=r['native_runtime_commands']+r['native_admin_commands']+auth['commands']))
    admin=read('selected-integration-native-admin-protocol.json')
    auth=read('selected-integration-managed-auth-protocol.json')
    if admin['failed_commands'] or auth['temp_written']:raise ValueError('selected_failed_or_temp')
    # The surrounding environment owns subject/Auth setup and final revocation.
    shared_admin=admin['commands']-sum(s['admin'] for s in slices)
    shared_auth=auth['commands']-sum(s['managed_auth'] for s in slices)
    if min(shared_admin,shared_auth)<0:raise ValueError('selected_shared_overlap')
    installation=[]
    for i in range(4):
        cli=read('cli-protocol-'+str(i)+'.json');isolation=read('cli-isolation-'+str(i)+'.json')
        coverage=read('cli-numeric-coverage-'+str(i)+'.json')
        if result.get('cli_profile')==ci_profile.PROFILE:ci_profile.cli_receipt(cli,i)
        if not cli['complete'] or not isolation['restored'] or not coverage['all_protocol_visible'] or coverage['temp_written']:
            raise ValueError('selected_installation')
        installation.append(dict(invocation=i,cli=cli['protocol_commands'],
            observer=len(cli['observer_commands']),isolation=isolation['commands']))
    controls=meter_controls(manifest,read,4)
    installation_total=sum(x['cli']+x['observer']+x['isolation'] for x in installation)+controls['commands']
    return dict(status='MEASURED_LOCAL_SELECTIONS_ONLY',ci=result['run_id'],head=result['commit'],
        candidate_sha256=result['candidate_sha256'],archive_sha256=collection['archive_sha256'],slices=slices,
        shared=dict(admin=shared_admin,managed_auth=shared_auth,installation=installation_total,
                    installation_detail=installation,cli_meter_controls=controls['commands']),
        measured_commands=sum(s['measured_commands'] for s in slices)+shared_admin+shared_auth+installation_total,
        measured_scope='Eight selected A/B HTTP tests, their fixtures/cleanup/Auth and shared two-app-migration installation. Excludes canonical'+('45' if result.get('cli_profile')==ci_profile.PROFILE else '44')+' bootstrap, browser suites, hosted allowance or physical review.',
        source_evidence=used,hosted_admission=False)


if __name__=='__main__':
    folder=pathlib.Path(sys.argv[1]).resolve();result=build(folder)
    target=disk(folder/'selected-measured-costs.json')
    with target.open('xb') as output:output.write((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_evidence','slices')}))
