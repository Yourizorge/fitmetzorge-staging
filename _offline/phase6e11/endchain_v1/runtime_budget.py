"""Runtime enforcement of the source-bound complete register, before execution.

This module performs no SQL and grants no admission. Every actual native command
and each managed-Auth allowance must pass this same meter. A stop never resets it.
"""
import collections,copy,time
from complete_register import PHASES,safety_path
from closure import RUN_ID,PURPOSE,allowance

class BudgetStop(RuntimeError):pass

class RuntimeBudget:
    def __init__(self,register,*,run_id,purpose,clock=time.monotonic):
        if (run_id,purpose)!=(RUN_ID,PURPOSE) or register.get('run_id')!=run_id or register.get('purpose')!=purpose:
            raise BudgetStop('runtime_reserved_run_binding')
        if not register.get('complete_register') or register.get('approved_limit')!=allowance(run_id,purpose) or not register.get('fits'):
            raise BudgetStop('runtime_register_admission')
        limits=register.get('phase_budgets',{})
        if set(limits)!=set(PHASES) or any(type(v) is not int or v<1 for v in limits.values()):
            raise BudgetStop('runtime_phase_budget')
        if sum(limits.values())!=register.get('normal_capacity') or register.get('worst_including_safety',99999)>allowance(run_id,purpose):
            raise BudgetStop('runtime_complete_capacity')
        self.limit=allowance(run_id,purpose);self.limits=dict(limits);self.clock=clock;self.started=clock()
        self.used=0;self.phases=collections.Counter();self.events=[];self.stopped=False;self.closed=False
        self.state={'guard':False,'observer':False,'controls':False,'claimed':False,'auth_maybe_live':False}
        self.state.update(guard_remove_attempted=False,observer_remove_attempted=False)
        self.safety_spent=collections.Counter();self.pending=None;self.stop_reason=None
        self.managed_pending={}
        self.safety_pending={};self.state_confirmations=[]

    def _reserve(self,phases,state):
        normal=sum(max(0,self.limits[p]-phases[p]) for p in ('cleanup','final','closure'))
        emergency=sum(x['sql'] for x in safety_path(**state))
        return max(normal,emergency)

    def charge(self,phase,count,*,action,kind='native',state_after=None,mutation=False):
        try:return self._charge(phase,count,action=action,kind=kind,state_after=state_after,mutation=mutation)
        except BudgetStop as error:
            self.stop(str(error));raise

    def _charge(self,phase,count,*,action,kind,state_after,mutation):
        if self.stopped or self.closed:raise BudgetStop('runtime_stopped_no_new_action')
        if self.pending is not None:raise BudgetStop('runtime_unconfirmed_command')
        if phase not in self.limits or type(count) is not int or count<1 or kind not in ('native','managed_auth','cli_bound','cli_reserved'):
            raise BudgetStop('runtime_command_shape')
        if type(action) is not str or not action or len(action)>120:raise BudgetStop('runtime_action_shape')
        elapsed=self.clock()-self.started
        if elapsed<0 or elapsed>=540:raise BudgetStop('runtime_ordinary_deadline')
        projected=self.phases.copy();projected[phase]+=count
        state={**self.state,**(state_after or {})}
        if set(state)!=set(self.state) or any(type(v) is not bool for v in state.values()):raise BudgetStop('runtime_state_shape')
        if (state_after or {}).get('auth_maybe_live') is False:
            raise BudgetStop('runtime_auth_release_requires_known_zero')
        if (state_after or {}).get('controls') is False:
            raise BudgetStop('runtime_control_release_requires_confirmation')
        if any((state_after or {}).get(k) is False for k in ('guard','observer')):
            raise BudgetStop('runtime_temporary_release_requires_known_zero')
        reserve=self._reserve(projected,state)
        if projected[phase]>self.limits[phase]:raise BudgetStop('runtime_phase_exhausted_'+phase)
        if self.used+count>self.limit or (mutation and self.used+count+reserve>self.limit):
            raise BudgetStop('runtime_cleanup_reserve')
        event={'number':len(self.events)+1,'first_command':self.used+1,'commands':count,
            'phase':phase,'action':action,'kind':kind,'mutation':mutation,'reserved_cleanup':reserve,
            'confirmed':False,'elapsed_ms':round(elapsed*1000)}
        self.used+=count;self.phases=projected;self.state=state;self.events.append(event)
        if kind=='managed_auth':self.managed_pending[event['number']]=event
        else:self.pending=event
        return event['number']

    def confirm(self,number,*,actual=None):
        managed=number in self.managed_pending
        event=self.managed_pending[number] if managed else self.pending
        if event is None or event['number']!=number:raise BudgetStop('runtime_confirmation_binding')
        if actual is not None and (type(actual) is not int or actual!=event['commands']):
            if type(actual) is int and actual>=0:
                event['actual_commands']=actual
                extra=max(0,actual-event['commands'])
                self.used+=extra;self.phases[event['phase']]+=extra
            self.stop('managed_command_count_mismatch');raise BudgetStop('managed_command_count_mismatch')
        event['confirmed']=True
        if managed:del self.managed_pending[number]
        else:self.pending=None

    def stop(self,reason):
        self.stopped=True
        if self.stop_reason is None:self.stop_reason=reason
        if self.pending:self.pending['stop_reason']=reason;self.pending=None

    def safety(self,action,count,*,kind='native'):
        if self.closed or not self.stopped:raise BudgetStop('runtime_safety_state')
        elapsed=self.clock()-self.started
        if elapsed<0 or elapsed>=600:raise BudgetStop('runtime_safety_deadline')
        allowed={x['action']:x for x in safety_path(**self.state)}
        if (type(count) is not int or count<1 or action not in allowed
                or kind!=allowed[action]['kind'] or self.safety_spent[action]+count>allowed[action]['sql']):
            raise BudgetStop('runtime_safety_action')
        if self.used+count>self.limit:raise BudgetStop('runtime_safety_ceiling')
        self.safety_spent[action]+=count;self.used+=count
        self.events.append({'number':len(self.events)+1,'first_command':self.used-count+1,
            'commands':count,'phase':'safety','action':action,'kind':kind,'confirmed':False})
        self.safety_pending[self.events[-1]['number']]=self.events[-1]
        return self.events[-1]['number']

    def confirm_safety(self,number,*,actual=None):
        event=self.safety_pending.get(number)
        if event is None or event['phase']!='safety' or event['confirmed']:
            raise BudgetStop('runtime_safety_confirmation')
        if actual is not None and (type(actual) is not int or actual!=event['commands']):
            if type(actual) is int and actual>=0:
                event['actual_commands']=actual;extra=max(0,actual-event['commands'])
                self.used+=extra;self.safety_spent[event['action']]+=extra
            self.stop('safety_managed_command_count_mismatch')
            raise BudgetStop('runtime_safety_command_count_mismatch')
        event['confirmed']=True
        del self.safety_pending[number]

    def confirm_auth_zero(self):
        if self.closed or not self.state['auth_maybe_live']:
            raise BudgetStop('runtime_auth_zero_state')
        self.state['auth_maybe_live']=False
        self.state_confirmations.append({'after_command':self.used,'state':'auth_maybe_live','value':False,
            'reason':'validated_terminal_auth_zero','sql':0})

    def close(self):
        if self.state['auth_maybe_live'] and not self.stopped:
            raise BudgetStop('runtime_auth_zero_unconfirmed')
        if self.pending is not None or (self.managed_pending and not self.stopped):
            raise BudgetStop('runtime_final_unconfirmed')
        self.closed=True
        return self.receipt()

    def confirm_temporary_absence(self):
        if self.closed or self.pending is not None:raise BudgetStop('runtime_absence_unconfirmed')
        self.state.update(guard=False,observer=False)
        self.state_confirmations.append({'after_command':self.used,'state':'temporary_absence',
            'value':False,'reason':'validated_metadata_absence','sql':0})

    def confirm_controls_restored(self):
        if self.closed or self.pending is not None or not self.state['controls']:
            raise BudgetStop('runtime_controls_unconfirmed')
        self.state['controls']=False
        self.state_confirmations.append({'after_command':self.used,'state':'controls',
            'value':False,'reason':'validated_original_controls','sql':0})

    def receipt(self):
        """Observe an incomplete run without closing or authorizing any action."""
        return {'used':self.used,'limit':self.limit,'phases':dict(self.phases),
            'state':dict(self.state),'state_confirmations':copy.deepcopy(self.state_confirmations),
            'safety':dict(self.safety_spent),'stopped':self.stopped,'stop_reason':self.stop_reason,
            'complete':all(x['confirmed'] for x in self.events),'events':copy.deepcopy(self.events)}
