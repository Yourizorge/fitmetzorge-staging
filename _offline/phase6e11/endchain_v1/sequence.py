"""Source-bound assembly plan. No hosted adapter, credentials or admission.

Keep the existing product scenario intact. Auth logout follows workflow and
fixture cleanup; a complete Auth test per actor cannot precede that workflow.
"""
import collections,copy,hashlib,importlib.util,json
from scenario import capture,ROOT

AUTH_SOURCE=ROOT/'_offline/phase6e11/auth_metadata_v1/auth_contract.py'
spec=importlib.util.spec_from_file_location('endchain_auth_contract',AUTH_SOURCE)
auth=importlib.util.module_from_spec(spec);spec.loader.exec_module(auth)
ROLES=('a_member','a_trainer','b_member')
ROLE_MAP={'member':'a_member','trainer':'a_trainer','b':'b_member'}
SOURCES=(
 '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py',
 '_offline/phase6e11/auth_metadata_v1/auth_contract.py',
 '_offline/phase6e11/auth_metadata_v1/audit.py',
 '_offline/phase6e11/auth_metadata_v1/hashes.mjs',
 '_offline/phase6e11/controller_guard_v1/guard.py',
 '_offline/phase6e11/controller_guard_v1/issuance.mjs',
 '_offline/phase6e11/controller_v1/auth.mjs',
 '_offline/phase6e11/controller_v1/core.mjs',
 '_offline/phase6e11/controller_v1/manifest.mjs',
 '_offline/phase6e11/controller_v1/store.mjs',
 '_offline/phase6e11/controller_v1/workflow_evidence.mjs',
 '_offline/phase6e11/controller_v1/core.test.mjs',
 '_offline/phase6e11/controller_v1/manifest.test.mjs',
 '_offline/phase6e11/controller_v1/workflow_evidence.test.mjs',
 '_offline/phase6e11/controller_v1/auth_guard.test.mjs',
 '_offline/phase6e11/controller_guard_v1/issuance.test.mjs',
 '_offline/phase6e11/request_v4/handler.mjs',
 '_offline/phase6e11/request_v4/transport.mjs',
 '_offline/phase6e11/request_v4/security.py',
 '_offline/phase6e11/edge_bridge_v2/handler.mjs',
 '_offline/phase6e11/endchain_v1/scenario.py',
 '_offline/phase6e11/endchain_v1/sequence.py',
 '_offline/phase6e11/endchain_v1/budget.mjs',
 '_offline/phase6e11/endchain_v1/budget.test.mjs',
 '_offline/phase6e11/endchain_v1/request_transport.mjs',
 '_offline/phase6e11/endchain_v1/request_transport.test.mjs',
 '_offline/phase6e11/endchain_v1/scoped_cycle.mjs',
 '_offline/phase6e11/endchain_v1/scoped_cycle.test.mjs',
 '_offline/phase6e11/endchain_v1/auth_arm.py',
 'supabase/migrations/20260924130052_phase6e11_private_transaction_audit.sql',
 'supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql',
 'supabase/migrations/20260928120846_phase6e11_request_binding.sql',
 'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql',
 'supabase/migrations/20261012185121_phase6e11_single_endchain_budget.sql',
)
GATES=(
 ('source_ci_and_budget_admission','before_auth'),
 ('exact_guard_install_and_attestation','before_auth'),
 ('exact_auth_observer_install_and_attestation','before_auth'),
 ('fixture_prepare_and_activate','before_workflow'),
 ('negative_controller_and_route_authorization','before_workflow'),
 ('revoke_and_scoped_fixture_delete_pairs','after_workflow_before_logout'),
 ('session_absence_and_preservation','after_logout'),
 ('exact_observer_and_guard_removal','always_safety_finally'),
 ('jit_revocation','always_safety_finally'),
 ('migration_identity_and_empty_dry_run','before_owner_window'),
 ('final_preservation_and_runtime_hashes','before_owner_window'),
)

def counts(rows):
    value=collections.Counter((t,op) for t,op,_ in rows)
    return [{'table':t,'operation':op,'count':n} for (t,op),n in sorted(value.items())]

def compile_sequence():
    scenario=capture();actions=[]
    def auth_action(role,operation):
        writes=[('auth.'+t,op,None) for (t,op),n in auth.COUNTS[operation].items() for _ in range(n)]
        actions.append({'kind':'auth','role':role,'operation':operation,
          'expected_counts':counts(writes),'required_validator':'auth_contract.Contract',
          'app_writes_allowed':False,'request_metadata_required':True,
          'session_key_binding_required':operation not in ('issue','revoked_denial')})
    for role in ROLES:
        for operation in auth.SEQUENCE[:4]:auth_action(role,operation)
    for action in scenario['workflow_actions']:
        actions.append({'kind':'workflow','role':ROLE_MAP[action['role']],
          'operation':action['request']['action'],'scenario_step':action['step'],
          'scenario_contract':copy.deepcopy(action),
          'expected_counts':counts([('fmz6e11_private.'+t,op,key) for t,op,key in action['writes']]),
          'required_validator':'workflow_evidence.validateWorkflow',
          'request_metadata_required':True,'session_key_binding_required':True})
    for role in ROLES:
        for operation in auth.SEQUENCE[4:]:auth_action(role,operation)
    for step,action in enumerate(actions):action['step']=step
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
    return {'status':'OFFLINE_SEQUENCE_PREPARATION_ONLY','hosted_admitted':False,
      'sources':sources,'actions':actions,
      'lifecycle_gates':[{'name':n,'position':p,'compiled':False} for n,p in GATES],
      'workflow_source_sha256':scenario['source_sha256'],
      'minimum_evidence_sql_commands':5*len(actions),
      'full_sql_budget_compiled':False,
      'limitations':['Auth effects are exact local GoTrue v2.196.0 expectations, not hosted proof.',
        'Scenario UUIDs and source templates are placeholders, not hosted row authorization.',
        'Lifecycle actions and full transport command ledger must be compiled before admission.',
        'Owner approved one 1280-command run; the local M44 candidate is not hosted admission.']}

def validate_sequence(value):
    # Bind to source bytes and all lifecycle gaps, not just the action count.
    if value!=compile_sequence():raise ValueError('endchain_sequence_or_source_changed')
    return {'status':'OFFLINE_SEQUENCE_VALID','hosted_admitted':False,
      'workflow_actions':sum(x['kind']=='workflow' for x in value['actions']),
      'auth_actions':sum(x['kind']=='auth' for x in value['actions']),
      'expected_writes':sum(c['count'] for x in value['actions'] for c in x['expected_counts'])}

if __name__=='__main__':print(json.dumps(compile_sequence(),indent=2,sort_keys=True))
