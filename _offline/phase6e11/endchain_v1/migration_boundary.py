"""Exact M43 -> M44 metadata transition; no SQL execution or access grant."""
import copy,hashlib,json,pathlib,re

VERSION='20261012185121'
FILE=VERSION+'_phase6e11_single_endchain_budget.sql'
SOURCE_SHA='b0e3d6ed8c988ede0405c348665d9d3a6e1bbd4f5f1da0ecf8dc1e8fb9698532'
TARGET="""jsonb_build_object(
 'function_oid',to_regprocedure('fmz6e11_controller_private.single_endchain_receipt()')::oid,
 'function',(select jsonb_build_object('body_sha',encode(sha256(convert_to(p.prosrc,'UTF8')),'hex'),
   'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'path',p.proconfig,
   'public_execute',exists(select 1 from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a where a.grantee=0 and a.privilege_type='EXECUTE'),
   'forbidden_execute',exists(select 1 from (values('anon'),('authenticated'),('service_role')) r(name) where has_function_privilege(r.name,p.oid,'EXECUTE')))
   from pg_proc p where p.oid=to_regprocedure('fmz6e11_controller_private.single_endchain_receipt()')),
 'trigger_oid',(select oid from pg_trigger where tgrelid='fmz6e11_controller_private.runs'::regclass and tgname='single_endchain_receipt'),
 'trigger',(select jsonb_build_object('type',tgtype,'enabled',tgenabled,'function_matches',tgfoid=to_regprocedure('fmz6e11_controller_private.single_endchain_receipt()'),
   'no_filter',tgqual is null,'no_arguments',tgnargs=0,'constraint',tgconstraint)
   from pg_trigger where tgrelid='fmz6e11_controller_private.runs'::regclass and tgname='single_endchain_receipt'),
 'constraint_oid',(select oid from pg_constraint where conrelid='fmz6e11_controller_private.runs'::regclass and conname='runs_command_count_check'),
 'constraint',(select jsonb_build_object('expression',pg_get_expr(conbin,conrelid),'validated',convalidated,'type',contype)
   from pg_constraint where conrelid='fmz6e11_controller_private.runs'::regclass and conname='runs_command_count_check'),
 'run_hashes',(select coalesce(jsonb_agg(h order by h),'[]') from (select encode(sha256(convert_to(to_jsonb(r)::text,'UTF8')),'hex') h from fmz6e11_controller_private.runs r limit 201) s),
 'migration_statements',(select to_jsonb(statements) from supabase_migrations.schema_migrations where version='20261012185121'))"""

CONSTRAINTS="""(select coalesce(jsonb_object_agg(p.oid::text,jsonb_build_object('name',p.conname,'table',p.conrelid,
 'definition',pg_get_constraintdef(p.oid),'validated',p.convalidated)),'{}') from pg_constraint p
 join pg_namespace n on n.oid=p.connamespace where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and n.nspname<>all($1::text[]))"""

def ast(text):
    from pglast.parser import parse_sql_json
    def clean(v):
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ('location','stmt_location','stmt_len')}
        if isinstance(v,list):return [clean(x) for x in v]
        return v
    return clean(json.loads(parse_sql_json(text)))['stmts']

def source(root):
    raw=(pathlib.Path(root)/'supabase/migrations'/FILE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('migration_candidate_bytes_changed')
    return raw.decode()

def validate(before,after,root):
    """Return a new expected state only after every exact delta is validated."""
    b=before['catalog'];a=after['catalog'];bt=b['m44'];at=a['m44'];text=source(root)
    if len(bt['run_hashes'])>200 or bt['run_hashes']!=at['run_hashes']:
        raise ValueError('migration_controller_rows_changed')
    if bt['function_oid'] is not None or bt['trigger_oid'] is not None or bt['migration_statements'] is not None:
        raise ValueError('migration_not_pending')
    if len(before['migrations'])!=43 or len(after['migrations'])!=44 or after['migrations'][:-1]!=before['migrations']:
        raise ValueError('migration_history_delta')
    if after['migrations'][-1]['version']!=VERSION or not isinstance(at['migration_statements'],list):
        raise ValueError('migration_registration_missing')
    if ast(text)!=ast(';\n'.join(at['migration_statements'])):raise ValueError('migration_registered_sql_changed')
    body=text.split('as $f$',1)[1].split('$f$;',1)[0]
    expected={'body_sha':hashlib.sha256(body.encode()).hexdigest(),'owner':'postgres','definer':False,
        'path':['search_path=pg_catalog, pg_temp'],'public_execute':False,'forbidden_execute':False}
    if at['function']!=expected:raise ValueError('migration_function_boundary')
    if at['trigger']!={'type':27,'enabled':'O','function_matches':True,'no_filter':True,'no_arguments':True,'constraint':0}:
        raise ValueError('migration_trigger_boundary')
    old=bt['constraint'];new=at['constraint']
    if not old or not new or any(c['type']!='c' or not c['validated'] for c in (old,new)):
        raise ValueError('migration_constraint_missing')
    expected_expr=re.search(r'check\((command_count>=0.*?)\);',text,re.S)[1]
    if ast('select '+old['expression'])!=ast('select command_count>=0 and command_count<=128') or ast('select '+new['expression'])!=ast('select '+expected_expr):
        raise ValueError('migration_constraint_expression')
    stripped=copy.deepcopy(a);stripped['m44']=copy.deepcopy(bt)
    for group,key in [('functions','function_oid'),('triggers','trigger_oid')]:
        oid=str(at[key])
        if at[key] is None or oid in b[group] or oid not in stripped[group]:raise ValueError('migration_added_object_missing')
        del stripped[group][oid]
    old_oid=str(bt['constraint_oid']);new_oid=str(at['constraint_oid'])
    if new_oid==old_oid or old_oid in a['constraints'] or new_oid not in a['constraints']:
        raise ValueError('migration_constraint_identity')
    del stripped['constraints'][new_oid];stripped['constraints'][old_oid]=b['constraints'][old_oid]
    if stripped!=b:raise ValueError('migration_unexpected_object_or_acl_delta')
    return copy.deepcopy(after)
