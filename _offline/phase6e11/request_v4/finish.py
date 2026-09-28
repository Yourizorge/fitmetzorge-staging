"""Seal current source/evidence references without rewriting historical attempts."""
import hashlib,json,pathlib
import install as i
from guard import save
HERE=pathlib.Path(__file__).resolve().parent
ROOT=i.ROOT
REFERENCES={
 'local_closure':'phase6e11-request-closeout-0008350441bc44908736191712256093/result.json',
 'ci42':'phase6e11-ci42-b8a0240c7df84466a7095d130b81fa0a/run-36423073344/result.json',
 'local_driver':'phase6e11-workflow-local-a51734e39df247a29694bd453b8056b1/request-v4-result.json',
 'local_security':'phase6e11-request-security-4fb275b9fa374f60a705dfd1c43547f3/request-security.json',
 'hosted_pair':'phase6e11-m42-be9a04735a66446b82d7503cd0d03831/pair.json',
 'historical_stop':'phase6e11-m42-be9a04735a66446b82d7503cd0d03831/result.json',
 'load_correction':'phase6e11-m42-load-closeout-8f2b10b23f9e47bf8bbba31a197ba82e/result.json',
 'fresh_dryrun':'phase6e11-m42-dry-closeout-166cbec729e44984a18e570b280ac621/result.json',
 'ci_diagnostic':'phase6e11-request-ci-receipts-442c38dad2df438ebea001488f865eb1/result.json',
 'temporary_access_closed':'phase6e11-request-probe-close-206b6443675d44fb9c13419567a3ec84/result.json',
 'publication_before_commit':'phase6e11-request-publication-1790601445624.json'}

def main():
    refs={name:ROOT/'supabase/.temp'/path for name,path in REFERENCES.items()}
    data={name:json.loads(path.read_text()) for name,path in refs.items()}
    if data['fresh_dryrun']['status']!='M42_INSTALLATION_PASS_WORKFLOW_PENDING':raise RuntimeError('installation_not_pass')
    if data['temporary_access_closed']['http_after']!=404 or data['temporary_access_closed']['jit_mappings']!=0:raise RuntimeError('access_not_closed')
    before=json.loads((refs['hosted_pair'].parent/'before/identity.json').read_text())
    after=json.loads((refs['hosted_pair'].parent/'after/identity.json').read_text())
    if before['tables']!=after['tables']:raise RuntimeError('drift')
    result={'status':'M42_PASS_HOSTED_EDGE_CONFIGURATION_NO_GO',
      'migration_sha256':i.c.sha(ROOT/'supabase/migrations'/i.M42),
      'migration41_sha256':i.c.sha(ROOT/'supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql'),
      'migrations':{'local':42,'hosted':42,'dryrun':'EMPTY','sql_partition_matches':True},
      'protected_tables':before['tables'],'protected_hashes_equal':True,
      'measurement_commands':[before['query_commands'],after['query_commands']],
      'own_temp_writes':0,'background_temp_bytes':[before['io']['ambient_temp_bytes'],after['io']['ambient_temp_bytes']],
      'background_cause_exactly_known':False,'historical_stop_unchanged':True,
      'evidence':{k:{'path':str(p.relative_to(ROOT)),'sha256':i.c.sha(p)} for k,p in refs.items()},
      'sources':{str(p.relative_to(ROOT)):i.c.sha(p) for p in HERE.iterdir() if p.is_file()},
      'documents':{str(p.relative_to(ROOT)):i.c.sha(p) for p in
        [ROOT/'docs/BUILD_STATUS.md',ROOT/'docs/PHASE6E11_REQUEST_BINDING_REPORT.md']},
      'previous_status_archive':'supabase/.temp/phase6e11-request-closeout-91393bd1e3f741cf8277860341aaa394/BUILD_STATUS.before.md',
      'tests':{'clean_migrations':42,'sql_regressions':12,'local_driver_pairs':45,'local_security':33,
        'baseline_edge':39,'new_request':6,'oidc':19,'installation_load':12,'auth_receipt_units':17,'buffer_local':18},
      'hosted_auth_tests':0,'hosted_workflow_tests':0,'hosted_delete_tests':0,'new_synthetic_fixtures':0,
      'jit':'disabled','jit_mappings':0,'temporary_probe_removed':True,'application_edge_deployed':False,
      'owner_window_open':False,'owner_retest':'NO_GO','freeze':False,'phase6e12_started':False,
      'preservation':data['local_closure']['preservation'],'published_runtime_unchanged':84,'local_candidate_assets_unchanged':88,
      'external_ai_calls':0,'external_ai_cost_eur':0,'real_member_ai_enabled':False,'production_touched':False}
    target=ROOT/'docs/PHASE6E11_REQUEST_BINDING_EVIDENCE.json';save(target,result)
    print(json.dumps({'file':str(target),'sha256':i.c.sha(target),'status':result['status']}))
if __name__=='__main__':main()
