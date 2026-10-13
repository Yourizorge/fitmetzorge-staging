"""One native PG17 connection, 71 separately committed/sealed request transactions."""
import json,os,pathlib,subprocess,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport_v1'))
import native_local as n
r=n.r
def main():
    folder=r.ROOT/'supabase/.temp'/('phase6e11-session-local-'+uuid.uuid4().hex);folder.mkdir()
    try:
        r.ServerBoundary.setUpClass();r.enable_local_tls=n.local_ca_and_leaf
        w=n.NativeRequests(folder)
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        payload={'ca':str(w.ca),'port':r.ServerBoundary.cluster.port,'window':w.w,'workspace':w.x,
            'revision':w.revisions()['revision'],'claims':{'sub':r.uid(1),'session_id':r.uid(101),
            'iss':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1','aud':'authenticated',
            'role':'authenticated','exp':int(time.time())+300}}
        p=subprocess.run([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
          '--allow-read='+str(w.ca),'--allow-env',str(HERE/'session_local.ts')],input=json.dumps(payload),
          text=True,capture_output=True,env=env,timeout=130,creationflags=0x08000000 if os.name=='nt' else 0)
        r.save(folder/'result.json',{'exitcode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
          'sources':{f.name:r.sha(f) for f in [HERE/'session_local.ts',HERE/'session_transport.mjs',pathlib.Path(__file__)]},'hosted_calls':0})
        print(json.dumps({'evidence':str(folder),'exitcode':p.returncode,'result':p.stdout.strip()}))
        return p.returncode
    finally:
        if getattr(r.ServerBoundary,'cluster',None):r.ServerBoundary.tearDownClass()
if __name__=='__main__':sys.exit(main())
