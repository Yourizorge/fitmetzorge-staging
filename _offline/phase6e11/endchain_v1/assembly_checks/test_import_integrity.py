"""Synthetic local loader regressions; no worker, DB, network or full-suite proof."""
from contextlib import contextmanager
import ast
import copy
import importlib
import importlib.machinery
import importlib.util
import marshal
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from assembly_checks import run as r


class ExactImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.sources = {}

    def source(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.sources[name] = r.sha(raw)
        return path

    def policy(self):
        return r.ExactSourceImports(self.root, self.sources, (self.root,))

    @contextmanager
    def installed(self, policy=None):
        policy = policy or self.policy()
        old_meta, old_path = list(sys.meta_path), list(sys.path)
        old_modules = dict(sys.modules)
        try:
            sys.path.insert(0, str(self.root))
            policy.install()
            yield policy
        finally:
            policy.active = False  # Only test-owned audit callback; hooks are process-lifetime.
            sys.meta_path[:] = old_meta
            sys.path[:] = old_path
            for name in set(sys.modules) - set(old_modules):
                sys.modules.pop(name, None)
            for name, module in old_modules.items():
                if sys.modules.get(name) is not module:
                    sys.modules[name] = module

    def test_old_origin_check_accepts_forged_module_new_preflight_rejects(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        fake = types.ModuleType('d07probe'); fake.__file__ = str(path); fake.VALUE = 99
        self.assertEqual(r.check_origin(fake, self.root, self.sources), 'd07probe.py')
        sys.modules['d07probe'] = fake
        try:
            with self.assertRaisesRegex(ValueError, 'import_preloaded:d07probe'):
                self.policy().install()
        finally:
            sys.modules.pop('d07probe', None)

    def test_cache_with_spoofed_outside_origin_rejected_by_name(self):
        self.source('d07probe.py', b'VALUE = 1\n')
        fake = types.ModuleType('d07probe'); fake.__file__ = '/not/the/source.py'
        sys.modules['d07probe'] = fake
        try:
            with self.assertRaisesRegex(ValueError, 'import_preloaded'):
                self.policy().reject_cached()
        finally:
            sys.modules.pop('d07probe', None)

    def test_cached_none_and_namespace_rejected(self):
        self.source('d07pkg/child.py', b'VALUE = 1\n')
        for name, module in (('d07pkg.child', None), ('d07pkg', types.ModuleType('d07pkg'))):
            sys.modules[name] = module
            try:
                with self.assertRaisesRegex(ValueError, 'import_preloaded'):
                    self.policy().reject_cached()
            finally:
                sys.modules.pop(name, None)

    def test_preloaded_alias_rejected_by_origin(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        fake = types.ModuleType('unrelated_alias'); fake.__file__ = str(path)
        sys.modules['unrelated_alias'] = fake
        try:
            with self.assertRaisesRegex(ValueError, 'import_preloaded:unrelated_alias'):
                self.policy().reject_cached()
        finally:
            sys.modules.pop('unrelated_alias', None)

    def poison_cache(self, path):
        cache = Path(importlib.util.cache_from_source(str(path)))
        cache.parent.mkdir(parents=True, exist_ok=True)
        stat = path.stat()
        header = (importlib.util.MAGIC_NUMBER + (0).to_bytes(4, 'little')
                  + (int(stat.st_mtime) & 0xffffffff).to_bytes(4, 'little')
                  + stat.st_size.to_bytes(4, 'little'))
        cache.write_bytes(header + marshal.dumps(compile('VALUE = 999\n', str(path), 'exec')))
        return cache

    def test_valid_timestamp_wrong_pyc_never_executes(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        cache = self.poison_cache(path)
        self.assertEqual(importlib.machinery.SourceFileLoader('d07probe', str(path)).get_code('d07probe').co_consts[0], 999)
        original = cache.read_bytes()
        with self.installed() as policy:
            module = importlib.import_module('d07probe')
            self.assertEqual(module.VALUE, 1)
            policy.verify_loaded()
        self.assertEqual(cache.read_bytes(), original)

    def test_transitive_package_uses_verified_bytes(self):
        self.source('d07pkg/__init__.py', b'from . import child\nVALUE = child.VALUE\n')
        path = self.source('d07pkg/child.py', b'VALUE = 2\n')
        self.poison_cache(path)
        with self.installed() as policy:
            self.assertEqual(importlib.import_module('d07pkg').VALUE, 2)
            policy.verify_loaded()

    def test_transitive_changed_source_fails_before_body(self):
        self.source('d07probe.py', b'import d07child\n')
        path = self.source('d07child.py', b'VALUE = 1\n')
        path.write_bytes(b'raise AssertionError("BODY_EXECUTED")\n')
        with self.installed(), self.assertRaisesRegex(ValueError, 'import_source_hash'):
            importlib.import_module('d07probe')

    def test_unlisted_transitive_fails_before_body(self):
        self.source('d07probe.py', b'import d07child\n')
        (self.root/'d07child.py').write_bytes(b'raise AssertionError("BODY_EXECUTED")\n')
        with self.installed(), self.assertRaisesRegex(ValueError, 'import_source_unlisted'):
            importlib.import_module('d07probe')

    def test_manual_loader_poisoned_pyc_rejected_before_execution(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        self.poison_cache(path)
        with self.installed():
            spec = importlib.util.spec_from_file_location('manual_probe', path)
            module = importlib.util.module_from_spec(spec)
            with self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
                spec.loader.exec_module(module)
            self.assertFalse(hasattr(module, 'VALUE'))

    def test_manual_exact_source_code_allowed_but_cache_registration_not_inferred(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        with self.installed() as policy:
            spec = importlib.util.spec_from_file_location('manual_probe', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.VALUE, 1)
            sys.modules['manual_probe'] = module
            with self.assertRaisesRegex(ValueError, 'import_cache_replaced'):
                policy.verify_loaded()

    def test_cache_replacement_cannot_pass_final_check(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        with self.installed() as policy:
            importlib.import_module('d07probe')
            fake = types.ModuleType('d07probe'); fake.__file__ = str(path)
            sys.modules['d07probe'] = fake
            with self.assertRaisesRegex(ValueError, 'import_cache_replaced'):
                policy.verify_loaded()

    def test_reload_revalidates_bytes(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        with self.installed():
            module = importlib.import_module('d07probe')
            path.write_bytes(b'VALUE = 2\n')
            with self.assertRaisesRegex(ValueError, 'import_source_hash'):
                importlib.reload(module)

    def test_expected_name_external_shadow_rejected_before_execution(self):
        self.source('d07probe.py', b'VALUE = 1\n')
        with tempfile.TemporaryDirectory() as external:
            Path(external, 'd07probe.py').write_bytes(b'raise AssertionError("BODY_EXECUTED")\n')
            with self.installed(), self.assertRaisesRegex(ValueError, 'import_shadow'):
                sys.path.insert(0, external)
                importlib.import_module('d07probe')

    def test_historical_manual_code_rejected(self):
        path = self.source(r.CHECKS+'historical/old.py', b'VALUE = 1\n')
        with self.installed(), self.assertRaisesRegex(ValueError, 'historical_execution_forbidden'):
            exec(compile(path.read_bytes(), str(path), 'exec'), {})

    def test_missing_expected_import_rejected(self):
        path = self.source('d07probe.py', b'VALUE = 1\n'); path.unlink()
        with self.installed(), self.assertRaisesRegex(ValueError, 'import_expected_missing'):
            importlib.import_module('d07probe')

    def test_manual_unbound_external_source_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside)/'unbound.py'
            path.write_bytes(b'VALUE = 1\n')
            with self.installed(), self.assertRaisesRegex(ValueError, 'import_execution_external_unbound'):
                spec = importlib.util.spec_from_file_location('unbound', path)
                spec.loader.exec_module(importlib.util.module_from_spec(spec))

    def test_explicit_dependency_directory_inside_repo_is_separate_trust_domain(self):
        dep = self.root/'deps'; dep.mkdir()
        (dep/'d07dependency.py').write_bytes(b'VALUE = 3\n')
        policy = r.ExactSourceImports(self.root, {}, (self.root,), (dep,))
        with self.installed(policy):
            sys.path.insert(0, str(dep))
            self.assertEqual(importlib.import_module('d07dependency').VALUE, 3)
            policy.verify_loaded()

    def test_metadata_discovery_retained_only_for_explicit_dependency_roots(self):
        dep = self.root/'deps'; dep.mkdir()
        info = dep/'d08fixture-1.2.3.dist-info'; info.mkdir()
        (info/'METADATA').write_bytes(b'Metadata-Version: 2.1\nName: d08fixture\nVersion: 1.2.3\n')
        unbound = self.root/'unbound'; unbound.mkdir()
        fake = unbound/'d08fixture-9.9.9.dist-info'; fake.mkdir()
        (fake/'METADATA').write_bytes(b'Metadata-Version: 2.1\nName: d08fixture\nVersion: 9.9.9\n')
        policy = r.ExactSourceImports(self.root, {}, (self.root,), (dep,))
        with self.installed(policy):
            sys.path[:0] = [str(unbound), str(dep)]
            self.assertEqual(importlib.metadata.version('d08fixture'), '1.2.3')

    def test_no_partial_pass_after_transitive_failure(self):
        self.source('d07probe.py', b'VALUE = 1\nimport d07child\nCOMPLETE = True\n')
        path = self.source('d07child.py', b'VALUE = 1\n'); path.write_bytes(b'VALUE = 2\n')
        with self.installed():
            with self.assertRaisesRegex(ValueError, 'import_source_hash'):
                importlib.import_module('d07probe')
            self.assertNotIn('d07probe', sys.modules)

    def test_caught_unlisted_transitive_failure_remains_latched(self):
        self.source('d07probe.py', b'try:\n    import d07child\nexcept ValueError:\n    pass\nVALUE = 1\n')
        (self.root/'d07child.py').write_bytes(b'raise AssertionError("BODY_EXECUTED")\n')
        with self.installed() as policy:
            module = importlib.import_module('d07probe')
            self.assertEqual(module.VALUE, 1)
            with self.assertRaisesRegex(ValueError, 'import_previous_failure'):
                policy.verify_loaded()

    def test_caught_custom_loader_denial_remains_latched(self):
        path = self.source('d07probe.py', b'VALUE = 1\n')
        self.poison_cache(path)
        with self.installed() as policy:
            spec = importlib.util.spec_from_file_location('manual_probe', path)
            with self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
                spec.loader.exec_module(importlib.util.module_from_spec(spec))
            with self.assertRaisesRegex(ValueError, 'import_previous_failure'):
                policy.verify_loaded()


class ExtendedPathTests(unittest.TestCase):
    def test_extended_paths_do_not_disable_link_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'source.py').write_bytes(b'pass\n')
            with patch.object(Path, 'is_symlink', return_value=True):
                with self.assertRaisesRegex(ValueError, 'source_link'):
                    r.read(temp, 'source.py')

    def test_drive_unc_and_idempotent_extended_forms(self):
        for path, expected in ((r'C:\repo\file.py', r'\\?\C:\repo\file.py'),
                               (r'\\server\share\file.py', r'\\?\UNC\server\share\file.py')):
            self.assertEqual(r.windows_extended(path), expected)
            self.assertEqual(r.windows_extended(expected), expected)

    def test_device_relative_and_drive_relative_rejected(self):
        for path in (r'\\.\PhysicalDrive0', 'relative/file', 'C:relative', r'\\?\GLOBALROOT\Device\disk'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                r.windows_extended(path)

    def test_real_long_path_read_retains_hash_and_escape_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = r.io_path(temp)
            name = '/'.join(['historical'] + ['part' + 'x'*35]*7 + ['source.py'])
            path = root/name
            path.parent.mkdir(parents=True)
            path.write_bytes(b'VALUE = 1\n')
            try:
                self.assertGreater(len(str(path)), 260)
                self.assertEqual(r.read(temp, name), b'VALUE = 1\n')
                with self.assertRaisesRegex(ValueError, 'source_path'):
                    r.read(temp, '../escape.py')
                with self.assertRaisesRegex(ValueError, 'source_path'):
                    r.read(temp, str(path))
            finally:
                path.unlink()
                for parent in path.parents:
                    if parent == root:
                        break
                    parent.rmdir()


class RecoveryFragmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = {}
        for path, (pin, _) in r.RECOVERY_FRAGMENTS.items():
            raw = r.read(r.SOURCE_ROOT, path)
            self.assertEqual(r.sha(raw), pin)
            target = self.root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            self.sources[path] = pin
        self.policy = r.ExactSourceImports(self.root, self.sources, (self.root,))

    def selected(self, name, names, change=False):
        path = self.root/name
        tree = ast.parse(path.read_bytes())
        body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                and node.name in names]
        if change:
            body = copy.deepcopy(body)
            body[0].body.insert(0, ast.copy_location(ast.Expr(value=ast.Constant('changed body')), body[0]))
        return compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), str(path), 'exec')

    def test_exact_four_existing_fragment_codeobjects_are_accepted(self):
        seen = 0
        for name, (_, selections) in r.RECOVERY_FRAGMENTS.items():
            for names in selections:
                code = self.selected(name, names)
                self.assertTrue(self.policy.recovery_fragment(self.root/name, code))
                self.policy._audit_execution(code)
                seen += 1
        self.assertEqual(seen, 4)

    def test_allowlist_matches_original_production_pins(self):
        tree = ast.parse(r.read(r.SOURCE_ROOT, r.PREFIX+'admission_budget_recovery_program.py'))
        pins = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'PINS' for target in node.targets))
        self.assertEqual({Path(name).name: pin for name, (pin, _) in r.RECOVERY_FRAGMENTS.items()}, pins)

    def test_wrong_function_rejected_even_in_pinned_source(self):
        name = r.PREFIX+'control_recovery.py'
        for names in (('intent',), ('recover',), ('replace_setup', 'recover', 'intent')):
            with self.subTest(names=names):
                code = self.selected(name, names)
                self.assertFalse(self.policy.recovery_fragment(self.root/name, code))
                with self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
                    self.policy._audit_execution(code)

    def test_modified_body_is_not_same_fragment(self):
        for name, (_, selections) in r.RECOVERY_FRAGMENTS.items():
            for names in selections:
                code = self.selected(name, names, change=True)
                with self.subTest(names=names), self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
                    self.policy._audit_execution(code)

    def test_changed_source_and_repinned_candidate_do_not_override_original_pins(self):
        name = r.PREFIX+'control_recovery.py'
        code = self.selected(name, ('replace_setup', 'recover'))
        raw = (self.root/name).read_bytes()+b'\n# changed source\n'
        (self.root/name).write_bytes(raw)
        self.policy.sources[name] = r.sha(raw)
        with self.assertRaisesRegex(ValueError, 'import_fragment_source_binding'):
            self.policy._audit_execution(code)

    def test_wrong_candidate_pin_or_missing_pin_is_rejected(self):
        name = r.PREFIX+'control_recovery.py'
        code = self.selected(name, ('replace_setup', 'recover'))
        for value in (None, '0'*64):
            self.policy.sources[name] = value
            with self.subTest(pin=value), self.assertRaisesRegex(ValueError, 'import_fragment_source_binding'):
                self.policy.recovery_fragment(self.root/name, code)

    def test_same_named_functions_in_different_file_not_allowed(self):
        name = r.PREFIX+'control_recovery.py'
        alias = r.PREFIX+'other_control.py'
        raw = (self.root/name).read_bytes()
        (self.root/alias).write_bytes(raw)
        self.policy.sources[alias] = r.sha(raw)
        code = self.selected(alias, ('replace_setup', 'recover'))
        with self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
            self.policy._audit_execution(code)

    def test_wrong_fragment_denial_stays_latched(self):
        name = r.PREFIX+'control_recovery.py'
        self.policy.active = True
        with self.assertRaisesRegex(ValueError, 'import_execution_not_exact_source'):
            self.policy.audit('exec', (self.selected(name, ('intent',)),))
        with self.assertRaisesRegex(ValueError, 'import_previous_failure'):
            self.policy.verify_loaded()


if __name__ == '__main__':
    unittest.main()
