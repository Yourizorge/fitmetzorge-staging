"""All original 45 contracts + cleanup through one counted HTTP/native session."""
import json, os, pathlib, subprocess, sys, threading, time
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from cleanup_local import CleanupRequests, n, r

class ComposedRequests(CleanupRequests):
    driver=None
    def invoke(self,request,role,rid):
        if self.driver is None:
            env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
            self.driver=subprocess.Popen([os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
                '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
                '--allow-read='+str(self.ca),'--allow-env',str(HERE/'workflow_session_driver.ts')],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf8',env=env,
                creationflags=0x08000000 if os.name=='nt' else 0)
            self.watchdog=threading.Timer(130,self.driver.kill);self.watchdog.start()
            self.driver.stdin.write(json.dumps({'mode':'disposable_local','ca':str(self.ca),'port':r.ServerBoundary.cluster.port})+'\n')
            self.driver.stdin.flush();self.traces=[]
        i={'member':1,'trainer':2,'b':3}[role]
        claims={'sub':r.uid(i),'session_id':r.uid(i+100),'iss':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',
            'aud':'authenticated','role':'authenticated','exp':int(time.time())+300}
        self.driver.stdin.write(json.dumps({'op':'invoke','input':request,'claims':claims,'requestId':rid})+'\n');self.driver.stdin.flush()
        line=self.driver.stdout.readline()
        if not line:raise r.Stop('composed_driver_stopped')
        value=json.loads(line);r.save(self.folder/('composed-command-'+str(self.serial)+'.json'),value)
        if value.get('status')=='NO_GO':raise r.Stop('composed_driver_'+value['phase']+'_'+value['code'])
        self.traces.append(value)
        return value['receipt']
    def close_driver(self):
        if not self.driver:return
        try:
            if self.driver.poll() is None:
                self.driver.stdin.write('{"op":"close"}\n');self.driver.stdin.flush()
            output,error=self.driver.communicate(timeout=5)
            r.save(self.folder/'composed-driver-close.json',{'exitcode':self.driver.returncode,'stdout':output,
                'stderr':error,'sources':{p.name:r.sha(p) for p in [pathlib.Path(__file__),HERE/'workflow_session_driver.ts',
                    HERE/'session_transport.mjs',HERE/'composed_handler.mjs']},'hosted_calls':0})
            if self.driver.returncode:raise r.Stop('composed_driver_exit')
        finally:
            self.watchdog.cancel()
            if self.driver.poll() is None:self.driver.kill();self.driver.communicate(timeout=5)

def main():
    r.enable_local_tls=n.local_ca_and_leaf;r.existing.Workflow=ComposedRequests
    try:return r.existing.main()
    finally:
        if r.LAST and isinstance(r.LAST,ComposedRequests):r.LAST.close_driver()

if __name__=='__main__':sys.exit(main())
