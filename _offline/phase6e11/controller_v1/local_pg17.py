"""Only disposable local PG17. Never contacts staging or loads credentials."""
import hashlib,json,os,pathlib,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'fingerprint_v1'))
from local_cluster import Cluster
M43=ROOT/'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql'
def main():
    cluster=Cluster();db=None
    files=[HERE/n for n in ['core.mjs','store.mjs','store.pg17.mjs','local_pg17.py']]+[M43]
    sources={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    try:
        db=cluster.start()
        if db.query("select current_setting('server_version_num')")[0][0]!='170006':raise RuntimeError('local_pg17_required')
        psql='C:/Program Files/PostgreSQL/18/bin/psql.exe'
        setup=subprocess.run([psql,'-X','-h','127.0.0.1','-p',str(cluster.port),'-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1'],
          input='create role anon;create role authenticated;create role service_role;'+M43.read_text(),
          capture_output=True,text=True,timeout=20,creationflags=0x08000000)
        if setup.returncode:raise RuntimeError('local_schema_setup_failed')
        env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE')}
        env.update(FMZ_LOCAL_PORT=str(cluster.port),FMZ_LOCAL_PSQL=psql)
        p=subprocess.run([os.environ['FMZ_NODE'],str(HERE/'store.pg17.mjs')],env=env,
          capture_output=True,text=True,timeout=90,creationflags=0x08000000)
        record={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'migration_sha256':hashlib.sha256(M43.read_bytes()).hexdigest(),
          'postgres':'17.6','hosted_calls':0,'cluster':str(cluster.path),'sources':sources,
          'sources_unchanged':all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in sources.items())}
        if not record['sources_unchanged']:raise RuntimeError('local_source_changed')
        (cluster.path/'controller-local.json').write_text(json.dumps(record,indent=2))
        print(p.stdout)
        if p.returncode:print(p.stderr)
        print(json.dumps({'evidence':str(cluster.path/'controller-local.json'),'exit':p.returncode}))
        return p.returncode
    finally:
        if db:db.close()
        cluster.stop()
if __name__=='__main__':sys.exit(main())
