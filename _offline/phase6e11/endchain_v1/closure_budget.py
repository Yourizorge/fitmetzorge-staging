"""Role C offline audit. No DB, HTTP, CLI, hosted admission or file writes.

Run with python -B closure_budget.py; run tests with unittest. Counts from
capacity probes are reservations, never claims of emitted SQL. Existing source
is exercised with memory transports only. A fresh integral CI remains required.
"""
import ast
import collections
import hashlib
import io
import json
import pathlib
import subprocess
import types
from unittest.mock import Mock, patch

from closure import RUN_ID, PURPOSE
from cli_envelope import SLOTS, OBSERVERS
from complete_register import PHASES, AUTH_CALLS, BOOTSTRAP, safety_path, classify
from integral_ci import Composition
from metered_composition import MeteredComposition, capacity
from registered_runner import execute
from runtime_budget import RuntimeBudget, BudgetStop

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED_HEAD = '9715ac8600bad89ff813ad399e745360028ce48a'
CLOSING_PHASES = ('cleanup', 'final', 'closure')
CASES = ('normal', 'pre_migration', 'post_migration', 'auth', 'controller',
         'route_a', 'route_b', 'restore', 'lost_response', 'duplicate',
         'timeout', 'partial_cleanup')
SOURCE_FILES = (
    'authorization.json', 'runtime_budget.py', 'complete_register.py',
    'metered_composition.py', 'registered_runner.py', 'registered_lifecycle.py',
    'integral_ci.py', 'integral_failures.py', 'integral_auth.mjs',
    'auth_evidence.py', 'auth_protocol.py', 'cli_envelope.py', 'cli_meter.py',
    'closure.py', 'safety_auth.py', 'safety_auth_native.py',
    'safety_auth_budget.py', 'safety_auth.mjs', 'native_runtime.py',
    'scenario.py', 'sql_protocol.py', 'integral_stream.py',
    'hosted_gate.py', 'lifecycle_gates.py', 'cli_stat_reader.py',
    'closure_budget.py', 'test_closure_budget.py',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchor(name, needle):
    lines = (HERE / name).read_text().splitlines()
    if needle.startswith('function:'):
        symbol=needle.partition(':')[2]
        hits=[node.lineno for node in ast.parse('\n'.join(lines)).body
              if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==symbol]
    else:
        hits = [n for n, line in enumerate(lines, 1) if needle in line]
    if len(hits) != 1:
        raise ValueError('source_anchor_missing_or_ambiguous:' + name + ':' + needle)
    return {'file': str((HERE / name).relative_to(ROOT)).replace('\\', '/'),
            'line': hits[0], 'sha256': digest(HERE / name)}


def account(events):
    """Validate exact-once evidence; unknown outcomes retain their whole bound.

    One event is one disjoint native, Auth or CLI dispatch. Observers must have
    their own events. event_id must come from the parent dispatcher, not a child.
    `confirmed` means an independently observed command count, not HTTP success.
    This validator cannot itself prove that a producer omitted no dispatch.
    """
    seen = set()
    phases = collections.Counter()
    actual = collections.Counter()
    reserved = collections.Counter()
    unresolved = []
    for event in events:
        key = event.get('event_id')
        phase = event.get('phase')
        kind = event.get('kind')
        bound = event.get('reserved_commands')
        observed = event.get('observed_commands')
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError('missing_or_duplicate_event')
        seen.add(key)
        if phase not in (*PHASES, 'safety', 'ci_bootstrap'):
            raise ValueError('unattributed_phase')
        if kind not in ('native', 'managed_auth', 'cli'):
            raise ValueError('unattributed_kind')
        if type(bound) is not int or bound < 1:
            raise ValueError('invalid_reservation')
        if observed is not None and (type(observed) is not int or observed < 0):
            raise ValueError('invalid_observation')
        if observed is not None and observed > bound:
            raise ValueError('observed_over_reservation')
        if type(event.get('confirmed')) is not bool:
            raise ValueError('missing_confirmation')
        if event['confirmed'] and observed is None:
            raise ValueError('confirmation_without_count')
        if event['confirmed'] is not True or observed is None:
            unresolved.append(key)
        if phase == 'ci_bootstrap':
            continue
        phases[phase] += bound
        reserved[kind] += bound
        if event['confirmed'] and observed is not None:
            actual[kind] += observed
    total = sum(phases.values())
    if total > 2349:
        raise ValueError('authorized_ceiling')
    return {'reserved_commands': total, 'phase_reservations': dict(phases),
            'reservations_by_kind': dict(reserved),
            'confirmed_observed_by_kind': dict(actual),
            'all_emitted_counts_known': not unresolved,
            'unresolved_event_ids': unresolved, 'hosted_admitted': False}


def meter():
    return RuntimeBudget(capacity(), run_id=RUN_ID, purpose=PURPOSE, clock=lambda: 0)


def capacity_probe(case):
    """Exercise real meter branches with capacity units, without emitting SQL."""
    if case not in CASES:
        raise ValueError('unknown_failure_case')
    m = meter()
    phases = capacity()['phase_budgets']
    if case == 'normal':
        for phase in PHASES:
            ticket = m.charge(phase, phases[phase], action='capacity_' + phase,
                              mutation=True)
            m.confirm(ticket)
        return {'case': case, 'reserved_used': m.used, 'emitted_sql': 0,
                'scope': 'aggregate meter only; no lifecycle or database PASS',
                'receipt_complete': m.close()['complete'], 'hosted_admitted': False}
    targets = {'pre_migration': 'preflight', 'post_migration': 'migration',
               'auth': 'auth', 'controller': 'controller', 'route_a': 'route_a',
               'route_b': 'route_b', 'restore': 'restore',
               'lost_response': 'route_a', 'duplicate': 'route_a',
               'timeout': 'route_b', 'partial_cleanup': 'cleanup'}
    target = targets[case]
    # This order intentionally represents capacity only, not actual run order.
    for phase in PHASES:
        state = {}
        if phase == 'guard':
            state.update(guard=True, observer=True)
        if phase == 'setup':
            state['controls'] = True
        if phase == 'auth':
            state['auth_maybe_live'] = True
        if phase == 'controller':
            state['claimed'] = True
        amount = 1 if phase == target else phases[phase]
        ticket = m.charge(phase, amount, action='capacity_' + phase,
                          mutation=True, state_after=state)
        if phase != target or case not in ('lost_response', 'timeout', 'partial_cleanup'):
            m.confirm(ticket)
        if phase == target:
            break
    before = m.used
    reserve = m._reserve(m.phases, m.state)
    m.stop(case)
    denied = False
    try:
        m.charge(target, 1, action='dependent_or_repeated_action', mutation=True)
    except BudgetStop:
        denied = True
    # Execute each allowed budget ticket once; these are NOT cleanup SQL calls.
    suffix = safety_path(**m.state)
    for item in suffix:
        ticket = m.safety(item['action'], item['sql'], kind=item['kind'])
        m.confirm_safety(ticket)
    return {'case': case, 'scope': 'real meter; simulated safety confirmations',
            'reserved_before_stop': before, 'reserve_at_stop': reserve,
            'safety_reserved': m.used - before, 'reserved_used': m.used,
            'dependent_action_denied': denied, 'emitted_sql': 0,
            'database_cleanup_proven': False, 'hosted_admitted': False}


def protocol_probe(case):
    """Exercise actual executor classification; transport is deliberately absent."""
    c = MeteredComposition()
    c.meter = meter()
    routes = {route: next(i for i, row in enumerate(c.scenario) if row['route'] == route)
              for route in ('A', 'B')}
    restore = next(i for i, row in enumerate(c.scenario)
                   if 'restore' in row['request']['action'])
    if case == 'controller':
        c.action = {'kind': 'lifecycle', 'operation': 'install'}
        phase = 'evidence_query'
    else:
        step = {'route_a': routes['A'], 'route_b': routes['B'],
                'restore': restore, 'partial_cleanup': 45}[case]
        c.action = {'kind': 'workflow', 'step': step}
        phase = 'call'
    c.before_sql(phase, 'BEGIN; SELECT 1; ROLLBACK')
    c.after_sql(phase, 'BEGIN; SELECT 1; ROLLBACK')
    return {'case': case, 'phase_bookings': dict(c.meter.phases),
            'booked_protocol_statements': len(c.commands), 'emitted_sql': 0}


def workflow_precharge_probe():
    c = MeteredComposition()
    c.meter = meter()
    before = c.meter._reserve(c.meter.phases, c.meter.state)
    with patch.object(Composition, 'workflow', side_effect=RuntimeError('offline_child_abort')):
        try:
            c.workflow(None, None, None, None, None)
        except RuntimeError as error:
            if str(error) != 'offline_child_abort':
                raise
    return {'reserved_cleanup_before': before,
            'reserved_cleanup_after': c.meter._reserve(c.meter.phases, c.meter.state),
            'precharged_managed_capacity': c.meter.used,
            'precharged_cleanup_auth': c.meter.phases['cleanup'],
            'unconfirmed_managed_tickets': len(c.meter.managed_pending),
            'emitted_sql': 0, 'scope': 'actual workflow wrapper; interrupted memory delegate',
            'note': '130 cleanup slots are prepaid, not refunded or observed SQL; total bound retains them.'}


def worker_abort_probe():
    """Run the actual parent finally block after a simulated child timeout."""
    c = MeteredComposition()
    c.meter = meter()
    c.auth_before('a_member', 'issue')
    events = []
    saved = {}
    worker = Mock(stdin=io.StringIO(), stdout=io.StringIO(''), returncode=None)
    worker.wait.side_effect = subprocess.TimeoutExpired('offline_worker', 5)
    worker.poll.side_effect = lambda: worker.returncode
    worker.kill.side_effect = lambda: (events.append('kill'), setattr(worker, 'returncode', -9))
    worker.communicate.side_effect = lambda **kw: events.append('joined')
    def remove_owned_objects():
        events.append('remove_owned_objects')
        lifecycle.removed=True
    lifecycle = types.SimpleNamespace(removed=False, dispatch=Mock(), own_worker=Mock(),
        parent_auth_cleanup=Mock(side_effect=lambda **kw: events.append('parent_auth')),
        close_temporary=Mock(side_effect=remove_owned_objects))
    config = {'mode': 'registered_synthetic', 'environment': 'disposable_ci',
              'identityBinding': {'preexisting': True}, 'admin': None, 'anon': None}
    with patch('registered_runner.subprocess.Popen', return_value=worker), \
         patch('registered_runner.threading.Timer', return_value=Mock()):
        try:
            execute(types.SimpleNamespace(save=lambda n, v: saved.update({n: v})),
                    c, lifecycle, config)
        except subprocess.TimeoutExpired:
            pass
        else:
            raise AssertionError('timeout_not_propagated')
    return {'scope': 'actual parent runner with in-memory worker and lifecycle',
            'events': events, 'auth_maybe_live': c.meter.state['auth_maybe_live'],
            'parent_auth_suffix_calls': lifecycle.parent_auth_cleanup.call_count,
            'parent_received_terminated': lifecycle.parent_auth_cleanup.call_args.kwargs['worker_terminated'],
            'owned_objects_removed': lifecycle.removed,
            'reserved_used': c.meter.used, 'emitted_sql': 0,
            'worker_complete': saved['registered-worker-terminal.json']['complete']}


def control_loss_probe(lost_enable):
    """Execute extracted, unchanged control-enable/restore AST in memory.

    This specifically tests lost replies after the server-side mutation. Query
    results are synthetic; no driver, meter, network or database is invoked.
    """
    if lost_enable not in (1, 2):
        raise ValueError('control_loss_position')
    tree = ast.parse((HERE / 'integral_ci.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Composition')
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'workflow')
    owner = next(n for n in fn.body if isinstance(n, ast.Try) and n.finalbody)
    first = next(i for i, n in enumerate(owner.body)
                 if isinstance(n, ast.ImportFrom) and n.module=='control_recovery')
    last = next(i for i,n in enumerate(owner.body)
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='times' for t in n.targets))
    setup = owner.body[first:last]
    recovery = next(n for n in owner.finalbody if isinstance(n, ast.If)
                    and ast.unparse(n.test) == 'enable_attempted and enabled is not None and (restored != controls)')
    controls = {'config': {'id': True, 'enabled': False, 'proof_hash': None},
                'request': {'id': True, 'enabled': False, 'expires_at': None}}
    state = json.loads(json.dumps(controls))
    calls = []
    saved = {}
    def query(channel, phase, text, values=()):
        calls.append(phase)
        if phase == 'control_enable':
            index = calls.count(phase)
            if index == 1:
                state['config'].update(enabled=True, proof_hash=hashlib.sha256(values[0].encode()).hexdigest())
            else:
                state['request'].update(enabled=True, expires_at=values[0])
            if index == lost_enable:
                raise RuntimeError('offline_lost_enable_response')
            return [{'id': True}]
        if phase == 'safety_control_restore':
            name = 'request' if 'request_private' in text else 'config'
            field = 'expires_at' if name == 'request' else 'proof_hash'
            if values[0] is not None and values[0] == state[name][field]:
                state[name].update(enabled=False, **{field: None})
            return []
        return [{'value': json.loads(json.dumps(state)),'expires_at':'2026-11-02T12:03:00+00:00'}]
    namespace = {'query': query, 'raw_query': query, 'enabled': None,
                 'restored': None, 'controls': controls, 'hashlib': hashlib,
                 'json': json, 'control_sql': 'synthetic_metadata',
                 'enable_attempted':False,'run_id':'69000000-0000-4000-8000-000000000099',
                 'gate': types.SimpleNamespace(save=lambda n, v: saved.update({n: v}))}
    extracted = ast.Module(body=[ast.Try(body=setup, handlers=[], orelse=[],
                                        finalbody=[recovery])], type_ignores=[])
    try:
        exec(compile(ast.fix_missing_locations(extracted), '<offline-control-source>', 'exec'), namespace)
    except RuntimeError as error:
        if str(error) != 'offline_lost_enable_response':
            raise
    return {'lost_enable': lost_enable, 'scope': 'actual control AST; memory query results',
            'calls': calls, 'config_still_enabled': state['config']['enabled'],
            'request_still_enabled': state['request']['enabled'], 'emitted_sql': 0}


def preflight_failure_probe(rollback_fails=False):
    from lifecycle_gates import preflight
    calls = []
    saved = {}
    connection = Mock()
    def query(sql):
        calls.append(sql)
        if sql == 'ROLLBACK' and rollback_fails:
            raise RuntimeError('offline_rollback_failure')
        # Fail the real identity validation after BEGIN and GUARD.
        return types.SimpleNamespace(description=True, fetchall=lambda: [{'ro': 'off'}])
    connection.execute.side_effect = query
    runtime = types.SimpleNamespace(connect=lambda: connection, environment='disposable_ci')
    c = MeteredComposition(runtime=runtime)
    runtime = c.native_runtime(None)
    try:
        initial = preflight(runtime, lambda n, v: saved.update({n: v}))
        c.admit_preflight(initial)
    except (ValueError, RuntimeError):
        c.abort('offline_preflight_failure')
    else:
        raise AssertionError('preflight_fault_not_observed')
    return {'scope': 'actual preflight function and call order; memory driver',
            'memory_driver_dispatches': len(calls), 'runtime_booked': c.meter.used,
            'connection_closed': connection.close.called,
            'receipt_saved': bool(saved), 'rollback_failure': rollback_fails,
            'phase_bookings': dict(c.meter.phases), 'safety_bookings': dict(c.meter.safety_spent),
            'receipt_complete': saved.get('integral-preflight.json', {}).get('complete'),
            'emitted_sql': 0}


def historical_stop():
    folder = HERE / 'receipts/ci-40354914899-numeric-stop'
    path = folder / 'registered-incomplete-protocol-trace.json'
    value = json.loads(path.read_text())
    trace = value['commands']
    c = MeteredComposition()
    classified = collections.Counter(classify(row, c.scenario) for row in trace)
    return {'receipt_sha256': digest(path), 'trace_entries': len(trace),
            'classified_trace': dict(classified),
            'runtime_booked': value['runtime_meter']['used'],
            'runtime_phases': value['runtime_meter']['phases'],
            'trace_confirmed': sum(row['confirmed'] is True for row in trace),
            'full_chain_complete': value['complete'],
            'scope': 'historical receipt only; no new execution or current CI claim'}


def findings():
    rows = [
        ('C01', 'registered_lifecycle.py', 'def parent_auth_cleanup(self,*,worker_terminated):',
         'Parent requires worker termination and identity-lock closure before one-shot Auth cleanup. Persisted parent evidence permits exact owned guard/audit removal even when Auth is unknown; removal identity checks remain mandatory. Offline sequencing regression passes; no real endchain failure-matrix claim.',
         'Validate the corrected parent path in the source-bound real failure matrix. Unknown mid-Auth outcomes remain C03, not proven revocation.'),
        ('C02', 'integral_ci.py', 'if enable_attempted and enabled is not None and restored!=controls:',
         'Main now records control intents before mutation and uses control_recovery. Both current-source lost-enable-response AST regressions restore the in-memory controls.',
         'Keep the source-bound real-stack control response-loss cases as a diagnostic gate; offline AST PASS is not hosted evidence.'),
        ('C03', 'safety_auth.py', 'self.mint_terminal=(set(e.contracts)',
         'Parent cleanup observes incomplete mint outcomes without session deletion or zero claims. Exact owned guard/audit removal is independent of Auth PASS after the child barrier and persisted parent evidence. Mid-Auth revocation remains unproven.',
         'Add a parent-owned terminal mint barrier and exact issued-session manifest covering each attempted issue/verify/refresh. Use its evidence to revoke only this run identities/sessions even after an incomplete prefix; retain NO_GO when outcome is unknown. Recompile within the existing 60-command Auth safety allowance; do not raise it.'),
        ('C04', 'integral_failures.py', 'function:run',
         'The failure-matrix implementation and diagnostic planner are evolving under D. Their presence alone does not prove a fresh real-stack PASS for every required failure path.',
         'Add fresh isolated source-bound CI cases for pre/postmigration, partial Auth, controller, A, B, restore, lost response, duplicate dispatch, hard timeout and partial cleanup. Assert actual protocol/Auth/CLI counts, terminal controls, Auth zero, fixture/delete evidence and retained incomplete pairs per case.'),
        ('C05', 'cli_envelope.py', "elif receipt.get('environment')=='staging':",
         'Hosted CLI receipt deliberately accepts unknown session command counts; whole-database unattributed calls do not meet the new exact allocation requirement.',
         'Before admission, require source-bound exact isolated CLI protocol evidence and a proven hosted invocation envelope, or replace the opaque invocation with an approved exact metered adapter. Keep 64/28/28 as reserved bounds, and eight observers per slot separate. Never label 120 slots as emitted SQL; unresolved attribution blocks admission.'),
        ('C06', 'complete_register.py', "'stop_path':'Rollback once, preserve incomplete",
         'Current emergency contract preserves partial fixtures; it does not implement owner-requested complete synthetic cleanup on every stop.',
         'Add an exact ownership journal and separately measured delete/absence suffix for partially executed fixtures, preserving historical proof. Register every command before first mutation and execute from parent after child termination. Recalculate all prefixes under 2349, retaining initial cleanup/final/closure 731; no blind delete or migration history repair.'),
        ('C07', 'metered_composition.py', "tickets=[self.meter.charge('setup',5",
         'All 360 workflow Auth slots are prepaid, including 130 cleanup slots. Register places Auth slots before individual workflow steps; failed wrapper has no per-dispatch observation.',
         'Align register and executor ordering explicitly. Keep prepaid capacity separate from emitted/confirmed commands with parent dispatch IDs and unknown outcomes. After worker failure retain the entire bound and a parent-owned remaining cleanup schedule; validate every actual prefix and never refund an unknown call.'),
        ('C08', 'runtime_budget.py', "if phase not in self.limits or type(count)",
         'Reviewer F correction: repeated action labels alone are not a demonstrated bug. Each charge creates its own event; repeated confirmation of the same ticket is rejected.',
         'Do not count the former label-repetition characterization as a defect or acceptance proof. Retain independent per-dispatch accounting requirements under the full-chain evidence gates.'),
        ('C09', 'authorization.json', '"purpose":',
         'Active run authorization is still the 20261018 binding; latest instruction requests a fresh unique run.',
         'Main must create the new source-bound authorization and synchronize Python/Node/migration/controller quota references, hashes and CI artifacts without changing historical receipts or raising limits. This Role C audit grants no new run identity.'),
        ('C10', 'lifecycle_gates.py', "def preflight(runtime,save,prefix='',*,meter=None):",
         'Preflight now charges each statement before dispatch through the shared runtime meter; admission validates existing tickets without charging twice. Lost-BEGIN and rollback errors independently attempt rollback, close and incomplete receipt persistence.',
         'Include test_preflight_failure.py in Main CI source manifest and validate both real callers through RegisteredLifecycle. Normal preflight remains four commands; stopped rollback uses its existing safety allocation.'),
    ]
    statuses={'C01':'locally_corrected','C02':'locally_corrected',
              'C03':'open_unknown_revocation','C08':'not_demonstrated_bug','C10':'locally_corrected'}
    return [{'id': ident, 'severity': 'blocking' if ident not in ('C01','C02','C08','C10') else 'informational',
             'status': statuses.get(ident,'open'), 'source': anchor(file, needle),
             'finding': finding, 'patch_for_main': fix}
            for ident, file, needle, finding, fix in rows]


def report():
    sources = {name: digest(HERE / name) for name in SOURCE_FILES}
    # Include contract and scenario sources outside this directory explicitly.
    for rel in ('../auth_metadata_v1/auth_contract.py',
                '../readiness_v1/workflow_audit_v1/workflow_local.py',
                '../controller_guard_v1/auth_service.py'):
        sources[rel] = digest(HERE / rel)
    plan = capacity()
    reserve = sum(plan['phase_budgets'][p] for p in CLOSING_PHASES)
    if reserve != 731 or plan['normal_capacity'] != 2338 or plan['approved_limit'] != 2349:
        raise ValueError('authorized_capacity_changed')
    return {
        'status': 'NO_GO_FULL_ENDCHAIN_UNPROVEN', 'role': 'C',
        'expected_start_head_owner_confirmed': EXPECTED_HEAD,
        'source_binding': sources, 'source_binding_scope': 'audited files, not full release manifest',
        'scope': 'offline meter/executor probes and source audit; no real SQL/Auth/CLI',
        'hosted_admitted': False, 'hosted_attempt_consumed': False,
        'limits': {'normal_capacity': 2338, 'worst_case_claimed': 2349,
                   'worst_case_full_executor_proven': False, 'cleanup_final_closure_reserve': reserve,
                   'phase_capacities': plan['phase_budgets'], 'own_temp_writes': 0,
                   'read_wal_limit_changed': False, 'automatic_retries': 0},
        'accounting': {'auth_matrix_expected_capacity': 3 * sum(AUTH_CALLS.values()),
                       'workflow_auth_expected_capacity': 72 * 5,
                       'cli_unknown_reserved_capacity': sum(SLOTS.values()),
                       'cli_observers_planned': len(SLOTS) * OBSERVERS,
                       'warning': '594 Auth capacity and 144 CLI-plus-observer capacity are not new observed counts'},
        'failure_matrix': [capacity_probe(case) for case in CASES],
        'protocol_probes': [protocol_probe(case) for case in
                            ('controller', 'route_a', 'route_b', 'restore', 'partial_cleanup')],
        'workflow_precharge_probe': workflow_precharge_probe(),
        'worker_abort_probe': worker_abort_probe(), 'historical_stop': historical_stop(),
        'control_lost_response_probes': [control_loss_probe(1), control_loss_probe(2)],
        'preflight_failure_probes': [preflight_failure_probe(), preflight_failure_probe(True)],
        'current_findings': findings(),
        'blocking_findings': [row for row in findings() if row['severity']=='blocking'],
        'historical_observations': {'file':'closure_budget.json',
            'sha256':digest(HERE / 'closure_budget.json'), 'superseded_statuses_separate':True},
        'required_main_gates': ['fresh unique source/run binding',
            'one combined GitHub run requiring both endchain CI and app CI PASS on separate real stacks; no combined PASS currently claimed',
            'complete PG17 plus real Auth composed CI and all real failure paths',
            'exact per-dispatch protocol/Auth/CLI accounting without unknown outcomes',
            'parent-owned cleanup and Auth zero after every child termination',
            'all-prefix executable bound <=2349 and initial cleanup reserve 731',
            'independent complete WAL classification under unchanged limits',
            'independent reviewer acceptance'],
        'boundaries': {'database_changes': 0, 'hosted_calls': 0, 'jit_actions': 0,
            'git_commit_push_dispatch': 0, 'real_member_data_access': 0,
            'production_touched': False, 'runtime_assets_changed': False,
            'historical_evidence_changed': False, 'external_ai_calls': 0,
            'external_ai_cost_eur': 0, 'owner_phone_test': 'NO_GO'},
    }


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, sort_keys=True))
