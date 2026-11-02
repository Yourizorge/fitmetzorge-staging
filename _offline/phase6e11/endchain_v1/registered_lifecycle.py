"""Shared lifecycle for three pre-existing synthetic identities, never signup.

CI may supply an independent observer for comparison. This class creates only
the source-bound, three-identity guard and metadata observer already authorized
by the owner. Admission, transport, command escrow and JIT are caller-owned.
"""
import copy,hashlib,json,uuid
from auth_evidence import AuthEvidence
from safety_auth import SafetyAuth

class RegisteredLifecycle:
    def __init__(self,*,gate,composition,run_id,ids,guard,audit,contract_type,sql,lock_query,independent_ci=False):
        guard.scope(run_id,ids)
        self.gate=gate;self.composition=composition;self.run_id=run_id;self.ids=dict(ids)
        self.guard=guard;self.audit=audit;self.sql=sql;self.lock_query=lock_query
        if hasattr(composition,'bind_auth_scope'):composition.bind_auth_scope(run_id,ids,gate=gate)
        self.receipt=None;self.metadata_receipt=None;self.removal_attempted={'guard':False,'audit':False}
        self.install_attempted={'guard':False,'audit':False}
        self.expiry=None
        self.installed=False;self.workflow_complete=False;self.removed=False;self.failed=False
        self.evidence=AuthEvidence(run_id=run_id,ids=ids,audit=audit,contract_type=contract_type,
            sql=sql,save=gate.save,independent_ci=independent_ci,
            zero_scope=getattr(composition,'auth_zero_scope',None))
        self.safety_auth=SafetyAuth(self)
        self.worker_owned=False;self.worker_terminated=False
        self.parent_auth_attempted=False;self.parent_auth_result=None;self.parent_auth_saved=False

    def own_worker(self):
        if self.worker_owned or self.installed:raise ValueError('registered_worker_ownership')
        self.worker_owned=True

    def parent_auth_cleanup(self,*,worker_terminated):
        # Process termination blocks future child dispatch, not already-sent HTTP.
        # SafetyAuth still requires the original complete, validated mint prefix.
        if self.parent_auth_attempted:return copy.deepcopy(self.parent_auth_result)
        self.parent_auth_attempted=True;self.worker_terminated=worker_terminated is True
        result={'status':'NO_GO','revocation_confirmed':False,'global_zero_claim':False,'safe_to_remove':False,
            'worker_terminated':self.worker_terminated,'child_mint_barrier':False,'retry':False}
        removal_barrier=False
        try:
            if not self.worker_terminated:
                result['reason']='worker_termination_unconfirmed'
            else:
                owner=getattr(self.lock_query,'__self__',None)
                from registered_runner import IdentitySession
                if isinstance(owner,IdentitySession):owner.close()
                # This stops child dispatch and releases its identity lock. It
                # does not prove completion of an already-sent Auth request.
                removal_barrier=True
                meter=getattr(self.composition,'meter',None)
                if meter is not None and meter.state.get('auth_maybe_live') is False:
                    result['reason']='auth_safety_not_required_by_meter'
                elif self.removed or self.receipt is None or self.metadata_receipt is None:
                    result['reason']='auth_safety_evidence_unavailable'
                else:
                    self.failed=True
                    result.update(self.safety_auth.parent_finish(worker_terminated=True))
                    if result.get('revocation_confirmed') is True and not (
                            meter is not None and meter.state.get('auth_maybe_live') is False):
                        result.update(revocation_confirmed=False,reason='parent_auth_zero_not_confirmed')
        except Exception as error:
            result.update(reason='parent_auth_cleanup_unconfirmed',error_class=type(error).__name__)
        # Eligibility for exact temporary-object removal is separate from Auth
        # revocation. Each remover still verifies its own run/object identity.
        result.update(safe_to_remove=removal_barrier,child_mint_barrier=removal_barrier)
        self.parent_auth_result=copy.deepcopy(result)
        self.gate.save('registered-parent-auth-cleanup.json',result)
        self.parent_auth_saved=True
        return copy.deepcopy(result)

    def dispatch(self,request):
        op=request.get('op')
        if op not in {'install','query','before','after','workflow','remove','finalize','evidence_query','safetyAuthlogout'}:
            raise ValueError('registered_operation_denied')
        if self.failed and op not in ('remove','safetyAuthlogout'):raise ValueError('registered_stopped')
        try:return self._dispatch(op,request)
        except Exception:
            self.failed=True
            if hasattr(self.composition,'abort'):self.composition.abort('registered_'+str(op)+'_failure')
            raise

    def _dispatch(self,op,request):
        c=self.composition
        if op=='safetyAuthlogout':
            if request.get('stage')=='start' and request.get('receipt')==self.receipt and self.receipt is not None:
                self.failed=True
                if hasattr(c,'abort'):c.abort('safety_auth_client_stop')
            return self.safety_auth.dispatch(request)
        if op=='install':
            if self.installed or request.get('ids')!=self.ids:raise ValueError('registered_install_binding')
            self.installed=True
            c.fixture_context['temporary_schemas']=[self.guard.scope(self.run_id,self.ids),self.audit.scope(self.run_id,self.ids)]
            if hasattr(self.gate,'apply_endchain_migration'):
                from lifecycle_gates import preflight
                runtime=c.native_runtime(self.gate)
                initial=preflight(runtime,self.gate.save)
                c.admit_preflight(initial)
                c.fixture_context['migration_boundary']=len(initial['migrations'])==44
                c.preservation(self.gate,self.ids,'before')
                self.gate.save('migration-boundary-before.json',c.gate_baseline)
                c.apply_migration(self.gate)
                c.preservation(self.gate,self.ids,'after_migration')
                c.pre_auth_dry_run(self.gate)
            else:c.preservation(self.gate,self.ids,'before')
            c.current_phase='guard_install'
            self.install_attempted['guard']=True
            self.sql(self.guard.install(self.run_id,self.ids,180))
            self.receipt=self.guard.validate(json.loads(self.sql(self.guard.inspect(self.run_id,self.ids))),self.run_id,self.ids)
            self.expiry=self.receipt['expires_at']
            c.current_phase='metadata_install'
            self.install_attempted['audit']=True
            self.sql(self.audit.install(self.run_id,self.ids,self.receipt['expires_at']))
            self.metadata_receipt=self.audit.validate(json.loads(self.sql(self.audit.inspect(self.run_id,self.ids))),
                self.run_id,self.ids,self.receipt['expires_at'])
            return copy.deepcopy(self.receipt)
        if not self.installed:raise ValueError('registered_not_installed')
        if op=='remove':
            if request.get('receipt')!=self.receipt:raise ValueError('registered_removal_receipt')
            if request.get('stopped') and self.worker_owned:
                # Keep exact evidence until the parent has joined the child and
                # attempted its one-shot native suffix. No child-owned teardown.
                return {'removed':False,'deferred_to_parent':True,'commandCount':len(c.commands)}
            if not request.get('stopped'):
                if self.failed or not self.workflow_complete or any(x.step!=6 for x in self.evidence.contracts.values()):
                    raise ValueError('registered_cleanup_chain_incomplete')
                c.preservation(self.gate,self.ids,'after_cleanup')
                c.finalize(self.gate,request)
            self.close_temporary()
            if not request.get('stopped'):
                if not self.removed:raise ValueError('registered_removal_unconfirmed')
                c.preservation(self.gate,self.ids,'final_post')
            return {'removed':self.removed,'commandCount':len(c.commands)}
        if op=='finalize':
            if not self.removed or self.failed:raise ValueError('registered_close_incomplete')
            return c.close_receipt(self.gate,request)
        if op=='evidence_query':return c.evidence_query(request,self.sql)
        if self.removed or self.receipt is None or self.metadata_receipt is None:
            raise ValueError('registered_guard_not_active')
        c.current_phase=op
        if op=='query':
            c.before_sql('auth_identity_lock',request['sql'])
            value=self.lock_query(request['sql'],request['args'])
            c.after_sql('auth_identity_lock',request['sql']);return value
        if op=='before':
            if hasattr(c,'auth_before'):c.auth_before(request['role'],request['operation'])
            return self.evidence.before(request['role'],request['operation'],request['action'])
        if op=='after':
            result=self.evidence.after(request['role'],request['operation'],request['before'],request['result'])
            if hasattr(c,'auth_after'):c.auth_after(request['operation'])
            if 'registered_auth_zero' in result:
                c.confirm_auth_zero(metadata=result['registered_auth_zero'])
            return result
        if op=='workflow':
            if self.workflow_complete or any(x.step!=4 for x in self.evidence.contracts.values()):
                raise ValueError('registered_auth_prefix_incomplete')
            value=c.workflow(self.gate,request,self.sql,self.ids,self.run_id)
            if value.get('pairs')!=71 or value.get('deletes')!=123:raise ValueError('registered_workflow_incomplete')
            self.workflow_complete=True;return value

    def close_temporary(self):
        # Exact safety removal is separately authorized even after NO-GO.
        # It never deletes fixtures, accounts, historical evidence or sessions.
        if self.worker_owned and self.failed and (not self.parent_auth_attempted or not self.worker_terminated):
            raise ValueError('registered_parent_cleanup_pending')
        if self.worker_owned and self.failed and (not self.parent_auth_saved
                or not self.parent_auth_result or self.parent_auth_result.get('safe_to_remove') is not True):
            raise ValueError('registered_parent_cleanup_evidence_pending')
        c=self.composition;c.current_phase='remove';failures=[]
        for name,module,attribute in [('audit',self.audit,'metadata_receipt'),('guard',self.guard,'receipt')]:
            receipt=getattr(self,attribute)
            if not self.install_attempted[name] or self.removal_attempted[name]:continue
            self.removal_attempted[name]=True
            try:
                if receipt is None:
                    c.safety_label=('observer' if name=='audit' else 'guard')+'_inspect'
                    state=json.loads(self.sql(module.inspect(self.run_id,self.ids)))
                    try:
                        receipt=(module.validate(state,self.run_id,self.ids,active=False) if name=='guard'
                            else module.validate(state,self.run_id,self.ids,self.expiry))
                    except ValueError:
                        namespace=module.scope(self.run_id,self.ids)
                        c.safety_label=('observer' if name=='audit' else 'guard')+'_absent'
                        absent=self.sql("select (to_regnamespace('"+namespace+"') is null)::text")
                        if absent=='true':self.install_attempted[name]=False;continue
                        raise
                c.safety_label=('observer' if name=='audit' else 'guard')+'_exact_remove'
                self.sql(module.remove(self.run_id,self.ids,receipt));setattr(self,attribute,None)
                self.install_attempted[name]=False
            except Exception as error:failures.append({'object':name,'error_class':type(error).__name__})
            finally:c.safety_label=None
        self.removed=not any(self.install_attempted.values())
        if failures:
            self.gate.save('registered-removal-stop.json',{'failures':failures,'retry':False})
            raise ValueError('registered_removal_unconfirmed')
