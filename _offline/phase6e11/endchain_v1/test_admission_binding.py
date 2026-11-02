"""Synthetic binding tests, not permission to connect to staging."""
import copy
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import admission_binding as b


class BindingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.sources = {}
        self.registers = {}
        for name in b.REQUIRED:
            path = name + '.json'
            data = b.canonical({'fixture': name})
            (self.root / path).write_bytes(data)
            self.sources[path] = b.sha(data)
            self.registers[name] = {'path': path, 'sha256': b.sha(data)}
        (self.root / 'old.sql').write_bytes(b'old source retained')
        self.pins = {'old.sql': b.sha(b'old source retained')}
        preserve = patch.object(b, 'PRESERVED', self.pins)
        preserve.start(); self.addCleanup(preserve.stop)
        self.args = dict(source_commit='a'*40, candidate_sha256='b'*64,
            sources=self.sources, registers=self.registers,
            created_at='2026-11-02T12:00:00Z', expires_at='2026-11-03T12:00:00Z')
        self.now = '2026-11-02T12:01:00Z'

    def value(self):
        return b.prepare(self.root, **self.args)

    def test_new_binding_never_grants_hosted_execution(self):
        value = self.value()
        result = b.readiness(value, self.root, self.now)
        self.assertNotEqual(value['run_id'], b.OLD_RUN)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertTrue(b.GATES <= set(result['blockers']))
        self.assertFalse(result['hosted_admitted'])
        self.assertEqual((self.root/'old.sql').read_bytes(), b'old source retained')

    def test_old_run_and_project_substitution_blocked(self):
        for key, val in (('run_id', b.OLD_RUN), ('old_run_reused', True),
                         ('project', 'other'), ('branch', 'feature'), ('repository', 'other')):
            with self.subTest(key=key):
                value = self.value(); value[key] = val
                with self.assertRaises(ValueError): b.validate(value, self.root, self.now)

    def test_permissions_and_higher_budget_not_inferred(self):
        for key, val in (('hosted_permission', True), ('hosted_admitted', True),
                         ('maximum_sql', 2350), ('maximum_sql', True)):
            with self.subTest(key=key):
                value = self.value(); value[key] = val
                with self.assertRaises(ValueError): b.validate(value, self.root, self.now)

    def test_boundary_expiry_and_future(self):
        value = self.value()
        for now in ('2026-11-02T11:59:59Z', '2026-11-03T12:00:00Z'):
            with self.assertRaisesRegex(ValueError, 'expired_or_future'):
                b.validate(value, self.root, now)
        b.validate(value, self.root, '2026-11-03T11:59:59Z')

    def test_timestamp_requires_utc_and_bounded_preparation(self):
        for end in ('2026-11-04T12:00:00Z', self.args['created_at'], '2026-11-03T12:00:00', 'bad'):
            with self.assertRaises(ValueError): b.prepare(self.root, **{**self.args, 'expires_at': end})

    def test_changed_old_binding_or_source_blocks(self):
        value = self.value()
        (self.root/'old.sql').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'source_changed'): b.validate(value, self.root, self.now)
        (self.root/'old.sql').write_bytes(b'old source retained')
        (self.root/'sql_register.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'source_changed'): b.validate(value, self.root, self.now)

    def test_all_registers_must_be_exact_source_members(self):
        for key in b.REQUIRED:
            args = copy.deepcopy(self.args); del args['registers'][key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'register_set'):
                b.prepare(self.root, **args)
        args = copy.deepcopy(self.args); args['registers']['cleanup_plan']['sha256'] = 'c'*64
        with self.assertRaisesRegex(ValueError, 'not_source_bound'): b.prepare(self.root, **args)

    def test_paths_and_case_aliases(self):
        for name in ('../outside', '/absolute', 'C:/absolute', 'a\\b', './old.sql'):
            with self.subTest(name=name), self.assertRaises(ValueError): b.source_path(self.root, name)
        with self.assertRaises(ValueError):
            b.verify_sources(self.root, {'old.sql': self.pins['old.sql'], 'OLD.SQL': self.pins['old.sql']})

    def test_ci_binding_calls_full_verifier_and_propagates_blockers(self):
        value = self.value()
        with patch('closure_ops.validate_bundle', side_effect=ValueError('closure_endchain_incomplete')) as verify:
            with self.assertRaisesRegex(ValueError, 'closure_endchain_incomplete'):
                b.attach_ci(value, chain=self.root/'chain', app=self.root/'app', root=self.root, now=self.now)
            verify.assert_called_once_with(self.root/'chain', self.root/'app', root=self.root)
        self.assertIsNone(value['ci'])

    def test_component_result_cannot_bind_as_complete(self):
        with patch('closure_ops.validate_bundle', return_value={'status': 'CLEAN_CI_PASS'}):
            with self.assertRaisesRegex(ValueError, 'complete_ci_required'):
                b.attach_ci(self.value(), chain=self.root/'chain', app=self.root/'app', root=self.root, now=self.now)

    def test_claimed_pass_is_not_artifact_verification_or_authority(self):
        value = self.value(); value['gates'] = {k: 'PASS' for k in b.GATES}
        self.assertIn('same_source_ci', b.readiness(value, self.root, self.now)['blockers'])
        value['ci'] = {'unit_fixture': True}
        with self.assertRaisesRegex(ValueError, 'ci_shape'): b.readiness(value, self.root, self.now)
        value['ci'] = None
        result = b.readiness(value, self.root, self.now)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertFalse(result['hosted_admitted'])
        self.assertFalse(result['owner_window_allowed'])

    def test_missing_wal_gate_cannot_hide_blocker(self):
        value = self.value(); del value['gates']['strict_wal']
        with self.assertRaisesRegex(ValueError, 'gate_set'): b.validate(value, self.root, self.now)


if __name__ == '__main__': unittest.main()
