"""Prove the exact libpq command-tag issue and unchanged transaction adapter on PG17."""
import json
import pathlib
import sys
import jit_diagnose as d
from local_cluster import Cluster


def main():
    cluster=Cluster();db=tx=ledger=None
    result={'hosted_calls':0,'tests':0,'status':'NO_GO'}
    try:
        for name in ('old','new','error'):(cluster.path/name).mkdir()
        db=cluster.start()
        if db.query("select current_setting('server_version_num')")[0][0]!='170006':raise RuntimeError('pg17_required')
        db.query('BEGIN TRANSACTION READ ONLY')
        try:
            db.query('SHOW transaction_read_only')
            raise RuntimeError('expected_terminal_row_count')
        except d.m.Stop as error:
            if str(error)!='terminal_row_count':raise
            result['original_failure']='terminal_row_count';result['tests']+=1
        # The existing transaction adapter drains libpq results before rollback.
        s=d.m.stream.t.old.s
        ledger=d.m.Ledger(cluster.path/'old-ledger',lock_scope=cluster.path/'old-lock')
        tx=s.Transaction(db,cluster.path/'old',ledger)
        if not tx.rollback()['confirmed']:raise RuntimeError('drain_rollback')
        result['tests']+=1;ledger.close();ledger=None;tx=None
        ledger=d.m.Ledger(cluster.path/'new-ledger',lock_scope=cluster.path/'new-lock')
        tx=s.Transaction(db,cluster.path/'new',ledger)
        tx.command(s.BEGIN,'begin')
        tx.transaction=s.identity(tx.command(s.CHECK,'read_only_check'))
        result['transaction']=tx.transaction;result['tests']+=1
        meta=tx.command('/* fmz6e11:qv1:local_meta */ select current_database(),current_user','metadata')
        if meta!=[['postgres','postgres']]:raise RuntimeError('local_metadata')
        result['tests']+=1
        if not tx.rollback()['confirmed']:raise RuntimeError('corrected_rollback')
        result['tests']+=1;tx=None;ledger.close();ledger=None
        # A SQL failure must also roll back and leave no partial local writes.
        ledger=d.m.Ledger(cluster.path/'error-ledger',lock_scope=cluster.path/'error-lock')
        tx=s.Transaction(db,cluster.path/'error',ledger)
        tx.command(s.BEGIN,'begin');tx.transaction=s.identity(tx.command(s.CHECK,'check'))
        try:tx.command('/* fmz6e11:qv1:local_injected */ select 1/0','injected')
        except d.m.Stop as error:
            if str(error)!='sqlstate_22012':raise
        else:raise RuntimeError('sql_error_expected')
        if not tx.rollback()['confirmed']:raise RuntimeError('error_rollback')
        result['tests']+=1;tx=None;ledger.close();ledger=None
        result.update(status='LOCAL_PG17_METADATA_PASS',postgres='17.6',source_sha256=d.hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
            diagnostic_sha256=d.hashlib.sha256((d.HERE/'jit_diagnose.py').read_bytes()).hexdigest())
    finally:
        if tx and tx.rollback_result is None:tx.rollback()
        if ledger:ledger.close()
        if db:db.close()
        cluster.stop()
        d.m.save(cluster.path/'metadata-result.json',result)
    print(json.dumps({**result,'evidence':str(cluster.path/'metadata-result.json')}))


if __name__=='__main__':main()
