"""Count the pinned CLI's SQL only in disposable CI, never staging logs.

Logging is enabled only around the isolated CI migration CLI connection and
restored in finally before the synthetic Auth or workflow client can start.
Raw log text is kept in memory and never becomes an artifact.
"""
import datetime,hashlib,os,pathlib,re,subprocess,uuid
from sql_protocol import statements

TAG='fmz_ci_endchain_meter'
PREFIX='FMZSQL|'

def source_commit(result):
    """Local CI owns commit; an optional hosted-style alias must agree exactly."""
    commit=result.get('commit') if isinstance(result,dict) else None
    if not isinstance(commit,str) or not re.fullmatch('[a-f0-9]{40}',commit):
        raise ValueError('ci_cli_source_commit')
    if 'head' in result and result['head']!=commit:
        raise ValueError('ci_cli_source_conflict')
    return commit

def invocation(gate,args,timeout):
    profile=getattr(gate,'cli_profile','endchain')
    if profile not in ('endchain','local_app'):raise ValueError('ci_cli_profile')
    # This logger is local-only; credentials/URLs must never enter its receipts.
    if tuple(args[:2])!=('db','push') or '--local' not in args or any(
        a not in ('db','push','--local','--skip-vault','--yes','--dry-run','--include-all') for a in args):
        raise ValueError('ci_cli_local_arguments')
    dry='--dry-run' in args;index=len(getattr(gate,'cli_protocol',[]))
    if profile=='endchain':
        from cli_envelope import capacity
        slots=('quota','pre_auth','final')
        if index>=len(slots):raise ValueError('ci_cli_slot_exhausted')
        slot=slots[index]
        if slot!='quota' and not dry:raise ValueError('ci_cli_readonly_slot')
        reserved=capacity(slot)
    else:slot='app_'+str(index);reserved=None
    return {'profile':profile,'slot':slot,'dry_run':dry,'index':index,
            'arguments':list(args),'capacity_reserved':reserved,'timeout_seconds':min(timeout,45)}

def bind_receipt(result,mode,numeric):
    if numeric['all_protocol_visible'] is not True or numeric['temp_written']!=0:
        raise ValueError('ci_cli_numeric_coverage')
    if result.get('complete') is not True or result['protocol_commands']<=0:
        raise ValueError('ci_cli_protocol_incomplete')
    result={**result,'profile':mode['profile'],'slot':mode['slot'],'dry_run':mode['dry_run'],
            'environment':'disposable_ci','hosted_admitted':False}
    if mode['profile']=='endchain':
        from cli_envelope import local
        return local(result,mode['slot'])
    return result

def validate_output(mode,exitcode,stdout,stderr):
    if exitcode:raise ValueError('ci_metered_cli_failed')
    if mode['profile']=='endchain' and mode['dry_run']:
        output=(stdout+stderr).lower()
        if 'up to date' not in output or re.search(r'would (?:be )?push|\d{14}_[a-z0-9_-]+\.sql',output):
            raise ValueError('ci_cli_dry_run_not_empty')

def parse(raw,prefix=PREFIX,applications=(TAG,)):
    commands=[];block=None
    def finish():
        if block is None:return
        message='\n'.join(block)
        found=re.match(r'(?:statement:|execute [^:]+:)\s*(.*)',message,re.S)
        if not found:return
        for s in statements(found[1]):
            commands.append({k:s[k] for k in ('sha256','kind','protocol_commands')})
    for line in raw.splitlines():
        if line.startswith(prefix):
            finish();block=None
            p=line.split('|',4)
            if len(p)!=5:raise ValueError('ci_cli_log_frame')
            if p[1] not in applications:continue
            message=re.sub(r'^\s*LOG:\s*','',p[4])
            block=[message]
        elif block is not None:block.append(line)
    finish()
    if not commands:raise ValueError('ci_cli_no_protocol_evidence')
    return commands

def run(gate,args,timeout):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    mode=invocation(gate,args,timeout)
    def save(name,value):gate.save(getattr(gate,'cli_namespace','')+name,value)
    commit=source_commit(getattr(gate,'result',None))
    save('cli-preregister-'+str(mode['index'])+'.json',{**mode,'source_commit':commit,
        'cli_meter_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'cli_sha256':hashlib.sha256(gate.binary.read_bytes()).hexdigest(),'hosted_admitted':False})
    admin=['docker','exec','-i',gate.container,'psql','-X','-U','supabase_admin','-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
    # A unique server prefix delimits each invocation, including file logs.
    # The pinned CLI sets @effect/sql-pg itself; it ignores PGAPPNAME.
    prefix='FMZSQL'+uuid.uuid4().hex+'|'
    gate.command('ci-meter-prefix',admin,sql="alter system set log_line_prefix='"+prefix+"%a|%p|%l|';")
    from cli_stat_reader import snapshot,compare
    from native_runtime import NativeRuntime
    runtime=NativeRuntime.disposable(gate)
    numeric_before,before_trace=snapshot(runtime)
    gate.command('ci-meter-role-logging',admin,sql="alter role postgres set log_statement='all';")
    gate.command('ci-meter-reload',admin,sql='select pg_reload_conf();')
    meta=subprocess.run(admin,input="select json_build_object('collector',current_setting('logging_collector'),"
        "'destination',current_setting('log_destination'),'directory',current_setting('data_directory'),"
        "'file',pg_current_logfile('stderr'));",capture_output=True,text=True,timeout=10)
    import json,posixpath
    if meta.returncode:raise RuntimeError('ci_log_metadata')
    location=json.loads(meta.stdout)
    save('cli-log-location-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',location)
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    environment={k:v for k,v in os.environ.items() if k not in
        ('GH_READ_TOKEN','GITHUB_TOKEN','SUPABASE_ACCESS_TOKEN','SUPABASE_DB_PASSWORD')}
    environment['PGOPTIONS']='-c application_name='+TAG
    environment['PGAPPNAME']=TAG
    try:
        process=subprocess.run([str(gate.binary),'--workdir',str(gate.work),*args],cwd=gate.work,
            env=environment,capture_output=True,text=True,timeout=mode['timeout_seconds'])
    finally:
        gate.command('ci-meter-role-restore',admin,sql='alter role postgres reset log_statement;')
    if location['file']:
        path=posixpath.normpath(posixpath.join(location['directory'],location['file']))
        if not path.startswith('/') or '\n' in path:raise RuntimeError('ci_log_path')
        logs=subprocess.run(['docker','exec',gate.container,'tail','-c','2000000',path],capture_output=True,text=True,timeout=10)
    else:
        logs=subprocess.run(['docker','logs','--since',at,gate.container],capture_output=True,text=True,timeout=10)
    raw=logs.stdout+logs.stderr
    if logs.returncode or len(raw.encode())>2000000:raise RuntimeError('ci_cli_log_budget')
    apps=sorted(set(line.split('|',4)[1] for line in raw.splitlines() if line.startswith(prefix) and len(line.split('|',4))==5))
    try:commands=parse(raw,prefix,(TAG,'@effect/sql-pg'));error=None
    except ValueError as e:commands=[];error=str(e)
    raw=None
    result={'arguments':list(args),'exitcode':process.returncode,'commands':commands,
        'protocol_commands':len(commands),'sql_text_exported':False,'hosted_calls':0,
        'cli_sha256':hashlib.sha256(gate.binary.read_bytes()).hexdigest(),
        'scope':'disposable CI session SQL only; not hosted CLI accounting'}
    result.update(complete=error is None,error=error,application_names=apps,invocation_prefix=prefix,
        unexpected_applications=[a for a in apps if a not in (TAG,'@effect/sql-pg')])
    numeric_after,after_trace=snapshot(runtime);runtime.clear()
    numeric=compare(numeric_before,numeric_after,len(commands),between=3)
    save('cli-numeric-coverage-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',numeric)
    result['numeric_protocol_coverage']=numeric['all_protocol_visible']
    result['observer_commands']=before_trace+after_trace
    result['total_commands']=len(commands)+len(before_trace)+len(after_trace)
    if result['unexpected_applications']:result.update(complete=False,error='ci_cli_unattributed_connection')
    try:
        validate_output(mode,process.returncode,process.stdout,process.stderr)
        result=bind_receipt(result,mode,numeric)
    except ValueError as error:result.update(complete=False,error=str(error),profile=mode['profile'],slot=mode['slot'],dry_run=mode['dry_run'])
    save('cli-protocol-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',result)
    if not hasattr(gate,'cli_protocol'):gate.cli_protocol=[]
    gate.cli_protocol.append(result)
    if process.returncode:raise RuntimeError('ci_metered_cli_failed')
    if not result['complete']:raise RuntimeError('ci_metered_cli_incomplete')
    return process
