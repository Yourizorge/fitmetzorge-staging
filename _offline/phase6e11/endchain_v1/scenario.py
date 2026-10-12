"""Capture the unchanged 45-action product scenario without SQL, Auth or files.

Only the existing main function and base_contract are compiled. All boundary
objects are in-memory recorders. This is a preregistration, not a workflow PASS.
"""
import ast,contextlib,copy,hashlib,io,json,pathlib,uuid

ROOT=pathlib.Path(__file__).resolve().parents[3]
SOURCE=ROOT/'_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'
AUDIT=ROOT/'_offline/phase6e11/readiness_v1/txaudit/audit.sql'
IDS={'member':'68000000-0000-4000-8000-000000000001','trainer':'68000000-0000-4000-8000-000000000002','b':'68000000-0000-4000-8000-000000000003'}
WINDOW='68000000-0000-4000-8000-000000000010'
A='68000000-0000-4000-8000-000000000011'
B='68000000-0000-4000-8000-000000000012'

class MemoryPath:
    def __truediv__(self,other):return self
    def mkdir(self):pass
    def __str__(self):return 'offline-memory-only'

class Boundary:
    cluster=None
    @staticmethod
    def setUpClass():pass
    @staticmethod
    def api(role,body):
        if role!='trainer' or body!={'op':'read','window':WINDOW,'workspace':A}:raise ValueError('scenario_source_read')
        return {'source_template':{'$trusted_source_template':True}}

class Capture:
    instance=None
    def __init__(self,folder):
        Capture.instance=self;self.folder=folder;self.w=WINDOW;self.x=A;self.b=B
        self.serial=0;self.revision=1;self.pv=0;self.pairs=[]
    def revisions(self):return {'revision':self.revision}
    def latest(self):return {'id':f'68000000-0000-4000-8000-{100+self.pv:012}','version':self.pv}
    def rows(self,q):
        if q=="select starts_at,ends_at from fmz6e11_private.windows where id='"+WINDOW+"'":
            return [{'starts_at':'$window_starts_at','ends_at':'$window_ends_at'}]
        if q=="select proposal_version from fmz6e11_private.b_states where workspace_id='"+B+"'":
            return [{'proposal_version':'$current_b_proposal_version'}]
        raise ValueError('scenario_unregistered_read')
    def body(self,action,data=None,x=None):
        self.serial+=1
        return {'op':'command','window':self.w,'workspace':x or self.x,
                'key':f'68000000-0000-4000-8001-{self.serial:012}',
                'expected':self.revision,'action':action,'data':data or {}}
    def perform(self,label,role,q,effects=(),outcome='committed',expected_http=200,**kwargs):
        if kwargs:raise ValueError('scenario_adapter_expansion')
        writes=self.base_contract(role,q,outcome,effects)
        self.pairs.append({'step':len(self.pairs),'label':label,'role':role,
            'route':'B' if q['workspace']==self.b else 'A','request':copy.deepcopy(q),
            'expected_outcome':outcome,'expected_http':expected_http,
            'before_revision':self.revision,'writes':copy.deepcopy(writes)})
        self.revision+=sum(t=='windows' and op=='UPDATE' for t,op,k in writes)
        for t,op,k in effects:
            if t=='proposals' and op=='INSERT':self.pv=k[1]
        return {'http_status':expected_http}

def capture():
    raw=SOURCE.read_bytes();tree=ast.parse(raw)
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Workflow')
    base=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='base_contract')
    saved=[]
    ns={'ROOT':MemoryPath(),'HERE':MemoryPath(),'Workflow':Capture,'ServerBoundary':Boundary,
        'uuid':uuid,'json':json,'uid':lambda n:f'68000000-0000-4000-8000-{n:012}',
        'lit':lambda s:"'"+s+"'",'sha':lambda _: 'source-not-measured-by-capture',
        'save':lambda path,value:saved.append(value)}
    exec(compile(ast.Module(body=[base,main],type_ignores=[]),str(SOURCE),'exec'),ns)
    Capture.base_contract=ns['base_contract']
    with contextlib.redirect_stdout(io.StringIO()):code=ns['main']()
    if code or len(Capture.instance.pairs)!=45:raise ValueError('existing_scenario_changed')
    return {'status':'OFFLINE_SCENARIO_CAPTURE_ONLY','source_sha256':hashlib.sha256(raw).hexdigest(),
            'placeholder_only':True,'hosted_calls':0,'workflow_actions':Capture.instance.pairs}

if __name__=='__main__':print(json.dumps(capture(),indent=2))
