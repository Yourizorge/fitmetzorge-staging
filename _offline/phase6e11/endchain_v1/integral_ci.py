"""A loopback-only bridge joining real GoTrue to the existing 71 PG actions.

This records actual protocol SQL, including setup and close. It cannot grant
hosted admission; the complete capacity register is checked separately.
"""
import hashlib,importlib.util,json,os,pathlib,re,subprocess,threading,time,uuid
from sql_protocol import statements

HERE=pathlib.Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('integral_candidate_scenario',HERE/'scenario.py')
_scenario=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_scenario)
capture=_scenario.capture

def configure_local_tls(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    # Generated keys stay inside the disposable container. Only its public CA
    # is copied to the local verifier; no staging trust settings are changed.
    args=['docker','exec','-u','root',gate.container,'sh','-c',
        "umask 077; openssl req -x509 -newkey rsa:2048 -nodes -days 1 "
        "-keyout /tmp/fmz-ci-server.key -out /tmp/fmz-ci-ca.crt -subj /CN=localhost "
        "-addext subjectAltName=DNS:localhost,IP:127.0.0.1 >/dev/null 2>&1 && "
        "chown postgres:postgres /tmp/fmz-ci-server.key /tmp/fmz-ci-ca.crt"]
    p=subprocess.run(args,capture_output=True,timeout=15)
    if p.returncode:raise RuntimeError('ci_tls_fixture')
    for setting,value in [('ssl_cert_file','/tmp/fmz-ci-ca.crt'),('ssl_key_file','/tmp/fmz-ci-server.key'),('ssl','on')]:
        gate.sql("alter system set "+setting+"='"+value+"';")
    gate.sql('select pg_reload_conf();')
    p=subprocess.run(['docker','exec',gate.container,'cat','/tmp/fmz-ci-ca.crt'],capture_output=True,timeout=5)
    if p.returncode or not p.stdout.startswith(b'-----BEGIN CERTIFICATE-----'):raise RuntimeError('ci_ca_fixture')
    ca=gate.work/'fmz-ci-ca.crt';ca.write_bytes(p.stdout)
    gate.save('integral-local-tls.json',{'ca_sha256':hashlib.sha256(p.stdout).hexdigest(),
        'hostname':'127.0.0.1','mode':'verify-full','scope':'disposable CI CA, not hosted TLS evidence'})

class Composition:
    runner=HERE/'integral_auth.mjs'
    def __init__(self):
        self.commands=[];self.pending=[];self.started=time.monotonic();self.events=[]
    def before_sql(self,phase,sql):
        parsed=statements(sql)
        if len(self.commands)+len(parsed)>4096:raise RuntimeError('ci_diagnostic_command_ceiling')
        for statement in parsed:
            self.commands.append({'command':len(self.commands)+1,'phase':phase,
                'sql_sha256':statement['sha256'],
                'at_ms':round((time.monotonic()-self.started)*1000),'confirmed':False})
        self.pending.append((len(self.commands)-len(parsed),len(self.commands),time.monotonic()))
    def after_sql(self,phase,sql):
        first,last,started=self.pending.pop()
        for row in self.commands[first:last]:
            row.update(confirmed=True,duration_ms=round((time.monotonic()-started)*1000))
    def workflow(self,gate,request,outer_sql,ids,run_id):
        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb
        from psycopg import sql as pgsql
        def private(args):
            p=subprocess.run(args,capture_output=True,text=True,timeout=10)
            if p.returncode:raise RuntimeError('ci_local_transport_setup')
            return p.stdout.strip()
        password=private(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
        ports=private(['docker','port',gate.container,'5432/tcp']).splitlines()
        endpoints=[x for x in ports if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+',x)]
        if len(endpoints)!=1:raise RuntimeError('ci_loopback_binding')
        port=int(endpoints[0].split(':')[1]);connections={}
        for channel in ('setup','writer','reader','workflow'):
            connections[channel]=psycopg.connect(host='127.0.0.1',port=port,dbname='postgres',user='postgres',
                password=password,autocommit=True,prepare_threshold=None,row_factory=dict_row,
                sslmode='verify-full',sslrootcert=str(gate.work/'fmz-ci-ca.crt'),connect_timeout=5,
                options='-c statement_timeout=5000 -c lock_timeout=1000 -c log_parameter_max_length=0 '
                    '-c log_parameter_max_length_on_error=0 -c log_statement=none -c log_min_duration_statement=-1 '
                    '-c log_min_duration_sample=-1 -c log_transaction_sample_rate=0 -c pgaudit.log_parameter=off')
        password=None
        def query(channel,phase,text,values=()):
            # SQL templates are fixed candidate sources, values are bound by the
            # driver. Repeated numbered parameters retain their original value.
            params=[]
            def bind(match):
                value=values[int(match[1])-1]
                params.append(Jsonb(value) if isinstance(value,(dict,list)) else value)
                return '%s'
            q=re.sub(r'\$(\d+)',bind,text)
            self.before_sql(phase,text)
            try:
                cur=connections[channel].execute(q,params)
                rows=cur.fetchall() if cur.description else []
                self.after_sql(phase,text);return rows
            except psycopg.Error as e:
                raise RuntimeError('ci_sql_'+(e.sqlstate or 'unknown')) from None
        process=None;timer=None;result=None
        try:
            roles={'member':ids['a_member'],'trainer':ids['a_trainer'],'b':ids['b_member']}
            # Verify the actual token with GoTrue again before it supplies claims.
            import urllib.request,base64
            token=request['tokens']['a_trainer']
            req=urllib.request.Request('http://127.0.0.1:59999/user',headers={'Authorization':'Bearer '+token})
            with urllib.request.urlopen(req,timeout=5) as response:user=json.loads(response.read(20000))
            claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
            if user['id']!=ids['a_trainer'] or claims['sub']!=user['id']:raise RuntimeError('ci_auth_identity')
            headers={'x-fmz6e11-proof':'synthetic-only-local-proof'}
            query('setup','control_enable',"update fmz6e11_private.config set enabled=true,proof_hash=encode(sha256(convert_to($1,'UTF8')),'hex')",['synthetic-only-local-proof'])
            query('setup','control_enable',"update fmz6e11_request_private.control set enabled=true,expires_at=clock_timestamp()+interval '3 minutes'")
            times=query('setup','fixture_times',"select clock_timestamp()-interval '10 seconds' starts_at,clock_timestamp()+interval '3 minutes' ends_at")[0]
            def call(q):
                query('setup','fixture_begin','BEGIN')
                try:
                    query('setup','fixture_bind',"select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
                        [json.dumps(claims),json.dumps(headers)])
                    value=query('setup','fixture_call','select public.fmz6e11_call($1::jsonb) value',[q])[0]['value']
                    if value.get('http_status',200)!=200:raise RuntimeError('ci_fixture_denied')
                    query('setup','fixture_commit','COMMIT');return value
                except BaseException:
                    query('setup','fixture_rollback','ROLLBACK');raise
            prepared=call({'op':'command','action':'prepare','window':None,'workspace':None,'expected':0,'key':str(uuid.uuid4()),
                'data':{'scenario':'kg',**{k:v.isoformat() for k,v in times.items()}}})
            window=prepared['window']
            active=call({'op':'command','action':'activate','window':window,'workspace':None,'expected':prepared['revision'],
                'key':str(uuid.uuid4()),'data':{}})
            spaces=query('setup','fixture_receipt','select route,id::text id from fmz6e11_private.workspaces where window_id=$1::uuid',[window])
            by_route={r['route']:r['id'] for r in spaces}
            payload={'mode':'disposable_ci','authUrl':'http://127.0.0.1:59999','tokens':request['tokens'],
                'ca':(gate.work/'fmz-ci-ca.crt').read_text(),
                'key':request['anon'],'proof':'synthetic-only-local-proof','ids':roles,'window':window,
                'a':by_route['A'],'b':by_route['B'],'initialRevision':active['revision'],
                'scenario':capture()['workflow_actions'],'sourceSha':gate.result['head'] if 'head' in gate.result else os.environ['GITHUB_SHA'],
                'commandCount':0}
            # Keep the complete outer count in this adapter. The unchanged
            # controller's own receipt counts its 71-action subchain only.
            offset=len(self.commands)
            process=subprocess.Popen(['node',str(HERE/'integral_workflow.mjs')],stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            timer=threading.Timer(125,process.kill);timer.start()
            process.stdin.write(json.dumps(payload)+'\n');process.stdin.flush();payload=None
            for line in process.stdout:
                message=json.loads(line)
                if message['op']=='complete':result=message['result'];break
                reply={}
                try:
                    if message['op']=='sql':
                        if message['channel'] not in ('writer','reader','workflow'):raise RuntimeError('ci_channel')
                        reply={'rows':query(message['channel'],message['phase'],message['q'],message['args']),
                            'commandCount':len(self.commands)-offset}
                    elif message['op']=='persist':
                        self.events.append(message['event'])
                        gate.save('integral-pair-%03d-%s.json'%(message['event']['step'],message['event']['phase']),message['event'])
                    else:raise RuntimeError('ci_operation')
                except Exception as error:
                    reply={'error':str(error) if re.fullmatch('[a-zA-Z0-9_]+',str(error)) else 'ci_query_failed',
                        'commandCount':len(self.commands)-offset}
                process.stdin.write(json.dumps(reply,default=str)+'\n');process.stdin.flush()
            process.wait(timeout=5)
            if process.returncode or not result or result.get('pairs')!=71:
                gate.save('integral-workflow-stop.json',result or {'status':'NO_GO','phase':'child_process'})
                raise RuntimeError('ci_integral_workflow_incomplete')
            if result['deletes']!=123:raise RuntimeError('ci_integral_delete_count')
            query('setup','control_restore',"update fmz6e11_request_private.control set enabled=false,expires_at=null")
            query('setup','control_restore',"update fmz6e11_private.config set enabled=false,proof_hash=null")
            gate.save('integral-workflow.json',result)
            return {'status':'REAL_AUTH_THROUGH_71_WORKFLOW_PAIRS','pairs':71,'deletes':123,
                'outer_sql_commands_so_far':len(self.commands),'hosted_admitted':False}
        finally:
            if timer:timer.cancel()
            if process and process.poll() is None:process.kill();process.communicate(timeout=5)
            for channel,connection in connections.items():
                if connection.info.transaction_status!=0:
                    try:query(channel,'safety_rollback','ROLLBACK')
                    except Exception:pass
                connection.close()
            gate.save('integral-protocol-trace.json',{'commands':self.commands,'events':self.events,
                'seconds':time.monotonic()-self.started,'hosted_calls':0,'full_chain_admission':False})
