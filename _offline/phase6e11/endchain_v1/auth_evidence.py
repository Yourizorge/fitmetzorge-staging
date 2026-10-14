"""Scoped Auth write evidence. Optional independent observer exists only in CI.

Only registered technical row hashes are retained. The aggregate Auth-role SQL
delta is a conservative bound, not attribution of unrelated background traffic.
"""
import copy,hashlib,json,uuid
from auth_protocol import STATS,difference
from complete_register import AUTH_CALLS

class AuthEvidence:
    def __init__(self,*,run_id,ids,audit,contract_type,sql,save,independent_ci=False):
        self.run_id=run_id;self.ids=dict(ids);self.audit=audit;self.sql=sql;self.save=save
        self.independent_ci=independent_ci;self.active=None;self.receipts=[];self.stopped=False
        self.contracts={r:contract_type(hashlib.sha256(ids[r].encode()).hexdigest()) for r in ids}

    def before(self,role,operation,action):
        if self.stopped or self.active is not None:raise ValueError('auth_evidence_not_ready')
        if role not in self.ids or operation not in AUTH_CALLS or str(uuid.UUID(action))!=action:
            raise ValueError('auth_evidence_scope')
        self.sql(self.audit.arm(self.run_id,self.ids,action,role,operation))
        if json.loads(self.sql(self.audit.events(self.run_id,self.ids,action)))!=[]:
            self.stopped=True;raise ValueError('auth_evidence_before_not_empty')
        seq='(select coalesce(max(seq),0) from fmz_ci_auth_observer.events)' if self.independent_ci else '0'
        value=json.loads(self.sql("select jsonb_build_object('seq',"+seq+",'auth_stats',"+STATS+")::text"))
        value['action']=action
        self.active={'role':role,'operation':operation,'before':copy.deepcopy(value)}
        self.save('auth-before-%02d.json'%len(self.receipts),{'role':role,'operation':operation,
            'action_id':action,'stats':value['auth_stats'],'rows':[]})
        return value

    def after(self,role,operation,before,result):
        active=self.active
        if self.stopped or active is None or (role,operation,before)!=(active['role'],active['operation'],active['before']):
            raise ValueError('auth_evidence_pair_binding')
        self.active=None
        try:
            # In staging the fixed scoped audit is the observation source. CI
            # additionally checks it against an all-Auth observer; that broad
            # observer is never installed by this runtime.
            if self.independent_ci:
                events_sql='select table_name,operation,xid,key_sha,actor_sha from fmz_ci_auth_observer.events where seq>'+str(int(before['seq']))+' order by seq'
                combined=json.loads(self.sql("select jsonb_build_object('events',(select coalesce(jsonb_agg(e),'[]') from ("+events_sql+") e),'auth_stats',"+STATS+")::text"))
            else:
                combined=json.loads(self.sql("select jsonb_build_object('auth_stats',"+STATS+")::text"))
            observed=json.loads(self.sql(self.audit.events(self.run_id,self.ids,before['action'])))
            captured={'role':role,'operation':operation,'action_id':before['action'],'events':observed,
                'after_stats':combined['auth_stats'],'pair_complete':False,'independent_ci':self.independent_ci}
            self.save('auth-after-%02d.json'%len(self.receipts),captured)
            load=difference(before['auth_stats'],combined['auth_stats'])
            load['scope']='disposable CI GoTrue role' if self.independent_ci else 'whole Auth role; conservative bound, background not separately attributed'
            self.save('auth-protocol-%02d.json'%len(self.receipts),{'role':role,'operation':operation,**load})
            if load['commands']!=AUTH_CALLS[operation]:raise ValueError('auth_command_bound_mismatch')
            if self.independent_ci:
                keys=('table_name','operation','xid','key_sha','actor_sha')
                if sorted(tuple(e[k] for k in keys) for e in combined['events'])!=sorted(tuple(e[k] for k in keys) for e in observed):
                    raise ValueError('auth_independent_observer_mismatch')
            check=self.contracts[role].validate(operation,observed,result.get('key_sha'))
            self.sql(self.audit.disarm(self.run_id,self.ids,before['action']))
            captured.update(pair_complete=True,contract=check)
            self.save('auth-pair-%02d.json'%len(self.receipts),captured)
            self.receipts.append(captured)
            return {'events':observed,'pair_complete':True,'exact_contract':True}
        except Exception:
            self.stopped=True;raise
