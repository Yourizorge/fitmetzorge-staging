"""Source-bound offline write-route contract, not authorization to execute routes."""
import ast
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
PRIVATE = 'fmz6e11_private.'
PHASES = ['before_saved', 'action_started', 'action_confirmed', 'after_saved', 'pair_validated', 'next_step_allowed']
MIGRATION = 'supabase/migrations/20260916162120_phase6e11_final_app_integration.sql'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_manifest(root=ROOT):
    files = []
    for folder in ('_offline/phase6e11', '_offline/phase6e10/ops', 'supabase/migrations'):
        for p in (root / folder).rglob('*'):
            if p.suffix in {'.py', '.mjs', '.cjs', '.sql', '.txt'} and not any(
                    x in p.parts for x in ('readiness_v1', '__pycache__')):
                files.append(p)
    files.extend(p for p in (root / 'assets').glob('phase6e11-*') if p.is_file())
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(set(files))}


def effect(table, operations, origin='direct'):
    return {'table': table if '.' in table else PRIVATE + table,
            'operations': operations.split(','), 'origin': origin}


def contracts():
    routes = []
    common = [effect('windows', 'update'), effect('audit', 'insert'),
              effect('requests', 'insert'), effect('events', 'insert')]
    def add(family, action, effects, transport='edge_rpc', aliases=(), closure=True, note=''):
        routes.append({
            'route_id': family + '.' + action, 'step_id_template': '{run_id}/{ordinal}/' + family + '.' + action,
            'action': action, 'family': family, 'transport': transport, 'aliases': list(aliases),
            'effects': effects, 'measurement_required': True,
            'before': 'durable same-contract scoped identity before action_started',
            'transaction': 'committed receipt plus request/actor/scope/source binding; transport ACK alone is insufficient',
            'after': 'durable immediate scoped identity even after denied/replayed/failed request',
            'phases': PHASES, 'missing_evidence_status': 'NO_GO',
            'cleanup_status': 'forbidden until pair_validated and separate sealed cleanup manifest',
            'direct_effects_reviewed': True, 'local_declared_effects_closed': closure,
            'complete_transitive_write_closure_proven': False,
            'note': note,
        })
    for action in ('member_accept', 'member_reject', 'trainer_approve', 'trainer_reject', 'trainer_block'):
        add('A', action, [effect('proposals', 'update'), *common])
    add('A', 'propose', [effect('proposals', 'insert'), *common])
    add('A', 'restore', [effect('proposals', 'insert'), *common],
        note='Creates proposal only; separate accept/approve/apply creates version.')
    add('A', 'apply', [effect('plans', 'insert'), effect('workspaces', 'update'), effect('proposals', 'update'), *common])
    add('A', 'source_append', [effect('source_versions', 'insert'), effect('source_heads', 'insert,update'), *common])
    add('A', 'source_withdraw', [effect('source_heads', 'update'), *common])
    for action in ('b_build', 'b_edit', 'b_confirm', 'b_apply', 'b_reject', 'b_restore', 'b_reopen'):
        effects = [effect('b_states', 'update'), effect('windows', 'update'), effect('requests', 'insert'), effect('events', 'insert')]
        if action == 'b_apply':
            effects.append(effect('b_versions', 'insert'))
        add('B', action, effects, note='b_build is intake using fixed defaults; b_edit has replace/add/remove/move subtypes. Edge first reads B state; one SQL transaction performs mutation.')
    for action in ('viewed', 'later'):
        add('shared', action, [effect('inbox_state', 'insert,update'), effect('requests', 'insert'), effect('events', 'insert')])
    window_common = [x for x in common if x['table'] != PRIVATE + 'events']
    add('window', 'prepare', [effect('windows', 'insert'), effect('participants', 'insert'),
        effect('workspaces', 'insert'), effect('plans', 'insert'), effect('b_states', 'insert'), *window_common])
    for action in ('activate', 'revoke'):
        add('window', action, window_common)
    add('window', 'cleanup', [
        *[effect(x, 'delete') for x in ('workspaces', 'participants', 'audit', 'requests', 'events')],
        *[effect(x, 'delete', 'workspace_fk_cascade') for x in ('source_versions', 'source_heads', 'plans', 'proposals', 'b_states', 'b_versions', 'inbox_state')],
        effect('windows', 'update'), effect('audit', 'insert'), effect('requests', 'insert')],
        note='Retains window tombstone and creates final audit/request receipt; does not mean all rows become zero.')
    for action in ('stale_revision', 'wrong_proposal_version', 'wrong_source_version', 'double_apply_new_key',
                   'idempotency_payload_conflict', 'consent_or_safety_block', 'unknown_action'):
        add('denial', action, [effect('events', 'insert')], note='Authorized workspace: inner SQL subtransaction rolls back business writes, outer denial event commits. Management/early authorization failures can roll back all writes.')
    add('replay', 'same_request_key', [effect('events', 'insert')],
        note='A/B replay commits only replay event; management replay may be fully read-only; no second plan.')
    add('denial', 'early_authorization', [], note='No target audit write before principal/workspace authorization.')
    auth_specs = {
        'auth_generate_link': [('auth.users', 'update'), ('auth.one_time_tokens', 'insert,update,delete'), ('auth.audit_log_entries', 'insert')],
        'auth_verify': [('auth.users','update'), ('auth.identities','update'), ('auth.sessions','insert'),
                        ('auth.refresh_tokens','insert'), ('auth.one_time_tokens','delete'), ('auth.audit_log_entries','insert')],
        'auth_refresh': [('auth.sessions','update'), ('auth.refresh_tokens','insert,update'), ('auth.audit_log_entries','insert')],
        'auth_logout': [('auth.sessions','delete'), ('auth.refresh_tokens','update,delete'), ('auth.audit_log_entries','insert')],
        'new_denial_control': [('auth.users','insert'), ('auth.identities','insert'), ('auth.audit_log_entries','insert'), ('public.profiles','insert')],
        'delete_control_identity': [('auth.users','delete'), ('auth.identities','delete'), ('auth.audit_log_entries','insert')],
    }
    for action, effects in auth_specs.items():
        add('auth', action, [effect(t, o, 'service_contract_requires_live_closure') for t, o in effects],
            'auth_http', closure=False,
            note='Listed effects are candidate service footprint, NOT an exhaustive verified GoTrue/trigger/FK closure; full closure gate remains false. GET /user is separately read-only.')
    for action in ('revoke_retained_sessions', 'revoke_interrupted_synthetic_sessions', 'revoke_control_sessions', 'revoke_test_session'):
        add('sql', action, [effect('auth.sessions','delete'), effect('auth.refresh_tokens','delete','fk_requires_verification'),
            effect('auth.mfa_amr_claims','delete','fk_requires_verification')], 'direct_sql', closure=False)
    add('sql', 'new_denial_profile', [effect('public.profiles','insert,update')], 'direct_sql', closure=False,
        note='Triggers on profiles must be transitively resolved; only exact synthetic controls permitted.')
    add('sql', 'delete_control_profile', [effect('public.profiles','delete')], 'direct_sql', closure=False)
    add('sql', 'new_private_registry', [effect('identities','insert'), effect('operators','insert'), effect('config','update')], 'direct_sql')
    add('management', 'new_edge_proof', [], 'management_secret', closure=False,
        note='External configuration write cannot be proven by database table hashes; forbidden in current task.')
    for action, table, operations in (
            ('safety_guard_or_consent', 'workspaces', 'update'),
            ('trainer_relation', 'public.profiles', 'update'),
            ('force_expiry', 'windows', 'update'),
            ('immutable_source_attempt', 'source_versions', 'update')):
        add('local_fixture', action, [effect(table, operations)], 'local_sql_only', closure=False,
            note='Existing negative-test injection, forbidden against hosted staging. Immutable-source attempt must roll back; the others require separate restoration pairs.')
    for action in ('install_failure_trigger', 'remove_failure_trigger'):
        add('local_fixture', action, [], 'local_ddl_only', closure=False,
            note='Existing test_fault function/trigger creation or deletion, not covered by row hashes; strictly local only.')
    return routes


def measured_labels(root=ROOT):
    result = []
    for rel in source_manifest(root):
        if not rel.endswith('.py') or not rel.startswith('_offline/phase6e11/'):
            continue
        tree = ast.parse((root / rel).read_text(encoding='utf-8-sig'))
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call) or len(n.args) < 2:
                continue
            is_gate = isinstance(n.func, ast.Attribute) and n.func.attr == 'run' and isinstance(n.func.value, ast.Name) and n.func.value.id in ('gate', 'g')
            is_measure = isinstance(n.func, ast.Name) and n.func.id == 'measured'
            if (is_gate or is_measure) and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                result.append({'file': rel, 'line': n.lineno, 'action': n.args[1].value})
    return sorted(result, key=lambda x: (x['file'], x['line']))


def build(root=ROOT):
    routes = contracts()
    metadata_path = 'docs/PHASE6E11_PG17_READONLY_METADATA.json'
    metadata_bytes = (root / metadata_path).read_bytes()
    observed = json.loads(metadata_bytes)['after']
    return {'version': '6e11-write-action-v1', 'baseline': '7883c2a90c7bed9e6bb27dbabf11ddedce0d08de',
        'scope': 'source-reviewed registry; no hosted execution or hidden closure assumption',
        'sources': source_manifest(root), 'measured_calls': measured_labels(root), 'routes': routes,
        'dependency_evidence': {'file': metadata_path, 'sha256': sha(metadata_bytes),
            'observed_at': observed['observed_at'],
            'foreign_keys': observed['foreign_keys'], 'triggers': observed['triggers'],
            'coverage': 'observed subset, not a transitive closure or permission to delete',
            'auth_insert_bootstrap': 'live body hash matches the local return-new no-op; profile insertion is a separate direct SQL route',
            'unresolved_body_binding': ['public.touch_updated_at']},
        'dispatch': {'edge': 'POST /functions/v1/fmz-phase6e11',
            'rpc': 'POST /rest/v1/rpc/fmz6e11_call',
            'sql_chain': ['public.fmz6e11_call', 'fmz6e11_private.api_call', 'fmz6e11_private.base_call'],
            'internal_b': 'server computation, never accepted as client role authority',
            'read_only_ops': ['home', 'read'], 'unregistered_dispatch': 'NO_GO'},
        'remaining_gaps': ['Auth service and transitive trigger/cascade closure',
            'external writer/cron write-then-revert coverage across 143 tables',
            'hosted runner does not yet consume this registry or query budget',
            'historical snapshot canonicalization/expected-hash bridge'],
        'complete_hosted_write_coverage': False}


def validate(register, root=ROOT, verify_sources=True):
    if verify_sources and register['sources'] != source_manifest(root):
        raise ValueError('source_manifest_changed_or_new_file')
    if register['dependency_evidence'] != build(root)['dependency_evidence']:
        raise ValueError('dependency_evidence_changed')
    ids = [r['route_id'] for r in register['routes']]
    expected = [r['route_id'] for r in contracts()]
    if sorted(ids) != sorted(expected) or len(ids) != len(set(ids)):
        raise ValueError('unregistered_write_route')
    actions = {r['action'] for r in register['routes']}
    if any(x['action'] not in actions for x in register['measured_calls']):
        raise ValueError('unregistered_measured_write')
    for route in register['routes']:
        if not route['measurement_required'] or route['phases'] != PHASES or not all(
                route.get(k) for k in ('before','transaction','after','missing_evidence_status','cleanup_status')):
            raise ValueError('missing_measurement_contract')
        expected_route = next(r for r in contracts() if r['route_id'] == route['route_id'])
        if route != expected_route:
            raise ValueError('route_contract_changed')
    return {'registered_routes': len(ids), 'source_files': len(register['sources']),
            'static_contract_pass': True, 'hosted_coverage_pass': False}


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--emit']:
        print(json.dumps(build(), indent=2, sort_keys=True))
    else:
        print(json.dumps(validate(json.loads((HERE / 'register.json').read_text()))))
