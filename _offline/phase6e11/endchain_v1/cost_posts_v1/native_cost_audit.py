"""Source-only conditional native-zero proof audit, not a driver probe."""
import ast
import hashlib

import source_cost_probes as probes


def symbol(raw, name):
    nodes = ast.parse(raw).body
    for part in name.split('.'):
        found = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part]
        if len(found) != 1:
            raise ValueError('native_audit_symbol:' + name)
        node = found[0]
        nodes = node.body
    return node


def build(checkpoint):
    costs = checkpoint.source('quota_candidate_v1/runtime_registered_costs.py')
    function = symbol(costs, 'native_proof')
    text = ast.unparse(function)
    # Keep the existing guard policy. An independent binary/OCI attestation
    # is a limitation of this source proof, NOT a new mandatory cost gate.
    if 'psycopg_binary/' not in text or 'item.hash.value' not in text or '(160009, 170006)' not in text:
        raise ValueError('native_guard_policy_changed')
    required = probes.literal(costs, 'NATIVE_SOURCES')
    for path, expected in required.items():
        if hashlib.sha256(checkpoint.source(path)).hexdigest() != expected:
            raise ValueError('native_source_guard_current_bytes_mismatch')
    evidence = probes.native_gate_order(checkpoint.source('quota_candidate_v1/runtime_registered_bootstrap.py'))
    provenance_limitations = [
        'native_proof checks extension hashes against the same installed wheel RECORD, not an independently pinned approved binary manifest',
        'loaded libpq dependency bytes/build-to-reviewed-source identity are not pinned by the two psycopg_binary/*.so-or-pyd checks',
    ]
    rows = []
    routes = [
        ('auth.observer_connect', 'quota_candidate_v1/runtime_registered_startup.py', 'LocalServer.open', True,
         'parameters built locally -> native_proof -> NativeRuntime copies parameters -> _local_call(connection) -> connect'),
        ('auth.observer_reconnect', 'quota_candidate_v1/runtime_registered_startup.py', 'LocalServer.suspend', True,
         '_local_call(connection) -> native_proof(server.parameters) -> same NativeRuntime.connect'),
        ('auth.observer_suspend', 'quota_candidate_v1/runtime_registered_startup.py', 'LocalServer.suspend', True,
         '_local_call(connection) -> native_proof(server.parameters) -> db.close; no connection context exit'),
        ('auth.observer_close', 'quota_candidate_v1/runtime_registered_startup.py', 'LocalServer.close', True,
         '_local_call(connection) -> native_proof(server.parameters) -> db.close in finally; no connection context exit'),
        ('auth.engine.connect', 'quota_candidate_v1/runtime_registered_cleanup.py', 'Prerequisite.connect', True,
         '_State.ctx.dsn from server.dsn -> parent config -> _local_call(connection) -> native_proof(server.parameters) -> RealBackend(config)'),
        ('auth.engine.close', 'quota_candidate_v1/runtime_registered_cleanup.py', 'Prerequisite.close_backend', True,
         '_local_call(connection_close) -> native_proof(server.parameters) -> RealBackend.close -> db.close'),
        ('auth.profile', 'admission_auth_runtime_profile.py', '_execute', True,
         'two _local_call(connection) calls on same owner.runtime; direct closes guarded with connection_close'),
        ('auth.fixture_closeout', 'quota_candidate_v1/runtime_registered_fixture_closeout.py', '_execute', True,
         'two _local_call(connection) calls on owner.runtime plus guarded direct closes; outer observer suspend/reconnect separate'),
        ('auth.scope', 'fixture_producer_scope.py', 'Scope._observe', False,
         'NativeRuntime.disposable constructs fresh parameters from Docker, then runtime.connect directly; suspension guard attests a different connection'),
        ('case.bootstrap.failure_closeout', 'quota_candidate_v1/runtime_bootstrap_closeout.py', 'collect', False,
         'NativeRuntime.disposable -> connect -> raw.close; no Context._local_call/native_proof for this fresh runtime'),
        ('case.quota_read', 'quota_candidate_v1/runtime_case_entry.py', 'quota_samples', False,
         'runtime.connect and connection.close called directly, outside Context connection hook'),
    ]
    for operation, path, method, guarded, route in routes:
        node = symbol(checkpoint.source(path), method)
        missing = []
        if not guarded:
            missing.append('No native_proof immediately before this actual connection/close route; bind its effective parameters/ambient target_session_attrs rather than another observer')
        if operation == 'auth.engine.connect':
            missing.append('Parent DSN follows the source-owned ctx chain, but the pre-dispatch guard receives server.parameters; no explicit equality to parsed actual config.dsn at this boundary')
        if operation == 'auth.engine.close':
            missing.append('Zero close cost is conditional on the opened backend being bound to the source-reviewed RealBackend; the Engine-connect DSN join remains open')
        conditional = guarded and operation != 'auth.engine.connect'
        rows.append({'operation': operation, 'source': path, 'symbol': method,
            'source_sha256': hashlib.sha256(checkpoint.source(path)).hexdigest(),
            'ast_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
            'route': route, 'guard_before_action': guarded, 'conditional_driver_sql_bound': 0,
            'conditional_source_bound': 0 if conditional else None,
            'route_binding_open': bool(missing),
            'root_effective_provenance_open': True,
            'full_cost_post_closed': False,
            'accepted_current_cost_bound': None, 'missing_preconditions': missing,
            'stronger_attestation_optional': True,
            'provenance_limitations_not_new_gates': provenance_limitations,
            'measurement_required_for_source_bound': False,
            'source_proven_autocommit': True, 'source_proven_prepare_threshold_none': True,
            'source_proven_direct_close_not_context_exit': True})
    return {'format': 'native-zero-conditional-source-audit-v1', 'routes': rows,
        'guard_order_probes': evidence,
        'source_bound_contract_startup_commands': ['BEGIN', 'SHOW max_connections', 'COMMIT'],
        'source_bound_contract_startup_upper_bound': 3,
        'startup_bound_accepted': False,
        'startup_conditional_source_bound': 3,
        'startup_bound_scope': 'existing conditional source contract only; not whole managed lifetime or current root composition',
        'startup_missing': ['existing root effective provenance/actual caller composition remains open; independent OCI attestation is not a new requirement'],
        'startup_limitations_not_new_gates': ['release-source derivation does not independently attest OCI build provenance'],
        'accepted_libpq_versions_in_current_guard': [160009, 170006],
        'reported_linux_component_version': None,
        'runtime_binary_observation': 'not imported without original receipt path and hash',
        'source_derivation_can_suffice_without_measurement': True,
        'positive_conditional_zero_routes': sum(r['conditional_source_bound'] == 0 for r in rows),
        'existing_root_gate_source': 'admission_budget_root_runtime.py actual_source_program effective_native_driver_and_OCI_startup_provenance',
        'native_total_accepted': False, 'full_managed_lifetime_bound': None,
        'actual_connection_executed': False, 'full_chain_admission': False}
