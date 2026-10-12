"""Unchanged 45 product assertions through the six-command native transport."""
import hashlib,json,os,pathlib,subprocess,sys,time
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport_v1'))
import native_local as n
r=n.r
class EndchainRequests(n.NativeRequests):
    def invoke(self,request,role,rid):
        i={'member':1,'trainer':2,'b':3}[role]
        claims={'sub':r.uid(i),'session_id':r.uid(i+100),'iss':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',
          'aud':'authenticated','role':'authenticated','exp':int(time.time())+3600}
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','DENO_DIR','USERPROFILE')}
        command=[os.environ['FMZ_DENO'],'run','--cached-only','--no-config','--frozen','--no-prompt',
          '--lock='+str(n.HERE/'native.lock'),'--allow-net=127.0.0.1:'+str(r.ServerBoundary.cluster.port),
          '--allow-read='+str(self.ca),'--allow-env',str(HERE/'native_local_driver.ts')]
        try:
            p=subprocess.run(command,
              input=json.dumps({'input':request,'claims':claims,'request_id':rid,'ca':str(self.ca),'port':r.ServerBoundary.cluster.port}),
              env=env,encoding='utf8',capture_output=True,timeout=25,creationflags=0x08000000 if os.name=='nt' else 0)
        except subprocess.TimeoutExpired as e:
            decode=lambda v:v.decode(errors='replace') if isinstance(v,bytes) else v
            r.save(self.folder/('native-timeout-'+str(self.serial)+'.json'),{
                'phase':'local_process_watchdog','seconds':25,'stdout':decode(e.stdout),'stderr':decode(e.stderr),
                'hosted_calls':0,'automatic_retry':False})
            raise r.Stop('native_process_watchdog')
        r.save(self.folder/('native-command-'+str(self.serial)+'.json'),{
            'exitcode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'local_synthetic_only':True})
        if p.returncode:raise r.Stop('native_endchain_driver_failed')
        value=json.loads(p.stdout)
        if value['commands']!=6 or not value['separate_seal']:raise r.Stop('command_shape')
        return value['receipt']
def main():
    r.enable_local_tls=n.local_ca_and_leaf;r.existing.Workflow=EndchainRequests
    code=r.existing.main()
    if code==0:
        r.save(r.LAST.folder/'endchain-native-result.json',{'status':'LOCAL_NATIVE_ENDCHAIN_45_PASS',
          'pairs':len(r.LAST.pairs),'request_commands':270,'previous_shape':360,'saved_commands':90,
          'm41':r.sha(r.M41),'m42':r.sha(r.M42),'hosted_admitted':False,'auth':'local stubs only',
          'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'request_transport.mjs',HERE/'native_local_driver.ts',pathlib.Path(__file__)]}})
    return code
if __name__=='__main__':sys.exit(main())
