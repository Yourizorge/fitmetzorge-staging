"""Offline real-file origin checks; no CI, database or network dispatch."""
import importlib.util
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import admission_module_binding as binding


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fmz-module-binding-')
        self.addCleanup(self.temp.cleanup)
        self.top = pathlib.Path(self.temp.name).resolve()
        self.checkout = self.top / 'checkout'
        self.candidate = self.top / 'candidate'
        self.out = self.top / 'out'
        for root in (self.checkout, self.candidate, self.out): root.mkdir()
        self.relative = '_offline/component/helper.py'
        for root in (self.checkout, self.candidate):
            path = root / self.relative
            path.parent.mkdir(parents=True)
            path.write_bytes(b'value = 1\n')
        self.sources = {self.relative: binding.sha(b'value = 1\n')}
        self.manifest()
        self.gate = types.SimpleNamespace(sources=self.candidate, out=self.out)
        env = patch.dict(os.environ, {'GITHUB_WORKSPACE': str(self.checkout)})
        env.start(); self.addCleanup(env.stop)

    def manifest(self):
        (self.out / 'candidate.json').write_text(json.dumps({'sources': self.sources}))

    def module(self, root=None):
        path = (root or self.checkout) / self.relative
        spec = importlib.util.spec_from_file_location('binding_test_helper', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_both_real_loaded_roots_and_json_safe_receipt(self):
        result = binding.verify(self.gate, [self.module(), self.module(self.candidate)])
        self.assertEqual(result['status'], 'SELECTED_MODULE_SOURCE_BINDING_PASS')
        self.assertEqual([r['origin_root'] for r in result['modules']], ['checkout', 'candidate'])
        self.assertEqual(json.loads(json.dumps(result)), result)
        self.assertFalse(result['hosted_admitted'])

    def test_checkout_crlf_only_records_both_digests(self):
        (self.checkout / self.relative).write_bytes(b'value = 1\r\n')
        record = binding.verify(self.gate, [self.module()])['modules'][0]
        self.assertNotEqual(record['actual_sha256'], record['candidate_sha256'])
        self.assertEqual(record['canonicalization'], 'CRLF-to-LF-only')

    def test_same_basename_external_identical_module_rejected(self):
        external = self.top / 'external'
        path = external / self.relative
        path.parent.mkdir(parents=True); path.write_bytes(b'value = 1\n')
        with self.assertRaisesRegex(binding.ModuleBindingError, 'external_origin'):
            binding.verify(self.gate, [self.module(external)])

    def test_changed_checkout_bytes_and_extra_whitespace_rejected(self):
        for data in (b'value = 2\n', b'value = 1 \n', b'value = 1\r'):
            (self.checkout / self.relative).write_bytes(data)
            with self.assertRaisesRegex(binding.ModuleBindingError, 'loaded_source_changed'):
                binding.verify(self.gate, [self.module()])

    def test_changed_candidate_bytes_including_crlf_rejected(self):
        for data in (b'value = 2\n', b'value = 1\r\n'):
            (self.candidate / self.relative).write_bytes(data)
            with self.assertRaisesRegex(binding.ModuleBindingError, 'candidate_hash'):
                binding.verify(self.gate, [self.module(self.candidate)])

    def test_origin_absence_and_non_module_rejected(self):
        for module in (types.ModuleType('missing'), types.SimpleNamespace(__file__=str(self.checkout/self.relative))):
            with self.assertRaises(binding.ModuleBindingError): binding.verify(self.gate, [module])

    def test_missing_workspace_never_falls_back_to_cwd(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(binding.ModuleBindingError, 'path_missing'):
            binding.verify(self.gate, [self.module()])

    def test_empty_selection_and_unregistered_source_rejected(self):
        with self.assertRaisesRegex(binding.ModuleBindingError, 'empty_selection'):
            binding.verify(self.gate, [])
        self.sources = {}; self.manifest()
        with self.assertRaisesRegex(binding.ModuleBindingError, 'source_not_registered'):
            binding.verify(self.gate, [self.module()])

    def test_candidate_nested_in_checkout_is_classified_as_candidate(self):
        nested = self.checkout / 'candidate'
        path = nested / self.relative
        path.parent.mkdir(parents=True); path.write_bytes(b'value = 1\n')
        self.gate.sources = nested
        record = binding.verify(self.gate, [self.module(nested)])['modules'][0]
        self.assertEqual(record['origin_root'], 'candidate')

    def test_symlink_checks_cover_actual_ancestor_candidate_and_root(self):
        module = self.module()
        original = pathlib.Path.is_symlink
        for forbidden in (self.checkout/self.relative, (self.checkout/self.relative).parent,
                          self.candidate/self.relative, self.checkout):
            def is_link(path):
                return path == forbidden or original(path)
            with self.subTest(path=str(forbidden)), patch.object(pathlib.Path, 'is_symlink', is_link):
                with self.assertRaisesRegex(binding.ModuleBindingError, 'symlink'):
                    binding.verify(self.gate, [module])

    def test_explicit_helper_is_checked_even_when_first_module_valid(self):
        valid = self.module()
        external = self.top / 'external'
        path = external/self.relative
        path.parent.mkdir(parents=True); path.write_bytes(b'value = 1\n')
        with self.assertRaisesRegex(binding.ModuleBindingError, 'external_origin'):
            binding.verify(self.gate, [valid, self.module(external)])

    def test_manifest_duplicate_keys_rejected(self):
        (self.out/'candidate.json').write_text('{"sources":{},"sources":{}}')
        with self.assertRaisesRegex(binding.ModuleBindingError, 'duplicate_manifest_key'):
            binding.verify(self.gate, [self.module()])

    def test_symlink_file_and_ancestor_rejected(self):
        link = self.top / 'alias'
        try:
            link.symlink_to(self.checkout, target_is_directory=True)
        except OSError as error:
            self.skipTest('OS does not permit symlink creation: ' + type(error).__name__)
        module = self.module()
        module.__file__ = str(link / self.relative)
        with self.assertRaisesRegex(binding.ModuleBindingError, 'symlink'):
            binding.verify(self.gate, [module])
        filelink = self.checkout / 'linked.py'
        filelink.symlink_to(self.checkout/self.relative)
        module.__file__ = str(filelink)
        with self.assertRaisesRegex(binding.ModuleBindingError, 'symlink'):
            binding.verify(self.gate, [module])

    def test_symlink_candidate_and_trusted_root_rejected(self):
        link = self.top / 'candidate-alias'
        try:
            link.symlink_to(self.candidate, target_is_directory=True)
        except OSError as error:
            self.skipTest('OS does not permit symlink creation: ' + type(error).__name__)
        self.gate.sources = link
        with self.assertRaisesRegex(binding.ModuleBindingError, 'symlink'):
            binding.verify(self.gate, [self.module()])
        self.gate.sources = self.candidate
        (self.candidate/self.relative).unlink()
        (self.candidate/self.relative).symlink_to(self.checkout/self.relative)
        with self.assertRaisesRegex(binding.ModuleBindingError, 'symlink'):
            binding.verify(self.gate, [self.module()])


if __name__ == '__main__': unittest.main()
