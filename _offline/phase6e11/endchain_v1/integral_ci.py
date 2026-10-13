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
    # Generated keys stay in disposable CI work/container storage, never the
    # evidence artifact. No staging credential or trust setting is changed.
    key=gate.work/'fmz-ci-server.key';ca=gate.work/'fmz-ci-ca.crt'
    commands=[('generate',['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
        '-keyout',str(key),'-out',str(ca),'-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1']),
        ('key_copy',['docker','cp',str(key),gate.container+':/tmp/fmz-ci-server.key']),
        ('ca_copy',['docker','cp',str(ca),gate.container+':/tmp/fmz-ci-ca.crt']),
        ('owner',['docker','exec','-u','root',gate.container,'chown','postgres:postgres','/tmp/fmz-ci-server.key','/tmp/fmz-ci-ca.crt']),
        ('mode',['docker','exec','-u','root',gate.container,'chmod','600','/tmp/fmz-ci-server.key'])]
    for stage,args in commands:
        p=subprocess.run(args,capture_output=True,timeout=15)
        gate.save('integral-tls-'+stage+'.json',{'stage':stage,'exitcode':p.returncode})
        if p.returncode:raise RuntimeError('ci_tls_'+stage)
    key.chmod(0o600)
    settings=[('ssl_cert_file','/tmp/fmz-ci-ca.crt'),('ssl_key_file','/tmp/fmz-ci-server.key'),('ssl','on'),
        ('log_parameter_max_length','0'),('log_parameter_max_length_on_error','0'),('log_statement','none'),
        ('log_min_duration_statement','-1'),('log_min_duration_sample','-1'),('log_transaction_sample_rate','0')]
    for setting,value in settings:
        gate.command('ci-bootstrap-'+setting,['docker','exec','-i',gate.container,'psql','-X','-U','supabase_admin',
            '-d','postgres','-qAt','-v','ON_ERROR_STOP=1'],sql="alter system set "+setting+"='"+value+"';")
    gate.command('ci-bootstrap-reload',['docker','exec','-i',gate.container,'psql','-X','-U','supabase_admin',
        '-d','postgres','-qAt','-v','ON_ERROR_STOP=1'],sql='select pg_reload_conf();')
    public=ca.read_bytes()
    if not public.startswith(b'-----BEGIN CERTIFICATE-----'):raise RuntimeError('ci_ca_fixture')
    gate.save('integral-local-tls.json',{'ca_sha256':hashlib.sha256(public).hexdigest(),
        'hostname':'127.0.0.1','mode':'verify-full','scope':'disposable CI CA, not hosted TLS evidence'})

class Composition:
    runner=HERE/'integral_auth.mjs'
    def __init__(self):
        self.commands=[];self.pending=[];self.started=time.monotonic();self.events=[]
        self.fixture_context={k:str(uuid.uuid4()) for k in ('window','a','b','key')}
        self.fixture_context['runs']={k:str(uuid.uuid4()) for k in ('seed','activate','delete_window')}
        self.preservation_baseline=None
        self.gate_baseline=None
    def preservation(self,gate,ids,label):
        import psycopg,integral_stream
        from psycopg.rows import dict_row
        p=subprocess.run(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'],capture_output=True,text=True,timeout=10)
        endpoint=subprocess.run(['docker','port',gate.container,'5432/tcp'],capture_output=True,text=True,timeout=10)
        choices=[x for x in endpoint.stdout.splitlines() if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+',x)]
        if p.returncode or endpoint.returncode or len(choices)!=1:raise RuntimeError('ci_preservation_endpoint')
        connection=psycopg.connect(host='127.0.0.1',port=int(choices[0].split(':')[1]),dbname='postgres',user='postgres',
            password=p.stdout.strip(),autocommit=True,prepare_threshold=None,row_factory=dict_row,
            sslmode='verify-full',sslrootcert=str(gate.work/'fmz-ci-ca.crt'),connect_timeout=5)
        p=None
        def query(phase,text,args=()):
            params=[]
            def bind(match):
                params.append(args[int(match[1])-1]);return '%s'
            bound=re.sub(r'\$(\d+)',bind,text)
            self.before_sql(phase,text)
            cursor=connection.execute(bound,params)
            rows=cursor.fetchall() if cursor.description else []
            query.terminal_count=cursor.rowcount
            self.after_sql(phase,text);return rows
        try:
            value=integral_stream.run(query,gate.save,ids,self.fixture_context,label,self.preservation_baseline)
            if self.preservation_baseline is None:self.preservation_baseline=value
            if label in ('before','after_cleanup'):
                import lifecycle_gates as gates
                from integral_io import QueryIO
                query('gates_'+label+'_begin','BEGIN TRANSACTION READ ONLY')
                query('gates_'+label+'_timeout',"SET LOCAL statement_timeout='5s'")
                if query('gates_'+label+'_readonly',"select current_setting('transaction_read_only')='on' readonly")[0]['readonly'] is not True:
                    raise RuntimeError('ci_gates_not_readonly')
                monitor=QueryIO(lambda channel,phase,text,args=():query('gates_'+label+'_'+phase,text,args))
                monitor.start()
                def checked(name,text,args=()):
                    qid=monitor.bind(text,args);rows=query('gates_'+label+'_'+name,text,args);monitor.executed(qid)
                    return rows
                context=self.fixture_context;people=list(ids.values());schemas=context['temporary_schemas']
                access=checked('access',gates.ACCESS,[people])[0];gates.check_access(access)
                migrations=checked('migrations',gates.MIGRATIONS)
                gates.check_migrations(migrations,self.gate_baseline['migrations'] if self.gate_baseline else None)
                catalog=checked('catalog',gates.CATALOG,[schemas])[0]['value']
                if self.gate_baseline and catalog!=self.gate_baseline['catalog']:raise RuntimeError('ci_object_or_acl_drift')
                absence=checked('absence',gates.ABSENCE,[schemas,people,context['window']])[0];gates.check_absence(absence)
                gate.save('integral-gates-'+label+'.json',{'access':access,'migrations':migrations,
                    'catalog_sha':gates.digest(catalog),'absence':absence,'io':monitor.close(),
                    'unchanged':self.gate_baseline is None or catalog==self.gate_baseline['catalog']})
                if self.gate_baseline is None:self.gate_baseline={'migrations':migrations,'catalog':catalog}
                query('gates_'+label+'_rollback','ROLLBACK')
            return {'label':label,'commands':value['protocol_commands'],'tables':len(value['tables']),
                'protected_equal':value['protected_equal']}
        finally:
            if connection.info.transaction_status!=0:
                try:query('gates_'+label+'_safety_rollback','ROLLBACK')
                finally:connection.close()
            else:connection.close()
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
    def evidence_query(self,request,sql):
        text=request['sql'];args=request['args']
        if not text.startswith('/* fmz6e11:controller_v1:evidence */ ') or 'fmz6e11_controller_private.' not in text:
            raise RuntimeError('ci_evidence_template_denied')
        def literal(match):
            v=args[int(match[1])-1]
            if v is None:return 'null'
            if isinstance(v,(dict,list)):v=json.dumps(v,separators=(',',':'))
            return "'"+str(v).replace("'","''")+"'"
        bound=re.sub(r'\$(\d+)',literal,text)
        # Fixed source CTE, no user-provided SQL. Wrapping preserves one command.
        prefix='/* fmz6e11:controller_v1:evidence */ '
        body=bound[len(prefix):]
        tails={
            'returning phase':"returning jsonb_build_object('phase',phase)::text",
            'returning id':"returning jsonb_build_object('id',id)::text",
            'returning state':"returning jsonb_build_object('state',state)::text",
            'select phase from e':"select jsonb_build_object('phase',phase)::text from e",
            'select id from r':"select jsonb_build_object('id',id)::text from r"}
        matches=[k for k in tails if body.rstrip().endswith(k)]
        if len(matches)!=1:raise RuntimeError('ci_evidence_terminal')
        tail=matches[0];value=sql(body.rstrip()[:-len(tail)]+tails[tail])
        rows=[json.loads(line) for line in value.splitlines() if line.startswith('{')]
        return {'rows':rows,'commandCount':len(self.commands)}
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
                options='-c statement_timeout=5000 -c lock_timeout=1000')
        password=None
        monitor=None;io_receipts=[]
        def raw_query(channel,phase,text,values=()):
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
        def query(channel,phase,text,values=()):
            track=monitor is not None and re.match(r'\s*(?:/\*.*?\*/\s*)?(select|with|insert|update|delete)\b',text,re.I|re.S)
            qid=monitor.bind(text,values) if track else None
            result=raw_query(channel,phase,text,values)
            if qid is not None:monitor.executed(qid)
            return result
        process=None;timer=None;result=None
        try:
            def start_reader():
                nonlocal monitor
                query('reader','lifecycle_reader_begin','BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY')
                if query('reader','lifecycle_reader_check',"select current_setting('transaction_read_only')='on' readonly")[0]['readonly'] is not True:
                    raise RuntimeError('ci_lifecycle_readonly')
                from integral_io import QueryIO
                monitor=QueryIO(raw_query);monitor.start()
            def end_reader(label):
                nonlocal monitor
                if monitor is not None:
                    gate.save('integral-'+label+'-io.json',monitor.close());monitor=None
                query('reader','lifecycle_reader_end','ROLLBACK')
            start_reader()
            roles={'member':ids['a_member'],'trainer':ids['a_trainer'],'b':ids['b_member']}
            from auth_protocol import STATS,difference
            auth_before=query('reader','workflow_auth_before','select '+STATS+' value')[0]['value']
            # Verify the actual token with GoTrue again before it supplies claims.
            import urllib.request,base64
            token=request['tokens']['a_trainer']
            req=urllib.request.Request('http://127.0.0.1:59999/user',headers={'Authorization':'Bearer '+token})
            with urllib.request.urlopen(req,timeout=5) as response:user=json.loads(response.read(20000))
            claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
            if user['id']!=ids['a_trainer'] or claims['sub']!=user['id']:raise RuntimeError('ci_auth_identity')
            headers={'x-fmz6e11-proof':'synthetic-only-local-proof'}
            control_sql="select jsonb_build_object('config',(select to_jsonb(c) from fmz6e11_private.config c where id),'request',(select to_jsonb(c) from fmz6e11_request_private.control c where id)) value"
            controls=query('reader','control_before',control_sql)[0]['value']
            if controls!={'config':{'id':True,'enabled':False,'proof_hash':None},'request':{'id':True,'enabled':False,'expires_at':None}}:
                raise RuntimeError('ci_control_not_closed')
            if query('setup','control_enable',"update fmz6e11_private.config set enabled=true,proof_hash=encode(sha256(convert_to($1,'UTF8')),'hex') where id and not enabled and proof_hash is null returning id",['synthetic-only-local-proof'])!=[{'id':True}]:raise RuntimeError('ci_control_enable_count')
            if query('setup','control_enable',"update fmz6e11_request_private.control set enabled=true,expires_at=clock_timestamp()+interval '3 minutes' where id and not enabled and expires_at is null returning id")!=[{'id':True}]:raise RuntimeError('ci_bridge_enable_count')
            enabled=query('reader','control_after',control_sql)[0]['value']
            if not enabled['config']['enabled'] or not enabled['request']['enabled']:raise RuntimeError('ci_controls_not_enabled')
            gate.save('integral-control-enable-pair.json',{'before_sha':hashlib.sha256(json.dumps(controls,sort_keys=True).encode()).hexdigest(),
                'after_sha':hashlib.sha256(json.dumps(enabled,sort_keys=True).encode()).hexdigest(),'expected_updates':2,'actual_updates':2})
            times=query('reader','fixture_times',"select clock_timestamp()-interval '10 seconds' starts_at,clock_timestamp()+interval '3 minutes' ends_at")[0]
            import fixture_lifecycle as fixture
            ctx=self.fixture_context
            ctx.update(trainer=ids['a_trainer'],member=ids['a_member'],b_member=ids['b_member'])
            window=ctx['window'];by_route={'A':ctx['a'],'B':ctx['b']}
            prepare={'op':'command','action':'prepare','window':None,'workspace':None,'expected':0,'key':ctx['key'],
                'data':{'scenario':'kg',**{k:v.isoformat() for k,v in times.items()}}}
            seed=fixture.perform(query,gate.save,ctx,'seed',fixture.seed_writes(ctx),fixture.SEED,
                [window,ctx['a'],ctx['b'],ctx['trainer'],ctx['member'],ctx['b_member'],ctx['key'],
                 times['starts_at'].isoformat(),times['ends_at'].isoformat(),prepare],claims,headers)
            if len(seed)!=1 or seed[0]['value'].get('revision')!=1:raise RuntimeError('ci_seed_incomplete')
            gate.save('integral-seed-io-pair.json',monitor.checkpoint())
            activation={'op':'command','action':'activate','window':window,'workspace':None,'expected':1,
                'key':str(uuid.uuid4()),'data':{}}
            active=fixture.perform(query,gate.save,ctx,'activate',[
                ['windows','UPDATE',[window]],['windows','UPDATE',[window]],
                ['audit','INSERT',[window,ctx['trainer'],'activate']],['requests','INSERT',[ctx['trainer'],activation['key']]]],
                'select public.fmz6e11_call($1::jsonb) value',[activation],claims,headers)[0]['value']
            if active.get('revision')!=2 or active.get('http_status',200)!=200:raise RuntimeError('ci_activation_denied')
            end_reader('fixture_setup')
            payload={'mode':'disposable_ci','authUrl':'http://127.0.0.1:59999','tokens':request['tokens'],
                'ca':(gate.work/'fmz-ci-ca.crt').read_text(),
                'key':request['anon'],'proof':'synthetic-only-local-proof','ids':roles,'window':window,
                'a':by_route['A'],'b':by_route['B'],'initialRevision':active['revision'],
                'scenario':capture()['workflow_actions'],'sourceSha':gate.result['head'] if 'head' in gate.result else os.environ['GITHUB_SHA'],
                'commandCount':0}
            payload['controllerContext']=request.get('controllerContext')
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
                        if message['channel']=='reader' and message['q']=='ROLLBACK' and monitor is not None:
                            terminal=monitor.close()
                            gate.save('integral-workflow-io.json',{'pairs':io_receipts,'terminal':terminal,
                                'scope':'71 workflow actions including scoped reads and evidence writes; no setup/Auth attribution'})
                            monitor=None
                        reply={'rows':query(message['channel'],message['phase'],message['q'],message['args']),
                            'commandCount':len(self.commands)-offset}
                        if message['channel']=='reader' and message['q'].startswith('select current_setting') and monitor is None:
                            from integral_io import QueryIO
                            monitor=QueryIO(raw_query);monitor.start()
                            reply['commandCount']=len(self.commands)-offset
                    elif message['op']=='persist':
                        self.events.append(message['event'])
                        gate.save('integral-pair-%03d-%s.json'%(message['event']['step'],message['event']['phase']),message['event'])
                        if message['event']['step']==45 and message['event']['phase']=='contract':
                            self.preservation(gate,ids,'before_cleanup')
                        if message['event']['phase']=='pair_validated':
                            evidence=monitor.checkpoint();io_receipts.append(evidence)
                            gate.save('integral-io-pair-%03d.json'%message['event']['step'],evidence)
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
            start_reader()
            auth_after=query('reader','workflow_auth_after','select '+STATS+' value')[0]['value']
            auth_load=difference(auth_before,auth_after)
            if auth_load['commands']!=360:raise RuntimeError('ci_workflow_auth_protocol')
            gate.save('workflow-auth-protocol.json',{'verified_calls':72,**auth_load})
            deleted=fixture.perform(query,gate.save,ctx,'delete_window',[['windows','DELETE',[window]]],
                "delete from fmz6e11_private.windows where id=$1::uuid and status='revoked' and not feature_enabled returning id::text",[window],claims,headers)
            if deleted!=[{'id':window}]:raise RuntimeError('ci_window_delete_unconfirmed')
            restore_before=query('reader','control_restore_before',control_sql)[0]['value']
            if restore_before!=enabled:raise RuntimeError('ci_control_unexpected_drift')
            if query('setup','control_restore',"update fmz6e11_request_private.control set enabled=false,expires_at=null where id and enabled and expires_at=$1::timestamptz returning id",[enabled['request']['expires_at']])!=[{'id':True}]:raise RuntimeError('ci_bridge_restore_count')
            if query('setup','control_restore',"update fmz6e11_private.config set enabled=false,proof_hash=null where id and enabled and proof_hash=$1 returning id",[enabled['config']['proof_hash']])!=[{'id':True}]:raise RuntimeError('ci_control_restore_count')
            restored=query('reader','control_restored',control_sql)[0]['value']
            if restored!=controls:raise RuntimeError('ci_control_restore_mismatch')
            gate.save('integral-control-restore-pair.json',{'before_sha':hashlib.sha256(json.dumps(restore_before,sort_keys=True).encode()).hexdigest(),
                'after_sha':hashlib.sha256(json.dumps(restored,sort_keys=True).encode()).hexdigest(),'expected_updates':2,'actual_updates':2,'original_state_restored':True})
            end_reader('fixture_closeout')
            gate.save('integral-workflow.json',result)
            return {'status':'REAL_AUTH_THROUGH_71_WORKFLOW_PAIRS','pairs':71,'deletes':123,
                'outer_sql_commands_so_far':len(self.commands),'next_step':result['next_step'],'hosted_admitted':False}
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
