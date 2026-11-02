"""New local component entry and read-only historical coverage validation.

The October runner/reset paths are disabled, including explicit diagnostics.
Legacy metadata remains readable; it cannot activate the historical run UUID.
run() delegates to real native component boundaries, without WAL admission.
"""
import copy,hashlib,importlib.util,json,os,pathlib,re,uuid
from closure import RUN_ID,PURPOSE,allowance
from safety_auth_budget import ROLES

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREFIX='_offline/phase6e11/endchain_v1/'
FORMAT='fmz-integral-failure-selection-v1'
LEGACY=('before_call','after_commit','after_snapshot')
from integral_failure_runtime import REQUIRED
BOUNDS={'cases':3,'registered_commands_per_case':2349,'diagnostic_selects_per_case':1,
        'worker_seconds':180,'worker_messages':200,'workflow_seconds':125,
        'sql_seconds':5,'lock_seconds':1,'files':2200,'bytes':80000000,'file_bytes':2000000}
# Preflight, matrix and coverage metadata share the existing individual limit.
REPORT_FILES=3
REPORT_BYTES=REPORT_FILES*BOUNDS['file_bytes']
SOURCE_FILES=tuple(PREFIX+n for n in (
    'integral_failures.py','test_integral_failures.py','integral_failure_runtime.py','integral_ci.py',
    'metered_composition.py','runtime_budget.py','lifecycle_gates.py','complete_register.py',
    'registered_runner.py','registered_lifecycle.py','safety_auth.py','safety_auth_native.py',
    'safety_auth_budget.py','auth_evidence.py','scenario.py','integral_auth.mjs',
    'integral_workflow.mjs','workflow_composition.mjs','closure.py','ci.py','artifact.py',
)) + (
    '_offline/phase6e11/controller_guard_v1/auth_service.py',
    '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py',
)


class FailureCoverageBlocked(RuntimeError):
    def __init__(self,report):
        super().__init__('ci_failure_coverage_incomplete')
        self.report=copy.deepcopy(report)


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def scenario_register():
    """Capabilities, not promises: no caller-provided flag can add a real hook."""
    rows=[]
    for case,receipts,sealed,event in (
        ('before_call',0,0,'workflow.step0.call.before'),
        ('after_commit',1,0,'workflow.step0.commit.after'),
        ('after_snapshot',1,1,'workflow.step0.second_measurement.before')):
        rows.append({'id':case,'implemented':True,'backend_fault':case,'step':0,
            'hook':event,'owner':'main','source':PREFIX+'integral_ci.py',
            'method':'Composition.workflow.raw_query','required_categories':[],
            'scope':'C04 real PG/GoTrue diagnostic only; not mid-phase or full failure coverage',
            'expected_receipts':receipts,'expected_sealed':sealed})
    missing=(
        ('normal','main','ci.py','Gate.advisors/confirmed normal closure',
         'bind existing complete normal-chain artifact from this same CI run/source; no additional replay'),
        ('pre_migration','C','metered_composition.py','admit_preflight/apply_migration',
         'after validated metered preflight, before migration dispatch'),
        ('post_migration','C','metered_composition.py','apply_migration',
         'after confirmed migration protocol, before dependent lifecycle writes'),
        ('mid_auth','E','registered_lifecycle.py','dispatch before/after',
         'real Auth operation prefix; unknown mint stays NO_GO without revocation claim'),
        ('mid_controller','main','integral_ci.py','evidence_query',
         'exact source-bound controller step before/after durable dispatch'),
        ('mid_route_a','main','integral_ci.py','Composition.workflow.raw_query',
         'source-derived nonzero Route A step and channel/phase'),
        ('mid_route_b','main','integral_ci.py','Composition.workflow.raw_query',
         'source-derived Route B step and channel/phase'),
        ('mid_restore','main','integral_ci.py','Composition.workflow.raw_query',
         'source-derived restore action and channel/phase'),
        ('lost_reply','E/main','registered_runner.py','execute/actual transport boundary',
         'actual dispatched operation, suppressed reply, independent outcome evidence; not an inferred HTTP outcome'),
        ('duplicate','main','integral_ci.py','Composition.workflow',
         'same exact request key/payload, actual replay, independent zero extra writes'),
        ('timeout','E','registered_runner.py','execute',
         'actual bounded worker/driver timeout; terminated worker and original failure retained'),
        ('partial_cleanup','E','registered_lifecycle.py','close_temporary',
         'one confirmed removal and one attempted/unconfirmed removal; no repeated delete'),
        ('cleanup_failure','E','registered_lifecycle.py','close_temporary',
         'actual cleanup dispatch boundary; original failure and retained claims survive cleanup error'),
        ('final_check_failure','main','integral_ci.py','final_post preservation',
         'actual independent final check fails without replacing the original failure'),
        ('closure_failure','main','integral_ci.py','close_receipt/confirm_closure',
         'actual closure boundary fails; terminal completeness remains false'),
    )
    for case,owner,file,method,event in missing:
        rows.append({'id':case,'implemented':False,'backend_fault':None,'step':None,
            'hook':case,'owner':owner,'source':PREFIX+file,'method':method,
            'required_categories':[case],'missing_hook':event,
            'missing_evidence':'real source-bound invocation, numeric outcome, stopped meter and exact terminal cleanup',
            'scope':'NOT_IMPLEMENTED_NOT_REAL_CI_EVIDENCE'})
    return rows


def source_binding(root,candidate,context):
    """Verify exact candidate AND loaded bytes; no Git/network/driver execution."""
    if (context.get('repository')!='Yourizorge/fitmetzorge-staging'
            or context.get('ref')!='refs/heads/main' or context.get('environment')!='disposable_ci'
            or not re.fullmatch('[0-9a-f]{40}',str(context.get('commit','')))
            or not re.fullmatch('[1-9][0-9]*',str(context.get('ci_run','')))
            or not re.fullmatch('[0-9a-f]{64}',str(candidate.get('sha256','')))):
        raise ValueError('ci_failure_source_identity')
    files=candidate.get('sources',{})
    verified={}
    for name in SOURCE_FILES:
        expected=files.get(name)
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):
            raise ValueError('ci_failure_candidate_source_missing')
        for folder in (pathlib.Path(root),ROOT):
            path=(folder/name).resolve()
            if not path.is_relative_to(folder.resolve()) or not path.is_file():
                raise ValueError('ci_failure_source_path')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError('ci_failure_source_drift')
        verified[name]=expected
    result={'context':dict(context),'candidate_sha256':candidate['sha256'],
        'source_hashes':verified,'scope':'failure selector and exact hook sources; not whole-CI attestation'}
    result['sha256']=sha(result)
    return result


def artifact_inventory(folder):
    """Sizes only. Do not read/export unrelated artifact contents."""
    folder=pathlib.Path(folder)
    files=total=largest=0
    for path in folder.rglob('*'):
        if path.is_symlink():raise ValueError('ci_failure_artifact_symlink')
        if path.is_file():
            size=path.stat().st_size
            files+=1;total+=size;largest=max(largest,size)
    return {'files':files,'bytes':total,'largest_file_bytes':largest}


def artifact_preflight(inventory,reserve,count):
    """A declared reservation is not a measured size or a raised collector cap."""
    fields=('files','bytes','largest_file_bytes')
    if any(type(inventory.get(k)) is not int or inventory[k]<0 for k in fields):
        raise ValueError('ci_failure_artifact_inventory')
    if (not isinstance(reserve,dict) or set(reserve)!={'files_per_case','bytes_per_case'}
            or any(type(v) is not int or v<=0 for v in reserve.values())):
        raise ValueError('ci_failure_artifact_reservation_required')
    projected_files=inventory['files']+REPORT_FILES+count*reserve['files_per_case']
    projected_bytes=inventory['bytes']+REPORT_BYTES+count*reserve['bytes_per_case']
    if (projected_files>BOUNDS['files'] or projected_bytes>BOUNDS['bytes']
            or inventory['largest_file_bytes']>BOUNDS['file_bytes']):
        raise ValueError('ci_failure_artifact_capacity')
    return {'before':dict(inventory),'reservation':dict(reserve),
        'projected_files':projected_files,'projected_bytes':projected_bytes,
        'projection_not_measurement':True,'collector_limits_unchanged':True}


def preflight(*,root,candidate,context,inventory,reserve=None,selection=None,diagnostic_only=False):
    """No stack reset, SQL, Auth, process launch or artifact write."""
    if type(diagnostic_only) is not bool:raise ValueError('ci_failure_mode')
    if allowance(RUN_ID,PURPOSE)!=BOUNDS['registered_commands_per_case']:
        raise ValueError('ci_failure_registered_limit_drift')
    selected=list(REQUIRED if selection is None else selection)
    register=scenario_register();by_id={row['id']:row for row in register}
    if (not selected or any(type(x) is not str or x not in by_id for x in selected)
            or len(set(selected))!=len(selected)):
        raise ValueError('ci_failure_selection')
    blockers=[]
    if len(selected)>BOUNDS['cases']:blockers.append('selected_cases_exceed_existing_three_case_bound')
    unsupported=[x for x in selected if not by_id[x]['implemented']]
    blockers.extend('missing_hook:'+x for x in unsupported)
    if not diagnostic_only:
        blockers.extend('required_hook_not_implemented:'+x for x in REQUIRED
                        if not by_id[x]['implemented'])
        blockers.extend('required_scenario_not_selected:'+x for x in REQUIRED if x not in selected)
    binding=source_binding(root,candidate,context)
    resources=None
    try:resources=artifact_preflight(inventory,reserve,len(selected))
    except ValueError as error:blockers.append(str(error))
    result={'format':FORMAT,'mode':'diagnostic_only' if diagnostic_only else 'full_required',
        'selection':selected,'register':register,'required':list(REQUIRED),
        'missing_hooks':[row for row in register if not row['implemented']],
        'source_binding':binding,'bounds':dict(BOUNDS),'artifacts':resources,
        'ready_for_execution':not blockers,'blockers':sorted(set(blockers)),
        'full_coverage_possible':False,'hosted_admission':False,'additional_hosted_commands':0,
        'bootstrap':'existing CI-only reset/bootstrap; not counted as registered-chain commands',
        'diagnostic_sql':'one existing final SELECT per executed legacy case, outside registered chain',
        'timeouts_changed':False,'automatic_retry':False}
    result['plan_sha256']=sha(result)
    return result


def _validate_plan(plan):
    if (not isinstance(plan,dict) or plan.get('format')!=FORMAT
            or plan.get('plan_sha256')!=sha({k:v for k,v in plan.items() if k!='plan_sha256'})
            or plan.get('register')!=scenario_register() or plan.get('bounds')!=BOUNDS
            or plan.get('required')!=list(REQUIRED)):
        raise ValueError('ci_failure_plan_binding')
    binding=plan['source_binding']
    if binding.get('sha256')!=sha({k:v for k,v in binding.items() if k!='sha256'}):
        raise ValueError('ci_failure_plan_source_binding')


def expected_state(case):
    spec=next((row for row in scenario_register() if row['id']==case and row['implemented']),None)
    if spec is None:raise ValueError('ci_failure_case_unimplemented')
    return {'receipts':spec['expected_receipts'],'sealed':spec['expected_sealed'],
        'completed':12,'stopped':1,'temporary_schemas':0,'retained_window':1,
        'control_enabled':0,'bridge_enabled':0,'auth_accounts':3,'auth_sessions':0,
        'auth_refresh_tokens':0}


def coverage(plan,reports):
    """Metadata validation only. Main must independently verify CI artifacts."""
    _validate_plan(plan)
    by_id={row['id']:row for row in scenario_register()}
    observed=[];invalid=[];covered=set()
    for report in reports:
        if not isinstance(report,dict):
            invalid.append('report_shape');continue
        case=report.get('case')
        if type(case) is not str or case not in plan['selection'] or case in observed:
            invalid.append('unexpected_or_duplicate_case');continue
        observed.append(case)
        spec=by_id[case]
        if not spec['implemented']:
            invalid.append('unsupported_case:'+case);continue
        meter=report.get('runtime_meter',{});safety=report.get('safety_auth',{})
        actual=report.get('actual',{})
        if (report.get('evidence_kind')!='REAL_DISPOSABLE_PG17_GOTRUE'
                or report.get('plan_sha256')!=plan['plan_sha256']
                or report.get('source_binding_sha256')!=plan['source_binding']['sha256']
                or report.get('observed_hook')!=spec['hook'] or report.get('fault_injected') is not True
                or report.get('primary_failure') not in ('ci_integral_workflow_incomplete','registered_worker_failed')
                or report.get('protocol_artifact')!='fault-'+case+'-integral-protocol-trace.json'
                or report.get('hosted_calls')!=0 or type(report.get('hosted_calls')) is not int
                or type(report.get('diagnostic_sql_commands')) is not int or report['diagnostic_sql_commands']!=1
                or report.get('mutation_retried') is not False
                or report.get('incomplete_pair_preserved') is not True
                or report.get('normal_receipt_reused_as_pass') is not False
                or report.get('three_auth_zero_confirmed') is not True
                or report.get('expected')!=expected_state(case) or actual!=expected_state(case)
                or any(type(v) is not int for v in actual.values())
                or meter.get('stopped') is not True or type(meter.get('used')) is not int
                or not 0<meter['used']<=BOUNDS['registered_commands_per_case']
                or meter.get('limit')!=BOUNDS['registered_commands_per_case']
                or meter.get('state',{}).get('auth_maybe_live') is not False
                or safety.get('status')!='NO_GO' or safety.get('revocation_confirmed') is not True
                or safety.get('global_zero_claim') is not False
                or not re.fullmatch('[0-9a-f]{64}',str(report.get('protocol_sha256','')))):
            invalid.append('unvalidated_real_case:'+case);continue
        covered.update(spec['required_categories'])
    missing=sorted(set(REQUIRED)-covered)
    missing_selected=sorted(set(plan['selection'])-set(observed))
    complete=not (missing or missing_selected or invalid or plan['blockers'])
    return {'status':'COVERAGE_METADATA_COMPLETE' if complete else 'NO_GO_FAILURE_COVERAGE',
        'complete':complete,'required':list(REQUIRED),'covered':sorted(covered),'missing_required':missing,
        'missing_selected':missing_selected,'invalid_reports':invalid,'diagnostic_cases':observed,
        'missing_hooks':plan['missing_hooks'],'plan_sha256':plan['plan_sha256'],
        'source_binding_sha256':plan['source_binding']['sha256'],
        'independent_artifact_review_required':True,'hosted_admission':False,
        'retained_failed_fixture_is_not_zero_all':True,'unit_tests_are_not_real_ci':True}


def require_full_coverage(plan,reports):
    result=coverage(plan,reports)
    if result['complete'] is not True:raise FailureCoverageBlocked(result)
    return result


def prepare(gate,selection,diagnostic_only,reserve):
    if (os.environ.get('GITHUB_ACTIONS')!='true'
            or os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging'
            or os.environ.get('GITHUB_REF')!='refs/heads/main'):
        raise RuntimeError('ci_only')
    if any((gate.out/name).exists() for name in ('integral-failure-preflight.json',
            'integral-failure-coverage.json','integral-real-failure-matrix.json')):
        raise RuntimeError('ci_failure_existing_evidence_preserved')
    context={'repository':os.environ['GITHUB_REPOSITORY'],'ref':os.environ['GITHUB_REF'],
        'commit':os.environ.get('GITHUB_SHA'),'ci_run':os.environ.get('GITHUB_RUN_ID'),
        'environment':'disposable_ci'}
    candidate=json.loads((gate.out/'candidate.json').read_text())
    plan=preflight(root=gate.sources,candidate=candidate,context=context,
        inventory=artifact_inventory(gate.out),reserve=reserve,selection=selection,
        diagnostic_only=diagnostic_only)
    if any(path.name.startswith(tuple('fault-'+case+'-' for case in plan['selection']))
           for path in gate.out.iterdir()):
        plan['blockers'].append('existing_failure_namespace_must_be_preserved')
        plan['ready_for_execution']=False
        plan['plan_sha256']=sha({k:v for k,v in plan.items() if k!='plan_sha256'})
    return plan


def recheck_sources(plan,root):
    binding=plan['source_binding']
    candidate={'sha256':binding['candidate_sha256'],'sources':binding['source_hashes']}
    if source_binding(root,candidate,binding['context'])!=binding:
        raise ValueError('ci_failure_source_binding_changed')


def check_artifact_usage(before,after,reserve):
    if (after['files']>BOUNDS['files'] or after['bytes']>BOUNDS['bytes']
            or after['largest_file_bytes']>BOUNDS['file_bytes']
            or after['files']-before['files']>reserve['files_per_case']
            or after['bytes']-before['bytes']>reserve['bytes_per_case']):
        raise RuntimeError('ci_failure_artifact_reservation_exceeded')


def auth_zero_projection(ids):
    if set(ids)!=set(ROLES) or len(set(ids.values()))!=3:raise ValueError('ci_failure_auth_scope')
    for value in ids.values():
        if str(uuid.UUID(value))!=value:raise ValueError('ci_failure_auth_scope')
    values=','.join("'"+ids[role]+"'" for role in ROLES)
    return (f",(select count(*) from auth.users where id in ({values})) auth_accounts"
        +f",(select count(*) from auth.sessions where user_id in ({values})) auth_sessions"
        +f",(select count(*) from auth.refresh_tokens where user_id::text in ({values})) auth_refresh_tokens")


def check_auth_zero(row,composition):
    if any(type(row.get(k)) is not int or row[k]!=v
            for k,v in {'auth_accounts':3,'auth_sessions':0,'auth_refresh_tokens':0}.items()):
        raise RuntimeError('ci_failure_three_auth_not_zero')
    receipt=composition.safety_auth_result
    if (not receipt or receipt.get('status')!='NO_GO' or receipt.get('revocation_confirmed') is not True
            or not composition.auth_zero_proof or composition.meter.state['auth_maybe_live']):
        raise RuntimeError('ci_failure_auth_zero_unconfirmed')

def already_present(gate):
    """Historical October replay is no longer authorized, even in disposable CI."""
    raise FailureCoverageBlocked({'status':'BLOCKED','reason':'historical_binding_read_only_reference',
        'mutation_started':False,'full_chain_admission':False})


def _historical_already_present_disabled(gate):
    raise FailureCoverageBlocked({'status':'BLOCKED','reason':'historical_binding_read_only_reference'})
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    from metered_composition import MeteredComposition
    import audit,auth_arm
    path=pathlib.Path(__file__).resolve().parent.parent/'controller_guard_v1/auth_service.py'
    spec=importlib.util.spec_from_file_location('present_actual_gotrue',path)
    real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    original_save=gate.save;original_arm=audit.arm;original_dry=getattr(gate,'final_dry_run',None)
    gate.save=lambda name,value:original_save('quota-present-'+name,value)
    gate.quota_already_present=True;gate.final_dry_run=None;gate.evidence_prefix='quota-present-'
    composition=MeteredComposition()
    try:
        audit.arm=auth_arm.render
        real.run(gate,composition)
        meter=composition.meter.receipt()
        if not meter['complete'] or meter['stopped'] or composition.fixture_context['migration_boundary']:
            raise RuntimeError('ci_present_quota_incomplete')
        if len(gate.cli_protocol)!=3 or any('--dry-run' not in r['arguments'] for r in gate.cli_protocol):
            raise RuntimeError('ci_present_quota_reapplied')
        gate.save('validated.json',{'complete':True,'hosted_calls':0,'migration_reapplied':False,
            'commands':meter['used'],'same_registered_chain':True})
        return True
    finally:
        gate.quota_already_present=False;gate.save=original_save;audit.arm=original_arm;gate.evidence_prefix=''
        gate.final_dry_run=original_dry

def run(gate,*,selection=None,diagnostic_only=False,artifact_reserve=None):
    from integral_failure_runtime import run as component_run
    if artifact_reserve is not None:
        raise ValueError('component_reservation_belongs_in_source_bound_driver')
    return component_run(gate,selection=selection,diagnostic_only=diagnostic_only)


def _historical_run_disabled(gate,*,selection=None,diagnostic_only=False,artifact_reserve=None):
    raise FailureCoverageBlocked({'status':'BLOCKED','reason':'historical_binding_read_only_reference',
        'mutation_started':False,'full_chain_admission':False})
    plan=prepare(gate,selection,diagnostic_only,artifact_reserve)
    _validate_plan(plan)
    gate.save('integral-failure-preflight.json',plan)
    if not plan['ready_for_execution']:
        raise FailureCoverageBlocked(plan)
    # Import the actual backend only after local admission. No unsupported hook
    # is emulated and the existing disposable bootstrap remains unchanged.
    from metered_composition import MeteredComposition
    import audit,auth_arm
    path=pathlib.Path(__file__).resolve().parent.parent/'controller_guard_v1/auth_service.py'
    spec=importlib.util.spec_from_file_location('failure_actual_gotrue',path)
    real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    reports=[];original_save=gate.save;original_arm=audit.arm
    for fault in plan['selection']:
        spec=next(row for row in plan['register'] if row['id']==fault)
        recheck_sources(plan,gate.sources)
        before_artifacts=artifact_inventory(gate.out)
        prefix='fault-'+fault+'-'
        gate.save=lambda name,value,prefix=prefix:original_save(prefix+name,value)
        composition=MeteredComposition(fault)
        try:
            audit.arm=auth_arm.render
            try:real.run(gate,composition)
            except RuntimeError as error:
                if str(error) not in ('ci_integral_workflow_incomplete','registered_worker_failed') or not composition.injected:raise
                primary_failure=str(error)
            else:raise RuntimeError('ci_expected_integral_failure_missing')
            w=composition.fixture_context['window']
            sql="""select
 (select count(*) from fmz6e11_request_private.receipts) receipts,
 (select count(*) from fmz6e11_request_private.receipts where state='pair_validated') sealed,
 (select count(*) from fmz6e11_controller_private.evidence where phase='pair_validated') completed,
 (select count(*) from fmz6e11_controller_private.runs where state='stopped' and next_step=12) stopped,
 (select count(*) from pg_namespace where nspname like 'fmz6e11_guard_%' or nspname like 'fmz6e11_am_%') temporary_schemas,
 (select count(*) from fmz6e11_private.windows where id='"""+w+"""') retained_window,
 (select count(*) from fmz6e11_private.config where enabled) control_enabled,
 (select count(*) from fmz6e11_request_private.control where enabled) bridge_enabled"""+auth_zero_projection(composition.auth_scope_ids)
            row=gate.rows(sql)[0]
            expected=expected_state(fault)
            if row!=expected:raise RuntimeError('ci_failure_final_state_'+fault)
            check_auth_zero(row,composition)
            evidence={'case':fault,'expected':expected,'actual':row,'hosted_calls':0,
                'diagnostic_sql_commands':1,'mutation_retried':False,'incomplete_pair_preserved':True,
                'normal_receipt_reused_as_pass':False,'commands':len(composition.commands),
                'three_auth_zero_confirmed':True,'safety_auth':composition.safety_auth_result,
                'evidence_kind':'REAL_DISPOSABLE_PG17_GOTRUE','fault_injected':composition.injected,
                'observed_hook':spec['hook'],'plan_sha256':plan['plan_sha256'],
                'source_binding_sha256':plan['source_binding']['sha256'],
                'primary_failure':primary_failure,'protocol_artifact':prefix+'integral-protocol-trace.json',
                'protocol_sha256':sha({'commands':composition.commands,'events':composition.events})}
            evidence['runtime_meter']=composition.meter.close()
            if not evidence['runtime_meter']['stopped'] or evidence['runtime_meter']['used']>allowance(RUN_ID,PURPOSE):
                raise RuntimeError('ci_failure_meter_not_stopped')
            recheck_sources(plan,gate.sources)
            gate.save('validated.json',evidence);reports.append(evidence)
            check_artifact_usage(before_artifacts,artifact_inventory(gate.out),artifact_reserve)
        finally:
            gate.save=original_save;audit.arm=original_arm
    result=coverage(plan,reports)
    gate.save('integral-real-failure-matrix.json',{'cases':reports,'hosted_calls':0,
        'separate_empty_CI_databases':True,'complete_failure_coverage':result['complete'],
        'plan_sha256':plan['plan_sha256'],'diagnostic_only':diagnostic_only})
    gate.save('integral-failure-coverage.json',result)
    # Even an explicitly requested diagnostic subset cannot make the existing
    # ci.py len(run(...)) caller fall through to full_chain_admission=True.
    require_full_coverage(plan,reports)
    return reports
