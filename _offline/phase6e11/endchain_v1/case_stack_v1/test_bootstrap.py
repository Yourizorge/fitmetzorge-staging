"""Fake-driver orchestration tests only; no actual PG/CLI/browser/Auth proof."""
import ast
import contextlib
import hashlib
import importlib
import importlib.util
import json
import io
import os
import pathlib
import re
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get('FMZ_CASE_STACK_SOURCE', HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))
b = importlib.import_module('case_stack_v1.bootstrap')
REAL_DEPENDENCIES = b._dependencies
spec = importlib.util.spec_from_file_location('case_stack_real_ci_profile',
    ROOT / '_offline/phase6e_server_v1/ci_profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)
meter_tree = ast.parse((ROOT / '_offline/phase6e11/endchain_v1/cli_meter.py').read_text())
meter_function = next(n for n in meter_tree.body if isinstance(n, ast.FunctionDef)
                      and n.name == 'source_commit')
meter_scope = {'re': re}
exec(compile(ast.Module(body=[meter_function], type_ignores=[]), '<real-source-commit>', 'exec'), meter_scope)
meter = types.SimpleNamespace(source_commit=meter_scope['source_commit'])
MIGRATIONS = sorted(['supabase/migrations/' + v + '_fixture.sql' for v in
                    ['20260813', '20260818'] + ['20260901%06d' % i for i in range(42)]] +
                   ['supabase/migrations/' + profile.QUOTA])


class FakeGate:
    def __init__(self, root):
        self.sources, self.work, self.out = [root / name for name in ('sources', 'work', 'out')]
        for folder in (self.sources, self.work, self.out):
            folder.mkdir()
        (self.work / 'supabase/migrations').mkdir(parents=True)
        (self.work / 'fmz-ci-ca.crt').write_bytes(b'-----BEGIN CERTIFICATE-----\nfixture')
        self.container = b.CONTAINER
        self.cli_profile, self.cli_namespace = 'local_app', ''
        self.serial, self.calls, self.history, self.native = 0, [], [], []
        self.cli_protocol = []
        self.closed = self.cleared = 0
        self.failure = None
        self.dry_output = 'Database is up to date'
        self.meta_override, self.empty_override = {}, {}
        self.fail_metadata = self.fail_close = self.fail_rollback = False
        self.fail_begin = self.fail_clear = self.fail_connect = False
        self.container_change = False
        self.pg = {'id': 'a'*64, 'image_id': b.IMAGE_ID, 'image': 'public.ecr.aws/' + b.IMAGE,
                   'running': True}
        self.result = {'commit': 'b'*40, 'candidate_sha256': 'c'*64, 'run_id': '123456789',
            'migrations_applied': 0, 'platform': {'image_id': b.IMAGE_ID,
                'image': self.pg['image'], 'repository_digests': [b.IMAGES[self.pg['image']]],
                'server': [{'num': '170006'}]}}
        self.save('platform.json', self.result['platform'])
        self.save('integral-local-tls.json', {'mode': 'verify-full'})
        files = {}
        for name in b.SOURCES:
            path = self.sources / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((HERE / pathlib.PurePosixPath(name).name).read_bytes())
            files[name] = b.sha(path.read_bytes())
        for name in MIGRATIONS + ['_offline/phase6e_server_v1/supabase/migrations/' + name
                                  for name in (profile.M45, profile.M46)]:
            path = self.sources / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'-- fake-driver fixture; no SQL executed\n')
            files[name] = b.sha(path.read_bytes())
        self.save('candidate.json', {'sha256': 'c'*64, 'sources': files})

    def save(self, name, value):
        with (self.out / name).open('x') as stream:
            json.dump(value, stream, sort_keys=True)

    def rows(self, text):
        if text != b.HISTORY:
            raise AssertionError('unregistered query')
        return [{'version': v} for v in sorted(self.history)]

    def command(self, label, args, **kwargs):
        self.serial += 1
        self.calls.append(('command', label, args, kwargs))
        if label.startswith('case-stack-container-'):
            pg = dict(self.pg)
            if self.container_change and label.endswith('after'):
                pg['id'] = 'd'*64
            output = json.dumps(pg)
        elif label == 'case-stack-system-identifier':
            if kwargs != {'sql': b.CONTROL_SQL, 'timeout': 5}:
                raise AssertionError('admin batch changed')
            output = '7399999999999999999\n'
        else:
            raise AssertionError('unexpected external command')
        self.save('%03d-%s.json' % (self.serial, label), {'exitcode': 0})
        return types.SimpleNamespace(stdout=output, returncode=0, stderr='')

    def cli(self, *args, timeout):
        phase = self.result['phase']
        self.calls.append(('cli', phase, args, timeout))
        if self.failure == phase:
            raise RuntimeError('PRIVATE_SENTINEL')
        if re.fullmatch('migration_[0-9]+', phase):
            index = int(phase.split('_')[1])
            self.history.append(pathlib.PurePosixPath(MIGRATIONS[index-1]).name.split('_')[0])
            if index == 45:
                self.save('cli-predispatch-canonical-45.json', {'complete': True})
                self.save('migration-boundary-post.json', {'complete': True})
            return types.SimpleNamespace(returncode=0, stdout='', stderr='')
        index = len(self.cli_protocol)
        actual = profile.cli_arguments(args, phase, index)
        if index in (0, 2):
            name = (profile.M45, profile.M46)[index // 2]
            if (self.work / 'supabase/migrations' / name).read_bytes() != (
                    self.sources / '_offline/phase6e_server_v1/supabase/migrations' / name).read_bytes():
                raise AssertionError('migration copy changed')
            self.history.append(name.split('_')[0])
        receipt = {'profile': 'local_app', 'complete': True, 'numeric_protocol_coverage': True,
            'exitcode': 0, 'arguments': list(actual), 'dry_run': index in (1, 3),
            'commands': [{'protocol_commands': 1}], 'protocol_commands': 1,
            'observer_commands': [{'confirmed': True, 'protocol_commands': 1} for _ in range(8)],
            'slot': 'app_' + str(index)}
        self.cli_protocol.append(receipt)
        self.save('cli-protocol-' + str(index) + '.json', receipt)
        return types.SimpleNamespace(returncode=0, stdout=self.dry_output, stderr='')

    def bind_modules(self, *modules):
        if not all(isinstance(module, types.ModuleType) for module in modules):
            raise AssertionError('bound modules required')


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.g = g = FakeGate(pathlib.Path(self.temp.name))
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_RUN_ID': '123456789',
            'GITHUB_SHA': 'b'*40, 'CANDIDATE_SHA256': 'c'*64, 'GITHUB_WORKSPACE': str(g.sources)}).start()

        class Connection:
            def execute(self, text):
                g.native.append(text)
                if text == 'BEGIN READ ONLY' and g.fail_begin:
                    raise RuntimeError('PRIVATE_BEGIN_RESPONSE_LOST')
                if text == b.META:
                    if g.fail_metadata:
                        raise RuntimeError('PRIVATE_METADATA_SENTINEL')
                    value = {'database': 'postgres', 'role': 'postgres', 'version': '170006',
                        'statement_timeout': '5s', 'lock_timeout': '1s', 'readonly': 'on', 'ssl': True,
                        'database_oid': 5, 'app_absent': not g.history, 'public_empty': not g.history}
                    value.update(g.meta_override)
                    return types.SimpleNamespace(fetchall=lambda: [value])
                if text == b.EMPTY:
                    value = {'runs_empty': True, 'steps_empty': True, 'evidence_empty': True}
                    value.update(g.empty_override)
                    return types.SimpleNamespace(fetchall=lambda: [value])
                if text not in ('BEGIN READ ONLY', 'ROLLBACK'):
                    raise AssertionError('unexpected native SQL')
                if text == 'ROLLBACK' and g.fail_rollback:
                    raise RuntimeError('rollback_failure')
            def close(self):
                g.closed += 1
                if g.fail_close:
                    raise OSError('PRIVATE_CLOSE_SENTINEL')

        class Runtime:
            @classmethod
            def disposable(cls, gate):
                assert gate is g
                return cls()
            def connect(self):
                if g.fail_connect:
                    raise RuntimeError('PRIVATE_CONNECT_SENTINEL')
                return Connection()
            def clear(self):
                g.cleared += 1
                if g.fail_clear:
                    raise ValueError('PRIVATE_CLEAR_SENTINEL')

        class Base:
            @staticmethod
            def rebuild(gate, migrations):
                for index, name in enumerate(migrations, 1):
                    (gate.work / 'supabase/migrations' / pathlib.PurePosixPath(name).name).write_bytes(
                        (gate.sources / name).read_bytes())
                    gate.result['phase'] = 'migration_' + str(index)
                    gate.cli('migration', 'up', '--local', timeout=120)
                    gate.result['migrations_applied'] = index

        self.bindings = []
        def verify(*args):
            self.bindings.append(args)
            return {'status': 'FAKE_DRIVER_SOURCE_CHECK'}
        self.deps = (types.SimpleNamespace(base=types.SimpleNamespace(Gate=Base)),
            profile, meter, types.SimpleNamespace(verify_all=verify), Runtime)
        patch.object(b, '_dependencies', return_value=self.deps).start()

    def run_stack(self):
        return b.bootstrap(self.g, MIGRATIONS)

    def test_complete_sequence_real_profile_contracts_and_pg_only_receipt(self):
        r = self.run_stack()
        cli = [x for x in self.g.calls if x[0] == 'cli']
        self.assertEqual(len(cli), 49)
        self.assertEqual([x[1] for x in cli[:45]], ['migration_'+str(i) for i in range(1, 46)])
        self.assertEqual([x[1] for x in cli[45:]],
                         ['local_app_schema', 'local_app_schema', 'local_app_outbox', 'advisors_and_dryrun'])
        self.assertEqual([x[3] for x in cli[45:]], [45]*4)
        self.assertEqual(r['cli_slots'], ['app_'+str(i) for i in range(4)])
        self.assertEqual(len(r['history']), 47)
        self.assertEqual(len(r['native_commands']), 7)
        self.assertTrue(all(x['confirmed'] for x in r['native_commands']))
        self.assertEqual(r['admin_sql_reserved'], 5)
        self.assertEqual(r['additional_sql_dispatch_max'], 15)
        self.assertEqual(len(r['history_commands']), 3)
        self.assertIsNone(r['bootstrap_total_sql_commands'])
        self.assertFalse(r['auth_database_bound'])
        for key in ('hosted_admission', 'full_chain_admission', 'quota_applied', 'claim_created',
                    'database_reset', 'app_suite_repeated'):
            self.assertFalse(r[key])
        self.assertEqual((self.g.closed, self.g.cleared), (2, 2))
        self.assertEqual(len(self.bindings), 2)
        for ref in r['evidence_refs']:
            raw = (self.g.out / ref['path']).read_bytes()
            self.assertEqual((ref['sha256'], ref['bytes']), (b.sha(raw), len(raw)))
        manifest = json.loads((self.g.out / 'candidate.json').read_bytes())['sources']
        self.assertEqual(r['migration_sources'], {name: manifest[name] for name in
            MIGRATIONS + ['_offline/phase6e_server_v1/supabase/migrations/' + name
                          for name in (profile.M45, profile.M46)]})
        self.assertEqual(len(r['migration_sources']), 47)

    def test_same_gate_cannot_be_reused_or_claim_erased(self):
        self.run_stack()
        before = list(self.g.calls)
        with self.assertRaisesRegex(b.StackStop, 'reuse'):
            self.run_stack()
        self.assertEqual(self.g.calls, before)

    def test_existing_disk_attempt_blocks_fresh_python_object(self):
        self.g.save('case-stack-attempt.json', {})
        with self.assertRaisesRegex(b.StackStop, 'reuse'):
            self.run_stack()
        self.assertFalse(self.g.calls)

    def test_preexisting_cli_or_migration_state_is_rejected(self):
        for key, value in [('migrations_applied', 1), ('migrations_applied', True)]:
            self.g.result[key] = value
            with self.assertRaisesRegex(b.StackStop, 'already_started'):
                self.run_stack()
        self.assertFalse(self.g.calls)

    def test_wrong_container_and_profile_cannot_dispatch(self):
        self.g.container = 'other'
        with self.assertRaisesRegex(b.StackStop, 'target'):
            self.run_stack()
        self.g.container = b.CONTAINER
        self.g.cli_profile = 'endchain'
        with self.assertRaisesRegex(b.StackStop, 'target'):
            self.run_stack()
        self.assertFalse(self.g.calls)

    def test_ambient_ci_mismatch_stops_before_native_or_cli(self):
        for key, value in [('GITHUB_ACTIONS', 'false'), ('GITHUB_REF', 'refs/heads/other'),
                           ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_RUN_ID', '999'),
                           ('GITHUB_SHA', 'd'*40), ('CANDIDATE_SHA256', 'd'*64)]:
            with self.subTest(key=key), patch.dict(os.environ, {key: value}), self.assertRaises(b.StackStop):
                self.run_stack()
        self.assertFalse(self.g.calls)
        self.assertFalse(self.g.native)

    def test_source_commit_conflict_is_not_fallback(self):
        self.g.result['head'] = 'd'*40
        with self.assertRaisesRegex(ValueError, 'source_conflict'):
            self.run_stack()
        self.assertFalse(self.g.calls)

    def test_tampered_migration_fails_before_dispatch(self):
        (self.g.sources / MIGRATIONS[0]).write_bytes(b'tampered')
        with self.assertRaisesRegex(b.StackStop, 'source_hash'):
            self.run_stack()
        self.assertFalse(self.g.calls)

    def test_missing_bootstrap_source_is_not_implicitly_admitted(self):
        path = self.g.out / 'candidate.json'
        value = json.loads(path.read_bytes())
        del value['sources'][b.SOURCES[0]]
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(b.StackStop, 'sources_missing'):
            self.run_stack()
        self.assertFalse(self.g.calls)

    def test_populated_migration_directory_is_not_reset(self):
        path = self.g.work / 'supabase/migrations/prior.sql'
        path.write_bytes(b'prior')
        with self.assertRaisesRegex(b.StackStop, 'migration_directory'):
            self.run_stack()
        self.assertEqual(path.read_bytes(), b'prior')
        self.assertFalse(self.g.calls)

    def test_wrong_live_image_stops_before_rebuild(self):
        self.g.pg['image_id'] = 'sha256:'+'d'*64
        with self.assertRaisesRegex(b.StackStop, 'container_image'):
            self.run_stack()
        self.assertEqual(len(self.g.calls), 1)

    def test_wrong_platform_digest_fails_before_rebuild(self):
        self.g.result['platform']['repository_digests'] = ['wrong']
        with self.assertRaisesRegex(b.StackStop, 'platform_binding'):
            self.run_stack()
        self.assertEqual(len(self.g.calls), 1)

    def test_tls_database_version_and_freshness_fail_closed(self):
        for index, override in enumerate(({'ssl': False}, {'database': 'other'}, {'version': '170005'},
                         {'statement_timeout': '30s'}, {'app_absent': False},
                         {'public_empty': False}, {'database_oid': True})):
            with self.subTest(override=override):
                trace = []
                self.g.meta_override = override
                with self.assertRaises(b.StackStop):
                    b._sample(self.g, self.deps[-1], trace, 'before_' + str(index), fresh=True)
                self.assertEqual(trace[-1]['command'], 'rollback')
                self.assertTrue(trace[-1]['confirmed'])

    def test_real_registry_must_be_empty_after_bootstrap(self):
        self.g.empty_override = {'runs_empty': False}
        with self.assertRaisesRegex(b.StackStop, 'registry_not_empty'):
            self.run_stack()
        self.assertFalse((self.g.out / 'case-stack-bootstrap.json').exists())

    def test_cli_failure_stops_once_preserves_failure_without_private_message(self):
        self.g.failure = 'local_app_schema'
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_SENTINEL'):
            self.run_stack()
        self.assertEqual(len([x for x in self.g.calls if x[:2] == ('cli', 'local_app_schema')]), 1)
        failure = (self.g.out / 'case-stack-failure.json').read_text()
        self.assertNotIn('PRIVATE', failure)
        self.assertEqual(json.loads(failure)['stage'], 'app46')
        with self.assertRaisesRegex(b.StackStop, 'reuse'):
            self.run_stack()

    def test_nonempty_or_ambiguous_dry_output_stops_before_app47(self):
        self.g.dry_output = 'up to date; would be pushing 20261014160019_phase6e_local_outbox.sql'
        with self.assertRaisesRegex(b.StackStop, 'dry_not_empty'):
            self.run_stack()
        self.assertFalse(any(x[:2] == ('cli', 'local_app_outbox') for x in self.g.calls))

    def test_native_failure_not_masked_by_close_or_rollback(self):
        self.g.fail_metadata = self.g.fail_close = self.g.fail_rollback = True
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_METADATA_SENTINEL'):
            self.run_stack()
        failure = json.loads((self.g.out / 'case-stack-failure.json').read_bytes())
        self.assertFalse(failure['native_commands'][-1]['confirmed'])
        self.assertEqual([x['stage'] for x in self.g.result['case_stack_secondary']],
                         ['native_rollback', 'native_close'])

    def test_lost_begin_response_rolls_back_and_keeps_first_error(self):
        self.g.fail_begin = self.g.fail_rollback = self.g.fail_close = self.g.fail_clear = True
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_BEGIN_RESPONSE_LOST'):
            self.run_stack()
        self.assertEqual(self.g.native, ['BEGIN READ ONLY', 'ROLLBACK'])
        self.assertEqual((self.g.closed, self.g.cleared), (1, 1))
        failure = json.loads((self.g.out / 'case-stack-failure.json').read_bytes())
        self.assertFalse(any(x['confirmed'] for x in failure['native_commands']))
        self.assertEqual(failure['additional_sql_prepaid'], 15)
        self.assertEqual([x['stage'] for x in self.g.result['case_stack_secondary']],
                         ['native_rollback', 'native_close', 'runtime_clear'])

    def test_close_failure_wins_clear_and_clear_alone_is_failure(self):
        self.g.fail_close = self.g.fail_clear = True
        with self.assertRaisesRegex(OSError, 'PRIVATE_CLOSE_SENTINEL'):
            b._sample(self.g, self.deps[-1], [], 'close_case', fresh=True)
        self.g.fail_close = False
        with self.assertRaisesRegex(ValueError, 'PRIVATE_CLEAR_SENTINEL'):
            b._sample(self.g, self.deps[-1], [], 'clear_case', fresh=True)
        self.assertEqual((self.g.closed, self.g.cleared), (2, 2))

    def test_connect_failure_wins_clear_without_spurious_rollback(self):
        self.g.fail_connect = self.g.fail_clear = True
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_CONNECT_SENTINEL'):
            self.run_stack()
        self.assertFalse(self.g.native)
        self.assertEqual((self.g.closed, self.g.cleared), (0, 1))

    def test_durable_fixed_reservation_and_intent_precede_every_native_dispatch(self):
        runtime = self.deps[-1]
        connect = runtime.connect
        def connected(instance):
            connection = connect(instance)
            execute = connection.execute
            def observed(text):
                stage = 'before' if not self.g.history else 'after'
                label = {'BEGIN READ ONLY': 'begin_read_only', b.META: 'metadata',
                         b.EMPTY: 'registry_empty', 'ROLLBACK': 'rollback'}[text]
                prepaid = json.loads((self.g.out / 'case-stack-attempt.json').read_bytes())
                self.assertEqual(prepaid['additional_sql_prepaid'], 15)
                intent = json.loads((self.g.out / ('case-stack-native-' + stage + '-' + label +
                                                   '-intent.json')).read_bytes())
                ref = intent['reservation_ref']
                raw = (self.g.out / ref['path']).read_bytes()
                self.assertEqual(b.sha(raw), ref['sha256'])
                self.assertIn('rollback', json.loads(raw)['commands'])
                self.assertFalse(intent['confirmed'])
                return execute(text)
            connection.execute = observed
            return connection
        with patch.object(runtime, 'connect', connected):
            self.run_stack()

    def test_reservation_fsync_failure_dispatches_nothing(self):
        with patch.object(b.os, 'fsync', side_effect=OSError('durability')), \
             self.assertRaisesRegex(OSError, 'durability'):
            self.run_stack()
        self.assertFalse(self.g.native)
        self.assertFalse(self.g.calls)
        self.assertTrue((self.g.out / 'case-stack-attempt.json').exists())
        with self.assertRaisesRegex(b.StackStop, 'reuse'):
            self.run_stack()

    def test_failed_metadata_intent_never_queries_and_still_rolls_back(self):
        durable = b._durable
        def fail(gate, name, value):
            if name.endswith('metadata-intent.json'):
                raise OSError('intent_primary')
            return durable(gate, name, value)
        with patch.object(b, '_durable', side_effect=fail), \
             self.assertRaisesRegex(OSError, 'intent_primary'):
            self.run_stack()
        self.assertEqual(self.g.native, ['BEGIN READ ONLY', 'ROLLBACK'])

    def test_failed_rollback_intent_uses_already_durable_exact_slot_no_pass(self):
        durable = b._durable
        def fail(gate, name, value):
            if name.endswith('rollback-intent.json'):
                raise OSError('rollback_intent_failure')
            return durable(gate, name, value)
        with patch.object(b, '_durable', side_effect=fail), \
             self.assertRaisesRegex(OSError, 'rollback_intent_failure'):
            self.run_stack()
        self.assertEqual(self.g.native[-1], 'ROLLBACK')
        reservation = json.loads((self.g.out / 'case-stack-reserve-native-before.json').read_bytes())
        self.assertEqual(reservation['commands'], ['begin_read_only', 'metadata', 'rollback'])
        self.assertFalse((self.g.out / 'case-stack-bootstrap.json').exists())

    def test_history_and_admin_reservations_exist_before_transport(self):
        rows, command = self.g.rows, self.g.command
        def observed_rows(text):
            stage = {45: 'canonical', 46: 'minimal', 47: 'complete'}[len(self.g.history)]
            value = json.loads((self.g.out / ('case-stack-reserve-history-' + stage + '.json')).read_bytes())
            self.assertEqual(value['reserved'], 1)
            return rows(text)
        def observed_command(label, *args, **kwargs):
            if label == 'case-stack-system-identifier':
                value = json.loads((self.g.out / 'case-stack-reserve-admin-system_identifier.json').read_bytes())
                self.assertEqual(value['reserved'], 5)
                self.assertTrue(value['no_refund'])
            return command(label, *args, **kwargs)
        self.g.rows, self.g.command = observed_rows, observed_command
        self.run_stack()

    def test_rollback_dispatch_failure_cannot_mask_earlier_intent_failure(self):
        durable = b._durable
        primary = OSError('PRIVATE_ROLLBACK_INTENT_FIRST')
        def fail(gate, name, value):
            if name.endswith('rollback-intent.json'):
                raise primary
            return durable(gate, name, value)
        self.g.fail_rollback = self.g.fail_close = self.g.fail_clear = True
        with patch.object(b, '_durable', side_effect=fail), self.assertRaises(OSError) as caught:
            self.run_stack()
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.g.native.count('ROLLBACK'), 1)
        self.assertFalse((self.g.out / 'case-stack-bootstrap.json').exists())
        self.assertIn('rollback_dispatch', [v['stage'] for v in self.g.result['case_stack_secondary']])

    def test_query_failure_stays_primary_over_intent_dispatch_and_clear_failures(self):
        durable = b._durable
        def fail(gate, name, value):
            if name.endswith('rollback-intent.json'):
                raise OSError('PRIVATE_ROLLBACK_INTENT_SECOND')
            return durable(gate, name, value)
        self.g.fail_metadata = self.g.fail_rollback = self.g.fail_clear = True
        with patch.object(b, '_durable', side_effect=fail), \
             self.assertRaisesRegex(RuntimeError, 'PRIVATE_METADATA_SENTINEL'):
            self.run_stack()
        self.assertEqual(self.g.native.count('ROLLBACK'), 1)

    def test_container_replacement_cannot_pass(self):
        self.g.container_change = True
        with self.assertRaisesRegex(b.StackStop, 'target_changed'):
            self.run_stack()

    def test_history_order_and_missing_version_are_checked(self):
        original = self.g.rows
        self.g.rows = lambda text: original(text)[:-1]
        with self.assertRaisesRegex(ValueError, 'history_identity'):
            self.run_stack()
        self.assertEqual(len([x for x in self.g.calls if x[0] == 'cli']), 45)

    def test_failed_durable_failure_receipt_does_not_mask_primary(self):
        save = self.g.save
        def fail(name, value):
            if name == 'case-stack-failure.json':
                raise OSError('secondary')
            return save(name, value)
        self.g.save = fail
        self.g.failure = 'migration_1'
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_SENTINEL'):
            self.run_stack()
        self.assertEqual(self.g.result['case_stack_secondary'][0]['stage'], 'failure_receipt')

    def test_admin_transport_failure_retains_reserved_batch_and_no_pass(self):
        command = self.g.command
        def failed(label, *args, **kwargs):
            if label == 'case-stack-system-identifier':
                raise RuntimeError('PRIVATE_ADMIN_FAILURE')
            return command(label, *args, **kwargs)
        self.g.command = failed
        with self.assertRaisesRegex(RuntimeError, 'PRIVATE_ADMIN_FAILURE'):
            self.run_stack()
        failure = json.loads((self.g.out / 'case-stack-failure.json').read_bytes())
        self.assertEqual(failure['admin_sql_reserved'], 5)
        self.assertIsNone(failure['admin_sql_confirmed'])
        self.assertFalse((self.g.out / 'case-stack-bootstrap.json').exists())

    def test_late_migration_drift_fails_even_when_history_matches(self):
        command = self.g.command
        def changed(label, *args, **kwargs):
            result = command(label, *args, **kwargs)
            if label == 'case-stack-system-identifier':
                (self.g.work / 'supabase/migrations' / pathlib.PurePosixPath(MIGRATIONS[0]).name
                 ).write_bytes(b'drift')
            return result
        self.g.command = changed
        with self.assertRaisesRegex(b.StackStop, 'migration_bytes_changed'):
            self.run_stack()

    def test_late_manifest_drift_fails_before_pass(self):
        command = self.g.command
        def changed(label, *args, **kwargs):
            result = command(label, *args, **kwargs)
            if label == 'case-stack-system-identifier':
                path = self.g.out / 'candidate.json'
                path.write_bytes(path.read_bytes() + b' ')
            return result
        self.g.command = changed
        with self.assertRaisesRegex(b.StackStop, 'manifest_changed'):
            self.run_stack()

    def test_lazy_dependencies_require_actual_instrumented_dispatcher(self):
        module = types.ModuleType('admission_ci')
        class Gate:
            def cli(self):
                raise AssertionError('must not dispatch')
        module.Gate = Gate
        module.app = types.ModuleType('app_ci')
        native = types.ModuleType('native_runtime')
        native.NativeRuntime = object()
        gate = Gate()
        selected = []
        gate.bind_modules = lambda *modules: selected.extend(modules)
        with patch.dict(sys.modules, {'admission_ci': module, 'cli_profile': profile,
                'cli_meter': types.ModuleType('cli_meter'),
                'ci_source_binding': types.ModuleType('ci_source_binding'), 'native_runtime': native}):
            result = REAL_DEPENDENCIES(gate)
            self.assertIs(result[-1], native.NativeRuntime)
            self.assertIn(b, selected)
            self.assertIn(module, selected)
            gate.cli = lambda: None
            with self.assertRaisesRegex(b.StackStop, 'dispatcher'):
                REAL_DEPENDENCIES(gate)

    def boundary_hooks(self, fail=None):
        g, events = self.g, []
        class Hooks:
            def before45(self, snapshot):
                events.append(('before45', len(g.history), snapshot))
                if fail == 'before45':
                    raise RuntimeError('before45_injected')
            def after45(self, snapshot):
                events.append(('after45', len(g.history), snapshot))
                if fail == 'after45':
                    raise RuntimeError('after45_injected')
        def before(gate):
            self.assertIs(gate, g)
            self.assertEqual(len(g.history), 44)
            events.append(('checked_before', 44))
            g.save('migration-boundary-pre.json', {'component_verified': True})
            return types.SimpleNamespace(sample={'history': list(g.history)})
        def dispatch(gate, args, expected):
            self.assertIs(gate, g)
            self.assertEqual(expected, g.sources / MIGRATIONS[-1])
            self.assertEqual(args, ('migration', 'up', '--local'))
            events.append(('actual_dispatch', 44))
            g.calls.append(('instrumented', 'migration_45'))
            g.history.append(profile.QUOTA.split('_')[0])
            g.save('cli-predispatch-canonical-45.json', {'complete': True})
            return {'instrumented_receipt': 'cli-predispatch-canonical-45.json'}
        def after(gate, token, result):
            self.assertIs(gate, g)
            self.assertEqual(len(token.sample['history']), 44)
            self.assertEqual(len(g.history), 45)
            events.append(('checked_after', 45))
            report = {'component_verified': True, 'after_m45': {'history_count': 45}}
            g.save('migration-boundary-post.json', report)
            return report
        patch.object(b, '_boundary_module', return_value=types.SimpleNamespace(
            before=before, after=after, M45=MIGRATIONS[-1])).start()
        g.instrumented_cli = lambda: types.SimpleNamespace(run_canonical=dispatch)
        return Hooks(), events

    def test_optional_boundaries_surround_one_real_dispatch_without_gate_patch(self):
        hooks, events = self.boundary_hooks()
        original_cli = self.g.cli.__func__
        result = b.bootstrap(self.g, MIGRATIONS, hooks=hooks)
        self.assertEqual([e[0] for e in events],
                         ['checked_before', 'before45', 'actual_dispatch', 'checked_after', 'after45'])
        self.assertIs(self.g.cli.__func__, original_cli)
        self.assertEqual(len(self.g.history), 47)
        self.assertEqual(result['status'], 'CLEAN47_BOOTSTRAP_PASS')
        for stage, count, snapshot in (events[1], events[-1]):
            self.assertEqual(snapshot['history_count'], count)
            self.assertEqual(snapshot['stage'], stage)
            self.assertEqual(snapshot['ci_run'], '123456789')
            for ref in snapshot['evidence_refs']:
                self.assertEqual(ref['sha256'], b.sha((self.g.out / ref['path']).read_bytes()))

    def test_before45_fault_stops_with44_and_never_dispatches_m45_or_app(self):
        hooks, events = self.boundary_hooks('before45')
        with self.assertRaisesRegex(RuntimeError, 'before45_injected'):
            b.bootstrap(self.g, MIGRATIONS, hooks=hooks)
        self.assertEqual([e[0] for e in events], ['checked_before', 'before45'])
        self.assertEqual(len(self.g.history), 44)
        self.assertFalse(self.g.cli_protocol)
        self.assertFalse((self.g.out / 'cli-predispatch-canonical-45.json').exists())
        self.assertTrue((self.g.out / 'case-stack-boundary-before45.json').exists())
        self.assertTrue((self.g.out / 'case-stack-failure.json').exists())

    def test_after45_fault_retains45_confirmation_and_does_not_apply_app46(self):
        hooks, events = self.boundary_hooks('after45')
        with self.assertRaisesRegex(RuntimeError, 'after45_injected'):
            b.bootstrap(self.g, MIGRATIONS, hooks=hooks)
        self.assertEqual(len(self.g.history), 45)
        self.assertEqual(self.g.result['migrations_applied'], 45)
        self.assertEqual(len([e for e in events if e[0] == 'actual_dispatch']), 1)
        self.assertFalse(self.g.cli_protocol)
        self.assertTrue((self.g.out / 'migration-boundary-post.json').exists())
        self.assertFalse((self.g.out / 'case-stack-bootstrap.json').exists())

    def test_unbound_hooks_rejected_before_native_or_cli(self):
        with self.assertRaisesRegex(b.StackStop, 'bound_hook'):
            b.bootstrap(self.g, MIGRATIONS,
                        hooks=types.SimpleNamespace(before45=lambda s: None, after45=lambda s: None))
        self.assertFalse(self.g.calls)
        self.assertFalse(self.g.native)

    def test_standalone_entry_registers_sources_and_never_runs_full_gate(self):
        entry = importlib.import_module('case_stack_v1.__main__')
        fake = types.ModuleType('admission_ci')
        fake.EXTRA = set()
        fake.app = types.SimpleNamespace(previous=types.SimpleNamespace(
            prior=types.SimpleNamespace(old=types.SimpleNamespace(EXTRA=set()))))
        gate = self.g
        gate.fetch = lambda: MIGRATIONS
        gate.install = lambda: None
        fake.Gate = lambda: gate
        with patch.dict(sys.modules, {'admission_ci': fake}), patch.object(b, 'bootstrap') as run:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(entry.main([]), 0)
            run.assert_called_once_with(gate, MIGRATIONS)
        self.assertTrue(set(b.SOURCES) <= fake.EXTRA)
        self.assertTrue(set(b.SOURCES) <= fake.app.previous.prior.old.EXTRA)
        self.assertEqual(gate.result['status'], 'BOOTSTRAP_ONLY_PASS')
        self.assertFalse(gate.result['case_execution_started'])
        self.assertFalse(gate.result['full_chain_admission'])

    def test_standalone_result_write_failure_keeps_primary_and_never_passes(self):
        entry = importlib.import_module('case_stack_v1.__main__')
        for failed_bootstrap in (False, True):
            with self.subTest(failed_bootstrap=failed_bootstrap):
                gate = types.SimpleNamespace(result={}, fetch=lambda: MIGRATIONS,
                    install=lambda: None)
                calls = []
                def save(name, value):
                    calls.append(name)
                    raise OSError('PRIVATE_RESULT_WRITE')
                gate.save = save
                fake = types.SimpleNamespace(EXTRA=set(), Gate=lambda: gate,
                    app=types.SimpleNamespace(previous=types.SimpleNamespace(
                        prior=types.SimpleNamespace(old=types.SimpleNamespace(EXTRA=set())))))
                output = io.StringIO()
                failure = ValueError('PRIVATE_BOOTSTRAP_PRIMARY') if failed_bootstrap else None
                with patch.dict(sys.modules, {'admission_ci': fake}), \
                     patch.object(b, 'bootstrap', side_effect=failure), \
                     contextlib.redirect_stdout(output):
                    self.assertEqual(entry.main([]), 1)
                value = json.loads(output.getvalue())
                self.assertEqual(value['status'], 'NO_GO')
                self.assertEqual(value['error_type'], 'ValueError' if failed_bootstrap else 'OSError')
                self.assertEqual(value['result_write_error_type'], 'OSError')
                self.assertFalse(value['full_chain_admission'])
                self.assertEqual(calls, ['result.json'])
                self.assertNotIn('PRIVATE', output.getvalue())


if __name__ == '__main__':
    unittest.main()
