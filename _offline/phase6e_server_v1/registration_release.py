"""Build a source-bound registration12 dossier, not a hosted admission token."""
import hashlib,json,os,pathlib,sys
import ci_profile
HERE=pathlib.Path(__file__).resolve().parent
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def build(folder):
    read=lambda n:json.loads(disk(folder/n).read_bytes())
    result=read('result.json');collection=read('collection.json');sources=read('candidate.json')['sources']
    if result['status']!='CLEAN_CI_PASS' or not collection['verified']:raise ValueError('ci_required')
    history=read('registration12-minimal-history.json')
    current=result.get('cli_profile')==ci_profile.PROFILE
    if result.get('cli_profile') not in (None,ci_profile.PROFILE):raise ValueError('registration_ci_profile')
    if current:
        if result.get('migrations_applied')!=47:raise ValueError('registration_complete_history')
        migration_history=ci_profile.history_contract(history['history'],sources,'minimal')
        ci_profile.history_contract(read('candidate-47-history.json')['history'],sources,'complete')
    else:
        if len(history['history'])!=45 or history['history'][-1]['version']!='20261014105919':raise ValueError('minimal_slice_history')
        migration_history={'profile':'historical_canonical44_app1','count':45,'current_profile':False}
    if read('registration12-dry-run.json')!={**read('registration12-dry-run.json'),'pending':False,'local_only':True}:raise ValueError('slice_dryrun')
    db=read('registration12-database.json');admin=read('registration12-integration-native-admin-protocol.json');auth=read('registration12-integration-managed-auth-protocol.json')
    cli=[read('cli-protocol-'+str(i)+'.json') for i in (0,1)]
    if current:
        for i,receipt in enumerate(cli):ci_profile.cli_receipt(receipt,i)
    coverage=[read('cli-numeric-coverage-'+str(i)+'.json') for i in (0,1)]
    isolation=[read('cli-isolation-'+str(i)+'.json') for i in (0,1)]
    if not all(x['restored'] and all(p['confirmed'] for p in x['protocol']) for x in isolation):raise ValueError('cli_isolation')
    if not all(x['complete'] for x in cli) or not all(x['all_protocol_visible'] and x['temp_written']==0 for x in coverage):raise ValueError('cli_evidence')
    if any(s['temp_written'] for s in auth['statements']):raise ValueError('auth_io')
    io=read('registration12-integration-application-io.json')
    if set(io['deltas'])!={'postgres','fmz6e_integration_server'} or any(v['temp_written'] for v in io['deltas'].values()):raise ValueError('application_io')
    if read('registration12-browser.json')['status']!='PASS':raise ValueError('browser_required')
    phases=[{'phase':'minimal_migration','commands':cli[0]['protocol_commands'],'evidence':'cli-protocol-0.json'},
            {'phase':'disposable_cli_isolation_and_restore','commands':sum(x['commands'] for x in isolation),'evidence':'cli-isolation-0/1.json'},
            {'phase':'empty_dryrun','commands':cli[1]['protocol_commands'],'evidence':'cli-protocol-1.json'},
            {'phase':'migration_numeric_observers','commands':sum(len(x['observer_commands']) for x in cli),'evidence':'cli-protocol-0/1.json'},
            {'phase':'fixture_setup_clock_denials_cleanup_and_auth_observers','commands':admin['commands'],'evidence':'registration12-integration-native-admin-protocol.json'},
            {'phase':'auth_requests_including_relogin_and_revocation','commands':auth['commands'],'evidence':'registration12-integration-managed-auth-protocol.json'},
            {'phase':'registration_read_write_rollback_and_terminal','commands':db['commands'],'evidence':'registration12-database.json'}]
    return {'status':'LOCAL_RELEASE_PREPARATION_ONLY','ci':collection['run'],'head':result['commit'],
        'candidate_sha256':result['candidate_sha256'],'source_hashes':sources,
        'migration_history':migration_history,'complete_history_count':47 if current else None,
        'scope':'frozen12 synthetic registration and historical facts only; no plan application, outbox or package21',
        'migration':'20261014105919_phase6e_synthetic_server_candidate.sql','migration_sha256':history['migration_sha256'],
        'phases':phases,'observed_sql_total':sum(x['commands'] for x in phases),
        'application_command_register':db['register'],
        'writeset':{'register_or_correct':['workspaces UPDATE exact workspace','revisions INSERT next version','requests INSERT exact UUID'],
            'audit':'one actor/request/xid; exact SHA256 row keys; three metadata audit entries; all-or-nothing',
            'cleanup':'exact owned requests, revisions, workspace; retained audit keys and DELETE counts',
            'other_members':'no allowed writes'},
        'budgets':{'hosted_authorized':False,'previous_4135_not_authorization':True,
            'timeout_seconds':5,'lock_timeout_seconds':1,'retries':0,
            'note':'CI protocol counts are exact observations, not a hosted maximum. Host Auth/guard/measurement escrow must be bound to the admitted 6E-11 outcome and exact release identities before release.'},
        'transport':{'implemented':'loopback HTTP with HttpOnly session/CSRF and verified local GoTrue; PostgreSQL verify-full, official hosted transport remains gated',
            'server_clock':'clock_timestamp at read/locked row and final CAS; expired access stops writes',
            'binding':'private operator workspace-to-actor UUID map; no client role',
            'default_off':'FMZ_LOCAL_REGISTRATION12_ENABLED is absent; incompatible with combined entry flag'},
        'rollback':'disable entry and exact synthetic subjects; retain revisions/audit; retry only same receipt after outcome recovery; no history deletion or migration rewind',
        'release_gates':['complete hosted 6E-11 evidence','required physical ownerreview','explicit selected registration12 release decision',
            'source-bound hosted transport, lifecycle write-set and full hosted budget; no default-on activation'],
        'hosted_applied':False,'owner_accepted':False,'real_member_ai':False}

if __name__=='__main__':
    folder=pathlib.Path(sys.argv[1]).resolve()
    if not folder.is_relative_to(HERE.parents[1]/'supabase/.temp') or not folder.name.startswith('verified-'):raise ValueError('scope')
    result=build(folder);target=disk(folder/'registration12-release-dossier.json')
    with target.open('x') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({'status':result['status'],'observed_sql_total':result['observed_sql_total'],'hosted_authorized':False}))
