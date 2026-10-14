"""First release slice: frozen12 registration, using only the minimal M45 schema.

No recommendation execution, day21, outbox or hosted activation is admitted here.
"""
import json,uuid
from store import Store,Denied,domain,digest,identifier,SCHEMA
from protocol import transaction

class RegistrationStore(Store):
    def __init__(self,dsn,auth,bindings,enabled=False,observer=None):
        super().__init__(dsn,auth,enabled=enabled,observer=observer)
        if not isinstance(bindings,dict) or not 1<=len(bindings)<=3:raise Denied('slice_bindings')
        self.bindings={identifier(w):identifier(a) for w,a in bindings.items()}
    def authorize(self,workspace,token):
        claims=self.auth.verify(token)
        if self.bindings.get(identifier(workspace))!=claims['sub']:raise Denied('workspace_denied')
        return claims
    def row(self,db,workspace,claims,lock=False):
        row=db.execute('select *,clock_timestamp() server_now from '+SCHEMA+'.workspaces where id=%s'+(' for update' if lock else ''),[workspace]).fetchone()
        if not row or str(row['member_id'])!=claims['sub'] or row['expires_at']<=row['server_now']:raise Denied('workspace_denied')
        if digest(row['state_text'])!=row['state_sha']:raise Denied('state_integrity')
        state=json.loads(row['state_text'])
        if state.get('slice')!='registration12':raise Denied('slice_binding')
        return row,state
    def read(self,workspace,token):
        claims=self.authorize(workspace,token)
        with transaction(self.connect,self.observer,'registration12_read') as db:
            db.execute('set transaction read only');self.bind(db,claims,str(uuid.uuid4()))
            row,state=self.row(db,workspace,claims)
            return {'workspace':workspace,'version':row['version'],'role':'member','durable':True,'hosted':False,
                    'state':domain('registration_view',state=state),'capabilities':{'registration12':True,'full_day21':False}}
    def execute(self,workspace,token,request_id,expected,request,fault=None):
        identifier(request_id);claims=self.authorize(workspace,token)
        if type(expected) is not int or not 0<=expected<=250:raise Denied('expected_version')
        raw=json.dumps({'expected':expected,'request':request},sort_keys=True,separators=(',',':'))
        if len(raw)>131072:raise Denied('request_size')
        payload=digest(raw)
        with transaction(self.connect,self.observer,'registration12_write') as db:
            self.bind(db,claims,request_id);row,state=self.row(db,workspace,claims,True)
            if not row['consent']:raise Denied('consent')
            prior=db.execute('select actor_id,payload_sha,version from '+SCHEMA+'.requests where workspace_id=%s and request_id=%s',[workspace,request_id]).fetchone()
            if prior:
                if str(prior['actor_id'])!=claims['sub'] or prior['payload_sha']!=payload:raise Denied('duplicate_conflict')
                return {'version':prior['version'],'idempotent':True}
            if row['version']!=expected:raise Denied('version_conflict')
            after=domain('registration_transition',state=state,request=request)
            if after['revision']!=expected+1:raise Denied('domain_version')
            text=json.dumps(after,separators=(',',':'));sha=digest(text)
            # Recheck the actual database clock at the final write boundary.
            changed=db.execute('update '+SCHEMA+'.workspaces set version=%s,consent=%s,state_text=%s,state_sha=%s where id=%s and version=%s and expires_at>clock_timestamp() returning version',
                [after['revision'],after['consent'],text,sha,workspace,expected]).fetchone()
            if not changed:raise Denied('expired_or_conflict')
            if fault=='after_head':raise Denied('injected_failure')
            db.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,request_id,state_text,state_sha) values(%s,%s,%s,%s,%s)',
                       [workspace,after['revision'],request_id,text,sha])
            if fault=='after_revision':raise Denied('injected_failure')
            db.execute('insert into '+SCHEMA+'.requests(workspace_id,request_id,actor_id,payload_sha,version) values(%s,%s,%s,%s,%s)',
                       [workspace,request_id,claims['sub'],payload,after['revision']])
            if fault=='after_receipt':raise Denied('injected_failure')
            writes=db.execute('select table_name,operation,key_sha,xid,actor_sha from '+SCHEMA+'.audit where workspace_id=%s and request_id=%s order by id',[workspace,request_id]).fetchall()
            expected_writes=[(SCHEMA+'.workspaces','UPDATE'),(SCHEMA+'.revisions','INSERT'),(SCHEMA+'.requests','INSERT')]
            keys=[digest(json.dumps([workspace])),digest(json.dumps([workspace,after['revision']])),digest(json.dumps([workspace,request_id]))]
            if [(w['table_name'],w['operation']) for w in writes]!=expected_writes or len({w['xid'] for w in writes})!=1 or [w['key_sha'] for w in writes]!=keys or any(w['actor_sha']!=digest(claims['sub']) for w in writes):raise Denied('writeset_mismatch')
            return {'version':after['revision'],'idempotent':False,'before_sha':row['state_sha'],'after_sha':sha,'writes':writes}
