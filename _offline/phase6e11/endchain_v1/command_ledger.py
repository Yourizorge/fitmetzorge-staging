"""Conservative admission bound for the CURRENT adapters, not a new hosted runner."""
import ast,hashlib,json,pathlib,subprocess,sys
from sequence import compile_sequence,ROOT
HERE=pathlib.Path(__file__).resolve().parent
SOURCES=[
 '_offline/phase6e11/controller_v1/store.mjs',
 '_offline/phase6e11/request_v4/transport.mjs',
 '_offline/phase6e11/controller_guard_v1/issuance.mjs',
 '_offline/phase6e11/auth_metadata_v1/audit.py',
 '_offline/phase6e11/auth_metadata_v1/hosted.py',
 '_offline/phase6e11/endchain_v1/component_trace.mjs',
 '_offline/phase6e11/endchain_v1/command_ledger.py',
]

def reader_trace():
    source=ROOT/SOURCES[4];tree=ast.parse(source.read_text())
    fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='read'
            and any(isinstance(x,ast.Nonlocal) for x in n.body))
    # Evaluate ONLY the extracted read wrapper against mocks. Never import/run hosted.py.
    outer=ast.parse("def outer():\n serial=0\n").body[0]
    outer.body.extend([fn,ast.Return(ast.Name(id='read',ctx=ast.Load()))])
    events=[]
    def command(q):
        events.append(q)
        return [['on']] if q=="select current_setting('transaction_read_only')" else []
    namespace={'command':command,'save':lambda *a:None,'hashlib':hashlib}
    module=ast.fix_missing_locations(ast.Module(body=[outer],type_ignores=[]))
    exec(compile(module,'<isolated-read-wrapper>','exec'),namespace)
    namespace['outer']()('select synthetic_metadata',False)
    if events!=['BEGIN TRANSACTION READ ONLY',"select current_setting('transaction_read_only')",
                'select synthetic_metadata','ROLLBACK']:
        raise ValueError('reader_command_shape_changed')
    return len(events)

def arm_trace():
    import importlib.util
    spec=importlib.util.spec_from_file_location('budget_auth_audit',ROOT/SOURCES[3])
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    ids={r:'69000000-0000-4000-8000-'+str(i).zfill(12) for i,r in enumerate(audit.g.ROLES,1)}
    run='69000000-0000-4000-8000-000000000010';action='69000000-0000-4000-8000-000000000011'
    text=audit.arm(run,ids,action,'a_member','verify')
    head,body=text.split('DO $arm$',1)
    if head.strip()!="BEGIN; SET LOCAL lock_timeout='1s';" or not body.endswith('END $arm$; COMMIT;'):
        raise ValueError('auth_arm_envelope_changed')
    if not audit.disarm(run,ids,action).startswith('DO $close$'):raise ValueError('disarm_changed')
    return {'arm':4,'disarm':1}

def ledger(trace):
    if trace.get('counts')!={'evidence':5,'workflow':8,'issuance_guard':6} or trace.get('hosted_calls')!=0:
        raise ValueError('component_trace_changed')
    sequence=compile_sequence();reader=reader_trace();arm=arm_trace();rows=[]
    for action in sequence['actions']:
        commands={'durable_phases':5,'before_read':reader,'after_read':reader}
        if action['kind']=='workflow':commands['transaction_and_seal']=8
        else:
            commands.update(auth_arm=arm['arm'],auth_disarm=arm['disarm'])
            if action['operation'] in ('issue','verify','refresh'):commands['identity_guard']=6
        rows.append({'step':action['step'],'kind':action['kind'],'role':action['role'],
                     'operation':action['operation'],'commands':commands,'total':sum(commands.values())})
    total=sum(r['total'] for r in rows)
    return {'status':'NO_GO_PRE_HOSTED_BUDGET' if total>1280 else 'INCOMPLETE_LIFECYCLE_LEDGER',
      'approved_limit':1280,'current_adapter_lower_bound':total,'actions':rows,
      'evidence_commands':315,'workflow_transaction_commands':360,
      'scoped_reader_commands':63*2*reader,'auth_observer_commands':18*sum(arm.values()),
      'identity_guard_commands':9*6,
      'not_yet_included':['baseline','fixture_prepare','controller_claim_close','negative_authorization',
        'revoke','fixture_cleanup','Auth_audit_cleanup','guard_install_remove','observer_install_remove',
        'IO_measurements','final_measurements','safety_reserve'],
      'hosted_run_started':False,'hosted_commands':0,'hosted_admitted':False,
      'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
      'scope':'Lower bound for unchanged current adapter shape, not a lower bound for all possible safe implementations.'}

def main():
    import os,uuid
    p=subprocess.run([os.environ.get('FMZ_NODE','node'),str(HERE/'component_trace.mjs')],
                     text=True,capture_output=True,timeout=10)
    if p.returncode:raise RuntimeError('component_trace_failed')
    trace=json.loads(p.stdout);result=ledger(trace)
    folder=ROOT/'supabase/.temp'/('phase6e11-endchain-budget-'+uuid.uuid4().hex);folder.mkdir()
    for name,value in [('component-trace',trace),('ledger',result)]:
        raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
        with (folder/(name+'.json')).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    print(json.dumps({'status':result['status'],'lower_bound':result['current_adapter_lower_bound'],
                     'approved_limit':1280,'hosted_commands':0,'evidence':str(folder)}))
if __name__=='__main__':main()
