"""LOCALONLY pre-GoTrue-start reduction on the actual disposable B stack.

No validator exception, hosted equivalence, patch-freshness or WAL claim. The
restriction remains until disposable teardown; this module never restores it.
The root must admit setup and safety costs independently of the 2349 body.
"""
import copy
import inspect
import json
import pathlib
import sys
import weakref

import admission_journal as durable
import admission_binding
import admission_module_binding as binding
import fixture_cleanup_runtime as engine
import fixture_producer_scope as scope
from native_runtime import NativeRuntime

PREFIX = 'registered-auth-runtime-profile'
ALTER = 'ALTER ROLE supabase_auth_admin NOCREATEROLE'
ROLE_FIELDS = ('name','oid','superuser','inherit','createrole','createdb','login',
               'replication','bypassrls','connlimit','validuntil','config')
META = """select jsonb_build_object(
 'cluster_id',(select system_identifier::text from pg_control_system()),
 'datid',(select oid::int from pg_database where datname=current_database()),
 'pid',pg_backend_pid(),'postmaster_start',pg_postmaster_start_time()::text,
 'pg17',current_setting('server_version_num')::int/10000=17,
 'ssl',coalesce((select ssl from pg_stat_ssl where pid=pg_backend_pid()),false),
 'bounded',current_setting('statement_timeout') in ('5s','5000ms')
 and current_setting('lock_timeout') in ('1s','1000ms'),
 'postgres',current_user='postgres' and current_database()='postgres',
 'origin',current_setting('session_replication_role')='origin',
 'readonly',current_setting('transaction_read_only')='on',
 'no_prepared',current_setting('max_prepared_transactions')='0',
 'tracked',current_setting('track_activities')='on',
 'external',exists(select 1 from pg_stat_activity where
 datid=(select oid from pg_database where datname=current_database())
 and pid<>pg_backend_pid()),
 'roles',(select coalesce(jsonb_agg(v),'[]'::jsonb) from (
 select rolname::text name,oid::int oid,rolsuper superuser,rolinherit inherit,
 rolcreaterole createrole,rolcreatedb createdb,rolcanlogin login,rolreplication replication,
 rolbypassrls bypassrls,rolconnlimit connlimit,rolvaliduntil::text validuntil,rolconfig config
 from pg_roles order by oid limit 257) v),
 'memberships',(select coalesce(jsonb_agg(v),'[]'::jsonb) from (
 select roleid::int roleid,member::int member,grantor::int grantor,
 admin_option,inherit_option,set_option from pg_auth_members
 order by roleid,member,grantor limit 257) v)) value"""
PLAN = (('begin','BEGIN'),('before_metadata',META),('before_privileges',scope.PRIVILEGES),
        ('restrict',ALTER),('after_metadata',META),('commit','COMMIT'),
        ('witness_begin','BEGIN TRANSACTION READ ONLY'),('witness_metadata',META),
        ('witness_privileges',scope.PRIVILEGES),('witness_rollback','ROLLBACK'))
LIMIT = 11
_ATTEMPTED = weakref.WeakKeyDictionary()


def require(value, reason):
    if not value: raise engine.Blocked('auth_runtime_profile_'+reason)


def command_register():
    return {'scope':'LOCALONLY_DISPOSABLE_SETUP', 'normal_sql':10, 'sql_limit':LIMIT,
        'commands':[{'id':'auth.profile.'+phase,'sql_sha256':durable.sha(text.encode()),
                     'sql_commands':1} for phase,text in PLAN],
        'failure_command':{'id':'auth.profile.failure_rollback','sql_commands':1,
                           'sql_sha256':durable.sha(b'ROLLBACK')},
        'connections':2, 'driver_implicit_sql_bound':None,
        'observer_suspend_reconnect':'separate_B_dispatches',
        'managed_compatibility_cost':'separate_actual_Auth_trace_required',
        'placement':'before_managed_stats_baseline_and_before_gotrue_start',
        'hosted_equivalence':False, 'wal_classification':'UNPROVEN_SETUP_DDL',
        'postgres_image_upgrade':False, 'privilege_validator_exception':False}


def metadata(rows, isolation, *, readonly):
    require(type(rows) is list and len(rows)==1 and set(rows[0])=={'value'}, 'metadata_shape')
    v=rows[0]['value']
    require(type(v) is dict and v.get('cluster_id')==isolation['pg_system_identifier']
        and v.get('datid')==isolation['database_oid']
        and all(v.get(k) is True for k in ('pg17','ssl','bounded','postgres','origin','no_prepared','tracked'))
        and v.get('external') is False and v.get('readonly') is readonly
        and type(v.get('pid')) is int and v['pid']>0
        and type(v.get('postmaster_start')) is str, 'target_or_session')
    for key in ('roles','memberships'):
        require(type(v.get(key)) is list and len(v[key])<=256, 'metadata_bound')
    require(v['roles'] and all(type(r) is dict and set(r)==set(ROLE_FIELDS) for r in v['roles']),
            'role_shape')
    require(len({r['oid'] for r in v['roles']})==len(v['roles'])
            and len({r['name'] for r in v['roles']})==len(v['roles']), 'role_duplicate')
    for r in v['roles']:
        require(type(r['oid']) is int and type(r['connlimit']) is int and
            all(type(r[k]) is bool for k in ('superuser','inherit','createrole','createdb','login',
                                           'replication','bypassrls')), 'role_types')
    require(sum(r['name']=='supabase_auth_admin' for r in v['roles'])==1, 'target_role')
    keys=('roleid','member','grantor','admin_option','inherit_option','set_option')
    require(all(type(r) is dict and set(r)==set(keys) and
        all(type(r[k]) is int for k in keys[:3]) and all(type(r[k]) is bool for k in keys[3:])
        for r in v['memberships']), 'membership_shape')
    require(len({(r['roleid'],r['member'],r['grantor']) for r in v['memberships']})==len(v['memberships']),
            'membership_duplicate')
    return copy.deepcopy(v)


def privileges(rows, *, before):
    require(type(rows) is list and len(rows)==4 and {r.get('role') for r in rows}==
            {'supabase_auth_admin','anon','authenticated','service_role'}, 'privilege_roles')
    for row in rows:
        require(set(row)=={'role',*scope.PRIVILEGE_FLAGS}, 'privilege_shape')
        for flag in scope.PRIVILEGE_FLAGS:
            expected=before and row['role']=='supabase_auth_admin' and flag=='createrole'
            require(row.get(flag) is expected, 'unexpected_privilege')


def delta(before, after, *, fresh):
    expected=copy.deepcopy(before)
    target=next(r for r in expected['roles'] if r['name']=='supabase_auth_admin')
    require(target['createrole'] is True, 'initial_capability')
    target['createrole']=False
    if fresh:
        require(after['pid']!=before['pid'], 'independent_backend')
        expected['pid']=after['pid']
        expected['readonly']=True
    require(after==expected, 'not_exact_one_field_reduction')


def before_start(server):
    require(server.start_attempted is False and server.container_id is None
            and server.auth is None and server.started_stats is None,
            'gotrue_started_during_profile')


def evidence_refs(journal, index, root):
    """Exact originals for B/D archive replay, including lossless packaging."""
    root=binding.checked_path(root)
    names={}
    for name,entry in journal.entries.items():
        relative=(journal.folder/name).relative_to(root).as_posix()
        names[relative]=entry
    for name in [*index['chunks'],journal.prefix+'-index.json']:
        require(name not in names,'evidence_alias')
        names[name]=None
    result=[]
    for name,expected in sorted(names.items()):
        path=binding.checked_path(root/name)
        require(path.is_relative_to(root) and path.stat().st_size<=durable.MAX_PACKAGED_BYTES,'evidence_path')
        raw=path.read_bytes()
        actual={'path':name,'sha256':durable.sha(raw),'bytes':len(raw)}
        require(len(raw)<=durable.MAX_PACKAGED_BYTES and (expected is None or
            all(actual[k]==expected[k] for k in ('sha256','bytes'))),'evidence_changed')
        result.append(actual)
    return result


def observation_rows(phase, rows):
    require(type(rows) is list and len(rows) <= 257,'observation_bound')
    result=copy.deepcopy(rows)
    if phase.endswith('_metadata'):
        fields={'cluster_id','datid','pid','postmaster_start','pg17','ssl','bounded','postgres',
                'origin','readonly','no_prepared','tracked','external','roles','memberships'}
        membership={'roleid','member','grantor','admin_option','inherit_option','set_option'}
        for row in result:
            require(type(row) is dict and set(row)=={'value'} and type(row['value']) is dict
                    and set(row['value'])==fields,'observation_fields')
            value=row['value']
            require(all(type(value[k]) is bool for k in ('pg17','ssl','bounded','postgres','origin',
                'readonly','no_prepared','tracked','external')),'observation_boolean')
            require(type(value['roles']) is list and len(value['roles'])<=257
                and type(value['memberships']) is list and len(value['memberships'])<=257,
                'observation_metadata_bound')
            for role in value['roles']:
                require(type(role) is dict and set(role)==set(ROLE_FIELDS),'observation_role_fields')
                require(all(type(role[k]) is bool for k in ('superuser','inherit','createrole',
                    'createdb','login','replication','bypassrls')),'observation_role_boolean')
                if role['config'] is not None:
                    require(type(role['config']) is list and len(role['config'])<=256
                        and all(type(v) is str for v in role['config']),'observation_config')
                    raw=json.dumps(role['config'],sort_keys=True,separators=(',', ':'),allow_nan=False).encode()
                    role['config']={'redacted':True,'sha256':durable.sha(raw),
                                    'bytes':len(raw),'count':len(role['config'])}
            require(all(type(r) is dict and set(r)==membership for r in value['memberships']),
                    'observation_membership_fields')
    elif phase.endswith('_privileges'):
        require(all(type(r) is dict and set(r)=={'role',*scope.PRIVILEGE_FLAGS} for r in result),
                'observation_privilege_fields')
        require(all(type(r[k]) is bool for r in result for k in scope.PRIVILEGE_FLAGS),
                'observation_privilege_boolean')
    else:
        require(phase in dict(PLAN) or phase=='failure_rollback','observation_phase')
        require(not result,'observation_unexpected_rows')
    raw=json.dumps(result,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()
    require(len(raw)<=800000,'observation_bytes')
    return result


def _execute(owner, journal, unchanged, *, runtime=None, isolation=None, source_binding=None):
    runtime = owner.runtime if runtime is None else runtime
    isolation = owner.isolation if isolation is None else isolation
    events=[]
    seen=set()
    phases=dict(PLAN)
    def charge(event):
        phase=event['phase']
        text='ROLLBACK' if phase=='failure_rollback' else phases.get(phase)
        require(phase not in seen and len(events)<LIMIT and text is not None
                and event['sql_sha256']==durable.sha(text.encode()), 'dispatch_bound')
        seen.add(phase)
        unchanged()
        journal.save('charge-%02d.json'%(len(events)+1),event)
        events.append(copy.deepcopy(event))
    protocol=engine.Protocol(charge)
    raw=None
    began=commit_attempted=commit_confirmed=False
    error=None
    result={'status':'NO_GO','scope':'LOCALONLY_DISPOSABLE_SETUP','capability_reduced':False,
        'commit_unknown':False,'hosted_admitted':False,'hosted_equivalence':False,
        'security_freshness_claim':False,'privilege_validator_exception':False,
        'actual_auth_compatibility_proven':False,'full_chain_admission':False,
        'wal_classification':'UNPROVEN_SETUP_DDL','automatic_restore':False}
    def query(phase,text,args=()):
        def execute():
            rows=protocol.execute(raw,phase,text,args)
            event=copy.deepcopy(protocol.events[-1])
            exported=observation_rows(phase,rows)
            journal.save('query-%02d-%s.json'%(event['ordinal'],phase),{
                'format':'c-query-observation-v1','component':'auth_runtime_profile',
                'case_run':getattr(owner,'binding',{}).get('run_id'),
                'scope_sha256':engine.digest(isolation),'source_binding':source_binding,
                'phase':phase,'protocol':event,'rows':exported,'rows_sha256':engine.digest(exported),
                'raw_rows_sha256':engine.digest(rows),
                'projection':'technical-fields-v1-role-config-digest',
                'query_io':{'observed':False,'reason':'not_instrumented_by_this_dispatch'}})
            return rows
        return owner._local_call('profile.'+phase,'native_sql',execute)
    def connect(phase):
        connection=owner._local_call('profile.'+phase,'connection',runtime.connect)
        require(connection.autocommit is True,'autocommit')
        return connection
    def close(phase):owner._local_call('profile.'+phase,'connection_close',raw.close)
    try:
        raw=connect('connect');began=True
        query('begin','BEGIN')
        before=metadata(query('before_metadata',META),isolation,readonly=False)
        privileges(query('before_privileges',scope.PRIVILEGES,[list(scope.SCHEMAS)]),before=True)
        require(next(r for r in before['roles'] if r['name']=='supabase_auth_admin')['createrole'] is True,
                'initial_capability')
        journal.save('intent.json',{'metadata_sha256':engine.digest(before),
            'source_program':command_register(),'restriction':'NOCREATEROLE',
            'no_auth_create_dispatched':True})
        query('restrict',ALTER)
        after=metadata(query('after_metadata',META),isolation,readonly=False)
        delta(before,after,fresh=False)
        journal.save('precommit.json',{'before_sha256':engine.digest(before),
            'after_sha256':engine.digest(after),'exact_one_field_reduction':True})
        commit_attempted=True
        query('commit','COMMIT');commit_confirmed=True;began=False
        close('close');raw=None
        raw=connect('witness_connect');began=True
        query('witness_begin','BEGIN TRANSACTION READ ONLY')
        witness=metadata(query('witness_metadata',META),isolation,readonly=True)
        delta(before,witness,fresh=True)
        privileges(query('witness_privileges',scope.PRIVILEGES,[list(scope.SCHEMAS)]),before=False)
        journal.save('witness.json',{'metadata_sha256':engine.digest(witness),
            'all_eight_privilege_checks_false':True,'independent_committed_observation':True})
        began=False
        query('witness_rollback','ROLLBACK')
        result.update(status='LOCALONLY_RUNTIME_CAPABILITY_REDUCED',capability_reduced=True)
    except BaseException as caught:error=caught
    finally:
        result['commit_unknown']=commit_attempted and not commit_confirmed
        if raw is not None:
            if began and not result['commit_unknown']:
                try:query('failure_rollback','ROLLBACK')
                except BaseException as caught:
                    if error is None:error=caught
                    else:error.add_note('profile_rollback_secondary:'+type(caught).__name__)
            try:close('final_close')
            except BaseException as caught:
                if error is None:error=caught
                else:error.add_note('profile_close_secondary:'+type(caught).__name__)
    if error is not None:
        result.update(status='NO_GO',capability_reduced=False,error_class=type(error).__name__)
    result.update(commit_confirmed=commit_confirmed,protocol=copy.deepcopy(protocol.events),
                  emitted_attempts=len(protocol.events),reserved_commands=LIMIT)
    return result,error


def run(server):
    from quota_candidate_v1.runtime_registered_bootstrap import Context
    from quota_candidate_v1.runtime_registered_startup import LocalServer
    frame=inspect.currentframe().f_back
    require(type(server) is LocalServer and frame.f_code is LocalServer.open.__code__
            and frame.f_locals.get('self') is server,'actual_startup_caller')
    del frame
    owner=server.owner
    before_start(server)
    require(owner not in _ATTEMPTED and owner._entering and owner._admitted
        and not owner._yielded and not owner._seed_attempted and owner.producer is None
        and owner.auth is None and type(owner) is Context and owner.server is server
        and type(server.runtime) is NativeRuntime and server.runtime.environment=='disposable_ci'
        and server.db is not None and not server.db.closed, 'before_gotrue_start')
    _ATTEMPTED[owner]=True
    modules=[sys.modules[__name__],binding,durable,engine,scope,
             admission_binding,sys.modules[scope.parser.__module__],
             sys.modules[engine.parameters.__module__],
             sys.modules[Context.__module__],sys.modules[LocalServer.__module__],
             sys.modules[NativeRuntime.__module__]]
    source=binding.verify(owner.gate,modules)
    require(owner.stack['status']=='CLEAN47_BOOTSTRAP_PASS'
        and owner.stack['scope']=='DISPOSABLE_CI_ONLY'
        and owner.stack['container']['id']==server.pg['Id']
        and owner.stack['auth_database_bound'] is False
        and server.parameters['host']==server.parameters['hostaddr']=='127.0.0.1'
        and server.parameters['sslmode']=='verify-full'
        and str(server.parameters['connect_timeout'])=='5'
        and durable.sha(pathlib.Path(server.parameters['sslrootcert']).read_bytes())==owner.stack['ca_sha256'],
        'owned_local_stack')
    isolation={'pg_system_identifier':owner.stack['pg_system_identifier'],
               'database_oid':owner.stack['database_oid']}
    def unchanged():
        owner._validate()
        require(not journal.poisoned,'journal_poisoned')
        journal._inventory()
        for name,ref in journal.entries.items():journal._read(name,ref)
        require(owner.producer is None and owner.auth is None and not owner._seed_attempted,
                'mint_before_profile_finished')
        before_start(server)
        require(binding.verify(owner.gate,modules)==source,'source_changed')
    journal=durable.Journal(pathlib.Path(owner.gate.out)/(PREFIX+'-private'),owner.gate.save,PREFIX+'-journal')
    journal.save('binding.json',{'source_binding':source,'case_run':owner.binding['run_id'],
        'target_sha256':engine.digest(isolation),'scope':'LOCALONLY_DISPOSABLE_SETUP',
        'before_gotrue_start':True,'future_credential_exclusivity_claim':False})
    result = {'status':'NO_GO','capability_reduced':False,'hosted_equivalence':False}
    error = None
    try:
        with server.suspend():
            result,error=_execute(owner,journal,unchanged,runtime=server.runtime,isolation=isolation,
                                  source_binding=source)
            if error is not None:raise error
    except BaseException as caught:
        error=caught
        result.update(status='NO_GO',capability_reduced=False,error_class=type(caught).__name__)
    try:
        journal.save('result.json',result)
        index=journal.seal()
    except BaseException as secondary:
        if error is None:raise
        error.add_note('profile_final_evidence_secondary:'+type(secondary).__name__)
    if error is not None:raise error
    return {'receipt':result,'ref':{'path':(journal.folder/'result.json').relative_to(owner.gate.out).as_posix(),
                                   'sha256':journal.entries['result.json']['sha256']},
            'evidence_refs':evidence_refs(journal,index,owner.gate.out)}
