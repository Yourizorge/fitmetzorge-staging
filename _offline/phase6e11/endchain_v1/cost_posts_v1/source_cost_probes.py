"""Offline execution of pinned source fragments with recording capabilities only.

No database/process/network capability is supplied to the fragments. Results are
source derivations, not observations of PostgreSQL or managed Auth.
"""
import ast
import builtins
import copy
import hashlib
import json
from types import SimpleNamespace as NS


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def selected(raw, symbol, namespace, *, imports=None):
    tree = ast.parse(raw)
    nodes = tree.body
    parts = symbol.split('.')
    for part in parts:
        matches = [n for n in nodes if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == part]
        if len(matches) != 1:
            raise ValueError('source_symbol_ambiguous:' + symbol)
        node = matches[0]
        nodes = node.body
    if not isinstance(node, ast.FunctionDef) or node.decorator_list:
        raise ValueError('source_function_required')
    if imports is None and any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(node)):
        raise ValueError('fragment_import_denied')
    safe = {n: getattr(builtins, n) for n in
            ('len', 'range', 'dict', 'list', 'tuple', 'str', 'type', 'BaseException')}
    if imports is not None:
        def bound_import(name, globals=None, locals=None, fromlist=(), level=0):
            if (level, name) not in imports:
                raise ValueError('fragment_import_denied')
            return imports[(level, name)]
        safe['__import__'] = bound_import
    space = dict(namespace, __builtins__=safe)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<pinned-cost-fragment>', 'exec'), space)
    return space[node.name], sha(ast.dump(node, include_attributes=False).encode())


def native_gate_order(raw):
    """Actual _local_call source; no driver package or connection is loaded."""
    def run(kind, deny):
        events = []
        primary = Injected('offline_driver_guard')
        def native_proof(parameters):
            events.append('native_proof')
            if deny:
                raise primary
        def action():
            events.append('action')
        ledger = NS(precharge=lambda name: events.append('precharge') or 'ticket',
                    unknown=lambda *a, **kw: events.append('unknown'),
                    confirm=lambda *a, **kw: events.append('confirm'))
        owner = NS(_validate=lambda: None, gate=None, _extra_modules=[], _extra_binding='source',
                   _admitted=True, execution_ledger=ledger, _closing=False, _cleanup_selected=False,
                   _calls=[], server=NS(parameters={'host': '127.0.0.1'}))
        def require(value, reason):
            if not value:
                raise ValueError(reason)
        function, digest = selected(raw, 'Context._local_call',
            {'require': require, 'source_binding': NS(verify=lambda *a: 'source')},
            imports={(1, 'runtime_registered_costs'): NS(native_proof=native_proof)})
        error = None
        try:
            function(owner, 'offline_connection_boundary', kind, action)
        except BaseException as caught:
            error = caught
        require(events[:2] == ['precharge', 'native_proof'], 'native_guard_order')
        require(('action' not in events and error is primary) if deny else error is None, 'native_guard_escape')
        return {'kind': kind, 'guard_denied': deny, 'events': events,
                'primary_preserved': error is primary if deny else error is None, 'ast_sha256': digest}
    return [run(kind, deny) for kind in ('connection', 'connection_close') for deny in (False, True)]


def literal(raw, name):
    found = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(found) != 1:
        raise ValueError('source_literal_ambiguous:' + name)
    return ast.literal_eval(found[0])


def platform(raw):
    function, function_sha = selected(raw, '_operations', {
        'TLS_SETTINGS': literal(raw, 'TLS_SETTINGS'), 'COMMAND_ID': literal(raw, 'COMMAND_ID')})
    rows = function()
    if len(rows) != 36 or sum(r['explicit_sql_statements'] or 0 for r in rows) != 13:
        raise ValueError('platform_outer_contract_changed')
    # None means an outer process without a direct SQL string, NOT zero total
    # SQL: nested processes/startup/driver work remains in unknown_atoms.
    for row in rows:
        row['direct_sql_calls'] = row['explicit_sql_statements'] or 0
        row['total_sql_bound'] = None
    prefixes = []
    for index in range(len(rows) + 1):
        prefixes.append({'reached': index,
            'retained_outer_process_tickets': index,
            'retained_direct_sql_slots': sum(r['direct_sql_calls'] for r in rows[:index]),
            'unreached_direct_sql_slots': sum(r['direct_sql_calls'] for r in rows[index:]),
            'failure_cleanup_upper_bound': None, 'refund': 0})
    return {'symbol': '_operations', 'ast_sha256': function_sha, 'operations': rows,
        'prefixes': prefixes, 'direct_sql_upper_bound': 13, 'outer_process_upper_bound': 36,
        'total_sql_upper_bound': None, 'domain': 'LOCAL_CI', 'hosted_projection': 'NOT_APPLICABLE',
        'unknown_atoms': list(literal(raw, 'UNKNOWN')),
        'scope': 'Gate.install outer calls only; entry parser and nested processes excluded, not zero',
        'actual_execution_evidence': False}


class Injected(RuntimeError):
    pass


def seed(raw):
    function, function_sha = selected(raw, 'Context._seed', {
        'tracked': NS(sha=sha), 'json': json,
        'native_runtime': NS(ALIASES={r: r + '@invalid.example' for r in ('a_trainer', 'a_member', 'b_member')})})

    def trace(fail=None, edge='after', rollback_fail=False):
        events = []
        original = Injected('offline_primary')
        secondary = Injected('offline_rollback')
        def sql(name, text, args=None):
            row = {'id': name, 'sql_sha256': sha(text.encode()),
                   'reserved': 1, 'dispatch_attempted': False, 'confirmed': False}
            events.append(row)
            if name == fail and edge == 'before':
                raise original
            row['dispatch_attempted'] = True
            if name == fail:
                raise original
            if name == 'seed.rollback' and rollback_fail:
                raise secondary
            row['confirmed'] = True
        def remember(*args):
            if fail == 'seed_confirmed':
                raise original
            return {'offline_only': True}
        owner = NS(ids={r: r for r in ('a_trainer', 'a_member', 'b_member')},
                   server=NS(_sql=sql), _remember=remember)
        error = None
        try:
            function(owner)
        except BaseException as caught:
            error = caught
        return {'failure': fail, 'edge': edge, 'rollback_failure': rollback_fail,
            'commands': events, 'reserved': len(events), 'refund': 0,
            'primary_preserved': error is original if fail else error is None,
            'secondary_preserved': bool(getattr(error, '__notes__', [])),
            'commit_attempted': any(r['id'] == 'seed.commit' for r in events),
            'numeric_terminal': error is None, 'actual_execution_evidence': False}

    normal = trace()
    cases = [normal]
    for row in normal['commands']:
        for edge in ('before', 'after'):
            for rollback_fail in (False, True):
                cases.append(trace(row['id'], edge, rollback_fail))
    cases.append(trace('seed_confirmed'))
    if max(r['reserved'] for r in cases) != 9 or not all(r['primary_preserved'] for r in cases):
        raise ValueError('seed_source_bound_changed')
    if any(r['commit_attempted'] and any(c['id'] == 'seed.rollback' for c in r['commands']) for r in cases):
        raise ValueError('seed_unknown_commit_retried')
    return {'symbol': 'Context._seed', 'ast_sha256': function_sha,
        'direct_sql_upper_bound': 9, 'normal': normal, 'fault_prefixes': cases[1:],
        'fault_prefix_count': len(cases)-1, 'scope': 'explicit SQL on already-owned observer connection',
        'driver_cost_covered_by': 'auth.observer_connect/observer_close; unresolved separately',
        'unknown_commit_refund': 0, 'actual_execution_evidence': False}


def recovery_module(raw, filename):
    # This is the existing pure recorder, not an artifact import or a runtime
    # adapter. Its raw digest is checked by the caller; its own PINS validate
    # the four selected source fragments again before execution.
    allowed = {'ast', 'builtins', 'copy', 'contextlib', 'hashlib', 'itertools',
               'json', 'pathlib', 're', 'types'}
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name not in allowed:
            raise ValueError('recorder_import_denied')
        return builtins.__import__(name, globals, locals, fromlist, level)
    space = {'__name__': 'offline_pinned_recovery', '__file__': str(filename),
             '__builtins__': dict(vars(builtins), __import__=imports)}
    exec(compile(raw, str(filename), 'exec'), space)
    return space['RecoveryProgram']


def dispatch_guards(profile_raw, fixture_raw, protocol_raw, scope_raw, sql_raw):
    """Exercise original pre-dispatch ceilings independently of query results.

    Arbitrary distinct phases make the test more permissive than the real fixed
    plans; the actual guard must still refuse attempt LIMIT+1. This is a bound
    on single-statement explicit calls, not on implicit driver/server commands.
    """
    def require(value, code):
        if not value:
            raise ValueError(code)
    def one(raw, symbol, limit, instance):
        phases = {str(i): 'SELECT 1' for i in range(limit+1)}
        events, seen = [], set()
        journal = NS(save=lambda *a: None)
        namespace = dict(require=require, copy=copy, durable=NS(sha=sha), parent=NS(sha=sha),
            LIMIT=limit, PROTOCOL_LIMIT=limit, events=events, seen=seen, phases=phases,
            unchanged=lambda: None, journal=journal)
        charge, digest = selected(raw, symbol, namespace)
        state = NS(seen=seen, events=events, plan=phases,
                   state=NS(unchanged=lambda: None, journal=journal))
        def call(index):
            event = {'phase': str(index), 'sql_sha256': sha(b'SELECT 1')}
            return charge(state, event) if instance else charge(event)
        for index in range(limit):
            call(index)
        denied = False
        try:
            call(limit)
        except ValueError:
            denied = True
        if not denied or len(events) != limit:
            raise ValueError('guard_ceiling_not_enforced')
        return {'symbol': symbol, 'ast_sha256': digest, 'explicit_sql_upper_bound': limit,
                'limit_plus_one_denied': True, 'no_credit_for_failed_sql': True,
                'total_sql_upper_bound': None, 'actual_execution_evidence': False}
    # Validate the shared dispatcher charges before appending the intent and
    # before its sole connection.execute. Parsing refuses multi-statements.
    tree = ast.parse(protocol_raw)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Protocol')
    execute = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'execute')
    calls = [n for n in ast.walk(execute) if isinstance(n, ast.Call)]
    charge = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'charge']
    wire = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'execute']
    parser = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'statements']
    if len(charge) != 1 or len(wire) != 1 or len(parser) != 1 or not parser[0].lineno < charge[0].lineno < wire[0].lineno:
        raise ValueError('protocol_precharge_order_changed')
    queries = next(n.value for n in ast.parse(scope_raw).body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'QUERIES' for t in n.targets))
    if not isinstance(queries, ast.Tuple):
        raise ValueError('scope_query_tuple_changed')
    names = [ast.literal_eval(n.elts[0]) for n in queries.elts]
    plan, plan_sha = selected(fixture_raw, 'protocol_plan', {
        'LOCK': 'source-bound-placeholder', 'OWNED_INVENTORY': 'source-bound-placeholder',
        'scope': NS(QUERIES=[(n, 'source-bound-placeholder') for n in names], SESSION='source-bound-placeholder'),
        'parent': NS(REGISTRY='source-bound-placeholder', DELETE_OPERATOR='source-bound-placeholder',
                     DELETE_IDENTITIES='source-bound-placeholder'),
        'sql': NS(ORDER=literal(sql_raw, 'ORDER'), INVENTORY='source-bound-placeholder',
                  delete=lambda t: 'source-bound-placeholder')})
    normal_count = len(plan())
    limit_assignment = next(n.value for n in ast.parse(fixture_raw).body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'PROTOCOL_LIMIT' for t in n.targets))
    if ast.dump(limit_assignment) != ast.dump(ast.parse('NORMAL_COMMANDS + 1', mode='eval').body):
        raise ValueError('fixture_failure_reserve_changed')
    return {'auth_profile': one(profile_raw, '_execute.charge', literal(profile_raw, 'LIMIT'), False),
        'fixture_closeout': dict(one(fixture_raw, '_Dispatch.charge', normal_count+1, True),
            normal_explicit=normal_count, unknown_commit_physical_only_explicit=len(plan(physical_only=True)),
            plan_ast_sha256=plan_sha),
        'protocol_ast_sha256': sha(ast.dump(execute, include_attributes=False).encode()),
        'scope': 'single-statement direct dispatches through Protocol; no driver/managed bound'}
