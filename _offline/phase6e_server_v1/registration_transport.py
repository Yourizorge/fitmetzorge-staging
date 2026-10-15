"""Unpublished release12 transport candidate; no entry point or activation flag.

Only a private operator with a verified release dossier may construct it. The
existing loopback server remains unchanged and does not import this candidate.
"""
import base64,copy,datetime,json,ssl,time,urllib.error,urllib.request
from registration_scope import PROJECT,admit,instant
from registration_store import RegistrationStore
from store import Denied,identifier

AUTH='https://'+PROJECT+'.supabase.co/auth/v1'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise Denied('auth_redirect_denied')

class VerifiedAuth:
    def __init__(self,publishable_key,allowed,lease,request=None):
        if not isinstance(publishable_key,str) or not publishable_key:raise Denied('auth_key_missing')
        self._key=publishable_key;self.allowed=frozenset(allowed);self.lease=lease
        self._request=request or self._https
    def __repr__(self):return '<VerifiedAuth private configuration>'
    def _https(self,token):
        request=urllib.request.Request(AUTH+'/user',headers={'apikey':self._key,'Authorization':'Bearer '+token})
        opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        try:
            with opener.open(request,timeout=5) as response:
                raw=response.read(65537)
                if response.status!=200 or len(raw)>65536:raise Denied('auth_response_boundary')
                user=json.loads(raw)
                return {'id':user['id']}
        except (OSError,ValueError,KeyError,urllib.error.URLError):raise Denied('auth_transport_denied') from None
    def verify(self,token):
        self.lease()
        if not isinstance(token,str) or len(token)>16384:raise Denied('auth_token_shape')
        try:
            # This decode is NOT authentication: /user verifies the same token
            # with Supabase before these claims may enter the database session.
            claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
            user=self._request(token)
            actor=identifier(user['id']);session=identifier(claims['session_id'])
            if actor not in self.allowed or claims['sub']!=actor or claims['role']!='authenticated':raise ValueError()
            if claims['iss']!=AUTH or type(claims['exp']) not in (int,float) or claims['exp']<=time.time():raise ValueError()
            if claims.get('aud')!='authenticated':raise ValueError()
        except (ValueError,KeyError,IndexError,TypeError):raise Denied('auth_binding_denied') from None
        return {'sub':actor,'session_id':session}
    def close(self):self._key=None

class Candidate(RegistrationStore):
    def __init__(self,runtime,publishable_key,scope,proof,actual_sources,registered_identities,observer,clock=None):
        self.clock=clock or (lambda:datetime.datetime.now(datetime.timezone.utc))
        self.scope=copy.deepcopy(scope)
        admit(scope,proof,now=self.clock().isoformat(),actual_sources=actual_sources,registered_identities=registered_identities)
        if runtime.environment!='staging' or runtime.auth_base!=AUTH:raise Denied('release_transport_project')
        if not callable(observer):raise Denied('release_command_observer_required')
        self.runtime=runtime;self.bindings=copy.deepcopy(scope['bindings']);self.observer=observer;self.full_day21=False
        self.auth=VerifiedAuth(publishable_key,self.bindings.values(),self.lease)
    def lease(self):
        current=self.clock()
        if not instant(self.scope['issued_at'])<=current<instant(self.scope['expires_at']):raise Denied('release_expired')
    def connect(self):
        self.lease()
        # NativeRuntime was constructed only from the exact official Connect
        # record: session5432, jit=true, verify-full, CA,5s connect/query,1s lock.
        return self.runtime.connect()
    def read(self,*args,**kwargs):
        value=super().read(*args,**kwargs);value['hosted']=True;return value
    def close(self):self.auth.close();self.runtime.clear()
