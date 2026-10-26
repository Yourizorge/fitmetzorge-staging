"""One-shot stopped-run Auth suffix. No normal evidence or contract is resumed.

MeteredComposition implements the hooks: authorize_safety_auth(60) is a
zero-command admission check; charge_safety_auth(role,10) charges managed SQL
before HTTP; confirm_safety_auth(ticket) confirms it without a refund. Native
SQL uses the existing composition.safety_label path, with 6 slots per role
and 12 for auth_native_fallback. All seven labels together cost at most 60.
"""
import copy,uuid
from auth_evidence import AuthEvidence
from safety_auth_native import native_suffix
from safety_auth_budget import (ROLES,MANAGED_PER_ROLE,NATIVE_PER_ROLE,NATIVE_FALLBACK,
    RESERVE,reserve_required,auth_state_before,auth_state_after)


class SafetyAuth:
    def __init__(self,lifecycle):
        self.owner=lifecycle;self.started=False;self.admitted=False;self.finished=False
        self.roles=[];self.next=0;self.pending=None;self.failed=False
        self.clone=None;self.mint_terminal=False;self.keys={};self.saved=set()

    def save(self,name,value):
        name='safety-auth-'+name
        if name in self.saved:raise ValueError('safety_auth_receipt_rewrite')
        self.saved.add(name);self.owner.gate.save(name,copy.deepcopy(value))

    def dispatch(self,request):
        r=self.owner;c=r.composition;stage=request.get('stage')
        if not r.failed or r.removed or not r.receipt or not r.metadata_receipt:
            raise ValueError('safety_auth_lifecycle')
        if stage=='start':
            if self.started or request.get('receipt')!=r.receipt:
                raise ValueError('safety_auth_start_binding')
            self.started=True
            for hook in ('authorize_safety_auth','charge_safety_auth','confirm_safety_auth'):
                if not callable(getattr(c,hook,None)):raise ValueError('safety_auth_meter_not_wired')
            c.authorize_safety_auth(RESERVE)
            self.admitted=True
            e=r.evidence
            self.mint_terminal=(set(e.contracts)==set(ROLES) and not e.stopped
                and e.active is None and all(x.step==4 and not x.stopped for x in e.contracts.values()))
            self.save('start.json',{'status':'NO_GO','mint_terminal':self.mint_terminal,
                'original_pair_unchanged':True,'maximum_commands':RESERVE})
            if self.mint_terminal:
                self.keys={role:copy.deepcopy(e.contracts[role].keys) for role in ROLES}
                self.clone=AuthEvidence(run_id=r.run_id,ids=r.ids,audit=r.audit,
                    contract_type=type(e.contracts[ROLES[0]]),sql=r.sql,save=self.save,
                    independent_ci=e.independent_ci)
                self.clone.contracts=copy.deepcopy(e.contracts)
                self.roles=list(ROLES)
            return {'roles':list(self.roles),'status':'NO_GO'}
        if not self.admitted or self.finished:raise ValueError('safety_auth_sequence')
        c.current_phase='safety_auth_'+str(stage)
        c.action={'kind':'safety_auth','operation':stage}
        if stage=='finish':
            self.finished=True
            c.safety_label='auth_native_fallback'
            try:
                result=native_suffix(r,self.save,self.keys,self.mint_terminal)
            finally:c.safety_label=None
            self.save('result.json',result)
            c.safety_auth_result=copy.deepcopy(result)
            if result.get('revocation_confirmed') is True:
                c.confirm_auth_zero(safety_receipt=result)
            return result
        if stage not in ('before','after') or self.failed or self.next>=len(self.roles):
            raise ValueError('safety_auth_sequence')
        role=request.get('role')
        if role!=self.roles[self.next]:raise ValueError('safety_auth_role_order')
        c.action['role']=role
        c.safety_label='auth_logout_'+role
        try:
            if stage=='before':
                if self.pending is not None:raise ValueError('safety_auth_pending')
                # Charge before any HTTP permission is returned. Never refund it.
                ticket=c.charge_safety_auth(role,MANAGED_PER_ROLE)
                action=str(uuid.uuid5(uuid.UUID(r.run_id),'safety-auth-logout:'+role))
                before=self.clone.before(role,'logout',action)
                self.pending={'role':role,'before':before,'ticket':ticket}
                return {'allowed':True,'action_id':action}
            if self.pending is None:raise ValueError('safety_auth_no_pending')
            value=self.clone.after(role,'logout',self.pending['before'],request['result'])
            c.confirm_safety_auth(self.pending['ticket'])
            self.pending=None;self.next+=1
            return value
        except Exception:
            self.failed=True
            raise
        finally:c.safety_label=None
