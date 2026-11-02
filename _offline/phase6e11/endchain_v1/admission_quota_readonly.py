"""Read-only M45 catalog proof on disposable CI; never executes a quota UUID.

Parent retains the older bridge/ACL checks, then calls run(gate). Four rows()
SELECTs replace mutation-based quota tests. A component PASS does not authorize
the new preparation run for 2349: the unchanged database gives it only 128.
"""
import hashlib
import json
import os
import pathlib

from admission_binding import NEW_RUN
from sql_protocol import parser

M45 = 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql'
M45_SHA = '64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635'
SCHEMA = 'fmz6e11_controller_private'
FUNCTION = 'recovery_run_receipt'
CONSTRAINT = 'runs_command_count_check'

QUERIES = {
    'constraint': """select c.conname name,c.contype::text kind,c.convalidated validated,
 c.connoinherit noinherit,c.conislocal local,c.coninhcount inherited,
 c.condeferrable deferrable,c.condeferred deferred,
 n.nspname schema,r.relname relation,pg_get_expr(c.conbin,c.conrelid,false) expression
 from pg_constraint c join pg_class r on r.oid=c.conrelid
 join pg_namespace n on n.oid=r.relnamespace
 where n.nspname='fmz6e11_controller_private' and r.relname='runs'
 and c.conname='runs_command_count_check'""",
    'function': """select n.nspname schema,p.proname name,p.pronargs nargs,
 p.prokind::text kind,p.prorettype='pg_catalog.trigger'::regtype returns_trigger,
 l.lanname language,pg_get_userbyid(p.proowner) owner,p.prosecdef definer,
 p.proleakproof leakproof,p.proisstrict strict,p.provolatile::text volatility,
 p.proparallel::text parallel,p.proconfig config,p.prosrc body,
 coalesce((select jsonb_agg(jsonb_build_object('grantee',pg_get_userbyid(a.grantee),
 'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable))
 from aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a),'[]'::jsonb) acl,
 jsonb_build_object('anon',has_function_privilege('anon',p.oid,'EXECUTE'),
 'authenticated',has_function_privilege('authenticated',p.oid,'EXECUTE'),
 'service_role',has_function_privilege('service_role',p.oid,'EXECUTE')) effective_execute
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 join pg_language l on l.oid=p.prolang
 where n.nspname='fmz6e11_controller_private' and p.proname='recovery_run_receipt'""",
    'trigger': """select n.nspname schema,r.relname relation,t.tgname name,
 pn.nspname function_schema,p.proname function_name,p.pronargs function_nargs,
 t.tgtype::int type,t.tgenabled::text enabled,t.tgisinternal internal,
 t.tgconstraint=0 nonconstraint,t.tgdeferrable deferrable,t.tginitdeferred deferred,
 t.tgnargs nargs,octet_length(t.tgargs) argument_bytes,t.tgattr::text columns,
 t.tgqual is null unconditional,t.tgoldtable old_transition,t.tgnewtable new_transition,
 pg_get_triggerdef(t.oid,false) definition
 from pg_trigger t join pg_class r on r.oid=t.tgrelid
 join pg_namespace n on n.oid=r.relnamespace
 join pg_proc p on p.oid=t.tgfoid join pg_namespace pn on pn.oid=p.pronamespace
 where n.nspname='fmz6e11_controller_private' and r.relname='runs'
 and t.tgname='recovery_run_receipt'""",
    'empty': """select not exists(select 1 from fmz6e11_controller_private.runs) runs_empty,
 not exists(select 1 from fmz6e11_controller_private.steps) steps_empty,
 not exists(select 1 from fmz6e11_controller_private.evidence) evidence_empty,
 current_setting('server_version_num')::int/10000=17 pg17,
 current_database()='postgres' database_ok""",
}


class QuotaStop(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strip_locations(value):
    """Keep every semantic AST field; discard only parser source coordinates."""
    if isinstance(value, dict):
        return {k: strip_locations(v) for k, v in value.items()
                if k not in ('location', 'stmt_location', 'stmt_len', 'arg_location')}
    if isinstance(value, (list, tuple)):
        return [strip_locations(v) for v in value]
    return value


def ast_hash(value):
    return sha(json.dumps(strip_locations(value), sort_keys=True, separators=(',', ':')).encode())


def single_node(text, kind):
    nodes = parser().parse_sql(text)
    if len(nodes) != 1 or type(nodes[0].stmt).__name__ != kind:
        raise QuotaStop('quota_ast_statement_shape')
    return nodes[0].stmt


def expression_ast(text):
    node = single_node('SELECT (' + text + ')', 'SelectStmt')
    if len(node.targetList) != 1:
        raise QuotaStop('quota_expression_shape')
    return strip_locations(node.targetList[0].val())


def source_contract(data):
    if sha(data) != M45_SHA:
        raise QuotaStop('quota_m45_source_hash')
    nodes = [n.stmt for n in parser().parse_sql(data.decode('utf-8'))]
    constraints = [c.def_ for n in nodes if type(n).__name__ == 'AlterTableStmt'
                   for c in n.cmds if c.def_ is not None and type(c.def_).__name__ == 'Constraint'
                   and c.def_.conname == CONSTRAINT]
    functions = [n for n in nodes if type(n).__name__ == 'CreateFunctionStmt']
    triggers = [n for n in nodes if type(n).__name__ == 'CreateTrigStmt']
    if len(constraints) != 1 or len(functions) != 1 or len(triggers) != 1:
        raise QuotaStop('quota_source_shape')
    function = functions[0]
    body = [option.arg[0].sval for option in function.options if option.defname == 'as']
    if len(body) != 1:
        raise QuotaStop('quota_source_body')
    expr = strip_locations(constraints[0].raw_expr())
    # Interpret only this tiny, exact source-bound CASE shape, never arbitrary SQL.
    try:
        case = expr['args'][1]['rexpr']
        if case['@'] != 'CaseExpr' or case['arg'] is not None: raise KeyError('case')
        caps = {}
        for branch in case['args']:
            uid = branch['expr']['rexpr']['arg']['val']['sval']
            cap = branch['result']['val']['ival']
            if uid in caps: raise KeyError('duplicate')
            caps[uid] = cap
        ordinary = case['defresult']['val']['ival']
        if len(caps) != 2 or sorted(caps.values()) != [2237, 2349] or ordinary != 128:
            raise KeyError('caps')
    except (KeyError, TypeError, IndexError):
        raise QuotaStop('quota_source_case_shape') from None
    if NEW_RUN in caps:
        raise QuotaStop('quota_preparation_exception_forbidden')
    return {'expression': expr, 'body': body[0], 'trigger': strip_locations(triggers[0]()),
            'ordinary_cap': ordinary, 'preparation_cap': ordinary}


def one(rows):
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise QuotaStop('quota_catalog_cardinality')
    return rows[0]


def typed_equal(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(typed_equal(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(typed_equal(a, b) for a, b in zip(actual, expected))
    return actual == expected


def exact_fields(row, expected):
    for key, value in expected.items():
        if key not in row or not typed_equal(row[key], value):
            raise QuotaStop('quota_catalog_field_' + key)


def validate(samples, contract):
    constraint = one(samples['constraint'])
    exact_fields(constraint, {'name': CONSTRAINT, 'kind': 'c', 'validated': True,
        'noinherit': False, 'local': True, 'inherited': 0, 'deferrable': False,
        'deferred': False, 'schema': SCHEMA, 'relation': 'runs'})
    actual = expression_ast(constraint['expression'])
    if actual != contract['expression']:
        raise QuotaStop('quota_constraint_ast_mismatch')
    function = one(samples['function'])
    exact_fields(function, {'schema': SCHEMA, 'name': FUNCTION, 'nargs': 0, 'kind': 'f',
        'returns_trigger': True, 'language': 'plpgsql', 'owner': 'postgres', 'definer': False,
        'leakproof': False, 'strict': False, 'volatility': 'v', 'parallel': 'u',
        'config': ['search_path=pg_catalog, pg_temp'], 'body': contract['body'],
        'effective_execute': {'anon': False, 'authenticated': False, 'service_role': False}})
    expected_acl = [{'grantee': 'postgres', 'grantor': 'postgres', 'privilege': 'EXECUTE', 'grantable': False}]
    if not typed_equal(function.get('acl'), expected_acl):
        raise QuotaStop('quota_function_acl')
    trigger = one(samples['trigger'])
    exact_fields(trigger, {'schema': SCHEMA, 'relation': 'runs', 'name': FUNCTION,
        'function_schema': SCHEMA, 'function_name': FUNCTION, 'function_nargs': 0,
        'type': 27, 'enabled': 'O', 'internal': False, 'nonconstraint': True,
        'deferrable': False, 'deferred': False, 'nargs': 0, 'argument_bytes': 0,
        'columns': '', 'unconditional': True, 'old_transition': None, 'new_transition': None})
    trigger_ast = strip_locations(single_node(trigger['definition'], 'CreateTrigStmt')())
    if trigger_ast != contract['trigger']:
        raise QuotaStop('quota_trigger_ast_mismatch')
    exact_fields(one(samples['empty']), dict.fromkeys(
        ('runs_empty', 'steps_empty', 'evidence_empty', 'pg17', 'database_ok'), True))
    return {'constraint_ast_sha256': ast_hash(actual), 'trigger_ast_sha256': ast_hash(trigger_ast),
            'function_body_sha256': sha(contract['body'].encode()),
            'ordinary_cap': contract['ordinary_cap'], 'new_preparation_cap': contract['preparation_cap']}


def run(gate):
    """Four read-only catalog SELECTs; raises after a sanitized NO_GO receipt."""
    receipt = {'status': 'NO_GO', 'component': 'quota_readonly', 'read_only': True,
               'hosted_admitted': False, 'quota_2349_admitted': False,
               'new_preparation_run': NEW_RUN, 'historical_uuid_reference_only': True,
               'mutation_commands': 0, 'sql_commands_attempted': 0, 'sql_commands_confirmed': 0}
    try:
        if (os.environ.get('GITHUB_ACTIONS') != 'true'
                or os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
                or os.environ.get('GITHUB_REF') != 'refs/heads/main'
                or getattr(gate, 'container', None) != 'supabase_db_fmz-db41-ci'):
            raise QuotaStop('quota_disposable_ci_required')
        data = (pathlib.Path(gate.sources) / M45).read_bytes()
        contract = source_contract(data)
        for query in QUERIES.values(): single_node(query, 'SelectStmt')
        gate.save('admission-quota-readonly-intent.json', {
            'm45_sha256': M45_SHA, 'mutation_commands': 0, 'planned_select_commands': 4,
            'queries': {name: sha(query.encode()) for name, query in QUERIES.items()},
            'old_uuid_sent_as_parameter': False, 'new_preparation_cap': 128})
        samples = {}
        for name, query in QUERIES.items():
            receipt['sql_commands_attempted'] += 1
            samples[name] = gate.rows(query)
            receipt['sql_commands_confirmed'] += 1
        receipt.update(validate(samples, contract), status='COMPONENT_PASS', m45_sha256=M45_SHA,
                       runs_empty=True, steps_empty=True, evidence_empty=True,
                       validated_constraint=True, invoker_and_private_acl=True)
    except Exception as error:
        receipt['reason'] = str(error) if isinstance(error, QuotaStop) else 'quota_catalog_or_transport_error'
        receipt['error_class'] = type(error).__name__
        gate.save('admission-quota-readonly.json', receipt)
        raise QuotaStop(receipt['reason']) from None
    gate.save('admission-quota-readonly.json', receipt)
    return receipt
