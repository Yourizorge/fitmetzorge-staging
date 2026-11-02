"""Local source/contract tests. No sockets, processes, credentials or DB fixtures."""
import ast
import contextlib
import copy
import io
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import release_train as train

FROZEN_CHECKOUT = train.ROOT


class ReleaseTrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = train.build(frozen_root=FROZEN_CHECKOUT)

    def test_all_nine_frozen_contracts_are_verified(self):
        self.assertEqual(self.document['release_order'], list(range(12, 21)))
        self.assertEqual(len(self.document['packages']), 9)
        for item in self.document['packages']:
            self.assertEqual(item['frozen_contract']['status'], train.OFFLINE)
            self.assertFalse(item['frozen_contract']['live_acceptance'])
            self.assertTrue(item['frozen_contract']['sources'])

    def test_all_bindings_are_exact_and_generated_json_is_excluded(self):
        sources = self.document['source_hashes']
        self.assertNotIn(train.PREFIX + 'release_train.json', sources)
        self.assertIn(train.PREFIX + 'release_train.py', sources)
        self.assertIn(train.PREFIX + 'test_release_train.py', sources)
        self.assertEqual(self.document['source_bundle_sha256'], train.canonical_hash(sources))
        for name, expected in sources.items():
            self.assertEqual(train.file_hash(train.ROOT, name), expected, name)

    def test_historical_ci_is_pinned_not_fresh_or_hosted(self):
        history = self.document['historical_ci']
        self.assertEqual(history['run_id'], '40354972820')
        self.assertEqual(history['commit'], train.HISTORY_COMMIT)
        self.assertEqual(history['selected_release_checks'], 359)
        self.assertTrue(history['selected_receipts_hash_verified'])
        self.assertFalse(history['archive_reverified_here'])
        self.assertFalse(history['fresh_full_ci_claimed'])
        self.assertFalse(history['hosted_admission'])
        self.assertNotEqual(history['commit'], self.document['owner_confirmed_base'])

    def test_current_source_drift_is_not_historical_ci_coverage(self):
        sources = train.read_json(train.ROOT, train.HISTORY + 'candidate.json')['sources']
        for item in self.document['packages']:
            impl = item['implementation']
            expected = sorted(n for n, h in impl['source_hashes'].items() if sources.get(n) != h)
            self.assertEqual(impl['historical_exact_byte_mismatches'], expected)
            self.assertFalse(impl['gate']['enabled'])

    def test_stable_input_packaging(self):
        with patch.object(train, 'build', return_value=self.document):
            self.assertEqual(train.input_files(), set(self.document['source_hashes']))

    def test_ci_release_security_uses_the_actual_pinned_install_target(self):
        tree = ast.parse(train.raw(train.ROOT / (train.PREFIX + 'ci.py')))
        gate = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Gate')
        methods = {n.name: n for n in gate.body if isinstance(n, ast.FunctionDef)}

        def command(method, label):
            calls = [n.value for n in methods[method].body if isinstance(n, ast.Expr)
                     and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                     and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'self'
                     and n.value.func.attr == 'command' and n.value.args
                     and isinstance(n.value.args[0], ast.Constant) and n.value.args[0].value == label]
            self.assertEqual(len(calls), 1, label)
            source = pathlib.Path('/candidate')
            namespace = {'self': type('GateStub', (), {'sources': source})(), 'sys': train.sys,
                         'str': str, 'folder': source / train.PREFIX}
            return calls[0], eval(compile(ast.Expression(calls[0].args[1]), '<ci-command>', 'eval'),
                                  {'__builtins__': {}}, namespace)

        _, install = command('install', 'pg17-parser-install')
        self.assertIn('pglast==7.20', install)
        self.assertIn('psycopg[binary]==3.2.10', install)
        self.assertIn('--only-binary=:all:', install)
        target = install[install.index('--target') + 1]
        call, security = command('regressions', 'release-security')
        self.assertEqual(security, ['env', 'PYTHONPATH=' + target, train.sys.executable, '-B',
                                    str(pathlib.Path('/candidate') / train.PREFIX / 'test_release_security.py')])
        self.assertEqual(len(call.args), 2)
        self.assertEqual(call.keywords, [])

    def test_large_frozen_bodies_are_checked_but_not_uploaded(self):
        sources = self.document['source_hashes']
        references = self.document['frozen_checkout_reference_hashes']
        for name in ('proactive-signals-demo/data.js', 'bounded-adjustments-demo/data.js',
                     'workout-reflection-demo/data.js', 'docs/PHASE6E17_EXAMPLES.json',
                     'docs/PHASE6E16_EXAMPLES.json', 'docs/PHASE6E18_EXAMPLES.json'):
            self.assertNotIn(name, sources)
            self.assertIn(name, references)
        self.assertFalse(set(sources) & set(references))
        self.assertEqual(self.document['frozen_checkout_reference_bundle_sha256'],
                         train.canonical_hash(references))
        for item in self.document['packages']:
            contract = item['frozen_contract']
            self.assertTrue(contract['checkout_body_bindings'])
            for name, binding in contract['checkout_body_bindings'].items():
                self.assertTrue(binding['checkout_bytes_verified'])
                self.assertFalse(binding['git_object_reverified_here'])
                self.assertEqual(binding['working_sha256'], contract['sources'][name])
                self.assertEqual(contract['sources'][name], sources.get(name, references.get(name)))
            for name in contract['input_hashes']:
                self.assertIn(name, sources)

    def test_minimal_candidate_verifies_against_separate_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = pathlib.Path(directory)
            for name in self.document['source_hashes']:
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(train.raw(train.safe_file(train.ROOT, name)))
            document = train.build(candidate, frozen_root=FROZEN_CHECKOUT)
            self.assertEqual(document, self.document)
            self.assertEqual(train.verify(document, candidate, frozen_root=FROZEN_CHECKOUT)['status'],
                             'MANIFEST_VALID_NOT_RELEASED')
            with self.assertRaisesRegex(ValueError, 'source_missing'):
                train.build(candidate, frozen_root=candidate)
            target = candidate / (train.PREFIX + 'release_train.py')
            target.write_bytes(target.read_bytes() + b'\n# changed\n')
            with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                train.verify(document, candidate, frozen_root=FROZEN_CHECKOUT)

    def test_checkout_mapping_requires_exact_working_and_git_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            target = root / 'body.js'
            lf, crlf = b'first\nsecond\n', b'first\r\nsecond\r\n'
            for actual, working, mapping in ((lf, lf, 'exact'), (lf, crlf, 'LF-to-CRLF-only'),
                                              (crlf, lf, 'CRLF-to-LF-only')):
                with self.subTest(mapping=mapping):
                    target.write_bytes(actual)
                    result = train.frozen_body(root, 'body.js', train.digest(working), train.digest(lf))
                    self.assertEqual(result['checkout_to_working_mapping'], mapping)
                    self.assertEqual(result['checkout_sha256'], train.digest(actual))
            target.write_bytes(lf)
            with self.assertRaisesRegex(ValueError, 'frozen_git_mapping'):
                train.frozen_body(root, 'body.js', train.digest(lf), '0' * 64)
            for changed in (b'first\nchanged\n', b'first\nsecond \n', b'first\rsecond\r'):
                target.write_bytes(changed)
                with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                    train.frozen_body(root, 'body.js', train.digest(lf))

    def test_modified_reference_cannot_be_self_attested(self):
        altered = copy.deepcopy(self.document)
        refs = altered['frozen_checkout_reference_hashes']
        refs[next(iter(refs))] = '0' * 64
        altered['frozen_checkout_reference_bundle_sha256'] = train.canonical_hash(refs)
        with patch.object(train, 'pinned'), patch.object(train, 'build', return_value=self.document):
            with self.assertRaisesRegex(ValueError, 'release_train_drift'):
                train.verify(altered)

    def test_coupled_selections_are_not_separate_runtime_gates(self):
        expected = {13: [13, 14], 14: [13, 14], 16: [16, 17], 17: [16, 17],
                    19: [19, 20], 20: [19, 20]}
        for item in self.document['packages']:
            peers = expected.get(item['package'], [item['package']])
            self.assertEqual(item['coupled_packages'], peers)
            self.assertEqual(item['independent_action_gate'], len(peers) == 1)

    def test_composed_workout_is_deferred_not_added_to_minimal12(self):
        minimal = self.document['packages'][0]['implementation']
        self.assertEqual(minimal['actions']['member'], ['register12', 'revoke'])
        supplements = self.document['post_train_supplements']
        self.assertEqual([p['implementation']['id'] for p in supplements], ['workout12', 'preferences'])
        self.assertEqual(supplements[0]['after_packages'], list(range(12, 21)))
        self.assertEqual(supplements[0]['implementation']['workspace_kind'], 'registration12')

    def test_route_scope_and_separate_apply_are_preserved(self):
        rows = {p['package']: p['implementation'] for p in self.document['packages']}
        for number in (15, 16, 17):
            self.assertEqual(rows[number]['routes'], ['B'])
            self.assertNotIn('apply', rows[number]['actions']['member'])
        self.assertIn('confirm', rows[18]['actions']['member'])
        self.assertIn('apply', rows[18]['actions']['member'])
        self.assertEqual(rows[18]['actions']['trainer'], ['approve', 'block'])

    def test_no_21_or_real_member_ai_and_no_new_budget(self):
        self.assertEqual(self.document['excluded']['actions'], ['record', 'finish_workout', 'finish_day'])
        self.assertTrue(self.document['excluded']['default_off'])
        for item in self.document['packages']:
            gate = item['implementation']['gate']
            self.assertFalse(gate['full_day21'])
            self.assertFalse(gate['real_member_ai'])
        self.assertEqual(self.document['authorization_boundary'], {
            'endchain_limit_unchanged': 2349, 'temp_bytes_limit': 0, 'read_wal_limit': 0,
            'additional_hosted_commands_authorized': 0})

    def test_actual_migration_identity_and_counts_not_old45_46_labels(self):
        baseline = self.document['migration_baseline']
        self.assertEqual(len(baseline['canonical_sources']), 45)
        self.assertIsNone(baseline['hosted_count_measured_here'])
        for item in self.document['packages']:
            migration = item['implementation']['migration']
            counts = [p['count_after_apply_on_clean_ci'] for p in migration['local_candidates']]
            self.assertEqual(counts, [46] if item['package'] == 12 else [46, 47])
            self.assertIsNone(migration['canonical_hosted_identity'])
            self.assertFalse(migration['hosted_applied'])

    def test_required_release_dimensions_have_actual_sources(self):
        for item in self.document['packages']:
            impl = item['implementation']
            for key in ('storage', 'auth_rls', 'api', 'version', 'idempotency',
                        'rollback', 'cleanup', 'migration', 'tests'):
                self.assertTrue(impl[key], (item['package'], key))
            self.assertTrue(impl['entry_files'])
            self.assertIsNone(impl['cleanup']['executor'])
            self.assertIsNone(impl['api']['edge_deployment'])
            self.assertFalse(impl['tests']['fresh_stack_executed_by_helper'])

    def test_frozen_source_drift_is_rejected_without_rebaselining(self):
        expected = train.read_json(train.ROOT, 'docs/PHASE6E12_FREEZE_EVIDENCE.json')['sources'][0]['file']
        original = train.raw
        with patch.object(train, 'raw', side_effect=lambda path:
                          b'changed' if pathlib.Path(path).as_posix().endswith('/' + expected)
                          else original(path)):
            with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                train.frozen(train.ROOT, 12, frozen_root=FROZEN_CHECKOUT)

    def test_rewritten_freeze_receipt_cannot_self_attest(self):
        with patch.object(train, 'file_hash', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                train.frozen(train.ROOT, 20)

    def test_corrupt_historical_artifact_is_not_downgraded_to_pass(self):
        original = train.file_hash
        with patch.object(train, 'file_hash', side_effect=lambda root, name:
                          '0' * 64 if name == train.HISTORY + 'result.json' else original(root, name)):
            with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                train.historical(train.ROOT)

    def test_dependency_missing_cycle_and_21_fail(self):
        for plan in (train.PLAN[1:], ((12, 'x', 'registration12', (20,)),) + train.PLAN[1:],
                     train.PLAN + ((21, 'x', 'preferences', (20,)),)):
            with self.subTest(plan=plan):
                with self.assertRaises(ValueError):
                    train.validate_plan(plan)

    def test_valid_snapshot_verifies_but_does_not_release(self):
        result = train.verify(self.document, frozen_root=FROZEN_CHECKOUT)
        self.assertEqual(result['status'], 'MANIFEST_VALID_NOT_RELEASED')
        self.assertFalse(result['hosted_admission'])

    def test_edited_gate_and_scope_are_rejected(self):
        for key, value in (('enabled', True), ('hosted_admission', True), ('fresh_full_ci_claimed', True)):
            altered = copy.deepcopy(self.document)
            altered['gate'][key] = value
            with patch.object(train, 'pinned'), patch.object(train, 'build', return_value=self.document):
                with self.assertRaisesRegex(ValueError, 'release_train_drift'):
                    train.verify(altered)

    def test_source_hash_and_empty_bindings_rejected(self):
        for sources in ({}, {'elsewhere.py': '0' * 64}):
            altered = copy.deepcopy(self.document)
            altered['source_hashes'] = sources
            with self.assertRaisesRegex(ValueError, 'source_bundle_binding'):
                train.verify(altered)

    def test_path_escape_missing_and_absolute_are_rejected(self):
        for name in ('../AGENTS.md', '/tmp/a', 'C:/x', 'a\\b', 'does-not-exist-release-train'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                train.file_hash(train.ROOT, name)

    def test_complete_selection_still_cannot_promote_old_ci(self):
        with patch.object(train, 'verify'):
            value = train.gate(self.document, list(range(12, 21)))
        self.assertEqual(value['status'], 'NO_GO')
        self.assertFalse(value['enabled'])
        self.assertEqual(set(value['blockers']), set(train.RELEASE_BLOCKERS))

    def test_partial_group_and_missing_dependency_are_blocked(self):
        with patch.object(train, 'verify'):
            value = train.gate(self.document, [13])
        self.assertIn('coupled_selection_missing:14', value['blockers'])
        self.assertIn('dependency_selection_missing:12', value['blockers'])

    def test_package21_duplicate_boolean_or_empty_request_rejected(self):
        for selection in ([21], [12, 12], [True], []):
            with self.subTest(selection=selection), patch.object(train, 'verify'):
                with self.assertRaises(ValueError):
                    train.gate(self.document, selection)

    def test_cli_exit_codes_are_not_release_success(self):
        with patch.object(train, 'build', return_value=self.document), \
                patch.object(train, 'verify', return_value={'status': 'MANIFEST_VALID_NOT_RELEASED'}), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.main(['check']), 0)
            self.assertEqual(train.main(['gate', '--package', '12']), 3)
            self.assertEqual(train.main(['gate', '--package', '21']), 2)

    def test_cli_does_not_write_snapshot(self):
        with patch.object(train, 'build', return_value=self.document), \
                patch.object(pathlib.Path, 'write_text', side_effect=AssertionError('write')), \
                patch.object(pathlib.Path, 'write_bytes', side_effect=AssertionError('write')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.main(['build']), 0)
            self.assertEqual(train.main(['inputs']), 0)


if __name__ == '__main__':
    unittest.main()
