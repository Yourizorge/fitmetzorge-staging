"""Live locked scope for parent-only deletion; unchanged C validators apply."""
import contextlib
import pathlib
import sys

import admission_auth_runtime_profile as profile
import fixture_cleanup_runtime as cleanup
import fixture_producer_scope as producer
from native_runtime import NativeRuntime

from .lifecycle import Records, need


class Queries:
    def __init__(self, records, limit):
        self.records, self.limit = records, limit
        self.protocol = cleanup.Protocol(self.charge)

    def charge(self, event):
        need(len(self.protocol.events) < self.limit, 'native_command_limit')
        self.records.save('sql-%03d-before.json' % event['ordinal'], event)

    def execute(self, connection, phase, text, args=()):
        rows = self.protocol.execute(connection, phase, text, args)
        event = self.protocol.events[-1]
        self.records.save('sql-%03d-after.json' % event['ordinal'], {
            **event, 'row_count': len(rows), 'raw_row_values_exported': False})
        if phase.endswith('_metadata') or phase.endswith('_privileges'):
            self.records.save('sql-%03d-observation.json' % event['ordinal'], {
                'phase': phase, 'rows': profile.observation_rows(phase, rows),
                'source_binding': self.records.source, 'query_io_observed': False})
        return rows


def reduce_profile(gate, runtime, isolation, container):
    """Same single-field local reduction and validators; no legacy run authority."""
    from .lifecycle import AuthContainer
    need(type(runtime) is NativeRuntime and runtime.environment == 'disposable_ci'
         and type(container) is AuthContainer and not container.create_attempted,
         'profile_before_container_creation')
    records = Records(gate, 'component-auth-profile',
                      [sys.modules[__name__], profile, producer, cleanup, sys.modules[NativeRuntime.__module__]])
    query = Queries(records, profile.LIMIT)
    records.save('plan.json', profile.command_register())
    connection = None
    primary = None
    transaction = False
    commit_attempted = False
    try:
        connection = runtime.connect()
        transaction = True
        query.execute(connection, 'begin', 'BEGIN')
        before = profile.metadata(query.execute(connection, 'before_metadata', profile.META), isolation, readonly=False)
        profile.privileges(query.execute(connection, 'before_privileges', producer.PRIVILEGES,
                                        [list(producer.SCHEMAS)]), before=True)
        query.execute(connection, 'restrict', profile.ALTER)
        after = profile.metadata(query.execute(connection, 'after_metadata', profile.META), isolation, readonly=False)
        profile.delta(before, after, fresh=False)
        commit_attempted = True
        query.execute(connection, 'commit', 'COMMIT'); transaction = False
        connection.close()
        need(connection.closed, 'profile_connection_close')
        connection = runtime.connect()
        query.execute(connection, 'witness_begin', 'BEGIN TRANSACTION READ ONLY'); transaction = True
        witness = profile.metadata(query.execute(connection, 'witness_metadata', profile.META), isolation, readonly=True)
        profile.delta(before, witness, fresh=True)
        profile.privileges(query.execute(connection, 'witness_privileges', producer.PRIVILEGES,
                                        [list(producer.SCHEMAS)]), before=False)
        query.execute(connection, 'witness_rollback', 'ROLLBACK'); transaction = False
    except BaseException as error:
        primary = error
    finally:
        if connection is not None:
            try:
                if transaction:
                    query.execute(connection, 'failure_rollback', 'ROLLBACK')
            except BaseException as secondary:
                if primary is None: primary = secondary
                else: primary.add_note('component_profile_rollback_secondary:'+type(secondary).__name__)
            finally:
                try:
                    connection.close()
                    need(connection.closed, 'profile_connection_close')
                except BaseException as secondary:
                    if primary is None: primary = secondary
                    else: primary.add_note('component_profile_close_secondary:'+type(secondary).__name__)
    try:
        if primary is None:
            records.save('result.json', {'status': 'LOCALONLY_RUNTIME_CAPABILITY_REDUCED',
                'commit_confirmed': True, 'commit_unknown': False,
                'isolation': isolation, 'explicit_commands': len(query.protocol.events),
                'profile_metadata_hashes': [producer.digest(v) for v in (before, after, witness)],
                'hosted_equivalence': False, 'full_chain_admission': False})
        else:
            records.save('incomplete.json', {'error_class': type(primary).__name__,
                'commit_attempted': commit_attempted, 'commit_known': False,
                'claims_released': False, 'full_chain_admission': False})
    except BaseException as secondary:
        if primary is None: primary = secondary
        else: primary.add_note('component_profile_receipt_secondary:'+type(secondary).__name__)
    try:
        records.seal()
    except BaseException as secondary:
        if primary is None: primary = secondary
        else: primary.add_note('component_profile_archive_secondary:'+type(secondary).__name__)
    if primary is not None:
        raise primary
    return records


class ScopeLease:
    """No serialized flag can replace this open, source-bound physical lock lease."""
    def __init__(self, gate, runtime, run_id):
        need(type(runtime) is NativeRuntime and runtime.environment == 'disposable_ci', 'scope_runtime')
        from auth_failure import binding
        binding(run_id)
        self.gate, self.runtime, self.run_id = gate, runtime, run_id
        self.records = Records(gate, 'component-parent-scope',
            [sys.modules[__name__], producer, cleanup, sys.modules[NativeRuntime.__module__]])
        self.contract = producer.source_contract(gate)
        self.query = Queries(self.records, 24)
        self.connection = None
        self.live = self.entered = False

    def __enter__(self):
        need(not self.entered, 'scope_replay')
        self.entered = True
        self.connection = self.runtime.connect()
        try:
            self.query.execute(self.connection, 'begin', 'BEGIN')
            tables = ','.join('fmz6e11_private.'+t for t in producer.TABLES)
            self.query.execute(self.connection, 'locks', 'LOCK TABLE '+tables+' IN SHARE MODE')
            samples = {}
            for name, text in producer.QUERIES:
                args = [list(producer.TABLES)] if name in ('relations','fks') else [
                    list(producer.SCHEMAS)] if name in ('privileges','functions') else ()
                samples[name] = producer.bounded(self.query.execute(self.connection, name, text, args))
            self.observation = producer.validate(samples, self.contract, before=True)
            self.records.save('validated.json', self.observation)
            self.live = True
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def check(self):
        self.records.check()
        need(self.live and self.connection is not None and not self.connection.closed, 'scope_not_held')
        need(producer.source_contract(self.gate) == self.contract, 'migration_contract_changed')

    def no_references(self, actors):
        self.check()
        actors = tuple(actors)
        external = [f for f in self.contract['fks'] if f['target_schema'] == 'auth']
        need(len(external) == 9, 'scope_fk_count')
        for index, fk in enumerate(external):
            need(fk['relation'] in producer.TABLES and len(fk['columns']) == 1
                 and fk['on_delete'] == fk['on_update'] == 'a', 'scope_fk_shape')
            # Identifiers come only from the pinned parsed migration contract.
            import re
            column = fk['columns'][0]
            need(re.fullmatch('[a-z_][a-z0-9_]*', column), 'scope_fk_column')
            sql = 'SELECT count(*) n FROM fmz6e11_private.'+fk['relation']+' WHERE '+column+'=ANY($1::uuid[])'
            rows = self.query.execute(self.connection, 'fk-%d'%index, sql, [list(actors)])
            need(rows == [{'n': 0}], 'parent_has_product_references')

    def __exit__(self, kind, error, traceback):
        self.live = False
        if self.connection is None:
            return False
        first = error
        try:
            self.query.execute(self.connection, 'rollback', 'ROLLBACK')
        except BaseException as secondary:
            if first is None: first = secondary
            else: first.add_note('component_scope_rollback_secondary:'+type(secondary).__name__)
        finally:
            try:
                self.connection.close()
                need(self.connection.closed, 'scope_connection_close')
            except BaseException as secondary:
                if first is None: first = secondary
                else: first.add_note('component_scope_close_secondary:'+type(secondary).__name__)
        if error is None and first is not None:
            raise first
        return False
