"""Local source/contract tests. No sockets, processes, credentials or DB fixtures."""
import contextlib
import copy
import io
import pathlib
import unittest
from unittest.mock import patch

import release_train as train


class ReleaseTrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = train.build()

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
        original = train.file_hash
        with patch.object(train, 'file_hash', side_effect=lambda root, name:
                          '0' * 64 if name == expected else original(root, name)):
            with self.assertRaisesRegex(ValueError, 'pinned_source_drift'):
                train.frozen(train.ROOT, 12)

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
        result = train.verify(self.document)
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
