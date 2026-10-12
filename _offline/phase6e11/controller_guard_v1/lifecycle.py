"""Owned DDL lifecycle; safety removal is independent of proof-run admission."""
import hashlib,importlib.util,json,pathlib
spec=importlib.util.spec_from_file_location('identity_guard_sql',pathlib.Path(__file__).with_name('guard.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def ddl_commands(sql):
    """Split only this renderer's two fixed envelopes, not arbitrary SQL."""
    if sql=='ROLLBACK':return [sql]
    for tag in ('install','remove'):
        marker='DO $'+tag+'$'
        if marker not in sql:continue
        prefix,body=sql.split(marker,1)
        tail='END $'+tag+'$;\nCOMMIT;'
        if not body.endswith(tail):raise ValueError('ddl_envelope')
        commands=[p.strip() for p in prefix.split(';') if p.strip()]
        commands += [marker+body[:-len('\nCOMMIT;')],'COMMIT']
        if not commands[0].endswith('BEGIN') or len(commands)!=(6 if tag=='install' else 5):raise ValueError('ddl_envelope')
        return commands
    raise ValueError('ddl_unregistered')

def catalog_sql():
    # Catalog definitions and ACL only; no account, token or application content.
    return """/* fmz6e11:controller_guard_v1:catalog */
select kind,name,encode(sha256(convert_to(body,'UTF8')),'hex') from (
 select 'schema' kind,nspname::text name,jsonb_build_array(nspowner,nspacl)::text body
 from pg_namespace where nspname='auth' or nspname like 'fmz6e11%'
 union all
 select 'relation',n.nspname||'.'||c.relname,jsonb_build_array(c.relowner,c.relacl,c.relrowsecurity,c.relforcerowsecurity)::text
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' or n.nspname like 'fmz6e11%'
 union all
 select 'function',p.oid::regprocedure::text,jsonb_build_array(p.proowner,p.proacl,pg_get_functiondef(p.oid))::text
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where (n.nspname='auth' or n.nspname like 'fmz6e11%') and p.prokind='f'
 union all
 select 'trigger',n.nspname||'.'||c.relname||'.'||t.tgname,jsonb_build_array(t.tgenabled,pg_get_triggerdef(t.oid))::text
 from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' or n.nspname like 'fmz6e11%'
 union all
 select 'policy',n.nspname||'.'||c.relname||'.'||p.polname,to_jsonb(p)::text
 from pg_policy p join pg_class c on c.oid=p.polrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' or n.nspname like 'fmz6e11%'
) s order by kind,name"""

def compare(before,after,schema,installed):
    a={(k,n):h for k,n,h in before};b={(k,n):h for k,n,h in after}
    if len(a)!=len(before) or len(b)!=len(after):raise ValueError('catalog_duplicate_identity')
    if any(b.get(k)!=v for k,v in a.items()):raise ValueError('existing_catalog_changed')
    additions=set(b)-set(a)
    expected={('schema',schema),('function',schema+'.identity_guard()'),
              *(('trigger','auth.users.'+schema+x) for x in ('_i','_u','_d'))}
    if additions!=(expected if installed else set()):raise ValueError('unexpected_catalog_additions')
    return {'existing_objects_equal':True,'existing_objects':len(a),'own_additions':len(additions)}

def execute(*,run,ids,query,read,save,seconds=180,action=None,safety_read=None):
    """query executes owned DDL; read uses a separate explicit RO transaction.

    Attempted install may have committed despite a lost acknowledgment. Inspect
    its unique schema in finally, validate its source, then remove exactly it.
    This path does not rely on the action result or the controller's NO-GO gate.
    """
    schema=g.scope(run,ids);attempted=False;receipt=None;phase='before_saved'
    result={'status':'NO_GO','guard_removed':False,'action_executed':False}
    before=None
    safety_storage=[]
    def state(reader):return json.loads(reader(g.inspect(run,ids))[0][0])
    safety_read=safety_read or read
    def record(name,value):save(name,value)
    def safety_record(name,value):
        try:record(name,value)
        except Exception:safety_storage.append(name)
    try:
        before=read(catalog_sql());record('before-catalog',before)
        phase='action_started';record('install-started',{'run':run,'sql_sha256':hashlib.sha256(g.install(run,ids,seconds).encode()).hexdigest()})
        attempted=True;query(g.install(run,ids,seconds),7)
        phase='action_confirmed';current=state(read);record('installed-state',current)
        receipt=g.validate(current,run,ids);record('removal-receipt',receipt)
        phase='after_saved';after=read(catalog_sql());record('after-install-catalog',after)
        phase='pair_validated';pair=compare(before,after,schema,True);record('install-pair',pair)
        if action is not None:
            phase='authorized_action';result['action_executed']=True;result['action']=action(receipt)
        result['status']='GUARD_LIFECYCLE_PASS'
    except Exception as error:
        result.update(phase=phase,error_class=type(error).__name__)
        if isinstance(error,ValueError) and str(error).replace('_','').isalnum():result['reason']=str(error)
    finally:
        if attempted:
            try:
                # No repeated mutation. A read establishes whether installation
                # actually committed; rollback of any failed DDL is unconditional.
                query('ROLLBACK',1)
                current=state(safety_read);safety_record('safety-inspection',current)
                if current['functions']:
                    proven=g.validate(current,run,ids,active=False)
                    if receipt is not None and proven!=receipt:raise ValueError('removal_receipt_changed')
                    safety_record('safety-removal-started',proven)
                    query(g.remove(run,ids,proven),5)
                elif current['triggers'] or current['other_relations'] or current['dependencies']:
                    raise ValueError('unknown_guard_objects')
                final=safety_read(catalog_sql());safety_record('after-removal-catalog',final)
                pair=compare(before,final,schema,False);safety_record('removal-pair',pair)
                result.update(guard_removed=True,catalog_restored=True)
            except Exception as error:
                result.update(status='NO_GO',removal_error_class=type(error).__name__,guard_removed=False)
        if safety_storage:result.update(status='NO_GO',missing_safety_evidence=safety_storage)
        try:record('lifecycle-result',result)
        except Exception:result.update(status='NO_GO',result_persistence_failed=True)
    return result
