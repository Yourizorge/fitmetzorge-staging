"""Bounded offline test receipt. No staging API, credential or provider access."""
import hashlib,json,os,pathlib,re,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def disk(path):return pathlib.Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path
def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-controller-'):raise RuntimeError('scope')
    sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    tests=sorted(str(p) for p in HERE.glob('*.test.mjs'))
    commands=[('node',[os.environ['FMZ_NODE'],'--require',str(ROOT/'_offline/phase6e12/no_network.cjs'),'--test','--test-reporter=tap',*tests],30)]
    commands += [(name,[sys.executable,'-B',str(HERE/name)],30) for name in ['test_install.py','test_transfer.py','test_lease_trace.py']]
    commands += [('pg17',[sys.executable,'-B',str(HERE/'local_pg17.py')],180)]
    results={}
    for label,command,limit in commands:
        process=subprocess.run(command,cwd=ROOT,encoding='utf8',capture_output=True,timeout=limit,creationflags=0x08000000 if os.name=='nt' else 0)
        result={'exit':process.returncode,'stdout':process.stdout,'stderr':process.stderr}
        if label=='node':
            result.update(tests=int(re.search(r'^# tests (\d+)$',process.stdout,re.M)[1]),passed=int(re.search(r'^# pass (\d+)$',process.stdout,re.M)[1]))
        elif label=='pg17':
            rows=[json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
            result.update(checks=rows[0]['checks'],evidence=rows[-1]['evidence'])
        else:result['tests']=int(re.search(r'Ran (\d+) tests',process.stderr)[1])
        results[label]=result
        if process.returncode:break
    unchanged=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in sources.items())
    value={'status':'LOCAL_PASS' if unchanged and len(results)==len(commands) and all(v['exit']==0 for v in results.values()) else 'NO_GO',
      'sources':sources,'sources_unchanged':unchanged,'results':results,'hosted_calls':0,'auth_calls':0,'provider_calls':0}
    target=disk(folder/('offline-tests-'+uuid.uuid4().hex+'.json'))
    with target.open('x',encoding='utf8') as out:json.dump(value,out,indent=2);out.flush();os.fsync(out.fileno())
    print(json.dumps({'status':value['status'],'file':target.name,'totals':{k:{n:v[n] for n in ['exit','tests','passed','checks'] if n in v} for k,v in results.items()}}))
    return 0 if value['status']=='LOCAL_PASS' else 2
if __name__=='__main__':sys.exit(main())
