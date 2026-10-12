"""Local regression receipt; no Supabase or GitHub call, no credential loading."""
import hashlib,json,os,pathlib,re,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def main():
    folder=ROOT/'supabase/.temp'/('phase6e11-controller-followup-'+uuid.uuid4().hex);folder.mkdir()
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','FMZ_LOCAL_PG_BIN','FMZ_NODE')}
    env['PYTHONDONTWRITEBYTECODE']='1'
    commands=[('node',[os.environ['FMZ_NODE'],'--test','--test-reporter=tap',*[str(p) for p in sorted(HERE.glob('*.test.mjs'))]])]
    # Legacy adapters insert same-named test directories into sys.path. A fresh
    # interpreter per module prevents discovery from importing a different file.
    commands += [('python_'+p.stem,[sys.executable,'-B',str(p),'-v']) for p in sorted(HERE.glob('test_*.py'))]
    commands += [('local_guard',[sys.executable,'-B',str(HERE/'local_auth_guard.py')])]
    results=[]
    for name,cmd in commands:
        p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=120,creationflags=0x08000000)
        output=p.stdout+p.stderr
        save(folder/(name+'.json'),{'exit':p.returncode,'output':output,'hosted_calls':0})
        count=re.search(r'# tests (\d+)',output) if name=='node' else re.search(r'Ran (\d+) tests',output)
        item={'suite':name,'exit':p.returncode,'tests':int(count[1]) if count else None}
        if name=='local_guard' and p.returncode==0:
            local=json.loads(p.stdout);item.update(checks=local['checks'],limitations=local['limitations'],evidence=local['evidence'])
        results.append(item)
        if p.returncode:break
    unchanged=all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h for n,h in sources.items())
    result={'status':'LOCAL_FOLLOWUP_PASS_HOSTED_AUTH_NOT_ADMITTED' if all(r['exit']==0 for r in results) and len(results)==len(commands) and unchanged else 'NO_GO',
        'sources':sources,'unchanged':unchanged,'tests':results,'hosted_calls':0,'owner_review_ready':False}
    save(folder/'local-tests.json',result)
    print(json.dumps({'folder':str(folder),'status':result['status'],'tests':results}))
    return 0 if result['status'].startswith('LOCAL_FOLLOWUP_PASS') else 2
if __name__=='__main__':sys.exit(main())
