"""Original local worker observations. No SQL, cleanup authority or PASS minting."""
import copy
import json
import os
import pathlib
import re
import stat
import threading
import time

from .compiler import canonical, read_source, require, sha

PREFIX='_offline/phase6e11/endchain_v1/'
OWN=PREFIX+'quota_candidate_v1/'
BASELINE=PREFIX+'registered_runner.py'
BASELINE_SHA='b37f9e42fbd0fbd10aff889a18bb5a110539e112dbe9e57597a9c6ea1a2d560b'
SOURCES=(BASELINE,OWN+'runtime_worker_evidence.py',OWN+'runtime_worker_runner.py',
    OWN+'runtime_parent_workflow.py',OWN+'runtime_recovery.py',OWN+'runtime_adapter.py',
    OWN+'runtime_case_entry.py',OWN+'runtime_case_terminal.py',OWN+'runtime_auth.mjs',
    OWN+'runtime_integral_workflow.mjs')
ROLES=('a_member','a_trainer','b_member')
OPERATIONS=('issue','verify','getUser','refresh','logout','revoked_denial')
METADATA=set(('version rows table key_sha value_sha operation before after count sha256 xid backend '
    'actor_sha workspace_sha request_sha payload_sha session_sha source_sha status phase code http_status '
    'request_id started_at ended_at query_count temp_read temp_written expected actual evidence_sha '
    'contract_sha protected_equal pair_complete present revoked expires_at kind changes user_sha route '
    'app_writes auth_events session_count refresh_count audit_count').split())
AFTER=METADATA|set(('events exact_contract registered_auth_zero seq action_id table_name at '
    'manifest_sha256 manifest_count registered_count scope_count extra_registered_count sessions '
    'refresh_tokens environment sources disabled_registry_rows_included unregistered_accounts_outside_manifest').split())


def metadata(value,keys,key='',depth=0):
    require(depth<=16,'worker_metadata_depth')
    if value is None or type(value) is bool:return
    if type(value) is int:
        require(0<=value<=2**53-1,'worker_metadata_integer');return
    if type(value) is str:
        require(len(value)<=128 and not re.search(r'eyJ|sbp_|sb_secret_|Bearer|postgres:|password',value,re.I)
            and (re.fullmatch(r'[A-Za-z0-9_.-]*',value) or
                 re.fullmatch(r'\d{4}-\d\d-\d\d[T ][0-9:.+-]+Z?',value)), 'worker_metadata_text')
        if key.endswith('_sha') or key.endswith('_sha256') or key=='sha256':
            require(re.fullmatch('[a-f0-9]{64}',value),'worker_metadata_hash')
        return
    if type(value) is list:
        require(len(value)<=512,'worker_metadata_array')
        for item in value:metadata(item,keys,key,depth+1)
        return
    require(type(value) is dict and set(value)<=keys,'worker_metadata_fields')
    if 'sources' in value:require(value['sources']=={},'worker_metadata_local_sources')
    for name,item in value.items():metadata(item,keys,name,depth+1)


def validate_result(value,kind):
    require(type(value) is dict,'worker_result_shape')
    if kind=='registered':
        require(set(value)=={'status','checks','proof','workflow','durable_steps','closure',
            'protocolCount','hosted_requests','emails_sent','environment'},'worker_result_fields')
        require(value['status']=='INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS'
            and value['environment']=='disposable_ci' and value['closure']=='confirmed'
            and all(type(value[k]) is int and value[k]==v for k,v in
                (('checks',18),('durable_steps',89),('hosted_requests',0),('emails_sent',0)))
            and type(value['protocolCount']) is int and 0<=value['protocolCount']<=2349,'worker_result_scope')
        work=value['workflow']
        require(type(work) is dict and set(work)=={'status','pairs','deletes','outer_sql_commands_so_far',
            'next_step','hosted_admitted'} and work['status']=='REAL_AUTH_THROUGH_71_WORKFLOW_PAIRS'
            and work['hosted_admitted'] is False,'worker_workflow_shape')
        require(all(type(work[k]) is int and work[k]==v for k,v in (('pairs',71),('deletes',123),('next_step',83)))
            and type(work['outer_sql_commands_so_far']) is int
            and 0<=work['outer_sql_commands_so_far']<=2349,'worker_workflow_count')
        proof=value['proof'];order=[(r,o) for r in ROLES for o in OPERATIONS[:4]]+[
            (r,o) for r in ROLES for o in OPERATIONS[4:]]
        require(type(proof) is list and len(proof)==18,'worker_proof_count')
        for row,(role,operation) in zip(proof,order):
            require(type(row) is dict and set(row)=={'role','operation','result','after'}
                and row['role']==role and row['operation']==operation,'worker_proof_order')
            metadata(row['result'],METADATA)
            require(type(row['after']) is dict and row['after'].get('pair_complete') is True
                and row['after'].get('exact_contract') is True,'worker_proof_pair')
            metadata(row['after'],AFTER)
    else:
        # Inner workflow results already have a fixed technical contract; never
        # retain arbitrary child diagnostics, SQL, credentials or error messages.
        allowed={'status','pairs','deletes','next_step','commandCount','real_local_auth',
            'worker_cpu_ms','worker_wall_ms','worker_cpu_limit_ms','worker_wall_limit_ms',
            'phase','code','close_failed','writes','proofs','hosted_admitted','missing'}
        require(kind=='workflow' and set(value)<=allowed,'workflow_result_fields')
        require(value.get('status') in ('LOCAL_COMPOSED_71_PASS','NO_GO')
            and value.get('real_local_auth') is True
            and value.get('hosted_admitted',False) is False,'workflow_result_scope')
        for key,item in value.items():
            if key in ('worker_cpu_ms','worker_wall_ms'):
                import math
                require(type(item) in (int,float) and math.isfinite(item) and item>=0,'workflow_result_time')
            else:metadata(item,METADATA,key)
    require(len(canonical(value))<=2_000_000,'worker_result_size')
    return value


def bind(composition):
    quota=composition.quota
    root=pathlib.Path(quota['root']);sources=quota['manifest']['sources'];binding=quota['binding']
    require(binding.get('environment')=='disposable_ci' and binding.get('hosted_permission') is False,
        'worker_evidence_environment')
    hashes={name:sha(read_source(root,name)) for name in SOURCES}
    require(all(sources.get(n)==h for n,h in hashes.items()) and hashes[BASELINE]==BASELINE_SHA,
        'worker_evidence_source')
    require(sha(pathlib.Path(__file__).read_bytes())==hashes[OWN+'runtime_worker_evidence.py'],
        'worker_evidence_loaded_source')
    return copy.deepcopy(binding),hashes,composition.phase_faults.case


def save(gate,name,value):
    root=pathlib.Path(gate.out).resolve(strict=True)
    path=root/name
    require(type(name) is str and re.fullmatch('[a-z0-9-]+[.]json',name)
        and path.parent==root and not path.exists(),'worker_evidence_fresh_path')
    raw=canonical(value)
    require(0<len(raw)<=2_000_000,'worker_evidence_size')
    flags=os.O_RDWR|os.O_CREAT|os.O_EXCL|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags,0o600)
    # Same descriptor for write, fsync and readback. Never trust Gate.save's
    # durability or replace an existing original after an uncertain write.
    with os.fdopen(fd,'w+b') as stream:
        require(stream.write(raw)==len(raw),'worker_evidence_short_write')
        stream.flush();os.fsync(stream.fileno())
        stream.seek(0)
        require(stream.read(len(raw)+1)==raw,'worker_evidence_readback')
        opened=os.fstat(stream.fileno());named=path.stat(follow_symlinks=False)
        require(stat.S_ISREG(named.st_mode) and not path.is_symlink()
            and path.resolve(strict=True).parent==root
            and (opened.st_dev,opened.st_ino,opened.st_size)==(named.st_dev,named.st_ino,len(raw)),
            'worker_evidence_file_identity')
    return {'path':name,'sha256':sha(raw),'bytes':len(raw)}


class WaitEvidence:
    """Record actual wait return values; a later reap never erases an earlier failure."""
    def __init__(self,binding,case,kind):
        require(kind in ('registered','workflow'),'worker_kind')
        self.binding=copy.deepcopy(binding);self.case=case;self.kind=kind
        self.process=None;self.events=[];self.lock=threading.Lock()
        self.wait_error=None;self.termination_error=None;self.watchdog_fired=False
        self.watchdog_stopped=True;self.watchdog_error=None;self.watchdog_deadline=None
        self.watchdog_stop_attempted=False
        self.wait_completed=False;self.returncode=None;self.reaped=False

    def attach(self,process):
        require(self.process is None and type(process.pid) is int and process.pid>0,'worker_process_owner')
        self.process=process

    def start_timer(self,timer,*,deadline):
        self.watchdog_stopped=False;self.watchdog_deadline=deadline
        timer.start()

    def stop_timer(self,timer):
        if timer is None or self.watchdog_stop_attempted:return
        self.watchdog_stop_attempted=True
        try:
            timer.cancel()
            # Join consumes only the remaining existing worker window. Never
            # grant a fresh timeout after that window has expired.
            remaining=max(0,self.watchdog_deadline-time.monotonic())
            timer.join(timeout=min(5,remaining))
            alive=timer.is_alive()
            require(type(alive) is bool,'worker_watchdog_alive_unknown')
            self.watchdog_stopped=not alive
            if alive:self.watchdog_error='WatchdogStillAlive'
            elif remaining==0:self.watchdog_error='WatchdogDeadlineElapsed'
        except BaseException as error:
            self.watchdog_stopped=False;self.watchdog_error=type(error).__name__

    def event(self,operation,**value):
        with self.lock:
            self.events.append({'ordinal':len(self.events)+1,'operation':operation,**value})

    def kill(self,watchdog=False):
        if watchdog:self.watchdog_fired=True
        self.event('kill',attempted=True,watchdog=watchdog)
        try:self.process.kill()
        except BaseException as error:
            self.termination_error=type(error).__name__
            self.event('kill_error',exception_class=self.termination_error)
            if not watchdog:raise

    def wait(self):
        self.event('wait',attempted=True,timeout_seconds=5)
        try:
            code=self.process.wait(timeout=5)
            require(type(code) is int and -255<=code<=255 and self.process.returncode==code,
                'worker_wait_result')
            self.wait_completed=True;self.returncode=code;self.reaped=True
            self.event('wait_return',returncode=code)
            return code
        except BaseException as error:
            if self.wait_error is None:self.wait_error=type(error).__name__
            self.event('wait_error',exception_class=type(error).__name__)
            raise

    def close(self):
        if self.process is None:return
        try:
            if self.process.poll() is None:self.kill()
            if not self.reaped:self.wait()
        except BaseException as error:
            if self.termination_error is None:self.termination_error=type(error).__name__
        # Closing pipe handles is distinct from proving a waited exit.
        if self.reaped:
            for name in ('stdin','stdout','stderr'):
                stream=getattr(self.process,name,None)
                if stream is not None:
                    try:stream.close()
                    except Exception as error:
                        if self.termination_error is None:self.termination_error=type(error).__name__

    @property
    def known(self):
        return (self.reaped and self.wait_completed and self.wait_error is None
            and self.termination_error is None and not self.watchdog_fired
            and self.watchdog_stopped and self.watchdog_error is None)

    def receipt(self):
        return {'format':self.kind+'-worker-wait-v1','binding':self.binding,'case_name':self.case,
            'pid':self.process.pid if self.process is not None else None,'wait_completed':self.wait_completed,
            'reaped':self.reaped,'returncode':self.returncode,'wait_error_class':self.wait_error,
            'termination_error_class':self.termination_error,'watchdog_fired':self.watchdog_fired,
            'watchdog_stopped':self.watchdog_stopped,'watchdog_error_class':self.watchdog_error,
            'events':copy.deepcopy(self.events),'automatic_retry':False,'full_chain_admission':False,
            'hosted_admitted':False}


def validate_wait(value,binding,case,*,normal,kind='registered'):
    require(value.get('format')==kind+'-worker-wait-v1' and value.get('binding')==binding
        and value.get('case_name')==case and type(value.get('pid')) is int and value['pid']>0
        and value.get('wait_completed') is True and value.get('reaped') is True
        and value.get('wait_error_class') is None and value.get('termination_error_class') is None
        and value.get('watchdog_fired') is False and value.get('automatic_retry') is False
        and value.get('watchdog_stopped') is True and value.get('watchdog_error_class') is None
        and type(value.get('returncode')) is int and -255<=value['returncode']<=255
        and (not normal or value['returncode']==0),'worker_wait_unconfirmed')
    events=value.get('events')
    require(type(events) is list and 2<=len(events)<=8
        and [e.get('ordinal') for e in events]==list(range(1,len(events)+1)),'worker_wait_events')
    require(events[-2].get('operation')=='wait' and events[-2].get('timeout_seconds')==5
        and events[-1].get('operation')=='wait_return'
        and events[-1].get('returncode')==value['returncode']
        and all(e.get('operation') in ('kill','wait','wait_return') for e in events),'worker_wait_return_original')


def export(gate,composition,case,worker_result):
    """Original references only; caller has already saved its live terminal witness."""
    binding,hashes,bound_case=bind(composition)
    require(case==bound_case,'worker_export_case')
    root=pathlib.Path(gate.out).resolve(strict=True)
    refs={}
    def original(name):
        path=root/name
        require(path.parent==root and not path.is_symlink() and path.resolve(strict=True).parent==root,
            'worker_export_path')
        raw=path.read_bytes();require(0<len(raw)<=2_000_000,'worker_export_bound')
        value=json.loads(raw);refs[name]={'path':name,'sha256':sha(raw),'bytes':len(raw)}
        return value
    names={'terminal_ref':'registered-worker-terminal.json','finally_ref':'case-registered-finally.json',
        'register_ref':'runtime-command-meter.json','terminal_witness_ref':'case-runtime-terminal.json',
        'wait_ref':'registered-worker-wait.json','observation_ref':'registered-worker-observation.json',
        'trace_ref':'integral-complete-protocol-trace.json' if case=='normal' else 'registered-incomplete-protocol-trace.json'}
    values={key:original(name) for key,name in names.items()}
    validate_wait(values['wait_ref'],binding,case,normal=case=='normal')
    observation=values['observation_ref']
    require(observation.get('binding')==binding and observation.get('case_name')==case
        and observation.get('source_hashes')==hashes
        and observation.get('wait_ref')==refs[names['wait_ref']],'worker_export_observation')
    inner_wait=root/'workflow-worker-wait.json'
    inner_result=root/'case-workflow-worker-result.json'
    if inner_wait.exists() or inner_result.exists() or case=='normal':
        inner=original('workflow-worker-wait.json')
        validate_wait(inner,binding,case,normal=case=='normal',kind='workflow')
        names['workflow_wait_ref']='workflow-worker-wait.json'
        if inner_result.exists():
            inner_value=validate_result(original('case-workflow-worker-result.json'),'workflow')
            if case=='normal':
                require(inner_value.get('status')=='LOCAL_COMPOSED_71_PASS'
                    and all(type(inner_value.get(k)) is int and inner_value[k]==v
                        for k,v in (('pairs',71),('deletes',123),('next_step',83))),
                    'workflow_export_incomplete_result')
            names['workflow_worker_result_ref']='case-workflow-worker-result.json'
        else:require(case!='normal','workflow_export_result_lost')
    if observation.get('result_ref') is not None:
        value=original('case-worker-result.json')
        require(observation['result_ref']==refs['case-worker-result.json'],'worker_export_result_original')
        validate_result(value,'registered')
    if case=='normal':
        require(worker_result is not None and observation.get('result_ref') is not None
            and canonical(value)==canonical(worker_result) and observation.get('complete_received') is True,
            'worker_export_result_lost')
        names['worker_result_ref']='case-worker-result.json'
        for i in range(18):original('auth-protocol-%02d.json'%i)
        for i in range(3):original('cli-protocol-%d.json'%i)
        for name in ('workflow-auth-protocol.json','integral-preflight.json','integral-closure.json'):original(name)
    else:
        require(worker_result is None,'worker_export_fault_result')
        names['fault_ref']='case-fault-boundary.json';original(names['fault_ref'])
    value={'format':'case-worker-export-v1','binding':binding,'case_name':case,
        'source_hashes':dict(composition.quota['manifest']['sources']),
        **{key:refs[name] for key,name in names.items()},'worker_result_ref':refs.get('case-worker-result.json') if case=='normal' else None,
        'all_original_refs':list(refs.values()),'full_chain_admission':False,'hosted_admitted':False}
    if case=='normal':value.update(auth_refs=[refs['auth-protocol-%02d.json'%i] for i in range(18)],
        cli_refs=[refs['cli-protocol-%d.json'%i] for i in range(3)],workflow_ref=refs['workflow-auth-protocol.json'],
        preflight_ref=refs['integral-preflight.json'],closure_ref=refs['integral-closure.json'])
    reference=save(gate,'case-worker-export.json',value)
    return reference,list(refs.values())
