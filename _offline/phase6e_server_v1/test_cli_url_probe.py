"""Pure offline fixtures: no Docker, database, CLI execution, or network."""
import copy
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cli_url_probe as probe

PREFIX = 'FMZSQL' + 'a' * 32 + '|'


def snapshot(calls=100):
    return {'reset': 'fixed', 'dealloc': 0, 'track_utility': 'on', 'track': 'top',
            'statements': [{'queryid': 'synthetic', 'calls': calls, 'since': 'fixed',
                            'temp_written': 0, 'wal': '0'}]}


def frames(pid, texts, app=''):
    return '\n'.join(PREFIX + app + '|' + str(pid) + '|' + str(i) + '|LOG: statement: ' + text
                     for i, text in enumerate(texts, 1)) + '\n'


def capture(noise=False):
    raw = frames(101, ('SELECT 1', 'SELECT 2'), '@effect/sql-pg')
    raw += frames(102, probe.OBSERVER) + frames(103, probe.OBSERVER)
    if noise:
        raw += frames(104, probe.NOISE)
    return {'route': 'db_url', 'cli_sha256': probe.CLI_SHA256, 'prefix': PREFIX,
            'raw_log': raw, 'before': snapshot(), 'after': snapshot(108 if noise else 106),
            'cli_pid': 101, 'observer_pids': (102, 103), 'noise_pid': 104 if noise else None,
            'cli_output': b'Already up to date', 'exit_code': 0}


class CaptureTests(unittest.TestCase):
    def test_both_routes_have_exact_quiet_equality(self):
        for route in ('local', 'db_url'):
            with self.subTest(route=route):
                data = capture(); data['route'] = route
                result = probe.CliUrlProbe().analyze(**data)
                self.assertEqual(result['protocol_commands'], 2)
                self.assertEqual(result['numeric_calls_minus_reader'], 2)
                self.assertTrue(result['cli_only_equality'])
                self.assertTrue(result['controlled_total_equality'])
                self.assertEqual(result['observer_commands'], 8)
                self.assertEqual(result['observer_calls_inside_window'], 4)
                self.assertFalse(result['runtime_executed'])
                self.assertFalse(result['hosted_admission'])
                self.assertFalse(result['migration_cause_proven'])

    def test_same_role_interference_does_not_weaken_cli_equality(self):
        for route in ('local', 'db_url'):
            data = capture(True); data['route'] = route
            result = probe.CliUrlProbe().analyze(**data)
            self.assertEqual(result['numeric_calls_minus_reader'], 4)
            self.assertFalse(result['cli_only_equality'])
            self.assertTrue(result['controlled_total_equality'])
            self.assertEqual(len(result['controlled_interference_commands']), 2)
            self.assertEqual(result['protocol_commands'], 2)

    def test_unexplained_third_call_is_not_subtracted(self):
        data = capture(True); data['after'] = snapshot(109)
        result = probe.CliUrlProbe().analyze(**data)
        self.assertFalse(result['cli_only_equality'])
        self.assertFalse(result['controlled_total_equality'])

    def test_only_hashes_leave_memory(self):
        data = capture()
        data['raw_log'] = data['raw_log'].replace('statement: SELECT 1\n', "statement: SELECT 'private-marker'\n", 1)
        data['cli_output'] = b'postgresql://private-user:private-password@127.0.0.1/private-db'
        result = probe.CliUrlProbe().analyze(**data)
        exported = json.dumps(result)
        for secret in ('private-marker', 'private-password', 'private-user', 'private-db', 'SELECT', 'postgresql://'):
            self.assertNotIn(secret, exported)
        for command in result['commands']:
            self.assertEqual(set(command), {'sha256', 'kind', 'protocol_commands'})

    def test_actual_exit_failure_remains_visible(self):
        data = capture(); data['exit_code'] = 1
        result = probe.CliUrlProbe().analyze(**data)
        self.assertEqual(result['exit_code'], 1)
        self.assertNotIn('status', result)
        self.assertFalse(result['hosted_admission'])

    def test_dry_run_templates_and_bounds(self):
        self.assertEqual(probe.argument_template('local'), ['db', 'push', '--local', '--dry-run', '--skip-vault'])
        self.assertEqual(probe.argument_template('db_url'), ['db', 'push', '--db-url', '<private-loopback-tls-url>',
                         '--skip-vault', '--yes', '--output-format', 'json', '--dry-run'])
        self.assertNotIn('jit=', probe.URL_OPTIONS)
        self.assertIn('default_transaction_read_only=on', probe.URL_OPTIONS)
        self.assertIn('statement_timeout=5000', probe.URL_OPTIONS)
        self.assertIn('lock_timeout=1000', probe.URL_OPTIONS)
        self.assertEqual((probe.CLI_SECONDS, probe.QUERY_MS, probe.MAX_OUTPUT), (45, 5000, 8192))

    def test_pinned_binary_route_and_pid_guards(self):
        for changes in ({'cli_sha256': '0' * 64}, {'route': 'hosted'}, {'observer_pids': (102, 102)},
                        {'cli_pid': 102}, {'cli_pid': '101'}, {'noise_pid': 103}, {'observer_pids': (102,)}):
            with self.subTest(changes=changes):
                data = capture(); data.update(changes)
                with self.assertRaises(ValueError): probe.CliUrlProbe().analyze(**data)

    def test_prefix_cannot_be_reused(self):
        analyzer = probe.CliUrlProbe(); analyzer.analyze(**capture())
        with self.assertRaisesRegex(ValueError, 'probe_reused_invocation'): analyzer.analyze(**capture())

    def test_other_invocation_is_excluded(self):
        data = capture()
        data['raw_log'] += frames(901, ('SELECT 999',), '@effect/sql-pg').replace(PREFIX, 'FMZSQL' + 'b' * 32 + '|')
        self.assertEqual(probe.CliUrlProbe().analyze(**data)['protocol_commands'], 2)

    def test_unknown_sessions_and_apps_fail_closed(self):
        for raw in (capture()['raw_log'] + frames(999, ('SELECT 1',), '@effect/sql-pg'),
                    capture()['raw_log'].replace('@effect/sql-pg', 'unbound-client')):
            data = capture(); data['raw_log'] = raw
            with self.assertRaisesRegex(ValueError, '^probe_capture_incomplete$'): probe.CliUrlProbe().analyze(**data)

    def test_observer_and_noise_protocol_are_bound(self):
        for raw in (capture(True)['raw_log'].replace(probe.NOISE[1], 'SELECT 3 AS cli_probe_noise'),
                    capture(True)['raw_log'].replace('ROLLBACK', 'COMMIT')):
            data = capture(True); data['raw_log'] = raw
            with self.assertRaisesRegex(ValueError, '^probe_capture_incomplete$'): probe.CliUrlProbe().analyze(**data)

    def test_log_frames_parser_errors_and_budgets_are_sanitized(self):
        for change in ({'raw_log': PREFIX + 'broken'}, {'prefix': 'invalid'},
                       {'raw_log': 'x' * (probe.MAX_LOG + 1)},
                       {'cli_output': b'x' * (probe.MAX_OUTPUT + 1)},
                       {'raw_log': capture()['raw_log'].replace('statement: SELECT 1\n', 'statement: INVALID private-marker\n', 1)},
                       {'raw_log': capture()['raw_log'].replace('statement: SELECT 1\n', "statement: SELECT '" + 'x' * probe.MAX_OUTPUT + "'\n", 1)},
                       {'raw_log': capture()['raw_log'].replace('|101|2|', '|101|1|')}):
            data = capture(); data.update(change)
            with self.assertRaises(ValueError) as caught: probe.CliUrlProbe().analyze(**data)
            self.assertNotIn('private-marker', str(caught.exception))
            self.assertNotIn('SELECT', str(caught.exception))

    def test_reset_decrease_and_utility_off_are_not_accepted(self):
        for change in ({'reset': 'changed'}, {'dealloc': 1}, {'track_utility': 'off'},
                       {'statements': []}, {'statements': snapshot(99)['statements']}):
            data = capture(); data['after'].update(change)
            with self.assertRaisesRegex(ValueError, '^probe_capture_incomplete$'): probe.CliUrlProbe().analyze(**data)

    def test_temp_writes_are_not_hidden(self):
        data = capture(); data['after']['statements'][0]['temp_written'] = 1
        self.assertEqual(probe.CliUrlProbe().analyze(**data)['temp_written'], 1)


class SavedReceiptTests(unittest.TestCase):
    def fixtures(self):
        before = {'stats': snapshot(), 'commands': [{'confirmed': True}] * 4}
        after = {'stats': snapshot(120), 'commands': [{'confirmed': True}] * 4}
        stored = probe.compare(before['stats'], after['stats'], 14, between=3)
        ci = probe.compare(snapshot(), snapshot(118), 14, between=3)
        return {'hosted-cli-before-0.json': before, 'hosted-cli-after-0.json': after,
                'cli-protocol-0.json': {'cli_sha256': probe.CLI_SHA256, 'protocol_commands': 14,
                                      'complete': True, 'numeric_protocol_coverage': True},
                'cli-numeric-coverage-0.json': {'hosted': stored, 'ci': ci}}

    def run_fixture(self, files):
        def read(folder, name):
            return files[name][folder] if name == 'cli-numeric-coverage-0.json' else files[name]
        with patch.object(probe, '_read', side_effect=read):
            return probe.replay_saved('hosted', 'ci')

    def test_exact_historical_shape_keeps_cause_unknown(self):
        result = self.run_fixture(self.fixtures())
        self.assertEqual((result['hosted_raw_calls'], result['hosted_net_calls']), (20, 16))
        self.assertEqual((result['ci_raw_calls'], result['ci_net_calls']), (18, 14))
        self.assertFalse(result['hosted_exact_equality'])
        self.assertFalse(result['migration_cause_proven'])
        self.assertFalse(result['hosted_admission'])
        self.assertNotIn('statements', result)

    def test_changed_incomplete_or_unpinned_receipts_fail(self):
        for mutation in ('changed', 'observer', 'ci_incomplete', 'pin'):
            files = self.fixtures()
            if mutation == 'changed': files['cli-numeric-coverage-0.json']['hosted']['numeric_calls_minus_reader'] = 14
            if mutation == 'observer': files['hosted-cli-after-0.json']['commands'][0]['confirmed'] = False
            if mutation == 'ci_incomplete': files['cli-protocol-0.json']['complete'] = False
            if mutation == 'pin': files['cli-protocol-0.json']['cli_sha256'] = '0' * 64
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): self.run_fixture(files)


if __name__ == '__main__':
    unittest.main()
