"""Versioned disposable runner; original dispatch/limits with durable exit evidence."""
import json,pathlib,re,subprocess,threading,time,traceback
from .runtime_worker_evidence import bind,save,validate_result,WaitEvidence

DISPATCH_OPS=frozenset(('install','query','before','after','workflow','remove','finalize',
    'evidence_query','safetyAuthlogout'))
AUTH_ROLES=('a_member','a_trainer','b_member')
AUTH_OPERATIONS=('issue','verify','getUser','refresh','logout','revoked_denial')

def execute(gate,composition,lifecycle,config):
    if config.get('mode')!='registered_synthetic' or config.get('environment')!='disposable_ci':
        raise ValueError('runner_environment')
    if config.get('identityBinding',{}).get('preexisting') is not True:
        raise ValueError('runner_preexisting_required')
    binding,source_hashes,case=bind(composition)
    from .compiler import sha,require
    require(sha(pathlib.Path(__file__).read_bytes())==source_hashes[
        '_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_worker_runner.py'],'worker_runner_loaded_source')
    observed=WaitEvidence(binding,case,'registered');result_ref=None
    lifecycle.own_worker()
    worker=None;timer=None;candidate=None;result=None;failure=None;count=0;started=time.monotonic()
    dispatch_failure=None;dispatch_secondary=[]
    try:
        worker=subprocess.Popen(['node',str(composition.runner)],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        observed.attach(worker)
        timer=threading.Timer(180,lambda:observed.kill(watchdog=True))
        observed.start_timer(timer,deadline=started+180)
        worker.stdin.write(json.dumps(config)+'\n');worker.stdin.flush()
        for line in worker.stdout:
            count+=1
            if count>200 or time.monotonic()-started>=180 or len(line)>2000000:
                raise RuntimeError('registered_worker_budget')
            request=json.loads(line)
            if type(request) is not dict or type(request.get('op')) is not str:
                raise ValueError('registered_operation_denied')
            op=request['op']
            if op not in DISPATCH_OPS|{'complete','failed'}:
                raise ValueError('registered_operation_denied')
            if op=='complete':
                candidate=validate_result(request['result'],'registered')
                result_ref=save(gate,'case-worker-result.json',candidate)
                break
            if op=='failed':raise RuntimeError('registered_worker_failed')
            if op in ('before','after') and (request.get('role') not in AUTH_ROLES
                    or request.get('operation') not in AUTH_OPERATIONS):
                raise ValueError('registered_auth_operation_denied')
            if op=='before':composition.action={'kind':'auth','role':request['role'],'operation':request['operation']}
            if op in ('install','remove','workflow'):composition.action={'kind':'lifecycle','operation':op}
            composition.current_phase=op
            try:reply={'value':lifecycle.dispatch(request)}
            except Exception as error:
                if dispatch_failure is None:dispatch_failure=error
                sqlstate=getattr(error,'sqlstate',None)
                if type(sqlstate) is not str or not re.fullmatch('[0-9A-Z]{5}',sqlstate):sqlstate=None
                try:
                    gate.save('registered-worker-stop-%03d.json'%count,{'operation':op,
                        'exception_class':type(error).__name__,'sqlstate':sqlstate,
                        'frames':[{'file':pathlib.Path(x.filename).name,'line':x.lineno,'function':x.name}
                            for x in traceback.extract_tb(error.__traceback__)],
                        'values_exported':False})
                except Exception as secondary:
                    dispatch_secondary.append({'stage':'stop_receipt','exception_class':type(secondary).__name__})
                    dispatch_failure.add_note('worker_secondary:stop_receipt:'+type(secondary).__name__)
                reply={'error':'registered_'+op+'_failed'}
            worker.stdin.write(json.dumps(reply,default=str)+'\n');worker.stdin.flush()
        observed.wait()
        if dispatch_failure is not None:raise dispatch_failure
        if time.monotonic()-started>=180:raise RuntimeError('registered_worker_budget')
        observed.stop_timer(timer)
        if not observed.known or observed.returncode or not candidate or candidate.get('checks')!=18 or not lifecycle.removed:
            raise RuntimeError('registered_worker_incomplete')
        composition.confirm_closure(gate,candidate)
        gate.save('integral-complete-protocol-trace.json',{'commands':composition.commands,
            'outer_sql_commands':len(composition.commands),'environment':config['environment'],
            'full_chain_admission':False})
        result=candidate
        return result
    except BaseException as error:
        failure=dispatch_failure if dispatch_failure is not None else error
        if failure is not error:
            failure.add_note('worker_secondary:worker_exit:'+type(error).__name__)
            raise failure from None
        raise
    finally:
        cleanup_errors=list(dispatch_secondary)
        # Each cleanup/evidence step is independent. Keep the original worker
        # failure while recording incomplete cleanup; never retry its SQL.
        def cleanup(stage,action):
            try:action()
            except Exception as error:
                cleanup_errors.append({'stage':stage,'exception_class':type(error).__name__})
                if failure is not None:failure.add_note('worker_secondary:'+stage+':'+type(error).__name__)
        if not observed.watchdog_stopped:observed.stop_timer(timer)
        observed.close()
        terminated=worker is None or observed.reaped
        termination_error=observed.termination_error
        config['admin']=None;config['anon']=None
        if not observed.known or cleanup_errors:result=None
        wait_ref=None
        def retain_wait():
            nonlocal wait_ref
            wait_ref=save(gate,'registered-worker-wait.json',observed.receipt())
        cleanup('wait_receipt',retain_wait)
        cleanup('worker_observation',lambda:save(gate,'registered-worker-observation.json',{
            'format':'registered-worker-observation-v1','binding':binding,'case_name':case,
            'source_hashes':source_hashes,'wait_ref':wait_ref,'result_ref':result_ref,
            'complete_received':candidate is not None,'messages':count,
            'original_exception_class':type(failure).__name__ if failure is not None else None,
            'automatic_retry':False,'full_chain_admission':False,'hosted_admitted':False}))
        if cleanup_errors:result=None
        if result is None and hasattr(composition,'abort'):
            cleanup('abort',lambda:composition.abort('registered_worker_incomplete'))
        try:
            if result is None:
                lifecycle.failed=True
                cleanup('parent_auth',lambda:lifecycle.parent_auth_cleanup(worker_terminated=terminated))
            if not lifecycle.removed:cleanup('temporary_removal',lifecycle.close_temporary)
        finally:
            if result is None:
                cleanup('incomplete_trace',lambda:gate.save('registered-incomplete-protocol-trace.json',{'commands':composition.commands,
                    'runtime_meter':composition.meter.receipt() if hasattr(composition,'meter') else None,
                    'complete':False,'automatic_retry':False}))
            cleanup('terminal_receipt',lambda:gate.save('registered-worker-terminal.json',{'complete':result is not None and not cleanup_errors,
                'guard_audit_removed':lifecycle.removed,'messages':count,
                'worker_terminated':terminated,'termination_error_class':termination_error,
                'cleanup_errors':cleanup_errors,
                'duration_ms':round((time.monotonic()-started)*1000),'automatic_retry':False,
                'secrets_exported':False}))
        if failure is None and (result is None or cleanup_errors):
            raise RuntimeError('registered_worker_cleanup_incomplete')

