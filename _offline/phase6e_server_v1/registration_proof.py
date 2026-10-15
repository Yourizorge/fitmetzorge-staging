"""Private scoped release12 measure pairs; no listener or hosted entry point."""
import collections,hashlib,json,threading,uuid
from protocol import transaction
from store import SCHEMA,Denied,digest,identifier

PAIR_SQL="""select
 (select state_sha from fmz6e_integration_private.workspaces where id=%s) state_sha,
 (select version from fmz6e_integration_private.workspaces where id=%s) version,
 (select count(*) from fmz6e_integration_private.revisions where workspace_id=%s) revisions,
 (select count(*) from fmz6e_integration_private.requests where workspace_id=%s) requests,
 coalesce((select jsonb_agg(jsonb_build_object('id',id,'table',table_name,'operation',operation,
 'key_sha',key_sha,'xid',xid,'actor_sha',actor_sha) order by id)
 from fmz6e_integration_private.audit where workspace_id=%s and request_id=%s),'[]') writes"""

class MeasuredRegistration:
    def __init__(self,store,save):
        self.store=store;self.save=save;self.pairs=[];self.lock=threading.Lock()
    def __getattr__(self,name):return getattr(self.store,name)
    def sample(self,workspace,request):
        # Operator metadata only. No payload, token, address or registration text.
        with transaction(self.store.runtime.connect,self.store.observer,'registration12_measure') as db:
            db.execute('set transaction read only')
            return db.execute(PAIR_SQL,[workspace]*5+[request]).fetchone()
    def execute(self,workspace,token,request,expected,payload,fault=None):
        identifier(workspace);identifier(request)
        if workspace not in self.store.bindings:raise Denied('measure_workspace')
        action=str(uuid.uuid4());prefix='pair-'+action;before=self.sample(workspace,request)
        binding={'action_id':action,'request_id':request,'workspace':workspace,'expected_version':expected,
                 'actor_sha256':digest(self.store.bindings[workspace]),
                 'payload_sha256':digest(json.dumps(payload,sort_keys=True,separators=(',',':')))}
        self.save(prefix+'-before.json',{'binding':binding,'sample':before})
        result=None;error=None
        try:result=self.store.execute(workspace,token,request,expected,payload,fault)
        except Exception as e:error=e
        after=self.sample(workspace,request)
        self.save(prefix+'-after.json',{'binding':binding,'sample':after,'error_class':type(error).__name__ if error else None})
        old={w['id']:w for w in before['writes']};new={w['id']:w for w in after['writes']}
        if any(new.get(key)!=value for key,value in old.items()):raise Denied('measure_audit_history_changed')
        writes=[value for key,value in new.items() if key not in old]
        wanted=[] if error or result.get('idempotent') else [(SCHEMA+'.workspaces','UPDATE'),(SCHEMA+'.revisions','INSERT'),(SCHEMA+'.requests','INSERT')]
        if collections.Counter((w['table'],w['operation']) for w in writes)!=collections.Counter(wanted):raise Denied('measure_extra_or_missing_write')
        if writes and (len({w['xid'] for w in writes})!=1 or any(w['actor_sha']!=binding['actor_sha256'] for w in writes)):
            raise Denied('measure_transaction_actor')
        if writes and [w['key_sha'] for w in writes]!=[w['key_sha'] for w in result['writes']]:raise Denied('measure_key_binding')
        pair={'binding':binding,'complete':True,'writes':writes,'expected_count':len(wanted),
              'before_version':before['version'],'after_version':after['version'],
              'before_state_sha':before['state_sha'],'after_state_sha':after['state_sha'],
              'error_class':type(error).__name__ if error else None,'parameters_exported':False}
        self.save(prefix+'-validated.json',pair)
        with self.lock:self.pairs.append(pair)
        if error:raise error
        return result
