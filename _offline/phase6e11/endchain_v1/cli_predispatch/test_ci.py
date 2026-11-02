"""Offline receipt/build/child-process checks; never creates a database client."""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fmz_predispatch_test_target', HERE / 'ci.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cli-predispatch-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.events = [
            dict(event='preregister', environment='disposable_ci', hosted_admission=False,
                 slot='final', cap=28, dry_run=True),
            dict(event='connect_attempt', id=1, tls_verify_full=True),
            dict(event='dispatch', id=1, outcome='unknown_consumed'),
            dict(event='frontend_frame', type='Q', sql_ids=[1]),
            dict(event='frontend_write_returned', type='Q'),
            dict(event='outcome', id=1, outcome='command_complete'),
            dict(event='terminal', sql_dispatches=1, confirmed_sql=1, unknown_consumed=0,
                 frontend_frames_by_type={'Q': 1}, frontend_write_returned_by_type={'Q': 1},
                 connection_attempts=1, complete=True, hosted_admission=False),
        ]

    def write(self):
        previous = '0' * 64
        lines = []
        for n, event in enumerate(self.events, 1):
            raw = json.dumps(dict(sequence=n, previous_sha256=previous, **event)).encode()
            lines.append(raw)
            previous = ci.sha(raw)
        file = self.root / 'ledger.jsonl'
        file.write_bytes(b'\n'.join(lines) + b'\n')
        return file

    def test_complete_safe_events_retained(self):
        result = ci.replay(self.write())
        self.assertEqual(result['event_count'], 7)
        self.assertEqual(len(result['events']), 7)
        self.assertEqual(result['terminal']['confirmed_sql'], 1)

    def test_unknown_is_not_refunded(self):
        self.events.pop(5)
        self.events[-1].update(confirmed_sql=0, unknown_consumed=1, complete=False)
        self.assertEqual(ci.replay(self.write())['terminal']['sql_dispatches'], 1)

    def test_cannot_turn_unknown_into_complete(self):
        self.events.pop(5)
        self.events[-1].update(confirmed_sql=0, unknown_consumed=1)
        with self.assertRaisesRegex(ValueError, 'scope_or_capacity'):
            ci.replay(self.write())

    def test_hash_chain_tamper(self):
        file = self.write()
        file.write_bytes(file.read_bytes().replace(b'"cap": 28', b'"cap": 29'))
        with self.assertRaisesRegex(ValueError, 'journal_chain'):
            ci.replay(file)

    def test_duplicate_confirmation(self):
        self.events.insert(6, self.events[5].copy())
        with self.assertRaisesRegex(ValueError, 'confirmation'):
            ci.replay(self.write())

    def test_frame_total_must_match_events(self):
        self.events[-1]['frontend_frames_by_type'] = {'Q': 2}
        with self.assertRaisesRegex(ValueError, 'totals'):
            ci.replay(self.write())

    def test_frame_requires_prepaid_identity(self):
        self.events[3]['sql_ids'] = [2]
        with self.assertRaisesRegex(ValueError, 'unpaid_frame'):
            ci.replay(self.write())

    def test_write_cannot_precede_frame(self):
        self.events[3], self.events[4] = self.events[4], self.events[3]
        with self.assertRaisesRegex(ValueError, 'unpaid_write'):
            ci.replay(self.write())

    def test_second_connection_is_rejected(self):
        self.events.insert(2, dict(event='connect_attempt', id=2, tls_verify_full=True))
        with self.assertRaisesRegex(ValueError, 'connection_count'):
            ci.replay(self.write())

    def test_hosted_admission_is_always_false(self):
        self.events[-1]['hosted_admission'] = True
        with self.assertRaisesRegex(ValueError, 'scope_or_capacity'):
            ci.replay(self.write())

    def test_slot_cannot_raise_cap(self):
        self.events[0]['cap'] = 29
        with self.assertRaisesRegex(ValueError, 'scope_or_capacity'):
            ci.replay(self.write())

    def test_slot_cannot_change_mode(self):
        self.events[0]['dry_run'] = False
        with self.assertRaisesRegex(ValueError, 'scope_or_capacity'):
            ci.replay(self.write())

    def test_terminal_must_be_last(self):
        self.events.append(dict(event='frontend_frame', type='X', sql_ids=[]))
        with self.assertRaisesRegex(ValueError, 'after_terminal'):
            ci.replay(self.write())

    def test_partial_tail_is_not_complete(self):
        file = self.write()
        file.write_bytes(file.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, 'journal_bound'):
            ci.replay(file)

    def test_duplicate_header(self):
        self.events.insert(1, self.events[0].copy())
        with self.assertRaisesRegex(ValueError, 'duplicate_header'):
            ci.replay(self.write())

    def test_no_terminal(self):
        self.events.pop()
        with self.assertRaisesRegex(ValueError, 'incomplete_journal'):
            ci.replay(self.write())

    def test_failure_prefix_is_explicitly_not_a_terminal_receipt(self):
        self.events = self.events[:5]
        result = ci.replay(self.write(), allow_incomplete=True)
        self.assertFalse(result['terminal_recorded'])
        self.assertFalse(result['terminal']['complete'])
        self.assertEqual(result['terminal']['unknown_consumed'], 1)
        self.assertEqual(result['terminal']['event'], 'incomplete_summary')

    def test_failure_mode_does_not_accept_tampered_prefix(self):
        self.events = self.events[:5]
        file = self.write()
        file.write_bytes(file.read_bytes().replace(b'"cap": 28', b'"cap": 29'))
        with self.assertRaisesRegex(ValueError, 'journal_chain'):
            ci.replay(file, allow_incomplete=True)

    def test_forged_build_manifest_cannot_drop_source_inventory(self):
        target = self.root / 'apps/cli/cli_predispatch'
        target.mkdir(parents=True)
        (target / 'build.json').write_text(json.dumps(dict(upstream_commit=ci.UPSTREAM,
            hosted_admission=False, source_before_lf={}, hook_sources={}, entry_sha256='0' * 64)))
        with self.assertRaisesRegex(ValueError, 'build_binding'):
            ci.source_binding(self.root)


class DiagnosticTests(unittest.TestCase):
    def test_known_boot_error_does_not_become_missing_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            file = pathlib.Path(temp) / 'absent.jsonl'
            receipt = {}
            with self.assertRaisesRegex(ValueError, 'cli_exit:hook_policy_validation'):
                ci.check_invocation(receipt, 1, b'error: cli_predispatch_history_policy\n', file)
            self.assertEqual(receipt['cli_exit_code'], 1)
            self.assertFalse(receipt['cli_diagnostic']['ledger_present'])
            self.assertEqual(receipt['cli_diagnostic']['reason'], 'cli_predispatch_history_policy')

    def test_unknown_output_and_secret_values_are_not_exported(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = b'postgresql://private:password@private.invalid SELECT private_payload'
            diagnostic = ci.invocation_diagnostic(7, raw, pathlib.Path(temp) / 'absent')
            self.assertEqual(diagnostic['stage'], 'cli_exit_unclassified')
            self.assertEqual(diagnostic['cli_exit_code'], 7)
            self.assertIsNone(diagnostic['reason'])
            self.assertNotIn('private', json.dumps(diagnostic))
            self.assertNotIn('password', json.dumps(diagnostic))

    def test_argument_heading_classifies_without_exporting_argument(self):
        with tempfile.TemporaryDirectory() as temp:
            diagnostic = ci.invocation_diagnostic(1, b'Error: Unknown argument: --private=secret\n', pathlib.Path(temp) / 'absent')
            self.assertEqual(diagnostic['stage'], 'cli_argument_parse')
            self.assertNotIn('secret', json.dumps(diagnostic))

    def test_zero_exit_without_ledger_remains_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = {}
            with self.assertRaisesRegex(ValueError, 'ledger_missing_after_success'):
                ci.check_invocation(receipt, 0, b'up to date', pathlib.Path(temp) / 'absent')
            self.assertEqual(receipt['cli_exit_code'], 0)


class ProcessTests(unittest.TestCase):
    def run_child(self, code, **kwargs):
        return ci.bounded([sys.executable, '-B', '-c', code], cwd=HERE, env=os.environ.copy(), **kwargs)

    def test_output_and_exit(self):
        code, output = self.run_child('print("bounded")', seconds=5)
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), b'bounded')

    def test_output_limit_terminates_child(self):
        with self.assertRaisesRegex(ValueError, 'output_limit'):
            self.run_child('print("x"*9000)', seconds=5)

    def test_timeout_terminates_child_without_retry(self):
        with self.assertRaisesRegex(ValueError, 'timeout'):
            self.run_child('import time; time.sleep(10)', seconds=.1)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cli-predispatch-inventory-')
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        self.gate = SimpleNamespace(sources=root / 'sources', work=root / 'work', out=root / 'out',
            result={'candidate_sha256': 'a' * 64, 'clean_rebuild': '47/47_PASS_LOCAL_CANDIDATE',
                    'migrations_applied': 47})
        self.gate.out.mkdir()
        (self.gate.work / 'supabase/migrations').mkdir(parents=True)
        self.sources = {}
        for n in range(47):
            prefix = 'supabase/migrations/' if n < 45 else '_offline/phase6e_server_v1/supabase/migrations/'
            name = str(n).zfill(14) + '_synthetic.sql'
            source = self.gate.sources / (prefix + name)
            source.parent.mkdir(parents=True, exist_ok=True)
            raw = b'SELECT 1;\n'
            source.write_bytes(raw)
            (self.gate.work / 'supabase/migrations' / name).write_bytes(raw)
            self.sources[prefix + name] = ci.sha(raw)
        self.manifest()

    def manifest(self):
        (self.gate.out / 'candidate.json').write_text(json.dumps(dict(sha256='a' * 64, sources=self.sources)))

    def test_exact_45_plus_2_source_inventory(self):
        files, bound = ci.migration_inventory(self.gate)
        self.assertEqual(len(files), 47)
        self.assertEqual(bound, self.sources)

    def test_working_file_tamper(self):
        next((self.gate.work / 'supabase/migrations').glob('*.sql')).write_bytes(b'SELECT 2;')
        with self.assertRaisesRegex(ValueError, 'migration_bytes'):
            ci.migration_inventory(self.gate)

    def test_missing_candidate_source(self):
        self.sources.pop(next(iter(self.sources)))
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'migration_bytes'):
            ci.migration_inventory(self.gate)

    def test_extra_migration_rejected(self):
        (self.gate.work / 'supabase/migrations/99999999999999_extra.sql').write_bytes(b'SELECT 1;')
        with self.assertRaisesRegex(ValueError, 'migration_inventory'):
            ci.migration_inventory(self.gate)

    def test_clean47_marker_is_required(self):
        self.gate.result['migrations_applied'] = 45
        with self.assertRaisesRegex(ValueError, 'clean47_required'):
            ci.migration_inventory(self.gate)

    def test_candidate_digest_must_agree(self):
        self.gate.result['candidate_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'inventory_binding'):
            ci.migration_inventory(self.gate)


class IsolationTests(unittest.TestCase):
    def test_reuses_existing_isolation_with_separate_profile_and_redacted_trace(self):
        saved = {}
        gate = SimpleNamespace(container='supabase_db_fmz-db41-ci', cli_protocol=['existing-app-receipt'],
                               save=lambda name, value: saved.update({name: value}))
        receipt = dict(complete=True, numeric_coverage={'all_protocol_visible': True})
        def existing(context, args, seconds, meter):
            self.assertEqual((args, seconds), ((), 45))
            result = meter(context, args, seconds)
            self.assertEqual(context.cli_protocol, [dict(complete=True, numeric_protocol_coverage=True)])
            context.save('cli-isolation-0.json', dict(scope='disposable', commands=8, restored=True,
                protocol=[dict(statement='known CI bootstrap command', confirmed=True)]))
            return result
        with patch.dict(sys.modules, cli_isolation=SimpleNamespace(measured=existing)):
            self.assertIs(ci.isolated(gate, receipt, lambda: receipt), receipt)
        self.assertEqual(gate.cli_protocol, ['existing-app-receipt'])
        self.assertEqual(receipt['ci_bootstrap_sql_commands'], 8)
        self.assertTrue(receipt['ci_cron_restored'])
        self.assertNotIn('known CI bootstrap command', json.dumps(saved))
        self.assertIn('cli-predispatch-cli-isolation-0.json', saved)

    def test_measurement_failure_is_not_retried(self):
        gate = SimpleNamespace(container='supabase_db_fmz-db41-ci')
        calls = []
        def measure():
            calls.append(1)
            raise RuntimeError('unknown_consumed')
        def existing(context, args, seconds, meter):
            return meter(context, args, seconds)
        with patch.dict(sys.modules, cli_isolation=SimpleNamespace(measured=existing)):
            with self.assertRaisesRegex(RuntimeError, 'unknown_consumed'):
                ci.isolated(gate, {}, measure)
        self.assertEqual(calls, [1])


if __name__ == '__main__':
    unittest.main()
