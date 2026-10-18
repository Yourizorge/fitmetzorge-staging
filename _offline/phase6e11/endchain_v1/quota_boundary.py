"""Exact new-run quota delta; M44 bytes, objects and closed rows are retained."""
import copy,hashlib,pathlib,re
import migration_boundary as legacy
ast=legacy.ast
VERSION='20261018070231'
FILE=VERSION+'_phase6e11_recovery_run_quota.sql'
SOURCE_SHA='00c3757bcb8b3da367285835e2b3013063838d133a9d77f2c10c718e72be2a5b'
CONSTRAINTS=legacy.CONSTRAINTS
TARGET=legacy.TARGET.replace('single_endchain_receipt','recovery_run_receipt').replace(legacy.VERSION,VERSION)
TARGET+=' || jsonb_build_object(\'legacy_m44\',('+legacy.TARGET+") - 'constraint' - 'constraint_oid' - 'run_hashes')"

def source(root):
    raw=(pathlib.Path(root)/'supabase/migrations'/FILE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('quota_candidate_bytes_changed')
    return raw.decode()

def expression(text):return re.search(r'check\((command_count>=0.*?)\);',text,re.S)[1]

def check_objects(value,text):
    stored=value['migration_statements']
    if not isinstance(stored,list) or ast(text)!=ast(';\n'.join(stored)):
        raise ValueError('quota_registered_sql_changed')
    body=text.split('as $f$',1)[1].split('$f$;',1)[0].replace('\r\n','\n')
    expected=dict(body_sha=hashlib.sha256(body.encode()).hexdigest(),owner='postgres',definer=False,
        path=['search_path=pg_catalog, pg_temp'],public_execute=False,forbidden_execute=False)
    if value['function_oid'] is None or value['function']!=expected:raise ValueError('quota_function_boundary')
    if value['trigger_oid'] is None or value['trigger']!=dict(type=27,enabled='O',function_matches=True,
        no_filter=True,no_arguments=True,constraint='0'):raise ValueError('quota_trigger_boundary')

def initial(state,root):
    value=state['catalog']['m44'];rows=state['migrations']
    names=[p.stem.split('_',1) for p in sorted((pathlib.Path(root)/'supabase/migrations').glob('*.sql'))]
    if len(names)!=45 or [[r['version'],r['name']] for r in rows] not in (names,names[:-1]):
        raise ValueError('quota_history_identity')
    check_objects(value['legacy_m44'],legacy.source(root))
    pending=len(rows)==44
    text=legacy.source(root) if pending else source(root)
    constraint=value['constraint']
    if not constraint or constraint['type']!='c' or not constraint['validated'] or ast('select '+constraint['expression'])!=ast('select '+expression(text)):
        raise ValueError('quota_constraint_expression')
    if pending:
        if any(value[k] is not None for k in ('function_oid','trigger_oid','migration_statements')):
            raise ValueError('quota_unregistered_objects')
    else:check_objects(value,source(root))
    return pending

def validate(before,after,root):
    pending=initial(before,root)
    if initial(after,root):raise ValueError('quota_registration_missing')
    b=before['catalog'];a=after['catalog'];bt=b['m44'];at=a['m44']
    if len(bt['run_hashes'])>200 or bt['run_hashes']!=at['run_hashes']:raise ValueError('quota_controller_rows_changed')
    if not pending:
        if before!=after:raise ValueError('quota_already_present_drift')
        return copy.deepcopy(after)
    if after['migrations'][:-1]!=before['migrations']:raise ValueError('quota_history_delta')
    if bt['legacy_m44']!=at['legacy_m44']:raise ValueError('quota_legacy_changed')
    stripped=copy.deepcopy(a);stripped['m44']=copy.deepcopy(bt)
    for group,key in [('functions','function_oid'),('triggers','trigger_oid')]:
        oid=str(at[key])
        if oid in b[group] or oid not in stripped[group]:raise ValueError('quota_added_object_missing')
        del stripped[group][oid]
    old_oid=str(bt['constraint_oid']);new_oid=str(at['constraint_oid'])
    if old_oid==new_oid or old_oid in a['constraints'] or new_oid not in a['constraints']:
        raise ValueError('quota_constraint_identity')
    del stripped['constraints'][new_oid];stripped['constraints'][old_oid]=b['constraints'][old_oid]
    if stripped!=b:raise ValueError('quota_unexpected_object_or_acl_delta')
    return copy.deepcopy(after)
