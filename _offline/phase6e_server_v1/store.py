"""Local/CI-only durable adapter. Never accepts a hosted database endpoint."""
import base64,hashlib,json,os,pathlib,re,subprocess,time,urllib.error,urllib.request,uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.conninfo import conninfo_to_dict
from protocol import transaction
import outbox
import planning

HERE=pathlib.Path(__file__).resolve().parent
SCHEMA='fmz6e_integration_private'


class Denied(Exception):
    pass


def identifier(value):
    try:
        if str(uuid.UUID(value))!=value:raise ValueError()
    except (ValueError,TypeError,AttributeError):raise Denied('identifier') from None
    return value


def digest(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def domain(op,**values):
    result=subprocess.run([os.environ.get('FMZ_NODE','node'),str(HERE/'worker.cjs')],
        input=json.dumps({'op':op,**values}),capture_output=True,text=True,timeout=10)
    if result.returncode or len(result.stdout)>10000000:raise Denied('domain_transport')
    try:value=json.loads(result.stdout)
    except ValueError:raise Denied('domain_transport') from None
    if not value.get('ok'):raise Denied(value.get('code','domain_error'))
    return value['value']


class LocalAuth:
    def __init__(self,url):
        if url not in ('http://127.0.0.1:59999','http://127.0.0.1:54321/auth/v1'):
            raise Denied('local_auth_boundary')
        self.url=url
    def call(self,path,token=None,data=None,method=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        req=urllib.request.Request(self.url+path,headers=headers,
            data=None if data is None else json.dumps(data).encode(),method=method)
        try:
            with urllib.request.urlopen(req,timeout=5) as response:
                raw=response.read(65536)
                return json.loads(raw) if raw else {}
        except (OSError,ValueError):raise Denied('auth_denied') from None
    def verify(self,token):
        user=self.call('/user',token)
        try:
            claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
            actor=identifier(user['id']);session=identifier(claims['session_id'])
            if claims['sub']!=actor or claims['role']!='authenticated' or claims['exp']<=time.time():
                raise ValueError()
        except (ValueError,KeyError,IndexError,TypeError):raise Denied('auth_binding') from None
        return {'sub':actor,'session_id':session}


class Store:
    def __init__(self,dsn,auth,enabled=False,observer=None,full_day21=False):
        if enabled is not True:raise Denied('feature_disabled')
        settings=conninfo_to_dict(dsn)
        if settings.get('host') not in ('127.0.0.1','localhost') or settings.get('sslmode')!='verify-full':
            raise Denied('local_database_boundary')
        if not pathlib.Path(settings.get('sslrootcert','')).is_file():raise Denied('local_ca_missing')
        self.dsn=dsn;self.auth=auth;self.observer=observer;self.full_day21=full_day21 is True
    def connect(self):
        return psycopg.connect(self.dsn,autocommit=True,row_factory=dict_row,
            prepare_threshold=None,connect_timeout=5,
            options='-c statement_timeout=5000 -c lock_timeout=1000')
    def bind(self,db,claims,request):
        live=db.execute('select exists(select 1 from auth.sessions where id=%s and user_id=%s and coalesce(not_after,\'infinity\'::timestamptz)>now()) live',
                        [claims['session_id'],claims['sub']]).fetchone()
        if not live or live['live'] is not True:raise Denied('session_expired_or_revoked')
        db.execute("select set_config('fmz6e.verified_session',%s,true)",[claims['session_id']])
        db.execute('set local role fmz6e_integration_server')
        db.execute("select set_config('request.jwt.claims',%s,true),set_config('fmz6e.request_id',%s,true)",
            [json.dumps(claims),request])
    def read(self,workspace,token):
        identifier(workspace);claims=self.auth.verify(token)
        with transaction(self.connect,self.observer,'read') as db:
            db.execute('set transaction read only')
            self.bind(db,claims,str(uuid.uuid4()))
            row=db.execute('select *,clock_timestamp() server_now from '+SCHEMA+'.workspaces where id=%s',[workspace]).fetchone()
            if not row:raise Denied('workspace_denied')
            state=json.loads(row['state_text'])
            if digest(row['state_text'])!=row['state_sha']:raise Denied('state_integrity')
            role='member' if str(row['member_id'])==claims['sub'] else 'trainer' if str(row['trainer_id'])==claims['sub'] else 'owner'
            visible=domain('view',state=state) if role=='member' else {
                'revision':row['version'],'route':row['route'],
                'active':{'version':state['active']['version'],'training':state['active']['training']},
                'review':None if state['review'] is None else {
                    'kind':state['review']['kind'],'base':state['review']['base'],
                    'member':state['review']['member'],'trainer':state['review']['trainer'],
                    'target':{'training':state['review']['target']['training'],
                              'cadence':state['review']['target']['cadence']}},
                'status':state['status'],'reason':'review_available' if state['review'] else 'no_review'}
            events=db.execute('select * from '+SCHEMA+'.outbox where workspace_id=%s order by created_at,event_key',[workspace]).fetchall() if role=='member' else []
            return {'workspace':workspace,'version':row['version'],'role':role,'actor':claims['sub'],
                    'state':visible,'durable':True,'hosted':False,
                    'capabilities':{'full_day21':self.full_day21},
                    'notices':[outbox.visible(e,row['server_now']) for e in events],
                    'planning':planning.from_state(state) if role=='member' else None}
    def execute(self,workspace,token,request_id,expected,request,fault=None):
        if not self.full_day21 and isinstance(request,dict) and request.get('action') in ('record','finish_workout','finish_day'):
            raise Denied('full_day21_disabled')
        identifier(workspace);identifier(request_id);claims=self.auth.verify(token)
        if type(expected) is not int or expected<0:raise Denied('expected_version')
        raw=json.dumps({'expected':expected,'request':request},sort_keys=True,separators=(',',':'))
        if len(raw)>131072:raise Denied('request_size')
        payload_sha=digest(raw)
        with transaction(self.connect,self.observer,'execute') as db:
            self.bind(db,claims,request_id)
            row=db.execute('select *,clock_timestamp() server_now from '+SCHEMA+'.workspaces where id=%s for update',[workspace]).fetchone()
            if not row:raise Denied('workspace_denied')
            role='member' if str(row['member_id'])==claims['sub'] else 'trainer' if str(row['trainer_id'])==claims['sub'] else 'owner'
            if role=='owner':raise Denied('owner_read_only')
            if not row['consent']:raise Denied('consent')
            prior=db.execute('select actor_id,payload_sha,version from '+SCHEMA+'.requests where workspace_id=%s and request_id=%s',[workspace,request_id]).fetchone()
            if prior:
                if str(prior['actor_id'])!=claims['sub'] or prior['payload_sha']!=payload_sha:raise Denied('duplicate_conflict')
                return {'version':prior['version'],'idempotent':True}
            if row['version']!=expected:raise Denied('version_conflict')
            if digest(row['state_text'])!=row['state_sha']:raise Denied('state_integrity')
            before=json.loads(row['state_text'])
            notice=request.get('action')=='notice_seen'
            if notice:
                if role!='member' or set(request)!={'action','data'} or set(request['data'])!={'id'} or not re.fullmatch('[a-f0-9]{64}',str(request['data']['id'])):raise Denied('notice_payload')
                after=before
            else:after=domain('transition',state=before,request=request,role=role)
            if after['revision'] not in (expected,expected+1):raise Denied('domain_version')
            text=json.dumps(after,separators=(',',':'),ensure_ascii=True)
            version=after['revision'];changed=version!=expected
            if not changed:
                # A no-op is still bound to an idempotency receipt, not a new plan.
                text=row['state_text']
            if changed:
                updated=db.execute('update '+SCHEMA+'.workspaces set version=%s,consent=%s,state_text=%s,state_sha=%s where id=%s and version=%s returning version',
                    [version,after['consent'],text,digest(text),workspace,expected]).fetchone()
                if not updated:raise Denied('version_conflict')
                if fault=='after_head':raise Denied('injected_failure')
                db.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,request_id,state_text,state_sha) values(%s,%s,%s,%s,%s)',
                    [workspace,version,request_id,text,digest(text)])
                if fault=='after_revision':raise Denied('injected_failure')
            db.execute('insert into '+SCHEMA+'.requests(workspace_id,request_id,actor_id,payload_sha,version) values(%s,%s,%s,%s,%s)',
                [workspace,request_id,claims['sub'],payload_sha,version])
            if fault=='after_receipt':raise Denied('injected_failure')
            events=db.execute('select * from '+SCHEMA+'.outbox where workspace_id=%s order by event_key for update',[workspace]).fetchall()
            try:updates=outbox.changes(events,after,request['action'],row['server_now'],row['expires_at'],request_id,
                                      request['data']['id'] if notice else None)
            except ValueError as e:raise Denied(str(e)) from None
            for event in updates:
                if event['operation']=='INSERT':
                    db.execute('insert into '+SCHEMA+'.outbox(workspace_id,event_key,source_sha,kind,status,expires_at,history) values(%s,%s,%s,%s,%s,%s,%s::jsonb)',
                        [workspace,event['event_key'],event['source_sha'],event['kind'],event['status'],event['expires_at'],json.dumps(event['history'])])
                else:
                    db.execute('update '+SCHEMA+'.outbox set status=%s,history=%s::jsonb where workspace_id=%s and event_key=%s',
                        [event['status'],json.dumps(event['history']),workspace,event['event_key']])
            if fault=='after_outbox':raise Denied('injected_failure')
            writes=db.execute('select table_name,operation,key_sha,xid,actor_sha from '+SCHEMA+'.audit where workspace_id=%s and request_id=%s order by id',
                [workspace,request_id]).fetchall()
            expected_writes=[(SCHEMA+'.workspaces','UPDATE'),(SCHEMA+'.revisions','INSERT')] if changed else []
            expected_writes.append((SCHEMA+'.requests','INSERT'))
            expected_writes.extend((SCHEMA+'.outbox',e['operation']) for e in updates)
            if [(x['table_name'],x['operation']) for x in writes]!=expected_writes or len({x['xid'] for x in writes})!=1:
                raise Denied('writeset_mismatch')
            if any(x['actor_sha']!=digest(claims['sub']) for x in writes):raise Denied('audit_actor')
            keys=([digest(json.dumps([workspace])),digest(json.dumps([workspace,version]))] if changed else [])
            keys.append(digest(json.dumps([workspace,request_id])))
            keys.extend(digest(json.dumps([workspace,e['event_key']])) for e in updates)
            if [x['key_sha'] for x in writes]!=keys:raise Denied('audit_key')
            return {'version':version,'idempotent':False,'writes':writes,
                    'before_sha':row['state_sha'],'after_sha':digest(text)}
