"""Bounded independent PG17 diagnostic; never hosted admission or causal PASS.

Each immutable interval closes its read transaction before coverage/classification.
pg_stat_statements attribution is to a query fingerprint, not to WAL record owners.
"""
import hashlib,ipaddress,json,os,pathlib,re,time,uuid
from integral_ci import bind_parameters
from lifecycle_gates import ACCESS,MIGRATIONS,CATALOG,ABSENCE
from integral_io import SNAPSHOT,check_plan
from integral_stream import statement,CONFIG,PAGE

MAX_COMMANDS=80
MAX_WAL_BYTES=65536
MAX_RECORDS=512
MAX_BLOCKS=512
WAIT_MS=300
QUERY_NAMES=('access','migrations','catalog','absence','snapshot','rowhash')
FAMILIES=QUERY_NAMES
ROLES={'a_member','a_trainer','b_member'}
ROW_HASH='select * from ('+statement([{
    'name':'supabase_migrations.schema_migrations','predicate':'true'}])+') diagnostic_hashes limit '+str(PAGE+1)
PREFLIGHT="""select current_setting('statement_timeout') statement_timeout,
 current_setting('lock_timeout') lock_timeout,
 current_setting('fsync')::boolean fsync,
 current_setting('server_version_num')::int version,
 current_setting('transaction_read_only') readonly,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 exists(select 1 from pg_available_extensions where name='pg_walinspect') available,
 (select n.nspname from pg_extension e join pg_namespace n on n.oid=e.extnamespace
  where e.extname='pg_walinspect') installed_schema,
 to_regnamespace('extensions') is not null target_schema"""
START="""select pg_current_wal_insert_lsn()::text start_lsn,
 current_setting('transaction_read_only')='on' readonly"""
END="""select pg_current_wal_insert_lsn()::text end_lsn,
 current_setting('transaction_read_only')='on' readonly"""
COVERAGE="select pg_current_wal_flush_lsn()::text flush_lsn"
WAIT="select pg_sleep(0.3)"
# This differs structurally from the measured SNAPSHOT, avoiding self-subtraction.
STATS="""select jsonb_build_object(
 'track',current_setting('pg_stat_statements.track'),
 'reset',(select stats_reset from extensions.pg_stat_statements_info),
 'dealloc',(select dealloc from extensions.pg_stat_statements_info),
 'rows',(select coalesce(jsonb_agg(jsonb_build_object(
   'queryid',queryid::text,'since',stats_since,'calls',calls,
   'wal_bytes',wal_bytes::text,'wal_records',wal_records,'wal_fpi',wal_fpi,
   'temp_read',temp_blks_read,'temp_written',temp_blks_written)),'[]')
 from extensions.pg_stat_statements(false)
 where dbid=(select oid from pg_database where datname=current_database())
 and userid=(select oid from pg_roles where rolname=current_user)
 and toplevel and queryid::text=$1),
 'database',(select jsonb_build_object('temp_bytes',temp_bytes,'reset',stats_reset)
 from pg_stat_database where datname=current_database()),
 'other_active',(select count(*) from pg_stat_activity
 where datname=current_database() and pid<>pg_backend_pid() and state='active')) value"""
# No current-insert LSN, sleep, flush operation, row payload or raw object ID export.
# Object classes describe the CURRENT catalog mapping, never historical identity.
INSPECT="""with bounds as materialized(select %s::pg_lsn lo,%s::pg_lsn hi),
 records as materialized(
 select start_lsn,end_lsn,resource_manager,record_type
 from {schema}.pg_get_wal_records_info((select lo from bounds),(select hi from bounds))
 limit 513),
 blocks as materialized(
 select start_lsn,end_lsn,reldatabase,reltablespace,relfilenode
 from {schema}.pg_get_wal_block_info((select lo from bounds),(select hi from bounds),false)
 limit 513),
 record_groups as(
 select resource_manager rmgr,record_type,count(*) records
 from records group by resource_manager,record_type),
 mapped as(
 select case
 when b.reldatabase=0 then 'shared_relation'
 when b.reldatabase<>(select oid from pg_database where datname=current_database())
 then 'other_database'
 when n.nspname='pg_catalog' then 'current_pg_catalog'
 when n.nspname='pg_toast' then 'current_pg_toast'
 when n.oid is not null then 'current_non_catalog_relation'
 else 'unresolved' end object_class
 from blocks b left join pg_class c on c.oid=case
 when b.reldatabase in(0,(select oid from pg_database where datname=current_database()))
 then pg_filenode_relation(b.reltablespace,b.relfilenode) end
 left join pg_namespace n on n.oid=c.relnamespace),
 object_groups as(select object_class,count(*) blocks from mapped group by object_class)
 select jsonb_build_object(
 'record_count',(select count(*) from records),
 'block_count',(select count(*) from blocks),
 'outside_records',(select count(*) from records,bounds where start_lsn<lo or end_lsn>hi),
 'outside_blocks',(select count(*) from blocks,bounds where start_lsn<lo or end_lsn>hi),
 'first_lsn',(select min(start_lsn)::text from records),
 'last_lsn',(select max(end_lsn)::text from records),
 'groups',(select coalesce(jsonb_agg(g order by rmgr,record_type),'[]') from record_groups g),
 'object_classes',(select coalesce(jsonb_agg(g order by object_class),'[]') from object_groups g)
 ) technical"""
OBJECT_CLASSES={'shared_relation','other_database','current_pg_catalog','current_pg_toast',
                'current_non_catalog_relation','unresolved'}

class DiagnosticOnlyStop(RuntimeError):pass

def admit(connection,environment,environ,ci_ca_path):
    if (environment!='disposable_ci' or environ.get('GITHUB_ACTIONS')!='true'
        or environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging'
        or environ.get('GITHUB_REF')!='refs/heads/main'
        or environ.get('FMZ6E11_LOCAL_WAL_DIAGNOSTIC')!='1'):
        raise ValueError('wal_diagnostic_ci_only')
    info=connection.info
    if (info.host!='127.0.0.1' or not ipaddress.ip_address(info.hostaddr).is_loopback
        or info.dbname!='postgres' or info.user!='postgres'
        or not 170000<=info.server_version<180000 or not connection.autocommit
        or info.transaction_status!=0):
        raise ValueError('wal_diagnostic_connection_denied')
    parameters=info.get_parameters()
    if parameters.get('options')!='-c statement_timeout=5000 -c lock_timeout=1000':
        raise ValueError('wal_diagnostic_connection_limits')
    if parameters.get('sslmode')!='verify-full' or str(parameters.get('connect_timeout'))!='5':
        raise ValueError('wal_diagnostic_tls_or_connect_limits')
    try:
        expected=pathlib.Path(ci_ca_path);actual=pathlib.Path(parameters.get('sslrootcert'))
        valid=(expected.is_absolute() and actual.is_absolute()
            and expected.name=='fmz-ci-ca.crt' and expected.is_file()
            and actual.resolve(strict=True)==expected.resolve(strict=True))
    except (OSError,ValueError,TypeError,RuntimeError):valid=False
    if not valid:raise ValueError('wal_diagnostic_ci_ca_binding')

def lsn(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9A-F]{1,8}/[0-9A-F]{1,8}',value):
        raise ValueError('wal_diagnostic_lsn_shape')
    high,low=(int(x,16) for x in value.split('/'))
    return (high<<32)+low

def integer(value):
    if type(value) is int and value>=0:return value
    if type(value) is str and re.fullmatch('[0-9]{1,30}',value):return int(value)
    raise ValueError('wal_diagnostic_numeric_shape')

def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                    default=str).encode()).hexdigest()

def stats_delta(before,after,qid):
    if (before['track'] not in ('top','all') or after['track']!=before['track']
        or before['reset']!=after['reset'] or before['dealloc']!=after['dealloc']
        or before['database']['reset']!=after['database']['reset']):
        raise ValueError('wal_diagnostic_statistics_reset')
    def one(value):
        rows=value['rows']
        if not isinstance(rows,list) or len(rows)>1:raise ValueError('wal_diagnostic_stats_ambiguous')
        if rows and rows[0]['queryid']!=qid:raise ValueError('wal_diagnostic_stats_queryid')
        return rows[0] if rows else None
    a=one(before);b=one(after)
    if b is None or a and a['since']!=b['since']:raise ValueError('wal_diagnostic_stats_missing')
    keys=('calls','wal_bytes','wal_records','wal_fpi','temp_read','temp_written')
    old={k:integer(a[k]) if a else 0 for k in keys}
    new={k:integer(b[k]) for k in keys}
    delta={k:new[k]-old[k] for k in keys}
    if min(delta.values())<0 or delta['calls']!=1:raise ValueError('wal_diagnostic_stats_calls')
    background=integer(after['database']['temp_bytes'])-integer(before['database']['temp_bytes'])
    if background<0:raise ValueError('wal_diagnostic_statistics_reset')
    return dict(queryid=qid,scope='same_database_user_toplevel_query_fingerprint_not_backend',
        reliable=True,delta=delta,before_counters=old,after_counters=new,
        baseline_absent=a is None,track=before['track'],
        stats_reset_sha256=sha(before['reset']),entry_since_sha256=sha(b['since']),
        dealloc=integer(before['dealloc']),before_sha256=sha(before),after_sha256=sha(after),
        background_temp_bytes=background,other_active_before=integer(before['other_active']),
        other_active_after=integer(after['other_active']),continuous_background_observation=False)

def technical_only(value,start,end):
    keys={'record_count','block_count','outside_records','outside_blocks','first_lsn',
          'last_lsn','groups','object_classes'}
    if not isinstance(value,dict) or set(value)!=keys:raise ValueError('wal_diagnostic_shape')
    for key in ('record_count','block_count','outside_records','outside_blocks'):
        if type(value[key]) is not int or value[key]<0:raise ValueError('wal_diagnostic_shape')
    if not 0<value['record_count']<=MAX_RECORDS or value['block_count']>MAX_BLOCKS:
        raise ValueError('wal_diagnostic_record_capacity')
    if value['outside_records'] or value['outside_blocks']:
        raise ValueError('wal_diagnostic_outside_interval')
    # Conservative exact-tail condition. Gaps/padding are not guessed into coverage.
    if not lsn(start)<=lsn(value['first_lsn'])<lsn(end) or lsn(value['last_lsn'])!=lsn(end):
        raise ValueError('wal_diagnostic_record_tail_incomplete')
    groups=value['groups'];objects=value['object_classes']
    if not isinstance(groups,list) or not isinstance(objects,list) or len(groups)>MAX_RECORDS or len(objects)>6:
        raise ValueError('wal_diagnostic_shape')
    for row in groups:
        if set(row)!={'rmgr','record_type','records'} or type(row['records']) is not int or row['records']<1:
            raise ValueError('wal_diagnostic_shape')
        if any(not isinstance(row[k],str) or not re.fullmatch('[A-Za-z0-9_ /+-]{1,96}',row[k])
               for k in ('rmgr','record_type')):raise ValueError('wal_diagnostic_shape')
    for row in objects:
        if set(row)!={'object_class','blocks'} or row['object_class'] not in OBJECT_CLASSES or type(row['blocks']) is not int or row['blocks']<1:
            raise ValueError('wal_diagnostic_shape')
    if sum(x['records'] for x in groups)!=value['record_count'] or sum(x['blocks'] for x in objects)!=value['block_count']:
        raise ValueError('wal_diagnostic_group_count')
    return {**value,'object_mapping_scope':'inspection_time_catalog_not_interval_object_proof',
            'record_owner_attribution':False}

def families(ids,context):
    if set(ids)!=ROLES or len(set(ids.values()))!=3:raise ValueError('wal_diagnostic_identity_scope')
    people=[str(uuid.UUID(ids[r])) for r in sorted(ROLES)]
    window=str(uuid.UUID(context['window']));schemas=context['temporary_schemas']
    if (not isinstance(schemas,list) or len(schemas)!=2 or len(set(schemas))!=2
        or not any(re.fullmatch('fmz6e11_guard_[a-f0-9]{32}',s) for s in schemas)
        or not any(re.fullmatch('fmz6e11_am_[a-f0-9]{32}',s) for s in schemas)):
        raise ValueError('wal_diagnostic_schema_scope')
    return (('access',ACCESS,[people]),('migrations',MIGRATIONS,[]),
        ('catalog',CATALOG,[schemas]),('absence',ABSENCE,[schemas,people,window]),
        ('snapshot',SNAPSHOT,['[]']),('rowhash',ROW_HASH,[]))

def run(connection,*,environment,ids,context,ci_ca_path,environ=None):
    admit(connection,environment,os.environ if environ is None else environ,ci_ca_path)
    queries=families(ids,context)
    result=dict(version=2,status='DIAGNOSTIC_ONLY',outcome='INCOMPLETE',
        full_chain_admission=False,wal_zero_pass=False,causal_attribution=False,
        scope='fixed_cluster_intervals_and_separate_query_fingerprint_counters',
        queries=[],commands=0,command_cap=MAX_COMMANDS,command_ledger=[],limitations=[],
        extension_installed=False,row_contents_exported=False,query_text_exported=False,
        rollback_confirmed=False,automatic_retries=0,wait_ms=0,
        measured_executions_per_family=1,warmup_executions=0,
        planning='counted_explain_without_analyze_before_first_execution',
        historical_cause='UNKNOWN',hosted_read_wal_limit_unchanged=0,
        max_wait_ms_per_query=WAIT_MS,max_total_wait_ms=WAIT_MS*len(FAMILIES),
        families=list(FAMILIES),rowhash_scope='bounded_migration_history_expression_not_full_cursor_cycle')
    opened=False;family='bootstrap';phase='preflight';item=None
    def execute(sql,args=(),label=''):
        nonlocal phase
        phase=label
        if result['commands']>=MAX_COMMANDS-(1 if opened and sql!='ROLLBACK' else 0):
            raise ValueError('wal_diagnostic_command_limit')
        row=dict(number=result['commands']+1,family=family,phase=label,commands=1,
            sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),confirmed=False)
        result['command_ledger'].append(row);result['commands']+=1
        cursor=connection.execute(sql,args);row['confirmed']=True
        return cursor
    def idle():
        if connection.info.transaction_status!=0:raise ValueError('wal_diagnostic_transaction_not_closed')
    def rollback():
        nonlocal opened
        # A lost rollback response is not authorization to retry it.
        opened=False
        execute('ROLLBACK',label='rollback');idle()
        if item is not None:item['rollback_confirmed']=True
    try:
        p=execute(PREFLIGHT,label='preflight').fetchone()
        if (p['statement_timeout'] not in ('5s','5000ms') or p['lock_timeout'] not in ('1s','1000ms')
            or not 170000<=p['version']<180000 or p['readonly']!='off' or p['ssl'] is not True
            or p.get('fsync') is not True):
            raise ValueError('wal_diagnostic_server_limits')
        result['fsync_attested']=True
        schema=p['installed_schema']
        if schema is None:
            if not p['available'] or not p['target_schema']:
                result['limitations'].append('pg_walinspect_unavailable');return result
            execute('CREATE EXTENSION pg_walinspect WITH SCHEMA extensions',label='extension_install')
            schema='extensions';result['extension_installed']=True
        if schema not in ('extensions','public','pg_catalog'):
            result['limitations'].append('pg_walinspect_schema_not_supported');return result
        stats_sql,stats_params=bind_parameters(STATS,['0'])
        reader=check_plan(execute('EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+stats_sql,
                                 stats_params,label='stats_reader_binding').fetchone()['QUERY PLAN'])
        seen={reader}
        for family,source,args in queries:
            item=dict(name=family,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                start_lsn=None,end_lsn=None,complete=False,coverage_complete=False,
                rollback_confirmed=False,outcome='INCOMPLETE',limitations=[],coverage_checks=[],wait_ms=0)
            result['queries'].append(item)
            sql,params=bind_parameters(source,args)
            qid=check_plan(execute('EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+sql,
                                  params,label='query_binding').fetchone()['QUERY PLAN'])
            if qid in seen:raise ValueError('wal_diagnostic_queryid_collision')
            seen.add(qid)
            stats_sql,stats_params=bind_parameters(STATS,[qid])
            before=execute(stats_sql,stats_params,label='stats_before').fetchone()['value']
            opened=True;execute('BEGIN TRANSACTION READ ONLY',label='begin')
            if family=='rowhash':execute(CONFIG,label='rowhash_configuration_outside_interval')
            start=execute(START,label='start').fetchone()
            if start['readonly'] is not True:raise ValueError('wal_diagnostic_transaction_not_readonly')
            lsn(start['start_lsn']);item['start_lsn']=start['start_lsn']
            begin=time.monotonic()
            cursor=execute(sql,params,label='measured_query')
            item['duration_ms']=round((time.monotonic()-begin)*1000)
            # The end query is immediate; never wait/classify inside the measured transaction.
            end=execute(END,label='end').fetchone()
            if end['readonly'] is not True:raise ValueError('wal_diagnostic_transaction_not_readonly')
            item['end_lsn']=end['end_lsn'];span=lsn(end['end_lsn'])-lsn(start['start_lsn'])
            item['span_bytes']=span
            rollback()
            if family=='rowhash':
                hashes=cursor.fetchall()
                if len(hashes)>PAGE:raise ValueError('wal_diagnostic_rowhash_capacity')
                item['hash_rows_discarded']=len(hashes);del hashes
            after=execute(stats_sql,stats_params,label='stats_after').fetchone()['value']
            try:item['query_stats']=stats_delta(before,after,qid)
            except (ValueError,KeyError,TypeError):
                item['query_stats']={'reliable':False,'before_sha256':sha(before),'after_sha256':sha(after)}
                item['limitations'].append('query_statistics_unconfirmed')
            if span<0 or span>MAX_WAL_BYTES:
                item['limitations'].append('wal_interval_capacity')
                continue
            idle()
            flush=execute(COVERAGE,label='coverage').fetchone()['flush_lsn']
            item['coverage_checks'].append({'flush_lsn':flush,'covers_end':lsn(flush)>=lsn(item['end_lsn'])})
            if lsn(flush)<lsn(item['end_lsn']):
                idle();item['wait_ms']=WAIT_MS;result['wait_ms']+=WAIT_MS
                execute(WAIT,label='coverage_wait_outside_transaction')
                idle();flush=execute(COVERAGE,label='coverage_after_wait').fetchone()['flush_lsn']
                item['coverage_checks'].append({'flush_lsn':flush,'covers_end':lsn(flush)>=lsn(item['end_lsn'])})
            item['flush_lsn']=flush
            if lsn(flush)<lsn(item['end_lsn']):
                item['limitations'].append('wal_not_flushed_through_fixed_end')
                continue
            item['coverage_complete']=True
            if span:
                idle()
                raw=execute(INSPECT.format(schema='"'+schema+'"'),
                    [item['start_lsn'],item['end_lsn']],label='classify_fixed_interval').fetchone()['technical']
                try:item['technical']=technical_only(raw,item['start_lsn'],item['end_lsn'])
                except (ValueError,KeyError,TypeError):
                    item['limitations'].append('record_coverage_or_shape_unconfirmed')
                    continue
            else:item['technical']={'record_count':0,'block_count':0,'groups':[],
                    'object_classes':[],'record_owner_attribution':False}
            stats=item['query_stats']
            if stats['reliable']:
                delta=stats['delta']
                item['query_family_wal_nonzero']=any(delta[k] for k in ('wal_bytes','wal_records','wal_fpi'))
                if delta['temp_written'] or delta['temp_read'] or stats['background_temp_bytes']:
                    item['limitations'].append('temporary_io_nonzero')
                if not span and item['query_family_wal_nonzero']:
                    item['limitations'].append('cluster_query_statistics_inconsistent')
            item['complete']=not item['limitations']
            if item['complete'] and span==0:item['outcome']='WAL_ZERO'
            elif item['complete']:
                # Classification is complete; ownership/benignness is NOT proven.
                item['limitations'].append('record_owner_attribution_unproven')
    except Exception as error:
        result['limitations'].append('pg_walinspect_install_unavailable' if phase=='extension_install' else 'probe_unconfirmed')
        result['error_class']=type(error).__name__
        if item is not None:item['complete']=False
    finally:
        if opened:
            try:rollback()
            except Exception as error:
                result['limitations'].append('rollback_unconfirmed')
                result['rollback_error_class']=type(error).__name__
        result['rollback_confirmed']=bool(result['queries']) and all(
            q['rollback_confirmed'] for q in result['queries'])
        for q in result['queries']:
            for limitation in q['limitations']:
                result['limitations'].append(q['name']+':'+limitation)
        result['intervals_complete']=(len(result['queries'])==len(FAMILIES)
            and all(q['complete'] for q in result['queries']) and result['rollback_confirmed'])
        result['diagnostic_complete']=result['intervals_complete'] and not result['limitations']
        if result['diagnostic_complete']:
            result['outcome']='WAL_ZERO'  # Observation only; wal_zero_pass remains false.
    return result

def run_and_stop(connection,save,**kwargs):
    try:receipt=run(connection,**kwargs)
    finally:connection.close()
    save('ci-wal-diagnostic.json',receipt)
    raise DiagnosticOnlyStop('ci_wal_diagnostic_only_not_admission')
