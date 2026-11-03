"""Prepared disposable-only DB terminality; main must wire BEFORE any producer.

API: tracked = TrackedRuntime.disposable(gate, durable_save); use tracked instead
of NativeRuntime for every fixture connection, then clear(), terminal(), and
physical_zero(context, original_receipt_ref). No Auth barrier is synthesized.
The wrapper is single-threaded like the current fixture runner. It cannot prove
coverage of clients created outside it, nor recover old unregistered sessions.
All extra commands are separately prepaid local diagnostics, not quota 2349.
"""
import copy
import json
import os
import threading
import uuid

from admission_binding import NEW_RUN, OLD_RUN
from fixture_cleanup_evidence import parameters
from fixture_cleanup_runtime import Blocked, Protocol, digest, validate_rows
from fixture_parent_closure import reference
import fixture_cleanup_runtime_sql as sql
from native_runtime import NativeRuntime

MAX_CONNECTIONS = 64
TERMINAL_LIMIT = 2
ZERO_LIMIT = 5
MAX_ZERO_CASES = 11

SESSION = """select pg_backend_pid() pid,backend_start::text backend_start,
 datid::text datid,pg_postmaster_start_time()::text postmaster_start,
 (select system_identifier::text from pg_control_system()) cluster_id,
 current_setting('application_name') application_name,
 current_setting('server_version_num')::int/10000=17 pg17,
 current_setting('statement_timeout') in ('5s','5000ms') bounded_statement,
 current_setting('lock_timeout') in ('1s','1000ms') bounded_lock,
 current_user='postgres' and current_database()='postgres' privileged,
 current_setting('track_activities')='on' tracked,
 current_setting('max_prepared_transactions')='0' no_prepared,
 current_setting('transaction_isolation')='read committed' fresh_snapshots,
 current_setting('transaction_read_only')='on' readonly
 from pg_stat_activity where pid=pg_backend_pid()"""
REGISTER = SESSION.replace("current_setting('application_name') application_name",
                          "set_config('application_name',$1,false) application_name")
ACTIVITY = """select pid,backend_start::text backend_start,application_name
 from pg_stat_activity a where exists(select 1 from
 jsonb_to_recordset($1::jsonb) e(pid int,backend_start text)
 where a.pid=e.pid and a.backend_start=e.backend_start::timestamptz)
 or left(application_name,length($2::text))=$2::text limit 65"""
IDENTITY = ('datid', 'postmaster_start', 'cluster_id')
CHECKS = ('pg17', 'bounded_statement', 'bounded_lock', 'privileged',
          'tracked', 'no_prepared', 'fresh_snapshots')


class _Meter:
    def __init__(self, save, prefix, limit):
        self.save, self.prefix, self.limit, self.used = save, prefix, limit, 0
        self.protocol = Protocol(self.charge)

    def charge(self, event):
        if self.used >= self.limit: raise Blocked('db_terminal_protocol_limit')
        self.used += 1  # Never refund a failed save or an uncertain send.
        self.save(self.prefix+'-charge-%03d.json' % self.used,
                  {**event, 'admitted_ordinal': self.used, 'protocol_limit': self.limit,
                   'budget_domain': 'additional_disposable_diagnostic_not_2349'})

    def query(self, connection, phase, text, args=(), *, reserve=0):
        if self.used >= self.limit - reserve: raise Blocked('db_terminal_protocol_limit')
        return self.protocol.execute(connection, phase, text, args)


class _Handle:
    def __init__(self, owner, raw):
        self.__owner, self.__raw, self.__closed = owner, raw, False

    def execute(self, text, args=None):
        self.__owner._producer_open()
        if self.__closed: raise Blocked('db_terminal_handle_closed')
        return self.__raw.execute(text, args)

    def close(self):
        self.__owner._thread()
        if not self.__closed:
            self.__closed = True
            self.__raw.close()


class TrackedRuntime:
    environment = 'disposable_ci'

    @classmethod
    def disposable(cls, gate, save):
        if (os.environ.get('GITHUB_ACTIONS') != 'true'
                or os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
                or os.environ.get('GITHUB_REF') != 'refs/heads/main'
                or getattr(gate, 'container', None) != 'supabase_db_fmz-db41-ci'):
            raise Blocked('db_terminal_disposable_required')
        return cls(gate, save)

    def __init__(self, gate, save):
        self.__gate, self.__save = gate, save
        self.__thread = threading.get_ident()
        self.__native = None
        self.__sealed = self.__poisoned = self.__terminal_attempted = False
        self.__terminal = None
        self.__sessions, self.__handles, self.__zero_cases = [], [], set()
        self.__server = None
        self.__tag = 'fmz-fixture-' + uuid.uuid4().hex + '-'
        self.__prefix = 'fixture-db-' + self.__tag
        self.__connects = 0
        self.__registration = _Meter(save, self.__prefix+'register', MAX_CONNECTIONS)
        save(self.__prefix+'intent.json', {'preparation_run': NEW_RUN, 'session_prefix': self.__tag,
             'maximum_connections': MAX_CONNECTIONS, 'terminal_protocol_limit': TERMINAL_LIMIT,
             'zero_protocol_limit_per_case': ZERO_LIMIT, 'maximum_zero_cases': MAX_ZERO_CASES,
             'scope': 'only_connections_minted_by_this_factory', 'full_cleanup_proven': False})
        self.__native = NativeRuntime.disposable(gate)
        if self.__native.environment != 'disposable_ci': raise Blocked('db_terminal_runtime')

    def _thread(self):
        if threading.get_ident() != self.__thread: raise Blocked('db_terminal_nonowner_thread')

    def _producer_open(self):
        self._thread()
        if self.__sealed or self.__poisoned: raise Blocked('db_terminal_factory_closed')

    def component_binding(self, gate):
        """Bind an injected factory to its original Gate before component dispatch."""
        self._producer_open()
        if gate is not self.__gate: raise Blocked('db_terminal_component_gate_changed')
        return {'session_prefix': self.__tag,
                'registration_commands_before_component': self.__registration.used}

    def _session(self, rows, raw, *, readonly):
        expected = {'pid', 'backend_start', 'application_name', 'readonly', *IDENTITY, *CHECKS}
        if len(rows) != 1 or set(rows[0]) != expected: raise Blocked('db_terminal_identity_shape')
        value = rows[0]
        if (type(value['pid']) is not int or value['pid'] <= 0 or value['pid'] != raw.info.backend_pid
                or any(value[k] is not True for k in CHECKS) or value['readonly'] is not readonly
                or any(not isinstance(value[k], str) or not value[k] for k in (*IDENTITY, 'backend_start'))):
            raise Blocked('db_terminal_identity_or_limits')
        server = {k: value[k] for k in IDENTITY}
        if self.__server is None: self.__server = server
        elif server != self.__server: raise Blocked('db_terminal_server_changed')
        return value

    def connect(self):
        self._producer_open()
        if self.__connects >= MAX_CONNECTIONS: raise Blocked('db_terminal_connection_limit')
        self.__connects += 1
        raw = None
        try:
            raw = self.__native.connect()
            if raw.autocommit is not True: raise Blocked('db_terminal_autocommit_required')
            tag = self.__tag + str(self.__connects)
            value = self._session(self.__registration.query(raw, 'register', REGISTER, [tag]), raw, readonly=False)
            if value['application_name'] != tag: raise Blocked('db_terminal_session_tag')
            self.__save(self.__prefix+'session-%03d.json' % self.__connects, value)
            self.__sessions.append(copy.deepcopy(value))
            handle = _Handle(self, raw)
            self.__handles.append(handle)
            return handle
        except BaseException:
            self.__poisoned = True
            if raw is not None:
                try: raw.close()
                except BaseException: pass
            raise

    def clear(self):
        """Close the local mint path and actual handles; NOT server terminality."""
        self._thread()
        if self.__sealed: return
        self.__sealed = True
        errors = []
        for handle in self.__handles:
            try: handle.close()
            except BaseException as error: errors.append(type(error).__name__)
        try: self.__native.clear()
        except BaseException as error:
            self.__poisoned = True
            errors.append(type(error).__name__)
        try:
            self.__save(self.__prefix+'sealed.json', {'factory_closed': True,
                 'registered_sessions_sha256': digest(self.__sessions), 'close_error_classes': errors,
                 'db_terminality_proven': False})
        except BaseException:
            self.__poisoned = True
            raise

    def _activity(self, meter, raw, *, reserve=0):
        owned = [{k: s[k] for k in ('pid', 'backend_start')} for s in self.__sessions]
        rows = meter.query(raw, 'backend_absence', ACTIVITY, [json.dumps(owned), self.__tag], reserve=reserve)
        if rows: raise Blocked('db_terminal_backend_still_present')

    def terminal(self):
        self._thread()
        if self.__terminal_attempted: raise Blocked('db_terminal_duplicate_observation')
        self.__terminal_attempted = True
        if not self.__sealed or self.__poisoned or not self.__sessions:
            raise Blocked('db_terminal_complete_registration_and_seal_required')
        meter = _Meter(self.__save, self.__prefix+'terminal', TERMINAL_LIMIT)
        observer = NativeRuntime.disposable(self.__gate)
        raw = None
        primary = None
        try:
            raw = observer.connect()
            if raw.autocommit is not True: raise Blocked('db_terminal_autocommit_required')
            self._session(meter.query(raw, 'observer_identity', SESSION), raw, readonly=False)
            self._activity(meter, raw)
        except BaseException as error:
            primary = error
            raise
        finally:
            terminal_error = None
            for name, action in (('close', lambda: raw.close() if raw is not None else None),
                                 ('clear', observer.clear)):
                try: action()
                except BaseException as error:
                    earlier = primary if primary is not None else terminal_error
                    if earlier is not None: earlier.add_note('db-terminal '+name+' failed: '+type(error).__name__)
                    else: terminal_error = error
            if primary is None and terminal_error is not None: raise terminal_error
        value = {'status': 'NO_GO', 'classification': 'TRACKED_DB_BACKENDS_TERMINAL',
                 'preparation_run': NEW_RUN, 'registered_sessions_sha256': digest(self.__sessions),
                 'registered_sessions': len(self.__sessions), 'db_terminality_proven': True,
                 'auth_mint_barrier_proven': False, 'external_producers_covered': False,
                 'full_cleanup_proven': False, 'protocol': copy.deepcopy(meter.protocol.events),
                 'registration_commands': self.__registration.used, 'terminal_commands': meter.used}
        self.__save(self.__prefix+'terminal.json', value)
        self.__terminal = copy.deepcopy(value)
        return value

    def physical_zero(self, context, original_ref):
        """Fresh physical absence only; never replay DELETE/COMMIT or release claims."""
        self._thread()
        if self.__terminal is None: raise Blocked('db_terminal_observation_required')
        args = parameters(context)
        if any(v in (OLD_RUN, NEW_RUN) for v in (args[0], *args[1])):
            raise Blocked('db_terminal_fresh_case_required')
        if args[0] in self.__zero_cases or len(self.__zero_cases) >= MAX_ZERO_CASES:
            raise Blocked('db_terminal_zero_case_limit_or_duplicate')
        self.__zero_cases.add(args[0])
        original = reference(self.__gate.out, original_ref)
        expected = {'preparation_run': NEW_RUN, 'case': args[0], 'scope_sha256': digest(args),
                    'component_only': True, 'status': 'NO_GO', 'commit_unknown': True,
                    'commit_confirmed': False, 'cleanup_complete': False, 'deletion_proven': False}
        if any(original.get(k) != v for k, v in expected.items()):
            raise Blocked('db_terminal_original_unknown_commit_binding')
        prefix = self.__prefix+'zero-'+args[0]
        self.__save(prefix+'-intent.json', {'original_ref': original_ref,
             'terminal_sha256': digest(self.__terminal), 'context': context, 'protocol_limit': ZERO_LIMIT})
        meter = _Meter(self.__save, prefix, ZERO_LIMIT)
        observer = NativeRuntime.disposable(self.__gate)
        raw = None
        began = False
        primary = None
        try:
            raw = observer.connect()
            if raw.autocommit is not True: raise Blocked('db_terminal_autocommit_required')
            began = True
            meter.query(raw, 'zero_begin', 'BEGIN TRANSACTION READ ONLY', reserve=1)
            self._session(meter.query(raw, 'zero_session', SESSION, reserve=1), raw, readonly=True)
            self._activity(meter, raw, reserve=1)
            rows = meter.query(raw, 'zero_inventory', sql.INVENTORY, args, reserve=1)
            if len(rows) != 1 or validate_rows(rows[0]['value']):
                raise Blocked('db_terminal_scoped_rows_remain_or_invalid')
        except BaseException as error:
            primary = error
            raise
        finally:
            terminal_error = None
            for name, action in (
                    ('rollback', lambda: meter.query(raw, 'zero_rollback', 'ROLLBACK') if began else None),
                    ('close', lambda: raw.close() if raw is not None else None),
                    ('clear', observer.clear)):
                try: action()
                except BaseException as error:
                    earlier = primary if primary is not None else terminal_error
                    if earlier is not None: earlier.add_note('physical-zero '+name+' failed: '+type(error).__name__)
                    else: terminal_error = error
            if primary is None and terminal_error is not None: raise terminal_error
        # Reread the immutable original after observation; never overwrite it.
        reference(self.__gate.out, original_ref)
        value = {'status': 'NO_GO', 'classification': 'physical_zero_original_commit_unknown',
                 'preparation_run': NEW_RUN, 'case': args[0], 'scope_sha256': digest(args),
                 'original_ref': original_ref, 'original_commit_unknown': True,
                 'physical_zero': True, 'delete_replayed': False, 'deletion_proven': False,
                 'original_claims_released': False, 'full_cleanup_proven': False,
                 'external_producers_covered': False, 'registry_cleanup_admitted': False,
                 'terminal_sha256': digest(self.__terminal), 'protocol_limit': ZERO_LIMIT,
                 'admitted_attempts': meter.used, 'protocol': copy.deepcopy(meter.protocol.events)}
        self.__save(prefix+'-result.json', value)
        return value
