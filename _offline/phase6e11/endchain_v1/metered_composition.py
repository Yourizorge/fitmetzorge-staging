"""The shared executor, with pre-execution phase and emergency accounting.

The two CLI/unknown envelopes are reservations, not observed session commands.
Fresh complete CI must recompute every prefix and agree before hosted admission.
"""
from integral_ci import Composition
from complete_register import classify,scenario_source,AUTH_CALLS
from runtime_budget import RuntimeBudget
from closure import RUN_ID,PURPOSE,BOOTSTRAP,allowance
from cli_envelope import CHARGE,charged

LIMITS=dict(preflight=4,migration=92,baseline=61,setup=33,guard=13,auth=318,controller=286,
    route_a=191,route_b=286,restore=54,measurements=136,io=97,cleanup=633,final=133,closure=1)

def capacity():
    return dict(complete_register=True,approved_limit=allowance(RUN_ID,PURPOSE),fits=True,run_id=RUN_ID,purpose=PURPOSE,
        phase_budgets=dict(LIMITS),normal_capacity=2338,worst_including_safety=2349)

class MeteredComposition(Composition):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.meter=RuntimeBudget(capacity(),run_id=RUN_ID,purpose=PURPOSE)
        self.meter_stack=[];self.managed_auth_ticket=None;self.safety_label=None
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

    def before_sql(self,phase,sql):
        from sql_protocol import statements
        count=len(statements(sql));ticket=None;safety=False
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
            else:
                effective='final_closure' if self.closing_receipt is not None else phase
                name=classify({'phase':effective,'action':self.action},self.scenario)
                state={}
                if phase=='guard_install':state['guard']=True
                if phase=='metadata_install':state['observer']=True
                if phase=='control_enable':state['controls']=True
                if phase=='evidence_query':state['claimed']=True
                if phase=='control_restored':state['controls']=False
                if phase=='gates_after_cleanup_absence':state=dict(guard=False,observer=False,controls=False)
                ticket=self.meter.charge(name,count,action=effective,state_after=state,
                    mutation=True)
        super().before_sql(phase,sql)
        self.meter_stack.append((ticket,safety))

    def after_sql(self,phase,sql):
        super().after_sql(phase,sql)
        ticket,safety=self.meter_stack.pop()
        if ticket is not None:
            if safety:self.meter.confirm_safety(ticket)
            else:self.meter.confirm(ticket)

    def auth_before(self,role,operation):
        if self.managed_auth_ticket is not None:raise ValueError('meter_auth_overlap')
        phase='cleanup' if operation in ('logout','revoked_denial') else 'auth'
        self.managed_auth_ticket=self.meter.charge(phase,AUTH_CALLS[operation],
            action='gotrue_'+role+'_'+operation,kind='managed_auth',mutation=True)

    def auth_after(self,operation):
        self.meter.confirm(self.managed_auth_ticket,actual=AUTH_CALLS[operation])
        self.managed_auth_ticket=None

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
        ticket=self.meter.charge('final',CHARGE,action='empty_cli_dry_run',kind='cli_reserved')
        result=super().finalize(gate,request)
        self.meter.confirm(ticket)
        return result

    def confirm_closure(self,gate,result):
        super().confirm_closure(gate,result)
        evidence=self.meter.close()
        gate.save('runtime-command-meter.json',evidence)
        if not evidence['complete'] or evidence['used']!=self.closing_receipt['global_commands']:
            raise ValueError('meter_closure_count_mismatch')
