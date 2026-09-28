"""Single migration-aware M42 application with paired efficient read-only streams."""
import hashlib,importlib.util,json,pathlib,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'migration_cursor_v2'))
spec=importlib.util.spec_from_file_location('retained_m41_cursor_install',HERE.parent/'migration_cursor_v2/install.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
d=old.d;c=old.canary;p=old.p;ROOT=old.ROOT
from guard import Ledger,Stop,save,digest
M42='20260928120846_phase6e11_request_binding.sql';VERSION=M42.split('_')[0]
CI=ROOT/'supabase/.temp/phase6e11-ci42-b8a0240c7df84466a7095d130b81fa0a/run-36423073344'
LOCAL=ROOT/'supabase/.temp/phase6e11-workflow-local-a51734e39df247a29694bd453b8056b1'
SECURITY=ROOT/'supabase/.temp/phase6e11-request-security-4fb275b9fa374f60a705dfd1c43547f3'
NEW='fmz6e11_request_private'
TAG='/* fmz6e11:qv1:request_v4_migration */\n'
REGISTRY=TAG+"""select jsonb_build_object(
 'relations',(select coalesce(jsonb_agg(to_jsonb(r) order by table_name),'[]') from fmz6e11_audit_private.relations r),
 'targets',(select coalesce(jsonb_agg(n.nspname||'.'||z.relname order by n.nspname||'.'||z.relname),'[]') from pg_class z
 join pg_namespace n on n.oid=z.relnamespace where z.relkind='r' and n.nspname in ('public','fmz6e11_private')),
 'observers',(select coalesce(jsonb_agg(jsonb_build_object('table',r.table_name,'enabled',t.tgenabled,
 'function',t.tgfoid::regprocedure::text) order by r.table_name),'[]') from fmz6e11_audit_private.relations r
 left join pg_trigger t on t.tgrelid=r.rel and t.tgname='fmz6e11_tx_observer'),
 'managed_observers',(select count(*) from pg_trigger t join pg_class z on z.oid=t.tgrelid
 join pg_namespace n on n.oid=z.relnamespace where n.nspname in ('auth','storage','realtime') and t.tgname='fmz6e11_tx_observer')
)::text"""
ACL=TAG+"""select jsonb_build_object(
 'schemas',(select count(*) from unnest(array['anon','authenticated','service_role']) r
 where has_schema_privilege(r,'fmz6e11_request_private','usage')),
 'functions',(select jsonb_agg(jsonb_build_object('name',p.proname,'definer',p.prosecdef,'config',p.proconfig,
 'public',exists(select 1 from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a where a.grantee=0 and a.privilege_type='EXECUTE'),
 'clients',exists(select 1 from unnest(array['anon','authenticated','service_role']) r where has_function_privilege(r,p.oid,'execute'))))
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e11_request_private'),
 'tables',(select jsonb_agg(jsonb_build_object('name',z.relname,'rls',z.relrowsecurity,
 'clients',exists(select 1 from unnest(array['anon','authenticated','service_role']) r where has_table_privilege(r,z.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')),
 'public',exists(select 1 from aclexplode(coalesce(z.relacl,acldefault('r',z.relowner))) a where a.grantee=0)))
 from pg_class z join pg_namespace n on n.oid=z.relnamespace where n.nspname='fmz6e11_request_private' and z.relkind='r'),
 'control',(select jsonb_build_object('enabled',enabled,'expires_at',expires_at) from fmz6e11_request_private.control where id),
 'receipts',(select count(*) from fmz6e11_request_private.receipts))::text"""

def plans(inventory,names=None):
    actual=[s+'.'+t for s,t,_ in inventory]
    if len(actual)!=len(set(actual)) or sum(int(n) for _,_,n in inventory)>128*1024*1024:raise Stop('inventory_budget')
    if names is None:
        if len(actual)!=153 or any(x.startswith(NEW+'.') for x in actual):raise Stop('before_inventory')
        names=actual
    elif set(actual)!=set(names)|{NEW+'.control',NEW+'.receipts'}:raise Stop('after_inventory')
    return [{'name':n,'cohorts':{'protected':'true'}} for n in names]

def query(plan):
    parts=[]
    for i,item in enumerate(plan):
        name=item['name'];table='.'.join(p.m.identifier(n) for n in name.split('.'))
        where='true'
        if name=='cron.job_run_details':where='false'
        elif name=='supabase_migrations.schema_migrations':where="version <> '"+VERSION+"'"
        elif name=='fmz6e11_audit_private.relations':where="table_name !~ '^(public|fmz6e11_private)[.]'"
        parts.append(f"select {i}::text,{p.m.ROW_HASH},'1'::text from {table} t where {where}")
    return TAG+' union all '.join(parts)

def history(meta):
    local=[f.stem.split('_',1) for f in sorted((ROOT/'supabase/migrations').glob('*.sql'))]
    actual=[[r['version'],r['name']] for r in meta['migrations']]
    if len(local)!=42 or local[-1][0]!=VERSION or actual not in (local[:-1],local):raise Stop('history_identity')
    return len(actual),local

def capture(connect,token,folder,names=None,bindings=None):
    folder.mkdir();ledger=Ledger(folder/'ledger',lock_scope=folder/'cycle-lock');db=tx=None
    result={'status':'incomplete'}
    try:
        ledger.begin_cycle();db=c.Connection(connect,token,c.CA);tx=d.HostedCursor(db,folder,ledger);tx.start_readonly()
        meta=json.loads(tx.command(TAG+p.jit.META_SQL,'project')[0][0])
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['database']!='postgres' or meta['role']!='postgres' or meta['read_only']!='on' or meta['pg_version']!='170006':raise Stop('project_binding')
        count,_=history(meta)
        numeric=d.base.decode(tx.measured(d.discovery_sql(),'cli_numeric'),d.base.STAT_COLUMNS,['statements','stats_info','background','health'])
        inventory=tx.command(TAG+p.m.INVENTORY,'inventory');plan=plans(inventory,names);sql=query(plan)
        registry=json.loads(tx.measured(REGISTRY,'registry')[0][0])
        if registry['managed_observers']:raise Stop('managed_observer_exists')
        catalog=tx.measured(TAG+p.m.CATALOG,'catalog')
        if bindings is None:
            prior=json.loads((old.CANARY/'after/identity.json').read_text())['bindings']
            bindings={n:({'queryid':None,'sql_sha256':hashlib.sha256(command.encode()).hexdigest()} if n=='declare' else prior[n])
              for n,command in [('declare',d.t.declare_sql(sql)),('fetch',d.t.fetch_sql(8192)),('close',d.t.CLOSE)]}
        save(folder/'manifest.json',{'sources':d.adapter.sources(),'migration_sha256':c.sha(ROOT/'supabase/migrations'/M42),
          'runner_sha256':c.sha(pathlib.Path(__file__)),'query':sql,'query_sha256':hashlib.sha256(sql.encode()).hexdigest(),
          'plan':plan,'canonical':d.t.CANONICAL,'algorithm':d.t.ALGORITHM,
          'exclusions':{'cron.job_run_details':'unchanged historical scheduler-log exclusion',
            'supabase_migrations.schema_migrations':'only exact M42 registration',
            'fmz6e11_audit_private.relations':'new application observer rows validated individually in registry pair'}})
        transfer=tx.transfer(sql,plan,8192,bindings)
        observed={}
        for name,command in [('declare',d.t.declare_sql(sql)),('fetch',d.t.fetch_sql(8192)),('close',d.t.CLOSE)]:
            matching=[v for v in tx.discovered.values() if v['sql_sha256']==hashlib.sha256(command.encode()).hexdigest()]
            observed[name]=matching[0] if matching else bindings[name]
            if observed[name]['queryid'] is None:raise Stop('transport_binding')
        if count==42:
            raw=json.loads(tx.measured(p.HISTORY,'history')[0][0]);save(folder/'history.json',raw)
            p.m.exact_statement_partition((ROOT/'supabase/migrations'/M42).read_text(),raw[-1]['statements'])
            acl=json.loads(tx.measured(ACL,'request_acl')[0][0]);save(folder/'acl.json',acl)
            if acl['schemas'] or len(acl['functions'])!=5 or len(acl['tables'])!=2 or acl['receipts'] or acl['control']!={'enabled':False,'expires_at':None}:raise Stop('request_acl_shape')
            if any(f['definer'] or f['public'] or f['clients'] or f['config']!=['search_path=pg_catalog, pg_temp'] for f in acl['functions']):raise Stop('request_function_acl')
            if any(not t['rls'] or t['clients'] or t['public'] for t in acl['tables']):raise Stop('request_table_acl')
        io=tx.close_proof()
        result.update(status='complete',tables=transfer['tables'],rows=transfer['rows'],catalog=catalog,registry=registry,
           metadata=meta,history_count=count,cli_numeric=numeric,io=io,bindings=observed,
           query_sha256=hashlib.sha256(sql.encode()).hexdigest(),transaction=tx.transaction)
    except Exception as e:
        result.update(reason=str(e) if isinstance(e,Stop) else type(e).__name__,phase=tx.phase if tx else 'connection',
                      pending_pair=tx.pending if tx else None)
    finally:
        if tx:
            result['rollback']=tx.rollback()
            if not result['rollback']['confirmed']:result['status']='incomplete'
        if db:db.close()
        result['query_commands']=ledger.queries
        save(folder/'identity.json',result);ledger.close()
    return result

def compare(before,after):
    if before['tables']!=after['tables'] or before['query_sha256']!=after['query_sha256']:raise Stop('protected_data_drift')
    oldcat={(k,n):h for k,n,h in before['catalog']};newcat={(k,n):h for k,n,h in after['catalog']}
    if any(newcat.get(k)!=v for k,v in oldcat.items()):raise Stop('existing_catalog_drift')
    targets=set(before['registry']['targets'])
    additions=[(k,n) for k,n in newcat if (k,n) not in oldcat]
    for kind,name in additions:
        if name.startswith(NEW+'.') or kind=='schema' and name==NEW:continue
        if kind=='trigger' and name.endswith('.fmz6e11_tx_observer') and name.rsplit('.',1)[0] in targets:continue
        raise Stop('unexpected_catalog_addition')
    rb={r['table_name']:r for r in before['registry']['relations']};ra={r['table_name']:r for r in after['registry']['relations']}
    if any(ra.get(k)!=v for k,v in rb.items()) or set(ra)!=set(rb)|targets:raise Stop('registry_drift')
    if before['registry']['targets']!=after['registry']['targets'] or after['registry']['managed_observers']:raise Stop('registry_scope')
    if len(after['registry']['observers'])!=len(ra) or any(
      r['enabled']!='O' or r['function']!='fmz6e11_audit_private.observe()' for r in after['registry']['observers']):
        raise Stop('observer_definition')
    return {'protected_data_unchanged':True,'protected_tables':len(before['tables']),'new_observer_rows':len(ra)-len(rb),
      'catalog_additions':additions,'managed_observers':0,'local_migrations':42,'hosted_migrations':42}

def admission():
    ci=json.loads((CI/'result.json').read_text())
    if ci['status']!='CLEAN_CI_PASS' or ci['clean_rebuild']!='42/42_PASS' or ci['dry_run']!='EMPTY':raise Stop('CI42_required')
    manifest=json.loads((CI/'candidate.json').read_text())['sources']
    for name,h in manifest.items():
        if c.sha(ROOT/name)!=h:raise Stop('CI_source_changed')
    local=json.loads((LOCAL/'request-v4-result.json').read_text())
    security=json.loads((SECURITY/'request-security.json').read_text())
    if local['pairs']!=45 or local['m42']!=c.sha(ROOT/'supabase/migrations'/M42) or security['count']!=33 or any(not x['pass'] for x in security['tests']):raise Stop('local_admission')
    return {'ci_result':c.sha(CI/'result.json'),'migration_sha256':local['m42'],'local_pairs':45,'negative_tests':33}

def main():
    admitted=admission();folder=ROOT/'supabase/.temp'/('phase6e11-m42-'+uuid.uuid4().hex);folder.mkdir()
    first=ROOT/'supabase/.temp/phase6e11-m42-owner-go-consumed.json'
    marker=first
    if first.exists():
        previous=ROOT/'supabase/.temp'/json.loads(first.read_text())['folder']
        prior_result=json.loads((previous/'result.json').read_text())
        prior_pair=json.loads((previous/'before/identity.json').read_text())
        if (prior_result.get('reason')!='before_unregistered_readonly_query' or prior_result.get('migration_applied')
          or not prior_result.get('jit_revoked') or prior_pair.get('query_commands')!=5
          or not prior_pair.get('rollback',{}).get('confirmed')):
            raise Stop('no_hosted_repeat_admitted')
        marker=ROOT/'supabase/.temp/phase6e11-m42-querylabel-correction-consumed.json'
    save(marker,{'folder':folder.name,'automatic_retry':False})
    save(folder/'contract.json',{**admitted,'collectors':1,'full_cycles':2,'query_limit_per_cycle':128,
      'cli_apply_reservation':32,'cli_dry_reservation':8,'automatic_retries':0,'application_writes':0,
      'expected_new_tables':[NEW+'.control',NEW+'.receipts'],'control_enabled':False,'managed_table_writes':False})
    connect=json.loads((c.CONNECT/'connect.json').read_text());token=p.jit.sb.credential();c.parameters(connect,token,c.CA)
    parent=None;result={'status':'NO_GO','phase':'lease','folder':str(folder),'migration_applied':False,'workflow_calls':0}
    try:
        parent=Ledger(folder/'action-ledger');c.jit_access.lease(token,folder)
        result['phase']='before';before=capture(connect,token,folder/'before')
        if before['status']!='complete' or before['history_count']!=41:raise Stop('before_'+before.get('reason','history'))
        parent.event('before_saved',identity_sha256=digest(before))
        for _ in range(32):parent.reserve_query()
        result['phase']='migration';parent.event('action_started',migration_sha256=admitted['migration_sha256'])
        applied=old.prior.cli_run(old.CLI,connect,c.CA,token,False);save(folder/'cli-apply.json',applied)
        result['migration_applied']=applied['exit_code']==0;parent.event('action_confirmed',receipt_sha256=digest(applied))
        result['phase']='after';after=capture(connect,token,folder/'after',[x['name'] for x in before['tables']],before['bindings'])
        if after['status']!='complete':raise Stop('after_'+after.get('reason','incomplete'))
        parent.event('after_saved',identity_sha256=digest(after))
        if after['history_count']!=42 or applied['exit_code'] or applied.get('migration_files')!=[M42]:raise Stop('migration_or_history')
        pair=compare(before,after);save(folder/'pair.json',pair);parent.event('pair_validated',receipt_sha256=digest(pair))
        load=old.cli_load(before['cli_numeric'],after['cli_numeric']);save(folder/'cli-load.json',load)
        result['phase']='dryrun'
        for _ in range(8):parent.reserve_query()
        dry=old.prior.cli_run(old.CLI,connect,c.CA,token,True);save(folder/'cli-dryrun.json',dry)
        if dry['exit_code'] or dry.get('migration_files') or not dry.get('up_to_date'):raise Stop('dryrun_not_empty')
        parent.event('next_step_allowed')
        result.update(status='M42_PAIRED_PASS_WORKFLOW_PENDING',preservation=pair,dry_run_empty=True,
          measurement_queries=[before['query_commands'],after['query_commands']],cli_query_reservation=40)
    except Exception as e:
        result['reason']=str(e) if isinstance(e,Stop) else type(e).__name__
        if parent:parent.event('halt',reason=result['reason'],cleanup_allowed=False)
    finally:
        if parent:parent.close()
        if (folder/'lease-request.json').exists():
            try:c.revoke(token,folder);result['jit_revoked']=True
            except Exception as e:result.update(status='NO_GO',jit_revoked=False,revocation_error=type(e).__name__)
        token=None;save(folder/'result.json',result)
    print(json.dumps(result));return result['status']=='M42_PAIRED_PASS_WORKFLOW_PENDING'
if __name__=='__main__':sys.exit(0 if main() else 2)
