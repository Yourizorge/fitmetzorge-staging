"""Pure action-boundary tests. No packet, receipt, database or Auth dependency."""
import copy
import unittest
from unittest.mock import patch

from release_selection import SLICES, FORBIDDEN, SelectionDenied, require_action, selection_allows, validate_slice


def context(slice_id, role='member', route='B'):
    return {'role': role, 'route': route,
            'workspace_kind': 'registration12' if slice_id in ('registration12', 'workout12') else 'primary'}


def request(action, domain=None):
    return {'action': action, 'data': {'domain': domain, 'value': None} if action == 'edit' else {}}


class Tests(unittest.TestCase):
    def test_operator_configuration_defaults_and_unknown_values(self):
        self.assertIsNone(validate_slice(None))
        for spec in SLICES:
            self.assertEqual(validate_slice(spec['id']), spec['id'])
        for value in ('', 'all', 'Preferences', 'preferences ', True, 1, [], {}, 'full_day21'):
            with self.subTest(value=value), self.assertRaises(SelectionDenied):
                validate_slice(value)

    def test_all_declared_actions_and_subdomains_are_executable(self):
        for spec in SLICES:
            for role, actions in spec['actions'].items():
                route = 'A' if role == 'trainer' else 'B'
                for action in actions:
                    for domain in spec['edit_domains'] if action == 'edit' else (None,):
                        with self.subTest(slice=spec['id'], role=role, action=action, domain=domain):
                            self.assertIsNone(require_action(spec['id'], request(action, domain), **context(spec['id'], role, route)))

    def test_neighboring_actions_are_denied_for_every_slice(self):
        actions = {action for spec in SLICES for group in spec['actions'].values() for action in group}
        for spec in SLICES:
            for action in actions - set(spec['actions']['member']):
                with self.subTest(slice=spec['id'], action=action), self.assertRaises(SelectionDenied):
                    require_action(spec['id'], request(action, 'time'), **context(spec['id']))

    def test_edit_subdomains_cannot_cross_plan_and_recovery_slices(self):
        for slice_id, domain in [('plans16_17', 'time'), ('recovery19_today20', 'training_exercise'),
                                 ('recovery19_today20', 'nutrition_item'), ('plans16_17', 'other')]:
            with self.subTest(slice=slice_id, domain=domain), self.assertRaisesRegex(SelectionDenied, 'edit_domain'):
                require_action(slice_id, request('edit', domain), **context(slice_id))
        for data in ({}, {'domain': 'time'}, {'domain': 'time', 'value': None, 'role': 'trainer'}, {'domain': [], 'value': None}):
            with self.assertRaisesRegex(SelectionDenied, 'edit_shape'):
                require_action('recovery19_today20', {'action': 'edit', 'data': data}, **context('recovery19_today20'))

    def test_route_and_trainer_matrix(self):
        require_action('review18', request('approve'), **context('review18', 'trainer', 'A'))
        for slice_id, action, role, route in [
            ('review18', 'approve', 'trainer', 'B'), ('review18', 'approve', 'member', 'A'),
            ('review18', 'apply', 'trainer', 'A'), ('intake15', 'intake', 'member', 'A'),
            ('plans16_17', 'edit', 'member', 'A'), ('preferences', 'preferences', 'trainer', 'A'),
            ('registration12', 'register12', 'trainer', 'A')]:
            with self.subTest(slice=slice_id, action=action, role=role, route=route), self.assertRaises(SelectionDenied):
                require_action(slice_id, request(action, 'training_day'), **context(slice_id, role, route))

    def test_wrong_workspace_kind_and_unknown_route_fail_closed(self):
        for spec in SLICES:
            action = spec['actions']['member'][0]
            ctx = context(spec['id'])
            ctx['workspace_kind'] = 'primary' if ctx['workspace_kind'] == 'registration12' else 'registration12'
            with self.assertRaisesRegex(SelectionDenied, 'workspace'):
                require_action(spec['id'], request(action, 'time'), **ctx)
            for route in ('C', '', True, []):
                with self.assertRaisesRegex(SelectionDenied, 'route'):
                    require_action(spec['id'], request(action, 'time'), **context(spec['id'], route=route))

    def test_historical_missing_route_does_not_grant_primary_access(self):
        for slice_id in ('registration12', 'workout12'):
            require_action(slice_id, request('register12'), **context(slice_id, route=None))
        with self.assertRaisesRegex(SelectionDenied, 'route'):
            require_action('preferences', request('preferences'), **context('preferences', route=None))

    def test_forbidden21_and_unknown_roles_always_denied(self):
        for spec in SLICES:
            for action in FORBIDDEN:
                with self.assertRaises(SelectionDenied):
                    require_action(spec['id'], request(action), **context(spec['id']))
            for role in ('owner', 'anon', 'service_role', None, []):
                with self.assertRaises(SelectionDenied):
                    require_action(spec['id'], request('revoke'), **context(spec['id'], role=role))

    def test_request_cannot_select_slice_or_forge_context(self):
        for extra in ({'role': 'trainer'}, {'release_slice': 'review18'}, {'workspace_kind': 'primary'}, {'route': 'A'}):
            with self.assertRaisesRegex(SelectionDenied, 'request_shape'):
                require_action('preferences', {**request('preferences'), **extra}, **context('preferences'))
        with self.assertRaisesRegex(SelectionDenied, 'slice_unknown'):
            require_action(None, request('preferences'), **context('preferences'))
        with self.assertRaises(SelectionDenied):
            require_action('preferences', {'action': 'build', 'data': {'role': 'member', 'release_slice': 'intake15'}}, **context('preferences'))

    def test_malformed_requests_are_denied_without_dispatch(self):
        for value in (None, [], {}, {'action': 'preferences'}, {'action': [], 'data': {}},
                      {'action': 'preferences', 'data': None}, {'action': 'preferences', 'data': []}):
            with self.subTest(request=value), self.assertRaises(SelectionDenied):
                require_action('preferences', value, **context('preferences'))

    def test_inspection_predicate_uses_canonical_policy_not_supplied_allowlist(self):
        packet = {'id': 'preferences', 'actions': {'member': ['build', 'apply', 'finish_day']}, 'routes': ['A', 'B']}
        self.assertFalse(selection_allows(packet, 'build', 'member', 'B'))
        self.assertTrue(selection_allows(packet, 'preferences', 'member', 'B'))
        for invalid in (None, {}, {'id': []}):
            self.assertFalse(selection_allows(invalid, 'preferences', 'member', 'B'))

    def test_guard_never_reads_files_or_modifies_request(self):
        value = {'action': 'preferences', 'data': {'language': 0, 'theme': 'light', 'units': 'metric'}}
        before = copy.deepcopy(value)
        with patch('builtins.open', side_effect=AssertionError('file IO is forbidden')):
            require_action('preferences', value, **context('preferences'))
        self.assertEqual(value, before)


if __name__ == '__main__':
    unittest.main()
