"""Offline contracts only; real migration/Auth execution remains mandatory CI."""
import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import ci_profile as p

HERE = pathlib.Path(__file__).resolve().parent


def checkout_ci(here=HERE):
    # The downloaded candidate omits the pinned harness; CI already binds it to this checkout.
    root = pathlib.Path(os.environ.get('GITHUB_WORKSPACE', here.parents[1])).resolve()
    source = root / '_offline/phase6e_server_v1/ci.py'
    if source.read_bytes().replace(b'\r\n', b'\n') != (here / 'ci.py').read_bytes().replace(b'\r\n', b'\n'):
        raise ValueError('ci_profile_checkout_mismatch')
    return source


def sources():
    return ['supabase/migrations/' + f.name for f in sorted((HERE.parents[1] / 'supabase/migrations').glob('*.sql'))]


def history(stage):
    added = [] if stage == 'canonical' else [p.M45] if stage == 'minimal' else [p.M45, p.M46]
    return [{'version': v} for v in sorted([pathlib.PurePosixPath(f).name.split('_')[0] for f in sources()] +
                                          [f.split('_')[0] for f in added])]


def receipt(index):
    return {'profile': p.PROFILE, 'slot': 'app_' + str(index),
            'arguments': list(p.APPLY if index in (0, 2) else p.DRY),
            'dry_run': index in (1, 3), 'complete': True, 'numeric_protocol_coverage': True,
            'exitcode': 0, 'commands': [{'protocol_commands': 1}] * 129, 'protocol_commands': 129,
            'observer_commands': [{'confirmed': True, 'protocol_commands': 1}] * 8}


class Tests(unittest.TestCase):
    def test_actual_canonical45_and_exact_46_47_histories(self):
        for stage, count in [('canonical', 45), ('minimal', 46), ('complete', 47)]:
            result = p.history_contract(history(stage), sources(), stage)
            self.assertEqual(result['count'], count)
            self.assertEqual(result['sorted_last'], p.QUOTA.split('_')[0])
            self.assertFalse(result['hosted_applied'])

    def test_missing_quota_duplicate_unknown_or_unsorted_history_denied(self):
        rows = history('complete')
        for changed in (rows[:-1], rows + [rows[0]], rows[::-1], rows[:-1] + [{'version': '99999999999999'}]):
            with self.assertRaisesRegex(ValueError, 'history_identity'):
                p.history_contract(changed, sources(), 'complete')
        with self.assertRaisesRegex(ValueError, 'canonical_45'):
            p.canonical(sources()[:-1])
        with self.assertRaisesRegex(ValueError, 'canonical_45'):
            p.canonical(sources() + [sources()[0]])

    def test_four_explicit_local_steps_and_backdated_include_all(self):
        for index, phase in enumerate(('local_app_schema', 'local_app_schema', 'local_app_outbox', 'advisors_and_dryrun')):
            request = ('migration', 'up', '--local') if index in (0, 2) else p.DRY
            actual = p.cli_arguments(request, phase, index)
            self.assertIn('--local', actual)
            self.assertEqual('--include-all' in actual, index in (0, 2))
        with self.assertRaisesRegex(ValueError, 'invocation_count'):
            p.cli_arguments(p.DRY, 'advisors_and_dryrun', 4)

    def test_wrong_stage_linked_database_and_skipped_apply_denied(self):
        for args, phase, index in [(p.DRY, 'local_app_schema', 0),
                                   (('migration', 'up', '--local'), 'migration_45', 0),
                                   (('db', 'push', '--linked'), 'local_app_schema', 0),
                                   (p.DRY, 'local_app_outbox', 3)]:
            with self.assertRaisesRegex(ValueError, 'sequence'):
                p.cli_arguments(args, phase, index)

    def test_more_than_endchain_cap_is_measured_not_reserved(self):
        for index in range(4):
            result = p.cli_receipt(receipt(index), index)
            self.assertEqual(result['protocol_commands'], 129)
            self.assertEqual(result['step'], p.SLOTS[index])

    def test_incomplete_numeric_profile_count_and_exit_fail_closed(self):
        for key, value in [('profile', 'endchain'), ('complete', False), ('numeric_protocol_coverage', False),
                           ('exitcode', 1), ('protocol_commands', 128), ('observer_commands', []),
                           ('arguments', list(p.DRY)), ('dry_run', True)]:
            row = receipt(0);row[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'evidence'):
                p.cli_receipt(row, 0)

    def test_endchain_charge_or_slot_cannot_be_reused(self):
        for key, value in [('capacity_reserved', 64), ('charged_commands', 72), ('slot', 'quota'),
                           ('slot', 'pre_auth'), ('slot', 'final')]:
            row = receipt(0);row[key] = value
            with self.assertRaisesRegex(ValueError, 'endchain_capacity'):
                p.cli_receipt(row, 0)

    def test_observer_count_must_be_exactly_eight(self):
        for index in range(4):
            for count in (7, 9):
                row = receipt(index)
                row['observer_commands'] = [{'confirmed': True, 'protocol_commands': 1}] * count
                with self.subTest(index=index, count=count), self.assertRaisesRegex(ValueError, 'evidence'):
                    p.cli_receipt(row, index)

    def test_slot_must_match_exact_invocation_index(self):
        for index in range(4):
            for slot in [None, 'app_unknown', *('app_' + str(i) for i in range(4) if i != index)]:
                row = receipt(index)
                if slot is None:
                    row.pop('slot')
                else:
                    row['slot'] = slot
                with self.subTest(index=index, slot=slot), self.assertRaisesRegex(ValueError, 'app_cli_slot'):
                    p.cli_receipt(row, index)

    def test_gate_uses_platform_boundary_and_retains_real_quota_checks(self):
        tree = ast.parse((HERE / 'ci.py').read_text())
        gate = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Gate')
        methods = {n.name: ast.unparse(n) for n in gate.body if isinstance(n, ast.FunctionDef)}
        for name in ('install', 'rebuild', 'regressions', 'advisors'):
            self.assertIn('base.Gate.' + name + '(self', methods[name])
            self.assertNotIn('super()', methods[name])
        self.assertIn('previous.prior.old.Gate.check_bridge(self)', methods['check_bridge'])
        self.assertIn('check_budget', methods['check_bridge'])
        self.assertIn('loaded-source-final.json', methods['advisors'])
        self.assertIn('verify_all(ROOT, self.sources, files)', methods['advisors'])

    def test_app_sources_include_profile_but_not_endchain_source_binding(self):
        tree = ast.parse((HERE / 'ci.py').read_text())
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and
                          any(isinstance(t, ast.Name) and t.id == 'NEW' for t in n.targets))
        names = {n.value for n in assignment.value.elts if isinstance(n, ast.Constant)}
        self.assertIn('ci_profile.py', names)
        self.assertIn('test_ci_profile.py', names)
        self.assertNotIn('ci_source_binding.py', names)


class CheckoutLayoutTests(unittest.TestCase):
    def test_downloaded_layout_runs_real_inheritance_from_bound_checkout(self):
        checkout = checkout_ci().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp) / '_offline/phase6e_server_v1'
            folder.mkdir(parents=True)
            for name in ('ci.py', 'ci_profile.py', 'test_ci_profile.py'):
                (folder / name).write_bytes((HERE / name).read_bytes())
            self.assertFalse((folder.parent / 'phase6e11/controller_v1/ci.py').exists())
            env = dict(os.environ, GITHUB_WORKSPACE=str(checkout))
            result = subprocess.run([sys.executable, '-B', str(folder / 'test_ci_profile.py'),
                                     'FetchInheritanceTests'], cwd=folder, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Ran 3 tests', result.stderr)

    def test_changed_checkout_app_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            candidate = root / 'candidate'
            source = root / '_offline/phase6e_server_v1/ci.py'
            candidate.mkdir();source.parent.mkdir(parents=True)
            (candidate / 'ci.py').write_bytes(b'candidate = 1\n')
            source.write_bytes(b'candidate = 2\n')
            with patch.dict(os.environ, {'GITHUB_WORKSPACE': str(root)}):
                with self.assertRaisesRegex(ValueError, 'ci_profile_checkout_mismatch'):
                    checkout_ci(candidate)


class FetchInheritanceTests(unittest.TestCase):
    def setUp(self):
        original_path = sys.path[:]
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), original_path))
        spec = importlib.util.spec_from_file_location('app_ci_fetch_test', checkout_ci())
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)
        import ci_source_binding
        self.binding = ci_source_binding
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gate = self.app.Gate.__new__(self.app.Gate)
        self.gate.out = pathlib.Path(self.temp.name)
        self.gate.sources = self.app.ROOT
        self.gate.result = {}
        self.files = {name: '0' * 64 for name in self.app.EXTRA | self.app.previous.prior.old.EXTRA}
        self.gate.save('candidate.json', {'sources': self.files})
        # Only replace the network-fetch boundary below the real guard/endchain/app chain.
        fetch = patch.object(self.app.previous.prior.old.Gate, 'fetch', return_value=['canonical.sql'])
        self.network_fetch = fetch.start()
        self.addCleanup(fetch.stop)

    def test_checkout_harness_matches_all_source_binding_pins(self):
        for name, expected in self.binding.HARNESS.items():
            raw = (self.app.ROOT / name).read_bytes().replace(b'\r\n', b'\n')
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_actual_fetch_inheritance_writes_one_exclusive_preflight(self):
        proof = {'status': 'unit-source-verifier-result'}
        with patch.object(self.binding, 'verify_all', return_value=proof) as verify, \
                patch.object(self.gate, 'save', wraps=self.gate.save) as save:
            self.assertEqual(self.gate.fetch(), ['canonical.sql'])
        self.network_fetch.assert_called_once_with()
        verify.assert_called_once_with(self.app.previous.HERE.parents[2], self.gate.sources, self.files)
        self.assertEqual([call.args[0] for call in save.call_args_list].count('loaded-source-preflight.json'), 1)
        self.assertEqual(json.loads((self.gate.out / 'loaded-source-preflight.json').read_text()), proof)
        self.assertEqual(self.gate.result['cli_profile'], 'local_app')
        with self.assertRaises(FileExistsError):
            self.gate.save('loaded-source-preflight.json', proof)

    def test_parent_source_failure_propagates_without_app_receipt(self):
        with patch.object(self.binding, 'verify_all', side_effect=ValueError('ci_loaded_source_mismatch')) as verify:
            with self.assertRaisesRegex(ValueError, 'ci_loaded_source_mismatch'):
                self.gate.fetch()
        verify.assert_called_once()
        self.assertFalse((self.gate.out / 'loaded-source-preflight.json').exists())
        self.assertFalse((self.gate.out / 'loaded-source-final.json').exists())


if __name__ == '__main__':
    unittest.main()
