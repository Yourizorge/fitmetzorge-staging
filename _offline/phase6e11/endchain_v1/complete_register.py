"""Complete, executable offline capacity register from an integral CI receipt.

It cannot run SQL or grant a larger budget. All native protocol commands and
managed GoTrue commands are counted, with bounded stream capacity and a safety
suffix at every prefix. CI bootstrap is explicit and is not a hosted action.
"""
import collections,hashlib,importlib.util,json,os,pathlib,re

def bound_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

HERE=pathlib.Path(__file__).resolve().parent
scenario_source=bound_module('register_bound_scenario',HERE/'scenario.py')
auth_source=bound_module('register_bound_auth',HERE.parent/'auth_metadata_v1/auth_contract.py')

from closure import RUN_ID,PURPOSE,allowance
from integral_stream import ROWS,PAGE,PAGES,PROTOCOL_CAPACITY
APPROVED=allowance(RUN_ID,PURPOSE)
PHASES=('preflight','migration','baseline','setup','guard','auth','controller','route_a',
        'route_b','restore','measurements','io','cleanup','final','closure')
BOOTSTRAP={'local_fixture_cleanup','local_observer_schema','local_observer_triggers',
           'profile_seed_a_member','profile_seed_a_trainer','profile_seed_b_member','operator_seed'}
PAIRS=('before_saved','action_started','action_confirmed','after_saved','pair_validated')
AUTH_CALLS={'issue':11,'verify':21,'getUser':5,'refresh':27,'logout':10,'revoked_denial':4}
INFRASTRUCTURE_WRITES={
 'controller':[
  {'table':'fmz6e11_controller_private.runs','operations':['INSERT','UPDATE'],'key':['exact reserved run_id']},
  {'table':'fmz6e11_controller_private.steps','operations':['INSERT','UPDATE'],'key':['run_id','step']},
  {'table':'fmz6e11_controller_private.evidence','operations':['INSERT'],'key':['run_id','step','phase']}],
 'auth_observer':[
  {'table':'exact temporary Auth schema.actions','operations':['INSERT'],'key':['action_id']},
  {'table':'exact temporary Auth schema.control','operations':['UPDATE'],'key':['singleton=true']},
  {'table':'exact temporary Auth schema.events','operations':['INSERT'],'key':['action_id','actor_sha','row_key_sha','xid']},
  {'table':'exact temporary Auth schema.session_keys','operations':['INSERT'],'key':['session_sha','actor_sha']}],
 'lifecycle_intent':[
  {'table':'fmz6e11_audit_private.runs','operations':['INSERT'],'key':['preallocated run_id']},
  {'table':'fmz6e11_audit_private.actors','operations':['INSERT','UPDATE'],'key':['registered synthetic actor UUID']},
  {'table':'fmz6e11_audit_private.actions','operations':['INSERT','UPDATE'],'key':['run_id','action_id']},
  {'table':'fmz6e11_audit_private.bindings','operations':['INSERT','DELETE'],'key':['current transaction']},
  {'table':'fmz6e11_audit_private.writes','operations':['INSERT'],'key':['action_id','ordinal']}],
 'request_intent':[
  {'table':'fmz6e11_request_private.receipts','operations':['INSERT','UPDATE'],'key':['request_id','actor','session','payload_sha']},
  {'ref':'lifecycle_intent'}],
 'controls':[
  {'table':'fmz6e11_private.config','operations':['UPDATE'],'key':['id=true'],'precondition':'exact original disabled state or this run proof hash'},
  {'table':'fmz6e11_request_private.control','operations':['UPDATE'],'key':['id=true'],'precondition':'exact original disabled state or this run expiry'}],
 'guard_objects':{'operations':['CREATE','DROP'],'scope':'exact run-derived guard/observer schema and source-hashed functions/triggers; no existing object replacement'},
 'fixtures':{'source':'fixture_lifecycle.py:seed_writes/perform; workflow_composition.mjs:CLEANUP_LAYOUT',
  'scope':'preallocated window/workspaces, exact synthetic UUIDs and action keys',
  'seed_counts':{'INSERT':10},'activate_counts':{'INSERT':2,'UPDATE':2},'window_close_counts':{'DELETE':1},
  'workflow_cleanup_counts':{'DELETE':123},'proof':'independent expected multiset, same xid/backend, pair then separate seal'},
 'readonly':[]}

def infrastructure_ref(command):
    p=command['phase']
    if p in ('controller_evidence','evidence_query','final_closure'):return 'controller'
    if p in ('guard_install','metadata_install','remove'):return 'guard_objects'
    if p in ('before','after'):return 'auth_observer'
    if p in ('control_enable','control_restore'):return 'controls'
    if p.startswith('lifecycle_') and p not in ('lifecycle_measure','lifecycle_reader_begin','lifecycle_reader_check','lifecycle_reader_end'):
        return 'fixtures' if p=='lifecycle_action' else 'lifecycle_intent'
    if p in ('call','seal'):return 'request_intent'
    return 'readonly'

def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def safety_path(guard=False,observer=False,controls=False,claimed=False):
    # No replay, blind fixture deletion or replacement of an incomplete pair.
    # Each connection is closed even if its one ROLLBACK cannot be confirmed.
    path=[('rollback_'+channel,1) for channel in ('auth_lock','writer','reader','workflow')]
    if claimed:path.append(('durable_stop',1))
    path += [('scoped_after_once',2),('numeric_io_and_terminal_witness',3)]
    if controls:path += [('control_before',1),('control_compare_restore',2),('control_after',1)]
    if observer:path += [('observer_inspect',1),('observer_exact_remove',5),('observer_absent',1)]
    if guard:path += [('guard_inspect',1),('guard_exact_remove',5),('guard_absent',1)]
    if claimed:path.append(('close_stopped_run',1))
    return [{'action':action,'sql':cost,'retry':False,'identity_bound':True} for action,cost in path]

def reserve_prefixes(rows):
    state={'guard':False,'observer':False,'controls':False,'claimed':False};out=[];used=0
    cleanup_remaining=sum(r['sql'] for r in rows if r['phase'] in ('cleanup','final','closure'))
    for i in range(len(rows)+1):
        if i:
            row=rows[i-1];used+=row['sql']
            if row['phase'] in ('cleanup','final','closure'):cleanup_remaining-=row['sql']
            for name,value in row.get('state_after',{}).items():state[name]=value
        suffix=safety_path(**state);emergency=sum(x['sql'] for x in suffix)
        reserve=max(emergency,cleanup_remaining)
        out.append({'after':i,'used':used,'remaining_normal_cleanup':cleanup_remaining,
                    'emergency_sql':emergency,'reserve':reserve,'required_total':used+reserve,
                    'path':suffix,'within_approved_limit':used+reserve<=APPROVED})
    return out

def classify(command,scenario):
    p=command['phase'];a=command.get('action') or {}
    if p in BOOTSTRAP:return 'ci_bootstrap'
    if p=='final_closure':return 'closure'
    if p.startswith('gates_after_migration'):return 'migration'
    if p.startswith('stream_before_cleanup'):return 'measurements'
    if p.startswith(('stream_after_cleanup','gates_after_cleanup')):return 'final'
    if p.startswith(('stream_before','gates_before')):return 'baseline'
    if p.startswith('preservation_'):return 'measurements'
    if a.get('kind')=='workflow' and a.get('step',0)>=45:return 'cleanup'
    if a.get('kind')=='auth' and a.get('operation') in ('logout','revoked_denial'):return 'cleanup'
    if p in ('guard_install','metadata_install'):return 'guard'
    if p=='remove':return 'cleanup'
    if p.startswith('control_') or p.startswith('lifecycle_') or p=='fixture_times':return 'setup' if a.get('kind')!='workflow' else 'cleanup'
    if p.startswith('io_'):return 'io'
    if p in ('workflow_auth_before','workflow_auth_after'):return 'io'
    if p=='controller_evidence' or p=='evidence_query':return 'controller'
    if p in ('before','after','auth_identity_lock'):return 'auth'
    if a.get('kind')=='workflow':
        step=a['step']
        if step>=45:return 'cleanup'
        if p=='measurement':return 'measurements'
        action=scenario[step]
        if 'restore' in action['request']['action']:return 'restore'
        return 'route_a' if action['route']=='A' else 'route_b'
    if p=='measurement':return 'measurements'
    raise ValueError('register_unclassified_'+p)

def build(folder):
    folder=pathlib.Path(folder).resolve()
    if os.name=='nt' and not str(folder).startswith('\\\\?\\'):folder=pathlib.Path('\\\\?\\'+str(folder))
    def read(name):return json.loads((folder/name).read_text())
    closure=read('integral-closure.json')
    if (closure.get('run_id'),closure.get('purpose'))!=(RUN_ID,PURPOSE) or closure.get('confirmed') is not True:
        raise ValueError('register_closure_unconfirmed')
    source=read('endchain-sources.json')['sources'];bundle=sha(source)
    trace=read('integral-complete-protocol-trace.json')['commands']
    if [x['command'] for x in trace]!=list(range(1,len(trace)+1)) or not all(x['confirmed'] for x in trace):
        raise ValueError('register_incomplete_protocol_trace')
    preflight=read('integral-preflight.json')
    if len(preflight['commands'])!=4 or len(preflight['migrations'])!=43 or not all(x['confirmed'] for x in preflight['commands']):
        raise ValueError('register_preflight')
    workflow=read('integral-workflow.json')
    if workflow.get('pairs')!=71 or workflow.get('deletes')!=123 or workflow.get('next_step')!=83:
        raise ValueError('register_workflow_incomplete')
    if workflow.get('worker_cpu_ms',2000)>=2000 or workflow.get('worker_wall_ms',120000)>=120000:
        raise ValueError('register_worker_limits')
    for label in ('before','after_cleanup'):
        gate=read('integral-gates-'+label+'.json')
        if gate['unchanged'] is not True or any(gate['absence'].values()):raise ValueError('register_lifecycle_missing')
    migration_pair=read('integral-migration-pair.json')
    if not all(migration_pair.get(k) is True for k in ('complete','controller_rows_unchanged','only_expected_ddl','protected_stream_baseline_preserved')):
        raise ValueError('register_migration_pair_missing')
    for label in ('seed','activate','delete_window'):
        pair=read('lifecycle-'+label+'-pair.json')
        if pair['pair_complete'] is not True or pair['protected_equal'] is not True:raise ValueError('register_fixture_pair')
    for label in ('enable','restore'):
        pair=read('integral-control-'+label+'-pair.json')
        if pair['actual_updates']!=2 or pair['expected_updates']!=2:raise ValueError('register_control_pair')
    scenario=scenario_source.capture()['workflow_actions'];rows=[];bootstrap=[]
    def add(phase,action,count,**more):
        if phase not in PHASES or type(count) is not int or count<0:raise ValueError('register_row_shape')
        for n in range(count):
            rows.append({'id':'cmd_'+str(len(rows)+1).zfill(5),'phase':phase,'action':action,
                'sql':1,'ordinal_in_action':n,'source_bundle_sha':bundle,'timeout_ms':5000,
                'retry':False,'stop':'NO_GO; no dependent mutation; identity-bound safety suffix',**more})
    def move_last_before(count,predicate):
        nonlocal rows
        group=rows[-count:];rest=rows[:-count]
        matches=[i for i,row in enumerate(rest) if predicate(row)]
        if not matches:raise ValueError('register_action_anchor_missing')
        at=matches[0];rows=rest[:at]+group+rest[at:]
    for c in preflight['commands']:add('preflight','project_tls_and_43_history',1,template_sha=c['sql_sha256'],writeset=[])
    cli=[read('cli-protocol-'+str(i)+'.json') for i in range(2)]
    if [c['protocol_commands'] for c in cli]!=[14,2] or not all(c['complete'] for c in cli):raise ValueError('register_cli_shape')
    for c in cli[0]['observer_commands'][:4]+cli[0]['commands']+cli[0]['observer_commands'][4:]:
        add('migration','candidate_44_migration_aware_cli',1,template_sha=c['sha256'],writeset=['exact M44 DDL and migration identity only'] if c['kind']!='numeric_observer' else [])
    for c in trace:
        phase=classify(c,scenario)
        if phase=='ci_bootstrap':bootstrap.append(c);continue
        action=c.get('action') or {};kind=action.get('kind');step=action.get('step')
        contract=scenario[step] if kind=='workflow' and step is not None and step<45 else None
        expected=collections.Counter(('fmz6e11_private.'+t,op) for t,op,key in contract['writes']) if contract else None
        binding={'trace_command':c['command'],'template_sha':c['sql_sha256'],
            'action_binding':action,'writeset':[{'table':t,'operation':op,'count':n} for (t,op),n in sorted(expected.items())] if contract and c['phase']=='call' else [],
            'infrastructure_writeset':infrastructure_ref(c),
            'proof':list(PAIRS) if kind in ('workflow','auth') else ['source identity','before/after or read-only receipt']}
        add(phase,c['phase'],1,**binding)
        # Safety reserve deliberately begins at the first attempted setup SQL.
        if c['phase']=='guard_install':rows[-1]['state_after']={'guard':True}
        if c['phase']=='metadata_install':rows[-1]['state_after']={'observer':True}
        if c['phase']=='control_enable':rows[-1]['state_after']={'controls':True}
        if c['phase']=='evidence_query':rows[-1]['state_after']={'claimed':True}
        if c['phase']=='control_restored':rows[-1]['state_after']={'controls':False}
    # Exact source-trigger removals are independently confirmed by the final
    # gates, not merely by observing that a removal was attempted.
    for row in rows:
        if row['action']=='gates_after_cleanup_absence':row['state_after']={'guard':False,'observer':False,'controls':False}
    streams=[]
    for label,phase in [('before','baseline'),('before_cleanup','measurements'),('after_cleanup','final')]:
        value=read('integral-stream-'+label+'.json')
        if not value['protected_equal'] or not value['complete_by_same_snapshot_capacity'] or value['rows']!=value['protected_rows_bounded'] or any(x['own_temp_written'] for x in value['profiles']):
            raise ValueError('register_stream_incomplete')
        # One bounded numeric sentinel replaces the former empty FETCH round.
        if value['protocol_commands']!=15+2*len(value['frames']) or len(value['frames'])>PAGES or value['rows']>ROWS:
            raise ValueError('register_stream_shape')
        extra=PROTOCOL_CAPACITY-value['protocol_commands'];streams.append({'label':label,'actual':value['protocol_commands'],'capacity':PROTOCOL_CAPACITY,'extra':extra})
        # Place the optional page slots before that stream's final rollback.
        at=next(i for i,r in enumerate(rows) if r['action']=='stream_'+label+'_rollback')
        old=rows[:];rows=[]
        add(phase,'bounded_additional_fetch_and_io',extra,template_sha=value['query_sha256'],writeset=[],
            proof=['same snapshot','one complete frame','numeric zero-temp delta'],optional=True)
        padding=rows;rows=old[:at]+padding+old[at:]
    # Auth SQL is managed SQL, but is not made invisible behind a single HTTP
    # request. Keep its count and query IDs separate from native protocol SQL.
    managed=[]
    for i in range(18):
        value=read('auth-protocol-%02d.json'%i)
        if value['commands']!=AUTH_CALLS[value['operation']] or any(x['temp_written'] for x in value['statements']):
            raise ValueError('register_auth_protocol')
        managed.append(value)
        add('auth' if i<12 else 'cleanup','gotrue_'+value['role']+'_'+value['operation'],value['commands'],
            queryids=[x['queryid'] for x in value['statements']],managed=True,
            writeset=[{'table':'auth.'+t,'operation':op,'count':n} for (t,op),n in auth_source.COUNTS[value['operation']].items()])
        move_last_before(value['commands'],lambda row:row.get('action_binding')==
            {'kind':'auth','role':value['role'],'operation':value['operation']})
    value=read('workflow-auth-protocol.json')
    if value['verified_calls']!=72 or value['commands']!=360 or any(x['temp_written'] for x in value['statements']):
        raise ValueError('register_workflow_auth')
    add('setup','gotrue_fixture_identity',5,managed=True,writeset=[])
    move_last_before(5,lambda row:row['action']=='workflow_auth_before')
    for step in range(71):
        phase='cleanup' if step>=45 else 'restore' if 'restore' in scenario[step]['request']['action'] else 'route_a' if scenario[step]['route']=='A' else 'route_b'
        add(phase,'gotrue_workflow_identity_'+str(step),5,managed=True,writeset=[])
        move_last_before(5,lambda row:row.get('action_binding')=={'kind':'workflow','step':step})
    for c in cli[1]['observer_commands'][:4]+cli[1]['commands']+cli[1]['observer_commands'][4:]:add('final','empty_cli_dry_run',1,template_sha=c['sha256'],writeset=[])
    if closure['global_commands']!=len(trace)-len(bootstrap)+36+594:raise ValueError('register_closure_count')
    closing=[r for r in rows if r['phase']=='closure']
    if len(closing)!=1:raise ValueError('register_closure_missing')
    rows=[r for r in rows if r['phase']!='closure']+closing
    migration=[r for r in rows if r['action']=='candidate_44_migration_aware_cli']
    rows=[r for r in rows if r['action']!='candidate_44_migration_aware_cli']
    at=next(i for i,r in enumerate(rows) if r['action']=='gates_after_migration_begin')
    rows=rows[:at]+migration+rows[at:]
    # Managed SQL rows are charged before their HTTP action by the executor.
    # The conservative prefix model reserves them even if the next action fails.
    for i,row in enumerate(rows):row['id']='cmd_'+str(i+1).zfill(5)
    prefixes=reserve_prefixes(rows);normal=sum(x['sql'] for x in rows);worst=max(x['required_total'] for x in prefixes)
    counts=dict(collections.Counter(r['phase'] for r in rows));total_managed=sum(x['sql'] for x in rows if x.get('managed'))
    return {'version':2,'run_id':RUN_ID,'purpose':PURPOSE,'complete_register':True,'approved_limit':APPROVED,'normal_capacity':normal,
        'worst_including_safety':worst,'extra_above_approved_limit':max(0,worst-APPROVED),
        'recommended_maximum':worst,'fits':worst<=APPROVED,'hosted_admitted':False,'hosted_attempt_consumed':False,
        'rows':rows,'prefixes':prefixes,'phase_budgets':counts,'stream_capacity':streams,
        'managed_auth_commands':total_managed,'native_and_cli_capacity':normal-total_managed,
        'observed_native_composition':len(trace),'ci_only_bootstrap_commands':len(bootstrap),
        'infrastructure_write_contracts':INFRASTRUCTURE_WRITES,
        'ci_only_bootstrap':bootstrap,'sources':source,'source_bundle_sha':bundle,
        'zero_sql_required':[{'action':x,'sql':0,'mandatory':True} for x in
            ['source_ci_admission','exact_project_and_connect_binding','JIT_create_expire_revoke_verify',
             'OIDC_allowlist_admission','Auth_version_binding','native_TLS_connection_and_close',
             'request_deadlines_and_secret_redaction','durable_local_manifest','runtime_frozen_and_Pages_checks']],
        'stop_path':'Rollback once, preserve incomplete evidence/fixtures, close exact own temporary access. No blind fixture deletion.',
        'data_limits':{'rows_per_stream':ROWS,'row_limit_scope':'transported protected row hashes per cycle; duplicates count separately',
                       'numeric_capacity_sentinel':ROWS+1,'capacity_counted_in_protocol':True,
                       'page_rows':PAGE,'cycles':3,'collectors':1,'query_ms':5000,
                       'worker_ms':120000,'guard_ms':180000,'full_retry':0,'own_temp_writes':0},
        'scope':'Offline integral capacity; not a universal minimum or permission to exceed the current limit.'}

class Escrow:
    """Executable pre-mutation gate. The current cap cannot be raised here."""
    def __init__(self,register):
        if (register.get('run_id'),register.get('purpose'))!=(RUN_ID,PURPOSE):
            raise ValueError('register_run_not_authorized')
        if not register.get('complete_register') or register.get('fits') is not True or register['worst_including_safety']>APPROVED:
            raise ValueError('complete_budget_not_admitted')
        self.register=register;self.used=0;self.index=0
    def charge(self):
        row=self.register['rows'][self.index];suffix=self.register['prefixes'][self.index+1]
        if self.used+row['sql']+suffix['reserve']>APPROVED:raise ValueError('cleanup_escrow')
        self.used+=row['sql'];self.index+=1;return row

if __name__=='__main__':
    import sys
    result=build(sys.argv[1]);print(json.dumps({k:v for k,v in result.items() if k not in ('rows','prefixes','sources','ci_only_bootstrap')},indent=2))
