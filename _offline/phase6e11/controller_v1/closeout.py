"""Assemble immutable local receipts; no network or database operation."""
import hashlib,json,os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE=ROOT/'supabase/.temp/phase6e11-controller-590796353d7344778ee8efb69454065c'
FINAL=ROOT/'supabase/.temp/phase6e11-controller-final-local'
FIRST=ROOT/'supabase/.temp/phase6e11-controller-install-e6994eca04324c5591ad87750c45d2b0'
SECOND=ROOT/'supabase/.temp/phase6e11-controller-install-1adf3ae609774e22a514872b1c718a40'
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def read(p):return json.loads(disk(p).read_text())
def sha(p):return hashlib.sha256(disk(p).read_bytes()).hexdigest()
def main():
    tests=sorted(FINAL.glob('offline-tests-*.json'),key=lambda p:p.stat().st_mtime)[-1]
    local=read(tests);ci=read(FINAL/'run-38243722556/result.json')
    assert local['status']=='LOCAL_PASS' and local['sources_unchanged'] and ci['status']=='CLEAN_CI_PASS'
    assert local['results']['node']['passed']==143 and local['results']['pg17']['checks']==62
    original=read(FIRST/'result.json');corrected=read(SECOND/'result.json');measurement=read(FIRST/'before/identity.json')
    assert original['reason']=='before_plan_shape_budget' and corrected['reason']=='management_http_406'
    assert not original['migration_applied'] and not corrected['migration_applied']
    assert measurement['rollback']['confirmed'] and measurement['query_commands']==18
    closed=read(SECOND/'lease-revoked.json');assert closed['jit_state']=='disabled' and closed['remaining_mappings']==0
    assert closed['ssl']['currentConfig']['database'] is True
    baseline=read(BASE/'before.json');changed=[n for n,h in baseline['retained'].items() if sha(ROOT/n)!=h];assert not changed
    preserved={n:sha(ROOT/n) for n in baseline['retained']}
    pg=pathlib.Path(local['results']['pg17']['evidence']);assert read(pg)['sources_unchanged']
    workflow=ROOT/'supabase/.temp/phase6e11-workflow-local-e4ba46eb524f4545aa37c0a48da9d2bf/request-v4-result.json'
    security=ROOT/'supabase/.temp/phase6e11-request-security-f1560f6903f34911aeb68be8e516a204/request-security.json'
    assert read(workflow)['pairs']==45 and read(security)['count']==33
    evidence=[tests,FINAL/'run-38243722556/result.json',FINAL/'run-38243722556/candidate.json',
      FIRST/'result.json',FIRST/'before/identity.json',FIRST/'before/manifest.json',FIRST/'lease-revoked.json',
      SECOND/'result.json',SECOND/'lease-revoked.json',workflow,security]
    sources=[p for p in HERE.iterdir() if p.is_file()]+[ROOT/'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql',ROOT/'.github/workflows/phase6e11-controller-ci.yml']
    value={'status':'NO_GO_HOSTED_WORKFLOW_NOT_PROVEN','baseline':baseline['head'],
      'local_tests':{'controller_node':143,'python':22,'pg17_store':62,'existing_security':33,'existing_workflow_pairs':45,
        'auth':'synthetic local stubs, NOT hosted Auth proof','ci_node_overlap':63,'ci_sql_regression_files':12},
      'ci':{'run':38243722556,'status':'CLEAN_CI_PASS','migrations':43,'dry_run':'EMPTY_LOCAL_CI_ONLY','postgres':'17.6','cli':'2.117.0'},
      'migration':{'local':43,'hosted_last_observed':42,'pending':'20261012104331_phase6e11_controller_evidence.sql',
        'sha256':sha(sources[-2]),'applied_hosted':False,'fresh_hosted_dry_run':False},
      'attempts':[{'run':FIRST.name,'phase':'before','reason':original['reason'],'sql_commands':18,'row_stream_started':False,'read_only_rollback':True,'jit_revoked':True},
        {'run':SECOND.name,'phase':'JIT lease admission','reason':corrected['reason'],'sql_commands':0,'database_connection_opened':False,'jit_revoked':True}],
      'remaining_failure_detail':'Which JIT enable/grant/confirmation subrequest returned 406 was not retained by the old helper; no cause invented.',
      'closure':closed,'preservation':{'existing_sources':len(preserved),'changed':changed,'full_data_pair_completed':False,
        'application_writes':0,'auth_calls':0,'new_fixtures':0,'fixture_cleanup':False,'historical_112_and_incomplete_113_unchanged':True},
      'deployment':{'controller':False,'application_edge':False,'owner_window':False,'owner_acceptance':False,'phase21_accepted':False},
      'sources':{p.relative_to(ROOT).as_posix():sha(p) for p in sources},
      'evidence':{p.relative_to(ROOT).as_posix():sha(p) for p in evidence},
      'local_pg17_receipt':{'path':str(pg),'sha256':sha(pg)},
      'external_ai_calls':0,'external_cost_eur':0,'real_member_ai':False,'production_touched':False}
    out=ROOT/'docs/PHASE6E11_CONTROLLER_EVIDENCE.json'
    with out.open('x',encoding='utf8') as stream:json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'status':value['status'],'evidence':str(out),'sources':len(sources),'preserved':len(preserved)}))
if __name__=='__main__':main()
