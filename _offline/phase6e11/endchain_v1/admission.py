"""Fail-closed full-chain preregistration. No network, credentials or SQL."""
import hashlib,json,pathlib,sys
from scenario import capture,ROOT

PHASES=('before_saved','action_started','action_confirmed','after_saved','pair_validated')
AUTH=('issue','verify','getUser','refresh','logout','revoked_denial')
ROLES=('a_member','a_trainer','b_member')
MAX_SECONDS=600

def plan():
    value=capture()
    value.update(auth_actions=[{'role':r,'operation':a} for r in ROLES for a in AUTH],
      state_order=[*PHASES,'next_step_allowed'],automatic_retries=0,collectors=1,
      max_seconds=MAX_SECONDS,canary_sql_limit_unchanged=128,
      approved_full_chain_sql_limit=1280,approval_scope='one_run_only',
      reserved_run_id='32321f17-07f1-4f3d-aa4b-3218bc7368a4',hosted_admitted=False,
      setup_and_cleanup_actions='must_be_compiled_and_source_bound_before_admission',
      safety_removal='exact_owned_guard_audit_and_JIT_even_after_NO_GO',
      incomplete_pair='no_dependent_mutation_or_unproven_fixture_cleanup',
      account_deletion='no_existing_registered_account_deletion',
      owner_window='only_after_complete_hosted_chain_and_final_preservation')
    value['minimum_evidence_commands']=len(PHASES)*(len(value['workflow_actions'])+len(value['auth_actions']))
    return value

def validate(value,*,approved_sql_limit=128,compiled_sql_commands=None,lifecycle_compiled=False,
             source_bound_ci=False,hosted_access_attested=False):
    expected=plan()
    if value!=expected:raise ValueError('endchain_manifest_changed')
    if compiled_sql_commands is None or not lifecycle_compiled:raise ValueError('endchain_lifecycle_uncompiled')
    if not isinstance(approved_sql_limit,int) or isinstance(approved_sql_limit,bool) or approved_sql_limit not in (128,1280):raise ValueError('endchain_budget_not_approved')
    if not isinstance(compiled_sql_commands,int) or isinstance(compiled_sql_commands,bool) or compiled_sql_commands<value['minimum_evidence_commands'] or compiled_sql_commands>approved_sql_limit:
        raise ValueError('endchain_query_budget')
    if not source_bound_ci:raise ValueError('endchain_ci_missing')
    if not hosted_access_attested:raise ValueError('endchain_access_missing')
    return {'manifest_sha256':hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'status':'OFFLINE_ADMISSION_INPUTS_VALID','hosted_pass':False}

def main():
    value=plan();folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-endchain-'):raise ValueError('endchain_output_scope')
    folder.mkdir(exist_ok=False)
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    import os
    with (folder/'preregistration.json').open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
    print(json.dumps({'status':value['status'],'workflow_actions':45,'auth_actions':18,
      'minimum_evidence_commands':value['minimum_evidence_commands'],'hosted_admitted':False,
      'sha256':hashlib.sha256(raw).hexdigest()}))

if __name__=='__main__':main()
