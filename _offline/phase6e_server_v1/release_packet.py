"""Offline release dossier. It cannot grant access, migrate or make requests."""
import hashlib,json,os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
MIGRATION='20261014105919_phase6e_synthetic_server_candidate.sql'

def build(receipt):
    def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
    read=lambda n:json.loads(disk(receipt/n).read_bytes())
    result=read('result.json');collection=read('collection.json');sources=read('candidate.json')['sources']
    if result['status']!='CLEAN_CI_PASS' or not collection.get('verified') or result['migrations_applied']!=45:
        raise ValueError('release_ci_missing')
    database=read('integration-database.json')
    admin=read('integration-native-admin-protocol.json')
    auth=read('integration-managed-auth-protocol.json')
    cli=[read('cli-protocol-'+str(i)+'.json') for i in range(2)]
    coverage=[read('cli-numeric-coverage-'+str(i)+'.json') for i in range(2)]
    if not all(x['complete'] for x in cli) or not all(x['all_protocol_visible'] for x in coverage):
        raise ValueError('release_cli_count_incomplete')
    if any(len(x.get('observer_commands',[]))!=8 or
           not all(c.get('confirmed') is True and c.get('protocol_commands')==1 for c in x['observer_commands'])
           for x in cli):
        raise ValueError('release_cli_observers_incomplete')
    if any(x['temp_written'] for x in coverage) or any(x['temp_written'] for x in auth['statements']):
        raise ValueError('release_temp_io')
    actual={'application_protocol':database['protocol']['commands'],'fixture_admin_protocol':admin['commands'],
        'managed_auth':auth['commands'],'migration_cli':cli[0]['protocol_commands'],'dry_run_cli':cli[1]['protocol_commands'],
        'cli_observers':sum(len(x['observer_commands']) for x in cli)}
    # These are proposed upper bounds for the next release, NOT permission to
    # spend the unrelated 6E-11 allowance or a claim of hosted measurement.
    phases=[
        {'phase':'protected_baseline_precleanup_postcleanup','cap':93,'basis':'3 bounded streams, at most 31 commands each; adaptation to new private schema must pass hosted admission'},
        {'phase':'identity_acl_sources_and_expiry','cap':12,'basis':'proposed fixed metadata slots; no Auth or data writes'},
        {'phase':'candidate_migration_and_final_dryrun','cap':65,'basis':'47+2 measured CLI protocol commands plus 8+8 explicit read-only observer commands'},
        {'phase':'fixture_setup_negative_tests_and_cleanup','cap':90,'basis':'81 measured commands, including 3 expected denied ACL commands; 9 explicit reserve slots'},
        {'phase':'application_transactions','cap':2055,'basis':'160 reads*8 + 64 mutations*12 + 1 RLS negative transaction*7; BEGIN/COMMIT/ROLLBACK included'},
        {'phase':'managed_auth','cap':1700,'basis':'1433 measured in this CI; conservative escrow, exact protocol coverage and caller allowlist required before a hosted release'},
    ]
    if actual['application_protocol']>2055 or actual['fixture_admin_protocol']>90 or actual['managed_auth']>1700:
        raise ValueError('release_observed_budget_exceeded')
    safety=[
        {'action':'rollback_and_close_four_owned_connections','cap':4},
        {'action':'disable_only_new_synthetic_entry_and_confirm','cap':4},
        {'action':'five_exact_local_scope_logouts','cap':50},
        {'action':'complete_scoped_delete_evidence_or_preserve_unconfirmed_fixtures','cap':21},
        {'action':'bounded_protected_terminal_stream','cap':31},
        {'action':'final_empty_dryrun_with_observers','cap':10},
    ]
    normal=sum(x['cap'] for x in phases);reserve=sum(x['cap'] for x in safety)
    return {'status':'OFFLINE_RELEASE_DOSSIER_NOT_HOSTED_ADMISSION','ci_run':collection['run'],
        'commit':result['commit'],'archive_sha256':collection['archive_sha256'],
        'candidate_sha256':result['candidate_sha256'],'source_hashes':sources,
        'migration':{'path':'_offline/phase6e_server_v1/supabase/migrations/'+MIGRATION,
            'sha256':hashlib.sha256((HERE/'supabase/migrations'/MIGRATION).read_bytes()).hexdigest(),
            'canonical_hosted_directory':False,'hosted_applied':False},
        'observed_local_commands':actual,'observed_local_total':sum(actual.values()),
        'phase_caps':phases,'normal_capacity':normal,'safety_suffix':safety,'safety_reserve':reserve,
        'proposed_maximum':normal+reserve,'owner_budget_approval':False,'automatic_retries':0,
        'flags':{'entry_enabled':False,'synthetic_only':True,'registration12':False,'full_day21':False,'real_member_ai':False},
        'release_gates':['complete 6E-11 hosted proof and physical owner review',
            'separate synthetic hosted slice approval; no bulk activation12-21',
            'source-bound hosted transport, exact identities and least-privilege session validation',
            'source-bound 12 metadata slots and all safety actions; no imaginary commands',
            'scoped Auth/delete evidence and preserved data in hosted measurements',
            'physical21 acceptance remains absent; expert/privacy/provider conditions remain open'],
        'local_boundary':'Store rejects non-loopback endpoints; no hosted driver, issuer or privilege is enabled by this dossier',
        'rollback':'disable entry/subjects first, preserve history; restoring a plan creates a new approved version; never drop history or rewind migrations'}

def main():
    receipt=pathlib.Path(sys.argv[1]).resolve()
    if not receipt.is_relative_to(HERE.parents[1]/'supabase/.temp') or not receipt.name.startswith('verified-'):
        raise ValueError('receipt_scope')
    value=build(receipt)
    target=receipt/'release-dossier.json'
    if os.name=='nt':target=pathlib.Path('\\\\?\\'+str(target))
    with target.open('x',encoding='utf8') as out:json.dump(value,out,indent=2,sort_keys=True)
    print(json.dumps({k:value[k] for k in ('status','observed_local_total','normal_capacity','safety_reserve','proposed_maximum')}))
if __name__=='__main__':main()
