"""Exact existing workflow functions plus the unchanged audit core on local PG17."""
import copy,json,os,pathlib,subprocess,sys,uuid
NEW=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(NEW.parent/'txaudit'))
from common import *
from journal import Journal
sys.path.insert(0,str(NEW.parent/'targeted'))
from test_server_boundary import ServerBoundary,uid

class Workflow:
    def __init__(self,folder):
        self.folder=folder;self.serial=0;self.pairs=[];self.run=str(uuid.uuid4())
        self.sql=ServerBoundary.sql
        self.sql((HERE/'audit.sql').read_text())
        self.sql(f"insert into {A}.runs(id,expires_at,enabled) values({lit(self.run)},clock_timestamp()+interval '10 minutes',true);")
        for i in range(1,4):
            self.sql(f"insert into {A}.actors values({lit(uid(i))},{lit(self.run)},'synthetic_fixture_only');")
        self.tables=self.rows("select n.nspname||'.'||c.relname name from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname in ('fmz6e11_private','auth','public') order by 1")
        for r in self.tables:
            self.sql(f"select {A}.attach({lit(r['name'])});")
        # Unpredictable surrogate IDs are NOT guessed. Existing unique proposal
        # keys and per-request event identities are the preregistered row selectors.
        keys={'fmz6e11_private.proposals':['workspace_id','version'],
              'fmz6e11_private.audit':['window_id','actor','action'],
              'fmz6e11_private.events':['window_id','workspace_id','actor','request_key','action','outcome']}
        for t,k in keys.items():
            self.sql(f"update {A}.relations set pk_columns=array["+','.join(lit(x) for x in k)+f"]::name[] where table_name={lit(t)};")
        self.w=ServerBoundary.window;self.x=ServerBoundary.workspaces['A'];self.b=ServerBoundary.workspaces['B']
    def rows(self,q):
        r=self.sql("select coalesce(json_agg(x),'[]') from ("+q+") x;")
        return json.loads(r.stdout.strip())
    def scalar(self,q):
        return json.loads([s for s in self.sql(q).stdout.splitlines() if s.startswith(('{','['))][-1])
    def snapshot(self):
        # Only a disposable local database containing synthetic rows.
        rows=self.rows(' union all '.join('select '+lit(t['name'])+' name,to_jsonb(t) row from '+t['name']+' t' for t in self.tables))
        return {t['name']:sorted([r['row'] for r in rows if r['name']==t['name']],key=digest) for t in self.tables}
    def revisions(self):
        return self.rows("select w.revision,a.active_version a_version,b.active_version b_version from fmz6e11_private.windows w join fmz6e11_private.workspaces a on a.window_id=w.id and a.route='A' join fmz6e11_private.b_states b on b.workspace_id="+lit(self.b)+" where w.id="+lit(self.w))[0]
    def latest(self):
        return self.rows("select id,version from fmz6e11_private.proposals where workspace_id="+lit(self.x)+" order by version desc limit 1")[0]
    def base_contract(self,role,q,outcome='committed',effects=()):
        actor=uid({'member':1,'trainer':2,'b':3}[role]);action=q['action'];w=q['window'];x=q['workspace'];key=q['key']
        e=list(effects)
        if outcome=='committed' and action in ('viewed','later'):
            e += [('requests','INSERT',[actor,key])]
        elif outcome not in ('denied','replayed') and not action.startswith('b_'):
            e += [('windows','UPDATE',[w]),('audit','INSERT',[w,actor,action]),('requests','INSERT',[actor,key])]
        elif outcome=='committed':
            e += [('windows','UPDATE',[w]),('requests','INSERT',[actor,key])]
        e += [('events','INSERT',[w,x,actor,key,action,outcome])]
        return e
    def b_input(self,q):
        row=ServerBoundary.api('b',{'op':'read','window':self.w,'workspace':self.b})['b_row']
        p=subprocess.run([os.environ['FMZ_NODE'],str(NEW/'compute.mjs')],input=json.dumps({'row':row,'request':q}),
            encoding='utf8',capture_output=True,timeout=15,creationflags=0x08000000 if sys.platform=='win32' else 0)
        if p.returncode:raise Stop('existing_computation_failed')
        return {'op':'internal_b','request':q,'computed':json.loads(p.stdout)}
    def body(self,action,data=None,x=None):
        return {'op':'command','window':self.w,'workspace':x or self.x,'key':str(uuid.uuid4()),
                'expected':self.revisions()['revision'],'action':action,'data':data or {}}
    def perform(self,label,role,q,effects=(),outcome='committed',input_body=None,expected_http=200,inject=None):
        self.serial+=1
        c={'run':self.run,'action':str(uuid.uuid4()),'actor':uid({'member':1,'trainer':2,'b':3}[role]),'workspace':q['workspace']}
        folder=self.folder/f'action-{self.serial:03d}';folder.mkdir()
        j=Journal(folder/'journal',c)
        before=self.snapshot();versions_before=self.revisions()
        e=self.base_contract(role,q,outcome,effects)
        entries=[]
        for table,op,key in e:
            table='fmz6e11_private.'+table if '.' not in table else table
            h=f"{A}.pk_hash({lit(self.run)},{lit(table)},{js(key)})"
            entries.append(f"jsonb_build_object('table',{lit(table)},'op',{lit(op)},'old',"+(h if op!='INSERT' else 'null')+",'new',"+(h if op!='DELETE' else 'null')+")")
        expr='jsonb_build_array('+','.join(entries)+')'
        self.sql(f"update {A}.runs set enabled=true where id={lit(self.run)};insert into {A}.actions(id,run_id,actor,workspace,expected,before_sha) values({lit(c['action'])},{lit(self.run)},{lit(c['actor'])},{lit(c['workspace'])},{expr},{lit(digest(before))});")
        ob=lambda:self.rows(observations(c))[0]
        registered=ob();j.record('before_saved',{'snapshot':before,'versions':versions_before,'contract':registered})
        claims={'sub':c['actor'],'session_id':uid({'member':101,'trainer':102,'b':103}[role])}
        request=input_body or (self.b_input(q) if q['action'].startswith('b_') else q)
        sql=(f"begin;select {A}.start_action({lit(c['action'])});set local role authenticated;"+
             "select set_config('request.jwt.claims',"+js(claims)+"::text,true);"+
             "select set_config('request.headers',"+js({'x-fmz6e11-proof':'synthetic-only-local-proof'})+"::text,true);"+
             "select public.fmz6e11_call("+js(request)+");reset role;"+(inject or '')+
             f"select {A}.confirm_action({lit(c['action'])});commit;")
        j.record('action_started',{'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),'local_auth_stub':True})
        p=self.sql(sql,success=False)
        if p.returncode:
            j.halt('action_started:sql',p.stderr.splitlines()[0]);raise Stop('workflow_sql:'+label+':'+p.stderr.splitlines()[0])
        values=[json.loads(s) for s in p.stdout.splitlines() if s.startswith('{')]
        receipt=values[-2];confirmation=values[-1]
        j.record('action_confirmed',{'receipt':receipt,'confirmation':confirmation})
        after=self.snapshot();observed=ob();versions_after=self.revisions()
        j.record('after_saved',{'snapshot':after,'versions':versions_after,'audit':observed})
        if receipt.get('http_status',200)!=expected_http:
            j.halt('after_saved:response_contract','unexpected_workflow_status')
            raise Stop('unexpected_workflow_status:'+label+':'+str(receipt))
        expected=registered['action']['expected'];actual=[{'table':r['table_name'],'op':r['operation'],'old':r['old_key_sha'],'new':r['new_key_sha']} for r in observed['writes']]
        if sorted(expected,key=digest)!=sorted(actual,key=digest):raise Stop('write_multiset:'+label)
        action=observed['action']
        if any(str(r['xid'])!=str(action['xid']) or r['backend']!=action['backend'] or r['actor']!=c['actor'] or r['workspace']!=c['workspace'] for r in observed['writes']):
            raise Stop('transaction_binding')
        allowed={r['table'] for r in expected}
        if any(before[t]!=after[t] for t in before if t not in allowed):raise Stop('forbidden_table_drift')
        if before['public.profiles']!=after['public.profiles'] or before['auth.users']!=after['auth.users'] or before['auth.sessions']!=after['auth.sessions']:
            raise Stop('synthetic_account_changed')
        proof={'label':label,'action':q['action'],'outcome':outcome,'context':c,'xid':str(action['xid']),
            'expected':expected,'actual':actual,'versions_before':versions_before,'versions_after':versions_after,
            'committed_operations':{op:sum(r['op']==op for r in actual) for op in ('INSERT','UPDATE','DELETE')},
            'forbidden_table_writes':0,'scope':'local PG17 existing functions; Auth stubs, NOT hosted authorization'}
        j.record('pair_validated',proof)
        seal=save(folder/'receipt.json',proof);j.record('next_step_allowed',{'receipt_sha256':seal,'hosted_admission':False})
        self.sql(f"select {A}.seal_pair({lit(c['action'])},{lit(digest(after))},{lit(seal)});")
        self.pairs.append(proof)
        print(json.dumps({'pair':self.serial,'label':label,'writes':len(actual),'status':'LOCAL_PASS'}),flush=True)
        return receipt

def main():
    folder=ROOT/'supabase/.temp'/('phase6e11-workflow-local-'+uuid.uuid4().hex);folder.mkdir()
    try:
        ServerBoundary.setUpClass()
        w=Workflow(folder)
        times=w.rows("select starts_at,ends_at from fmz6e11_private.windows where id="+lit(w.w))[0]
        # The fixture source is exactly the source template already used by the app.
        template=ServerBoundary.api('trainer',{'op':'read','window':w.w,'workspace':w.x})['source_template']
        q=w.body('source_append',{'body':template,'valid_from':times['starts_at'],'valid_until':times['ends_at']})
        w.perform('source v1','trainer',q,[('source_versions','INSERT',[w.x,1]),('source_heads','INSERT',[w.x])])
        q=w.body('propose');w.perform('proposal v1','member',q,[('proposals','INSERT',[w.x,1])])
        p=w.latest();d={'proposal':p['id'],'proposal_version':p['version']}
        w.perform('apply before approvals denied','trainer',w.body('apply',d),outcome='denied',expected_http=403)
        for role,action in [('member','member_accept'),('trainer','trainer_approve')]:
            w.perform(action,role,w.body(action,d),[('proposals','UPDATE',[w.x,1])])
        q=w.body('apply',d)
        w.perform('separate apply 1 to 2','trainer',q,[('plans','INSERT',[w.x,2]),('workspaces','UPDATE',[w.x]),('proposals','UPDATE',[w.x,1])])
        w.perform('same request replay','trainer',q,outcome='replayed')
        w.perform('fresh request double apply','trainer',w.body('apply',d),outcome='denied',expected_http=409)
        w.perform('restore proposal','member',w.body('restore',{'plan_version':1}),[('proposals','INSERT',[w.x,2])])
        p=w.latest();d={'proposal':p['id'],'proposal_version':p['version']}
        for role,action in [('member','member_accept'),('trainer','trainer_approve')]:
            w.perform('restore '+action,role,w.body(action,d),[('proposals','UPDATE',[w.x,2])])
        w.perform('restore applied as v3','trainer',w.body('apply',d),[('plans','INSERT',[w.x,3]),('workspaces','UPDATE',[w.x]),('proposals','UPDATE',[w.x,2])])
        for version,role,action in [(3,'member','member_reject'),(4,'trainer','trainer_reject'),(5,'trainer','trainer_block')]:
            w.perform('new restore '+str(version),'member',w.body('restore',{'plan_version':1}),[('proposals','INSERT',[w.x,version])])
            p=w.latest();d={'proposal':p['id'],'proposal_version':p['version']}
            if role=='trainer':w.perform('accept for '+action,'member',w.body('member_accept',d),[('proposals','UPDATE',[w.x,version])])
            w.perform(action,role,w.body(action,d),[('proposals','UPDATE',[w.x,version])])
        q=w.body('propose');q['expected']-=1
        w.perform('stale revision','member',q,outcome='denied',expected_http=409)
        # Same Route B transitions as the existing integration suite, including
        # server-only computation and re-confirmation after editing/restoring.
        def b(action,data=None,outcome='committed',version=None,http=200):
            q=w.body(action,data,x=w.b)
            effects=[] if outcome!='committed' else [('b_states','UPDATE',[w.b])]
            if version:effects.append(('b_versions','INSERT',[w.b,version]))
            w.perform(action,'b',q,effects,outcome=outcome,expected_http=http)
            return q
        b('b_build')
        b('b_confirm')
        b('b_edit',{'kind':'move','session':0,'index':0,'to':1})
        b('b_apply',outcome='denied',http=403)
        b('b_confirm')
        activated=b('b_apply',version=1)
        w.perform('B same-key replay','b',activated,outcome='replayed')
        b('b_apply',outcome='denied',http=403)
        b('b_reopen');b('b_confirm');b('b_apply',version=2)
        b('b_restore',{'version':1})
        b('b_apply',outcome='denied',http=403)
        b('b_confirm');b('b_apply',version=3)
        b('b_reopen');b('b_reject');b('b_apply',outcome='denied',http=403)
        q=w.body('b_reopen',x=w.b);q['expected']-=1
        w.perform('B stale revision','b',q,outcome='denied',expected_http=409)
        b('b_edit',{'kind':'sleep','hours':9},outcome='denied',http=403)
        for role,x,pv in [('member',w.x,5),('b',w.b,6)]:
            if role=='b':pv=w.rows('select proposal_version from fmz6e11_private.b_states where workspace_id='+lit(w.b))[0]['proposal_version']
            for action,op in [('viewed','INSERT'),('later','UPDATE')]:
                w.perform(action+' '+role,role,w.body(action,{'proposal_version':pv},x=x),
                          [('inbox_state',op,[x,uid(1 if role=='member' else 3),pv])])
        save(folder/'result.json',{'status':'LOCAL_EXISTING_AB_WORKFLOW_AUDIT_PASS','pairs':len(w.pairs),'proofs':w.pairs,
             'actual_source':sha(ROOT/'supabase/migrations/20260916162120_phase6e11_final_app_integration.sql'),
             'audit_core':sha(HERE/'audit.sql'),'hosted_admission':False,'auth':'local stubs only',
             'setup_audited':False,'remaining':['prepare/cleanup','6e9/6e10','hosted binding','Auth']})
        print(json.dumps({'status':'LOCAL_EXISTING_AB_WORKFLOW_AUDIT_PASS','pairs':len(w.pairs),'directory':str(folder)}))
        return 0
    except BaseException as e:
        save(folder/'HALT.json',{'type':type(e).__name__,'reason':str(e)[:500],'hosted_calls':0})
        print(json.dumps({'status':'LOCAL_FAIL','directory':str(folder),'reason':str(e)[:500]}))
        return 1
    finally:
        if getattr(ServerBoundary,'cluster',None):ServerBoundary.tearDownClass()
if __name__=='__main__':sys.exit(main())
