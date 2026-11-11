"""Disposable case lifecycle: three streams, history47/48, strict measured gates."""
import copy
import hashlib
import pathlib
import sys

import lifecycle_gates as gates
from integral_ci import bind_parameters
from integral_io import QueryIO
from . import runtime_catalog, runtime_history

LABELS = ('before', 'after_migration', 'before_cleanup', 'after_cleanup', 'final_post')
GATE_COMMANDS = {'before': 20, 'after_migration': 20, 'pre': 11, 'post': 9}
_FRAGMENT = 'final_catalog as (' + gates.CATALOG + ')'
if gates.FINAL.count(_FRAGMENT) != 1:
    raise ValueError('case_final_catalog_source')
FINAL = gates.FINAL.replace(_FRAGMENT,
                            'final_catalog as (' + runtime_catalog.CATALOG_AFTER + ')')


def require(value, reason):
    if not value:
        raise ValueError('case_lifecycle_' + reason)


class CasePreservation:
    def __init__(self, composition, *, history, stream, catalog):
        self.composition = composition
        self.history, self.stream, self.catalog = history, stream, catalog
        require(catalog.history is history and stream.version == history.local_version,
                'owner_binding')
        require(stream.run_id == composition.quota['binding']['run_id']
                and stream.manifest_sha == composition.quota['binding']['binding_sha']
                and catalog.artifact['manifest'] == composition.quota['manifest'],
                'case_binding')
        self.gate = self.lifecycle = None
        self.ids = None
        self.prefix_attempted = False
        self.attempts = []

    def prepare_prefix(self, gate, lifecycle, prefix):
        """One 4-command preflight, stream/20, quota72, gate20, pre-Auth36."""
        c = self.composition
        require(not self.prefix_attempted and not self.attempts, 'prefix_retry')
        require(lifecycle.composition is c and lifecycle.gate is gate
                and not lifecycle.installed and not lifecycle.worker_owned
                and not lifecycle.failed and not lifecycle.removed, 'lifecycle_binding')
        require(getattr(gate, 'prefix', None) is prefix and prefix.composition is c
                and prefix.gate is gate._gate and not prefix.attempts
                and gate.cli_protocol is prefix.cli_protocol
                and not gate.cli_protocol, 'prefix_binding')
        require(c.case_history is self.history and c.case_preservation is self
                and not c.preflight_admitted and c.preservation_baseline is None
                and c.gate_baseline is None and not c.meter.stopped and not c.meter.closed,
                'composition_binding')
        require(pathlib.Path(c.quota['root']).resolve() == gate.sources.resolve()
                and lifecycle.run_id == c.quota['binding']['run_id']
                and prefix.version == self.history.local_version, 'source_binding')
        require(c.native_runtime(gate).environment == 'disposable_ci', 'environment')
        self.prefix_attempted = True
        self.gate, self.lifecycle, self.ids = gate, lifecycle, dict(lifecycle.ids)
        c.fixture_context['temporary_schemas'] = [
            lifecycle.guard.scope(lifecycle.run_id, self.ids),
            lifecycle.audit.scope(lifecycle.run_id, self.ids)]
        c.fixture_context['migration_boundary'] = False
        # Reuse the existing scope validation before any prefix dispatch.
        gates.final_parameters(self.ids, c.fixture_context, 'pre')
        try:
            value = runtime_history.preflight(c.native_runtime(gate), c.meter, self.history, gate.save)
            c.admit_preflight(value)
            self.run(gate, self.ids, 'before')
            prefix.run_pending()
            self.run(gate, self.ids, 'after_migration')
            c.pre_auth_dry_run(gate)
        except BaseException as error:
            self._abort(error)
            raise

    def _abort(self, primary):
        try:
            self.composition.abort('case_preservation_incomplete')
        except BaseException as secondary:
            primary.add_note('case_lifecycle_meter_stop_secondary:' + type(secondary).__name__)

    @staticmethod
    def _secondary(primary, stage, error):
        if primary is None:
            return error
        primary.add_note('case_lifecycle_' + stage + '_secondary:' + type(error).__name__)
        return primary

    @staticmethod
    def _io_failure(gate, name, evidence):
        primary = sys.exception()
        try:
            gate.save(name, evidence)
        except BaseException as error:
            if primary is None:
                raise
            primary.add_note('case_lifecycle_io_receipt_secondary:' + type(error).__name__)

    @staticmethod
    def _zero_io(io):
        require(io['last_pair']['own_wal_bytes'] == 0 and io['closing_wal_bytes'] == 0
                and io['last_pair']['own_temp_written'] == 0 and io['closing_temp_written'] == 0,
                'read_io_nonzero')

    def _monitor(self, gate, phase, query):
        return QueryIO(lambda channel, name, text, values=(): query(phase+'_'+name, text, values),
            on_failure=lambda evidence: self._io_failure(
                gate, 'integral-'+phase+'-io-failure.json', evidence))

    @staticmethod
    def _readonly(phase, query):
        rows = query(phase+'_readonly',
                     "select current_setting('transaction_read_only')='on' readonly")
        require(len(rows) == 1 and rows[0].get('readonly') is True, 'not_readonly')

    def _gate(self, gate, ids, label, query):
        c = self.composition
        phase = 'gates_' + label
        query(phase+'_begin', 'BEGIN TRANSACTION READ ONLY')
        query(phase+'_timeout', "SET LOCAL statement_timeout='5s'")
        self._readonly(phase, query)
        monitor = self._monitor(gate, phase, query)
        monitor.start()
        def checked(name, text, args=()):
            qid = monitor.bind(text, args, read_only=True)
            rows = query(phase+'_'+name, text, args)
            monitor.executed(qid)
            return rows
        context = c.fixture_context
        access_rows = checked('access', gates.ACCESS, [list(ids.values())])
        require(len(access_rows) == 1, 'access_rows')
        access = access_rows[0]
        gates.check_access(access)
        raw = checked('migrations', runtime_history.MIGRATIONS, [self.history.inspect_versions])
        appended = label == 'after_migration'
        attested = self.history.attest(raw, appended=appended)
        migrations = attested['migrations']
        catalog_rows = checked('catalog', runtime_catalog.CATALOG_AFTER if appended
                               else runtime_catalog.CATALOG_BEFORE, [context['temporary_schemas']])
        require(len(catalog_rows) == 1, 'catalog_rows')
        state = {'migrations': migrations, 'catalog': catalog_rows[0]['value']}
        catalog_receipt = self.catalog.transition(state) if appended else self.catalog.initial(state)
        absence_rows = checked('absence', gates.ABSENCE,
                               [context['temporary_schemas'], list(ids.values()), context['window']])
        require(len(absence_rows) == 1, 'absence_rows')
        absence = absence_rows[0]
        gates.check_absence(absence)
        io = monitor.close()
        self._zero_io(io)
        query(phase+'_rollback', 'ROLLBACK')
        gate.save('case-history-'+label+'.json', attested)
        gate.save('case-catalog-'+label+'.json', catalog_receipt)
        gate.save('integral-gates-'+label+'.json', {
            'access': access, 'migrations': migrations, 'catalog_sha': gates.digest(state['catalog']),
            'absence': absence, 'io': io, 'unchanged': True,
            'history_count': len(migrations), 'canonical_migration_added': False})
        return state

    def _final(self, gate, ids, stage, query):
        c = self.composition
        phase = 'gates_final_' + stage
        args = gates.final_parameters(ids, c.fixture_context, stage)
        query(phase+'_begin', 'BEGIN TRANSACTION READ ONLY')
        if stage == 'pre':
            query(phase+'_timeout', "SET LOCAL statement_timeout='5s'")
            self._readonly(phase, query)
        monitor = self._monitor(gate, phase, query)
        monitor.start()
        qid = monitor.bind(FINAL, args, read_only=True)
        rows = query(phase+'_metadata', FINAL, args)
        monitor.executed(qid)
        require(len(rows) == 1 and type(rows[0].get('value')) is dict, 'final_rows')
        value = rows[0]['value']
        require(set(value) == {'access', 'migrations', 'catalog', 'absence', 'temporary_schema_names',
                              'readonly', 'statement_timeout', 'lock_timeout'}, 'final_shape')
        require(value['readonly'] is True and value['statement_timeout'] in ('5s', '5000ms')
                and value['lock_timeout'] in ('1s', '1000ms'), 'final_readonly_limits')
        gates.check_access(value['access'])
        self.history.check_observed(value['migrations'])
        catalog_receipt = self.catalog.check_observed({
            'migrations': value['migrations'], 'catalog': value['catalog']})
        names = sorted(args[3]) if stage == 'pre' else []
        require(value['temporary_schema_names'] == names
                and type(value['absence'].get('temporary_schemas')) is int
                and value['absence']['temporary_schemas'] == len(names), 'final_temporary_scope')
        gates.check_absence({**value['absence'], 'temporary_schemas': 0})
        if stage == 'post':
            c.temporary_absence_confirmed()
        io = monitor.close()
        self._zero_io(io)
        query(phase+'_rollback', 'ROLLBACK')
        gate.save('case-catalog-final-'+stage+'.json', catalog_receipt)
        gate.save('integral-gates-'+('final_pre' if stage == 'pre' else 'after_cleanup')+'.json', {
            'access': value['access'], 'migrations': value['migrations'],
            'catalog_sha': gates.digest(value['catalog']), 'absence': value['absence'],
            'io': io, 'unchanged': True, 'stage': stage,
            'metadata_sql_sha256': hashlib.sha256(FINAL.encode()).hexdigest(),
            'catalog_excluded_schemas': args[0], 'temporary_schema_names': value['temporary_schema_names']})

    def run(self, gate, ids, label):
        c = self.composition
        require(self.gate is gate and dict(ids) == self.ids and c.case_preservation is self,
                'run_binding')
        require(len(self.attempts) < len(LABELS) and label == LABELS[len(self.attempts)],
                'sequence_or_retry')
        require(not c.meter.stopped and not c.meter.closed, 'meter_stopped')
        if label in ('after_cleanup', 'final_post'):
            require(label not in c.final_attempted
                    and (label != 'final_post' or c.final_pre_complete and c.final_dry_complete),
                    'final_sequence')
            c.final_attempted.add(label)
        self.attempts.append(label)
        connection = None
        begun = rollback_attempted = False
        failure = None
        stream_value = baseline = None
        dispatched = 0
        phase = 'connect'
        failure_phase = None
        gate_start = None

        def query(name, text, args=()):
            nonlocal begun, rollback_attempted, dispatched, phase
            phase = name
            rollback = text == 'ROLLBACK'
            previous_label = c.safety_label
            try:
                # A stream validation exception reaches its own finally here.
                # Stop before that rollback, so the existing reader safety slot pays.
                if rollback and sys.exception() is not None and not c.meter.stopped:
                    c.abort('case_preservation_stream_failure')
                if rollback and c.meter.stopped:
                    c.safety_label = 'rollback_reader'
                c.before_sql(name, text)
                bound, params = bind_parameters(text, args)
                if text.startswith('BEGIN '):
                    begun = True
                    rollback_attempted = False
                if rollback:
                    rollback_attempted = True
                dispatched += 1
                cursor = connection.execute(bound, params)
                rows = cursor.fetchall() if cursor.description else []
                query.terminal_count = cursor.rowcount
                if rollback:
                    begun = False
                c.after_sql(name, text)
                return rows
            except BaseException as error:
                self._abort(error)
                raise
            finally:
                c.safety_label = previous_label
        query.terminal_count = None

        try:
            runtime = c.native_runtime(gate)
            require(runtime.environment == 'disposable_ci', 'environment')
            connection = runtime.connect()
            if label not in ('after_migration', 'final_post'):
                stream_value = self.stream.run(query, gate.save, ids, c.fixture_context,
                                               label, c.preservation_baseline)
                require(stream_value['protocol_commands'] == dispatched
                        and stream_value['protected_equal'] is True, 'stream_trace_count')
            gate_start = dispatched
            if label in ('before', 'after_migration'):
                baseline = self._gate(gate, ids, label, query)
                require(dispatched-gate_start == GATE_COMMANDS[label], 'gate_command_count')
            elif label in ('after_cleanup', 'final_post'):
                stage = 'pre' if label == 'after_cleanup' else 'post'
                self._final(gate, ids, stage, query)
                require(dispatched-gate_start == GATE_COMMANDS[stage], 'final_command_count')
        except BaseException as error:
            failure = error
            failure_phase = phase
            self._abort(error)
        finally:
            # BEGIN may have reached PostgreSQL despite a lost response. Never
            # repeat a rollback already dispatched by the stream or gate.
            if begun and not rollback_attempted:
                try:
                    query('safety_rollback', 'ROLLBACK')
                except BaseException as error:
                    failure = self._secondary(failure, 'rollback', error)
            if connection is not None:
                try:
                    connection.close()
                except BaseException as error:
                    if failure is None:
                        failure_phase = 'connection_close'
                    failure = self._secondary(failure, 'close', error)
                    self._abort(failure)
            if failure is not None:
                try:
                    gate.save('integral-preservation-'+label+'-stop.json', {
                        'phase': failure_phase or phase, 'exception_class': type(failure).__name__,
                        'sqlstate': getattr(failure, 'sqlstate', None),
                        'dispatch_attempts': dispatched, 'rollback_attempted': rollback_attempted,
                        'automatic_retry': False, 'full_chain_admission': False})
                except BaseException as error:
                    failure = self._secondary(failure, 'stop_receipt', error)
        if failure is not None:
            raise failure
        if baseline is not None:
            c.gate_baseline = copy.deepcopy(baseline)
        if c.preservation_baseline is None and stream_value is not None:
            c.preservation_baseline = copy.deepcopy(stream_value)
        if label == 'after_cleanup':
            c.final_pre_complete = True
        elif label == 'final_post':
            c.final_cleanup_confirmed()
        return {'label': label, 'commands': dispatched,
                'stream_commands': stream_value['protocol_commands'] if stream_value else 0,
                'gate_commands': dispatched-gate_start if gate_start is not None else 0,
                'tables': len(stream_value['tables']) if stream_value else 0,
                'protected_equal': stream_value['protected_equal'] if stream_value else True}
