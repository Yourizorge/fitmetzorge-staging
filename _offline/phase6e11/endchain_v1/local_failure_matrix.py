"""Serial, disposable PG17 failures. No hosted transport or retry admission."""
import hashlib,json,os,pathlib,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def main():
    folder=ROOT/'supabase/.temp'/('phase6e11-composition-failures-'+uuid.uuid4().hex);folder.mkdir()
    cases=[('call_before',{'command':10,'when':'before'},'action_started','call',0,0),
           ('commit_receipt_lost',{'command':11,'when':'after'},'action_started','commit',1,0),
           ('after_measurement_missing',{'command':14,'when':'before'},'after_saved',None,1,1)]
    receipts=[]
    for name,fault,phase,transport_phase,requests,sealed in cases:
        p=subprocess.run([sys.executable,'-B',str(HERE/'local_composition.py'),json.dumps(fault)],
            cwd=ROOT,env=os.environ,text=True,capture_output=True,timeout=180)
        if p.returncode!=2:raise RuntimeError('expected_local_stop_missing_'+name)
        summary=json.loads(p.stdout);path=pathlib.Path(summary['folder'])/'result.json'
        raw=path.read_bytes();v=json.loads(raw);result=v['result'];observed=v['independent_diagnostic'][0]
        if result['status']!='NO_GO' or result['phase']!=phase or result.get('injected') is not True:
            raise RuntimeError('failure_phase_'+name)
        if (result.get('transport_failure') or {}).get('phase')!=transport_phase:
            raise RuntimeError('transport_phase_lost_'+name)
        if observed['pairs']!=0 or observed['request_receipts']!=requests or observed['sealed']!=sealed:
            raise RuntimeError('partial_write_state_'+name)
        if result['commands'][-1]['phase']!='measurement' or len(result['commands'])>20:
            raise RuntimeError('rollback_or_command_boundary_'+name)
        if result.get('closure_failures') or not v['sources_unchanged'] or v['hosted_calls']!=0:
            raise RuntimeError('failure_closure_'+name)
        receipts.append({'case':name,'phase':phase,'transport_phase':transport_phase,'commands':len(result['commands']),
            'independent_local_diagnostic_commands':1,'state':observed,
            'receipt':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest()})
    result={'status':'LOCAL_PG17_FAILURE_MATRIX_PASS','cases':receipts,'hosted_calls':0,
        'full_chain_admission':False,'note':'Three distinct failed local runs; none is retried or promoted to a valid pair.'}
    with (folder/'result.json').open('x') as f:json.dump(result,f,indent=2);f.flush();os.fsync(f.fileno())
    print(json.dumps({'folder':str(folder),**result}));return 0

if __name__=='__main__':sys.exit(main())
