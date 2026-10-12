"""Exact predeclared GoTrue v2.196.0 effects; not a hosted compatibility claim."""
from collections import Counter
import re

COUNTS={
 'issue':{('users','UPDATE'):1,('audit_log_entries','INSERT'):1,('one_time_tokens','INSERT'):1},
 'verify':{('users','UPDATE'):3,('audit_log_entries','INSERT'):1,('one_time_tokens','DELETE'):1,('sessions','INSERT'):1,('refresh_tokens','INSERT'):1,('mfa_amr_claims','INSERT'):1},
 'getUser':{},
 'refresh':{('users','UPDATE'):1,('audit_log_entries','INSERT'):2,('sessions','UPDATE'):1,('refresh_tokens','UPDATE'):1,('refresh_tokens','INSERT'):1},
 'logout':{('audit_log_entries','INSERT'):1,('sessions','DELETE'):1,('refresh_tokens','DELETE'):2,('mfa_amr_claims','DELETE'):1},
 'revoked_denial':{}}
SEQUENCE=tuple(COUNTS)
HASH=re.compile('[a-f0-9]{64}')

class Contract:
    def __init__(self,actor_sha):
        if not HASH.fullmatch(actor_sha):raise ValueError('auth_contract_actor')
        self.actor=actor_sha;self.step=0;self.stopped=False;self.keys={};self.seen=set()
    def validate(self,operation,events,session_sha=None):
        if self.stopped:raise ValueError('auth_contract_stopped')
        try:return self._validate(operation,events,session_sha)
        except Exception:self.stopped=True;raise
    def _validate(self,operation,events,session_sha):
        if self.step>=len(SEQUENCE) or operation!=SEQUENCE[self.step]:raise ValueError('auth_contract_sequence')
        actual=Counter((e['table_name'],e['operation']) for e in events)
        expected=Counter({('auth.'+t,o):n for (t,o),n in COUNTS[operation].items()})
        if actual!=expected:raise ValueError('auth_contract_write_multiset')
        if events and len({e['xid'] for e in events})!=1:raise ValueError('auth_contract_transaction')
        if any(e['actor_sha']!=self.actor or not HASH.fullmatch(e['key_sha']) for e in events):raise ValueError('auth_contract_row_owner')
        grouped={}
        for e in events:grouped.setdefault((e['table_name'].split('.')[1],e['operation']),[]).append(e['key_sha'])
        for e in events:
            if e['table_name']=='auth.users' and e['key_sha']!=self.actor:raise ValueError('auth_contract_user_key')
        def keys(table,op):return grouped.get((table,op),[])
        def one(table,op):return keys(table,op)[0]
        if operation=='issue':self.keys['link']=one('one_time_tokens','INSERT')
        if operation=='verify':
            if one('one_time_tokens','DELETE')!=self.keys['link']:raise ValueError('auth_contract_link_delete')
            if not isinstance(session_sha,str) or not HASH.fullmatch(session_sha) or one('sessions','INSERT')!=session_sha:raise ValueError('auth_contract_session')
            self.keys.update(session=session_sha,refresh=one('refresh_tokens','INSERT'),amr=one('mfa_amr_claims','INSERT'))
        if operation=='refresh':
            if session_sha!=self.keys['session'] or one('sessions','UPDATE')!=session_sha or one('refresh_tokens','UPDATE')!=self.keys['refresh']:raise ValueError('auth_contract_refresh_binding')
            fresh=one('refresh_tokens','INSERT')
            if fresh==self.keys['refresh']:raise ValueError('auth_contract_refresh_reuse')
            self.keys['fresh']=fresh
        if operation=='logout':
            if session_sha!=self.keys['session'] or one('sessions','DELETE')!=session_sha or one('mfa_amr_claims','DELETE')!=self.keys['amr'] or Counter(keys('refresh_tokens','DELETE'))!=Counter([self.keys['refresh'],self.keys['fresh']]):raise ValueError('auth_contract_delete_binding')
        for table,op in grouped:
            if op=='INSERT':
                for key in keys(table,op):
                    if (table,key) in self.seen:raise ValueError('auth_contract_duplicate_insert')
                    self.seen.add((table,key))
        self.step+=1
        return {'operation':operation,'writes':len(events),'exact_multiset':True,'delete_binding':operation in ('verify','logout'),'complete':self.step==6}
