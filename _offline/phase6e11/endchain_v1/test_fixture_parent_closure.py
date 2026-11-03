"""Offline source-owned suffix regressions; transport is mocked, not PG evidence."""
import copy
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import fixture_parent_closure as parent
from admission_binding import NEW_RUN
from admission_journal import Journal
from fixture_cleanup_runtime import Cleanup, digest
from fixture_cleanup_runtime_test import Database, Cursor, CONTEXT, row

IDS = {r: '79000000-0000-4000-8000-%012d' % i for i, r in enumerate(parent.ROLES, 1)}
ENV = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
       'GITHUB_REF': 'refs/heads/main'}


class Runtime(Database):
    def __init__(self):
        super().__init__()
        self.registry = parent.expected_registry(IDS)
        self.registry_lost_commit = False
        self.registry_bad_delete = False
        self.registry_rollback_error = False
        self.cleared = False

    def clear(self): self.cleared = True

    def connect(self):
        inner = super().connect()
        owner = self
        class Connection:
            def __init__(self): self.backup = None; self.registry_tx = False
            def close(self):
                if self.backup is not None: owner.registry = self.backup
                inner.close()
            def execute(self, text, args=None):
                if text.startswith('BEGIN'): self.backup = copy.deepcopy(owner.registry)
                if text == 'COMMIT':
                    self.backup = None
                    cursor = inner.execute(text, args)
                    if self.registry_tx and owner.registry_lost_commit:
                        raise ConnectionError('injected reply loss after registry COMMIT')
                    return cursor
                if text == 'ROLLBACK':
                    if owner.registry_rollback_error and self.registry_tx:
                        owner.calls.append(text)
                        raise ConnectionError('injected rollback reply loss')
                    if self.backup is not None: owner.registry = self.backup; self.backup = None
                if 'from fmz6e11_private.identities where user_id=any' in text:
                    self.registry_tx = True; owner.calls.append(text)
                    return Cursor([{'value': copy.deepcopy(owner.registry)}])
                if text.startswith('delete from fmz6e11_private.operators'):
                    owner.calls.append(text)
                    if owner.rows: raise RuntimeError('simulated retained fixture FK')
                    removed = owner.registry['operators']; owner.registry['operators'] = []
                    return Cursor(copy.deepcopy(removed))
                if text.startswith('delete from fmz6e11_private.identities'):
                    owner.calls.append(text)
                    removed = owner.registry['identities']; owner.registry['identities'] = []
                    return Cursor([] if owner.registry_bad_delete else copy.deepcopy(removed))
                return inner.execute(text, args)
        return Connection()


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fmz-parent-closure-')
        self.addCleanup(self.temp.cleanup)
        self.out = pathlib.Path(self.temp.name).resolve()
        self.db = Runtime()
        self.gate = types.SimpleNamespace(out=self.out, save=self.publish,
            container='supabase_db_fmz-db41-ci', fixture_cleanup_ids=copy.deepcopy(IDS))
        self.contexts = {CONTEXT['window']: copy.deepcopy(CONTEXT)}
        self.seed()

    def publish(self, name, value):
        with (self.out/name).open('xb') as stream:
            stream.write((json.dumps(value, sort_keys=True) + '\n').encode())
            stream.flush(); os.fsync(stream.fileno())

    def ref(self, name):
        return {'path': name, 'sha256': parent.sha((self.out/name).read_bytes())}

    def seed(self):
        original = Cleanup(self.db, CONTEXT, self.db.save, lambda event: None)
        original.prepare()
        self.db.rows = [row('windows')]
        original.capture(self.db.connect())
        case = {'case': 'missing_barrier', 'fixture_case': CONTEXT['window'],
                'expectation_pass': True, 'receipt': {'status': 'BLOCKED',
                'reason': 'cleanup_writer_barrier_required', 'deletion_proven': False}}
        self.detail = {'status': 'COMPONENT_PASS', 'preparation_run': NEW_RUN, 'cases': [case]}
        self.records = copy.deepcopy(self.db.saved)
        self.records['fixture-cleanup-component-detail.json'] = copy.deepcopy(self.detail)
        original_journal = Journal(self.out/'admission-fixture-private-journal', self.publish,
                                   'admission-fixture-journal')
        for name, value in self.records.items(): original_journal.save(name, value)
        original_journal.seal()
        self.bootstrap = {'status': 'DISPOSABLE_BOOTSTRAP_PASS', 'commit_confirmed': True,
            'registered_accounts': 3, 'existing_rows_overwritten': False,
            'after_registry_confirmed': True, 'before': {'identities': 0, 'operators': 0},
            'actor_hashes': {k: parent.sha(v.encode()) for k, v in IDS.items()}}
        self.publish('admission-fixture-bootstrap.json', self.bootstrap)
        self.publish('terminal-source.json', {'unit_test_only': True, 'worker_joined': True,
                                            'writers_closed': True, 'mint_barrier': True})
        self.terminal = {'preparation_run': NEW_RUN, 'actor_hashes': self.bootstrap['actor_hashes'],
            'fixture_case_ids': [CONTEXT['window']], 'worker_joined': True,
            'writers_closed': True, 'mint_barrier': True, 'evidence_refs': [self.ref('terminal-source.json')]}
        self.publish('terminal-barrier.json', self.terminal)
        self.barrier = self.ref('terminal-barrier.json')
        self.before = len(self.db.calls)

    def run_parent(self, contexts=None):
        with patch.dict(os.environ, ENV), patch.object(parent.NativeRuntime, 'disposable', return_value=self.db):
            return parent.run(self.gate, contexts=self.contexts if contexts is None else contexts,
                              barrier=self.barrier)

    def immutable(self):
        return {p.relative_to(self.out).as_posix(): parent.sha(p.read_bytes())
                for p in self.out.rglob('*') if p.is_file()}

    def test_known_retained_fixture_then_bootstrap_closed_without_global_pass(self):
        prior = self.immutable()
        result = self.run_parent()
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['suffix_status'], 'SCOPED_PARENT_CLOSURE_CONFIRMED')
        self.assertFalse(result['full_cleanup_proven'])
        self.assertFalse(result['original_claims_released'])
        self.assertFalse(result['auth_objects_touched'])
        self.assertEqual(result['protocol_attempts'], 22 + 11)
        self.assertEqual(result['planned_protocol_limit'], 33)
        self.assertEqual(self.db.rows, [])
        self.assertEqual(self.db.registry, {'identities': [], 'operators': []})
        self.assertTrue(self.db.cleared)
        self.assertTrue(all(parent.sha((self.out/p).read_bytes()) == h for p, h in prior.items()))
        sql_calls = self.db.calls[self.before:]
        self.assertFalse(any('delete from auth.' in text for text in sql_calls))
        self.assertEqual(sql_calls.count('COMMIT'), 2)
        flat = json.loads((self.out/'fixture-parent-closure.json').read_bytes())
        self.assertTrue(all(not isinstance(v, (dict, list)) for v in flat.values()))

    def test_missing_context_blocks_registry_and_all_dispatch(self):
        result = self.run_parent(contexts={})
        self.assertEqual(result['suffix_status'], 'PARTIAL_CLOSURE_NO_GO')
        self.assertEqual(result['protocol_attempts'], 0)
        self.assertEqual(len(self.db.calls), self.before)
        self.assertIsNone(result['registry'])
        self.assertEqual(len(self.db.registry['identities']), 3)

    def test_wrong_context_hash_cannot_be_adopted(self):
        self.contexts[CONTEXT['window']]['a'] = '78000000-0000-4000-8000-000000000099'
        result = self.run_parent()
        self.assertEqual(result['protocol_attempts'], 0)
        self.assertIn('parent_original_binding', str(result['cases']))

    def test_foreign_current_rows_block_delete_and_registry(self):
        self.db.rows = [row(n=2)]
        result = self.run_parent()
        self.assertEqual(result['suffix_status'], 'PARTIAL_CLOSURE_NO_GO')
        self.assertIsNone(result['registry'])
        self.assertFalse(any('with removed as' in s for s in self.db.calls[self.before:]))
        self.assertEqual(self.db.rows, [row(n=2)])

    def test_lost_fixture_commit_is_never_repaired_by_zero(self):
        self.db.lost_commit = True
        result = self.run_parent()
        outcome = result['cases'][0]['receipt']
        self.assertTrue(outcome['commit_unknown'])
        self.assertTrue(outcome['absence_confirmed'])
        self.assertFalse(outcome['deletion_proven'])
        self.assertIsNone(result['registry'])
        self.assertEqual(self.db.calls[self.before:].count('COMMIT'), 1)
        self.assertEqual(result['status'], 'NO_GO')

    def test_lost_registry_commit_retains_unknown_not_false_deletion(self):
        self.db.registry_lost_commit = True
        result = self.run_parent()
        self.assertTrue(result['registry']['commit_unknown'])
        self.assertTrue(result['registry']['absence_confirmed'])
        self.assertFalse(result['registry']['deletion_proven'])
        self.assertIsNone(result['registry']['deleted_identities'])
        self.assertEqual(result['suffix_status'], 'PARTIAL_CLOSURE_NO_GO')

    def test_changed_bootstrap_registry_is_not_adopted(self):
        self.db.registry['identities'][0]['provenance_sha'] = 'f' * 64
        result = self.run_parent()
        self.assertEqual(result['registry']['reason'], 'parent_bootstrap_changed_or_not_owned')
        self.assertFalse(any(s.startswith('delete from fmz6e11_private.operators')
                             for s in self.db.calls[self.before:]))

    def test_partial_registry_delete_rollback_retains_all_known_rows(self):
        self.db.registry_bad_delete = True
        original = copy.deepcopy(self.db.registry)
        result = self.run_parent()
        self.assertTrue(result['registry']['rollback_confirmed'])
        self.assertFalse(result['registry']['commit_confirmed'])
        self.assertEqual(self.db.registry, original)
        self.assertLessEqual(result['protocol_attempts'], result['planned_protocol_limit'])

    def test_rollback_error_never_claims_confirmation(self):
        self.db.registry_bad_delete = self.db.registry_rollback_error = True
        result = self.run_parent()
        self.assertFalse(result['registry']['rollback_confirmed'])
        self.assertFalse(result['registry']['deletion_proven'])
        self.assertEqual(len(self.db.registry['identities']), 3)

    def test_missing_mint_or_writer_barrier_stops_before_runtime(self):
        self.terminal['mint_barrier'] = False
        self.publish('blocked-terminal.json', self.terminal)
        self.barrier = self.ref('blocked-terminal.json')
        result = self.run_parent()
        self.assertEqual(result['reason'], 'parent_independent_terminal_barrier_required')
        self.assertEqual(result['protocol_attempts'], 0)
        self.assertEqual(len(self.db.calls), self.before)

    def test_changed_durable_receipt_blocks_before_runtime(self):
        path = self.out/'admission-fixture-private-journal/fixture-cleanup-component-detail.json'
        path.write_bytes(path.read_bytes() + b' ')
        result = self.run_parent()
        self.assertEqual(result['reason'], 'parent_receipt_changed')
        self.assertEqual(len(self.db.calls), self.before)

    def test_duplicate_invocation_cannot_replay_or_overwrite(self):
        self.run_parent(); before = len(self.db.calls)
        with self.assertRaises(FileExistsError): self.run_parent()
        self.assertEqual(len(self.db.calls), before)

    def test_predispatch_fsync_failure_sends_no_sql(self):
        real = parent.Journal.save
        def save(journal, name, value):
            if '-charge-' in name:
                with patch('admission_journal.os.fsync', side_effect=OSError('test fsync')):
                    return real(journal, name, value)
            return real(journal, name, value)
        with patch.object(parent.Journal, 'save', save), self.assertRaisesRegex(ValueError, 'journal_poisoned'):
            self.run_parent()
        self.assertEqual(len(self.db.calls), self.before)
        self.assertFalse((self.out/'fixture-parent-closure-journal-index.json').exists())

    def test_hosted_and_wrong_repository_rejected_without_private_journal(self):
        with patch.dict(os.environ, {**ENV, 'GITHUB_REPOSITORY': 'other/repo'}):
            with self.assertRaisesRegex(parent.Blocked, 'disposable'):
                parent.run(self.gate, contexts=self.contexts, barrier=self.barrier)
        self.assertFalse((self.out/'fixture-parent-closure-private').exists())

    def test_registry_templates_are_single_statements_and_no_auth_delete(self):
        from sql_protocol import statements
        for text in (parent.REGISTRY, parent.DELETE_OPERATOR, parent.DELETE_IDENTITIES, parent.REGISTRY_LOCK):
            self.assertEqual(len(statements(text)), 1)
            self.assertNotIn('auth.', text)

    def test_original_unknown_commit_and_missing_ownership_rejected(self):
        evidence = parent.Evidence(self.gate)
        case = copy.deepcopy(self.detail['cases'][0])
        case['receipt']['commit_unknown'] = True
        with self.assertRaisesRegex(parent.Blocked, 'commit_not_replayable'):
            parent.ownership(evidence, case, CONTEXT)
        case['receipt'].pop('commit_unknown')
        evidence.index['records'] = {k: v for k, v in evidence.index['records'].items() if '-writer-' not in k}
        with self.assertRaisesRegex(parent.Blocked, 'no_original_writer'):
            parent.ownership(evidence, case, CONTEXT)

    def test_original_unconfirmed_rollback_cannot_authorize_new_suffix(self):
        evidence = parent.Evidence(self.gate)
        case = copy.deepcopy(self.detail['cases'][0])
        case['case'] = 'interrupted_delete'
        case['receipt'] = {'status': 'NO_GO', 'rollback_confirmed': False}
        with self.assertRaisesRegex(parent.Blocked, 'transaction_not_closed'):
            parent.ownership(evidence, case, CONTEXT)
        case['receipt']['rollback_confirmed'] = True
        self.assertEqual(len(parent.ownership(evidence, case, CONTEXT)), 1)

    def test_original_writer_chain_is_validated_not_just_presence(self):
        evidence = parent.Evidence(self.gate)
        original_get = evidence.get
        def changed(name):
            value = original_get(name)
            if '-writer-' in name: value['previous'] = '0' * 64
            return value
        with patch.object(evidence, 'get', side_effect=changed):
            with self.assertRaisesRegex(parent.Blocked, 'writer_chain'):
                parent.ownership(evidence, self.detail['cases'][0], CONTEXT)

    def test_registry_remaining_fixture_fk_never_cascades(self):
        events, receipts = [], {}
        result = parent.close_registry(self.db, IDS, lambda n, v: receipts.update({n: v}), events.append)
        self.assertFalse(result['commit_confirmed'])
        self.assertTrue(result['rollback_confirmed'])
        self.assertFalse(result['deletion_proven'])
        self.assertEqual(len(self.db.registry['identities']), 3)
        self.assertLessEqual(len(events), parent.REGISTRY_LIMIT)

    def test_all_registry_failure_prefixes_fit_reserved_protocol_bound(self):
        # BEGIN/check/lock/before/operator/identities/COMMIT; rollback only before COMMIT.
        for failed_index in range(7):
            self.assertLessEqual(failed_index + 1 + int(failed_index < 6) + 4, parent.REGISTRY_LIMIT)


if __name__ == '__main__': unittest.main()
