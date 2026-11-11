"""Offline transport fixtures only; never a real platform/root-admission proof."""
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import install_platform as p


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = pathlib.Path(self.temp.name)
        self.program = {'outer_operations': p._operations(),
                        'unknown_atoms': [{'id': name, 'units': None} for name in p.UNKNOWN]}

    def monitor(self):
        journal = p._Journal(self.out)
        self.addCleanup(journal.close)
        plan = [{'id': 'fixture.sql', 'label': 'psql', 'channel': 'gate', 'explicit_sql_statements': 1}]
        return p._Monitor(journal, plan, lambda sql: 1), journal

    def test_outer_inventory_is_not_total_sql_or_nested_process_count(self):
        plan = p._operations()
        self.assertEqual(len(plan), 36)
        self.assertEqual(sum(row['channel'] == 'tls_process' for row in plan), 5)
        self.assertEqual(sum(row['explicit_sql_statements'] or 0 for row in plan), 13)
        self.assertEqual(len({row['id'] for row in plan}), 36)
        self.assertTrue(all(row['covered_by'] == p.COMMAND_ID for row in plan))

    def test_source_program_never_turns_inventory_into_bound(self):
        with patch.object(p, '_pins', return_value={'fixture': 'verified-in-test'}):
            result = p.source_program(self.out)
        self.assertIsNone(result['units'])
        self.assertIsNone(result['reserve_after'])
        self.assertIsNone(result['observed_sql_commands'])
        self.assertFalse(result['bound_complete'])
        self.assertFalse(result['source_inventory_complete'])
        self.assertFalse(result['release_binary_equivalence_claimed'])
        self.assertTrue(all(row['units'] is None for row in result['unknown_atoms']))

    def test_source_hash_exact_except_crlf(self):
        source = self.out / 'fixture.py'
        source.write_bytes(b'fixture\r\n')
        self.assertEqual(p._pins(self.out, {'fixture.py': p.sha(b'fixture\n')})['fixture.py']['raw_sha256'],
                         p.sha(b'fixture\r\n'))
        source.write_bytes(b'changed\n')
        with self.assertRaisesRegex(p.PlatformIncomplete, 'source_changed'):
            p._pins(self.out, {'fixture.py': p.sha(b'fixture\n')})

    def test_durable_intent_precedes_dispatch_and_contains_no_sql(self):
        monitor, journal = self.monitor()
        def execute():
            rows = [json.loads(line) for line in journal.path.read_bytes().splitlines()]
            self.assertEqual(rows[-1]['event'], 'dispatch_intent')
            self.assertEqual(rows[-1]['outcome'], 'unknown_consumed')
            return types.SimpleNamespace(returncode=0)
        sql = "select 'DO_NOT_EXPORT'"
        monitor.dispatch('gate', 'psql', execute, sql=sql)
        self.assertEqual((monitor.attempted_explicit_sql, monitor.confirmed_explicit_sql), (1, 1))
        raw = journal.path.read_bytes()
        self.assertNotIn(b'DO_NOT_EXPORT', raw)
        self.assertNotIn(sql.encode(), raw)
        rows = [json.loads(line) for line in raw.splitlines()]
        previous = '0' * 64
        for row in rows:
            self.assertEqual(row['previous_sha256'], previous)
            previous = p.sha(json.dumps(row, sort_keys=True, separators=(',', ':')).encode())

    def test_lost_response_remains_consumed_unconfirmed(self):
        monitor, journal = self.monitor()
        with self.assertRaises(OSError):
            monitor.dispatch('gate', 'psql', Mock(side_effect=OSError('lost')), sql='select 1')
        self.assertEqual((monitor.attempted_explicit_sql, monitor.confirmed_explicit_sql), (1, 0))
        self.assertEqual(len(journal.path.read_bytes().splitlines()), 1)

    def test_fsync_and_short_write_prevent_dispatch(self):
        for failure in ('fsync', 'write'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                journal = p._Journal(folder)
                monitor = p._Monitor(journal, [p._operations()[0]], lambda sql: 1)
                execute = Mock()
                try:
                    with patch.object(p.os, failure, side_effect=OSError('disk')):
                        with self.assertRaises(OSError):
                            monitor.dispatch('gate', 'pg17-parser-install', execute)
                    execute.assert_not_called()
                finally: journal.close()
        with tempfile.TemporaryDirectory() as folder:
            journal = p._Journal(folder)
            try:
                with patch.object(p.os, 'write', return_value=1), self.assertRaisesRegex(
                        p.PlatformIncomplete, 'short_write'):
                    journal.append({'event': 'test'})
            finally: journal.close()

    def test_unknown_label_channel_or_statement_count_stops_dispatch(self):
        monitor, _ = self.monitor()
        execute = Mock()
        for channel, label in [('tls_process', 'psql'), ('gate', 'new-command')]:
            with self.assertRaisesRegex(p.PlatformIncomplete, 'dispatch_order'):
                monitor.dispatch(channel, label, execute, sql='select 1')
        monitor.count_sql = lambda sql: 2
        with self.assertRaisesRegex(p.PlatformIncomplete, 'statement_shape'):
            monitor.dispatch('gate', 'psql', execute, sql='select 1;select 2')
        execute.assert_not_called()

    def fixture(self, *, dispatch_failure=None, save_failure=False):
        events = []
        tls = types.SimpleNamespace(subprocess=types.SimpleNamespace(run=Mock(
            return_value=types.SimpleNamespace(returncode=0))))
        test = self
        class Gate:
            def __init__(self): self.out = self.work = test.out; self.container = p.PG_NAME
            def save(self, name, value):
                if save_failure and name == 'case-platform-install.json': raise OSError('PRIVATE_SAVE')
                with (self.out / name).open('x') as stream: json.dump(value, stream)
            def command(self, label, args, **kwargs):
                events.append('dispatch')
                if dispatch_failure: raise dispatch_failure
                return types.SimpleNamespace(returncode=0)
            def install(self):
                for row in test.program['outer_operations']:
                    if row['label'] == 'generate':
                        tls.subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048',
                            '-nodes', '-days', '1', '-keyout', str(self.work / 'fmz-ci-server.key'),
                            '-out', str(self.work / 'fmz-ci-ca.crt'), '-subj', '/CN=localhost',
                            '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1'],
                            capture_output=True, timeout=15)
                    elif row['channel'] == 'tls_process': tls.subprocess.run(['fixture-process'])
                    else:
                        sql = 'select 1' if row['explicit_sql_statements'] else None
                        args = ['fixture-process'] if sql is None else ['docker', 'exec', '-i',
                            p.PG_NAME, 'psql', '-X', '-U',
                            'postgres' if row['label'] == 'psql' else 'supabase_admin',
                            '-d', 'postgres', '-qAt', '-v', 'ON_ERROR_STOP=1']
                        self.command(row['label'], args, sql=sql)
        gate = Gate()
        ledger = types.SimpleNamespace(precharge=Mock(side_effect=lambda command: events.append('precharge') or object()),
            unknown=Mock(), confirm=Mock())
        authority = {'command_id': p.COMMAND_ID, 'units': 'TEST_ONLY_NOT_RUNTIME_AUTHORITY'}
        return gate, ledger, tls, events, authority

    def test_successful_outer_install_still_unknown_never_confirm_thirteen(self):
        gate, ledger, tls, events, authority = self.fixture()
        original = tls.subprocess
        with patch.object(p, '_context', return_value=(self.program, authority, tls, lambda sql: 1)):
            with self.assertRaisesRegex(p.PlatformIncomplete, 'managed_startup_unobserved'):
                p.install_platform(gate, ledger=ledger)
        self.assertEqual(events[0], 'precharge')
        self.assertNotIn('command', vars(gate))
        self.assertIs(tls.subprocess, original)
        self.assertEqual(original.run.call_args_list[0].args[0][-1],
            'subjectAltName=DNS:localhost,IP:127.0.0.1,DNS:' + p.PG_NAME)
        ledger.unknown.assert_called_once()
        ledger.confirm.assert_not_called()
        receipt = json.loads((self.out / 'case-platform-install.json').read_bytes())
        self.assertEqual(receipt['outer_dispatch_attempts'], 36)
        self.assertEqual(receipt['explicit_sql_confirmed'], 13)
        self.assertIsNone(receipt['total_observed_sql_commands'])
        self.assertEqual(receipt['outcome'], 'unknown_consumed')
        self.assertFalse(receipt['hosted_admitted'])

    def test_genuine_admission_guard_failure_has_no_dispatch_or_charge(self):
        gate, ledger, tls, events, authority = self.fixture()
        with patch.object(p, '_context', side_effect=ValueError('root_incomplete')):
            with self.assertRaisesRegex(ValueError, 'root_incomplete'):
                p.install_platform(gate, ledger=ledger)
        self.assertEqual(events, [])
        ledger.precharge.assert_not_called()
        self.assertFalse((self.out / 'case-platform-dispatch.ledger.txt').exists())

    def test_precharge_failure_never_enters_installer(self):
        gate, ledger, tls, events, authority = self.fixture()
        ledger.precharge.side_effect = OSError('root journal')
        with patch.object(p, '_context', return_value=(self.program, authority, tls, lambda sql: 1)):
            with self.assertRaises(OSError): p.install_platform(gate, ledger=ledger)
        self.assertEqual(events, [])
        ledger.unknown.assert_not_called()

    def test_primary_survives_unknown_and_receipt_failures(self):
        original_error = ValueError('PRIVATE_PRIMARY')
        gate, ledger, tls, events, authority = self.fixture(dispatch_failure=original_error, save_failure=True)
        original_subprocess = tls.subprocess
        ledger.unknown.side_effect = OSError('PRIVATE_LEDGER')
        with patch.object(p, '_context', return_value=(self.program, authority, tls, lambda sql: 1)):
            with self.assertRaises(ValueError) as caught: p.install_platform(gate, ledger=ledger)
        self.assertIs(caught.exception, original_error)
        self.assertIn('platform_ledger_secondary:OSError', original_error.__notes__)
        self.assertIn('platform_receipt_secondary:OSError', original_error.__notes__)
        self.assertIs(tls.subprocess, original_subprocess)
        self.assertNotIn('command', vars(gate))
        self.assertNotIn(b'PRIVATE', (self.out / 'case-platform-dispatch.ledger.txt').read_bytes())

    def test_exclusive_journal_does_not_truncate_old_receipt(self):
        path = self.out / 'case-platform-dispatch.ledger.txt'
        path.write_bytes(b'historical')
        with self.assertRaises(FileExistsError): p._Journal(self.out)
        self.assertEqual(path.read_bytes(), b'historical')

    def test_tls_patch_rejects_other_container_or_extra_openssl_arguments(self):
        gate = types.SimpleNamespace(work=self.out, container='other')
        with self.assertRaisesRegex(p.PlatformIncomplete, 'tls_container'):
            p._tls_generate(gate, (['openssl'],), {'capture_output': True, 'timeout': 15})
        gate.container = p.PG_NAME
        with self.assertRaisesRegex(p.PlatformIncomplete, 'generate_source'):
            p._tls_generate(gate, (['openssl', '-unsafe-extra'],), {'capture_output': True, 'timeout': 15})

    def test_native_startup_options_are_bounded_without_extra_sql(self):
        gate = types.SimpleNamespace(container=p.PG_NAME)
        original = ['docker', 'exec', '-i', p.PG_NAME, 'psql', '-X', '-U', 'postgres',
                    '-d', 'postgres', '-qAt', '-v', 'ON_ERROR_STOP=1']
        actual = p._native_args(gate, 'psql', original)
        self.assertEqual(actual[2:6], ['-e', 'PGOPTIONS=-c statement_timeout=5000 -c lock_timeout=1000',
                                    '-e', 'PGCONNECT_TIMEOUT=5'])
        self.assertEqual(actual[6:], original[2:])
        with self.assertRaisesRegex(p.PlatformIncomplete, 'native_command'):
            p._native_args(gate, 'psql', [*original, '--host=outside'])


if __name__ == '__main__':
    unittest.main()
