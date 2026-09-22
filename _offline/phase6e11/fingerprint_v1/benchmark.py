"""Reproducible synthetic benchmark. No cloud credentials, cleanup or network service."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid
from guard import Ledger, Stop, digest, encoded, save
from fingerprint import collect, configure, legacy_sql, plan, SCHEMA_SQL, SETTINGS, Reducer, stream_sql
from local_cluster import Cluster, EXPECTED, SELECTION, process_counters
from pq import LocalDB

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def worker(port, directory, ledger_path, method):
    directory=pathlib.Path(directory)
    g=Ledger(ledger_path);db=LocalDB(int(port),g)
    try:
        pid=int(db.query('select pg_backend_pid()')[0][0])
        client_before=process_counters(os.getpid());server_before=process_counters(pid)
        identity,metrics=collect(db,g,directory/'cycle',EXPECTED,SELECTION,method)
        server_after=process_counters(pid);client_after=process_counters(os.getpid())
        metrics.update(method=method,identity_sha256=digest(identity),
                       client_before=client_before,client_after=client_after,
                       server_before=server_before,server_after=server_after)
        save(directory/'worker.json',metrics)
    finally:
        db.close();g.close()


def stats(db):
    db.query('select pg_stat_clear_snapshot()')
    row=db.query('select temp_bytes,temp_files,blks_read,blks_hit from pg_stat_database where datname=current_database()')[0]
    return dict(zip(('temp_bytes','temp_files','shared_blocks_read','shared_blocks_hit'),map(int,row)))


def transition_probe(db, directory):
    # Both interpretations read the same repeatable-read source transaction.
    configure(db);schema=db.query(SCHEMA_SQL);plans=plan(schema,SELECTION,EXPECTED)
    db.query("select set_config('TimeZone','America/New_York',true)")
    old={plans[int(i)]['name']:json.loads(c) for i,c in db.query(legacy_sql(plans))}
    db.query("select set_config('TimeZone','UTC',true)")
    reducer=Reducer(plans,directory/'transition-chunks')
    for row in db.rows(stream_sql(plans)):reducer.add(row)
    new=reducer.finish(db.terminal_count)
    db.query('commit')
    record={'version':'synthetic-transition-demonstration-v1','same_repeatable_read_snapshot':True,
            'dataset_identity':digest({'schema':schema,'canonical_tables':new}),
            'old_canonical':{**SETTINGS,'TimeZone':'America/New_York'},
            'new_canonical':SETTINGS,'historical_baseline_replaced':False,
            'tables':[{'name':x['name'],'old':old[x['name']],'new':x['cohorts']} for x in new]}
    record['changed_tables']=[x['name'] for x in record['tables'] if x['old']!=x['new']]
    if not record['changed_tables']:raise Stop('timezone_difference_not_demonstrated')
    save(directory/'transition.json',record)
    return {'manifest_sha256':digest(record),'changed_tables':record['changed_tables'],
            'dataset_identity':record['dataset_identity']}


def main():
    source_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
    cluster=Cluster();report={'version':1,'scope':'synthetic local PostgreSQL only',
        'run_id':str(uuid.uuid4()),'hosted_calls':0,'external_ai_calls':0,'deleted_files':0,'results':[]}
    try:
        db=cluster.start();cluster.fixture(db)
        transition=cluster.path/'transition';transition.mkdir()
        report['transition']=transition_probe(db,transition)
        cluster.enlarge(db)
        report['fixture']={'tables':143,'bulk_rows':100000,'catalog_products':25000,'catalog_names':75000,
                           'source_version':'synthetic-fixture-v1'}
        report['postgres_version']=db.query("select version()")[0][0]
        report['cluster']=str(cluster.path)
        for method in ('legacy','stream','stream'):
            output=cluster.path/('bench-'+str(len(report['results'])));output.mkdir()
            before=stats(db)
            started=time.monotonic()
            result=subprocess.run([sys.executable,str(HERE/'benchmark.py'),'--worker',str(cluster.port),
                                   str(output),str(cluster.path/'benchmark-ledger'),method],
                                  capture_output=True,timeout=180,
                                  creationflags=0x08000000 if os.name=='nt' else 0)
            if result.returncode:
                raise Stop('benchmark_worker_failed')
            time.sleep(0.15)
            after=stats(db)
            measured=json.loads((output/'worker.json').read_text())
            measured['wall_seconds_including_worker']=time.monotonic()-started
            measured['database_counter_delta']={k:after[k]-before[k] for k in before}
            report['results'].append(measured)
        identities=[x['identity_sha256'] for x in report['results']]
        if len(set(identities))!=1:raise Stop('benchmark_identity_mismatch')
        report['byte_identical']=True
        if source_hashes != {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}:
            raise Stop('source_changed_during_benchmark')
        report['source_hashes']=source_hashes
        report['complete_cycles']={'benchmark':3,'small_transition_comparison':2}
        report['pass']=True
    except BaseException as error:
        report['pass']=False
        report['failure_type']=str(error) if isinstance(error,Stop) else type(error).__name__
    finally:
        if 'db' in locals():db.close()
        cluster.stop()
        target=ROOT/'supabase/.temp'/('phase6e11-fingerprint-benchmark-'+report['run_id']+'.json')
        save(target,report)
        print(json.dumps({'report':str(target),**report}))
    if not report['pass']:raise SystemExit(1)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        worker(*sys.argv[2:])
    else:
        main()
