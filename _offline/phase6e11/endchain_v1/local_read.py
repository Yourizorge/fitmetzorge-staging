"""Read-only route adapter equivalence and cross-route tests on local PG17."""
import json, os, pathlib, subprocess, sys, uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport_v1'))
import native_local as n
r=n.r
def main():
    folder=r.ROOT/'supabase/.temp'/('phase6e11-read-local-'+uuid.uuid4().hex);folder.mkdir()
    try:
        r.ServerBoundary.setUpClass();r.enable_local_tls=n.local_ca_and_leaf;w=n.NativeRequests(folder)
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        p=subprocess.run([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
          '--allow-read='+str(w.ca),'--allow-env',str(HERE/'read_local.ts')],
          input=json.dumps({'port':r.ServerBoundary.cluster.port,'ca':str(w.ca),'window':w.w,'b':w.b,
            'actors':[r.uid(i) for i in range(1,4)],'sessions':[r.uid(i) for i in range(101,104)]}),
          text=True,capture_output=True,env=env,timeout=45,creationflags=0x08000000 if os.name=='nt' else 0)
        r.save(folder/'result.json',{'exitcode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
            'sources':{x.name:r.sha(x) for x in [pathlib.Path(__file__),HERE/'read_local.ts',HERE/'session_transport.mjs']},'hosted_calls':0})
        print(json.dumps({'folder':str(folder),'exitcode':p.returncode,'result':p.stdout.strip()}));return p.returncode
    finally:
        if getattr(r.ServerBoundary,'cluster',None):r.ServerBoundary.tearDownClass()
if __name__=='__main__':sys.exit(main())
