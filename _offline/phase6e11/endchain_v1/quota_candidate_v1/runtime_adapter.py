"""Opt-in disposable full-chain adapter. No provisioning, hosted access or dispatch."""
import collections
import copy
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time

import admission_budget
from complete_register import PHASES, scenario_source
from integral_ci import Composition
from metered_composition import MeteredComposition
from native_runtime import NativeRuntime
from runtime_budget import RuntimeBudget, BudgetStop
from registered_lifecycle import RegisteredLifecycle
from registered_runner import IdentitySession
from closure import BOOTSTRAP
from cli_envelope import charged, CHARGE
from .compiler import binding_for_case, validate_target, read_source, canonical, sha, require
from .runtime_parent_workflow import WorkflowBridge

HERE = pathlib.Path(__file__).resolve().parent
PREFIX = '_offline/phase6e11/endchain_v1/quota_candidate_v1/'
_KEY = object()
DAG_SOURCE = '_offline/phase6e11/endchain_v1/admission_budget_current_release.py'


class PreparedCase:
    """A local model-checked context, not a full-chain or hosted PASS receipt."""
    def __init__(self, key, value):
        require(key is _KEY, 'runtime_preflight_required')
        self.__json = canonical(value)
    def config(self):
        return json.loads(self.__json)


def source_inputs(root):
    from .compiler import source_files
    refs = json.loads((HERE / 'runtime_refs.json').read_text())
    names = set(refs['references']) | {PREFIX + n for n in refs['runtime_files']} | {DAG_SOURCE}
    return {**source_files(root), **{name: sha(read_source(root, name)) for name in sorted(names)}}


def verify_runtime_sources(root, manifest):
    refs = json.loads((HERE / 'runtime_refs.json').read_text())
    sources = manifest['sources']
    for name, expected in refs['references'].items():
        require(sources.get(name) == expected and sha(read_source(root, name)) == expected,
                'runtime_reference_changed')
    for name in refs['runtime_files']:
        expected = sha((HERE / name).read_bytes())
        require(sources.get(PREFIX + name) == expected
                and sha(read_source(root, PREFIX + name)) == expected, 'runtime_adapter_source')
    # Do not validate a candidate file and execute a different already-loaded module.
    modules = [sys.modules[name] for name in ('admission_budget', 'complete_register',
        'integral_ci', 'metered_composition', 'native_runtime', 'runtime_budget', 'closure', 'cli_envelope',
        'registered_lifecycle', 'registered_runner')]
    modules.extend((scenario_source, sys.modules['integral_ci']._scenario))
    for module in modules:
        name = '_offline/phase6e11/endchain_v1/' + pathlib.Path(module.__file__).name
        require(sha(pathlib.Path(module.__file__).read_bytes()) == sources.get(name),
                'runtime_loaded_module')


def validate_isolation(value, binding, prior_cases=()):
    """Validate Main's technical, measured stack inventory, not a caller PASS flag."""
    required = {'run_id', 'ci_run', 'source_commit', 'environment', 'pg_container',
                'auth_container', 'pg_system_identifier', 'database_oid', 'db_target_sha256',
                'auth_target_sha256', 'registry_empty', 'pg17', 'ssl', 'auth_database_bound',
                'reused', 'evidence_sha256', 'native_ssl', 'auth_ssl', 'auth_sslmode'}
    require(type(value) is dict and set(value) == required, 'runtime_isolation_shape')
    for key in ('run_id', 'ci_run', 'source_commit'):
        require(value[key] == binding[key], 'runtime_isolation_case')
    require(value['environment'] == 'disposable_ci' and value['reused'] is False
            and all(value[k] is True for k in ('registry_empty', 'pg17', 'ssl', 'auth_database_bound',
                                              'native_ssl', 'auth_ssl'))
            and value['auth_sslmode'] == 'verify-full',
            'runtime_isolation_evidence')
    import re
    for key in ('pg_container', 'auth_container', 'db_target_sha256', 'auth_target_sha256', 'evidence_sha256'):
        require(isinstance(value[key], str) and re.fullmatch('[a-f0-9]{64}', value[key]),
                'runtime_isolation_digest')
    require(value['pg_container'] != value['auth_container']
            and value['db_target_sha256'] == value['auth_target_sha256'], 'runtime_auth_database')
    require(isinstance(value['pg_system_identifier'], str)
            and re.fullmatch('[1-9][0-9]{0,19}', value['pg_system_identifier'])
            and type(value['database_oid']) is int and value['database_oid'] > 0,
            'runtime_database_identity')
    require(isinstance(prior_cases, (list, tuple)) and len(prior_cases) <= 14, 'runtime_prior_cases')
    for prior in prior_cases:
        require(prior['run_id'] != value['run_id'] and prior['pg_container'] != value['pg_container']
                and prior['auth_container'] != value['auth_container']
                and (prior['pg_system_identifier'], prior['database_oid']) !=
                    (value['pg_system_identifier'], value['database_oid']), 'runtime_database_reuse')
    return copy.deepcopy(value)


def compile_register(root, plan, sources):
    """Regenerate authoritative current source; historical arithmetic is not admission."""
    require(plan.get('format') == 'admission-current-dispatch-dag-v1', 'runtime_current_dag_required')
    require(DAG_SOURCE in sources and sha(read_source(root,DAG_SOURCE)) == sources[DAG_SOURCE],
            'runtime_current_compiler_source')
    import admission_budget_current_release as current
    require(sha(pathlib.Path(current.__file__).read_bytes()) == sources[DAG_SOURCE],
            'runtime_loaded_current_compiler')
    return current.compile_release(plan,sources,source_root=root,runtime_dir=HERE)


def prepare_case(root, manifest, run_id, *, plan_ref=None, current_plan=None,
                 current_plan_sha256=None, isolation, prior_cases=(),
                 environment, connection, ca_path, now):
    """No DB calls. Missing real source-bound full register is an explicit stop."""
    binding = binding_for_case(root, manifest, run_id, now=now)
    validate_target(root, manifest, environment=environment, connection=connection, ca_path=ca_path, now=now)
    verify_runtime_sources(root, manifest)
    verified_sources=dict(manifest['sources'])
    if current_plan is not None or current_plan_sha256 is not None:
        require(plan_ref is None and type(current_plan) is dict, 'runtime_plan_ambiguous')
        raw=canonical(current_plan)
        require(sha(raw)==current_plan_sha256, 'runtime_dag_changed')
        plan=json.loads(raw)
        for field in ('source_hashes','register_source_hashes'):
            require(type(plan.get(field)) is dict and plan[field], 'runtime_dag_sources_missing')
            for name,digest in plan[field].items():
                target=name if name in manifest['sources'] else '_offline/phase6e11/endchain_v1/'+name
                require(manifest['sources'].get(target)==digest and sha(read_source(root,target))==digest,
                        'runtime_dag_source_changed')
                require(name not in verified_sources or verified_sources[name]==digest,
                        'runtime_dag_source_alias_collision')
                verified_sources[name]=digest
        plan_ref=dict(path=None,sha256=current_plan_sha256)
    else:
        require(type(plan_ref) is dict and set(plan_ref) == {'path', 'sha256'}, 'runtime_full_register_missing')
        require(manifest['sources'].get(plan_ref['path']) == plan_ref['sha256'], 'runtime_register_unbound')
        raw = read_source(root, plan_ref['path'])
        require(sha(raw) == plan_ref['sha256'], 'runtime_register_changed')
        plan = json.loads(raw)
    model = compile_register(root, plan, verified_sources)
    if current_plan is not None:
        require(model.get('dag_sha256')==current_plan_sha256
                and model.get('plan_sha256')==plan.get('plan_sha256'), 'runtime_dag_compiler_binding')
    require(model.get('bound_complete') is True and model.get('fits') is True
            and type(model.get('minimal_cap')) is int and model['minimal_cap'] <= binding['cap'],
            'runtime_full_register_incomplete')
    registry = dict(format='fmz6e11-disposable-runtime-register-v1',
        run_id=binding['run_id'], purpose=binding['purpose'], binding_sha=binding['binding_sha'],
        source_commit=binding['source_commit'], candidate_sha=binding['candidate_sha'],
        plan_path=plan_ref['path'], plan_sha256=plan_ref['sha256'],
        semantic_plan_sha256=model.get('plan_sha256'), dag_sha256=model.get('dag_sha256'),
        approved_limit=binding['cap'], complete_register=True, fits=True,
        phase_budgets=model['phase_capacities'], normal_capacity=model['normal_capacity'],
        worst_including_safety=model['minimal_cap'], hosted_permission=False)
    release = model if model.get('format') == 'admission-actual-execution-release-v1' else None
    if release is not None:
        registry.update(release_format=release['format'], release_sha256=sha(canonical(release)))
    isolated = validate_isolation(isolation, binding, prior_cases)
    return PreparedCase(_KEY, dict(root=str(pathlib.Path(root).resolve()), manifest=copy.deepcopy(manifest),
        binding=binding, register=registry, isolation=isolated,
        current_dag=plan if current_plan is not None or release is not None else None,
        release_model=copy.deepcopy(release)))


class CaseBudget(RuntimeBudget):
    def __init__(self,prepared,*,clock=time.monotonic):
        require(isinstance(prepared, PreparedCase), 'runtime_preflight_required')
        context=prepared.config(); register=context['register']; binding=context['binding']
        run_id,purpose=binding['run_id'],binding['purpose']
        if register.get('run_id')!=run_id or register.get('purpose')!=purpose:
            raise BudgetStop('runtime_reserved_run_binding')
        if not register.get('complete_register') or register.get('approved_limit')!=binding['cap'] or not register.get('fits'):
            raise BudgetStop('runtime_register_admission')
        limits=register.get('phase_budgets',{})
        if set(limits)!=set(PHASES) or any(type(v) is not int or v<1 for v in limits.values()):
            raise BudgetStop('runtime_phase_budget')
        if sum(limits.values())!=register.get('normal_capacity') or register.get('worst_including_safety',99999)>binding['cap']:
            raise BudgetStop('runtime_complete_capacity')
        self.limit=binding['cap'];self.limits=dict(limits);self.clock=clock;self.started=clock()
        self.used=0;self.phases=collections.Counter();self.events=[];self.stopped=False;self.closed=False
        self.state={'guard':False,'observer':False,'controls':False,'claimed':False,'auth_maybe_live':False}
        self.state.update(guard_remove_attempted=False,observer_remove_attempted=False)
        self.safety_spent=collections.Counter();self.pending=None;self.stop_reason=None
        self.managed_pending={}
        self.safety_pending={};self.state_confirmations=[]
        self.setup_connection_owned=False

    def _reserve(self,phases,state):
        # The actual bridge opens a fourth native connection, absent from the old model.
        return super()._reserve(phases,state)+1

    def safety(self,action,count,*,kind='native'):
        if action!='rollback_setup':return super().safety(action,count,kind=kind)
        if self.closed or not self.stopped:raise BudgetStop('runtime_safety_state')
        elapsed=self.clock()-self.started
        if elapsed<0 or elapsed>=600:raise BudgetStop('runtime_safety_deadline')
        if (not self.setup_connection_owned or type(count) is not int or count!=1
                or kind!='native' or self.safety_spent[action]):
            raise BudgetStop('runtime_safety_action')
        if self.used+count>self.limit:raise BudgetStop('runtime_safety_ceiling')
        self.safety_spent[action]+=count;self.used+=count
        event=dict(number=len(self.events)+1,first_command=self.used,commands=1,
                   phase='safety',action=action,kind=kind,confirmed=False)
        self.events.append(event);self.safety_pending[event['number']]=event
        return event['number']

class CaseComposition(WorkflowBridge, MeteredComposition):
    runner = HERE / 'runtime_auth.mjs'
    def __init__(self,prepared,*,runtime,fault=None,phase_faults=None):
        require(isinstance(prepared, PreparedCase), 'runtime_preflight_required')
        require(isinstance(runtime, NativeRuntime) and runtime.environment=='disposable_ci', 'runtime_disposable_only')
        Composition.__init__(self,fault=fault,runtime=runtime)
        self.quota=prepared.config()
        self.runner=self.worker_path('runtime_auth.mjs')
        self.meter=CaseBudget(prepared)
        self.meter_stack=[];self.managed_auth_ticket=None;self.safety_label=None
        self.managed_auth_binding=None;self.auth_scope_run_id=None;self.auth_scope_ids=None
        self.auth_prefix_roles=set();self.auth_terminal_roles=set();self.auth_zero_proof=None
        self.safety_auth_started=False;self.safety_auth_tickets={};self.safety_auth_result=None
        self.auth_zero_scope=None
        self.preflight_admitted=False
        self.scenario=scenario_source.capture()['workflow_actions']
        self.phase_faults=phase_faults
        if phase_faults is not None:phase_faults.attach(self)

    def apply_migration(self, gate):
        raise BudgetStop('runtime_canonical_migration_reapply_forbidden')

    def worker_path(self,name):
        require(name in ('runtime_auth.mjs','runtime_integral_workflow.mjs'), 'runtime_worker_name')
        root=pathlib.Path(self.quota['root']).resolve(strict=True)
        relative=PREFIX+name
        require(sha(read_source(root,relative))==self.quota['manifest']['sources'].get(relative),
                'runtime_worker_source')
        return root/relative

    def preservation(self,gate,ids,label):
        owner=getattr(self,'case_preservation',None)
        require(owner is not None and owner.composition is self, 'runtime_case_preservation_required')
        return owner.run(gate,ids,label)

    def admit_preflight(self,value):
        from .runtime_history import MIGRATIONS
        from integral_stream import GUARD
        from sql_protocol import single
        history=getattr(self,'case_history',None)
        rows=value.get('commands',[])
        require(not self.preflight_admitted and history is not None and history.before is not None
            and value.get('migrations')==history.before and len(history.before)==47
            and value.get('complete') is True and value.get('metered_before_dispatch') is True
            and value.get('rollback_confirmed') is True and value.get('connection_closed') is True
            and len(rows)==4 and self.meter.phases['preflight']==4,
            'runtime_case_preflight')
        expected=[single(sql)['sha256'] for sql in
            ('BEGIN TRANSACTION READ ONLY',GUARD,MIGRATIONS,'ROLLBACK')]
        require([r.get('sql_sha256') for r in rows]==expected, 'runtime_case_preflight_sql')
        tickets=[r.get('meter_ticket') for r in rows]
        require(all(type(t) is int and 1<=t<=len(self.meter.events) for t in tickets)
            and len(set(tickets))==4,'runtime_case_preflight_ticket')
        for row,ticket in zip(rows,tickets):
            event=self.meter.events[ticket-1]
            require(row.get('confirmed') is True and row.get('dispatch_attempted') is True
                and row.get('meter_phase')=='preflight' and event['phase']=='preflight'
                and event['kind']=='native' and event['commands']==1 and event['confirmed'] is True
                and event['action']=='preflight_'+row['sql_sha256'], 'runtime_case_preflight_ticket')
        self.preflight_admitted=True

    def confirm_case_prefix(self,gate):
        require(self.preflight_admitted and not getattr(self,'case_prefix_ready',False)
            and not self.meter.stopped and not self.meter.closed and self.meter.pending is None
            and self.meter.phases['migration']==128 and len(gate.cli_protocol)==2
            and [r['slot'] for r in gate.cli_protocol]==['quota','pre_auth']
            and [charged(r) for r in gate.cli_protocol]==[72,36]
            and self.case_history.after is not None and len(self.case_history.after)==48
            and self.gate_baseline['migrations']==self.case_history.after,
            'runtime_case_prefix_incomplete')
        events=[e for e in self.meter.events if e['phase'] in ('preflight','migration')]
        require(events and all(e['confirmed'] is True for e in events), 'runtime_case_prefix_unconfirmed')
        self.case_prefix_ready=True

    def before_sql(self, phase, sql):
        faults=getattr(self,'phase_faults',None)
        effective='final_closure' if self.closing_receipt is not None else phase
        if faults is not None:faults.outer('before',effective,sql)
        return super().before_sql(phase,sql)

    def after_sql(self, phase, sql):
        value=super().after_sql(phase,sql)
        faults=getattr(self,'phase_faults',None)
        effective='final_closure' if self.closing_receipt is not None else phase
        if faults is not None:faults.outer('after',effective,sql)
        return value

    def evidence_query(self, request, sql):
        faults=getattr(self,'phase_faults',None)
        if faults is not None:faults.controller_before(request['args'])
        return super().evidence_query(request,sql)

    def worker_config(self, config):
        require(config.get('environment') == 'disposable_ci'
                and config.get('mode') == 'registered_synthetic', 'runtime_disposable_only')
        return {**config, 'quota': copy.deepcopy(self.quota)}

    def workflow(self, *args, **kwargs):
        # The versioned child path must not bypass the original 72-call precharge.
        tickets = [self.meter.charge('setup', 5, action='gotrue_fixture_identity', kind='managed_auth')]
        for step in range(71):
            phase = ('cleanup' if step >= 45 else 'restore'
                     if 'restore' in self.scenario[step]['request']['action'] else 'route_a'
                     if self.scenario[step]['route'] == 'A' else 'route_b')
            tickets.append(self.meter.charge(phase, 5,
                action='gotrue_workflow_identity_' + str(step), kind='managed_auth'))
        from .runtime_dispatch import WorkflowDispatch
        self.workflow_dispatch = WorkflowDispatch(self.meter, tickets)
        result = WorkflowBridge.workflow(self, *args, **kwargs)
        for ticket in tickets:
            self.meter.confirm(ticket, actual=5)
        return result

    def close_receipt(self, gate, request):
        if not self.final_post_complete or self.closing_receipt is not None:
            raise RuntimeError('ci_final_post_required')
        def read(name):
            return json.loads((gate.out / (getattr(gate, 'evidence_prefix', '') + name)).read_text())
        self.closing_receipt = counted_close(self.commands, read('integral-preflight.json'),
            [read('cli-protocol-' + str(i) + '.json') for i in range(3)],
            [read('auth-protocol-%02d.json' % i) for i in range(18)],
            read('workflow-auth-protocol.json'), request['run_id'], request['purpose'], self.quota['binding'])
        gate.save('integral-closure-intent.json', self.closing_receipt)
        return self.closing_receipt

class CaseLifecycle(RegisteredLifecycle):
    def dispatch(self, request):
        from .runtime_http import HttpJournal
        try:
            journal = getattr(self, 'http_journal', None)
            if journal is None:
                journal = self.http_journal = HttpJournal(self.gate, self.composition)
            require(type(request) is dict and 'http_terminal' in request, 'runtime_http_snapshot_missing')
            journal.accept(request['http_terminal'])
        except BaseException as error:
            self.failed = True
            try:
                self.composition.abort('case_http_evidence_failed')
            except BaseException as secondary:
                error.add_note('case_http_abort_secondary:' + type(secondary).__name__)
            raise
        return super().dispatch({k:v for k,v in request.items() if k != 'http_terminal'})

    def _dispatch(self, op, request):
        if op=='install':
            c=self.composition
            require(getattr(c,'case_prefix_ready',False) and not self.installed
                and request.get('ids')==self.ids, 'runtime_case_install_prefix')
            self.installed=True
            require(c.fixture_context['temporary_schemas']==[
                self.guard.scope(self.run_id,self.ids),self.audit.scope(self.run_id,self.ids)],
                'runtime_case_install_scope')
            c.current_phase='guard_install';self.install_attempted['guard']=True
            self.sql(self.guard.install(self.run_id,self.ids,180))
            self.receipt=self.guard.validate(json.loads(self.sql(self.guard.inspect(self.run_id,self.ids))),
                self.run_id,self.ids)
            self.expiry=self.receipt['expires_at']
            c.current_phase='metadata_install';self.install_attempted['audit']=True
            self.sql(self.audit.install(self.run_id,self.ids,self.expiry))
            self.metadata_receipt=self.audit.validate(json.loads(self.sql(self.audit.inspect(self.run_id,self.ids))),
                self.run_id,self.ids,self.expiry)
            return copy.deepcopy(self.receipt)
        value=super()._dispatch(op,request)
        faults=getattr(self.composition,'phase_faults',None)
        if faults is not None and op=='after':
            faults.auth_confirmed(request['role'],request['operation'])
        return value


def execute_case(gate, composition, lifecycle, config):
    """Actual existing runner, after local caller-owned prefix and lifecycle wiring."""
    require(isinstance(composition, CaseComposition), 'runtime_case_composition')
    require(isinstance(lifecycle, RegisteredLifecycle) and lifecycle.composition is composition
            and lifecycle.gate is gate, 'runtime_case_lifecycle')
    quota = composition.quota
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    from .compiler import validate_case_binding
    validate_case_binding(quota['root'], quota['manifest'], quota['binding'], now=now)
    verify_runtime_sources(quota['root'], quota['manifest'])
    require(composition.runner==composition.worker_path('runtime_auth.mjs'), 'runtime_worker_root')
    require(not hasattr(gate, 'apply_endchain_migration'), 'runtime_canonical_migration_reapply_forbidden')
    require(lifecycle.run_id == quota['binding']['run_id']
            and config.get('registeredIds') == lifecycle.ids
            and not lifecycle.worker_owned and not lifecycle.installed, 'runtime_case_lifecycle_binding')
    lock = getattr(lifecycle.lock_query, '__self__', None)
    require(isinstance(lock, IdentitySession) and lock.composition is composition
            and lock.runtime is composition.runtime and composition.runtime.environment == 'disposable_ci',
            'runtime_identity_session_binding')
    meter = composition.meter
    require(not meter.stopped and not meter.closed and meter.pending is None
            and not meter.managed_pending and meter.phases['preflight'] == 4
            and meter.phases['migration'] == 128 and getattr(composition,'case_prefix_ready',False),
            'runtime_verified_prefix_required')
    prefix = [event for event in meter.events if event['phase'] in ('preflight', 'migration')]
    require(prefix and all(event['confirmed'] is True for event in prefix),
            'runtime_verified_prefix_required')
    from .runtime_worker_runner import execute
    # No new timeout, reset, SQL, fault relabel or PASS promotion around this call.
    return execute(gate, composition, lifecycle, composition.worker_config(config))


def counted_close(trace, preflight, cli, auth, workflow, run_id, purpose, binding):
    if (run_id, purpose) != (binding['run_id'], binding['purpose']):
        raise ValueError('closure_run_not_registered')
    if [c['command'] for c in trace] != list(range(1, len(trace) + 1)) or not all(c['confirmed'] for c in trace):
        raise ValueError('closure_incomplete_protocol')
    if any(c['phase'] == 'final_closure' for c in trace):
        raise ValueError('closure_already_attempted')
    if len(preflight['commands']) != 4 or not all(c['confirmed'] for c in preflight['commands']):
        raise ValueError('closure_preflight')
    if len(cli) != 3 or [x.get('slot') for x in cli]!=['quota','pre_auth','final']:
        raise ValueError('closure_cli')
    cli_charge=sum(charged(item) for item in cli)
    expected = {'issue': 11, 'verify': 21, 'getUser': 5, 'refresh': 27, 'logout': 10, 'revoked_denial': 4}
    keys = {(x['role'], x['operation']) for x in auth}
    if len(auth) != 18 or keys != {(r, op) for r in ('a_member', 'a_trainer', 'b_member') for op in expected}:
        raise ValueError('closure_auth_matrix')
    if any(x['commands'] != expected[x['operation']] or any(s['temp_written'] for s in x['statements']) for x in auth):
        raise ValueError('closure_auth_load')
    if workflow['commands'] != 360 or workflow['verified_calls'] != 72 or any(s['temp_written'] for s in workflow['statements']):
        raise ValueError('closure_workflow_auth')
    native = sum(c['phase'] not in BOOTSTRAP for c in trace)
    managed = sum(x['commands'] for x in auth) + workflow['commands']
    total = native + 4 + cli_charge + managed + 1
    if total > binding['cap']:
        raise ValueError('closure_budget')
    return {'run_id': run_id, 'purpose': purpose, 'native_before_close': native,
            'managed_auth': managed, 'preflight': 4, 'cli': cli_charge, 'closing_commands': 1,
            'cli_count_classification':'120 reserved unknown slots plus 24 confirmed native observers; not 144 observed CLI commands',
            'global_commands': total, 'confirmed': False}
