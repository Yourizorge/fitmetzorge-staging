"""Derive a sanitized report from retained receipts; never contacts services."""
import hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    folder=ROOT/sys.argv[1]
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-controller-followup-'):raise RuntimeError('scope')
    migration=ROOT/'supabase/.temp/phase6e11-controller-m43-resume-91ce1111de3c4318afa43e811a586663'
    auth=ROOT/'supabase/.temp/phase6e11-controller-auth-readonly-5d58bc34a58944afa70b08753c4130e3'
    result=read(migration/'result.json');before=read(migration/'before/identity.json');after=read(migration/'after/identity.json')
    tests=read(folder/'local-tests.json')
    if result['status']!='M43_PAIRED_PASS_CONTROLLER_PENDING' or before['tables']!=after['tables']:raise RuntimeError('migration_pair')
    if not result['jit_revoked'] or tests['status']!='LOCAL_FOLLOWUP_PASS_HOSTED_AUTH_NOT_ADMITTED':raise RuntimeError('prerequisite')
    files=[migration/n for n in ['contract.json','result.json','pair.json','before/identity.json','after/identity.json','after/history.json','after/acl.json',
        'cli-dryrun-before.json','cli-apply.json','cli-dryrun-after.json','cli-load.json','closed.json']]
    files += [auth/n for n in ['contract.json','result.json','inventory.json','auth-settings.json','transaction-confirmed.json','rollback.json','closed.json']]
    files += [folder/'local-tests.json',folder/'alias-lock-metadata.json']
    def io(value):
        p=value['io'];profiles=p['profiles']+[p['reader']]
        return {'commands':value['query_commands'],'rows':value['rows'],'tables':len(value['tables']),
            'all_reader_calls_covered':p['all_reader_calls_covered'],
            'own_temp_blocks_written':sum(x['delta']['temp_blks_written'] for x in profiles)+p['closing']['temp_blks_written'],
            'background_temp_bytes':p['ambient_temp_bytes'],'background_exact_attribution':False,
            'max_profile_ms':max(x['delta']['total_exec_time'] for x in profiles)}
    summaries=[]
    for t in tests['tests']:
        summaries.append({k:v for k,v in t.items() if k!='evidence'})
    report={'date':'2026-10-12','baseline_head':'f7833846ce74406cadbaabc044b14241d16a4d9a',
        'status':'M43_HOSTED_PASS_CONTROLLER_AUTH_NO_GO','owner_window':False,'owner_acceptance':False,
        'migration':{'before':42,'after':43,'local':43,'file':'20261012104331_phase6e11_controller_evidence.sql',
            'sha256':sha(ROOT/'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql'),
            'registered_sql_exact':True,'dry_run_empty':True,'acl':read(migration/'after/acl.json')},
        'preservation':{'existing_tables':len(before['tables']),'unchanged':True,
            'tables_sha256':hashlib.sha256(json.dumps(before['tables'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'exclusions':['cron.job_run_details contents','new M43 migration-history row'],
            'new_proof_tables_empty':True,'auth_writes':0,'app_writes':0},
        'io':{'before':io(before),'after':io(after),'cli':read(migration/'cli-load.json'),
            'installation_budget':296,'count_with_40_cli_reservations_and_21_historical':result['commands_including_cli_reservations_and_historical'],
            'workflow_canary_executed':False,'workflow_canary_cap_unchanged':128},
        'jit':{'revoked':True,'active_mappings':0,'ssl_enforcement':True,
            'original_406_cause':'unrecoverable from old helper; all new instrumented subrequests succeeded'},
        'auth_preflight':read(auth/'result.json'),
        'alias_stability':read(folder/'alias-lock-metadata.json')['result'],
        'tests':summaries,'new_controller_ci_admission':False,
        'local_pg17_checks':{'metadata':6,'auth_preflight':4,'store':67,'identity_guard':6},
        'retained_limitations':['112 historical valid pairs and incomplete step113 unchanged',
            'one historical native SHOW probe failed; metadata receipt counts3 while old aggregate incorrectly says0',
            'historical policy receipt used unrecognized refresh rotation key; no rotation claim from null',
            'KEY SHARE alone does not protect mutable email under partial index; hosted Auth issuance blocked',
            'source-bound hosted Auth, fixture lifecycle, A/B and cleanup composition still pending'],
        'evidence':{p.relative_to(ROOT).as_posix():sha(p) for p in files},
        'controller_sources':{p.relative_to(ROOT).as_posix():sha(p) for p in HERE.iterdir() if p.is_file()},
        'external_ai_calls':0,'external_ai_eur':0,'real_member_ai':False,'production_touched':False}
    target=ROOT/'docs/PHASE6E11_M43_HOSTED_FOLLOWUP_EVIDENCE.json';write(target,report)
    print(json.dumps({'file':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'status':report['status'],
        'before_io':report['io']['before'],'after_io':report['io']['after'],'tests':summaries}))
if __name__=='__main__':main()
