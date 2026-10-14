"""Private, bounded worker runner. Never accepts browser input or exports keys."""
import json,pathlib,re,subprocess,threading,time,traceback

def execute(gate,composition,lifecycle,config):
    if config.get('mode')!='registered_synthetic' or config.get('environment') not in ('disposable_ci','staging'):
        raise ValueError('runner_environment')
    if config.get('identityBinding',{}).get('preexisting') is not True:
        raise ValueError('runner_preexisting_required')
    worker=None;timer=None;result=None;count=0;started=time.monotonic()
    try:
        worker=subprocess.Popen(['node',str(composition.runner)],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        timer=threading.Timer(180,worker.kill);timer.start()
        worker.stdin.write(json.dumps(config)+'\n');worker.stdin.flush()
        for line in worker.stdout:
            count+=1
            if count>200 or time.monotonic()-started>=180 or len(line)>2000000:
                raise RuntimeError('registered_worker_budget')
            request=json.loads(line);op=request['op']
            if op=='complete':
                candidate=request['result'];composition.confirm_closure(gate,candidate)
                result=candidate;break
            if op=='failed':raise RuntimeError('registered_worker_failed')
            if op=='before':composition.action={'kind':'auth','role':request['role'],'operation':request['operation']}
            if op in ('install','remove','workflow'):composition.action={'kind':'lifecycle','operation':op}
            composition.current_phase=op
            try:reply={'value':lifecycle.dispatch(request)}
            except Exception as error:
                gate.save('registered-worker-stop-%03d.json'%count,{'operation':op,
                    'exception_class':type(error).__name__,'sqlstate':getattr(error,'sqlstate',None),
                    'frames':[{'file':pathlib.Path(x.filename).name,'line':x.lineno,'function':x.name}
                        for x in traceback.extract_tb(error.__traceback__)],
                    'values_exported':False})
                reply={'error':'registered_'+op+'_failed'}
            worker.stdin.write(json.dumps(reply,default=str)+'\n');worker.stdin.flush()
        worker.wait(timeout=5)
        if worker.returncode or not result or result.get('checks')!=18 or not lifecycle.removed:
            raise RuntimeError('registered_worker_incomplete')
        gate.save('integral-complete-protocol-trace.json',{'commands':composition.commands,
            'outer_sql_commands':len(composition.commands),'environment':config['environment'],
            'full_chain_admission':False})
        return result
    finally:
        if timer:timer.cancel()
        if worker and worker.poll() is None:worker.kill();worker.communicate(timeout=5)
        config['admin']=None;config['anon']=None
        if result is None and hasattr(composition,'abort'):composition.abort('registered_worker_incomplete')
        try:
            if not lifecycle.removed:lifecycle.close_temporary()
        finally:
            gate.save('registered-worker-terminal.json',{'complete':result is not None,
                'guard_audit_removed':lifecycle.removed,'messages':count,
                'duration_ms':round((time.monotonic()-started)*1000),'automatic_retry':False,
                'secrets_exported':False})

class IdentitySession:
    """Exact identity-lock queries over the same verified native driver."""
    def __init__(self,runtime,composition,run_id,ids):
        self.runtime=runtime;self.composition=composition;self.connection=None
        from native_runtime import ALIASES
        self.allowed={(ids[role],email) for role,email in ALIASES.items()}
        self.guard='fmz6e11_guard_'+run_id.replace('-','')+'.identity_guard()'
        root=pathlib.Path(__file__).resolve().parent.parent
        def template(file,name):
            values=re.findall(r'(?:const|export const) '+name+r'=\x60([^\x60]+)\x60',file.read_text())
            if len(values)!=1 or '${' in values[0]:raise ValueError('identity_template_binding')
            return values[0]
        self.lock=template(root/'controller_v1/auth_guard.mjs','LOCK_IDENTITY')
        self.attest=template(root/'controller_guard_v1/issuance.mjs','attestation')
    def query(self,text,args):
        controls={'BEGIN','ROLLBACK',"SET LOCAL lock_timeout='1s'","SET LOCAL statement_timeout='2s'"}
        if text not in controls and text not in (self.lock,self.attest):
            raise ValueError('registered_identity_query_denied')
        if text in controls and args or text==self.lock and tuple(args) not in self.allowed or text==self.attest and args!=[self.guard]:
            raise ValueError('registered_identity_parameters_denied')
        if self.connection is None:self.connection=self.runtime.connect()
        from integral_ci import bind_parameters
        query,parameters=bind_parameters(text,args)
        cursor=self.connection.execute(query,parameters)
        return cursor.fetchall() if cursor.description else []
    def close(self):
        if self.connection is None:return
        c=self.composition
        try:
            if self.connection.info.transaction_status!=0:
                c.safety_label='rollback_auth_lock'
                c.before_sql('safety_rollback','ROLLBACK')
                self.connection.execute('ROLLBACK')
                c.after_sql('safety_rollback','ROLLBACK')
        finally:
            self.connection.close();self.connection=None;c.safety_label=None
