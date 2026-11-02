"""Actual PG17 cleanup cases on an existing disposable clean47 Gate.

run(gate) requires gate.fixture_cleanup_ids (three already registered synthetic
identities). It never creates Auth accounts, changes config or activates a quota.
All fixture UUIDs are fresh; failure-case rows remain in the disposable database.
"""
import copy
from collections import Counter
import hashlib
import pathlib
import uuid

from admission_binding import NEW_RUN
from fixture_cleanup_runtime import Blocked, Cleanup, Protocol, digest
from native_runtime import NativeRuntime
import fixture_cleanup_runtime_sql as sql

HERE = pathlib.Path(__file__).resolve().parent
FILES = ('fixture_cleanup_runtime.py', 'fixture_cleanup_runtime_sql.py',
         'fixture_cleanup_runtime_ci.py', 'fixture_cleanup_runtime_test.py',
         'fixture_cleanup_evidence.py', 'admission_binding.py', 'sql_protocol.py', 'native_runtime.py')
ROLES = ('a_member', 'a_trainer', 'b_member')
REGISTRY = """select role,user_id::text id from fmz6e11_private.identities i where enabled
 and user_id=any($1::uuid[]) and (role<>'a_trainer' or exists(
 select 1 from fmz6e11_private.operators o where o.user_id=i.user_id and o.enabled))"""
PROTECTED_TABLES = (
        'fmz6e11_private.config', 'fmz6e11_private.identities', 'fmz6e11_private.operators',
        'fmz6e11_audit_private.runs', 'fmz6e11_audit_private.actions', 'fmz6e11_audit_private.writes',
        'fmz6e11_audit_private.actors', 'fmz6e11_audit_private.bindings', 'fmz6e11_audit_private.relations',
        'fmz6e11_request_private.receipts', 'fmz6e11_controller_private.runs',
        'fmz6e11_controller_private.steps', 'fmz6e11_controller_private.evidence',
        'auth.users', 'auth.sessions', 'public.profiles')
SCOPED = {'auth.users': 'id=any($1::uuid[])', 'auth.sessions': 'user_id=any($1::uuid[])',
          'public.profiles': 'id=any($1::uuid[])'}
# Stream at most 1001 hash rows; no full-table aggregate/sort or raw Auth payload.
PROTECTED = 'select * from (' + ' union all '.join(
    "select '" + name + "' table_name," + sql.sha('to_jsonb(t)') +
    ' row_sha from ' + name + ' t' + (' where ' + SCOPED[name] if name in SCOPED else '')
    for name in PROTECTED_TABLES) + ') bounded_metadata limit 1001'


def protected_witness(rows):
    if len(rows) > 1000:
        raise Blocked('cleanup_protected_witness_overflow')
    for r in rows:
        if set(r) != {'table_name', 'row_sha'} or r['table_name'] not in PROTECTED_TABLES:
            raise Blocked('cleanup_protected_witness_shape')
        if not isinstance(r['row_sha'], str) or len(r['row_sha']) != 64:
            raise Blocked('cleanup_protected_witness_hash')
    # Keep multiplicity: an unordered set comparison would silently lose duplicates.
    return Counter((r['table_name'], r['row_sha']) for r in rows)


def inserts(context, ids):
    w, a, b = (context[k] for k in ('window', 'a', 'b'))
    m, t, bm = (ids[k] for k in ROLES)
    # Existing FK constraints and all existing triggers remain enabled.
    return [
        ('windows', "insert into fmz6e11_private.windows(id,operator_id,package_version,scenario,starts_at,ends_at) values($1::uuid,$2::uuid,'6e11@1','kg',clock_timestamp(),clock_timestamp()+interval '10 minutes')", [w, t]),
        ('participants', "insert into fmz6e11_private.participants(window_id,user_id,role) values($1::uuid,$2::uuid,'a_member'),($1::uuid,$3::uuid,'a_trainer'),($1::uuid,$4::uuid,'b_member')", [w, m, t, bm]),
        ('workspaces', "insert into fmz6e11_private.workspaces(id,window_id,route,member_id,trainer_id,observations) values($1::uuid,$3::uuid,'A',$4::uuid,$5::uuid,'[]'),($2::uuid,$3::uuid,'B',$6::uuid,null,'[]')", [a, b, w, m, t, bm]),
        ('source_versions', "insert into fmz6e11_private.source_versions(workspace_id,version,source_id,trainer_id,body,hash,valid_from,valid_until) values($1::uuid,1,$2::uuid,$3::uuid,'{}',repeat('0',64),clock_timestamp(),clock_timestamp()+interval '5 minutes')", [a, str(uuid.uuid4()), t]),
        ('source_heads', "insert into fmz6e11_private.source_heads(workspace_id,version,status) values($1::uuid,1,'active')", [a]),
        ('plans', "insert into fmz6e11_private.plans(workspace_id,version,content,hash) values($1::uuid,1,'{}',repeat('0',64))", [a]),
        ('proposals', "insert into fmz6e11_private.proposals(workspace_id,version,source_version,source_hash,base_version,base_hash,reflection,status) values($1::uuid,1,1,repeat('0',64),1,repeat('0',64),'{}','member_pending')", [a]),
        ('b_states', "insert into fmz6e11_private.b_states(workspace_id) values($1::uuid)", [b]),
        ('b_versions', "insert into fmz6e11_private.b_versions(workspace_id,version,content,source_version,source_hash) values($1::uuid,1,'{}',1,repeat('0',64))", [b]),
        ('inbox_state', "insert into fmz6e11_private.inbox_state(workspace_id,actor,proposal_version,disposition) values($1::uuid,$2::uuid,1,'viewed')", [a, m]),
        ('audit', "insert into fmz6e11_private.audit(window_id,actor,action,receipt) values($1::uuid,$2::uuid,'cleanup-component','{}')", [w, t]),
        ('requests', "insert into fmz6e11_private.requests(actor,key,payload_hash,window_id,receipt) values($1::uuid,$2::uuid,repeat('0',64),$3::uuid,'{}')", [t, str(uuid.uuid4()), w]),
        ('events', "insert into fmz6e11_private.events(window_id,workspace_id,actor,actor_role,action,outcome,request_key,request_hash) values($1::uuid,$2::uuid,$3::uuid,'a_trainer','cleanup-component','committed',$4::uuid,repeat('0',64))", [w, a, t, str(uuid.uuid4())]),
    ]


class ResponseFault:
    """Drop one response AFTER the real server command, never replace SQL execution."""
    environment = 'disposable_ci'
    def __init__(self, runtime, needle):
        self.runtime, self.needle, self.injected = runtime, needle, False
    def connect(self):
        connection = self.runtime.connect()
        owner = self
        class Connection:
            def execute(self, text, args=None):
                cursor = connection.execute(text, args)
                if not owner.injected and owner.needle in text:
                    owner.injected = True
                    raise ConnectionError('local_response_dropped_after_server_execution')
                return cursor
            def close(self): connection.close()
        return Connection()


def run(gate):
    result = {'status': 'BLOCKED', 'component': 'fixture_cleanup', 'preparation_run': NEW_RUN,
              'hosted_admitted': False, 'full_endchain_pass': False,
              'global_2349_proven': False, 'wal_classification': 'NOT_MEASURED',
              'cases': [], 'local_diagnostic_dispatches': [], 'fixture_mutation_attempted': False}
    runtime = None
    def finish():
        result['local_diagnostic_sql_count'] = len(result['local_diagnostic_dispatches'])
        result['planned_cleanup_protocol_count'] = len(sql.plan()['normal'])
        result['planned_capture_per_writer_transaction'] = 1
        result['planned_prepare_protocol_count'] = 4
        result['counts_are_protocol_only_not_nested_sql_or_io'] = True
        result['local_setup_sql_count'] = len(result.get('local_setup_protocol', []))
        result['local_component_sql_count'] = result['local_diagnostic_sql_count'] - result['local_setup_sql_count']
        gate.save('fixture-cleanup-component-detail.json', result)
        flat = {k: result[k] for k in ('status', 'component', 'preparation_run', 'hosted_admitted',
                'full_endchain_pass', 'global_2349_proven', 'wal_classification',
                'fixture_mutation_attempted', 'local_diagnostic_sql_count',
                'planned_cleanup_protocol_count', 'planned_capture_per_writer_transaction',
                'planned_prepare_protocol_count', 'counts_are_protocol_only_not_nested_sql_or_io',
                'local_setup_sql_count', 'local_component_sql_count')}
        flat.update(cases_executed=len(result['cases']),
                    cases_expectation_pass=sum(c['expectation_pass'] for c in result['cases']),
                    protected_and_history_unchanged=result.get('protected_and_history_unchanged', False),
                    retained_fault_fixtures=result.get('fault_case_fixtures_retained', False),
                    detail_receipt='fixture-cleanup-component-detail.json',
                    reason=result.get('reason'), error_class=result.get('error_class'))
        gate.save('fixture-cleanup-component.json', flat)
        return flat
    ids = getattr(gate, 'fixture_cleanup_ids', None)
    if not isinstance(ids, dict) or set(ids) != set(ROLES):
        result['reason'] = 'cleanup_main_registered_fixture_ids_required'
        return finish()
    try:
        if len(set(ids.values())) != 3 or any(str(uuid.UUID(v)) != v for v in ids.values()):
            raise ValueError('ids')
        sources = pathlib.Path(gate.sources) / '_offline/phase6e11/endchain_v1'
        result['source_hashes'] = {}
        for name in FILES:
            data = (sources / name).read_bytes()
            if data != (HERE / name).read_bytes():
                raise Blocked('cleanup_loaded_source_differs_from_candidate')
            result['source_hashes'][name] = hashlib.sha256(data).hexdigest()
    except (ValueError, TypeError, OSError, Blocked):
        result['reason'] = 'cleanup_identity_or_source_prerequisite'
        return finish()

    def charge(event):
        entry = {**event,
            'diagnostic_ordinal': len(result['local_diagnostic_dispatches']) + 1,
            'budget_domain': 'disposable_local_diagnostic_not_2349'}
        gate.save('fixture-cleanup-charge-%04d.json' % entry['diagnostic_ordinal'], entry)
        result['local_diagnostic_dispatches'].append(entry)
    setup = Protocol(charge)
    def execute(connection, label, text, args=()):
        return setup.execute(connection, 'local_setup_' + label, text, args)
    try:
        runtime = NativeRuntime.disposable(gate)
        connection = runtime.connect()
        try:
            check = execute(connection, 'prerequisite', sql.CHECK)[0]
            if not all(check[k] is True for k in check if k != 'readonly'):
                raise Blocked('cleanup_pg17_limits_required')
            registered = execute(connection, 'identity_registry', REGISTRY, [list(ids.values())])
            if {r['role']: r['id'] for r in registered} != ids:
                raise Blocked('cleanup_registered_local_identities_required')
            protected = protected_witness(execute(connection, 'protected_before', PROTECTED, [list(ids.values())]))
        finally:
            connection.close()
        # Each failed case is retained; it is never recycled into a successful run.
        for name in ('full', 'partial', 'parent_only', 'dependent_without_workspace', 'zero', 'lost_writer_commit',
                     'missing_barrier', 'foreign_row', 'lost_commit', 'interrupted_delete', 'lock_timeout'):
            context = {k: str(uuid.uuid4()) for k in ('window', 'a', 'b')}
            cleanup = Cleanup(runtime, context, gate.save, charge)
            cleanup.prepare()
            commands = inserts(context, ids)
            selected = commands if name not in ('parent_only', 'dependent_without_workspace', 'partial', 'zero') else (
                commands[:1] if name == 'parent_only' else
                [commands[0], commands[-1]] if name == 'dependent_without_workspace' else
                commands[:3] if name == 'partial' else [])
            if selected:
                writer = runtime.connect()
                try:
                    execute(writer, name + '_begin', 'BEGIN')
                    for table, text, args in selected:
                        result['fixture_mutation_attempted'] = True
                        execute(writer, name + '_insert_' + table, text, args)
                    if name != 'foreign_row': cleanup.capture(writer)
                    if name == 'lost_writer_commit':
                        # The same real writer connection executes COMMIT once;
                        # only delivery of its response is fault-injected.
                        class LostWriter:
                            def execute(self, text, args=None):
                                writer.execute(text, args)
                                raise ConnectionError('local_lost_writer_commit')
                        try: execute(LostWriter(), name + '_commit', 'COMMIT')
                        except ConnectionError: pass
                    else:
                        execute(writer, name + '_commit', 'COMMIT')
                finally:
                    writer.close()
            original = copy.deepcopy(cleanup._rows)
            if name in ('lost_commit', 'interrupted_delete'):
                cleanup.runtime = ResponseFault(runtime, 'COMMIT' if name == 'lost_commit' else 'delete from fmz6e11_private.events')
            locker = None
            try:
                if name == 'lock_timeout':
                    locker = runtime.connect()
                    execute(locker, 'fault_locker_begin', 'BEGIN')
                    execute(locker, 'fault_locker_lock', 'LOCK TABLE fmz6e11_private.windows IN ROW EXCLUSIVE MODE')
                try:
                    receipt = cleanup.run(worker_joined=name != 'missing_barrier', writers_closed=True, mint_barrier=True)
                except Blocked as error:
                    if name != 'missing_barrier': raise
                    receipt = {'status': 'BLOCKED', 'reason': str(error), 'deletion_proven': False}
                if name == 'missing_barrier':
                    if receipt['status'] != 'BLOCKED' or receipt['reason'] != 'cleanup_writer_barrier_required':
                        raise Blocked('cleanup_expected_barrier_rejection')
                elif name in ('foreign_row', 'lost_commit', 'interrupted_delete', 'lock_timeout'):
                    if receipt['status'] != 'NO_GO': raise Blocked('cleanup_expected_fault_no_go')
                    if name == 'foreign_row' and receipt.get('reason') != 'cleanup_unowned_or_changed_row':
                        raise Blocked('cleanup_foreign_rejection_reason')
                    if name == 'lost_commit' and not (receipt['commit_unknown'] and receipt['absence_confirmed']):
                        raise Blocked('cleanup_lost_commit_witness')
                    if name in ('interrupted_delete', 'lock_timeout') and not receipt.get('rollback_confirmed'):
                        raise Blocked('cleanup_rollback_witness')
                    if name == 'interrupted_delete' and receipt.get('remaining_counts') != receipt['predelete_counts']:
                        raise Blocked('cleanup_partial_rollback_rows_changed')
                    if name == 'lock_timeout' and any(e['phase'].startswith('delete_') for e in cleanup.protocol.events):
                        raise Blocked('cleanup_lock_timeout_dispatched_delete')
                    if name == 'lock_timeout' and receipt.get('error_class') != 'LockNotAvailable':
                        raise Blocked('cleanup_expected_actual_lock_timeout')
                elif receipt['status'] != 'COMPONENT_PASS':
                    raise Blocked('cleanup_success_case_failed')
                if name == 'full':
                    if set(r['table'] for r in original) != set(sql.ORDER) or not receipt['deletion_proven']:
                        raise Blocked('cleanup_full_coverage')
                    used = len(cleanup.protocol.events)
                    try: cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
                    except Blocked: pass
                    else: raise Blocked('cleanup_duplicate_accepted')
                    if used != len(cleanup.protocol.events): raise Blocked('cleanup_duplicate_dispatched')
                if name == 'zero' and receipt['deletion_proven']:
                    raise Blocked('cleanup_zero_fabricated_delete')
                if name in ('full', 'partial', 'parent_only', 'dependent_without_workspace', 'zero', 'lost_writer_commit'):
                    expected = {'full': 16, 'partial': 6, 'parent_only': 1,
                                'dependent_without_workspace': 2, 'zero': 0, 'lost_writer_commit': 16}[name]
                    if receipt['delete_count'] != expected: raise Blocked('cleanup_expected_delete_count')
                result['cases'].append({'case': name, 'fixture_case': cleanup.case,
                                        'original_writer_commit_unknown': name == 'lost_writer_commit',
                                        'expectation_pass': True, 'receipt': receipt})
            finally:
                if locker is not None:
                    try: execute(locker, 'fault_locker_rollback', 'ROLLBACK')
                    finally: locker.close()
        connection = runtime.connect()
        try:
            after = protected_witness(execute(connection, 'protected_after', PROTECTED, [list(ids.values())]))
        finally:
            connection.close()
        if after != protected: raise Blocked('cleanup_protected_or_history_changed')
        result.update(status='COMPONENT_PASS', protected_and_history_unchanged=True,
                      protected_witness_rows=sum(protected.values()),
                      protected_witness_sha256=digest(sorted((list(k), n) for k, n in protected.items())),
                      fault_case_fixtures_retained=True, no_mutation_retry=True,
                      registry_rows_inserted=0, registry_rows_updated=0, registry_restore_required=False)
    except BaseException as error:
        result['status'] = 'NO_GO' if result['fixture_mutation_attempted'] else 'BLOCKED'
        result['reason'] = str(error) if isinstance(error, Blocked) else 'cleanup_component_execution_error'
        result['error_class'] = type(error).__name__
    finally:
        result['local_setup_protocol'] = setup.events
        if runtime is not None: runtime.clear()
    return finish()
