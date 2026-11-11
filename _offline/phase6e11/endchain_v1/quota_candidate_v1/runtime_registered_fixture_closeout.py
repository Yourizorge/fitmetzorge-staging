"""Registered-case adapter for the existing exact thirteen-table DELETE engine.

prepare(Context) is a zero-SQL pre-body hook. run(Context) is a one-shot parent
suffix, not a case PASS. No component-case journal or caller barrier is accepted.
Every dispatch is separately admitted by the actual parent's root ledger.
"""
import copy
import inspect
import json
import pathlib
import sys
import uuid
import weakref

import admission_journal as durable
import admission_binding
import admission_module_binding as binding
from admission_binding import NEW_RUN, OLD_RUN
import fixture_cleanup_runtime as engine
import fixture_cleanup_runtime_sql as sql
import fixture_lifecycle as fixture
import fixture_parent_closure as parent
import fixture_producer_scope as scope

PREFIX = 'registered-fixture-closeout'
_REGISTRATIONS = weakref.WeakKeyDictionary()
_PROOFS = weakref.WeakKeyDictionary()
LOCK = parent.REGISTRY_LOCK.replace(' IN SHARE',
    ',fmz6e11_private.config,fmz6e11_workflow_audit.control,'
    'fmz6e11_request_private.control,fmz6e11_request_private.receipts,'
    'fmz6e11_audit_private.actions,fmz6e11_audit_private.writes,'
    'fmz6e11_audit_private.relations IN SHARE')
AUDIT_KEYS = {**sql.KEYS, 'proposals': ('workspace_id', 'version'),
    'audit': ('window_id', 'actor', 'action'),
    'events': ('window_id', 'workspace_id', 'actor', 'request_key', 'action', 'outcome')}


def require(ok, code):
    if not ok:
        raise engine.Blocked('registered_fixture_' + code)


def fresh(value):
    require(type(value) is str and str(uuid.UUID(value)) == value
            and value not in (OLD_RUN, NEW_RUN), 'fresh_uuid')
    return value


# Authorized actions come only from original pre-dispatch filesystem records.
# The audit observer binds each write to the action's full xid/backend/actor.
# Both an owned INSERT and the CURRENT tuple version are mandatory. A matching
# key alone, or an old audit entry for a later foreign version, grants no deletion.
AUTHORIZED = """with permitted as (
 select a.* from fmz6e11_audit_private.actions a
 where a.actor=any($5::uuid[]) and a.workspace=any($2::uuid[])
 and a.state in ('action_confirmed','pair_validated') and a.xid is not null
 and (exists(select 1 from jsonb_to_recordset($3::jsonb)
 e(id uuid,run uuid,before_sha text) where a.id=e.id and a.run_id=e.run
 and a.before_sha=e.before_sha)
 or exists(select 1 from fmz6e11_request_private.receipts r
 where r.request_id=any($4::uuid[]) and r.action_id=a.id and r.run_id=a.run_id
 and r.actor=a.actor and r.workspace_id=a.workspace and r.window_id=$1::uuid
 and r.xid=a.xid and r.backend=a.backend and r.state in ('confirmed','pair_validated')))
), owned as (
 select w.* from fmz6e11_audit_private.writes w join permitted a on a.id=w.action_id
 where w.run_id=a.run_id and w.xid=a.xid and w.backend=a.backend
 and w.actor=a.actor and w.workspace=a.workspace
 and exists(select 1 from jsonb_array_elements(a.expected) e
 where e->>'table'=w.table_name and e->>'op'=w.operation
 and e->>'old' is not distinct from w.old_key_sha
 and e->>'new' is not distinct from w.new_key_sha)
) """


def _owned(table, version):
    key = 'jsonb_build_array(' + ','.join('t.'+c for c in AUDIT_KEYS[table]) + ')'
    # Compute the exact canonical salted audit key directly; do not trust a
    # mutable relations.pk_columns entry or invoke a user-replaced function.
    salted = sql.sha("jsonb_build_array('fmz6e11-key-v1',w.run_id::text,"
                     "'fmz6e11_private." + table + "'," + key + ')')
    return ("exists(select 1 from owned w where w.table_name='fmz6e11_private."+table+
            "' and w.new_key_sha="+salted+
            (" and w.operation in ('INSERT','UPDATE') and mod(w.xid::text::numeric,4294967296)::text=t.xmin::text"
             if version else " and w.operation='INSERT'") + ')')


OWNED_INVENTORY = AUTHORIZED + "select jsonb_build_object('rows',coalesce(jsonb_agg(value),'[]'::jsonb),'xid',null) value from (" + ' union all '.join(
    'select '+sql.metadata(t)+" || jsonb_build_object('scope_ok',"+sql.scope_ok(t)+
    ",'insert_owned',"+_owned(t, False)+",'version_owned',"+_owned(t, True)+
    ') value from fmz6e11_private.'+t+' t where '+sql.TABLE_SCOPE[t]
    for t in sql.ORDER) + ' limit 1001) inventory'


def protocol_plan(*, physical_only=False):
    rows = [('begin', 'BEGIN'), ('lock', LOCK), *scope.QUERIES,
            ('ownership_inventory', OWNED_INVENTORY), ('registry_before', parent.REGISTRY)]
    if not physical_only:
        rows += [('delete_'+t, sql.delete(t)) for t in sql.ORDER]
    rows += [('fixture_zero', sql.INVENTORY), ('delete_operator', parent.DELETE_OPERATOR),
             ('delete_identities', parent.DELETE_IDENTITIES), ('registry_after', parent.REGISTRY),
             ('commit', 'COMMIT'), ('absence_begin', 'BEGIN'), ('absence_lock', LOCK),
             ('absence_session', scope.SESSION), ('absence_fixture', sql.INVENTORY),
             ('absence_registry', parent.REGISTRY), ('absence_rollback', 'ROLLBACK')]
    return rows


NORMAL_COMMANDS = len(protocol_plan())
PROTOCOL_LIMIT = NORMAL_COMMANDS + 1

CATALOG_FIELDS = {
    'session': 'pid cluster_id postmaster_start datid pg17 statement_bounded lock_bounded no_prepared tracked fresh origin privileged',
    'relations': 'name kind rls partition owner inherited rules',
    'privileges': 'role '+ ' '.join(scope.PRIVILEGE_FLAGS),
    'functions': 'schema name nargs argument_types language definer config owner body_sha256 auth_execute',
    'triggers': 'schema relation name type enabled function_schema function_name nargs argument_bytes columns unconditional nonconstraint old_transition new_transition',
    'fks': 'relation columns target_schema target target_columns on_delete on_update validated deferrable deferred',
    'gates': 'rpc_closed bridge_closed windows_closed identities_empty operators_empty',
    'activity': 'pid backend_start usename backend_type state',
}


def observation_rows(phase, rows, contract):
    """Only technical projections selected by the pinned query may be exported."""
    require(type(rows) is list and len(rows) <= 1001, 'observation_bound')
    result = copy.deepcopy(rows)
    catalog = 'session' if phase == 'absence_session' else phase
    if catalog in CATALOG_FIELDS:
        require(len(rows) <= 257, 'catalog_observation_bound')
        fields = set(CATALOG_FIELDS[catalog].split())
        require(all(type(row) is dict and set(row) == fields for row in rows), 'observation_fields')
        booleans = {'pg17','statement_bounded','lock_bounded','no_prepared','tracked','fresh','origin',
            'privileged','rls','partition','inherited','rules','definer','auth_execute','unconditional',
            'nonconstraint','validated','deferrable','deferred','rpc_closed','bridge_closed',
            'windows_closed','identities_empty','operators_empty',*scope.PRIVILEGE_FLAGS}
        require(all(type(v) is bool for row in rows for k,v in row.items() if k in booleans),
                'observation_boolean')
        if catalog == 'functions':
            for row in result:
                expected = contract.get('functions', {}).get((row['schema'], row['name'], row['nargs']))
                if row['config'] is not None and (expected is None or row['config'] != expected['config']):
                    require(type(row['config']) is list and len(row['config']) <= 256
                            and all(type(v) is str for v in row['config']), 'observation_config')
                    raw = json.dumps(row['config'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
                    row['config'] = {'redacted':True,'sha256':parent.sha(raw),
                                     'bytes':len(raw),'count':len(row['config'])}
                require(type(row['argument_types']) is list and all(type(t) is dict and
                    set(t) == {'schema','name','array'} for t in row['argument_types']), 'observation_types')
    elif phase in ('ownership_inventory','fixture_zero','absence_fixture'):
        for row in result:
            require(type(row) is dict and set(row) == {'value'} and type(row['value']) is dict
                    and set(row['value']) == {'rows','xid'}, 'observation_inventory')
            fields = {'table','key_sha','row_sha','xmin','scope_ok'}
            if phase == 'ownership_inventory': fields |= {'insert_owned','version_owned'}
            require(type(row['value']['rows']) is list and len(row['value']['rows']) <= 1001
                    and all(type(r) is dict and set(r) == fields for r in row['value']['rows']),
                    'observation_inventory_fields')
    elif phase in ('registry_before','registry_after','absence_registry'):
        for row in result:
            require(type(row) is dict and set(row) == {'value'} and type(row['value']) is dict
                    and set(row['value']) == {'identities','operators'}, 'observation_registry')
            for key, fields in (('identities', {'id','role','provenance_sha','enabled'}),
                                ('operators', {'id','enabled'})):
                require(type(row['value'][key]) is list and len(row['value'][key]) <= 1001
                        and all(type(r) is dict and set(r) == fields for r in row['value'][key]),
                        'observation_registry_fields')
    elif phase in ('delete_operator','delete_identities'):
        fields = {'id','enabled'} if phase == 'delete_operator' else {'id','role','provenance_sha','enabled'}
        require(all(type(row) is dict and set(row) == fields for row in result), 'observation_returning')
    elif phase in {'delete_'+t for t in sql.ORDER}:
        for row in result:
            require(type(row) is dict and set(row) == {'value'} and type(row['value']) is list
                    and len(row['value']) <= 1001 and all(type(r) is dict and
                    set(r) == {'table','key_sha','row_sha','xmin'} for r in row['value']),
                    'observation_delete_fields')
    else:
        require(phase in dict(protocol_plan()) or phase == 'failure_rollback', 'observation_phase')
        require(not result, 'observation_unexpected_rows')
    raw = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(len(raw) <= 800000, 'observation_bytes')
    return result


def command_register():
    return {'format': 'registered-fixture-program-v1',
        'commands': [{'id': 'auth.fixture.'+phase, 'sql_sha256': parent.sha(text.encode()),
                      'sql_commands': 1} for phase, text in protocol_plan()],
        'failure_command': {'id': 'auth.fixture.failure_rollback', 'sql_commands': 1,
                            'sql_sha256': parent.sha(b'ROLLBACK')},
        'normal_sql': NORMAL_COMMANDS, 'sql_limit_including_reserve': PROTOCOL_LIMIT,
        'original_unknown_physical_zero_sql': len(protocol_plan(physical_only=True)),
        'connections': 2, 'connection_implicit_sql_bound': None,
        'observer_suspend_reconnect': 'separate_B_dispatches',
        'read_wal_verified': False, 'full_chain_admission': False, 'hosted_admitted': False}


def validate_owned(value):
    require(type(value) is dict and set(value) == {'rows', 'xid'}
            and type(value['rows']) is list and len(value['rows']) <= 1000, 'inventory_bound')
    clean = []
    for row in value['rows']:
        require(type(row) is dict and row.get('insert_owned') is True
                and row.get('version_owned') is True, 'unowned_version')
        clean.append({k: v for k, v in row.items() if k not in ('insert_owned', 'version_owned')})
    return engine.validate_rows({'rows': clean, 'xid': value['xid']})


def _modules():
    return [sys.modules[__name__], durable, binding, engine, sql, fixture, parent, scope,
            admission_binding, sys.modules[scope.NativeRuntime.__module__],
            sys.modules[scope.parser.__module__], sys.modules[engine.parameters.__module__],
            sys.modules[parent.row_multiset.__module__]]


class Registration:
    def __init__(self):
        raise TypeError('actual_pre_body_context_only')


class Proof:
    def __init__(self):
        raise TypeError('actual_parent_closure_only')

    def unchanged(self):
        require(type(self) is Proof and self in _PROOFS, 'unissued_proof')
        state = _PROOFS[self]
        state.unchanged()
        require(state.journal.sealed and not state.journal.poisoned, 'unsealed_proof')
        state.journal._inventory()
        for name, ref in state.journal.entries.items():
            state.journal._read(name, ref)
        require(state.result['physical_zero'] and state.result['registry_absence_confirmed']
                and not state.result['registry_commit_unknown'], 'physical_zero_unproven')

    def owners(self):
        self.unchanged()
        state = _PROOFS[self]
        return {state.owner.role_map[r]: {'actor': v['id'], 'email': v['email'], 'session_ids': None}
                for r, v in state.handoff['owned'].items()}

    @property
    def owner(self):
        self.unchanged()
        return _PROOFS[self].owner

    @property
    def receipt(self):
        self.unchanged()
        return copy.deepcopy(_PROOFS[self].result)

    @property
    def ref(self):
        self.unchanged()
        state = _PROOFS[self]
        return {'path': (state.journal.folder/'result.json').relative_to(state.owner.gate.out).as_posix(),
                'sha256': state.journal.entries['result.json']['sha256']}

    @property
    def evidence_refs(self):
        self.unchanged()
        state = _PROOFS[self]
        refs = {}
        for name, sha in state.originals.items():
            path = binding.checked_path(pathlib.Path(state.owner.gate.out)/name)
            refs[name] = {'path': name, 'sha256': sha, 'bytes': path.stat().st_size}
        for name, entry in state.journal.entries.items():
            relative = (state.journal.folder/name).relative_to(state.owner.gate.out).as_posix()
            require(relative not in refs, 'evidence_alias')
            refs[relative] = {'path': relative, **entry}
        return [refs[name] for name in sorted(refs)]


class _State:
    def __init__(self, owner):
        self.owner = owner
        self.lifecycle, self.c = owner._case
        self.context = copy.deepcopy({k: self.c.fixture_context[k]
                                     for k in ('window', 'a', 'b', 'key', 'runs')})
        self.ids = copy.deepcopy(owner.ids)
        self.handoff = owner.producer.handoff()
        require(set(self.ids) == set(parent.ROLES) and self.ids == {
            r: v['id'] for r, v in self.handoff['owned'].items()}, 'known_owners')
        values = [*self.ids.values(), *self.context['runs'].values(),
                  *(self.context[k] for k in ('window', 'a', 'b', 'key'))]
        require(len(set(map(fresh, values))) == len(values)
                and set(self.context['runs']) == {'seed', 'activate', 'delete_window'}, 'scope_ids')
        require(owner.runtime is self.c.runtime and owner.runtime.environment == 'disposable_ci', 'runtime')
        self.source = binding.verify(owner.gate, _modules())
        self.journal = durable.Journal(pathlib.Path(owner.gate.out)/(PREFIX+'-private'),
                                       owner.gate.save, PREFIX+'-journal')
        self.originals = {}
        self.attempted = False
        self.result = None
        self.journal.save('registration.json', {'case_run': owner.binding['run_id'],
            'scope': self.context, 'actor_hashes': {r: parent.sha(v.encode()) for r, v in self.ids.items()},
            'source_binding': self.source, 'before_prefix_and_fixture_writes': True,
            'ownership_is_not_inferred_from_current_rows': True})

    def unchanged(self):
        self.owner._validate()
        require(not self.journal.poisoned, 'journal_poisoned')
        self.journal._inventory()
        for name, ref in self.journal.entries.items():
            self.journal._read(name, ref)
        require(self.owner._case == (self.lifecycle, self.c) and self.owner.ids == self.ids
                and {k: self.c.fixture_context[k] for k in self.context} == self.context,
                'original_scope_changed')
        require(self.owner.producer.handoff() == self.handoff, 'original_owners_changed')
        require(binding.verify(self.owner.gate, _modules()) == self.source, 'source_changed')
        for path, sha in self.originals.items():
            self.read_ref(path, sha)

    def read_ref(self, name, expected):
        if name.endswith('.json'):
            parent.read_record(self.owner.gate.out, name, expected)
            return
        root = binding.checked_path(self.owner.gate.out)
        path = binding.checked_path(root/name)
        require(path.is_relative_to(root) and path.stat().st_size <= 262144, 'raw_receipt_bound')
        raw = path.read_bytes()
        require(len(raw) <= 262144 and parent.sha(raw) == expected, 'raw_receipt_changed')

    def read(self, name, sha=None):
        value, observed = parent.read_record(self.owner.gate.out, name, sha)
        require(name not in self.originals or self.originals[name] == observed, 'receipt_changed')
        self.originals[name] = observed
        return value

    def inputs(self):
        self.unchanged()
        owner = self.owner
        require(owner._closing and owner._yielded and owner._seed_ref is not None, 'confirmed_seed')
        seed = owner._seed_ref
        path = (owner.records.folder/seed['name']).relative_to(owner.gate.out).as_posix()
        # Records.save wraps content with its own sequence/hash-chain metadata.
        value = self.read(path, seed['sha256'])
        content = value
        require(content.get('provenance_sha256') == parent.expected_registry(self.ids)['identities'][0]['provenance_sha']
                and content.get('actor_hashes') == {r: parent.sha(v.encode()) for r, v in self.ids.items()}
                and content.get('explicit_commands') == 9 and content.get('adopted_existing_rows') is False,
                'seed_receipt')
        body = owner._body_terminal()
        self.original_commit_unknown = any(not row.get('confirmed') and 'commit' in row.get('phase', '')
                                           for row in self.c.commands)
        self.journal.save('body-terminal.json', body)
        for ref in body['worker']['evidence_refs'] + body.get('evidence_refs', []):
            self.read_ref(ref['path'], ref['sha256'])
            require(ref['path'] not in self.originals or self.originals[ref['path']] == ref['sha256'],
                    'original_reference_changed')
            self.originals[ref['path']] = ref['sha256']
        recovery = getattr(self.c, 'workflow_recovery', None)
        if recovery is not None:
            require(recovery.get('complete') is True and recovery.get('worker_terminated') is True
                    and not recovery.get('secondary'), 'writer_close_unknown')
        actions, requests = [], []
        gate = owner._case_owners['gate']
        prefix = getattr(gate, 'evidence_prefix', '')
        # Optional records may legitimately be absent when a prefix failed
        # before first workflow dispatch. They never confer synthetic ownership.
        for stage, run_id in self.context['runs'].items():
            name = prefix+'lifecycle-'+stage+'-before.json'
            if not (pathlib.Path(owner.gate.out)/name).exists():
                continue
            record = self.read(name)
            fresh(record['action'])
            require(record['run'] == run_id and record['state']['coverage'] is True, 'lifecycle_intent')
            if stage == 'seed':
                ctx = {**self.context, 'trainer': self.ids['a_trainer'],
                       'member': self.ids['a_member'], 'b_member': self.ids['b_member']}
                require(record['contract'] == fixture.seed_writes(ctx), 'seed_write_contract')
            actions.append({'id': record['action'], 'run': run_id,
                            'before_sha': fixture.digest(record['state'])})
        seen_steps = set()
        for event in self.c.events:
            if event.get('phase') != 'contract':
                continue
            step = event['step']
            require(type(step) is int and 0 <= step <= 70 and step not in seen_steps, 'request_step')
            seen_steps.add(step)
            name = prefix+'integral-pair-%03d-contract.json' % step
            require(self.read(name) == event, 'request_original')
            requests.append(fresh(event['request_id']))
        require(len(set(requests)) == len(requests) and len(actions) <= 3 and len(requests) <= 71,
                'request_bound')
        self.journal.save('write-registry-refs.json', {'originals': self.originals,
            'lifecycle_actions': actions, 'request_ids': requests,
            'original_status_preserved': True})
        return actions, requests


def prepare(owner):
    from .runtime_registered_bootstrap import Context
    frame = inspect.currentframe().f_back
    require(type(owner) is Context and frame.f_code is Context.bind_case.__code__
            and frame.f_locals.get('self') is owner, 'prepare_caller')
    del frame
    require(owner._case is not None and owner._yielded and not owner._closing
            and getattr(owner, '_fixture_registration', None) is None, 'prepare_sequence')
    lifecycle, c = owner._case
    require(not lifecycle.worker_owned and not c.case_preservation.prefix_attempted
            and not c.commands and not c.events, 'before_body_required')
    state = _State(owner)
    registration = object.__new__(Registration)
    _REGISTRATIONS[registration] = state
    return registration


class _Dispatch:
    def __init__(self, state):
        self.state, self.events = state, []
        self.plan = dict(protocol_plan())
        self.seen = set()
        self.protocol = engine.Protocol(self.charge)
        self.contract = {}

    def charge(self, event):
        phase = event['phase']
        require(phase not in self.seen and len(self.events) < PROTOCOL_LIMIT, 'dispatch_bound')
        expected = 'ROLLBACK' if phase == 'failure_rollback' else self.plan.get(phase)
        require(expected is not None and event['sql_sha256'] == parent.sha(expected.encode()), 'dispatch_source')
        self.seen.add(phase)
        self.state.unchanged()
        self.state.journal.save('charge-%02d.json' % (len(self.events)+1), event)
        self.events.append(copy.deepcopy(event))

    def query(self, connection, phase, text, args=(), **_):
        def execute():
            rows = self.protocol.execute(connection, phase, text, args)
            event = copy.deepcopy(self.protocol.events[-1])
            exported = observation_rows(phase, rows, self.contract)
            self.state.journal.save('query-%02d-%s.json' % (event['ordinal'], phase), {
                'format':'c-query-observation-v1','component':'registered_fixture',
                'case_run':getattr(self.state.owner,'binding',{}).get('run_id'),
                'scope_sha256':engine.digest(self.state.context),
                'source_binding':getattr(self.state,'source',None),
                'migration_sources_sha256':engine.digest(self.contract.get('hashes',{})),
                'phase':phase,'protocol':event,'rows':exported,
                'rows_sha256':engine.digest(exported),'raw_rows_sha256':engine.digest(rows),
                'projection':'technical-fields-v1-unbound-function-config-digest',
                'query_io':{'observed':False,'reason':'not_instrumented_by_this_dispatch'}})
            return rows
        return self.state.owner._local_call('fixture.'+phase, 'native_sql', execute)


def _execute(state, actions, requests):
    """Only run issues a capability; testing this engine never creates one."""
    owner, context = state.owner, state.context
    expected = parent.expected_registry(state.ids)
    args = engine.parameters(context)
    meter = _Dispatch(state)
    result = {'status': 'NO_GO', 'physical_zero': False, 'registry_absence_confirmed': False,
        'registry_commit_confirmed': False, 'registry_commit_unknown': False,
        'original_claims_released': False, 'original_commit_reclassified': False,
        'full_chain_admission': False, 'hosted_admitted': False, 'global_auth_barrier': False,
        'returned_fixture_deletes': 0, 'delete_replayed': False, 'read_wal_verified': False}
    result.update(format='registered-fixture-physical-closure-v1',
        case_run=getattr(owner, 'binding', {}).get('run_id'),
        source_binding=getattr(state, 'source', None),
        scope_sha256=engine.digest(context), actor_hashes={r: parent.sha(v.encode()) for r,v in state.ids.items()},
        tables=list(sql.ORDER), physical_exclusion_held_for_delete_and_absence=False,
        future_privileged_connections_excluded=False)
    raw = None
    open_tx = commit_attempted = False
    primary = None
    def query(phase, text, values=()):
        return meter.query(raw, phase, text, values)
    def registry(phase):
        rows = query(phase, parent.REGISTRY, [list(state.ids.values())])
        require(len(rows) == 1 and set(rows[0]['value']) == set(expected), 'registry_shape')
        return rows[0]['value']
    def zero(phase):
        rows = query(phase, sql.INVENTORY, args)
        require(len(rows) == 1 and not engine.validate_rows(rows[0]['value']), 'physical_rows_remain')
    def connect(phase):
        connection = owner._local_call('fixture.'+phase, 'connection', owner.runtime.connect)
        require(connection.autocommit is True, 'autocommit')
        return connection
    def close(phase):
        owner._local_call('fixture.'+phase, 'connection_close', raw.close)
    try:
        raw = connect('connect')
        open_tx = True
        query('begin', 'BEGIN')
        query('lock', LOCK)
        contract = scope.source_contract(owner.gate)
        meter.contract = contract
        held = scope.collect(raw, meter, contract, before=False)
        require(held['cluster_id'] == owner.isolation['pg_system_identifier']
                and int(held['datid']) == owner.isolation['database_oid'], 'cluster_changed')
        rows = query('ownership_inventory', OWNED_INVENTORY,
                     [*args, json.dumps(actions), requests, list(state.ids.values())])
        require(len(rows) == 1, 'ownership_shape')
        owned = validate_owned(rows[0]['value'])
        require(not (getattr(state, 'original_commit_unknown', False) and owned),
                'unknown_original_commit_nonzero_no_replay')
        before = registry('registry_before')
        require(all(parent.same_rows(before[k], expected[k]) for k in expected), 'registry_not_original_seed')
        state.journal.save('predelete.json', {'rows': owned, 'scope': held, 'registry': before})
        physical_only = getattr(state, 'original_commit_unknown', False)
        result['original_commit_unknown'] = physical_only
        for table in (() if physical_only else sql.ORDER):
            wanted = [{k: v for k, v in r.items() if k != 'scope_ok'} for r in owned if r['table'] == table]
            actual = query('delete_'+table, sql.delete(table), [*args, json.dumps(wanted)])
            require(len(actual) == 1 and parent.same_rows(actual[0].get('value'), wanted), 'delete_multiset')
            result['returned_fixture_deletes'] += len(wanted)
            state.journal.save('delete-'+table+'.json', {'expected': wanted,
                'returned': actual[0]['value'], 'commit_confirmed': False})
        zero('fixture_zero')
        removed = query('delete_operator', parent.DELETE_OPERATOR, [state.ids['a_trainer']])
        require(parent.same_rows(removed, expected['operators']), 'operator_returning')
        state.journal.save('delete-operator.json', {'returned': removed, 'commit_confirmed': False})
        removed = query('delete_identities', parent.DELETE_IDENTITIES, [json.dumps(expected['identities'])])
        require(parent.same_rows(removed, expected['identities']), 'identity_returning')
        state.journal.save('delete-identities.json', {'returned': removed, 'commit_confirmed': False})
        require(not any(registry('registry_after').values()), 'registry_remaining')
        state.unchanged()
        state.journal.save('commit-intent.json', {'returned_fixture_deletes': result['returned_fixture_deletes']})
        commit_attempted = True
        query('commit', 'COMMIT')
        result['registry_commit_confirmed'] = True
        open_tx = False
        close('close')
        raw = None
        raw = connect('absence_connect')
        open_tx = True
        query('absence_begin', 'BEGIN')
        query('absence_lock', LOCK)
        current = scope.one(query('absence_session', scope.SESSION))
        require(all(current.get(k) is True for k in ('pg17', 'statement_bounded', 'lock_bounded',
            'no_prepared', 'tracked', 'fresh', 'origin', 'privileged'))
            and all(current.get(k) == held[k] for k in ('cluster_id', 'postmaster_start', 'datid')),
            'absence_session')
        zero('absence_fixture')
        require(not any(registry('absence_registry').values()), 'registry_absence')
        state.unchanged()
        state.journal.save('absence.json', {'physical_zero': True, 'registry_zero': True,
            'original_commit_reclassified': False})
        open_tx = False  # Lost rollback is not retried.
        query('absence_rollback', 'ROLLBACK')
        result.update(physical_zero=True, registry_absence_confirmed=True,
            physical_exclusion_held_for_delete_and_absence=True,
            status='SCOPED_PHYSICAL_CLOSURE_CONFIRMED_ORIGINAL_STATUS_UNCHANGED')
    except BaseException as error:
        primary = error
        result['registry_commit_unknown'] = commit_attempted and not result['registry_commit_confirmed']
    finally:
        if raw is not None:
            if open_tx and not result['registry_commit_unknown']:
                try: query('failure_rollback', 'ROLLBACK')
                except BaseException as error:
                    if primary is None: primary = error
                    else: primary.add_note('fixture_rollback_secondary:'+type(error).__name__)
            try: close('final_close')
            except BaseException as error:
                if primary is None: primary = error
                else: primary.add_note('fixture_close_secondary:'+type(error).__name__)
    if primary is not None:
        result.update(status='NO_GO', physical_zero=False, registry_absence_confirmed=False,
                      error_class=type(primary).__name__)
    result.update(protocol=copy.deepcopy(meter.protocol.events), sql_limit=PROTOCOL_LIMIT,
        emitted_attempts=len(meter.protocol.events), reserved_commands=PROTOCOL_LIMIT,
        unused_reserve_is_not_emitted=True)
    return result, primary


def run(owner):
    from .runtime_registered_bootstrap import Context
    frame = inspect.currentframe().f_back
    require(type(owner) is Context and frame.f_code is Context._finish.__code__
            and frame.f_locals.get('self') is owner, 'run_caller')
    del frame
    registration = getattr(owner, '_fixture_registration', None)
    require(type(registration) is Registration and registration in _REGISTRATIONS, 'registration_required')
    state = _REGISTRATIONS[registration]
    require(state.owner is owner and not state.attempted, 'replay')
    state.attempted = True
    actions, requests = state.inputs()
    error = None
    try:
        with owner.server.suspend():
            state.result, error = _execute(state, actions, requests)
            if error is not None:
                raise error
    except BaseException as caught:
        error = caught
        if state.result is None:
            state.result = {'status': 'NO_GO', 'physical_zero': False,
                            'registry_absence_confirmed': False, 'registry_commit_unknown': False}
        state.result.update(status='NO_GO', physical_zero=False, registry_absence_confirmed=False,
                            error_class=type(caught).__name__)
    try:
        state.journal.save('result.json', state.result)
        index = state.journal.seal()
        for name in [*index['chunks'], state.journal.prefix+'-index.json']:
            _, sha = parent.read_record(owner.gate.out, name)
            state.originals[name] = sha
    except BaseException as secondary:
        if error is None:
            raise
        error.add_note('fixture_final_evidence_secondary:'+type(secondary).__name__)
    if error is not None:
        raise error
    proof = object.__new__(Proof)
    _PROOFS[proof] = state
    proof.unchanged()
    return proof
