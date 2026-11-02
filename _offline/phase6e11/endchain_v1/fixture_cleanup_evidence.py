"""C06 evidence preparation only: no connection, mutation, retry or admission.

The read template is NOT registered for runtime dispatch. Its single statement
is not a complete cost estimate: transaction, IO, ownership, mutation, commit
and independent absence witnesses still need an approved all-prefix register.
Never treat a zero sample as proof that this run deleted the rows.
"""
import hashlib,json,pathlib,uuid

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TABLE_SCOPE={
    'windows':'id=$1::uuid',
    'workspaces':'window_id=$1::uuid or id=any($2::uuid[])',
    'participants':'window_id=$1::uuid',
    'audit':'window_id=$1::uuid',
    'requests':'window_id=$1::uuid',
    'events':'window_id=$1::uuid or workspace_id=any($2::uuid[])',
    **{name:'workspace_id=any($2::uuid[])' for name in
       ('inbox_state','proposals','source_heads','source_versions','plans','b_versions','b_states')},
}
# Fixed source identifiers only. No row bodies, account data or session data.
INVENTORY_SQL="""/* fmz6e11:endchain_v1:partial_fixture_inventory_unregistered */
select jsonb_build_object(
 'window',$1::uuid,'workspaces',to_jsonb($2::uuid[]),
 'readonly',current_setting('transaction_read_only')='on',
 'statement_timeout',current_setting('statement_timeout'),
 'lock_timeout',current_setting('lock_timeout'),
 'counts',jsonb_build_object("""+',\n'.join(
    "'"+name+"',(select count(*) from fmz6e11_private."+name+" where "+predicate+")"
    for name,predicate in TABLE_SCOPE.items())+')) value'

SOURCES=(
    '_offline/phase6e11/endchain_v1/fixture_cleanup_evidence.py',
    '_offline/phase6e11/endchain_v1/test_fixture_cleanup_evidence.py',
    '_offline/phase6e11/endchain_v1/fixture_lifecycle.py',
    '_offline/phase6e11/endchain_v1/workflow_composition.mjs',
    '_offline/phase6e11/endchain_v1/complete_register.py',
    '_offline/phase6e11/endchain_v1/runtime_budget.py',
    '_offline/phase6e11/endchain_v1/metered_composition.py',
    'supabase/migrations/20260916162120_phase6e11_final_app_integration.sql',
    'supabase/migrations/20260924130052_phase6e11_private_transaction_audit.sql',
    'supabase/migrations/20260928120846_phase6e11_request_binding.sql',
)


def parameters(context):
    values=[context.get(name) for name in ('window','a','b')]
    if any(not isinstance(value,str) for value in values):raise ValueError('cleanup_scope_uuid')
    try:canonical=[str(uuid.UUID(value)) for value in values]
    except ValueError:raise ValueError('cleanup_scope_uuid') from None
    if values!=canonical or len(set(values))!=3:raise ValueError('cleanup_scope_binding')
    return [values[0],values[1:]]


def classify_sample(row,context,*,worker_terminated,writer_transactions_closed):
    """Validate a supplied sample, not its transport or an executed cleanup."""
    window,workspaces=parameters(context)
    expected={'window','workspaces','readonly','statement_timeout','lock_timeout','counts'}
    if not isinstance(row,dict) or set(row)!=expected:raise ValueError('cleanup_sample_shape')
    if row['window']!=window or row['workspaces']!=workspaces:raise ValueError('cleanup_sample_scope')
    if row['readonly'] is not True or row['statement_timeout'] not in ('5s','5000ms') or row['lock_timeout'] not in ('1s','1000ms'):
        raise ValueError('cleanup_readonly_limits')
    counts=row['counts']
    if not isinstance(counts,dict) or set(counts)!=set(TABLE_SCOPE) or any(type(n) is not int or n<0 for n in counts.values()):
        raise ValueError('cleanup_sample_coverage')
    if type(worker_terminated) is not bool or type(writer_transactions_closed) is not bool:
        raise ValueError('cleanup_barrier_shape')
    terminal=worker_terminated and writer_transactions_closed
    zero=not any(counts.values())
    return {'status':'INCOMPLETE_WRITER_BARRIER' if not terminal else
            'SCOPED_ZERO_SAMPLE_ONLY' if zero else 'SCOPED_FIXTURES_REMAIN',
        'counts':dict(counts),'sampled_rows':sum(counts.values()),'all_sampled_counts_zero':zero,
        'worker_terminated':worker_terminated,'writer_transactions_closed':writer_transactions_closed,
        'cleanup_proven':False,'delete_count':None,'deletion_proven':False,
        'transport_and_io_verified':False,'ownership_for_delete_proven':False,
        'historical_evidence_modified':False,'hosted_admitted':False}


def source_gaps():
    """Bind the actual missing safety registration and current normal-path gates."""
    from complete_register import safety_path
    from metered_composition import capacity
    registered=safety_path(guard=True,observer=True,controls=True,claimed=True,auth_maybe_live=True)
    actions={row['action'] for row in registered}
    missing=[action for action in ('fixture_cleanup_inventory','fixture_cleanup_delete','fixture_cleanup_absence')
             if action not in actions]
    source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}
    anchors=[]
    checks={
        '_offline/phase6e11/endchain_v1/workflow_composition.mjs':
            ('cleanup_preregistered_count','cleanup_auth_denied'),
        'supabase/migrations/20260928120846_phase6e11_request_binding.sql':
            ('request_previous_pair_incomplete','request_cleanup_guard'),
        '_offline/phase6e11/endchain_v1/complete_register.py':
            ('Rollback once, preserve incomplete evidence/fixtures',),
    }
    for name,markers in checks.items():
        lines=(ROOT/name).read_text().splitlines()
        for marker in markers:
            positions=[i for i,line in enumerate(lines,1) if marker in line]
            if len(positions)!=1:raise ValueError('cleanup_source_gate_changed')
            anchors.append({'file':name,'line':positions[0],'gate':marker,'sha256':source_hashes[name]})
    plan=capacity()
    return {'status':'NO_GO_PARTIAL_FIXTURE_SUFFIX_UNPROVEN','source_hashes':source_hashes,
        'source_gates':anchors,'missing_safety_actions':missing,
        'registered_safety':registered,'normal_capacity':plan['normal_capacity'],
        'approved_limit':plan['approved_limit'],
        'normal_cleanup_final_closure_reserve':sum(plan['phase_budgets'][p] for p in ('cleanup','final','closure')),
        'normal_reserve_is_not_new_safety_authorization':True,
        'inventory_sql_sha256':hashlib.sha256(INVENTORY_SQL.encode()).hexdigest(),
        'new_suffix_command_count':None,'all_prefix_bound_proven':False,
        'runtime_wired':False,'sql_emitted':0,'delete_count':None,'cleanup_proven':False,
        'hosted_admitted':False,
        'required_integration':[
            'Persist the pre-mutation run/window/workspace ownership journal and baseline absence.',
            'After worker join, close all writers and prove no in-flight writer before taking a fresh inventory.',
            'Compile an independent exact key/delete manifest, including cascade effects, without rewriting incomplete historical pairs.',
            'Register every inventory/IO/transaction/delete/commit/absence command before dispatch; prove all prefixes <=2349.',
            'Wire parent-owned one-shot cleanup before temporary guard removal; preserve unknown responses without retry.',
            'Require committed delete multiset, fresh independent absence, protected-data preservation and unchanged WAL/temp limits.',
        ]}


if __name__=='__main__':print(json.dumps(source_gaps(),indent=2,sort_keys=True))
