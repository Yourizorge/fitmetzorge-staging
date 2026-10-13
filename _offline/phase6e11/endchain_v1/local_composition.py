"""Fast native composition on disposable PG17; never real hosted credentials."""
import json, os, pathlib, subprocess, sys, uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scenario import capture
sys.path.insert(0,str(HERE.parent/'transport_v1'))
import native_local as n
r=n.r
def main():
    folder=r.ROOT/'supabase/.temp'/('phase6e11-composition-local-'+uuid.uuid4().hex);folder.mkdir()
    sources=[pathlib.Path(__file__),HERE/'composition_local.ts',HERE/'session_transport.mjs',
        HERE/'workflow_composition.mjs',HERE/'composed_handler.mjs',HERE/'native_store.mjs']
    before={x.name:r.sha(x) for x in sources}
    r.save(folder/'source-before.json',before)
    try:
        r.ServerBoundary.setUpClass();r.enable_local_tls=n.local_ca_and_leaf;w=n.NativeRequests(folder)
        for name in ['20261012104331_phase6e11_controller_evidence.sql','20261012185121_phase6e11_single_endchain_budget.sql']:
            w.sql((r.ROOT/'supabase/migrations'/name).read_text())
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        roles=['member','trainer','b']
        payload={'port':r.ServerBoundary.cluster.port,'ca':str(w.ca),'window':w.w,'a':w.x,'b':w.b,
            'ids':{role:r.uid(i+1) for i,role in enumerate(roles)},
            'sessions':{role:r.uid(i+101) for i,role in enumerate(roles)},'initialRevision':w.revisions()['revision'],
            'scenario':capture()['workflow_actions'],'sourceSha':'262b49d5c13149315fa7a610863fa1a15822bcb1','includeCleanup':True}
        if len(sys.argv)>1:payload['fault']=json.loads(sys.argv[1])
        process=subprocess.run([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
          '--allow-read='+str(w.ca),'--allow-env',str(HERE/'composition_local.ts')],input=json.dumps(payload),
          text=True,capture_output=True,env=env,timeout=130,creationflags=0x08000000 if os.name=='nt' else 0)
        result=json.loads(process.stdout) if process.stdout else {'status':'NO_GO','phase':'local_process'}
        after={x.name:r.sha(x) for x in sources}
        if before!=after:result={'status':'NO_GO','phase':'source_binding','code':'source_changed','prior':result}
        # Independent local diagnostics after the test process has closed all
        # sessions. This is separately labelled SQL, not part of run admission.
        inspection=w.rows("""select
 (select count(*) from fmz6e11_controller_private.evidence where phase='pair_validated') pairs,
 (select count(*) from fmz6e11_request_private.receipts) request_receipts,
 (select count(*) from fmz6e11_request_private.receipts where state='pair_validated') sealed,
 (select count(*) from fmz6e11_audit_private.writes) observed_writes,
 (select count(*) from fmz6e11_controller_private.runs where state='closed') closed_runs""")
        r.save(folder/'result.json',{'exitcode':process.returncode,'result':result,'stderr':process.stderr,
            'independent_local_diagnostic_commands':1,'independent_diagnostic':inspection,
            'sources':before,'sources_unchanged':before==after,'hosted_calls':0})
        print(json.dumps({'folder':str(folder),'exitcode':process.returncode,'status':result.get('status'),
            'phase':result.get('phase'),'code':result.get('code'),'commands':len(result.get('commands',[])),
            'pairs':result.get('pairs'),'seconds':result.get('seconds')}));return process.returncode if before==after else 2
    finally:
        if getattr(r.ServerBoundary,'cluster',None):r.ServerBoundary.tearDownClass()
if __name__=='__main__':sys.exit(main())
