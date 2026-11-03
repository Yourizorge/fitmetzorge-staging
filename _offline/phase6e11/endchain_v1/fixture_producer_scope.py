"""Bounded disposable PG17 scope observations, NOT a global producer barrier.

Scope(gate).before_bootstrap(); later Scope.after_mint_closure(terminal_ref).
Each observation is ten prepaid commands including rollback. Actual catalog
rows are checked against the candidate's migration ASTs; only digests/counts
are saved. Neither an empty activity snapshot nor this receipt authorizes a
DELETE. A consuming closure must also hold physical locks across its zero
inventory and mutation. GoTrue/Auth lifecycle remains a separate obligation.
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

import admission_module_binding as binding
from admission_binding import NEW_RUN
from fixture_cleanup_runtime import Blocked, Protocol, digest
import fixture_cleanup_runtime_sql as fixture_sql
from fixture_parent_closure import reference
from native_runtime import NativeRuntime
from sql_protocol import parser

TABLES = tuple(sorted(fixture_sql.ORDER))
SCHEMA = 'fmz6e11_private'
ROW_LIMIT = 256
LIMIT = 10
SCHEMAS = (SCHEMA, 'fmz6e11_audit_private', 'fmz6e11_workflow_audit', 'fmz6e11_request_private')
RELATIONS = """select c.relname name,c.relkind::text kind,c.relrowsecurity rls,
 c.relispartition partition,pg_get_userbyid(c.relowner) owner,
 exists(select 1 from pg_inherits i where c.oid in (i.inhrelid,i.inhparent)) inherited,
 exists(select 1 from pg_rewrite r where r.ev_class=c.oid) rules
 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='fmz6e11_private' and c.relname=any($1::text[]) limit 257"""
SESSION = """select pg_backend_pid() pid,
 (select system_identifier::text from pg_control_system()) cluster_id,
 pg_postmaster_start_time()::text postmaster_start,
 (select oid::text from pg_database where datname=current_database()) datid,
 current_setting('server_version_num')::int/10000=17 pg17,
 current_setting('statement_timeout') in ('5s','5000ms') statement_bounded,
 current_setting('lock_timeout') in ('1s','1000ms') lock_bounded,
 current_setting('max_prepared_transactions')='0' no_prepared,
 current_setting('track_activities')='on' tracked,
 current_setting('transaction_isolation')='read committed' fresh,
 current_setting('session_replication_role')='origin' origin,
 current_user='postgres' and current_database()='postgres' privileged"""
PRIVILEGES = """select r.rolname role,r.rolsuper superuser,r.rolcreaterole createrole,
 exists(select 1 from pg_roles x where x.oid<>r.oid and
 (pg_has_role(r.oid,x.oid,'USAGE') or pg_has_role(r.oid,x.oid,'SET'))
 and (x.rolsuper or x.rolcreaterole)) elevated_membership,
 exists(select 1 from pg_namespace n where n.nspname=any($1::text[])
 and has_schema_privilege(r.oid,n.oid,'CREATE')) schema_create,
 exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=any($1::text[]) and c.relkind in ('r','p','v','m','f')
 and (has_table_privilege(r.oid,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
 or has_any_column_privilege(r.oid,c.oid,'INSERT,UPDATE'))) direct_write,
 exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname=any($1::text[]) and has_function_privilege(r.oid,p.oid,'EXECUTE')
 and not(r.rolname='authenticated' and n.nspname='fmz6e11_private'
 and p.proname='api_call' and p.proargtypes='3802'::oidvector)) private_execute,
 exists(select 1 from pg_roles x where x.oid<>r.oid and pg_has_role(r.oid,x.oid,'SET')
 and exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=any($1::text[]) and c.relkind in ('r','p')
 and (has_table_privilege(x.oid,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
 or has_any_column_privilege(x.oid,c.oid,'INSERT,UPDATE')))) set_role_write,
 exists(select 1 from pg_roles x where x.oid<>r.oid and pg_has_role(r.oid,x.oid,'SET')
 and (exists(select 1 from pg_namespace n where n.nspname=any($1::text[])
 and has_schema_privilege(x.oid,n.oid,'CREATE')) or exists(select 1 from pg_proc p
 join pg_namespace n on n.oid=p.pronamespace where n.nspname=any($1::text[])
 and has_function_privilege(x.oid,p.oid,'EXECUTE')
 and not(x.rolname='authenticated' and n.nspname='fmz6e11_private'
 and p.proname='api_call' and p.proargtypes='3802'::oidvector)))) set_role_indirect_write
 from pg_roles r where r.rolname in ('supabase_auth_admin','anon','authenticated','service_role') limit 257"""
# All Auth relations and their cascading descendants, not only auth.users.
REACHABLE = """with recursive reachable(oid) as (
 select c.oid from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='auth' and c.relkind in ('r','p')
 union select k.conrelid from pg_constraint k join reachable r on k.confrelid=r.oid
 where k.contype='f' and (k.confdeltype in ('c','n','d') or k.confupdtype in ('c','n','d'))
), targets as (select oid from reachable union select c.oid from pg_class c
 join pg_namespace n on n.oid=c.relnamespace where n.nspname='fmz6e11_private') """
TRIGGERS = REACHABLE + """select n.nspname schema,c.relname relation,t.tgname name,
 t.tgtype::int type,t.tgenabled::text enabled,pn.nspname function_schema,p.proname function_name,
 p.pronargs nargs,octet_length(t.tgargs) argument_bytes,t.tgattr::text columns,
 t.tgqual is null unconditional,t.tgconstraint=0 nonconstraint,
 t.tgoldtable old_transition,t.tgnewtable new_transition
 from pg_trigger t join targets x on x.oid=t.tgrelid join pg_class c on c.oid=x.oid
 join pg_namespace n on n.oid=c.relnamespace join pg_proc p on p.oid=t.tgfoid
 join pg_namespace pn on pn.oid=p.pronamespace
 where not t.tgisinternal limit 257"""
FUNCTIONS = REACHABLE + """select n.nspname schema,p.proname name,p.pronargs nargs,
 array(select jsonb_build_object('schema',an.nspname,'name',at.typname,'array',at.typarray=t.oid)
 from unnest(p.proargtypes) with ordinality v(oid,ord) join pg_type t on t.oid=v.oid
 join pg_type at on at.oid=case when t.oid=(select e.typarray from pg_type e where e.oid=t.typelem)
 then t.typelem else t.oid end
 join pg_namespace an on an.oid=at.typnamespace order by v.ord) argument_types,
 l.lanname language,p.prosecdef definer,p.proconfig config,pg_get_userbyid(p.proowner) owner,
 encode(sha256(convert_to(replace(p.prosrc,chr(13)||chr(10),chr(10)),'UTF8')),'hex') body_sha256,
 has_function_privilege('supabase_auth_admin',p.oid,'EXECUTE') auth_execute
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace join pg_language l on l.oid=p.prolang
 where n.nspname=any($1::text[]) or (n.nspname='public' and p.proname='fmz6e11_call')
 or exists(select 1 from pg_trigger t join targets x on x.oid=t.tgrelid
 where t.tgfoid=p.oid and not t.tgisinternal)
 or (p.prosecdef and n.nspname not in ('pg_catalog','auth','information_schema')
 and has_function_privilege('supabase_auth_admin',p.oid,'EXECUTE')) limit 257"""
FKS = """select c.relname relation,array(select a.attname::text from unnest(k.conkey)
 with ordinality v(attnum,ord) join pg_attribute a on a.attrelid=c.oid and a.attnum=v.attnum order by v.ord) columns,
 tn.nspname target_schema,tc.relname target,
 array(select a.attname::text from unnest(k.confkey) with ordinality v(attnum,ord)
 join pg_attribute a on a.attrelid=tc.oid and a.attnum=v.attnum order by v.ord) target_columns,
 k.confdeltype::text on_delete,k.confupdtype::text on_update,k.convalidated validated,
 k.condeferrable deferrable,k.condeferred deferred
 from pg_constraint k join pg_class c on c.oid=k.conrelid
 join pg_namespace n on n.oid=c.relnamespace join pg_class tc on tc.oid=k.confrelid
 join pg_namespace tn on tn.oid=tc.relnamespace
 where k.contype='f' and n.nspname='fmz6e11_private' and c.relname=any($1::text[]) limit 257"""
GATES = """select (select count(*)=1 and bool_and(not enabled) from fmz6e11_private.config) rpc_closed,
 (select count(*)=1 and bool_and(not enabled) from fmz6e11_workflow_audit.control) bridge_closed,
 not exists(select 1 from fmz6e11_private.windows where feature_enabled or status='active') windows_closed,
 not exists(select 1 from fmz6e11_private.identities) identities_empty,
 not exists(select 1 from fmz6e11_private.operators) operators_empty"""
# Never collect query text, JWT claims, addresses, or connection parameters.
ACTIVITY = """select pid,backend_start::text backend_start,usename,backend_type,state
 from pg_stat_activity where datid=(select oid from pg_database where datname=current_database())
 and pid<>pg_backend_pid() and (usename is distinct from 'supabase_auth_admin'
 or backend_type is distinct from 'client backend') limit 257"""
QUERIES = (('session', SESSION), ('relations', RELATIONS), ('privileges', PRIVILEGES),
           ('functions', FUNCTIONS), ('triggers', TRIGGERS), ('fks', FKS), ('gates', GATES), ('activity', ACTIVITY))
SAFE_AUTH_FUNCTIONS = {('public', 'fmz_handle_new_auth_user', 0), ('public', 'touch_updated_at', 0)}
PRIVILEGE_FLAGS = ('superuser','createrole','elevated_membership','schema_create',
                   'direct_write','private_execute','set_role_write','set_role_indirect_write')


class PrivilegeViolation(Blocked):
    """Only fixed role/flag enums escape; never persist raw catalog rows."""
    def __init__(self, roles):
        super().__init__('producer_unexpected_privilege')
        self.diagnostics = [{'role': row['role'], 'flags': {
            flag: 'true' if row.get(flag) is True else 'missing_or_non_boolean'
            for flag in PRIVILEGE_FLAGS if row.get(flag) is not False}}
            for row in roles if any(row.get(flag) is not False for flag in PRIVILEGE_FLAGS)]


def source_contract(gate):
    """Only candidate-registered migration bytes; no checkout fallback or third root."""
    root = binding.checked_path(gate.sources)
    manifest = json.loads(binding.checked_path(pathlib.Path(gate.out)/'candidate.json').read_bytes(),
                          object_pairs_hook=binding.unique_object)
    sources = manifest['sources']
    names = sorted(n for n in sources if n.startswith('supabase/migrations/') and n.endswith('.sql'))
    if not 1 <= len(names) <= 64: raise Blocked('producer_migration_bound')
    functions, triggers, fks, hashes = {}, {}, [], {}
    for name in names:
        path = binding.checked_path(root/name)
        if not path.is_relative_to(root): raise Blocked('producer_source_escape')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sources[name]: raise Blocked('producer_source_hash')
        hashes[name] = sources[name]
        for statement in parser().parse_sql(raw.decode('utf-8-sig').replace('\r\n', '\n')):
            node = statement.stmt
            kind = type(node).__name__
            if kind == 'CreateFunctionStmt':
                names_ = tuple(s.sval for s in node.funcname)
                if len(names_) != 2: continue
                opts = {o.defname: o.arg for o in node.options or () if o.defname != 'set'}
                body = opts.get('as')
                if not body or len(body) != 1: continue
                configs = [o.arg for o in node.options if o.defname == 'set']
                if any(not o.args or any(type(v.val).__name__ != 'String' for v in o.args) for o in configs):
                    continue  # Unsupported function configuration is not an allowlist entry.
                config = [o.name+'='+', '.join(v.val.sval for v in o.args) for o in configs]
                key = (*names_, len(node.parameters or ()))
                argument_types=[]
                for parameter in node.parameters or ():
                    type_names=[v.sval for v in parameter.argType.names]
                    argument_types.append({'schema':type_names[-2] if len(type_names)>1 else 'pg_catalog',
                        'name':type_names[-1], 'array':bool(parameter.argType.arrayBounds)})
                functions[key] = {'body_sha256': hashlib.sha256(body[0].sval.encode()).hexdigest(),
                    'argument_types':argument_types,
                    'language': opts['language'].sval, 'definer': bool(opts.get('security') and opts['security'].boolval),
                    'config': config or None, 'owner': 'postgres'}
            elif kind == 'CreateTrigStmt':
                key = (node.relation.schemaname or 'public', node.relation.relname, node.trigname)
                triggers[key] = {'type': node.events | node.timing | int(node.row),
                    'function_schema': node.funcname[0].sval, 'function_name': node.funcname[1].sval}
            elif kind == 'CreateStmt' and node.relation.schemaname == SCHEMA and node.relation.relname in TABLES:
                for col in node.tableElts or ():
                    constraints = col.constraints if type(col).__name__ == 'ColumnDef' else (col,)
                    for c in constraints or ():
                        if type(c).__name__ != 'Constraint' or c.pktable is None: continue
                        fks.append({'relation': node.relation.relname,
                            'columns': [s.sval for s in c.fk_attrs] if c.fk_attrs else [col.colname],
                            'target_schema': c.pktable.schemaname or SCHEMA, 'target': c.pktable.relname,
                            'target_columns': [s.sval for s in c.pk_attrs],
                            'on_delete': c.fk_del_action, 'on_update': c.fk_upd_action,
                            'validated': True, 'deferrable': bool(c.deferrable), 'deferred': bool(c.initdeferred)})
    # This one trigger is created inside the bound legacy DO block, not top-level SQL.
    triggers[('auth','users','fmz_after_auth_user_insert_bootstrap')] = {
        'type': 5, 'function_schema': 'public', 'function_name': 'fmz_handle_new_auth_user'}
    external = [f for f in fks if f['target_schema'] == 'auth']
    if len(external) != 9 or any(f['target'] != 'users' or f['on_delete'] != 'a'
                              or f['on_update'] != 'a' for f in external):
        raise Blocked('producer_nine_noaction_source_contract')
    return {'functions': functions, 'triggers': triggers, 'fks': fks, 'hashes': hashes}


def bounded(rows):
    if not isinstance(rows, list) or len(rows) > ROW_LIMIT or any(not isinstance(r, dict) for r in rows):
        raise Blocked('producer_metadata_bound')
    return rows


def one(rows):
    if len(bounded(rows)) != 1: raise Blocked('producer_metadata_cardinality')
    return rows[0]


def validate(samples, contract, *, before):
    for rows in samples.values(): bounded(rows)
    session = one(samples['session'])
    flags = ('pg17','statement_bounded','lock_bounded','no_prepared','tracked','fresh','origin','privileged')
    if any(session.get(k) is not True for k in flags): raise Blocked('producer_session_limits')
    relations = samples['relations']
    if len(relations) != 13 or {r['name'] for r in relations} != set(TABLES):
        raise Blocked('producer_exact_thirteen_tables')
    for r in relations:
        if any(r.get(k) != v for k, v in {'kind':'r','rls':True,'partition':False,
                'owner':'postgres','inherited':False,'rules':False}.items()):
            raise Blocked('producer_relation_shape')
    roles = samples['privileges']
    if len(roles) != 4 or {r['role'] for r in roles} != {'supabase_auth_admin','anon','authenticated','service_role'}:
        raise Blocked('producer_role_set')
    if any(r.get(k) is not False for r in roles for k in PRIVILEGE_FLAGS):
        raise PrivilegeViolation(roles)
    if sorted(map(digest, samples['fks'])) != sorted(map(digest, contract['fks'])):
        raise Blocked('producer_fk_contract')
    seen = set()
    for row in samples['functions']:
        key = (row['schema'], row['name'], row['nargs'])
        if key in seen or key not in contract['functions']: raise Blocked('producer_unbound_function')
        seen.add(key)
        if any(row.get(k) != v for k,v in contract['functions'][key].items()):
            raise Blocked('producer_changed_function')
        if row.get('auth_execute') is not False and key not in SAFE_AUTH_FUNCTIONS:
            raise Blocked('producer_auth_callable_unreviewed_function')
    required = {(SCHEMA,n,1) for n in ('api_call','base_call')} | {(SCHEMA,'principal',0), ('public','fmz6e11_call',1)}
    if not required <= seen: raise Blocked('producer_rpc_function_missing')
    observed = set()
    for row in samples['triggers']:
        key = (row['schema'], row['relation'], row['name'])
        expected = contract['triggers'].get(key)
        if row['name'] == 'fmz6e11_tx_observer' and row['schema'] in ('public',SCHEMA):
            expected = {'type':29, 'function_schema':'fmz6e11_audit_private', 'function_name':'observe'}
        if key in observed or expected is None: raise Blocked('producer_unregistered_trigger')
        observed.add(key)
        expected = {**expected, 'enabled':'O','nargs':0,'argument_bytes':0,'columns':'',
                    'unconditional':True,'nonconstraint':True,'old_transition':None,'new_transition':None}
        if any(row.get(k) != v for k,v in expected.items()): raise Blocked('producer_changed_trigger')
        if (row['function_schema'],row['function_name'],0) not in seen:
            raise Blocked('producer_trigger_function_missing')
    required_triggers = {(SCHEMA,t,'fmz6e11_tx_observer') for t in TABLES}
    required_triggers |= {k for k in contract['triggers'] if k[0] == SCHEMA}
    required_triggers.add(('auth','users','fmz_after_auth_user_insert_bootstrap'))
    if not required_triggers <= observed: raise Blocked('producer_trigger_missing')
    gates = one(samples['gates'])
    fields = ('rpc_closed','bridge_closed','windows_closed') + (('identities_empty','operators_empty') if before else ())
    if any(gates.get(k) is not True for k in fields): raise Blocked('producer_rpc_or_bootstrap_open')
    if samples['activity']: raise Blocked('producer_external_backend_present')
    return {'cluster_id': session['cluster_id'], 'postmaster_start': session['postmaster_start'],
            'datid': session['datid'], 'tables': list(TABLES), 'auth_fk_noaction_count': 9,
            'metadata_sha256': digest(samples), 'migration_sources_sha256': digest(contract['hashes'])}


class Meter:
    def __init__(self, save, prefix, limit):
        self.save, self.prefix, self.limit, self.used, self.poisoned = save, prefix, limit, 0, False
        self.protocol = Protocol(self.charge)
    def charge(self, event):
        if self.poisoned or self.used >= self.limit: raise Blocked('producer_meter_closed')
        self.used += 1
        try: self.save(self.prefix+'-charge-%03d.json'%self.used, {**event, 'limit':self.limit,
            'admitted':self.used, 'budget_domain':'additional_disposable_diagnostic_not_2349'})
        except BaseException:
            self.poisoned = True
            raise
    def query(self, connection, phase, text, args=(), *, reserve=1):
        if self.used >= self.limit-reserve: raise Blocked('producer_protocol_limit')
        return self.protocol.execute(connection, phase, text, args)


def collect(connection, meter, contract, *, before):
    samples = {}
    for name,text in QUERIES:
        args = [list(TABLES)] if name in ('relations','fks') else [list(SCHEMAS)] if name in ('privileges','functions') else ()
        samples[name] = bounded(meter.query(connection, name, text, args))
    return validate(samples, contract, before=before)


class Scope:
    def __init__(self, gate):
        if (os.environ.get('GITHUB_ACTIONS') != 'true'
                or os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
                or os.environ.get('GITHUB_REF') != 'refs/heads/main'
                or getattr(gate,'container',None) != 'supabase_db_fmz-db41-ci'):
            raise Blocked('producer_disposable_required')
        self.gate, self.attempted, self.baseline = gate, set(), None
        self.binding = binding.verify(gate, [sys.modules[__name__], binding,
            sys.modules[Protocol.__module__], fixture_sql, sys.modules[NativeRuntime.__module__],
            sys.modules[parser.__module__], sys.modules[reference.__module__]])
        self.contract = source_contract(gate)

    def before_bootstrap(self):
        return self._observe('before', None)

    def after_mint_closure(self, terminal_ref):
        if self.baseline is None: raise Blocked('producer_before_bootstrap_required')
        terminal = reference(self.gate.out, terminal_ref)
        if (terminal.get('preparation_run') != NEW_RUN or terminal.get('db_terminality_proven') is not True
                or terminal.get('classification') != 'TRACKED_DB_BACKENDS_TERMINAL'):
            raise Blocked('producer_tracked_terminal_required')
        return self._observe('after', terminal_ref)

    def _observe(self, stage, terminal_ref):
        if stage in self.attempted: raise Blocked('producer_duplicate_observation')
        self.attempted.add(stage)
        if source_contract(self.gate) != self.contract:
            raise Blocked('producer_source_contract_changed')
        prefix = 'fixture-producer-scope-'+stage
        meter = Meter(self.gate.save, prefix, LIMIT)
        result = {'status':'NO_GO','preparation_run':NEW_RUN,'stage':stage,'terminal_ref':terminal_ref,
            'global_auth_barrier':False,'physical_exclusion_held':False,'mutation_admitted':False,
            'protocol_limit':LIMIT,'source_binding':self.binding}
        self.gate.save(prefix+'-intent.json', result)
        runtime, raw, began, error = None, None, False, None
        try:
            runtime = NativeRuntime.disposable(self.gate)
            raw = runtime.connect()
            if raw.autocommit is not True: raise Blocked('producer_autocommit_required')
            began = True
            meter.query(raw,'begin','BEGIN TRANSACTION READ ONLY')
            result.update(collect(raw,meter,self.contract,before=stage=='before'))
            if stage == 'after' and any(result[k] != self.baseline[k] for k in
                    ('cluster_id','postmaster_start','datid','migration_sources_sha256')):
                raise Blocked('producer_baseline_changed')
        except BaseException as caught: error = caught
        finally:
            for action in (lambda: meter.query(raw,'rollback','ROLLBACK',reserve=0) if began else None,
                           lambda: raw.close() if raw is not None else None,
                           lambda: runtime.clear() if runtime is not None else None):
                try: action()
                except BaseException as caught:
                    if error is None: error = caught
                    else: error.add_note('scope finalizer: '+type(caught).__name__)
        result.update(admitted_attempts=meter.used, emitted_attempts=len(meter.protocol.events),
                      protocol=copy.deepcopy(meter.protocol.events))
        if error is not None:
            result.update(reason=str(error) if isinstance(error,Blocked) else 'producer_observation_failed',
                          error_class=type(error).__name__)
            if isinstance(error,PrivilegeViolation):
                result['privilege_violations'] = copy.deepcopy(error.diagnostics)
        else: result['status'] = 'SCOPE_METADATA_CONFIRMED_NOT_A_BARRIER'
        self.gate.save(prefix+'-result.json',result)
        if error is not None: raise error
        if stage == 'before': self.baseline = copy.deepcopy(result)
        return result
