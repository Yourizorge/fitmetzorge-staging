"""M43 + additive M44 in a disposable local PG17 cluster, no hosted route."""
import hashlib,json,os,pathlib,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'fingerprint_v1'))
from local_cluster import Cluster
from database_checks import run,M44

def main():
    cluster=Cluster();result={'status':'NO_GO','hosted_calls':0}
    psql=pathlib.Path(os.environ.get('FMZ_PSQL','C:/Program Files/PostgreSQL/18/bin/psql.exe'))
    def sql(q):
        return subprocess.run([str(psql),'-X','-h','127.0.0.1','-p',str(cluster.port),'-U','postgres',
            '-d','postgres','-qAt','-v','ON_ERROR_STOP=1'],input=q,text=True,capture_output=True,
            timeout=20,creationflags=0x08000000 if os.name=='nt' else 0)
    try:
        db=cluster.start();db.close()
        p=sql('create role anon;create role authenticated;create role service_role;')
        if p.returncode:raise RuntimeError('local_roles')
        hashes={}
        for name in ['20261012104331_phase6e11_controller_evidence.sql',M44]:
            path=ROOT/'supabase/migrations'/name;raw=path.read_bytes()
            p=sql(raw.decode('utf-8-sig'))
            if p.returncode:raise RuntimeError('local_migration_'+name)
            hashes[name]=hashlib.sha256(raw).hexdigest()
        result=run(sql);result['sources']=hashes
    except Exception as e:
        result['error']=str(e) if isinstance(e,RuntimeError) else type(e).__name__
    finally:
        cluster.stop()
        with (cluster.path/'single-budget-result.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({**result,'evidence':str(cluster.path/'single-budget-result.json')}))
    return 0 if result['status']=='LOCAL_SINGLE_BUDGET_PASS' else 2
if __name__=='__main__':sys.exit(main())
