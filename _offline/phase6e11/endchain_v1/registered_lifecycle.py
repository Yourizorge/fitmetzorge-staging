"""Shared lifecycle for three pre-existing synthetic identities, never signup.

CI may supply an independent observer for comparison. This class creates only
the source-bound, three-identity guard and metadata observer already authorized
by the owner. Admission, transport, command escrow and JIT are caller-owned.
"""
import copy,hashlib,json,uuid
from auth_evidence import AuthEvidence

class RegisteredLifecycle:
    def __init__(self,*,gate,composition,run_id,ids,guard,audit,contract_type,sql,lock_query,independent_ci=False):
        guard.scope(run_id,ids)
        self.gate=gate;self.composition=composition;self.run_id=run_id;self.ids=dict(ids)
        self.guard=guard;self.audit=audit;self.sql=sql;self.lock_query=lock_query
        self.receipt=None;self.metadata_receipt=None;self.removal_attempted={'guard':False,'audit':False}
        self.install_attempted={'guard':False,'audit':False}
        self.expiry=None
        self.installed=False;self.workflow_complete=False;self.removed=False;self.failed=False
        self.evidence=AuthEvidence(run_id=run_id,ids=ids,audit=audit,contract_type=contract_type,
            sql=sql,save=gate.save,independent_ci=independent_ci)

    def dispatch(self,request):
        op=request.get('op')
        if op not in {'install','query','before','after','workflow','remove','finalize','evidence_query'}:
            raise ValueError('registered_operation_denied')
        if self.failed and op!='remove':raise ValueError('registered_stopped')
        try:return self._dispatch(op,request)
        except Exception:
            self.failed=True
            if hasattr(self.composition,'abort'):self.composition.abort('registered_'+str(op)+'_failure')
            raise

    def _dispatch(self,op,request):
        c=self.composition
        if op=='install':
            if self.installed or request.get('ids')!=self.ids:raise ValueError('registered_install_binding')
            self.installed=True
            c.fixture_context['temporary_schemas']=[self.guard.scope(self.run_id,self.ids),self.audit.scope(self.run_id,self.ids)]
            c.preservation(self.gate,self.ids,'before')
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
            self.close_temporary()
            if not request.get('stopped'):
                if self.failed or not self.workflow_complete or any(x.step!=6 for x in self.evidence.contracts.values()):
                    raise ValueError('registered_cleanup_chain_incomplete')
                c.preservation(self.gate,self.ids,'after_cleanup')
            return {'removed':self.removed,'commandCount':len(c.commands)}
        if op=='finalize':
            if not self.removed or self.failed:raise ValueError('registered_close_incomplete')
            return c.finalize(self.gate,request)
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
