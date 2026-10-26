"""CI-only observation, never admission. No connection creation or hosted transport."""
import hashlib,ipaddress,os,pathlib,re,time,uuid
from integral_ci import bind_parameters
from lifecycle_gates import ACCESS,MIGRATIONS,CATALOG,ABSENCE

MAX_COMMANDS=16
MAX_WAL_BYTES=65536
MAX_RECORDS=512
ROLES={'a_member','a_trainer','b_member'}
PREFLIGHT="""select current_setting('statement_timeout') statement_timeout,
 current_setting('lock_timeout') lock_timeout,
 current_setting('server_version_num')::int version,
 current_setting('transaction_read_only') readonly,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 inet_server_addr()::text server_addr,
 exists(select 1 from pg_available_extensions where name='pg_walinspect') available,
 (select n.nspname from pg_extension e join pg_namespace n on n.oid=e.extnamespace
  where e.extname='pg_walinspect') installed_schema,
 to_regnamespace('extensions') is not null target_schema"""
START="""select pg_current_wal_insert_lsn()::text start_lsn,
 current_setting('transaction_read_only')='on' readonly"""

# Description, raw block references, relation IDs and block data never leave SQL.
INSPECT="""with boundary as materialized(select pg_current_wal_insert_lsn() end_lsn,
 pg_current_wal_flush_lsn() flush_lsn)
 select end_lsn::text end_lsn,flush_lsn::text flush_lsn,
 pg_wal_lsn_diff(end_lsn,%s::pg_lsn)::bigint span_bytes,
 case when flush_lsn>=end_lsn and end_lsn>%s::pg_lsn
 and pg_wal_lsn_diff(end_lsn,%s::pg_lsn)<=65536 then (
  with records as materialized(
   select start_lsn,resource_manager,record_type
   from {schema}.pg_get_wal_records_info(%s::pg_lsn,boundary.end_lsn) limit 513),
  blocks as materialized(
   select start_lsn,count(*) blockcount
   from {schema}.pg_get_wal_block_info(%s::pg_lsn,boundary.end_lsn,false)
   group by start_lsn),
  groups as(
   select r.resource_manager rmgr,r.record_type,count(*) records,
    sum(coalesce(b.blockcount,0))::bigint blockcount
   from records r left join blocks b using(start_lsn)
   group by r.resource_manager,r.record_type)
  select jsonb_build_object('record_count',(select count(*) from records),
   'groups',(select coalesce(jsonb_agg(g order by rmgr,record_type),'[]') from groups g))
 ) else null end technical
 from boundary"""

class DiagnosticOnlyStop(RuntimeError):
    pass

def admit(connection,environment,environ,ci_ca_path):
    if (environment!='disposable_ci' or environ.get('GITHUB_ACTIONS')!='true'
        or environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging'
        or environ.get('GITHUB_REF')!='refs/heads/main'
        or environ.get('FMZ6E11_LOCAL_WAL_DIAGNOSTIC')!='1'):
        raise ValueError('wal_diagnostic_ci_only')
    info=connection.info
    # Check the effective numeric peer, not just a hostname or caller mode.
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
        expected=pathlib.Path(ci_ca_path)
        actual=pathlib.Path(parameters.get('sslrootcert'))
        valid=(expected.is_absolute() and actual.is_absolute()
            and expected.name=='fmz-ci-ca.crt' and expected.is_file()
            and actual.resolve(strict=True)==expected.resolve(strict=True))
    except (OSError,ValueError,TypeError,RuntimeError):
        valid=False
    if not valid:raise ValueError('wal_diagnostic_ci_ca_binding')

def technical_only(value):
    if set(value)!={'record_count','groups'} or type(value['record_count']) is not int:
        raise ValueError('wal_diagnostic_shape')
    if not 0<=value['record_count']<=MAX_RECORDS or len(value['groups'])>MAX_RECORDS:
        raise ValueError('wal_diagnostic_record_capacity')
    groups=[]
    for row in value['groups']:
        if set(row)!={'rmgr','record_type','records','blockcount'}:
            raise ValueError('wal_diagnostic_shape')
        if any(not isinstance(row[k],str) or not re.fullmatch('[A-Za-z0-9_ /+-]{1,96}',row[k])
               for k in ('rmgr','record_type')):
            raise ValueError('wal_diagnostic_shape')
        if any(type(row[k]) is not int or row[k]<0 for k in ('records','blockcount')):
            raise ValueError('wal_diagnostic_shape')
        groups.append(dict(row))
    if sum(row['records'] for row in groups)!=value['record_count']:
        raise ValueError('wal_diagnostic_record_count')
    return {'record_count':value['record_count'],'groups':groups}

def run(connection,*,environment,ids,context,ci_ca_path,environ=None):
    admit(connection,environment,os.environ if environ is None else environ,ci_ca_path)
    if set(ids)!=ROLES or len(set(ids.values()))!=3:
        raise ValueError('wal_diagnostic_identity_scope')
    people=[str(uuid.UUID(v)) for v in ids.values()]
    window=str(uuid.UUID(context['window']))
    schemas=context['temporary_schemas']
    if len(schemas)!=2 or any(not re.fullmatch('fmz6e11_(guard|am)_[a-f0-9]{32}',s) for s in schemas):
        raise ValueError('wal_diagnostic_schema_scope')
    result={'status':'DIAGNOSTIC_ONLY','full_chain_admission':False,'wal_zero_pass':False,
        'causal_attribution':False,'scope':'cluster_wal_interval_not_exclusive_to_query',
        'queries':[],'commands':0,'limitations':[],'extension_installed':False,
        'row_contents_exported':False,'query_text_exported':False,'rollback_confirmed':False}
    opened=False;phase='preflight'
    def execute(sql,args=()):
        # Always retain a slot for the one rollback after an attempted BEGIN.
        if result['commands']>=MAX_COMMANDS-(1 if opened and sql!='ROLLBACK' else 0):
            raise ValueError('wal_diagnostic_command_limit')
        result['commands']+=1
        return connection.execute(sql,args)
    try:
        p=execute(PREFLIGHT).fetchone()
        if (p['statement_timeout'] not in ('5s','5000ms') or p['lock_timeout'] not in ('1s','1000ms')
            or not 170000<=p['version']<180000 or p['readonly']!='off' or p['ssl'] is not True):
            raise ValueError('wal_diagnostic_server_limits')
        schema=p['installed_schema']
        if schema is None:
            if not p['available'] or not p['target_schema']:
                result['limitations'].append('pg_walinspect_unavailable');return result
            phase='extension_install'
            execute('CREATE EXTENSION pg_walinspect WITH SCHEMA extensions')
            schema='extensions';result['extension_installed']=True
        if schema not in ('extensions','public','pg_catalog'):
            result['limitations'].append('pg_walinspect_schema_not_supported');return result
        phase='metadata_probe';opened=True
        execute('BEGIN TRANSACTION READ ONLY')
        for name,source,args in (
            ('access',ACCESS,[people]),('migrations',MIGRATIONS,[]),
            ('catalog',CATALOG,[schemas]),('absence',ABSENCE,[schemas,people,window])):
            attestation=execute(START).fetchone()
            if attestation['readonly'] is not True:
                raise ValueError('wal_diagnostic_transaction_not_readonly')
            start=attestation['start_lsn']
            if not isinstance(start,str) or not re.fullmatch('[0-9A-F]+/[0-9A-F]+',start):
                raise ValueError('wal_diagnostic_lsn_shape')
            item={'name':name,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                'start_lsn':start,'end_lsn':None,'complete':False}
            result['queries'].append(item)
            sql,params=bind_parameters(source,args)
            begin=time.monotonic()
            execute(sql,params)  # Discard the original metadata result, never serialize it.
            item['duration_ms']=round((time.monotonic()-begin)*1000)
            observed=execute(INSPECT.format(schema='"'+schema+'"'),[start]*5).fetchone()
            end=observed['end_lsn'];flushed=observed['flush_lsn'];span=observed['span_bytes']
            if (any(not isinstance(lsn,str) or not re.fullmatch('[0-9A-F]+/[0-9A-F]+',lsn)
                    for lsn in (end,flushed)) or type(span) is not int or span<0):
                raise ValueError('wal_diagnostic_lsn_shape')
            item.update(end_lsn=end,flush_lsn=flushed,span_bytes=span)
            if tuple(int(x,16) for x in flushed.split('/'))<tuple(int(x,16) for x in end.split('/')):
                result['limitations'].append('wal_not_flushed_through_end');break
            if span>MAX_WAL_BYTES:
                result['limitations'].append('wal_interval_capacity');break
            item['technical']=(technical_only(observed['technical']) if span else {'record_count':0,'groups':[]})
            item['complete']=True
    except Exception as error:
        # Never export exception text, connection details or SQL diagnostics.
        result['limitations'].append('pg_walinspect_install_unavailable' if phase=='extension_install' else 'probe_unconfirmed')
        result['error_class']=type(error).__name__
    finally:
        if opened:
            try:execute('ROLLBACK')
            except Exception as error:
                result['limitations'].append('rollback_unconfirmed')
                result['rollback_error_class']=type(error).__name__
            else:result['rollback_confirmed']=True
    return result

def run_and_stop(connection,save,**kwargs):
    """Main may call only in a separate diagnostic CI invocation; never continue proof."""
    try:receipt=run(connection,**kwargs)
    finally:connection.close()
    save('ci-wal-diagnostic.json',receipt)
    raise DiagnosticOnlyStop('ci_wal_diagnostic_only_not_admission')
