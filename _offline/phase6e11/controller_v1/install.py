"""M43 admission and paired efficient stream. No Auth/application writes."""
import hashlib,importlib.util,json,pathlib,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'request_v4'))
spec=importlib.util.spec_from_file_location('controller_prior_m42_install',HERE.parent/'request_v4/install.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
stream_spec=importlib.util.spec_from_file_location('controller_155_transfer',HERE/'transfer.py')
stream=importlib.util.module_from_spec(stream_spec);stream_spec.loader.exec_module(stream)
d,c,p,ROOT=prior.d,prior.c,prior.p,prior.ROOT
from guard import Ledger,Stop,save,digest
M43='20261012104331_phase6e11_controller_evidence.sql';VERSION=M43.split('_')[0]
NEW='fmz6e11_controller_private';TAG='/* fmz6e11:qv1:controller_m43 */\n'
CI=ROOT/'supabase/.temp/phase6e11-controller-final-local/run-38243722556'
LOCAL=ROOT/'supabase/.temp/phase6e11-workflow-local-e4ba46eb524f4545aa37c0a48da9d2bf'
SECURITY=ROOT/'supabase/.temp/phase6e11-request-security-f1560f6903f34911aeb68be8e516a204'
ACL=TAG+"""select jsonb_build_object(
 'functions',(select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='fmz6e11_controller_private'),
 'client_usage',(select count(*) from pg_namespace n cross join pg_roles r where n.nspname='fmz6e11_controller_private'
 and r.rolname in ('anon','authenticated','service_role') and has_schema_privilege(r.oid,n.oid,'usage')),
 'tables',(select jsonb_agg(jsonb_build_object('name',z.relname,'rls',z.relrowsecurity,
 'clients',exists(select 1 from unnest(array['anon','authenticated','service_role']) r where has_table_privilege(r,z.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')),
 'public',exists(select 1 from aclexplode(coalesce(z.relacl,acldefault('r',z.relowner))) a where a.grantee=0)))
 from pg_class z join pg_namespace n on n.oid=z.relnamespace where n.nspname='fmz6e11_controller_private' and z.relkind='r'),
 'rows',(select count(*) from fmz6e11_controller_private.runs)+(select count(*) from fmz6e11_controller_private.steps)+(select count(*) from fmz6e11_controller_private.evidence))::text"""

def admitted():
    result=json.loads((CI/'result.json').read_text())
    if result['status']!='CLEAN_CI_PASS' or result['clean_rebuild']!='43/43_PASS' or result['controller_security']!='PASS' or result['dry_run']!='EMPTY':raise Stop('ci43_required')
    manifest=json.loads((CI/'candidate.json').read_text())['sources']
    for name,h in manifest.items():
        if c.sha(ROOT/name)!=h:raise Stop('tested_candidate_changed')
    if json.loads((LOCAL/'request-v4-result.json').read_text())['pairs']!=45:raise Stop('local_pairs_missing')
    if json.loads((SECURITY/'request-security.json').read_text())['count']!=33:raise Stop('local_security_missing')
    return {'ci_sha256':c.sha(CI/'result.json'),'migration_sha256':c.sha(ROOT/'supabase/migrations'/M43),
      'local_pairs_sha256':c.sha(LOCAL/'request-v4-result.json'),'local_security_sha256':c.sha(SECURITY/'request-security.json')}

def plan(inventory,names=None):
    actual=[s+'.'+t for s,t,_ in inventory];added={NEW+'.runs',NEW+'.steps',NEW+'.evidence'}
    if len(actual)!=len(set(actual)) or sum(int(n) for _,_,n in inventory)>128*1024*1024:raise Stop('inventory_budget')
    if names is None:
        if any(n.startswith(NEW+'.') for n in actual):raise Stop('controller_already_present')
        names=actual
    elif set(actual)!=set(names)|added:raise Stop('unexpected_table_change')
    return [{'name':n,'cohorts':{'protected':'true'}} for n in names]

def stream_query(plans):
    parts=[]
    for i,item in enumerate(plans):
        name=item['name'];table='.'.join(p.m.identifier(n) for n in name.split('.'));where='true'
        if name=='cron.job_run_details':where='false'
        elif name=='supabase_migrations.schema_migrations':where="version <> '"+VERSION+"'"
        parts.append(f"select {i}::text,{p.m.ROW_HASH},'1'::text from {table} t where {where}")
    return TAG+' union all '.join(parts)

def capture(connect,token,folder,parent,names=None,bindings=None):
    folder.mkdir();db=tx=None;result={'status':'incomplete'}
    class SharedLedger(Ledger):
        def reserve_query(self):
            parent.reserve_query();return super().reserve_query()
    ledger=SharedLedger(folder/'ledger',lock_scope=folder/'cycle-lock')
    try:
        ledger.begin_cycle();db=c.Connection(connect,token,c.CA);tx=stream.ControllerCursor(db,folder,ledger);tx.start_readonly()
        meta=json.loads(tx.command(TAG+p.jit.META_SQL,'project')[0][0])
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['database']!='postgres' or meta['role']!='postgres' or meta['read_only']!='on' or meta['pg_version']!='170006':raise Stop('project_binding')
        local=[f.stem.split('_',1) for f in sorted((ROOT/'supabase/migrations').glob('*.sql'))]
        actual=[[r['version'],r['name']] for r in meta['migrations']]
        if len(local)!=43 or actual not in (local[:-1],local):raise Stop('history_identity')
        count=len(actual)
        # Keep the CLI interval outside both streams: per-FETCH time is not one
        # migration query. This incorporates the retained M42 load reconciliation.
        if names is not None:
            numeric=d.base.decode(tx.measured(d.discovery_sql(),'cli_numeric'),d.base.STAT_COLUMNS,['statements','stats_info','background','health'])
        inventory=tx.command(TAG+p.m.INVENTORY,'inventory');plans=plan(inventory,names);sql=stream_query(plans)
        registry=json.loads(tx.measured(prior.REGISTRY,'registry')[0][0]);catalog=tx.measured(TAG+p.m.CATALOG,'catalog')
        if registry['managed_observers']:raise Stop('managed_observer_exists')
        if bindings is None:
            prior_bindings=json.loads((prior.old.CANARY/'after/identity.json').read_text())['bindings']
            bindings={n:({'queryid':None,'sql_sha256':hashlib.sha256(command.encode()).hexdigest()} if n=='declare' else prior_bindings[n])
              for n,command in [('declare',d.t.declare_sql(sql)),('fetch',d.t.fetch_sql(8192)),('close',d.t.CLOSE)]}
        save(folder/'manifest.json',{'sources':d.adapter.sources(),'migration_sha256':c.sha(ROOT/'supabase/migrations'/M43),
          'runner_sha256':c.sha(pathlib.Path(__file__)),'query':sql,'query_sha256':hashlib.sha256(sql.encode()).hexdigest(),
          'plan':plans,'canonical':d.t.CANONICAL,'algorithm':d.t.ALGORITHM,
          'exclusions':{'cron.job_run_details':'unchanged scheduler-log exclusion','supabase_migrations.schema_migrations':'exact M43 registration only'}})
        transfer=tx.transfer(sql,plans,8192,bindings);observed={}
        if names is None:
            numeric=d.base.decode(tx.measured(d.discovery_sql(),'cli_numeric'),d.base.STAT_COLUMNS,['statements','stats_info','background','health'])
        for name,command in [('declare',d.t.declare_sql(sql)),('fetch',d.t.fetch_sql(8192)),('close',d.t.CLOSE)]:
            matches=[v for v in tx.discovered.values() if v['sql_sha256']==hashlib.sha256(command.encode()).hexdigest()]
            observed[name]=matches[0] if matches else bindings[name]
            if observed[name]['queryid'] is None:raise Stop('transport_binding')
        if count==43:
            raw=json.loads(tx.measured(p.HISTORY,'history')[0][0]);save(folder/'history.json',raw)
            p.m.exact_statement_partition((ROOT/'supabase/migrations'/M43).read_text(),raw[-1]['statements'])
            acl=json.loads(tx.measured(ACL,'request_acl')[0][0]);save(folder/'acl.json',acl)
            if acl['functions'] or acl['client_usage'] or acl['rows'] or {x['name'] for x in acl['tables']}!={'runs','steps','evidence'}:raise Stop('controller_acl_shape')
            if any(not x['rls'] or x['clients'] or x['public'] for x in acl['tables']):raise Stop('controller_acl')
        result.update(status='complete',tables=transfer['tables'],rows=transfer['rows'],catalog=catalog,registry=registry,
          metadata=meta,history_count=count,cli_numeric=numeric,io=tx.close_proof(),bindings=observed,
          query_sha256=hashlib.sha256(sql.encode()).hexdigest(),transaction=tx.transaction)
    except Exception as e:result.update(reason=str(e) if isinstance(e,Stop) else type(e).__name__,phase=tx.phase if tx else 'connection',pending_pair=tx.pending if tx else None)
    finally:
        if tx:
            result['rollback']=tx.rollback()
            if not result['rollback']['confirmed']:result['status']='incomplete'
        if db:db.close()
        result['query_commands']=ledger.queries;save(folder/'identity.json',result);ledger.close()
    return result

def compare(before,after):
    if before['tables']!=after['tables'] or before['query_sha256']!=after['query_sha256']:raise Stop('protected_data_drift')
    a={(k,n):h for k,n,h in before['catalog']};b={(k,n):h for k,n,h in after['catalog']}
    if any(b.get(k)!=v for k,v in a.items()):raise Stop('existing_catalog_drift')
    additions=[(k,n) for k,n in b if (k,n) not in a]
    if any(not (n.startswith(NEW+'.') or k=='schema' and n==NEW) for k,n in additions):raise Stop('unexpected_catalog_addition')
    if before['registry']!=after['registry']:raise Stop('observer_registry_drift')
    return {'protected_data_unchanged':True,'tables':len(before['tables']),'new_catalog':additions,'observers_unchanged':True}

def corrected_admission():
    marker=ROOT/'supabase/.temp/phase6e11-controller-m43-attempt.json'
    if not marker.exists():raise Stop('expected_historical_attempt')
    previous=ROOT/'supabase/.temp'/json.loads(marker.read_text())['folder']
    result=json.loads((previous/'result.json').read_text());before=json.loads((previous/'before/identity.json').read_text())
    if result.get('reason')!='before_plan_shape_budget' or result.get('migration_applied') or not result.get('jit_revoked') or before.get('query_commands')!=18 or not before.get('rollback',{}).get('confirmed'):
        raise Stop('no_corrected_attempt_admitted')
    manifest=json.loads((previous/'before/manifest.json').read_text());stream.check_plan(manifest['plan'])
    return {'original_attempt':previous.name,'original_queries':18,'original_status':'incomplete','original_identity_sha256':c.sha(previous/'before/identity.json')}

def main():
    admission=admitted();folder=ROOT/'supabase/.temp'/('phase6e11-controller-install-'+uuid.uuid4().hex);folder.mkdir()
    historical=corrected_admission()
    save(ROOT/'supabase/.temp/phase6e11-controller-m43-corrected-once.json',{'folder':folder.name,'automatic_retries':0,**historical})
    save(folder/'contract.json',{**admission,'query_cap_per_measurement':128,'cli_reservation':40,'query_cap_total':296,
      'full_cycles':2,'historical_incomplete_cycle':1,**historical,'collectors':1,'application_writes':0,'auth_calls':0,'scope':'migration installation, NOT the 128-command workflow canary'})
    parent=None;token=None;result={'status':'NO_GO','migration_applied':False,'phase':'lease','folder':str(folder)}
    try:
        class InstallLedger(Ledger):MAX_QUERIES=296
        parent=InstallLedger(folder/'action-ledger')
        for _ in range(historical['original_queries']):parent.reserve_query()
        token=p.jit.sb.credential();connect=json.loads((c.CONNECT/'connect.json').read_text());c.parameters(connect,token,c.CA)
        c.jit_access.lease(token,folder)
        # Each retained measurement has its own unchanged 128-command guard;
        # the global lock also covers the separately reserved CLI operations.
        for _ in range(40):parent.reserve_query()
        result['phase']='before';before=capture(connect,token,folder/'before',parent)
        if before['status']!='complete' or before['history_count']!=42:raise Stop('before_'+before.get('reason','history'))
        parent.event('before_saved',identity_sha256=digest(before));result['phase']='migration'
        parent.event('action_started',migration_sha256=admission['migration_sha256'])
        applied=prior.old.prior.cli_run(prior.old.CLI,connect,c.CA,token,False);save(folder/'cli-apply.json',applied)
        result['migration_applied']=applied['exit_code']==0;parent.event('action_confirmed',receipt_sha256=digest(applied))
        result['phase']='after';after=capture(connect,token,folder/'after',parent,[x['name'] for x in before['tables']],before['bindings'])
        if after['status']!='complete':raise Stop('after_'+after.get('reason','incomplete'))
        parent.event('after_saved',identity_sha256=digest(after))
        if after['history_count']!=43 or applied['exit_code'] or applied.get('migration_files')!=[M43]:raise Stop('migration_identity')
        pair=compare(before,after);save(folder/'pair.json',pair);parent.event('pair_validated',receipt_sha256=digest(pair))
        load=prior.old.cli_load(before['cli_numeric'],after['cli_numeric']);save(folder/'cli-load.json',load)
        result['phase']='dry_run';dry=prior.old.prior.cli_run(prior.old.CLI,connect,c.CA,token,True);save(folder/'cli-dryrun.json',dry)
        if dry['exit_code'] or dry.get('migration_files') or not dry.get('up_to_date'):raise Stop('dryrun_not_empty')
        parent.event('next_step_allowed');result.update(status='M43_PAIRED_PASS_CONTROLLER_PENDING',preservation=pair,dry_run_empty=True)
    except Exception as e:result['reason']=str(e) if isinstance(e,Stop) else type(e).__name__
    finally:
        if parent:
            result['cli_reservation']=40
            result['measurement_queries']=[json.loads((folder/n/'identity.json').read_text()).get('query_commands',0)
              for n in ['before','after'] if (folder/n/'identity.json').exists()]
            result['commands_and_cli_reservation']=parent.queries
            parent.close()
        if (folder/'lease-request.json').exists():
            try:c.revoke(token,folder);result['jit_revoked']=True
            except Exception as e:result.update(status='NO_GO',jit_revoked=False,close_error=type(e).__name__)
        token=None;save(folder/'result.json',result)
    print(json.dumps(result));return 0 if result['status']=='M43_PAIRED_PASS_CONTROLLER_PENDING' else 2
if __name__=='__main__':sys.exit(main())
