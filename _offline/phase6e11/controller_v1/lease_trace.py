"""Fixed request-phase journal; dependency-injected, no credential retrieval."""
import re,time
PROJECT='mokxyyullfhkfalopbzd'

class LeaseFailure(RuntimeError):
    def __init__(self,phase,status):
        self.phase=phase;self.status=status
        super().__init__('jit_request_rejected')

def request(api,save,phase,path,method='GET',body=None):
    save(phase+'-started',{'phase':phase,'method':method,'at_ms':int(time.time()*1000)})
    try:value=api(path,method,body)
    except Exception as error:
        match=re.fullmatch('management_http_([0-9]{3})',str(error))
        status=int(match[1]) if match else None
        save(phase+'-failed',{'phase':phase,'http_status':status,'error_class':'management_rejected' if status else 'management_transport','at_ms':int(time.time()*1000)})
        raise LeaseFailure(phase,status) from None
    save(phase+'-confirmed',{'phase':phase,'at_ms':int(time.time()*1000)})
    return value

def inspect_closed(api,save):
    root='/v1/projects/'+PROJECT
    state=request(api,save,'jit_state_read',root+'/jit-access')
    mappings=request(api,save,'jit_mapping_list',root+'/database/jit/list')
    if state.get('state')!='disabled' or mappings.get('items')!=[]:raise LeaseFailure('preflight_not_closed',None)
    return {'jit_state':'disabled','remaining_mappings':0}

def grant_once(api,save,owner,expires):
    # Called only after a separately verified owner and closed-state inspection.
    # No retry, reset, alternate role, endpoint or credential fallback exists.
    root='/v1/projects/'+PROJECT
    request(api,save,'jit_enable',root+'/jit-access','PUT',{'state':'enabled'})
    request(api,save,'jit_role_grant',root+'/database/jit','PUT',{'user_id':owner,'roles':[{'role':'postgres','expires_at':expires}]})
    value=request(api,save,'jit_mapping_confirm',root+'/database/jit')
    if value.get('user_id')!=owner or value.get('user_roles')!=[{'role':'postgres','expires_at':expires}]:
        raise LeaseFailure('jit_mapping_mismatch',None)
    return True
