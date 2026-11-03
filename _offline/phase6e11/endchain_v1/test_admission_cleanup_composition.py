"""Orchestration controls with fake collaborators; not PG/Auth evidence."""
import contextlib
import hashlib
import json
import pathlib
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import admission_cleanup_composition as m


class Composition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name)
        self.events = []
        def save(name, value):
            self.events.append('save:' + name)
            with (self.out/name).open('x') as stream:
                json.dump(value, stream)
        self.save = save
        self.gate = types.SimpleNamespace(out=self.out, save=save)
        self.closure = m.Closure(self.gate, save)
        @contextlib.contextmanager
        def suspend():
            self.events.append('suspend')
            try: yield
            finally: self.events.append('resume')
        self.ctx = {'suspend_admin': suspend}

    def ready(self):
        self.closure.scope = Mock()
        self.closure.tracked = Mock()
        self.closure.terminal_ref = {'path': 'terminal.json', 'sha256': 'a'*64}
        folder = self.out/'admission-auth-request-registry'
        folder.mkdir()
        (folder/'closed.json').write_text('{}')
        self.seal = types.SimpleNamespace(refs={'name': 'closed.json',
            'sha256': hashlib.sha256(b'{}').hexdigest()})
        self.auth = types.SimpleNamespace(registry=Mock())
        self.auth.registry.valid_proof.return_value = True

    def test_scope_precedes_registered_factory(self):
        scope = Mock()
        scope.before_bootstrap.side_effect = lambda: self.events.append('baseline')
        with patch.object(m.producer, 'Scope', return_value=scope), \
                patch.object(m.db.TrackedRuntime, 'disposable',
                    side_effect=lambda *_: self.events.append('factory') or 'runtime'):
            self.assertEqual(self.closure.begin(self.ctx), 'runtime')
        self.assertEqual(self.events, ['suspend', 'baseline', 'resume', 'factory'])
        with self.assertRaisesRegex(m.Blocked, 'duplicate_bootstrap'):
            self.closure.begin(self.ctx)

    def test_scope_failure_does_not_mint_fixture_factory(self):
        scope = Mock()
        scope.before_bootstrap.side_effect = RuntimeError('scope')
        with patch.object(m.producer, 'Scope', return_value=scope), \
                patch.object(m.db.TrackedRuntime, 'disposable') as mint:
            with self.assertRaisesRegex(RuntimeError, 'scope'): self.closure.begin(self.ctx)
            mint.assert_not_called()
        self.assertEqual(self.events, ['suspend', 'resume'])

    def test_terminal_requires_sealed_original(self):
        evidence = Mock()
        evidence.get.return_value = {'component_status': 'COMPONENT_PASS',
            'terminal': {'db_terminality_proven': True, 'status': 'NO_GO'}}
        with patch.object(m.parent, 'Evidence', return_value=evidence): self.closure.bind_terminal()
        self.assertEqual(json.loads((self.out/'admission-fixture-terminal.json').read_text())['status'], 'NO_GO')
        evidence.unchanged.assert_called_once()
        self.assertEqual(self.closure.terminal_ref,
            m.file_ref(self.out, 'admission-fixture-terminal.json'))

    def test_missing_terminal_blocks_auth_cleanup(self):
        evidence = Mock()
        evidence.get.return_value = {'component_status': 'NO_GO', 'terminal': {}}
        with patch.object(m.parent, 'Evidence', return_value=evidence):
            with self.assertRaisesRegex(m.Blocked, 'terminal_missing'): self.closure.bind_terminal()
        self.assertEqual(list(self.out.iterdir()), [])

    def test_incomplete_setup_is_not_adopted_by_finalizer(self):
        with patch.object(m.auth_parent, 'finalize') as finish:
            with self.assertRaisesRegex(m.Blocked, 'incomplete_fixture'):
                self.closure.finalize(self.ctx, Mock(), Mock())
            finish.assert_not_called()

    def test_c_physical_closure_precedes_auth_delete(self):
        self.ready()
        folder = self.out/'fixture-parent-physical-zero-private'; folder.mkdir()
        (folder/'result.json').write_text('{}')
        def physical(*args, **kwargs):
            self.events.append('physical')
            return dict.fromkeys(('registry_deletion_proven', 'registry_absence_confirmed',
                'original_receipts_unchanged'), True)
        def finalizer(*args, **kwargs):
            self.events.append('auth')
            self.assertEqual(args[4], m.file_ref(self.out, 'fixture-parent-physical-zero-private/result.json'))
            return {'status': 'TEST_ONLY'}
        previous = Mock(); self.gate.save = previous
        with patch.object(m.physical, 'run', side_effect=physical), \
                patch.object(m.auth_parent, 'finalize', side_effect=finalizer):
            self.assertEqual(self.closure.finalize(self.ctx, self.auth, self.seal), {'status': 'TEST_ONLY'})
        self.assertEqual(self.events, ['suspend', 'physical', 'resume', 'auth'])
        self.assertIs(self.gate.save, previous)
        with self.assertRaisesRegex(m.Blocked, 'duplicate_finalizer'):
            self.closure.finalize(self.ctx, self.auth, self.seal)

    def test_failed_c_never_calls_auth_finalizer_and_restores_namespace(self):
        self.ready()
        previous = Mock(); self.gate.save = previous
        with patch.object(m.physical, 'run', return_value={'registry_deletion_proven': False}), \
                patch.object(m.auth_parent, 'finalize') as finish:
            with self.assertRaisesRegex(m.Blocked, 'registry_closure_incomplete'):
                self.closure.finalize(self.ctx, self.auth, self.seal)
            finish.assert_not_called()
        self.assertIs(self.gate.save, previous)

    def test_forged_auth_record_stops_before_c(self):
        self.ready(); self.seal.refs['sha256'] = 'b'*64
        with patch.object(m.physical, 'run') as run:
            with self.assertRaisesRegex(m.Blocked, 'seal_changed'):
                self.closure.finalize(self.ctx, self.auth, self.seal)
            run.assert_not_called()

    def test_reference_cannot_escape_output(self):
        with self.assertRaisesRegex(m.Blocked, 'parent_receipt_path'):
            m.file_ref(self.out, '../outside.json')


if __name__ == '__main__': unittest.main()
