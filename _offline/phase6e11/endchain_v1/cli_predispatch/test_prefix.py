"""Prefix planning/durability regressions; no actual database or CLI process."""
import importlib.util
import json
import os
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_canonical as canonical
HERE, ARGS = canonical.HERE, canonical.ARGS

spec = importlib.util.spec_from_file_location('prefix_test_target', HERE / 'prefix.py')
prefix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prefix)


class PrefixTests(unittest.TestCase):
    def setUp(self):
        canonical.CanonicalTests.setUp(self)
        self.all_names = sorted(self.hashes)
        self.gate.result['run_id'] = '123'
        self.gate._case_stack_run_id = '129c55a7-748c-4f07-96b2-e198e08b8e04'
        patch.dict(os.environ, GITHUB_ACTIONS='true', GITHUB_REF='refs/heads/main',
            GITHUB_RUN_ATTEMPT='1', GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging',
            GITHUB_SHA='a'*40, GITHUB_RUN_ID='123').start()

    def manifest(self):
        canonical.CanonicalTests.manifest(self)

    def select(self, index):
        self.gate.result.update(phase='migration_' + str(index), migrations_applied=index-1)
        for name in self.all_names[index:]:
            path = self.gate.work / name
            if path.exists(): path.unlink()  # Owned TemporaryDirectory fixture only.

    def test_first_exact_prefix_has_no_assumed_history(self):
        self.select(1)
        value = prefix.plan(self.gate, ARGS)
        self.assertEqual(value['prefix_index'], 1)
        self.assertEqual(value['expected_history_versions'], [])
        self.assertEqual(len(value['migration_sources']), 1)

    def test_44_prefix_preserves_exact_legacy_identities(self):
        self.select(44)
        value = prefix.plan(self.gate, ARGS)
        self.assertEqual(len(value['expected_history_versions']), 43)
        self.assertEqual([v for v in value['expected_history_versions'] if len(v)==8], ['20260813','20260818'])
        self.assertEqual(value['target'].name, pathlib.PurePosixPath(self.all_names[43]).name)

    def test_changed_source_or_extra_file_rejected_before_dispatch(self):
        self.select(2)
        (self.gate.work/self.all_names[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'cli_prefix_bytes'): prefix.plan(self.gate, ARGS)

    def test_no_non_ci_project_retry_or_remote_mode(self):
        self.select(2)
        for key, value in [('GITHUB_ACTIONS','false'),('GITHUB_REPOSITORY','wrong/project'),
                           ('GITHUB_REF','refs/heads/other'),('GITHUB_RUN_ATTEMPT','2')]:
            with patch.dict(os.environ,{key:value}), self.assertRaisesRegex(ValueError,'disposable_only'):
                prefix.plan(self.gate, ARGS)
        with self.assertRaisesRegex(ValueError,'command'):
            prefix.plan(self.gate, ('db','push','--linked'))

    def test_existing_attempt_or_receipt_cannot_retry(self):
        self.select(3)
        self.gate._cli_prefix_attempts = {3}
        with self.assertRaisesRegex(ValueError,'reuse'): prefix.plan(self.gate, ARGS)
        self.gate._cli_prefix_attempts.clear()
        (self.gate.out/'cli-predispatch-prefix-3.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'reuse'): prefix.plan(self.gate, ARGS)

    def test_m45_and_bad_ordinal_rejected(self):
        for index in (0,45,46):
            self.gate.result.update(phase='migration_'+str(index),migrations_applied=index-1)
            with self.assertRaises(ValueError): prefix.plan(self.gate, ARGS)

    def test_cross_ci_run_rejected_before_dispatch(self):
        self.select(1)
        with patch.dict(os.environ,GITHUB_RUN_ID='456'), self.assertRaisesRegex(ValueError,'cli_prefix_ci_run'):
            prefix.plan(self.gate,ARGS)

    def test_reserved_case_ids_rejected_before_dispatch(self):
        self.select(1)
        for run_id in ('6f8c8909-9b79-4011-a9d1-db5e23c6b6c1','11a909f4-7113-424a-aa4b-ce9964720a3e'):
            self.gate._case_stack_run_id=run_id
            with self.subTest(run_id=run_id),self.assertRaisesRegex(ValueError,'case_run_id'):
                prefix.plan(self.gate,ARGS)

    def exercise(self, *, fail=None, nonempty=False, close_fail=False):
        executed=[]; closed=[]
        class Connection:
            def execute(_,sql):
                executed.append(sql)
                if sql==fail: raise TimeoutError('PRIVATE_SENTINEL')
                return SimpleNamespace(description=sql.startswith('SELECT'),
                    fetchall=lambda: [{'version':'unexpected'}] if nonempty else [])
            def close(_):
                closed.append(True)
                if close_fail: raise OSError('PRIVATE_CLOSE')
        runtime=SimpleNamespace(connect=lambda:Connection(),clear=lambda:None)
        with patch.dict(sys.modules,native_runtime=SimpleNamespace(
                NativeRuntime=SimpleNamespace(disposable=lambda g:runtime))):
            try: prefix.provision(self.gate)
            except Exception as error: caught=error
            else: caught=None
        receipt=json.loads((self.gate.out/'cli-prefix-history-provision.json').read_bytes())
        self.assertNotIn('PRIVATE', json.dumps(receipt))
        self.assertEqual(closed,[True])
        return executed,receipt,caught

    def test_provision_prepaid_seven_confirmations_no_implicit_zero_claim(self):
        commands, receipt, error=self.exercise()
        self.assertIsNone(error)
        self.assertEqual(commands,list(prefix.HISTORY_SETUP))
        self.assertEqual(receipt['explicit_reserve'],8)
        self.assertEqual(len(receipt['protocol']),7)
        self.assertTrue(receipt['complete'])
        self.assertFalse(receipt['implicit_driver_sql_proven'])
        for row in receipt['protocol']:
            self.assertTrue(row['confirmed'])
            self.assertTrue((self.gate.out/('cli-prefix-history-provision-'+str(row['ordinal'])+'-intent.json')).exists())

    def test_lost_commit_keeps_unknown_and_original_error_with_rollback(self):
        commands,receipt,error=self.exercise(fail='COMMIT')
        self.assertIsInstance(error,TimeoutError)
        self.assertEqual(commands[-2:],['COMMIT','ROLLBACK'])
        self.assertFalse(receipt['complete'])
        self.assertFalse(receipt['protocol'][-2]['confirmed'])
        self.assertTrue(receipt['protocol'][-1]['confirmed'])

    def test_unexpected_existing_history_rolls_back(self):
        commands,receipt,error=self.exercise(nonempty=True)
        self.assertRegex(str(error),'initial_history_not_empty')
        self.assertNotIn('COMMIT',commands)
        self.assertEqual(commands[-1],'ROLLBACK')
        self.assertFalse(receipt['complete'])

    def test_close_failure_not_promoted_to_complete(self):
        _,receipt,error=self.exercise(close_fail=True)
        self.assertRegex(str(error),'provision_closeout')
        self.assertFalse(receipt['complete'])

    def test_runtime_setup_failure_keeps_durable_failed_receipt(self):
        def unavailable(gate): raise OSError('PRIVATE_RUNTIME')
        with patch.dict(sys.modules,native_runtime=SimpleNamespace(
                NativeRuntime=SimpleNamespace(disposable=unavailable))):
            with self.assertRaises(OSError): prefix.provision(self.gate)
        raw = (self.gate.out/'cli-prefix-history-provision.json').read_text()
        receipt = json.loads(raw)
        self.assertFalse(receipt['complete'])
        self.assertEqual(receipt['protocol'], [])
        self.assertEqual(receipt['failure_class'], 'OSError')
        self.assertNotIn('PRIVATE_RUNTIME', raw)
        self.assertTrue((self.gate.out/'cli-prefix-history-provision-reserve.json').is_file())


if __name__ == '__main__': unittest.main()
