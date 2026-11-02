"""Bootstrap contract tests; actual PG17 execution belongs to source-bound CI."""
import copy
import hashlib
import json
import types
import unittest
from unittest.mock import patch
import admission_fixture_context as b

IDS = {'a': '00000000-0000-4000-8000-000000000001',
       'trainer': '00000000-0000-4000-8000-000000000002',
       'b': '00000000-0000-4000-8000-000000000003'}


class Cursor:
    def __init__(self, rows): self.rows = rows; self.description = rows is not None
    def fetchall(self): return self.rows


class Runtime:
    environment = 'disposable_ci'
    def __init__(self, *, existing=False, lost=False):
        self.commands = []; self.closed = 0; self.existing = existing; self.lost = lost
        self.ids = {role: IDS[source] for role,source in b.ROLE_MAP.items()}
    def connect(self): return self
    def clear(self): self.cleared = True
    def close(self): self.closed += 1
    def execute(self, sql, args=None):
        self.commands.append(sql)
        if sql == 'COMMIT' and self.lost: raise ConnectionError('test-only')
        if 'count(*)' in sql: return Cursor([{'identities': int(self.existing), 'operators': 0}])
        if 'from auth.users' in sql or 'insert into fmz6e11_private.identities' in sql:
            return Cursor([{'id': x} for x in self.ids.values()])
        if 'insert into fmz6e11_private.operators' in sql:
            return Cursor([{'id': IDS['trainer']}])
        if "current_setting('transaction_read_only')" in sql: return Cursor([{'readonly': True}])
        if 'left join fmz6e11_private.operators' in sql:
            sha = hashlib.sha256(json.dumps(self.ids, sort_keys=True).encode()).hexdigest()
            return Cursor([{'id': value, 'role': role, 'enabled': True,
                'operator': role=='a_trainer', 'provenance_sha': sha} for role,value in self.ids.items()])
        return Cursor(None)


class Tests(unittest.TestCase):
    def execute(self, runtime):
        self.receipts = {}
        def save(name, value):
            self.assertNotIn(name, self.receipts)
            self.receipts[name] = copy.deepcopy(value)
        self.gate = types.SimpleNamespace(save=save)
        with patch.object(b.NativeRuntime, 'disposable', return_value=runtime):
            return b.run(self.gate, {'claims': {k:{'sub':v} for k,v in IDS.items()}})

    def test_normal_exact_bootstrap_is_counted_and_separate(self):
        runtime = Runtime(); result = self.execute(runtime)
        self.assertEqual(result['status'], 'DISPOSABLE_BOOTSTRAP_PASS')
        self.assertEqual(len(runtime.commands), 10)
        self.assertEqual(len(result['dispatches']), 10)
        self.assertTrue(all(x['confirmed'] for x in result['dispatches']))
        self.assertFalse(self.receipts['admission-fixture-dispatch-01.json']['confirmed'])
        self.assertEqual(runtime.closed, 2)
        self.assertTrue(runtime.cleared)
        self.assertEqual(set(self.gate.fixture_cleanup_ids), set(b.ROLE_MAP))
        self.assertTrue(result['local_setup_not_hosted_run_capacity'])

    def test_existing_registry_never_overwritten(self):
        runtime = Runtime(existing=True)
        with self.assertRaisesRegex(ValueError, 'existing_registry'): self.execute(runtime)
        self.assertFalse(any('insert into' in sql for sql in runtime.commands))
        self.assertEqual(runtime.commands[-1], 'ROLLBACK')
        self.assertEqual(self.receipts['admission-fixture-bootstrap.json']['status'], 'NO_GO')

    def test_unknown_commit_does_not_issue_retry_or_claim_pass(self):
        runtime = Runtime(lost=True)
        with self.assertRaises(ConnectionError): self.execute(runtime)
        self.assertEqual(runtime.commands.count('COMMIT'), 1)
        receipt = self.receipts['admission-fixture-bootstrap.json']
        self.assertFalse(receipt['commit_confirmed'])
        self.assertEqual(receipt['status'], 'NO_GO')
        self.assertFalse(receipt['automatic_retry'])

    def test_duplicate_actor_is_rejected_before_runtime(self):
        with patch.object(b.NativeRuntime, 'disposable') as create:
            with self.assertRaises(ValueError):
                b.run(types.SimpleNamespace(), {'claims': {k:{'sub':IDS['a']} for k in IDS}})
            create.assert_not_called()

    def test_close_failure_retains_receipt_and_blocks_following_fixture(self):
        runtime = Runtime()
        def close():
            runtime.closed += 1
            if runtime.closed == 2: raise OSError('synthetic-close')
        runtime.close = close
        with self.assertRaisesRegex(RuntimeError, 'closure_unconfirmed'): self.execute(runtime)
        receipt = self.receipts['admission-fixture-bootstrap.json']
        self.assertEqual(receipt['close_error_class'], 'OSError')
        self.assertEqual(receipt['status'], 'NO_GO')
        self.assertFalse(hasattr(self.gate, 'fixture_cleanup_ids'))
        self.assertTrue(runtime.cleared)

    def test_close_failure_does_not_replace_original_commit_failure(self):
        runtime = Runtime(lost=True)
        runtime.close = lambda: (_ for _ in ()).throw(OSError('synthetic-close'))
        with self.assertRaises(ConnectionError): self.execute(runtime)
        receipt = self.receipts['admission-fixture-bootstrap.json']
        self.assertEqual(receipt['error_class'], 'ConnectionError')
        self.assertEqual(receipt['close_error_class'], 'OSError')


if __name__ == '__main__': unittest.main()
