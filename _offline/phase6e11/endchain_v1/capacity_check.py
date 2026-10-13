"""Source-bound capacity counter. Deliberately NOT a complete run admission.

The current maximum stream size must be affordable before mutation. A small
test database does not establish the worst-case command budget for staging.
"""
import ast, collections, hashlib, importlib.util, json, os, pathlib, sys, uuid
from sql_protocol import statements
from sequence import compile_sequence, ROOT

HERE=pathlib.Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def source_digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def cursor_budget(cycles=2):
    # Execute only the pure budget function, never import a hosted adapter.
    path=HERE.parent/'cursor_v1/transfer.py'
    tree=ast.parse(path.read_text())
    maximum=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='MAX_ROWS' for t in n.targets))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='budget')
    import math
    scope={'math':math,'MAX_ROWS':maximum}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),scope)
    return {**scope['budget'](8192,maximum,cycles),'source_sha256':source_digest(path)}

def lifecycle_count():
    g=module('capacity_guard',HERE.parent/'controller_guard_v1/guard.py')
    a=module('capacity_audit',HERE.parent/'auth_metadata_v1/audit.py')
    ids={r:f'68000000-0000-4000-8000-{i:012}' for i,r in enumerate(g.ROLES,1)}
    run='68000000-0000-4000-8000-000000000020';deadline='2026-10-12T12:00:00+00:00'
    gs=g.scope(run,ids);s=a.scope(run,ids)
    guard_receipt={'run':run,'schema':gs,'function_sha':'a'*64,
        'trigger_shas':{gs+x:'b'*64 for x in ('_i','_u','_d')}}
    observer_receipt={'schema':s,'lease':{'run':run,'expires_at':deadline,'version':1},
        'secure_function':True,'function_count':1,'relations':a.RELATIONS,'dependencies':7,
        'body_sha':hashlib.sha256(a.function_body(s,ids,deadline).encode()).hexdigest(),
        'function_sha':'c'*64,'triggers':[{'name':s+'_'+str(i),'table':'auth.'+t,'sha':'d'*64,
        'enabled':'O','type':29} for i,t in enumerate(a.TABLES)]}
    sqls={'guard_install':g.install(run,ids),'guard_inspect':g.inspect(run,ids),
        'guard_remove':g.remove(run,ids,guard_receipt),'guard_removed_inspect':g.inspect(run,ids),
        'observer_install':a.install(run,ids,deadline),'observer_inspect':a.inspect(run,ids),
        'observer_remove':a.remove(run,ids,observer_receipt),'observer_removed_inspect':a.inspect(run,ids)}
    return {name:len(statements(sql)) for name,sql in sqls.items()}

def verify_receipt(value,source_check=True):
    r=value.get('result',{})
    if value.get('exitcode')!=0 or value.get('hosted_calls')!=0 or value.get('sources_unchanged') is not True:
        raise ValueError('composition_source_or_exit')
    if r.get('status')!='LOCAL_COMPOSED_71_PASS' or r.get('pairs')!=71 or r.get('deletes')!=123:
        raise ValueError('composition_not_complete')
    if source_check and any(source_digest(HERE/name)!=digest for name,digest in value['sources'].items()):
        raise ValueError('composition_sources_changed')
    commands=r['commands']
    if [c['command'] for c in commands]!=list(range(1,len(commands)+1)):
        raise ValueError('command_gap_or_duplicate')
    counts=dict(collections.Counter(c['phase'] for c in commands))
    expected={'begin':71,'binding':71,'call':71,'commit':71,'seal':71,'identity':1,
        'controller_evidence':357,'measurement':145,'read_begin':20,'read_binding':20,'read_call':20,'rollback':20}
    if counts!=expected or len(commands)!=938:raise ValueError('composition_command_shape')
    if commands[-1]['phase']!='controller_evidence' or commands[-2]['phase']!='measurement':
        raise ValueError('closure_not_counted')
    return counts

def build(value,source_check=True):
    counts=verify_receipt(value,source_check)
    auth=[a for a in compile_sequence()['actions'] if a['kind']=='auth']
    if len(auth)!=18:raise ValueError('auth_sequence_changed')
    # Five durable states, fresh before/after, one arm and one disarm.
    # Identity-lock transactions apply only to issue/verify/refresh.
    auth_cost=18*(5+2+1+1)+sum(a['operation'] in ('issue','verify','refresh') for a in auth)*6
    lifecycle=lifecycle_count();cursor=cursor_budget()
    known={'workflow_and_25_delete_batches_plus_revoke':sum(counts.values()),
        'auth_18_actions':auth_cost,'two_bounded_stream_cycles':cursor['commands'],
        'guard_and_observer_install_inspect_remove':sum(lifecycle.values())}
    total=sum(known.values())
    return {'status':'NO_GO_CAPACITY_NOT_CLOSED','approved_maximum':1280,
        'source_bound_known_capacity':total,'known_capacity_above_limit':max(0,total-1280),
        'complete_budget':False,'recommended_new_maximum':None,'hosted_admitted':False,
        'hosted_attempt_consumed':False,'known_components':known,'guard_observer_commands':lifecycle,
        'stream_capacity':cursor,'actual_local_commands':938,
        'actual_local_seconds':value['result']['seconds'],
        'not_yet_costed':['fixture_prepare_activate_and_final_window_delete',
            'request_control_enable_restore','independent_object_catalog_pairs',
            'continuous_scoped_query_io_binding_and_closing_witness',
            'own_auth_audit_cleanup_and_post_logout_absence',
            'migration_identity_and_empty_dry_run','all_prefix_failure_and_safety_suffixes'],
        'zero_sql_but_still_required':['jit_grant_revoke_attestation','http_auth_and_oidc',
            'durable_evidence_publication','runtime_and_frozen_preservation'],
        'caveat':'Capacity at the existing 131072-row stream ceiling, not an observed hosted count, '
                 'not a universal minimum and not permission for a larger budget. No IO values are simulated.'}

if __name__=='__main__':
    path=pathlib.Path(sys.argv[1]).resolve()
    if path.parent.parent!=ROOT/'supabase/.temp' or path.name!='result.json':raise ValueError('local_receipt_scope')
    result=build(json.loads(path.read_text()))
    result['input_receipt_sha256']=source_digest(path)
    result['checker_sha256']=source_digest(pathlib.Path(__file__))
    folder=ROOT/'supabase/.temp'/('phase6e11-capacity-'+uuid.uuid4().hex);folder.mkdir()
    raw=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    with (folder/'result.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    print(json.dumps({'folder':str(folder),'sha256':hashlib.sha256(raw).hexdigest(),**result},indent=2,sort_keys=True))
