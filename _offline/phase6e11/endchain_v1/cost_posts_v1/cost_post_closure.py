"""Pinned offline 47-post compiler. No runtime admission or external calls.

The retained register is input evidence, not executable code. Current source
bytes must match every pin. Alias obligations are cross-references, never extra
charges. Explicit caps, declared reservations and unknown total costs differ.
"""
import argparse
import ast
import collections
import hashlib
import json
import os
import pathlib

import source_cost_probes as probes
import native_cost_audit

PREFIX = '_offline/phase6e11/endchain_v1/'
HERE = pathlib.Path(__file__).resolve().parent
LIMIT = 2349


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class Checkpoint:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve(strict=True)
        self.manifest = json.loads((HERE / 'sources.json').read_bytes())
        self.raw = {}
        for name, digest in self.manifest['sources'].items():
            self.raw[name] = self.read(name, digest, 2_000_000)
        ref = self.manifest['report']
        raw = self.read(ref['path'], ref['sha256'], ref['bytes'])
        require(len(raw) == ref['bytes'], 'report_bytes')
        self.report = json.loads(raw)
        require(self.report['approved_limit'] == self.report['hosted_limit'] == LIMIT, 'limit_changed')
        require(len(self.report['missing_costs']) == 47, 'post_inventory_changed')
        require(self.report['bound_complete'] is False, 'unexpected_complete_input')

    def read(self, name, digest, limit):
        path = self.root / name
        require(not pathlib.PurePosixPath(name).is_absolute() and '..' not in pathlib.PurePosixPath(name).parts,
                'source_path')
        require(path.resolve(strict=True).is_relative_to(self.root), 'source_escape')
        for part in (path, *path.parents):
            if part == self.root:
                break
            require(not part.is_symlink() and not getattr(part, 'is_junction', lambda: False)(), 'source_link')
        require(path.stat().st_size <= limit, 'source_size')
        raw = path.read_bytes()
        require(len(raw) <= limit and sha(raw) == digest, 'source_changed:' + name)
        return raw

    def source(self, name):
        return self.raw[PREFIX + name]

    def refs(self, names):
        return [{'path': PREFIX+n, 'sha256': sha(self.source(n))} for n in names]

    def recheck(self):
        for name, raw in self.raw.items():
            self.read(name, sha(raw), 2_000_000)


class PrefixLedger:
    """Offline reservation replay only; uncertainty is sticky and never refunded."""
    def __init__(self, events):
        self.events, self.index, self.charged = events, 0, 0
        self.groups, self.uncertain = set(), set()

    def advance(self, event_id, *, outcome='confirmed'):
        require(self.index < len(self.events), 'extra_event')
        event = self.events[self.index]
        require(event['event_id'] == event_id, 'event_order')
        require(outcome in event['outcomes'], 'event_outcome')
        if event['stage'] == 'precharge':
            group = event['charge_group']
            require(group not in self.groups and type(event['cost']) is int and event['cost'] >= 0,
                    'charge_group_replay')
            # Even an uncertain rejected reservation is not used as refund.
            self.charged += event['cost']
            self.groups.add(group)
        if outcome != 'confirmed':
            self.uncertain.add(event_id)
        self.index += 1
        return self.receipt()

    def receipt(self):
        return {'events_reached': self.index, 'declared_charged': self.charged,
                'unknown_events': sorted(self.uncertain), 'refund': 0,
                'actual_sql_commands': None, 'admitted': False}


# Every historical missing label receives an exact current implementation
# location. Root labels are aliases of components, not independent SQL costs.
ROOT_MAP = {
    'platform_install': ('case.platform.install', ['install_platform.py'], 'platform'),
    'clean47': ('case.bootstrap.clean47', ['case_stack_v1/bootstrap.py', 'cli_predispatch/pending.py'], 'bootstrap'),
    'auth_start': ('auth.auth_start', ['quota_candidate_v1/runtime_registered_startup.py', 'quota_candidate_v1/runtime_registered_costs.py'], 'managed'),
    'auth_target': ('auth.target_before/auth.auth_target_connection/auth.seed', ['quota_candidate_v1/runtime_registered_startup.py', 'quota_candidate_v1/runtime_registered_bootstrap.py'], 'seed'),
    'auth_create': ('auth.create.*', ['quota_candidate_v1/runtime_registered_bootstrap.py'], 'managed'),
    'quota_read': ('case.quota_read', ['quota_candidate_v1/runtime_case_entry.py', 'integral_io.py'], 'quota'),
    'cli_isolation': ('case.core/cli pending isolation', ['quota_candidate_v1/runtime_prefix.py', 'cli_predispatch/pending.py'], 'isolation'),
    'core_recovery': ('case.core/recovery', ['quota_candidate_v1/runtime_recovery.py', 'control_recovery.py'], 'recovery'),
    'fixture_tracking': ('case.core/tracking', ['fixture_db_terminality.py', 'fixture_producer_scope.py'], 'tracking'),
    'fixture_closure': ('auth.fixture_closeout', ['quota_candidate_v1/runtime_registered_fixture_closeout.py', 'fixture_cleanup_runtime.py'], 'fixture'),
    'auth_closure': ('auth.parent_cleanup', ['quota_candidate_v1/runtime_registered_cleanup.py', 'auth_failure_parent_finalizer.py'], 'parent'),
    'auth_stop': ('auth.auth_stop', ['quota_candidate_v1/runtime_registered_startup.py'], 'managed'),
    'case_finally': ('case.core/session close', ['quota_candidate_v1/runtime_case_entry.py', 'hosted_gate.py', 'registered_runner.py'], 'recovery'),
}
REASONS = {
    'platform': '36 outer calls/13 direct SQL are bounded; image entrypoint, nested CLI/services, implicit psql, background/reset and failed-install cleanup are not.',
    'bootstrap': 'Canonical rebuild is local setup. Source receipts and AST+16 CLI reservations do not bound native startup/reset/implicit protocol; complete prefix originals remain required.',
    'managed': '128 is a reservation, not a managed SQL upper bound. Startup source derivation is conditional on OCI/build/config; settle lifetime once after stop, never sum overlapping observations.',
    'native': 'Existing native_proof conditional source bound0 is valid without measurement. Seven guarded routes are positive; existing root effective provenance, unguarded callers and Engine DSN/backend joins remain distinct. Independent wheel/OCI attestation is optional, not a new gate.',
    'seed': 'Original seed is now independently enumerated: at most9 explicit calls, no rollback after COMMIT attempt. Connection and target-profile dependencies remain separate and unresolved.',
    'profile': 'Original guard enforces11 single-statement calls; two profile connections plus observer suspension/reconnect lack complete implicit-cost proof. Commit-unknown is not refunded.',
    'fixture': 'Original guard enforces37 single-statement calls (normal36/physical-only23); ownership/terminal proof, implicit connections and outer exception composition remain mandatory.',
    'parent': 'Implemented adapters invalidate the old not-implemented description. 13+5N explicit scope/observer slots plus128N declared DELETE tickets; managed DELETE and connection/lifetime union not bounded.',
    'quota': '20 ordered explicit calls include rollback; no retry. One native connection/open-close still lacks effective driver-cost proof.',
    'isolation': '4 normal/8 exceptional isolation slots per reached pending slot are not a complete driver/CLI bound; reconcile reachability with outer root and avoid duplicate core charging.',
    'tracking': 'Source hooks exist; registry state, producer scope and physical-terminal branches must bind every native dispatch before a root total can be stated.',
    'recovery': 'Pinned recorder bounds direct recovery at8 SQL,1 replacement,5 closes; these are already within case.core. Shared prefix allowance, caller session closes and exceptional entry state are not yet joined.',
    'core_native': '88 source joins exist;1407 retained native/observer rows lack an actual dispatcher binding. Historical reservation rows cannot prove execution count.',
    'context': 'Cleanup depends on seed/ownership/worker/commit state; normal and14 selected prefixes are mapped, but suffix failures and all conditional native/managed costs remain unknown.',
    'scope': 'Disposable platform/bootstrap must not inflate hosted requirement. Core caller projection is not fully proven; local CI remains visible and hosted total stays null.',
    'inventory': 'Retained source pins match current bytes; added narrow caller/WAL pins do not prove transitive dynamic imports, subprocess inputs, released CLI/OCI or driver binary closure.',
    'meter': 'Actual unchanged meter predicates require2352 for the retained partial core, with first denial2350. This is a proven cap blocker, not a complete execution maximum or quota request.',
}


NEXT = {
 'actual_join:exception:8695': ('Map each nonconfirmed event.next to the actual entry state of runtime_recovery.finish; use the original eight-slot recorder without granting duplicate rollback credits.', 'core.dag.actual_join_proofs.proofs.exception.unjoined_prefix_outcomes + runtime_case_entry.execute_registered finally', 'offline_join'),
 'actual_join:native:1407': ('Bind each unmatched retained_row_id to an actual runtime_catalog/runtime_stream/native dispatcher, statement identity and maximum multiplicity; fail on extra or omitted rows.', 'core.dag.actual_join_proofs.proofs.native.unmatched_row_ids + runtime_adapter/registered_runner actual calls', 'offline_join'),
 'actual_meter_requires_2352': ('Keep admission denied at the existing first2350 requirement; finish missing recovery joins before calculating a complete minimum. Do not alter classification or cap.', 'core.dag.meter_requirements.rows and runtime_budget mutation/reserve predicates', 'proven_blocker'),
 'auth.auth_start:managed_sql_bound': ('Join the existing conditional startup3 source contract to serve-only/configured caller and fault branches; preserve its OCI limitation without inventing a new independent-attestation requirement.', 'runtime_registered_startup.LocalServer.open + runtime_registered_costs.source_bound_contract + existing root effective-provenance join', 'offline_join'),
 'auth.auth_stop:managed_stop_or_driver_close_sql': ('Bind exact-owned stop and after-stop backend absence to lifetime termination; account managed shutdown independently from the Docker process call.', 'LocalServer.close + original process-stopped/backend-after-stop/lifetime records', 'runtime_and_source'),
 'auth.create.a_member:128_is_declared_reservation_not_managed_upper_bound': ('Derive POST/admin/users SQL upper bound for first a_member creation, including triggers/config and transport-unknown outcome; do not accept128 as proof.', 'BootstrapRequests._create_owned a_member + pinned GoTrue handler/storage schema', 'source_derivation'),
 'auth.create.a_trainer:128_is_declared_reservation_not_managed_upper_bound': ('Derive second a_trainer create bound with one existing owned account; bind owner journaling failure and no replay.', 'BootstrapRequests._create_owned a_trainer + original admitted/owned refs + pinned GoTrue handler', 'source_derivation'),
 'auth.create.b_member:128_is_declared_reservation_not_managed_upper_bound': ('Derive third b_member create bound and final complete/seal publication failures; retain all three consumed creates on loss.', 'BootstrapRequests._create_owned b_member/create_all/close + exact managed storage branch', 'source_derivation'),
 'auth.derived_cost_contract:effective_native_driver_and_OCI_startup_provenance': ('Retain the existing root effective-provenance gate; bind native0/startup3 conditions to actual caller/configuration. Independent wheel/libpq/OCI attestation is optional; do not add it as a universal gate.', 'runtime_registered_costs.native_proof/source_bound_contract + admission_budget_root_runtime.py effective-provenance branch', 'offline_join'),
 'auth.engine.a:delete:128_delete_reservation_not_managed_upper_bound': ('Derive owned a-member DELETE/admin/users managed SQL maximum; include user-cascade shape and lost response, not just ticket128.', 'Prerequisite.delete + auth_failure_parent_finalizer.Engine role a + pinned GoTrue DELETE handler', 'source_derivation'),
 'auth.engine.b:delete:128_delete_reservation_not_managed_upper_bound': ('Derive owned b-member DELETE bound for its actual cleanup order and remaining related rows; preserve unknown deletion outcome.', 'Prerequisite.delete + Engine role b + current FK/cascade contract', 'source_derivation'),
 'auth.engine.trainer:delete:128_delete_reservation_not_managed_upper_bound': ('Derive trainer DELETE bound with trainer/member FK restrictions and actual prior deletions; do not reuse member bound without source proof.', 'Prerequisite.delete + Engine trainer + exact FK before/after evidence', 'source_derivation'),
 'auth.engine.close:driver_close_SQL': ('Bind backend.close implementation/transaction state to exact runtime library; retain close failure and never clear an unresolved DELETE.', 'Prerequisite.close_backend + auth_failure.RealBackend.close + effective driver proof', 'source_provenance'),
 'auth.engine.connect:driver_implicit_SQL': ('Bind RealBackend constructor/connect effective parameters and library identity; include connection failure before parent Engine starts.', 'Prerequisite.connect + auth_failure.RealBackend.__init__ + native_proof', 'source_provenance'),
 'auth.fixture_closeout:C_physical_suffix_actual_state_and_terminal_join': ('Join original worker/HTTP terminal proof and ownership registry to selected physical suffix for every reached core fault; reject absent or unknown-commit deletion authority.', '_State.attest + physical.run + original write-registry-refs and worker-recovery refs', 'offline_join'),
 'auth.fixture_closeout:fixture_connections_suspend_reconnect_and_fault_edges': ('Compose the37-command guard with two actual fixture connections plus observer suspend/reconnect and failures at each boundary.', 'runtime_registered_fixture_closeout._execute/run + LocalServer.suspend + effective driver proof', 'offline_join'),
 'auth.health:managed_sql_bound': ('Derive /health handler and concurrent managed-worker costs in exact GoTrue build; one HTTP attempt alone is not a SQL bound.', 'runtime_registered_startup.health + pinned GoTrue health route and worker configuration', 'source_derivation'),
 'auth.observer_close:managed_stop_or_driver_close_sql': ('Prove final observer connection.close behavior after all closeout failures; include pending transaction state and library identity.', 'LocalServer.close finally + original observer-close and driver identity', 'source_provenance'),
 'auth.observer_connect:driver_implicit_sql': ('Bind initial observer runtime.connect parameters before profile/startup to reviewed binary/driver source; no synthetic-peer zero promotion.', 'LocalServer.open observer_connect + NativeRuntime.connect effective parameters', 'source_provenance'),
 'auth.observer_reconnect:driver_implicit_SQL': ('Bind reconnect in suspend.finally, including when the suspended body fails; count a distinct connection attempt and preserve primary error.', 'LocalServer.suspend finally + per-call effective parameters and driver provenance', 'source_provenance'),
 'auth.observer_suspend:driver_close_sql': ('Bind pre-profile/cleanup observer close and failed-close state; do not assume reconnect ran when close was not confirmed.', 'LocalServer.suspend before yield + native close implementation', 'source_provenance'),
 'auth.parent_cleanup:actual_parent_engine_and_shared_fixture_proof_prefix_join': ('Connect preseed0..3 ownership and postbody C-proof branches to the actual Engine trace; settle lifetime once and never delete on incomplete proof.', 'runtime_registered_cleanup.run/_State.attest + Context._finish + original producer seal/C proof', 'offline_join'),
 'auth.profile:profile_connections_suspend_reconnect_and_fault_edges': ('Compose proven11 explicit profile slots with suspend, two connects, two closes and reconnect; retain unknown COMMIT and no auto-restore.', 'admission_auth_runtime_profile._execute/run + LocalServer.suspend + driver proof', 'offline_join'),
 'auth.scope:scope_connection_implicit_SQL': ('Bind exact10-command Scope attestation connection and its close before Engine admission; include failed privilege/producer checks.', 'runtime_registered_cleanup._State.attest + fixture_producer_scope.Scope + driver proof', 'source_provenance'),
 'case.auth.context:child_normal_and_all_fault_suffixes': ('Connect the15 selected case programs to actual Context startup/enter/exit and preseed ownership branches, preserving cleanup on enter failure.', 'Context.__enter__/_finish + case_fault selectors + original child terminal evidence', 'offline_join'),
 'case.auth.context:conditional_cleanup_edges': ('Expand cleanup-selection, producer-constructor/close, seed attempted/confirmed, C-proof and parent-Engine failure transitions; do not use caller-chosen skip edges.', 'Context._finish + Ledger.select_cleanup source-owned predicates', 'offline_join'),
 'case.bootstrap.clean47:canonical47_rebuild_CLI_protocol_observers_and_isolation': ('Compose clean-stack reset, history provisioning,44 canonical originals, M45 receipt branch and app46/47 protocol/isolation counts with native startup costs.', 'case_stack_v1.bootstrap + prefix_receipt + cli_predispatch.pending + actual original ref closure', 'offline_join'),
 'case.bootstrap.failure_closeout:fresh_connection_implicit_SQL': ('Compose existing four direct absence queries and Docker inventory with NativeRuntime.disposable discovery/connect/close/clear after each pre/post-M45 fault.', 'runtime_bootstrap_closeout.collect + NativeRuntime.disposable + original preauth absence refs', 'source_provenance'),
 'case.core:actual_prefix_recovery_and_managed_partition_join': ('Partition confirmed native/CLI and managed lifetime from actual parent dispatch, retaining unknown replies and shared prepaid groups.', 'runtime_case_entry.observed_core/observed_fault_core + runtime_parent_workflow.dispatch_reply + Context._settle_root', 'offline_join'),
 'case.core:actual_recovery_state_expansion': ('Attach each fault prefix to its owned connections/controls/worker/cache state and the original8/1/5 recovery recorder; do not add its standalone maximum again.', 'runtime_recovery.finish + PreparedExecution and prefix state + register_recovery_paths', 'offline_join'),
 'case.core:hosted_projection_requires_exact_caller_scope': ('Prove which real core callers are hosted-equivalent and which setup/fixture diagnostics are local-only; preserve both ledgers and all commands.', 'runtime_case_entry.execute_registered + runtime_adapter + original caller/domain bindings', 'scope_join'),
 'case.platform.install:platform_startup_implicit_SQL_and_process_inventory': ('Expand each of eight named inner atoms beginning exact PG-image entrypoint/initdb and released CLI start; bind retries, managed services, reset and failure cleanup before total admission.', 'install_platform.UNKNOWN/UPSTREAM_PINS + Gate.install + exact OCI/CLI build source and subprocess inputs', 'source_provenance'),
 'case.quota_read:20_explicit_plus_unbound_connection': ('Bind the20 ordered QueryIO calls and conditional rollback to runtime.connect/close cost under exact effective parameters.', 'runtime_case_entry.quota_samples/quota_read_program + integral_io.QueryIO + driver proof', 'source_provenance'),
 'source_inventory:transitive_dynamic_import_and_subprocess_input_closure': ('Close imports and invoked script/config inputs outside the143 checked pins; bind executable/image bytes, not only repository source or declared expected hashes.', 'bound_module/dependency callers + Gate.command argv/input closure + exact released artifact hashes', 'source_provenance'),
}
ROOT_NEXT = {
 'platform_install': ('Use the platform outer-prefix subprogram; join its eight unknown inner atoms once at the root, not as a second platform charge.', 'install_platform.source_program/_Monitor + case_stack_v1.ci'),
 'clean47': ('Join bootstrap local setup and pre/post45 closeout to the root program; do not replay canonical45 in the actual core.', 'bootstrap/prefix_receipt/runtime_bootstrap_closeout + root_order'),
 'auth_start': ('Replace stale migrations-not-implemented wording with exact serve-only source contract; keep OCI/build and managed startup bound unresolved.', 'LocalServer.open/configuration + runtime_registered_costs.source_bound_contract'),
 'auth_target': ('Use the existing target attestations and independently enumerated9-slot seed; attach profile and connection dependencies, rather than claiming seeding is unimplemented.', 'LocalServer.open target_before/auth_target_connection + Context._seed + auth.profile'),
 'auth_create': ('Alias the three individual create cost posts; charge each once and keep their managed bound unknown.', 'BootstrapRequests.create_all and three role-specific create posts'),
 'quota_read': ('Alias the20-command quota macro and its one unbound native connection; do not add a second20 to the root.', 'runtime_case_entry.quota_samples + case.quota_read'),
 'cli_isolation': ('Map each reached PendingPrefix slot to its4/8 isolation suffix and exact original CLI envelope, without charging observer groups twice.', 'runtime_prefix.PendingPrefix.run + cli_predispatch.pending/isolation receipts'),
 'core_recovery': ('Use the core recovery state expansion as the single owner of rollback/control restoration allowances.', 'runtime_recovery.finish + actual_join:exception and case.core recovery posts'),
 'fixture_tracking': ('Map actual tracking install/action/outcome/terminal operations to core events and scope proof; count optional tracking only when selected by actual source.', 'fixture_db_terminality.TrackedRuntime + fixture_producer_scope.Scope'),
 'fixture_closure': ('Alias the37-slot guarded physical program and its connection/ownership prerequisites; preserve unknown-commit physical-only branch.', 'runtime_registered_fixture_closeout.protocol_plan/_execute/run'),
 'auth_closure': ('Use implemented preseed/postbody parent adapters, derive managed DELETE bounds and join C proof; old not-implemented description is stale.', 'Context._finish + runtime_registered_cleanup.run + Engine'),
 'auth_stop': ('Alias exact-owned stop/lifetime observation and observer close; no zero from a successful Docker exit alone.', 'LocalServer.close + auth.auth_stop/auth.observer_close'),
 'case_finally': ('Join identity/scalar session close transaction states to already consumed rollback slots; preserve original and secondary errors on receipt failure.', 'runtime_case_entry.execute_registered finally + IdentitySession.close + ScalarSession.close'),
}


def locate(post):
    if post.startswith('root:'):
        alias, sources, reason = ROOT_MAP[post[5:]]
        return sources, reason, alias
    if post.startswith('actual_meter'):
        return ['admission_budget_current_release.py', 'runtime_budget.py'], 'meter', None
    if post.startswith('actual_join:native'):
        return ['admission_budget_release_joins.py', 'quota_candidate_v1/runtime_catalog.py', 'quota_candidate_v1/runtime_stream.py'], 'core_native', None
    if post.startswith('actual_join:exception'):
        return ['admission_budget_release_joins.py', 'admission_budget_recovery_program.py', 'quota_candidate_v1/runtime_recovery.py'], 'recovery', None
    if post.startswith('source_inventory'):
        return ['admission_budget_root_runtime.py'], 'inventory', None
    if 'platform.install' in post:
        return ['install_platform.py'], 'platform', None
    if 'bootstrap.clean47' in post:
        return ROOT_MAP['clean47'][1], 'bootstrap', None
    if 'bootstrap.failure_closeout' in post:
        return ['quota_candidate_v1/runtime_bootstrap_closeout.py', 'native_runtime.py'], 'native', None
    if 'quota_read' in post:
        return ROOT_MAP['quota_read'][1], 'quota', None
    if 'derived_cost' in post:
        return ['quota_candidate_v1/runtime_registered_costs.py'], 'native', None
    if 'observer_' in post or 'engine.connect' in post or 'engine.close' in post or post.startswith('auth.scope:'):
        return ['quota_candidate_v1/runtime_registered_startup.py', 'quota_candidate_v1/runtime_registered_cleanup.py', 'native_runtime.py'], 'native', None
    if post.startswith('auth.profile:'):
        return ['admission_auth_runtime_profile.py', 'fixture_cleanup_runtime.py'], 'profile', None
    if post.startswith('auth.fixture_closeout:'):
        return ROOT_MAP['fixture_closure'][1], 'fixture', None
    if post.startswith('auth.parent_cleanup:') or post.startswith('auth.engine.'):
        return ROOT_MAP['auth_closure'][1], 'parent', None
    if post.startswith('auth.'):
        return ['quota_candidate_v1/runtime_registered_bootstrap.py', 'quota_candidate_v1/runtime_registered_startup.py', 'quota_candidate_v1/runtime_registered_costs.py'], 'managed', None
    if 'hosted_projection' in post:
        return ['quota_candidate_v1/runtime_case_entry.py', 'admission_budget_root_runtime.py'], 'scope', None
    if 'recovery_state' in post or post.startswith('case.core:'):
        return ['quota_candidate_v1/runtime_case_entry.py', 'quota_candidate_v1/runtime_parent_workflow.py', 'quota_candidate_v1/runtime_recovery.py'], 'recovery', None
    if post.startswith('case.auth.context:'):
        return ['quota_candidate_v1/runtime_registered_bootstrap.py', 'admission_budget_root_runtime.py'], 'context', None
    raise ValueError('post_unmapped:' + post)


def compile_cases(report):
    events = report['core_events']
    ids = [e['event_id'] for e in events]
    require(len(set(ids)) == len(ids), 'duplicate_core_event')
    ledger = PrefixLedger(events)
    prefixes = [{'events_reached': 0, 'declared_charged': 0, 'refund': 0}]
    for event in events:
        row = ledger.advance(event['event_id'])
        prefixes.append({'events_reached': row['events_reached'], 'declared_charged': row['declared_charged'], 'refund': 0})
    require(ledger.charged == report['core_normal_capacity'], 'precharge_total_changed')
    cases = {'normal': {'core_prefix_length': len(events), 'core_declared_charged': ledger.charged,
                       'suffix': 'normal_context_closeout', 'boundary': 'terminal'}}
    for name, case in report['core_fault_cases'].items():
        if 'before_event' in case:
            target, edge = case['before_event'], 'before'
        else:
            target, edge = case.get('after_event', case.get('case_event_id')), 'after'
        require(target in ids, 'fault_selector_not_in_program:' + name)
        index = ids.index(target) + int(edge == 'after')
        cases[name] = {'core_prefix_length': index,
            'core_declared_charged': prefixes[index]['declared_charged'],
            'boundary': dict(event_id=target, edge=edge, selector=case['selector']),
            'suffix': 'quota_or_prepare_or_core', 'hook_sql_commands': case['hook_sql_commands'],
            'timeout_replaces_existing_dispatch': case.get('replacement_not_additional', False)}
    for name, case in report['bootstrap_fault_cases'].items():
        closeout = case['closeout']
        cases[name] = {'core_prefix_length': 0, 'core_declared_charged': 0,
            'boundary': case['selector'], 'suffix': 'bootstrap_selected_pre_or_post',
            'closeout_direct_sql_reserved': closeout['reserved_sql_commands'],
            'closeout_docker_inventory_calls': closeout['docker_inventory_calls'],
            'fresh_native_connection_upper_bound': None, 'Auth_state': 'not_started'}
    require(len(cases) == 15, 'normal_plus_all14_required')
    for case in cases.values():
        case.update(total_local_ci_upper_bound=None, total_hosted_equivalent_upper_bound=None,
            root_prefix=['case.platform.install', 'case.bootstrap.clean47'],
            local_setup_hosted_projection='NOT_APPLICABLE', refund=0,
            actual_execution_evidence=False, bound_complete=False, admitted=False)
    return {'cases': cases, 'prefixes': prefixes,
        'core_events': [{k: e[k] for k in ('event_id', 'stage', 'charge_group', 'cost', 'capacity_use', 'phase', 'outcomes') if k in e}
                        for e in events],
        'model_reserves': report['core']['dag']['meter_requirements'],
        'reserve_scope': 'retained core predicates only; NOT full recovery bound',
        'normal_root_order': report['actual_source_program']['root_order'],
        'context_normal': report['actual_source_program']['context_normal'],
        'conditional_fault_suffixes': report['actual_source_program']['fault_suffixes']}


def reserve_gate(charged, remaining_upper_bound, *, limit=LIMIT):
    """A diagnostic predicate, not an authorization or dispatch function."""
    require(type(charged) is int and charged >= 0 and limit == LIMIT, 'gate_contract')
    if remaining_upper_bound is None:
        return {'decision': 'DENY', 'reason': 'remaining_reserve_unknown', 'required': None, 'limit': limit}
    require(type(remaining_upper_bound) is int and remaining_upper_bound >= 0, 'reserve_not_numeric')
    needed = charged + remaining_upper_bound
    return {'decision': 'DENY' if needed > limit else 'ARITHMETIC_ONLY',
            'reason': 'cap_exceeded' if needed > limit else 'other_source_and_runtime_gates_still_required',
            'required': needed, 'limit': limit}


def case_gates(program):
    result = {}
    for name, case in program['cases'].items():
        # Totals do not contain the still-unknown remaining suffix: neither
        # observations nor the declared historical reserve can supply it.
        result[name] = {'core': reserve_gate(case['core_declared_charged'], None),
            'local_ci_bound_complete': False, 'hosted_scope_complete': False,
            'remaining_full_suffix_upper_bound': None, 'decision': 'DENY'}
    return result


def platform_pin_gate(checkpoint):
    tree = ast.parse(checkpoint.source('install_platform.py'))
    value = next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'PINS' for t in n.targets))
    def literal(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name) and node.id == 'PREFIX':
            return PREFIX
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return literal(node.left) + literal(node.right)
        if isinstance(node, ast.Dict):
            return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
        raise ValueError('platform_pin_expression')
    rows = []
    for path, expected in literal(value).items():
        raw = checkpoint.raw[path]
        rows.append({'path': path, 'actual_raw_sha256': sha(raw), 'expected_lf_sha256': expected,
                     'matches_original_runtime_pin': sha(raw.replace(b'\r\n', b'\n')) == expected})
    return {'rows': rows, 'runtime_source_program_accepts': all(r['matches_original_runtime_pin'] for r in rows),
        'unreviewed_repin_performed': False,
        'meaning': 'Declarative outer operation bound does not establish current Gate.install reachability'}


def compile_checkpoint(root):
    checkpoint = Checkpoint(root)
    report = checkpoint.report
    platform = probes.platform(checkpoint.source('install_platform.py'))
    platform['runtime_pin_gate'] = platform_pin_gate(checkpoint)
    seed = probes.seed(checkpoint.source('quota_candidate_v1/runtime_registered_bootstrap.py'))
    guards = probes.dispatch_guards(checkpoint.source('admission_auth_runtime_profile.py'),
        checkpoint.source('quota_candidate_v1/runtime_registered_fixture_closeout.py'),
        checkpoint.source('fixture_cleanup_runtime.py'), checkpoint.source('fixture_producer_scope.py'),
        checkpoint.source('fixture_cleanup_runtime_sql.py'))
    native = native_cost_audit.build(checkpoint)
    recovery = report['core']['dag']['actual_join_proofs']['proofs']['exception']['workflow_finally']
    for name, digest in recovery['source_hashes'].items():
        actual = name if name == 'control_recovery.py' else 'quota_candidate_v1/' + name
        require(sha(checkpoint.source(actual)) == digest, 'recovery_original_source_changed')
    recover = {k: recovery[k] for k in ('format', 'source_hashes', 'maxima', 'base_states', 'traces',
        'unique_shapes', 'rollback_slots', 'compare_restore_slots', 'unresolved', 'covered_by')}
    recover.update(reused_verified_original_enumeration=True, additional_parent_charge=False,
                   actual_execution_evidence=False, full_sql_upper_bound=None)
    rows = []
    posts = sorted(report['missing_costs'], key=lambda p: (p != 'case.platform.install:platform_startup_implicit_SQL_and_process_inventory', p))
    for index, post in enumerate(posts, 1):
        names, reason, alias = locate(post)
        if post.startswith('root:'):
            action, evidence = ROOT_NEXT[post[5:]]
            work_kind = 'alias_join'
        else:
            require(post in NEXT, 'post_next_action_missing:' + post)
            action, evidence, work_kind = NEXT[post]
        rows.append({'ordinal': index, 'id': post,
            'classification': 'bounded' if reason == 'meter' else 'unknown',
            'classification_scope': 'partial core meter cap conflict only' if reason == 'meter' else 'full named cost post',
            'cost_closed': False, 'upper_bound': None, 'observed_commands': None,
            'reason': REASONS[reason], 'source_refs': checkpoint.refs(names),
            'smallest_next_action': action, 'missing_evidence_source': evidence,
            'work_kind': work_kind,
            'alias_of': alias, 'additive_charge': False if alias else None,
            'bounded_subprogram': {'platform': 'platform', 'seed': 'seed', 'profile': 'guards.auth_profile',
                'fixture': 'guards.fixture_closeout', 'recovery': 'recovery'}.get(reason),
            'domain': 'LOCAL_CI' if reason in ('platform', 'bootstrap', 'seed', 'profile', 'fixture', 'parent', 'context') else 'CALLER_SCOPE_REQUIRED',
            'hosted_projection': 'NOT_APPLICABLE' if reason in ('platform', 'bootstrap', 'seed', 'profile') else 'UNPROVEN'})
        native_routes = [r for r in native['routes'] if post.split(':', 1)[0] == r['operation']]
        if native_routes:
            rows[-1]['native_precondition_audit'] = native_routes[0]
            rows[-1]['missing_evidence_source'] += '; native audit specifies exact uncovered preconditions, not lack of measurement'
        if reason == 'platform':
            rows[-1]['runtime_pin_gate'] = platform['runtime_pin_gate']
            rows[-1]['smallest_next_action'] = 'First review existing admission_ci.py and hook.cjs delta against install_platform.PINS; current source_program refuses both. ' + rows[-1]['smallest_next_action']
            rows[-1]['pin_delta_provenance'] = {
                'source': 'Main read-only Git review supplied in this task; not independently queried',
                'admission_ci.py': {'commit': '235b74e', 'delta': 'LOCAL_SOURCES adds bootstrap_prefix/prefix_originals/test_source_bytes/byte_pairs'},
                'cli_predispatch/hook.cjs': {'commit': '56f61ad', 'delta': 'bounded ci_prefix: exact UUID, canonical1..44, local-bootstrap-only, AST+16, frame cap, SQL bytes<=131072, history binding'},
                'smallest_fix': 'review/rebind exactly the two existing pins; run platform source-pin and canonical/prefix boundary tests before platform dispatch',
                'pin_changed_by_this_delivery': False}
    program = compile_cases(report)
    program['case_gates'] = case_gates(program)
    coverage = {'format': 'source-bound-47-cost-posts-v1', 'status': 'NO_GO', 'READY': False,
        'compiler_source_hashes': {name: sha((HERE/name).read_bytes()) for name in
            ('cost_post_closure.py','source_cost_probes.py','native_cost_audit.py','sources.json')},
        'source_checkpoint_commit': checkpoint.manifest['reported_main_commit'], 'remote_queried': False,
        'original_report': checkpoint.manifest['report'], 'original_full_register_sha256': report['full_register_sha256'],
        'post_count': len(rows), 'closed_full_cost_posts': sum(r['cost_closed'] for r in rows),
        'bounded_explicit_subprograms': ['platform.outer', 'seed', 'profile.guard', 'fixture.guard', 'recovery.standalone'],
        'rows': rows, 'source_hashes': checkpoint.manifest['sources'], 'hosted_limit': LIMIT,
        'historical_reference': {'normal': 2338, 'closing': 731, 'read_only': True},
        'retained_partial_core': {'normal_declared_capacity': report['core_normal_capacity'],
            'meter_required_limit': report['core_meter_required_limit'], 'first_denied': report['core']['dag']['meter_requirements']['first_denied']},
        'actual_sql_executed': 0, 'bound_complete': False, 'minimal_cap': None,
        'total_local_ci_upper_bound': None, 'total_hosted_equivalent_upper_bound': None,
        'observations_promoted_to_bounds': False, 'source_inventory_complete': False,
        'component_43196418228': {'source': 'Main report', 'independently_read': False,
            'phase': 'ImportError before DB/Auth counters', 'numeric_evidence_accepted': False},
        'wal': {'probe_executed': False, 'new_explicit_diagnostic_proposal': 5,
            'source_refs': checkpoint.refs(['wal_plan/plan_only.py','wal_plan/HANDOFF.md',
                'offline-workpackage-20261111/wal-intervals.json']),
            'implicit_connection_bound': None, 'statement_timeout_ms': 5000,
            'representative_fixture_proven': False, 'full_wal_coverage': False,
            'old_incomplete_intervals_retained': True, 'new_probe_admitted': False,
            'missing': ['exact ACCESS/CATALOG actor and catalog equivalence',
                'driver and connection accounting', 'planning/utility/background/serialization WAL coverage'],
            'method': 'existing EXPLAIN ANALYZE WAL proposal; not fourth LSN method'}}
    checkpoint.recheck()
    parts = {'coverage': coverage, 'subprograms': {'platform': platform, 'seed': seed, 'guards': guards, 'recovery': recover,
                                                'conditional_native_contract': native},
             'program': program}
    parts['full_register_sha256'] = sha(canonical(parts))
    return parts


def export(root, destination):
    result = compile_checkpoint(root)
    directory = pathlib.Path(destination)
    directory.mkdir(parents=False, exist_ok=False)
    refs = {}
    for name in ('coverage', 'subprograms', 'program'):
        raw = canonical({'full_register_sha256': result['full_register_sha256'], name: result[name]}) + b'\n'
        require(len(raw) < 2_000_000, 'member_too_large')
        with (directory/(name+'.json')).open('xb') as stream:
            require(stream.write(raw) == len(raw), 'short_write')
            stream.flush()
            os.fsync(stream.fileno())
        refs[name] = {'bytes': len(raw), 'sha256': sha(raw)}
    receipt = dict(full_register_sha256=result['full_register_sha256'], files=refs,
                   status='NO_GO', actual_sql_executed=0, minimal_cap=None)
    with (directory/'receipt.json').open('xb') as stream:
        stream.write(canonical(receipt)+b'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.source_root, args.out), sort_keys=True))
