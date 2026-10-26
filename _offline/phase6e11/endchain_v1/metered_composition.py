"""The shared executor, with pre-execution phase and emergency accounting.

The three CLI/unknown envelopes are reservations, not observed session commands.
Fresh complete CI must recompute every prefix and agree before hosted admission.
"""
import copy,uuid
from integral_ci import Composition
from complete_register import classify,scenario_source,AUTH_CALLS,safety_path
from safety_auth_budget import ROLES,RESERVE,MANAGED_PER_ROLE,auth_state_before
from runtime_budget import RuntimeBudget
from closure import RUN_ID,PURPOSE,BOOTSTRAP,allowance
from cli_envelope import CHARGE,DRY_CAP,OBSERVERS,charged

LIMITS=dict(preflight=4,migration=128,baseline=61,setup=33,guard=13,auth=318,controller=286,
    route_a=191,route_b=286,restore=54,measurements=136,io=97,cleanup=633,final=97,closure=1)

def capacity():
    return dict(complete_register=True,approved_limit=allowance(RUN_ID,PURPOSE),fits=True,run_id=RUN_ID,purpose=PURPOSE,
        phase_budgets=dict(LIMITS),normal_capacity=2338,worst_including_safety=2349)

class MeteredComposition(Composition):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.meter=RuntimeBudget(capacity(),run_id=RUN_ID,purpose=PURPOSE)
        self.meter_stack=[];self.managed_auth_ticket=None;self.safety_label=None
        self.managed_auth_binding=None;self.auth_scope_run_id=None;self.auth_scope_ids=None
        self.auth_prefix_roles=set();self.auth_terminal_roles=set();self.auth_zero_proof=None
        self.safety_auth_started=False;self.safety_auth_tickets={};self.safety_auth_result=None
        self.auth_zero_scope=None
        self.scenario=scenario_source.capture()['workflow_actions']

    def admit_ci_prefix(self,preflight,cli):
        if len(preflight['commands'])!=4 or not all(x['confirmed'] for x in preflight['commands']):
            raise ValueError('meter_ci_preflight_missing')
        charged(cli)
        for phase,n in [('preflight',4),('migration',CHARGE)]:
            ticket=self.meter.charge(phase,n,action='verified_disposable_ci_prefix',kind='cli_bound')
            self.meter.confirm(ticket)

    def admit_preflight(self,preflight):
        if len(preflight['commands'])!=4 or not all(x['confirmed'] for x in preflight['commands']):
            raise ValueError('meter_preflight_missing')
        ticket=self.meter.charge('preflight',4,action='verified_preflight',kind='cli_bound')
        self.meter.confirm(ticket)

    def apply_migration(self,gate):
        ticket=self.meter.charge('migration',CHARGE,action='candidate_quota_migration_aware_cli',kind='cli_reserved',mutation=True)
        receipt=gate.apply_endchain_migration()
        if charged(receipt)!=CHARGE:
            self.abort('migration_protocol_incomplete');raise ValueError('migration_protocol_incomplete')
        self.meter.confirm(ticket)

    def abort(self,reason):
        self.meter.stop(reason)

    def pre_auth_dry_run(self,gate):
        ticket=self.meter.charge('migration',DRY_CAP+OBSERVERS,action='pre_auth_empty_cli_dry_run',kind='cli_reserved')
        gate.cli('db','push','--local','--dry-run','--skip-vault')
        receipt=gate.cli_protocol[-1]
        if receipt.get('slot')!='pre_auth' or charged(receipt)!=DRY_CAP+OBSERVERS:
            self.abort('pre_auth_dry_run_incomplete');raise ValueError('pre_auth_dry_run_incomplete')
        self.meter.confirm(ticket)

    def before_sql(self,phase,sql):
        from sql_protocol import statements
        count=len(statements(sql));ticket=None;safety=False;removal=None
        if phase=='remove' and self.safety_label in ('guard_exact_remove','observer_exact_remove'):
            removal=self.safety_label.removesuffix('_exact_remove')
            if count!=5 or self.meter.state[removal+'_remove_attempted']:
                raise ValueError('meter_removal_replay_or_shape')
        if phase not in BOOTSTRAP:
            if phase.startswith('safety_') and not self.meter.stopped:self.abort('workflow_safety_close')
            if self.meter.stopped:
                labels={'safety_control_before':'control_before','safety_control_restore':'control_compare_restore',
                    'safety_control_after':'control_after'}
                label=self.safety_label or labels.get(phase)
                if label is None and phase in ('controller_evidence','evidence_query') and sql.startswith(
                    "/* fmz6e11:controller_v1:evidence */ with r as (update fmz6e11_controller_private.runs set state='stopped'"):
                    label='durable_stop'
                if not label:raise ValueError('meter_unknown_safety_action')
                ticket=self.meter.safety(label,count);safety=True
                if removal:self.meter.state[removal+'_remove_attempted']=True
            else:
                effective='final_closure' if self.closing_receipt is not None else phase
                name=classify({'phase':effective,'action':self.action},self.scenario)
                state={}
                if phase=='guard_install':state['guard']=True
                if phase=='metadata_install':state['observer']=True
                if phase=='control_enable':state['controls']=True
                if phase=='evidence_query':state['claimed']=True
                if removal:state[removal+'_remove_attempted']=True
                ticket=self.meter.charge(name,count,action=effective,state_after=state,
                    mutation=True)
        super().before_sql(phase,sql)
        if removal:self.commands[-count]['removal_precharged']={'object':removal,'commands':count}
        self.meter_stack.append((ticket,safety))

    def after_sql(self,phase,sql):
        super().after_sql(phase,sql)
        ticket,safety=self.meter_stack.pop()
        if ticket is not None:
            if safety:self.meter.confirm_safety(ticket)
            else:self.meter.confirm(ticket)

    def auth_before(self,role,operation):
        if self.managed_auth_ticket is not None:raise ValueError('meter_auth_overlap')
        if role not in ROLES or operation not in AUTH_CALLS:raise ValueError('meter_auth_binding')
        phase='cleanup' if operation in ('logout','revoked_denial') else 'auth'
        self.managed_auth_ticket=self.meter.charge(phase,AUTH_CALLS[operation],
            action='gotrue_'+role+'_'+operation,kind='managed_auth',mutation=True,
            state_after={'auth_maybe_live':True} if auth_state_before(False,operation) else None)
        self.managed_auth_binding=(role,operation)

    def auth_after(self,operation):
        if self.managed_auth_binding is None or self.managed_auth_binding[1]!=operation:
            raise ValueError('meter_auth_confirmation_binding')
        role=self.managed_auth_binding[0]
        self.meter.confirm(self.managed_auth_ticket,actual=AUTH_CALLS[operation])
        if operation=='refresh':self.auth_prefix_roles.add(role)
        if operation=='revoked_denial':self.auth_terminal_roles.add(role)
        self.managed_auth_ticket=None;self.managed_auth_binding=None

    def bind_auth_scope(self,run_id,ids,*,gate=None):
        if self.auth_scope_run_id is not None:raise ValueError('meter_auth_scope_rebind')
        if set(ids)!=set(ROLES) or len(set(ids.values()))!=3:raise ValueError('meter_auth_scope')
        for value in [run_id,*ids.values()]:
            if str(uuid.UUID(value))!=value:raise ValueError('meter_auth_scope')
        self.auth_scope_run_id=run_id;self.auth_scope_ids=dict(ids)
        from auth_zero import scope
        runtime=getattr(gate,'runtime',None) or self.runtime
        environment=runtime.environment if runtime is not None else 'disposable_ci'
        self.auth_zero_scope=scope(ids,environment,getattr(gate,'sources',None))

    def authorize_safety_auth(self,count):
        m=self.meter
        if (count!=RESERVE or self.safety_auth_started or self.auth_scope_run_id is None
                or not m.stopped or m.closed or not m.state['auth_maybe_live']):
            raise ValueError('meter_safety_auth_state')
        elapsed=m.clock()-m.started
        if elapsed<0 or elapsed>=600:raise ValueError('meter_safety_auth_deadline')
        remaining=sum(max(0,x['sql']-m.safety_spent[x['action']]) for x in safety_path(**m.state))
        if m.used+remaining>m.limit:raise ValueError('meter_safety_auth_capacity')
        self.safety_auth_started=True

    def charge_safety_auth(self,role,count):
        if (not self.safety_auth_started or role not in ROLES or count!=MANAGED_PER_ROLE
                or role in self.safety_auth_tickets):raise ValueError('meter_safety_auth_managed_binding')
        ticket=self.meter.safety('auth_logout_managed_'+role,count,kind='managed_auth')
        self.safety_auth_tickets[role]=ticket
        return ticket

    def confirm_safety_auth(self,ticket):
        if ticket not in self.safety_auth_tickets.values():raise ValueError('meter_safety_auth_ticket')
        self.meter.confirm_safety(ticket,actual=MANAGED_PER_ROLE)

    def confirm_auth_zero(self,*,safety_receipt=None,metadata=None):
        # Called only AFTER the caller has validated the metadata response.
        # Ordinary SQL precharge/after_sql cannot release this state.
        if safety_receipt is None:
            if self.meter.stopped or self.auth_terminal_roles!=set(ROLES):
                raise ValueError('meter_auth_zero_not_terminal')
            from auth_zero import validate
            fields={'manifest_sha256','manifest_count','registered_count','scope_count',
                'extra_registered_count','sessions','refresh_tokens'}
            if metadata is None:raise ValueError('meter_auth_zero_metadata_required')
            verified=validate({k:metadata[k] for k in fields if k in metadata},self.auth_zero_scope)
            proof={'source':'validated_final_auth_after','metadata':verified}
        else:
            r=safety_receipt
            if (not self.meter.stopped or not self.safety_auth_started or self.auth_prefix_roles!=set(ROLES)
                    or r.get('run_id')!=self.auth_scope_run_id or r.get('status')!='NO_GO'
                    or r.get('reason')!='exact_three_account_session_zero'
                    or any(r.get(k) is not True for k in ('mint_terminal','revocation_confirmed','commit_confirmed'))
                    or r.get('global_zero_claim') is not False
                    or type(r.get('native_commands')) is not int or not 1<=r['native_commands']<=12):
                raise ValueError('meter_safety_auth_zero_unconfirmed')
            proof={'source':'validated_safety_native','receipt':copy.deepcopy(r),'role_count':3}
        if safety_receipt is None:
            if not self.commands or not self.commands[-1]['confirmed']:
                raise ValueError('meter_auth_zero_trace_missing')
        self.meter.confirm_auth_zero();self.auth_zero_proof=proof
        if safety_receipt is None:
            self.commands[-1]['auth_zero_validated']=True

    def temporary_absence_confirmed(self):
        super().temporary_absence_confirmed()
        self.meter.confirm_temporary_absence()

    def confirm_controls_restored(self,restored,expected):
        super().confirm_controls_restored(restored,expected)
        self.meter.confirm_controls_restored()

    def workflow(self,*args,**kwargs):
        tickets=[self.meter.charge('setup',5,action='gotrue_fixture_identity',kind='managed_auth')]
        for step in range(71):
            phase='cleanup' if step>=45 else 'restore' if 'restore' in self.scenario[step]['request']['action'] else 'route_a' if self.scenario[step]['route']=='A' else 'route_b'
            tickets.append(self.meter.charge(phase,5,action='gotrue_workflow_identity_'+str(step),kind='managed_auth'))
        result=super().workflow(*args,**kwargs)
        # The shared workflow verifies exactly 72 /user calls and 360 managed
        # commands with zero temp writes before returning. No refund on failure.
        for ticket in tickets:self.meter.confirm(ticket,actual=5)
        return result

    def finalize(self,gate,request):
        ticket=self.meter.charge('final',DRY_CAP+OBSERVERS,action='empty_cli_dry_run',kind='cli_reserved')
        result=super().finalize(gate,request)
        self.meter.confirm(ticket)
        return result

    def confirm_closure(self,gate,result):
        super().confirm_closure(gate,result)
        evidence=self.meter.close()
        gate.save('runtime-command-meter.json',evidence)
        if not evidence['complete'] or evidence['used']!=self.closing_receipt['global_commands']:
            raise ValueError('meter_closure_count_mismatch')
