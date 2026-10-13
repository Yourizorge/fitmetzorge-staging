"""Real GoTrue CI-only integration; no hosted requests or staging credentials.

Private pipes carry ephemeral local credentials. Only technical write metadata
and sanitized outcomes may be returned to the CI artifact writer.
"""
import base64,hashlib,hmac,json,os,pathlib,re,secrets,subprocess,threading,time,urllib.request,uuid
import guard
import audit
import auth_contract

IMAGE='supabase/gotrue:v2.196.0'
NAME='fmz-guard-auth-ci'
ROLES=guard.ROLES

def run(gate, composition=None):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging' or os.environ.get('GITHUB_REF')!='refs/heads/main':
        raise RuntimeError('ci_only')
    phase='initialization';command_evidence=[];contracts={}
    def private(args,**kwargs):
        p=subprocess.run(args,capture_output=True,text=True,timeout=kwargs.pop('timeout',30),**kwargs)
        state=re.search(r'ERROR:\s+([0-9A-Z]{5})\b',p.stderr)
        code=state[1] if state else None
        command_evidence.append({'phase':phase,'exitcode':p.returncode,'sqlstate':code})
        if p.returncode:raise RuntimeError('ci_'+phase+'_failed'+('_'+code if code else ''))
        return p.stdout.strip()
    def sql(text,actor='postgres'):
        if composition is not None:composition.before_sql(phase,text)
        args=['docker','exec','-i',gate.container]
        if actor=='supabase_auth_admin':args+=['sh','-c','PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X -h 127.0.0.1 -U supabase_auth_admin -d postgres -qAt -v ON_ERROR_STOP=1 -v VERBOSITY=sqlstate']
        else:args+=['psql','-X','-U','postgres','-d','postgres','-qAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=sqlstate']
        value=private(args,input=text)
        if composition is not None:composition.after_sql(phase,text)
        return value
    def rows(text):return json.loads(sql('select coalesce(jsonb_agg(x),\'[]\') from ('+text+') x'))
    secret=secrets.token_hex(32)
    def jwt(role):
        def b64(value):return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).decode().rstrip('=')
        body=b64({'alg':'HS256','typ':'JWT'})+'.'+b64({'role':role,'iss':'supabase','exp':int(time.time())+600})
        return body+'.'+base64.urlsafe_b64encode(hmac.new(secret.encode(),body.encode(),hashlib.sha256).digest()).decode().rstrip('=')
    # Obtain only this disposable container's local password, in memory.
    password=private(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
    if not password:raise RuntimeError('ci_local_password_missing')
    network=private(['docker','inspect','--format','{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}',gate.container])
    if not re.fullmatch(r'[A-Za-z0-9_-]+',network):raise RuntimeError('ci_network')
    gate.command('auth-image',['docker','pull',IMAGE],timeout=180)
    image=json.loads(private(['docker','image','inspect','--format','{{json .RepoDigests}}',IMAGE]))
    env={**os.environ,'GOTRUE_DB_DATABASE_URL':'postgres://supabase_auth_admin:'+password+'@'+gate.container+':5432/postgres',
        'GOTRUE_JWT_SECRET':secret}
    args=['docker','run','-d','--name',NAME,'--network',network,'-p','127.0.0.1:59999:9999',
        '-e','GOTRUE_DB_DATABASE_URL','-e','GOTRUE_JWT_SECRET']
    public={'GOTRUE_API_HOST':'0.0.0.0','GOTRUE_API_PORT':'9999','GOTRUE_DB_DRIVER':'postgres',
        'API_EXTERNAL_URL':'http://127.0.0.1:59999','GOTRUE_SITE_URL':'http://127.0.0.1:59999',
        'GOTRUE_JWT_ISSUER':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1','GOTRUE_JWT_ADMIN_ROLES':'service_role',
        'GOTRUE_JWT_AUD':'authenticated','GOTRUE_JWT_DEFAULT_GROUP_NAME':'authenticated','GOTRUE_JWT_EXP':'3600',
        'GOTRUE_EXTERNAL_EMAIL_ENABLED':'true','GOTRUE_MAILER_AUTOCONFIRM':'true',
        'GOTRUE_DISABLE_SIGNUP':'true','GOTRUE_SECURITY_REFRESH_TOKEN_ROTATION_ENABLED':'true',
        'GOTRUE_LOG_LEVEL':'panic'}
    for k,v in public.items():args+=['-e',k+'='+v]
    args.append(IMAGE)
    process=psql=timer=None;receipt=None;metadata_receipt=None;ids={};run_id=str(uuid.uuid4());captures=[];container_started=False
    try:
        # Remove only fixtures created by the immediately preceding CI checks.
        phase='local_fixture_cleanup'
        fixed=[f'68000000-0000-4000-8000-{i:012}' for i in range(1,5)]
        sql('delete from auth.users where id in ('+','.join(guard.literal(x) for x in fixed)+')')
        phase='local_container_start'
        private(args,env=env);container_started=True;env.clear();password=None
        healthy=False
        for _ in range(10):
            try:
                with urllib.request.urlopen('http://127.0.0.1:59999/health',timeout=2) as response:healthy=response.status==200
                if healthy:break
            except OSError:pass
            time.sleep(1)
        if not healthy:raise RuntimeError('ci_auth_health')
        # Technical metadata only. These observers exist exclusively in CI.
        phase='local_observer_schema'
        sql("""create schema fmz_ci_auth_observer;
create table fmz_ci_auth_observer.events(seq bigint generated always as identity,table_name text,operation text,xid text,key_sha text,actor_sha text);
grant usage on schema fmz_ci_auth_observer to supabase_auth_admin;
grant insert,select on fmz_ci_auth_observer.events to supabase_auth_admin;
grant usage on all sequences in schema fmz_ci_auth_observer to supabase_auth_admin;
create function fmz_ci_auth_observer.observe() returns trigger language plpgsql security invoker set search_path=pg_catalog,pg_temp as $$
declare v jsonb;actor_hash text;begin
v:=case when TG_OP='DELETE' then to_jsonb(OLD) else to_jsonb(NEW) end;
actor_hash:=encode(sha256(convert_to(case when TG_TABLE_NAME='users' then v->>'id' when TG_TABLE_NAME='audit_log_entries' then v->'payload'->>'actor_id' else v->>'user_id' end,'UTF8')),'hex');
if TG_TABLE_NAME='mfa_amr_claims' then
 select e.actor_sha into strict actor_hash from fmz_ci_auth_observer.events e where e.table_name='auth.sessions' and e.key_sha=encode(sha256(convert_to(v->>'session_id','UTF8')),'hex') order by e.seq desc limit 1;
end if;
insert into fmz_ci_auth_observer.events(table_name,operation,xid,key_sha,actor_sha) values(TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,TG_OP,pg_current_xact_id()::text,encode(sha256(convert_to(coalesce(v->>'id',v->>'token',v->>'user_id',v->>'session_id','no-key'),'UTF8')),'hex'),actor_hash);
return null;end$$;
grant execute on function fmz_ci_auth_observer.observe() to supabase_auth_admin;
""")
        phase='local_observer_triggers'
        sql("""do $$declare r record;begin for r in select c.oid,n.nspname,c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' and c.relkind='r' and c.relname<>'schema_migrations' loop
execute format('create trigger fmz_ci_auth_observe after insert or update or delete on %I.%I for each row execute function fmz_ci_auth_observer.observe()',r.nspname,r.relname);
end loop;end$$;""",'supabase_auth_admin')
        psql=subprocess.Popen(['docker','exec','-i',gate.container,'psql','-X','-U','postgres','-d','postgres','-qAt','-v','ON_ERROR_STOP=1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def session_query(query,values):
            for index,value in reversed(list(enumerate(values,1))):query=query.replace('$'+str(index),guard.literal(value))
            if '$' in query:raise RuntimeError('ci_parameter_binding')
            commands={'BEGIN','ROLLBACK',"SET LOCAL lock_timeout='1s'","SET LOCAL statement_timeout='2s'"}
            control=query in commands
            if not control and not (query.startswith('/* fmz6e11:controller_v1:identity_lock */') or query.startswith('/* fmz6e11:controller_guard_v1:attest */')):raise RuntimeError('ci_query_denied')
            q=query if control else "select coalesce(jsonb_agg(q),'[]') from ("+query+') q'
            marker='fmz_end_'+uuid.uuid4().hex
            psql.stdin.write(q+';\n\\echo '+marker+'\n');psql.stdin.flush();output=[]
            while True:
                line=psql.stdout.readline()
                if not line:raise RuntimeError('ci_guard_session_failed')
                if line.strip()==marker:break
                output.append(line)
            return [] if control else json.loads(''.join(output))
        runner=pathlib.Path(__file__).with_name('auth_service.mjs') if composition is None else composition.runner
        process=subprocess.Popen(['node',str(runner)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        timer=threading.Timer(190,process.kill);timer.start()
        process.stdin.write(json.dumps({'mode':'disposable_ci','url':'http://127.0.0.1:59999','admin':jwt('service_role'),'anon':jwt('anon'),
            **({'sourceSha':os.environ['GITHUB_SHA'],'authContracts':{
                operation:[{'table':'auth.'+t,'operation':o,'count':n} for (t,o),n in counts.items()]
                for operation,counts in auth_contract.COUNTS.items()}} if composition is not None else {})})+'\n');process.stdin.flush();secret=None
        result=None;phase='start';started=time.monotonic();commands=0
        for line in process.stdout:
            commands+=1
            if time.monotonic()-started>180 or commands>200:raise RuntimeError('ci_auth_budget')
            request=json.loads(line);op=request['op'];phase=op
            if op=='complete':result=request['result'];break
            if op=='failed':raise RuntimeError(request['code'])
            try:
                if op=='install':
                    ids=request['ids'];guard.scope(run_id,ids)
                    contracts={r:auth_contract.Contract(hashlib.sha256(ids[r].encode()).hexdigest()) for r in ids}
                    for role in ('a_trainer','a_member','b_member'):
                        phase='profile_seed_'+role;uid=ids[role]
                        trainer=guard.literal(ids['a_trainer'])+'::uuid' if role=='a_member' else 'null'
                        sql('insert into public.profiles(id,email,role,name,trainer_id) values('+guard.literal(uid)+','+guard.literal(guard.ALIASES[role])+','+guard.literal('trainer' if role=='a_trainer' else 'client')+",'CI synthetic',"+trainer+') on conflict(id) do update set role=excluded.role,email=excluded.email,trainer_id=excluded.trainer_id;'+
                            'insert into fmz6e11_private.identities(user_id,role,provenance_sha) values('+guard.literal(uid)+','+guard.literal(role)+","+guard.literal('c'*64)+');')
                    phase='operator_seed'
                    sql('insert into fmz6e11_private.operators values('+guard.literal(ids['a_trainer'])+',true)')
                    if composition is not None:
                        composition.fixture_context['temporary_schemas']=[guard.scope(run_id,ids),audit.scope(run_id,ids)]
                        composition.preservation(gate,ids,'before')
                    phase='guard_install'
                    sql(guard.install(run_id,ids,180));receipt=guard.validate(json.loads(sql(guard.inspect(run_id,ids))),run_id,ids)
                    phase='metadata_install'
                    sql(audit.install(run_id,ids,receipt['expires_at']))
                    metadata_receipt=audit.validate(json.loads(sql(audit.inspect(run_id,ids))),run_id,ids,receipt['expires_at']);value=receipt
                elif op=='query':
                    if composition is not None:composition.before_sql('auth_identity_lock',request['sql'])
                    value=session_query(request['sql'],request['args'])
                    if composition is not None:composition.after_sql('auth_identity_lock',request['sql'])
                elif op=='workflow' and composition is not None:
                    value=composition.workflow(gate,request,sql,ids,run_id)
                elif op=='evidence_query' and composition is not None:
                    value=composition.evidence_query(request,sql)
                elif op=='before':
                    action=request.get('action') if composition is not None else str(uuid.uuid4())
                    if str(uuid.UUID(action))!=action:raise RuntimeError('ci_action_binding')
                    sql(audit.arm(run_id,ids,action,request['role'],request['operation']))
                    if json.loads(sql(audit.events(run_id,ids,action)))!=[]:raise RuntimeError('metadata_before_not_empty')
                    if composition is not None:
                        from auth_protocol import STATS
                        value=json.loads(sql("select jsonb_build_object('seq',(select coalesce(max(seq),0) from fmz_ci_auth_observer.events),'auth_stats',"+STATS+")::text"))
                        value['action']=action
                    else:value={'action':action,'seq':int(sql('select coalesce(max(seq),0) from fmz_ci_auth_observer.events'))}
                elif op=='after':
                    event_sql='select table_name,operation,xid,key_sha,actor_sha from fmz_ci_auth_observer.events where seq>'+str(int(request['before']['seq']))+' order by seq'
                    if composition is not None:
                        from auth_protocol import STATS,difference
                        combined=json.loads(sql("select jsonb_build_object('events',(select coalesce(jsonb_agg(e),'[]') from ("+event_sql+") e),'auth_stats',"+STATS+")::text"))
                        events=combined['events'];protocol=difference(request['before']['auth_stats'],combined['auth_stats'])
                        gate.save('auth-protocol-%02d.json'%len(captures),{'role':request['role'],'operation':request['operation'],**protocol})
                    else:events=rows(event_sql)
                    observed=json.loads(sql(audit.events(run_id,ids,request['before']['action'])))
                    capture={'role':request['role'],'operation':request['operation'],'events':events,'scoped_audit':observed,'pair_complete':False}
                    captures.append(capture)
                    keys=('table_name','operation','xid','key_sha','actor_sha')
                    if sorted(tuple(e[k] for k in keys) for e in events)!=sorted(tuple(e[k] for k in keys) for e in observed):raise RuntimeError('ci_independent_observer_mismatch')
                    actor_sha=hashlib.sha256(ids[request['role']].encode()).hexdigest()
                    if any(e['actor_sha']!=actor_sha for e in events):raise RuntimeError('ci_auth_actor_mismatch')
                    allowed={
                        'issue':{'auth.users','auth.audit_log_entries','auth.one_time_tokens'},
                        'verify':{'auth.users','auth.identities','auth.sessions','auth.refresh_tokens','auth.audit_log_entries','auth.one_time_tokens','auth.mfa_amr_claims'},
                        'getUser':set(),'refresh':{'auth.users','auth.sessions','auth.refresh_tokens','auth.audit_log_entries'},
                        'logout':{'auth.sessions','auth.refresh_tokens','auth.audit_log_entries','auth.mfa_amr_claims'},'revoked_denial':set()}
                    if any(e['table_name'] not in allowed[request['operation']] for e in events):raise RuntimeError('ci_auth_extra_write')
                    required={'issue':[('auth.users','UPDATE')],
                        'verify':[('auth.users','UPDATE'),('auth.sessions','INSERT'),('auth.refresh_tokens','INSERT'),('auth.mfa_amr_claims','INSERT')],
                        'refresh':[('auth.refresh_tokens','UPDATE'),('auth.refresh_tokens','INSERT')],
                        'logout':[('auth.sessions','DELETE'),('auth.mfa_amr_claims','DELETE')],'getUser':[],'revoked_denial':[]}
                    if any(not any(e['table_name']==t and e['operation']==op for e in events) for t,op in required[request['operation']]):
                        raise RuntimeError('ci_auth_missing_write')
                    if composition is not None:
                        contracts[request['role']].validate(request['operation'],observed,request['result'].get('key_sha'))
                    sql(audit.disarm(run_id,ids,request['before']['action']))
                    capture['pair_complete']=True;value={'events':events,'pair_complete':True,'exact_contract':composition is not None}
                elif op=='remove':
                    if request['receipt']!=receipt:raise RuntimeError('ci_removal_receipt')
                    sql(audit.remove(run_id,ids,metadata_receipt));metadata_receipt=None
                    sql(guard.remove(run_id,ids,receipt));receipt=None
                    if composition is not None:composition.preservation(gate,ids,'after_cleanup')
                    value={'removed':True,'commandCount':len(composition.commands)} if composition is not None else True
                else:raise RuntimeError('ci_ipc_denied')
                reply={'value':value}
            except Exception as error:
                code=str(error) if re.fullmatch('[a-zA-Z0-9_]+',str(error)) else 'ci_action_failed'
                reply={'error':code}
            process.stdin.write(json.dumps(reply)+'\n');process.stdin.flush()
        process.wait(timeout=5)
        if not result or process.returncode or result['checks']!=18:raise RuntimeError('ci_auth_incomplete')
        result.update(image=IMAGE,digests=image,guard_removed=receipt is None,checks=18,ci_observers_only=True)
        if composition is not None:
            gate.save('integral-complete-protocol-trace.json',{'commands':composition.commands,
                'outer_sql_commands':len(composition.commands),'hosted_calls':0,'full_chain_admission':False})
        return result
    finally:
        # Never emit raw process output or container logs: Auth may include secrets.
        if timer:timer.cancel()
        for p in (process,psql):
            if p and p.poll() is None:p.kill();p.communicate(timeout=5)
        if metadata_receipt:sql(audit.remove(run_id,ids,metadata_receipt))
        if receipt:sql(guard.remove(run_id,ids,receipt))
        gate.save('real-auth-ci-observed.json',{'image':IMAGE,'digests':image,'completed_pairs':captures,'command_evidence':command_evidence,'last_phase':phase,'hosted_requests':0})
        if composition is not None:
            gate.save('integral-auth-final-trace.json',{'commands':composition.commands,'last_phase':phase,
                'confirmed_pairs':sum(x['pair_complete'] for x in captures),'hosted_calls':0})
        if container_started:private(['docker','rm','-f',NAME])
