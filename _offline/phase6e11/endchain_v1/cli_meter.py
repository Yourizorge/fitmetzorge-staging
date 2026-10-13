"""Count the pinned CLI's SQL only in disposable CI, never staging logs.

Logging is enabled only around the isolated CI migration CLI connection and
restored in finally before the synthetic Auth or workflow client can start.
Raw log text is kept in memory and never becomes an artifact.
"""
import datetime,hashlib,os,re,subprocess
from sql_protocol import statements

TAG='fmz_ci_endchain_meter'
PREFIX='FMZSQL|'

def parse(raw):
    commands=[];block=None
    def finish():
        if block is None:return
        message='\n'.join(block)
        found=re.match(r'(?:statement:|execute [^:]+:)\s*(.*)',message,re.S)
        if not found:return
        for s in statements(found[1]):
            commands.append({k:s[k] for k in ('sha256','kind','protocol_commands')})
    for line in raw.splitlines():
        if line.startswith(PREFIX):
            finish();block=None
            p=line.split('|',4)
            if len(p)!=5:raise ValueError('ci_cli_log_frame')
            if p[1]!=TAG:continue
            message=re.sub(r'^\s*LOG:\s*','',p[4])
            block=[message]
        elif block is not None:block.append(line)
    finish()
    if not commands:raise ValueError('ci_cli_no_protocol_evidence')
    return commands

def run(gate,args,timeout):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    admin=['docker','exec','-i',gate.container,'psql','-X','-U','supabase_admin','-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
    gate.command('ci-meter-prefix',admin,sql="alter system set log_line_prefix='FMZSQL|%a|%p|%l|';")
    gate.command('ci-meter-role-logging',admin,sql="alter role postgres set log_statement='all';")
    gate.command('ci-meter-reload',admin,sql='select pg_reload_conf();')
    meta=subprocess.run(admin,input="select json_build_object('collector',current_setting('logging_collector'),"
        "'destination',current_setting('log_destination'),'directory',current_setting('data_directory'),"
        "'file',pg_current_logfile('stderr'));",capture_output=True,text=True,timeout=10)
    import json,posixpath
    if meta.returncode:raise RuntimeError('ci_log_metadata')
    location=json.loads(meta.stdout)
    gate.save('cli-log-location-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',location)
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    environment={k:v for k,v in os.environ.items() if k not in
        ('GH_READ_TOKEN','GITHUB_TOKEN','SUPABASE_ACCESS_TOKEN','SUPABASE_DB_PASSWORD')}
    environment['PGOPTIONS']='-c application_name='+TAG
    environment['PGAPPNAME']=TAG
    try:
        process=subprocess.run([str(gate.binary),'--workdir',str(gate.work),*args],cwd=gate.work,
            env=environment,capture_output=True,text=True,timeout=timeout)
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
    apps=sorted(set(line.split('|',4)[1] for line in raw.splitlines() if line.startswith(PREFIX) and len(line.split('|',4))==5))
    try:commands=parse(raw);error=None
    except ValueError as e:commands=[];error=str(e)
    raw=None
    result={'arguments':list(args),'exitcode':process.returncode,'commands':commands,
        'protocol_commands':len(commands),'sql_text_exported':False,'hosted_calls':0,
        'cli_sha256':hashlib.sha256(gate.binary.read_bytes()).hexdigest(),
        'scope':'disposable CI session SQL only; not hosted CLI accounting'}
    result.update(complete=error is None,error=error,application_names=apps)
    gate.save('cli-protocol-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',result)
    if not hasattr(gate,'cli_protocol'):gate.cli_protocol=[]
    gate.cli_protocol.append(result)
    if process.returncode:raise RuntimeError('ci_metered_cli_failed')
    return process
