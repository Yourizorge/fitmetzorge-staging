"""Three fresh disposable Supabase stacks; actual GoTrue and failed workflows.

Never a hosted retry. The normal receipt remains untouched. Each case resets
only its disposable CI database and writes a separate evidence namespace.
"""
import importlib.util,json,os,pathlib,uuid
from closure import RUN_ID,PURPOSE,allowance
from safety_auth_budget import ROLES


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
    """Prove the second allowed entry state without a second migration apply."""
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

def run(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    from integral_ci import configure_local_tls
    from metered_composition import MeteredComposition
    import audit,auth_arm
    path=pathlib.Path(__file__).resolve().parent.parent/'controller_guard_v1/auth_service.py'
    spec=importlib.util.spec_from_file_location('failure_actual_gotrue',path)
    real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    reports=[];original_save=gate.save;original_arm=audit.arm
    for fault,receipts,sealed in [('before_call',0,0),('after_commit',1,0),('after_snapshot',1,1)]:
        prefix='fault-'+fault+'-'
        gate.save=lambda name,value,prefix=prefix:original_save(prefix+name,value)
        composition=MeteredComposition(fault)
        try:
            audit.arm=auth_arm.render
            try:real.run(gate,composition)
            except RuntimeError as error:
                if str(error) not in ('ci_integral_workflow_incomplete','registered_worker_failed') or not composition.injected:raise
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
            expected={'receipts':receipts,'sealed':sealed,'completed':12,'stopped':1,'temporary_schemas':0,
                      'retained_window':1,'control_enabled':0,'bridge_enabled':0,
                      'auth_accounts':3,'auth_sessions':0,'auth_refresh_tokens':0}
            if row!=expected:raise RuntimeError('ci_failure_final_state_'+fault)
            check_auth_zero(row,composition)
            evidence={'case':fault,'expected':expected,'actual':row,'hosted_calls':0,
                'diagnostic_sql_commands':1,'mutation_retried':False,'incomplete_pair_preserved':True,
                'normal_receipt_reused_as_pass':False,'commands':len(composition.commands),
                'three_auth_zero_confirmed':True,'safety_auth':composition.safety_auth_result}
            evidence['runtime_meter']=composition.meter.close()
            if not evidence['runtime_meter']['stopped'] or evidence['runtime_meter']['used']>allowance(RUN_ID,PURPOSE):
                raise RuntimeError('ci_failure_meter_not_stopped')
            gate.save('validated.json',evidence);reports.append(evidence)
        finally:
            gate.save=original_save;audit.arm=original_arm
    gate.save('integral-real-failure-matrix.json',{'cases':reports,'hosted_calls':0,'separate_empty_CI_databases':True})
    return reports
