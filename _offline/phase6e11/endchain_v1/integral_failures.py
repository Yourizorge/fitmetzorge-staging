"""Three fresh disposable Supabase stacks; actual GoTrue and failed workflows.

Never a hosted retry. The normal receipt remains untouched. Each case resets
only its disposable CI database and writes a separate evidence namespace.
"""
import importlib.util,json,os,pathlib

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
        composition.admit_ci_prefix(json.loads((gate.out/'integral-preflight.json').read_text()),
            json.loads((gate.out/'cli-protocol-0.json').read_text()))
        try:
            gate.cli('db','reset','--local','--no-seed',timeout=180)
            configure_local_tls(gate)
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
 (select count(*) from fmz6e11_request_private.control where enabled) bridge_enabled"""
            row=gate.rows(sql)[0]
            expected={'receipts':receipts,'sealed':sealed,'completed':12,'stopped':1,'temporary_schemas':0,
                      'retained_window':1,'control_enabled':0,'bridge_enabled':0}
            if row!=expected:raise RuntimeError('ci_failure_final_state_'+fault)
            evidence={'case':fault,'expected':expected,'actual':row,'hosted_calls':0,
                'diagnostic_sql_commands':1,'mutation_retried':False,'incomplete_pair_preserved':True,
                'normal_receipt_reused_as_pass':False,'commands':len(composition.commands)}
            evidence['runtime_meter']=composition.meter.close()
            if not evidence['runtime_meter']['stopped'] or evidence['runtime_meter']['used']>2226:
                raise RuntimeError('ci_failure_meter_not_stopped')
            gate.save('validated.json',evidence);reports.append(evidence)
        finally:
            gate.save=original_save;audit.arm=original_arm
    gate.save('integral-real-failure-matrix.json',{'cases':reports,'hosted_calls':0,'separate_empty_CI_databases':True})
    return reports
