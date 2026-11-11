"""One-shot faults at real executor boundaries; no SQL, Auth or proof simulation."""
import copy
import hashlib
import pathlib
import re
import uuid

from .compiler import canonical, require, sha

CASES = ('normal', 'pre_migration', 'post_migration', 'mid_auth', 'controller',
         'route_a', 'route_b', 'restore', 'lost_response', 'duplicate',
         'timeout', 'partial_fixture_cleanup', 'cleanup_failure', 'final_check_failure', 'closure_failure')
TIMEOUT_SQL = 'SELECT pg_sleep(6)'


class InjectedFault(RuntimeError):
    pass


def selectors(scenario):
    require(len(scenario) == 45 and [r['step'] for r in scenario] == list(range(45)), 'fault_scenario_shape')
    def first(predicate):
        hits = [r for r in scenario if predicate(r)]
        require(bool(hits), 'fault_source_selector_missing')
        return hits[0]['step']
    a = first(lambda r: r['step'] > 0 and r['route'] == 'A' and r['expected_outcome'] == 'committed')
    b = first(lambda r: r['route'] == 'B' and r['expected_outcome'] == 'committed')
    restore = first(lambda r: 'restore' in r['request']['action'] and r['expected_outcome'] == 'committed')
    replay = first(lambda r: r['expected_outcome'] == 'replayed')
    require(replay > 0 and scenario[replay]['request'] == scenario[replay-1]['request'],
            'fault_replay_not_same_payload')
    result = {
        'normal': {'stage': 'confirmed_closure'},
        'pre_migration': {'stage': 'before45', 'history_count': 44},
        'post_migration': {'stage': 'after45', 'history_count': 45},
        'mid_auth': {'stage': 'auth_confirmed', 'role': 'a_member', 'operation': 'refresh'},
        'controller': {'stage': 'controller_before', 'controller_step': 2, 'pair_phase': 'pair_validated'},
        'route_a': {'stage': 'native_after', 'channel': 'workflow', 'phase': 'commit', 'step': a},
        'route_b': {'stage': 'native_after', 'channel': 'workflow', 'phase': 'commit', 'step': b},
        'restore': {'stage': 'native_after', 'channel': 'workflow', 'phase': 'commit', 'step': restore},
        'lost_response': {'stage': 'native_after', 'channel': 'workflow', 'phase': 'commit', 'step': 0},
        'duplicate': {'stage': 'pair_confirmed', 'step': replay},
        'timeout': {'stage': 'native_timeout', 'channel': 'workflow', 'phase': 'call', 'step': 0},
        'partial_fixture_cleanup': {'stage': 'native_after', 'channel': 'workflow', 'phase': 'commit', 'step': 47},
        'cleanup_failure': {'stage': 'outer_before', 'phase': 'remove'},
        'final_check_failure': {'stage': 'outer_after', 'phase': 'gates_final_post_metadata'},
        'closure_failure': {'stage': 'outer_before', 'phase': 'final_closure'},
    }
    return result


def export_hooks(scenario):
    """Exact executor selectors for the budget owner, not a fabricated cost DAG."""
    root = pathlib.Path(__file__).parent
    source = '_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_faults.py'
    return {'format': 'quota-case-hooks-v1', 'source': source,
            'source_sha256': sha((root / 'runtime_faults.py').read_bytes()),
            'scenario_sha256': sha(canonical(scenario)), 'cases': selectors(scenario),
            'hook_sql_commands': 0, 'timeout_replaces_call_commands': 1,
            'timeout_sql_sha256': sha(TIMEOUT_SQL.encode()), 'timeout_limit_ms': 5000,
            'recovery_implementation': ['registered_runner.execute.finally',
                'RegisteredLifecycle.parent_auth_cleanup/close_temporary',
                'WorkflowBridge.workflow.finally', 'CaseBudget.safety'],
            'recovery_edges_complete': False, 'full_chain_admission': False}


class PhaseFaults:
    """Trusted private case owner. Never serializes SQL, parameters or row contents."""
    def __init__(self, case, binding, scenario, *, out, save):
        require(case in CASES, 'fault_case_unknown')
        from .compiler import binding as identity
        require(str(uuid.UUID(binding['run_id']))==binding['run_id']
            and uuid.UUID(binding['run_id']).version==4
            and binding['run_id'] not in (identity.OLD_RUN,identity.NEW_RUN)
            and binding.get('parent_id')==identity.NEW_RUN
            and binding.get('environment')=='disposable_ci'
            and binding.get('execution_admitted') is False and binding.get('hosted_permission') is False
            and re.fullmatch('[a-f0-9]{40}',binding['source_commit'])
            and re.fullmatch('[a-f0-9]{64}',binding['candidate_sha'])
            and re.fullmatch('[1-9][0-9]{0,18}',binding['ci_run']), 'fault_binding')
        self.case = case
        self.binding = copy.deepcopy(binding)
        self.selector = selectors(scenario)[case]
        self.out = pathlib.Path(out).resolve()
        self.save = save
        self.fired = None
        self.timeout_armed = False
        self.seen = 0
        self.abort = None

    def attach(self, composition):
        require(self.abort is None and composition.quota['binding'] == self.binding, 'fault_composition_binding')
        self.abort = composition.abort

    def _observe(self, stage, **values):
        self.seen += 1
        require(self.seen <= 16384, 'fault_hook_observation_bound')
        return {'stage': stage, **values}

    def _matches(self, event):
        return self.fired is None and self.case != 'normal' and all(event.get(k) == v for k, v in self.selector.items())

    def _fire(self, event, *, raise_error=True):
        require(self.fired is None and self.case != 'normal', 'fault_no_replay')
        code = 'case_injected_' + self.case
        error = InjectedFault(code)
        self.fired = {'case': self.case, 'run_id': self.binding['run_id'],
            'source_commit': self.binding['source_commit'], 'ci_run': self.binding['ci_run'],
            'candidate_sha': self.binding['candidate_sha'], 'original_error_code': code,
            'event': copy.deepcopy(event), 'observations_before_fault': self.seen,
            'automatic_retry': False, 'full_chain_admission': False}
        if self.abort is not None:
            self.abort(code)
        try:
            self.save('case-fault-boundary.json', self.fired)
        except Exception as secondary:
            error.add_note('case_fault_receipt_secondary:' + type(secondary).__name__)
            if not raise_error:
                raise error from secondary
        if raise_error:
            raise error

    def migration(self, snapshot, stage):
        require(set(snapshot) == {'stage', 'source_commit', 'ci_run', 'candidate_sha256',
            'history_count', 'evidence_refs', 'full_chain_admission', 'hosted_admission'}, 'fault_migration_shape')
        require(snapshot['stage'] == stage and snapshot['source_commit'] == self.binding['source_commit']
            and str(snapshot['ci_run']) == self.binding['ci_run']
            and snapshot['candidate_sha256'] == self.binding['candidate_sha']
            and snapshot['history_count'] == (44 if stage == 'before45' else 45)
            and snapshot['full_chain_admission'] is False and snapshot['hosted_admission'] is False,
            'fault_migration_binding')
        refs = snapshot['evidence_refs']
        expected = (['migration-boundary-pre.json'] if stage == 'before45' else
                    ['cli-predispatch-canonical-45.json', 'migration-boundary-post.json'])
        require([r['path'] for r in refs] == expected, 'fault_migration_evidence_names')
        for ref in refs:
            require(set(ref) == {'path', 'sha256', 'bytes'}, 'fault_migration_reference')
            path = self.out / ref['path']
            require(not path.is_symlink() and path.resolve().parent == self.out, 'fault_migration_path')
            raw = path.read_bytes()
            require(len(raw) == ref['bytes'] and len(raw) <= 2000000 and sha(raw) == ref['sha256'],
                    'fault_migration_evidence_hash')
        event = self._observe(stage, history_count=snapshot['history_count'],
                              evidence_refs=copy.deepcopy(refs), dispatch_confirmed=stage == 'after45')
        if self._matches(event): self._fire(event)

    def before45(self, snapshot): self.migration(snapshot, 'before45')
    def after45(self, snapshot): self.migration(snapshot, 'after45')

    def auth_confirmed(self, role, operation):
        event = self._observe('auth_confirmed', role=role, operation=operation, dispatch_confirmed=True)
        if self._matches(event): self._fire(event)

    def controller_before(self, args):
        # NativeStore.record: [run,step,phase,metadata]. Never retain metadata.
        if len(args) < 3 or args[0] != self.binding['run_id']: return
        event = self._observe('controller_before', controller_step=args[1], pair_phase=args[2],
                              dispatch_attempted=False)
        if self._matches(event): self._fire(event)

    def outer(self, side, phase, text):
        event = self._observe('outer_' + side, phase=phase, sql_sha256=sha(text.encode()),
                              dispatch_confirmed=side == 'after', dispatch_attempted=side == 'after')
        if self._matches(event): self._fire(event)

    def prepare_native(self, channel, phase, text, values, action):
        if self.case == 'timeout' and not self.timeout_armed and self.fired is None and \
                channel == 'workflow' and phase == 'call' and action == {'kind': 'workflow', 'step': 0}:
            self.timeout_armed = True
            # A real bounded driver cancellation inside the existing transaction.
            # It replaces this diagnostic call, never runs the product mutation too.
            return TIMEOUT_SQL, ()
        return text, values

    def native_after(self, channel, phase, text, action):
        event = self._observe('native_after', channel=channel, phase=phase,
            step=action.get('step') if action and action.get('kind') == 'workflow' else None,
            sql_sha256=sha(text.encode()), dispatch_confirmed=True)
        if self._matches(event): self._fire(event)

    def native_error(self, channel, phase, text, action, sqlstate):
        if self.case == 'timeout' and self.timeout_armed and self.fired is None:
            require(channel == 'workflow' and phase == 'call' and text == TIMEOUT_SQL
                    and sqlstate == '57014', 'fault_timeout_not_observed')
            event = self._observe('native_timeout', channel=channel, phase=phase, step=0,
                sql_sha256=sha(text.encode()), sqlstate=sqlstate, dispatch_attempted=True,
                dispatch_confirmed=False, statement_timeout_ms=5000)
            self._fire(event, raise_error=False)

    def pair_confirmed(self, event):
        observed = self._observe('pair_confirmed', step=event.get('step'),
            pair_sha256=sha(canonical(event)), dispatch_confirmed=True)
        if self._matches(observed): self._fire(observed)

    def receipt(self):
        return {'case': self.case, 'run_id': self.binding['run_id'], 'selected_hook': self.selector,
            'fault_observed': self.fired is not None, 'fault': copy.deepcopy(self.fired),
            'timeout_armed': self.timeout_armed, 'observed_hook_count': self.seen,
            'full_matrix_pass': False, 'full_chain_admission': False, 'hosted_admission': False}
