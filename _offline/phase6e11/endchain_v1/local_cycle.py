"""Real PG17 + native TLS driver: read-committed snapshots across I/U/D."""
import json,os,pathlib,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport_v1'))
import native_local as n
r=n.r
def main():
    folder=r.ROOT/'supabase/.temp'/('phase6e11-cycle-local-'+uuid.uuid4().hex);folder.mkdir()
    try:
        r.ServerBoundary.setUpClass();r.enable_local_tls=n.local_ca_and_leaf
        w=n.NativeRequests(folder)
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        p=subprocess.run([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
          '--allow-read='+str(w.ca),'--allow-env',str(HERE/'cycle_local.ts'),str(w.ca),str(r.ServerBoundary.cluster.port)],
          text=True,capture_output=True,env=env,timeout=25,creationflags=0x08000000 if os.name=='nt' else 0)
        r.save(folder/'result.json',{'exitcode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
            'sources':{f.name:r.sha(f) for f in [HERE/'cycle_local.ts',HERE/'scoped_cycle.mjs',pathlib.Path(__file__)]},
            'hosted_calls':0})
        print(json.dumps({'evidence':str(folder),'exitcode':p.returncode,'result':p.stdout.strip()}))
        return p.returncode
    finally:
        if getattr(r.ServerBoundary,'cluster',None):r.ServerBoundary.tearDownClass()
if __name__=='__main__':sys.exit(main())
