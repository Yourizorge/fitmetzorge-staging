"""One-shot cleanup component, currently local-only, with pre-COMMIT ownership.

Caller must prepare before any fixture write and capture on EACH owned writer
transaction before COMMIT. Missing capture is not repaired using a zero sample.
The immutable save callback must refuse overwrites. No automatic mutation retry.
Hosted wiring, global prefix budget and WAL/IO admission remain separate blockers.
"""
import copy
import hashlib
import json
import re

from admission_binding import NEW_RUN, OLD_RUN
from fixture_cleanup_evidence import parameters
import fixture_cleanup_runtime_sql as sql


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class Blocked(RuntimeError):
    pass


class Protocol:
    """Pre-dispatch admission, then attempted ledger. Uncertain sends stay charged."""
    def __init__(self, charge):
        self.charge = charge
        self.events = []

    def execute(self, connection, phase, text, args=()):
        from sql_protocol import statements
        if len(statements(text)) != 1:
            raise Blocked('cleanup_single_statement')
        event = {'ordinal': len(self.events) + 1, 'phase': phase,
                 'sql_sha256': hashlib.sha256(text.encode()).hexdigest(), 'confirmed': False}
        self.charge(copy.deepcopy(event))
        self.events.append(event)
        values = []
        def bind(match):
            value = args[int(match[1]) - 1]
            values.append(json.dumps(value) if isinstance(value, dict) else value)
            return '%s'
        bound = re.sub(r'\$(\d+)', bind, text.replace('%', '%%')) if args else text
        cursor = connection.execute(bound, values if args else None)
        rows = cursor.fetchall() if cursor.description else []
        event['confirmed'] = True
        return rows


def validate_rows(value):
    if not isinstance(value, dict) or set(value) != {'rows', 'xid'}:
        raise Blocked('cleanup_inventory_shape')
    rows = value['rows']
    if not isinstance(rows, list) or len(rows) > 1000:
        raise Blocked('cleanup_inventory_bound')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'table', 'key_sha', 'row_sha', 'xmin', 'scope_ok'}:
            raise Blocked('cleanup_inventory_row')
        if row['table'] not in sql.ORDER or row['scope_ok'] is not True:
            raise Blocked('cleanup_foreign_scope')
        if any(not isinstance(row[k], str) or not re.fullmatch('[a-f0-9]{64}', row[k]) for k in ('key_sha', 'row_sha')):
            raise Blocked('cleanup_inventory_digest')
        if not isinstance(row['xmin'], str) or not row['xmin'].isdigit():
            raise Blocked('cleanup_inventory_xmin')
        identity = (row['table'], row['key_sha'])
        if identity in seen:
            raise Blocked('cleanup_duplicate_key')
        seen.add(identity)
    return copy.deepcopy(rows)


class Cleanup:
    def __init__(self, runtime, context, save, charge, *, preparation_run=NEW_RUN):
        # Do not accidentally activate the new offline UUID as a hosted quota.
        if runtime.environment != 'disposable_ci':
            raise Blocked('cleanup_hosted_not_admitted')
        if preparation_run != NEW_RUN:
            raise Blocked('cleanup_preparation_binding')
        self.args = parameters(context)
        if OLD_RUN in [self.args[0], *self.args[1]] or NEW_RUN in [self.args[0], *self.args[1]]:
            raise Blocked('cleanup_fresh_case_required')
        self.runtime, self.save = runtime, save
        self.protocol = Protocol(charge)
        self.case = self.args[0]
        self.prefix = 'fixture-cleanup-' + self.case + '-'
        self.binding = {'preparation_run': preparation_run, 'case': self.case,
                        'scope_sha256': digest(self.args), 'component_only': True}
        self.prepared = False
        self.attempted = False
        self.snapshots = []
        self._rows = []

    def write(self, name, value):
        self.save(self.prefix + name + '.json', {**self.binding, **copy.deepcopy(value)})

    def query(self, connection, phase, text, args=()):
        return self.protocol.execute(connection, phase, text, args)

    def check(self, connection, phase, readonly):
        rows = self.query(connection, phase, sql.CHECK)
        if len(rows) != 1 or set(rows[0]) != {'pg17', 'bounded_statement', 'bounded_lock', 'privileged', 'origin', 'unbound', 'readonly'}:
            raise Blocked('cleanup_session_shape')
        if any(rows[0][k] is not True for k in rows[0] if k != 'readonly') or rows[0]['readonly'] is not readonly:
            raise Blocked('cleanup_session_limits')

    def inventory(self, connection, phase):
        result = self.query(connection, phase, sql.INVENTORY, self.args)
        if len(result) != 1:
            raise Blocked('cleanup_inventory_result')
        return result[0]['value']

    def prepare(self):
        if self.prepared or self.attempted:
            raise Blocked('cleanup_duplicate_prepare')
        self.write('intent', {'planned_protocol': [(p, hashlib.sha256(s.encode()).hexdigest())
                   for p, s in sql.plan()['normal']], 'global_2349_admitted': False})
        connection = self.runtime.connect()
        try:
            self.query(connection, 'prepare_begin', 'BEGIN TRANSACTION READ ONLY')
            self.check(connection, 'prepare_check', True)
            rows = validate_rows(self.inventory(connection, 'prepare_inventory'))
            if rows:
                raise Blocked('cleanup_baseline_not_empty')
            self.query(connection, 'prepare_rollback', 'ROLLBACK')
            self.write('baseline', {'rows': [], 'source': 'actual_empty_inventory'})
            self.prepared = True
        finally:
            connection.close()

    def capture(self, writer):
        """Persist current-owned rowversions before writer COMMIT (including lost reply).

        The caller owns and serializes its writer transactions. A snapshot already
        persisted for a transaction that later rolls back is harmless: cleanup only
        accepts exact rowversions from any persisted snapshot, never new keys.
        """
        if not self.prepared or self.attempted:
            raise Blocked('cleanup_capture_sequence')
        value = self.inventory(writer, 'capture')
        rows = validate_rows(value)
        xid = value['xid']
        if not isinstance(xid, str) or not xid.isdigit():
            raise Blocked('cleanup_capture_requires_writer_xid')
        prior = {digest(r) for snapshot in self.snapshots for r in snapshot['rows']}
        for row in rows:
            if digest(row) not in prior and row['xmin'] != str(int(xid) % (2**32)):
                raise Blocked('cleanup_unowned_writer_row')
        snapshot = {'rows': rows, 'xid': xid, 'previous': digest(self.snapshots),
                    'before_commit': True}
        self.write('writer-%04d' % len(self.snapshots), snapshot)
        self.snapshots.append(snapshot)
        self._rows = rows

    def run(self, *, worker_joined, writers_closed, mint_barrier):
        if self.attempted:
            raise Blocked('cleanup_duplicate_attempt')
        if not self.prepared or any(x is not True for x in (worker_joined, writers_closed, mint_barrier)):
            raise Blocked('cleanup_writer_barrier_required')
        # An immutable claim receipt is written before even opening a connection.
        self.attempted = True
        self.write('claim', {'writer_journal_sha256': digest(self.snapshots), 'writer_barrier': True})
        result = {**self.binding, 'status': 'NO_GO', 'commit_confirmed': False,
                  'commit_unknown': False, 'absence_confirmed': False, 'deletion_proven': False,
                  'cleanup_complete': False, 'delete_count': None, 'returned_delete_count': 0,
                  'hosted_admitted': False, 'global_budget_proven': False,
                  'wal_classification': 'NOT_MEASURED_COMPONENT_ONLY'}
        connection = None
        began = False
        commit_attempted = False
        before = []
        try:
            connection = self.runtime.connect()
            began = True
            self.query(connection, 'begin', 'BEGIN')
            self.check(connection, 'check', False)
            self.query(connection, 'barrier', sql.LOCK)
            before = validate_rows(self.inventory(connection, 'inventory'))
            allowed = {digest(r) for snapshot in self.snapshots for r in snapshot['rows']}
            if any(digest(r) not in allowed for r in before):
                raise Blocked('cleanup_unowned_or_changed_row')
            self.write('predelete', {'rows': before, 'expected_counts': self.counts(before),
                       'writer_journal_sha256': digest(self.snapshots)})
            for table in sql.ORDER:
                expected = [{k: v for k, v in r.items() if k != 'scope_ok'} for r in before if r['table'] == table]
                records = self.query(connection, 'delete_' + table, sql.delete(table),
                                     [*self.args, json.dumps(expected)])
                if len(records) != 1 or not isinstance(records[0].get('value'), list):
                    raise Blocked('cleanup_delete_receipt_shape')
                actual = records[0]['value']
                if sorted(map(digest, actual)) != sorted(map(digest, expected)):
                    raise Blocked('cleanup_delete_multiset')
                result['returned_delete_count'] += len(actual)
                self.write('delete-' + table, {'expected': expected, 'returned': actual,
                           'commit_confirmed': False})
            # The audit is persisted before COMMIT; none of these rows are history rewrites.
            self.write('commit-intent', {'delete_counts': self.counts(before)})
            commit_attempted = True
            self.query(connection, 'commit', 'COMMIT')
            result['commit_confirmed'] = True
            began = False
            self.write('commit', {'commit_confirmed': True, 'delete_counts': self.counts(before)})
        except BaseException as error:
            result['error_class'] = type(error).__name__
            result['reason'] = str(error) if isinstance(error, Blocked) else 'cleanup_transport_or_storage_error'
            result['commit_unknown'] = commit_attempted and not result['commit_confirmed']
            if connection is not None and began and not commit_attempted:
                try:
                    self.query(connection, 'rollback', 'ROLLBACK')
                    result['rollback_confirmed'] = True
                except BaseException:
                    result['rollback_confirmed'] = False
        finally:
            if connection is not None:
                try:
                    connection.close()
                except BaseException:
                    result['close_unknown'] = True
        # Always use a fresh connection. Absence never repairs an unknown COMMIT.
        witness = None
        try:
            witness = self.runtime.connect()
            self.query(witness, 'absence_begin', 'BEGIN TRANSACTION READ ONLY')
            self.check(witness, 'absence_check', True)
            remaining = validate_rows(self.inventory(witness, 'absence'))
            self.query(witness, 'absence_rollback', 'ROLLBACK')
            result['remaining_counts'] = self.counts(remaining)
            result['absence_confirmed'] = not remaining
        except BaseException as error:
            result['absence_error_class'] = type(error).__name__
        finally:
            if witness is not None:
                try:
                    witness.close()
                except BaseException:
                    result['close_unknown'] = True
        good = (result['commit_confirmed'] and result['absence_confirmed'] and
                not result.get('error_class') and not result.get('close_unknown'))
        result.update(status='COMPONENT_PASS' if good else 'NO_GO', cleanup_complete=good,
                      deletion_proven=good and bool(before), delete_count=len(before) if good else None,
                      predelete_counts=self.counts(before), protocol=copy.deepcopy(self.protocol.events))
        self.write('result', result)
        return result

    @staticmethod
    def counts(rows):
        return {table: sum(r['table'] == table for r in rows) for table in sql.ORDER}
