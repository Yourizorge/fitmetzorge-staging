"""Offline packet integrity/selection tests; no database, Auth or hosted calls."""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import workday_release as p


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = p.build()

    def test_exact_order_and_private_candidates(self):
        rows = self.document['packets']
        self.assertEqual([r['ordinal'] for r in rows], list(range(1, 9)))
        self.assertEqual([r['id'] for r in rows], [s['id'] for s in p.SLICES])
        self.assertEqual(rows[0]['release_after'], 'hosted11_and_owner_review')
        for before, after in zip(rows, rows[1:]):
            self.assertEqual(after['release_after'], before['id'])
        self.assertEqual([c['path'] for c in rows[0]['database']['candidates']], [p.M45])
        for row in rows[1:]:
            self.assertEqual([c['path'] for c in row['database']['candidates']], [p.M45, p.M46])
            self.assertFalse(row['database']['hosted_applied'])
            self.assertIsNone(row['database']['canonical_hosted_migration'])

    def test_transitive_frozen_dependencies_and_exact_byte_hashes(self):
        for row in self.document['packets']:
            self.assertEqual(row['source_bundle_sha256'], p.sha(row['source_hashes']))
            self.assertIn('_offline/phase6e12/core.cjs', row['source_hashes'])
            self.assertIn('training-rules-demo/model.js', row['source_hashes'])
            self.assertIn('nutrition-rules-demo/model.js', row['source_hashes'])
            self.assertIn('assets/fit-met-zorge-logo-cropped.png', row['source_hashes'])
            for name, value in row['source_hashes'].items():
                self.assertEqual(value, p.digest(p.raw(p.ROOT / name)))

    def test_server_asset_inventory_and_generated_evidence_are_separate(self):
        hashes = self.document['packets'][0]['source_hashes']
        for name in ('workday_release_packets.json', 'work_register.json'):
            self.assertNotIn(p.PREFIX + name, hashes)
        self.assertFalse(any('/receipts/' in name for name in hashes))
        server = p.raw(p.HERE / 'server.py').decode('utf-8-sig')
        for name in ('offline_shell.html', 'offline_shell.css', 'offline_shell.js', 'offline_sw.js', 'account_center.js'):
            if name in server:
                self.assertIn(p.PREFIX + name, hashes)

    def test_path_escape_and_missing_sources_fail_closed(self):
        for name in ('../outside.py', '/outside.py', 'C:/outside.py', 'bad\\path.py', 'absent.py'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                p.safe_file(p.ROOT, name)

    def test_source_drift_invalidates_check(self):
        read = p.raw
        def changed(path):
            value = read(path)
            return value + b'\n// source changed\n' if path == p.ROOT / p.PREFIX / 'domain.cjs' else value
        with patch.object(p, 'raw', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'packet_drift'):
                p.verify(self.document)

    def test_packet_tampering_cannot_add_actions_or_enable_gate(self):
        for fault in ('enabled', 'action', 'count', 'order', 'source'):
            value = copy.deepcopy(self.document)
            row = value['packets'][0]
            if fault == 'enabled':
                row['gate']['enabled'] = True
            elif fault == 'action':
                row['actions']['member'].append('finish_day')
            elif fault == 'count':
                row['accounting']['hosted_approved_limit'] = 2237
            elif fault == 'order':
                row['ordinal'] = 2
            else:
                row['source_hashes'][p.M45] = '0' * 64
            with self.subTest(fault=fault), patch.object(p, 'build', return_value=self.document):
                with self.assertRaisesRegex(ValueError, 'packet_drift'):
                    p.verify(value)

    def test_selection_is_not_bulk_action_access(self):
        minimal = p.selected(self.document, 'registration12')
        journey = p.selected(self.document, 'workout12')
        for action in ('start12', 'finish12'):
            self.assertFalse(p.selection_allows(minimal, action, 'member', 'B'))
            self.assertTrue(p.selection_allows(journey, action, 'member', 'B'))
        plans = p.selected(self.document, 'plans16_17')
        recovery = p.selected(self.document, 'recovery19_today20')
        self.assertTrue(p.selection_allows(plans, 'edit', 'member', 'B', 'nutrition_item'))
        self.assertFalse(p.selection_allows(plans, 'edit', 'member', 'B', 'time'))
        self.assertTrue(p.selection_allows(recovery, 'edit', 'member', 'A', 'time'))
        self.assertFalse(p.selection_allows(recovery, 'edit', 'member', 'B', 'nutrition_item'))
        self.assertFalse(p.selection_allows(plans, 'apply', 'member', 'B'))
        self.assertFalse(p.selection_allows(p.selected(self.document, 'intake15'), 'intake', 'member', 'A'))

    def test_review_roles_and_unaccepted21_never_selected(self):
        review = p.selected(self.document, 'review18')
        self.assertTrue(p.selection_allows(review, 'approve', 'trainer', 'A'))
        self.assertFalse(p.selection_allows(review, 'approve', 'member', 'A'))
        self.assertFalse(p.selection_allows(review, 'approve', 'trainer', 'B'))
        self.assertFalse(p.selection_allows(review, 'apply', 'owner', 'A'))
        for packet in self.document['packets']:
            for action in p.FORBIDDEN:
                for role in ('member', 'trainer', 'owner', 'anon'):
                    for route in ('A', 'B'):
                        self.assertFalse(p.selection_allows(packet, action, role, route))
            self.assertFalse(packet['gate']['enabled'])
            self.assertTrue(packet['gate']['local_boundary_implemented'])
            self.assertFalse(packet['gate']['local_action_guard']['generated_json_required'])
            self.assertIn(p.PREFIX + 'release_selection.py', packet['source_hashes'])
            self.assertIn(p.PREFIX + 'release_selection_http.py', packet['source_hashes'])
            self.assertFalse(packet['gate']['full_day21'])
            self.assertFalse(packet['status']['released'])

    def test_static_protocol_includes_terminals_and_unknown_full_closure(self):
        model = self.document['sql_model']
        expected = {'registration_read': 8, 'registration_changed': 12, 'registration_replay': 8,
                    'member_read': 9, 'trainer_read': 8, 'primary_changed': 13,
                    'primary_unchanged': 11, 'primary_replay': 8}
        for key, count in expected.items():
            row = model['profiles'][key]
            self.assertEqual(row['base_commands'], count)
            self.assertEqual(len(row['sequence']), count)
            sql = [model['templates'][ref]['sql'] for ref in row['sequence']]
            self.assertEqual((sql[0], sql[-1]), ('BEGIN', 'COMMIT'))
            self.assertIsNone(row['managed_auth_commands'])
            self.assertEqual(len(row['failure_prefixes']), count)
            for prefix in row['failure_prefixes']:
                self.assertEqual(prefix['with_one_attempted_rollback'], prefix['attempted_commands'] + 1)
                self.assertEqual(model['templates'][prefix['rollback_template']]['sql'], 'ROLLBACK')
        for template in model['templates'].values():
            self.assertEqual(template['template_sha256'], p.digest(template['sql'].encode()))
        self.assertEqual(set(model['outbox_templates']), {'INSERT', 'UPDATE'})

    def test_changed_source_sql_structure_is_not_silently_remodeled(self):
        read = p.raw
        def changed(path):
            value = read(path)
            if path == p.ROOT / p.PREFIX / 'store.py':
                return value.replace(b"db.execute('set local role fmz6e_integration_server')", b"db.execute('set local role fmz6e_integration_server');db.execute('SELECT 1')")
            return value
        with patch.object(p, 'raw', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'sql_structure_changed'):
                p.sql_profiles(p.ROOT)

    def test_writesets_cover_noop_outbox_and_immutable_history(self):
        first = self.document['packets'][0]
        self.assertFalse(first['writeset']['outbox']['enabled_in_adapter'])
        self.assertEqual([r['operation'] for r in first['writeset']['changed']], ['UPDATE', 'INSERT', 'INSERT'])
        for row in self.document['packets']:
            self.assertEqual(row['writeset']['other_members'], 'zero allowed writes')
            self.assertIn('audit', row['writeset'])
            self.assertIn('state_sha', row['writeset']['changed'][0]['columns'])
            self.assertFalse(row['permissions']['Data_API_exposed'])
            self.assertIn('service_role', row['permissions']['denied_schema_roles'])
            if row['id'] not in ('registration12', 'workout12'):
                self.assertTrue(row['writeset']['outbox']['enabled_in_adapter'])
                self.assertIn('one requests INSERT', row['writeset']['no_op'])

    def test_existing_receipt_helpers_reproduce_historical_accounting(self):
        history = self.document['history']
        if history['classification'] == 'ARCHIVE_NOT_AVAILABLE':
            self.assertIsNone(history['registration12_observed_sql'])
            self.assertIsNone(history['transport_pair_count'])
            self.assertIsNone(history['transport_observed_sql'])
        else:
            self.assertEqual(history['registration12_observed_sql'], 970)
            self.assertEqual(history['transport_pair_count'], 22)
            self.assertGreater(history['transport_observed_sql'], 0)
        self.assertFalse(history['hosted_authorized'])
        self.assertEqual(history['current_source_ci'], 'NOT_ESTABLISHED_BY_THIS_HELPER')
        for row in self.document['packets']:
            accounting = row['accounting']
            self.assertTrue(accounting['modeled_not_measured'])
            self.assertIsNone(accounting['normal_commands'])
            self.assertIsNone(accounting['safe_stop_maximum'])
            self.assertIsNone(accounting['hosted_approved_limit'])
            self.assertEqual(accounting['automatic_retries'], 0)
            self.assertTrue(all(r['commands'] is None for r in accounting['future_command_register']))

    def test_receipt_corruption_is_rejected_before_reuse(self):
        if not p.disk(p.ARCHIVE / 'MANIFEST.json').is_file():
            self.skipTest('Historical archive absent in isolated candidate; no archive proof claimed')
        read = p.raw
        target = p.ARCHIVE / 'registration12-transport-register.json'
        def changed(path):
            value = read(path)
            return value + b' ' if path == target else value
        with patch.object(p, 'raw', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'receipt_hash'):
                p.historical_evidence(p.ROOT)

    def test_missing_archive_is_not_measured_or_current_ci_evidence(self):
        result = p.historical_evidence(p.ROOT, p.HERE / 'absent-unit-test-archive')
        self.assertEqual(result['classification'], 'ARCHIVE_NOT_AVAILABLE')
        self.assertIsNone(result['transport_observed_sql'])
        self.assertFalse(result['hosted_authorized'])
        self.assertEqual(result['source_hashes'], {})

    def test_gate_is_always_closed_and_performs_no_execution(self):
        data = json.dumps(self.document).encode()
        with patch.object(p, 'raw', return_value=data), patch.object(p, 'verify'), patch.object(p.subprocess, 'run') as run:
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(p.main(['gate', '--slice', 'preferences']), 3)
            self.assertFalse(json.loads(out.getvalue())['enabled'])
            run.assert_not_called()

    def test_old_and_in_progress_register_fields_do_not_become_ci_pass(self):
        old = {'functions': [{'id': 'registration12', 'state': 'real_local_ci_pass', 'evidence': 'old CI only', 'remaining': 'review'}]}
        value = p.status_rows(old)
        first = value['slices'][0]
        self.assertEqual(first['local_ci'], ['old CI only'])
        self.assertEqual(first['hosted'], ['NOT_RECORDED'])
        self.assertEqual(first['released'], [False])
        newer = copy.deepcopy(old)
        newer['hosted11'] = 'EXACT_RUN_AUTHORIZED_SOURCE_CI_IN_PROGRESS'
        newer['functions'][0].update(local_ci='IN_PROGRESS', hosted='NOT_PROVEN', review='PENDING', released=False, dependency='source CI')
        result = p.status_rows(newer)
        self.assertEqual(result['slices'][0]['local_ci'], ['IN_PROGRESS'])
        self.assertEqual(result['hosted11'], newer['hosted11'])
        self.assertEqual(len(p.status_rows({})['slices']), 8)

    def test_local_runner_only_selects_fixed_offline_commands(self):
        rows = p.local_test_commands(self.document)
        self.assertEqual(len({tuple(row['argv']) for row in rows}), len(rows))
        for row in rows:
            self.assertEqual(row['cwd'], p.PREFIX.rstrip('/'))
            self.assertFalse(row['network'])
            self.assertIn(row['argv'][0], ('python', 'node'))
            self.assertNotIn('ci.py', row['argv'])
            for name in row['argv'][2:]:
                self.assertTrue((p.HERE / name).is_file())


if __name__ == '__main__':
    unittest.main()
