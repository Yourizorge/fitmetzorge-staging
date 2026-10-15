"""One local login; explicit server mounts, never browser-selected store/role."""
from store import Denied,identifier

class ComposedStore:
    def __init__(self,primary,workspaces,registration):
        if primary.auth is not registration.auth:raise Denied('auth_composition')
        self.primary=primary;self.registration=registration;self.auth=primary.auth
        self.workspaces=frozenset(identifier(w) for w in workspaces)
        if self.workspaces & set(registration.bindings):raise Denied('workspace_collision')
    def mounted(self,workspace):
        identifier(workspace)
        if workspace in self.registration.bindings:return self.registration
        if workspace in self.workspaces:return self.primary
        raise Denied('workspace_denied')
    def read(self,workspace,token):return self.mounted(workspace).read(workspace,token)
    def execute(self,workspace,token,request_id,expected,request,fault=None):
        return self.mounted(workspace).execute(workspace,token,request_id,expected,request,fault)
