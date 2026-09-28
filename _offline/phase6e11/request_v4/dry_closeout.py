"""Metadata-only M42 closure; no fingerprint, application mutation or reapplication."""
import hashlib,json,os,pathlib,re,subprocess,sys,uuid
import load_closeout as l
i=l.i
from guard import Ledger,Stop,save

def dry(connect,token):
    url=i.old.prior.cli_check.connection_url(connect,i.c.CA)
    if 'default_transaction_read_only%3Don' not in url or 'verify-full' not in url:raise Stop('readonly_cli_options')
    env={k:v for k,v in os.environ.items() if not k.startswith('PG')}
    env.update(PGPASSWORD=token,DO_NOT_TRACK='1')
    try:
        proc=subprocess.run([str(i.old.CLI),'db','push','--db-url',url,'--dry-run','--skip-vault','--output-format','json'],
            cwd=i.ROOT,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=30)
        raw=(proc.stdout+proc.stderr).decode('utf-8','replace')
        if token in raw or re.search(r'sbp_[A-Za-z0-9_-]+',raw):raise Stop('secret_not_saved')
        result={'exit_code':proc.returncode,'output_sha256':hashlib.sha256(raw.encode()).hexdigest(),
            'migration_files':sorted(set(re.findall(r'\b[0-9]{14}_[a-z0-9_]+\.sql\b',raw))),
            'up_to_date':'up to date' in raw.lower(),'read_only_connection':True}
        return result
    finally:env.pop('PGPASSWORD',None)

def main():
    corrected=l.verify();i.admission()
    folder=i.ROOT/'supabase/.temp'/('phase6e11-m42-dry-closeout-'+uuid.uuid4().hex);folder.mkdir()
    save(i.ROOT/'supabase/.temp/phase6e11-m42-dry-closeout-consumed.json',{'folder':folder.name})
    save(folder/'saved-load-correction.json',corrected)
    token=i.p.jit.sb.credential();connect=json.loads((i.c.CONNECT/'connect.json').read_text())
    result={'status':'NO_GO','phase':'lease','full_fingerprints':0,'application_writes':0,'folder':str(folder)}
    ledger=db=tx=None
    try:
        ledger=Ledger(folder/'ledger');i.c.jit_access.lease(token,folder)
        db=i.c.Connection(connect,token,i.c.CA);tx=i.d.HostedCursor(db,folder,ledger);tx.start_readonly()
        result['phase']='metadata'
        meta=json.loads(tx.command(i.TAG+i.p.jit.META_SQL,'project')[0][0])
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['read_only']!='on' or i.history(meta)[0]!=42:raise Stop('project_history')
        history=json.loads(tx.measured(i.p.HISTORY,'history')[0][0])
        i.p.m.exact_statement_partition((i.ROOT/'supabase/migrations'/i.M42).read_text(),history[-1]['statements'])
        acl=json.loads(tx.measured(i.ACL,'acl')[0][0]);save(folder/'acl.json',acl)
        previous=json.loads((l.RUN/'after/acl.json').read_text())
        if acl!=previous:raise Stop('acl_changed')
        io=tx.close_proof();save(folder/'io.json',io)
        rollback=tx.rollback();save(folder/'readonly-closure.json',rollback)
        if not rollback['confirmed']:raise Stop('rollback_unconfirmed')
        db.close();db=None;tx=None
        result['phase']='dryrun'
        for _ in range(8):ledger.reserve_query()
        value=dry(connect,token);save(folder/'dryrun.json',value)
        if value['exit_code'] or value['migration_files'] or not value['up_to_date']:raise Stop('dryrun_not_empty')
        result.update(status='M42_INSTALLATION_PASS_WORKFLOW_PENDING',local=42,hosted=42,dry_run='EMPTY',
          migration_sha256=i.c.sha(i.ROOT/'supabase/migrations'/i.M42),
          registered_statements_sha256=hashlib.sha256('\n'.join(history[-1]['statements']).encode()).hexdigest(),
          registered_sql_exact_partition=True,default_control_disabled=True,query_commands_including_cli_reservation=ledger.queries)
    except Exception as e:result['reason']=str(e) if isinstance(e,Stop) else type(e).__name__
    finally:
        if tx:result['rollback']=tx.rollback()
        if db:db.close()
        if ledger:ledger.close()
        if (folder/'lease-request.json').exists():
            try:i.c.revoke(token,folder);result['jit_revoked']=True
            except Exception as e:result.update(status='NO_GO',jit_revoked=False,revocation_error=type(e).__name__)
        token=None;save(folder/'result.json',result)
    print(json.dumps(result));return result['status']=='M42_INSTALLATION_PASS_WORKFLOW_PENDING'

if __name__=='__main__':sys.exit(0 if main() else 2)
