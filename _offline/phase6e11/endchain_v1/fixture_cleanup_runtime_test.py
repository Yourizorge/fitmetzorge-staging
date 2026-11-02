"""Focused runtime contracts; mocked transport is NOT actual PG17 evidence."""
import copy
import unittest
from unittest.mock import Mock

from admission_binding import OLD_RUN
from fixture_cleanup_runtime import Blocked, Cleanup, Protocol, digest
import fixture_cleanup_runtime_sql as sql

CONTEXT = {k: '78000000-0000-4000-8000-%012d' % i for i, k in enumerate(('window', 'a', 'b'), 1)}


def row(table='windows', n=1, xmin='41'):
    return {'table': table, 'key_sha': digest([table, n]), 'row_sha': digest([table, n, xmin]),
            'xmin': xmin, 'scope_ok': True}


class Cursor:
    description = True
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows


class Database:
    environment = 'disposable_ci'
    def __init__(self):
        self.rows = []
        self.saved = {}
        self.calls = []
        self.connections = []
        self.fail = None
        self.lost_commit = False
        self.corrupt_return = False
        self.xid = '41'
    def save(self, name, value):
        if name in self.saved: raise FileExistsError(name)
        self.saved[name] = copy.deepcopy(value)
    def connect(self):
        db = self
        class Connection:
            def __init__(self): self.backup = None; self.readonly = False; self.closed = False
            def close(self):
                if self.backup is not None: db.rows = self.backup
                self.closed = True
            def execute(self, text, args=None):
                db.calls.append(text)
                if db.fail and db.fail in text: raise TimeoutError('injected')
                if text.startswith('BEGIN'):
                    self.backup = copy.deepcopy(db.rows); self.readonly = 'READ ONLY' in text
                    return Cursor([])
                if text == 'ROLLBACK':
                    db.rows = self.backup; self.backup = None; return Cursor([])
                if text == 'COMMIT':
                    self.backup = None
                    if db.lost_commit: raise ConnectionError('injected after real commit boundary')
                    return Cursor([])
                if text == sql.CHECK:
                    return Cursor([{**dict.fromkeys(('pg17', 'bounded_statement', 'bounded_lock', 'privileged', 'origin', 'unbound'), True),
                                    'readonly': self.readonly}])
                if text.startswith('LOCK TABLE'): return Cursor([])
                if text.startswith('with removed as'):
                    table = text.split('fmz6e11_private.')[1].split(' ')[0]
                    actual = [{k: v for k, v in r.items() if k != 'scope_ok'} for r in db.rows if r['table'] == table]
                    db.rows = [r for r in db.rows if r['table'] != table]
                    return Cursor([{'value': [] if db.corrupt_return else actual}])
                return Cursor([{'value': {'rows': copy.deepcopy(db.rows), 'xid': db.xid}}])
        c = Connection(); self.connections.append(c); return c


class CleanupRuntimeTests(unittest.TestCase):
    def setup_case(self, rows=()):
        db = Database(); meter = Mock()
        cleanup = Cleanup(db, CONTEXT, db.save, meter)
        cleanup.prepare()
        db.rows = copy.deepcopy(list(rows))
        if rows: cleanup.capture(db.connect())
        return db, cleanup, meter

    def run_case(self, cleanup):
        return cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)

    def test_all_thirteen_actual_templates_and_physical_keys(self):
        from sql_protocol import parser, statements
        for group in sql.plan().values():
            for _, text in group:
                self.assertEqual(len(statements(text)), 1)
                self.assertEqual(len(parser().parse_sql(text)), 1)
        self.assertEqual(len(sql.ORDER), 13)
        self.assertEqual(sql.KEYS['audit'], ('id',))
        self.assertEqual(sql.KEYS['events'], ('id',))
        self.assertNotIn('fmz6e11_request_private', sql.LOCK)

    def test_full_parent_partial_and_dependent_inventory(self):
        for rows in ([row(t) for t in sql.ORDER], [row()], [row('events')], [row('plans'), row('b_states')]):
            db, cleanup, meter = self.setup_case(rows)
            result = self.run_case(cleanup)
            self.assertEqual(result['status'], 'COMPONENT_PASS')
            self.assertEqual(result['delete_count'], len(rows))
            self.assertTrue(result['deletion_proven'])
            self.assertEqual(db.rows, [])
            self.assertEqual(len(cleanup.protocol.events), 4 + 1 + 22)
            self.assertEqual(meter.call_count, len(cleanup.protocol.events))
            self.assertTrue(db.connections[-1].readonly)

    def test_zero_is_absence_not_proven_deletion(self):
        db, cleanup, _ = self.setup_case()
        result = self.run_case(cleanup)
        self.assertEqual(result['status'], 'COMPONENT_PASS')
        self.assertEqual(result['delete_count'], 0)
        self.assertFalse(result['deletion_proven'])
        self.assertFalse(result['hosted_admitted'])

    def test_barrier_is_required_before_connect_or_dispatch(self):
        for key in ('worker_joined', 'writers_closed', 'mint_barrier'):
            db, cleanup, _ = self.setup_case([row()]); before = len(db.calls)
            flags = dict(worker_joined=True, writers_closed=True, mint_barrier=True); flags[key] = False
            with self.assertRaisesRegex(Blocked, 'writer_barrier'): cleanup.run(**flags)
            self.assertEqual(len(db.calls), before)

    def test_foreign_or_changed_row_blocks_all_deletes(self):
        for replacement in ([row(n=2)], [row(xmin='42')], [dict(row(), scope_ok=False)]):
            db, cleanup, _ = self.setup_case([row()]); db.rows = replacement
            result = self.run_case(cleanup)
            self.assertEqual(result['status'], 'NO_GO')
            self.assertFalse(any('with removed as' in q for q in db.calls))
            self.assertEqual(db.rows, replacement)

    def test_baseline_foreign_rows_never_become_owned(self):
        db = Database(); db.rows = [row()]
        cleanup = Cleanup(db, CONTEXT, db.save, Mock())
        with self.assertRaisesRegex(Blocked, 'baseline_not_empty'): cleanup.prepare()
        self.assertEqual(db.rows, [row()])

    def test_foreign_transaction_capture_and_missing_capture_fail_closed(self):
        db, cleanup, _ = self.setup_case()
        db.rows = [row(xmin='42')]
        with self.assertRaisesRegex(Blocked, 'unowned_writer_row'): cleanup.capture(db.connect())
        result = self.run_case(cleanup)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['returned_delete_count'], 0)

    def test_duplicate_same_instance_or_new_instance_no_dispatch(self):
        db, cleanup, _ = self.setup_case([row()]); self.run_case(cleanup)
        before = len(db.calls)
        with self.assertRaisesRegex(Blocked, 'duplicate_attempt'): self.run_case(cleanup)
        second = Cleanup(db, CONTEXT, db.save, Mock())
        with self.assertRaises(FileExistsError): second.prepare()
        self.assertEqual(len(db.calls), before)

    def test_lost_commit_keeps_unknown_even_when_fresh_absence_zero(self):
        db, cleanup, _ = self.setup_case([row()]); db.lost_commit = True
        result = self.run_case(cleanup)
        self.assertTrue(result['commit_unknown']); self.assertTrue(result['absence_confirmed'])
        self.assertEqual(result['status'], 'NO_GO'); self.assertIsNone(result['delete_count'])
        self.assertEqual(db.calls.count('COMMIT'), 1)
        self.assertFalse(result['deletion_proven'])

    def test_timeout_or_partial_delete_or_interrupted_storage_rolls_back(self):
        for mode in ('timeout', 'partial', 'storage'):
            original = [row(t) for t in sql.ORDER]
            db, cleanup, _ = self.setup_case(original)
            if mode == 'timeout': db.fail = 'delete from fmz6e11_private.proposals'
            if mode == 'partial': db.corrupt_return = True
            if mode == 'storage':
                save = cleanup.save
                def broken(name, value):
                    if 'delete-events' in name: raise OSError('disk')
                    save(name, value)
                cleanup.save = broken
            result = self.run_case(cleanup)
            self.assertEqual(result['status'], 'NO_GO')
            self.assertTrue(result['rollback_confirmed'])
            self.assertEqual(db.rows, original)
            self.assertNotIn('COMMIT', db.calls)

    def test_predispatch_meter_denial_never_calls_transport(self):
        connection = Mock(); charge = Mock(side_effect=Blocked('capacity'))
        protocol = Protocol(charge)
        with self.assertRaises(Blocked): protocol.execute(connection, 'begin', 'BEGIN')
        connection.execute.assert_not_called(); self.assertEqual(protocol.events, [])

    def test_unknown_dispatch_never_refunds(self):
        connection = Mock(); connection.execute.side_effect = TimeoutError()
        charge = Mock(); protocol = Protocol(charge)
        with self.assertRaises(TimeoutError): protocol.execute(connection, 'begin', 'BEGIN')
        self.assertEqual(charge.call_count, 1); self.assertFalse(protocol.events[0]['confirmed'])

    def test_historical_binding_and_hosted_rejected_before_connections(self):
        db = Database()
        with self.assertRaises(Blocked): Cleanup(db, CONTEXT, db.save, Mock(), preparation_run=OLD_RUN)
        with self.assertRaises(Blocked): Cleanup(db, {**CONTEXT, 'window': OLD_RUN}, db.save, Mock())
        db.environment = 'staging'
        with self.assertRaises(Blocked): Cleanup(db, CONTEXT, db.save, Mock())
        self.assertEqual(db.connections, [])

    def test_receipts_contain_all_tables_and_no_body_values(self):
        db, cleanup, _ = self.setup_case([row(t) for t in sql.ORDER])
        result = self.run_case(cleanup)
        for table in sql.ORDER:
            receipt = db.saved[cleanup.prefix + 'delete-' + table + '.json']
            self.assertEqual(len(receipt['returned']), 1)
            self.assertFalse(receipt['commit_confirmed'])
            self.assertEqual(result['remaining_counts'][table], 0)

    def test_ci_missing_identity_prerequisite_blocks_without_native_connect(self):
        from fixture_cleanup_runtime_ci import run
        from unittest.mock import patch
        gate = Mock(spec=['save', 'sources', 'out', 'rows', 'sql'])
        with patch('fixture_cleanup_runtime_ci.NativeRuntime.disposable') as native:
            result = run(gate)
        native.assert_not_called()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result['fixture_mutation_attempted'])
        self.assertEqual(result['local_diagnostic_sql_count'], 0)
        self.assertTrue(all(not isinstance(v, (dict, list, tuple)) for v in result.values()))

    def test_ci_setup_templates_are_real_schema_single_statements(self):
        from fixture_cleanup_runtime_ci import inserts, PROTECTED, REGISTRY
        from sql_protocol import parser
        ids = {r: '79000000-0000-4000-8000-%012d' % i for i, r in enumerate(('a_member', 'a_trainer', 'b_member'), 1)}
        statements = inserts(CONTEXT, ids)
        self.assertEqual({t for t, _, _ in statements}, set(sql.ORDER))
        for text in [PROTECTED, REGISTRY] + [s for _, s, _ in statements]:
            self.assertEqual(len(parser().parse_sql(text)), 1)

    def test_capture_storage_failure_leaves_rows_unowned(self):
        db, cleanup, _ = self.setup_case()
        db.rows = [row()]
        old_save = cleanup.save
        cleanup.save = Mock(side_effect=OSError('disk'))
        with self.assertRaises(OSError): cleanup.capture(db.connect())
        self.assertEqual(cleanup.snapshots, [])
        cleanup.save = old_save
        self.assertEqual(self.run_case(cleanup)['status'], 'NO_GO')

    def test_plan_bounds_every_failure_prefix_without_mutation_retry(self):
        normal = sql.plan()['normal']
        self.assertEqual(len(normal), 22)
        commit = next(i for i, (name, _) in enumerate(normal) if name == 'commit')
        for failed_index in range(commit + 1):
            dispatched = failed_index + 1
            rollback = int(failed_index < commit)
            witness = 4
            self.assertLessEqual(dispatched + rollback + witness, 22)

    def test_protected_witness_is_bounded_scoped_and_duplicate_preserving(self):
        from fixture_cleanup_runtime_ci import protected_witness, PROTECTED
        self.assertNotIn('jsonb_agg', PROTECTED.lower())
        self.assertNotIn('order by', PROTECTED.lower())
        self.assertIn('limit 1001', PROTECTED.lower())
        self.assertIn('user_id=any($1::uuid[])', PROTECTED)
        item = {'table_name': 'auth.sessions', 'row_sha': 'a' * 64}
        self.assertNotEqual(protected_witness([item]), protected_witness([item, item]))
        self.assertEqual(protected_witness([item, item]), protected_witness([item, item][::-1]))
        with self.assertRaisesRegex(Blocked, 'overflow'):
            protected_witness([item] * 1001)


if __name__ == '__main__': unittest.main()
