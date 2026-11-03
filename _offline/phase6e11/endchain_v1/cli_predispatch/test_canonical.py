"""Offline canonical planning and mocked runner; never invokes CLI or a DB."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from test_pending import pending, evidence

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path(os.environ.get('FMZ_CLI_TEST_SOURCE_ROOT', str(HERE.parents[3])))
ARGS = ('migration', 'up', '--local')


class CanonicalTests(unittest.TestCase):
    def setUp(self):
        temp_root = str(pathlib.Path(tempfile.gettempdir()).resolve())
        if os.name == 'nt':
            temp_root = '\\\\?\\' + temp_root
        temp = tempfile.TemporaryDirectory(prefix='cli-canonical-', dir=temp_root)
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        self.saved = {}
        self.gate = SimpleNamespace(sources=root/'sources', work=root/'work', out=root/'out',
            cli_profile='local_app', cli_protocol=[], container='supabase_db_fmz-db41-ci', serial=123,
            result=dict(commit='a'*40, candidate_sha256='b'*64, phase='migration_45', migrations_applied=44))
        self.gate.out.mkdir()
        (self.gate.work/'supabase/migrations').mkdir(parents=True)
        (self.gate.sources/'supabase/migrations').mkdir(parents=True)
        self.hashes = {}
        # Copy exact current source bytes into an owned temporary test fixture.
        files = sorted((SOURCE/'supabase/migrations').glob('*.sql'))
        self.assertEqual(len(files), 45, 'Set FMZ_CLI_TEST_SOURCE_ROOT for an isolated delivery')
        for file in files:
            raw = file.read_bytes()
            relative = 'supabase/migrations/' + file.name
            self.hashes[relative] = pending.common.sha(raw)
            (self.gate.sources/relative).write_bytes(raw)
            (self.gate.work/relative).write_bytes(raw)
        self.assertEqual(self.hashes[pending.CANONICAL], pending.CANONICAL_SHA)
        self.manifest()
        (self.gate.work/'fmz-ci-ca.crt').write_text('synthetic-ca')
        def save(name, value):
            raw = json.dumps(value, sort_keys=True, indent=2).encode()
            self.saved[name] = json.loads(raw)
            (self.gate.out/name).write_bytes(raw)
        self.gate.save = save
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, cli_meter=SimpleNamespace(source_commit=lambda r:r['commit'])).start()

    def manifest(self):
        (self.gate.out/'candidate.json').write_text(json.dumps(dict(sha256='b'*64, sources=self.hashes)))

    def plan(self):
        return pending.plan_canonical(self.gate, ARGS, self.gate.sources/pending.CANONICAL)

    def test_exact_current45_source_44_history_and_no_app_index(self):
        p = self.plan()
        self.assertEqual(len(p['files']), 45)
        self.assertEqual(len(p['expected_history_versions']), 44)
        self.assertEqual([v for v in p['expected_history_versions'] if len(v)==8], ['20260813','20260818'])
        self.assertNotIn('20261018070231', p['expected_history_versions'])
        self.assertEqual(p['target_sha256'], pending.CANONICAL_SHA)
        self.assertIsNone(p['index'])

    def test_target_cannot_be_app_migration(self):
        with self.assertRaisesRegex(ValueError, 'pending_target'):
            pending.plan_canonical(self.gate, ARGS, self.gate.sources/pending.APP/pending.FILES[0])

    def test_m45_changed_consistently_in_manifest_source_and_work_is_rejected(self):
        raw = b'BEGIN; COMMIT;\n'
        for root in (self.gate.sources, self.gate.work): (root/pending.CANONICAL).write_bytes(raw)
        self.hashes[pending.CANONICAL] = pending.common.sha(raw)
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'canonical_immutable'): self.plan()

    def test_working_m45_tamper_is_rejected(self):
        (self.gate.work/pending.CANONICAL).write_bytes(b'SELECT 1;')
        with self.assertRaisesRegex(ValueError, 'pending_bytes'): self.plan()

    def test_historical_migration_tamper_is_rejected(self):
        first = sorted(self.hashes)[0]
        (self.gate.sources/first).write_bytes(b'SELECT 1;')
        with self.assertRaisesRegex(ValueError, 'pending_bytes'): self.plan()

    def test_wrong_phase_or_count_or_existing_app_slot_is_rejected(self):
        for change in (dict(phase='local_app_schema'),dict(migrations_applied=43),dict(migrations_applied=45)):
            old = self.gate.result.copy()
            self.gate.result.update(change)
            with self.assertRaisesRegex(ValueError, 'canonical_clean44'): self.plan()
            self.gate.result = old
        self.gate.cli_protocol.append({})
        with self.assertRaisesRegex(ValueError, 'canonical_clean44'): self.plan()

    def test_extra_work_migration_is_rejected(self):
        (self.gate.work/'supabase/migrations'/pending.FILES[0]).write_bytes(b'SELECT 1;')
        with self.assertRaisesRegex(ValueError, 'pending_inventory'): self.plan()

    def test_prior_canonical_receipt_cannot_be_reused(self):
        self.gate.save(pending.CANONICAL_RECEIPT, {'complete':False})
        with self.assertRaisesRegex(ValueError, 'canonical_reuse'): self.plan()

    def exercise(self, *, fail=False, numeric=True, restore=True, compile_ok=True,
                 ledger_raw=b'{"z":1,"a":2}\n', corrupt_policy=False):
        calls = []; compiled = {}; state = {'cleared':False}
        def bounded(argv, **kwargs):
            if argv[-1]=='--version': return 0, b'1.4.1'
            if argv[:2]==['docker','port']: return 0, b'127.0.0.1:54322'
            if argv[:2]==['docker','exec']: return 0, b'synthetic-private-password'
            if argv[1].endswith('policy.cjs'):
                if not compile_ok: raise ValueError('synthetic_compile_failure')
                p = json.loads(pathlib.Path(argv[2]).read_text())
                file = pathlib.Path(p.pop('migration_paths')[0])
                self.assertEqual(pending.common.sha(file.read_bytes()), pending.CANONICAL_SHA)
                p['migrations'] = [dict(sha256=pending.CANONICAL_SHA,version='20261018070231',
                    ast_hashes=['1'*64,'2'*64])]
                compiled.update(p)
                return 0, json.dumps(p).encode()
            calls.append(argv)
            if ledger_raw is not None:
                pathlib.Path(kwargs['env']['FMZ_CLI_PREDISPATCH_LEDGER']).write_bytes(ledger_raw)
            if fail: raise ValueError('synthetic_timeout')
            if corrupt_policy:
                pathlib.Path(kwargs['env']['FMZ_CLI_PREDISPATCH_POLICY']).write_bytes(b'{}')
            return 0, b'Applied canonical migration'
        def isolated(view, receipt, measure):
            try: return measure()
            finally:
                receipt['ci_bootstrap_sql_commands'] = 8
                receipt['ci_cron_restored'] = restore
                view.save('cli-predispatch-cli-isolation-0.json', dict(commands=8,restored=restore,
                    protocol=[dict(statement_sha256='f'*64,confirmed=True)]*8))
        runtime = SimpleNamespace(clear=lambda:state.update(cleared=True))
        patch.dict(sys.modules, native_runtime=SimpleNamespace(NativeRuntime=SimpleNamespace(disposable=lambda g:runtime)),
            cli_stat_reader=SimpleNamespace(snapshot=lambda r:({'track':'top','track_utility':'on'},
                [dict(confirmed=True,protocol_commands=1)]*4),
                compare=lambda *a,**kw:dict(all_protocol_visible=numeric,temp_written=0))).start()
        patch.dict(os.environ,GITHUB_ACTIONS='true',GITHUB_REF='refs/heads/main',GITHUB_RUN_ATTEMPT='1',
            GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging',GITHUB_SHA='a'*40,
            FMZ_CLI_PREDISPATCH_UPSTREAM=str(HERE)).start()
        patch.object(pending.common,'source_binding',return_value={}).start()
        patch.object(pending.shutil,'which',return_value='bun').start()
        patch.object(pending.common,'bounded',side_effect=bounded).start()
        patch.object(pending.common,'replay',side_effect=lambda *a,**kw:evidence(compiled)).start()
        patch.object(pending.common,'isolated',side_effect=isolated).start()
        target = self.gate.sources/pending.CANONICAL
        if fail or not numeric or not restore or not compile_ok or corrupt_policy:
            expected = ('synthetic_timeout' if fail else 'synthetic_compile_failure' if not compile_ok
                        else 'pending_numeric' if not numeric else 'canonical_isolation' if not restore
                        else 'canonical_evidence_durability')
            with self.assertRaisesRegex(ValueError,expected) as caught:
                pending.run_canonical(self.gate,ARGS,target)
            self.failure = caught.exception
            returned = None
        else:
            returned = pending.run_canonical(self.gate,ARGS,target)
        final = self.gate.out/pending.CANONICAL_RECEIPT
        if final.exists(): self.saved[pending.CANONICAL_RECEIPT] = json.loads(final.read_bytes())
        self.assertEqual(self.gate.cli_protocol, [])
        self.assertEqual(self.gate.serial, 123)  # Adapter does not forge a legacy dispatch.
        self.assertEqual(self.gate.result['phase'],'migration_45')
        self.assertEqual(self.gate.result['migrations_applied'],44)
        self.assertEqual(len(calls), 1 if compile_ok else 0)
        self.assertFalse(any(name.startswith('cli-protocol-') for name in self.saved))
        self.assertNotIn('synthetic-private-password',json.dumps(self.saved))
        self.assertNotIn('synthetic-private-password',json.dumps(calls))
        with self.assertRaisesRegex(ValueError,'canonical_reuse'):
            pending.run_canonical(self.gate,ARGS,target)
        if compile_ok: self.assertTrue(state['cleared'])
        return returned

    def test_one_apply_returns_only_dedicated_hash_bound_receipt(self):
        result = self.exercise()
        self.assertEqual(result,dict(instrumented_receipt=pending.CANONICAL_RECEIPT,
            sha256=pending.common.sha((self.gate.out/pending.CANONICAL_RECEIPT).read_bytes())))
        r = self.saved[pending.CANONICAL_RECEIPT]
        self.assertTrue(r['complete'])
        self.assertTrue(r['actual_migration_execution'])
        self.assertEqual(r['policy']['cap'],64)
        self.assertEqual(r['policy']['closure_reserve'],1)
        self.assertEqual(r['observer_commands'],8)
        self.assertEqual(r['query_ms'],5000)
        self.assertEqual(r['cli_seconds'],45)
        self.assertEqual(r['invocation_id'],r['policy']['invocation_id'])
        self.assertEqual(r['isolation_receipt_sha256'],pending.common.sha((self.gate.out/pending.CANONICAL_ISOLATION).read_bytes()))
        self.assertEqual((self.gate.out/r['ledger_ref']['path']).read_bytes(),b'{"z":1,"a":2}\n')
        for field in ('ledger_ref', 'policy_ref'):
            ref = r[field]
            self.assertEqual(set(ref), {'path','sha256'})
            self.assertEqual(ref['sha256'],pending.common.sha((self.gate.out/ref['path']).read_bytes()))
        self.assertTrue(r['policy_file_unchanged'])

    def test_unknown_failure_consumes64_without_app_slot_or_retry(self):
        raw = b'{"z":1,"a":2}\n{"partial":'
        self.exercise(fail=True, ledger_raw=raw)
        r = self.saved[pending.CANONICAL_RECEIPT]
        self.assertFalse(r['complete'])
        self.assertEqual(r['reserved_sql_consumed_on_failure'],64)
        self.assertEqual((self.gate.out/r['ledger_ref']['path']).read_bytes(),raw)

    def test_missing_ledger_does_not_mask_primary_failure(self):
        self.exercise(fail=True, ledger_raw=None)
        r = self.saved[pending.CANONICAL_RECEIPT]
        self.assertFalse(r['complete'])
        self.assertEqual(r['reserved_sql_consumed_on_failure'],64)
        self.assertNotIn('ledger_ref',r)
        self.assertIn('policy_ref',r)
        self.assertEqual(r['durability_errors'],[dict(artifact='ledger',error_class='ValueError')])
        self.assertIn('durability_secondary:ledger',self.failure.__notes__[0])

    def test_modified_policy_preserves_original_bytes_and_fails_closed(self):
        self.exercise(corrupt_policy=True)
        r = self.saved[pending.CANONICAL_RECEIPT]
        self.assertFalse(r['complete'])
        self.assertFalse(r['policy_file_unchanged'])
        self.assertEqual(json.loads((self.gate.out/r['policy_ref']['path']).read_bytes()),r['policy'])
        self.assertEqual(r['reserved_sql_consumed_on_failure'],64)

    def test_numeric_failure_after_execution_remains_no_go(self):
        self.exercise(numeric=False)
        r = self.saved[pending.CANONICAL_RECEIPT]
        self.assertTrue(r['actual_migration_execution'])
        self.assertFalse(r['complete'])
        self.assertEqual(r['reserved_sql_consumed_on_failure'],64)

    def test_failed_isolation_restore_cannot_return_success(self):
        self.exercise(restore=False)
        self.assertFalse(self.saved[pending.CANONICAL_RECEIPT]['complete'])

    def test_setup_failure_is_not_retried(self):
        self.exercise(compile_ok=False)

    def test_wrong_ci_source_is_rejected_before_runtime(self):
        with patch.dict(os.environ,GITHUB_ACTIONS='true',GITHUB_REF='refs/heads/main',
                        GITHUB_RUN_ATTEMPT='1',GITHUB_SHA='c'*40):
            with patch.object(pending,'run_apply') as run:
                with self.assertRaisesRegex(ValueError,'canonical_source_scope'):
                    pending.run_canonical(self.gate,ARGS,self.gate.sources/pending.CANONICAL)
                run.assert_not_called()


class RawArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cli-raw-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.policy = self.root/'source-policy.json'
        self.policy_raw = b'{ "z": 1, "a": 2 }\r\n'
        self.policy.write_bytes(self.policy_raw)
        self.ledger = self.root/'source-ledger.jsonl'
        self.ledger_raw = b'{"z":1,"a":2}\n{"partial":'
        self.ledger.write_bytes(self.ledger_raw)
        self.out = self.root/'out'
        self.out.mkdir()
        self.gate = SimpleNamespace(out=self.out,cli_protocol=[])
        self.receipt = dict(complete=True)

    def persist(self, primary=None):
        return pending.save_canonical(self.gate,self.receipt,self.policy,self.policy_raw,self.ledger,primary)

    def test_raw_copy_is_exact_hash_bound_and_fsynced(self):
        with patch.object(pending.os,'fsync',wraps=os.fsync) as fsync:
            self.persist()
        self.assertEqual(fsync.call_count,3)
        for key, original in (('policy_ref',self.policy_raw),('ledger_ref',self.ledger_raw)):
            ref = self.receipt[key]
            self.assertEqual((self.out/ref['path']).read_bytes(),original)
            self.assertEqual(ref['sha256'],pending.common.sha(original))
        self.assertTrue(self.receipt['policy_file_unchanged'])

    def test_original_hashchain_replays_after_copy_without_reserialization(self):
        from test_ci import ReceiptTests
        fixture = ReceiptTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        source = fixture.write()
        original = source.read_bytes()
        self.ledger.write_bytes(original)
        self.persist()
        copied = self.out/self.receipt['ledger_ref']['path']
        self.assertEqual(copied.read_bytes(),original)
        self.assertEqual(pending.common.replay(copied),pending.common.replay(source))
        sorted_copy = self.root/'sorted-ledger.txt'
        sorted_copy.write_bytes(b'\n'.join(json.dumps(json.loads(line),sort_keys=True).encode()
                                        for line in original.splitlines())+b'\n')
        with self.assertRaisesRegex(ValueError,'journal_chain'): pending.common.replay(sorted_copy)

    def test_exclusive_write_never_replaces_existing_bytes(self):
        file = self.out/pending.CANONICAL_LEDGER
        file.write_bytes(b'previous-evidence')
        with self.assertRaises(FileExistsError):
            pending.exclusive_raw(self.out,file.name,self.ledger_raw,262144)
        self.assertEqual(file.read_bytes(),b'previous-evidence')

    def test_read_bounds_and_empty_failure_evidence(self):
        self.ledger.write_bytes(b'x'*262144)
        self.assertEqual(len(pending.bounded_raw(self.ledger,262144)),262144)
        with self.ledger.open('ab') as stream: stream.write(b'x')
        with self.assertRaisesRegex(ValueError,'raw_bound'): pending.bounded_raw(self.ledger,262144)
        self.ledger.write_bytes(b'')
        self.assertEqual(pending.bounded_raw(self.ledger,262144),b'')

    def test_policy_and_final_receipt_bounds(self):
        for name, limit in ((pending.CANONICAL_POLICY,16384),(pending.CANONICAL_RECEIPT,524288)):
            with self.assertRaisesRegex(ValueError,'raw_destination'):
                pending.exclusive_raw(self.out,name,b'x'*(limit+1),limit)
            self.assertFalse((self.out/name).exists())

    def test_oversized_final_receipt_keeps_raw_evidence_and_primary(self):
        self.receipt['synthetic_padding'] = 'x'*524288
        primary = ValueError('original_timeout')
        self.persist(primary)
        self.assertFalse((self.out/pending.CANONICAL_RECEIPT).exists())
        self.assertTrue((self.out/pending.CANONICAL_POLICY).is_file())
        self.assertTrue((self.out/pending.CANONICAL_LEDGER).is_file())
        self.assertIn('durability_secondary:receipt',primary.__notes__[0])

    def test_partial_write_keeps_partial_file_without_reference(self):
        real_open = pathlib.Path.open
        class ShortWriter:
            def __init__(self, stream): self.stream=stream
            def __enter__(self): return self
            def __exit__(self,*args): self.stream.close()
            def write(self,raw): return self.stream.write(raw[:3])
        def short_open(path,*args,**kwargs):
            stream = real_open(path,*args,**kwargs)
            return ShortWriter(stream) if path.name==pending.CANONICAL_LEDGER and args==('xb',) else stream
        primary = ValueError('original_timeout')
        with patch.object(pathlib.Path,'open',new=short_open): self.persist(primary)
        self.assertEqual((self.out/pending.CANONICAL_LEDGER).read_bytes(),self.ledger_raw[:3])
        self.assertNotIn('ledger_ref',self.receipt)
        self.assertFalse(self.receipt['complete'])
        self.assertEqual(self.receipt['reserved_sql_consumed_on_failure'],64)
        self.assertEqual(str(primary),'original_timeout')

    def test_copy_hash_mismatch_is_not_referenced(self):
        original = pending.bounded_raw
        def altered(path,limit):
            return b'corrupt-copy' if path.name==pending.CANONICAL_LEDGER else original(path,limit)
        with patch.object(pending,'bounded_raw',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'canonical_evidence_durability'): self.persist()
        self.assertNotIn('ledger_ref',self.receipt)
        self.assertFalse(self.receipt['complete'])

    def test_fsync_failure_is_secondary_and_no_false_reference(self):
        primary = ValueError('original_timeout')
        with patch.object(pending.os,'fsync',side_effect=OSError('synthetic-fsync')): self.persist(primary)
        self.assertNotIn('ledger_ref',self.receipt)
        self.assertNotIn('policy_ref',self.receipt)
        self.assertFalse(self.receipt['complete'])
        self.assertIn('receipt',primary.__notes__[0])

    def test_missing_policy_after_dispatch_keeps_original_copy_and_ledger(self):
        self.policy.unlink()
        with self.assertRaisesRegex(ValueError,'canonical_evidence_durability'): self.persist()
        self.assertEqual((self.out/pending.CANONICAL_POLICY).read_bytes(),self.policy_raw)
        self.assertEqual((self.out/pending.CANONICAL_LEDGER).read_bytes(),self.ledger_raw)
        self.assertFalse(self.receipt['complete'])

    def test_oversized_ledger_is_not_truncated_or_retried(self):
        self.ledger.write_bytes(b'x'*262145)
        primary = ValueError('original_timeout')
        self.persist(primary)
        self.assertFalse((self.out/pending.CANONICAL_LEDGER).exists())
        self.assertEqual(self.ledger.stat().st_size,262145)
        self.assertFalse(self.receipt['complete'])

    def test_raw_destination_must_be_direct_child(self):
        with self.assertRaisesRegex(ValueError,'raw_destination'):
            pending.exclusive_raw(self.out,'../outside.txt',b'content',100)


if __name__=='__main__': unittest.main()
