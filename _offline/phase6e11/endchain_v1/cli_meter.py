"""Count the pinned CLI's SQL only in disposable CI, never staging logs.

Session-local logging applies only to the isolated migration CLI connection.
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
    gate.sql("alter system set log_line_prefix='FMZSQL|%a|%p|%l|';")
    gate.sql('select pg_reload_conf();')
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    environment={k:v for k,v in os.environ.items() if k not in
        ('GH_READ_TOKEN','GITHUB_TOKEN','SUPABASE_ACCESS_TOKEN','SUPABASE_DB_PASSWORD')}
    environment['PGOPTIONS']='-c log_statement=all -c application_name='+TAG
    environment['PGAPPNAME']=TAG
    process=subprocess.run([str(gate.binary),'--workdir',str(gate.work),*args],cwd=gate.work,
        env=environment,capture_output=True,text=True,timeout=timeout)
    logs=subprocess.run(['docker','logs','--since',at,gate.container],capture_output=True,text=True,timeout=10)
    raw=logs.stdout+logs.stderr
    if logs.returncode or len(raw.encode())>2000000:raise RuntimeError('ci_cli_log_budget')
    commands=parse(raw);raw=None
    result={'arguments':list(args),'exitcode':process.returncode,'commands':commands,
        'protocol_commands':len(commands),'sql_text_exported':False,'hosted_calls':0,
        'cli_sha256':hashlib.sha256(gate.binary.read_bytes()).hexdigest(),
        'scope':'disposable CI session SQL only; not hosted CLI accounting'}
    gate.save('cli-protocol-'+str(len(getattr(gate,'cli_protocol',[])))+'.json',result)
    if not hasattr(gate,'cli_protocol'):gate.cli_protocol=[]
    gate.cli_protocol.append(result)
    if process.returncode:raise RuntimeError('ci_metered_cli_failed')
    return process
