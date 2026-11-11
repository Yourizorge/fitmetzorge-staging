"""Synthetic import fixtures only. No network, database or Main writes."""
import builtins
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import py_compile
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from admission_trusted_loader import PREFIX, TrustedImports, TrustedImportError

HERE = Path(__file__).resolve().parent
PKG = "a_verified_fixture_pkg"
LEAF = "a_verified_fixture_leaf"


class LoaderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fmz-trusted-loader-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.sources = {}
        self.base = self.root / PREFIX
        self.base.mkdir(parents=True)
        self.initial_hooks = (builtins.__import__, importlib.import_module,
                              importlib.util.spec_from_file_location, tuple(sys.meta_path))
        self.external = {}

    def tearDown(self):
        for name, value in self.external.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
        self.assertEqual(self.initial_hooks, (builtins.__import__, importlib.import_module,
            importlib.util.spec_from_file_location, tuple(sys.meta_path)))

    def source(self, name, text, package=False, register=True):
        relative = PREFIX + name.replace(".", "/") + ("/__init__.py" if package else ".py")
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
        if register:
            self.sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def seed(self, name, module):
        if name not in self.external:
            self.external[name] = sys.modules.get(name)
        sys.modules[name] = module

    def loader(self):
        return TrustedImports(self.root, self.sources)

    def test_exact_parent_relative_absolute_dynamic_and_lazy_imports(self):
        self.source(PKG, "TOKEN = 'parent'\n", package=True)
        self.source(LEAF, "VALUE = 13\n")
        self.source(PKG + ".child", "from dataclasses import dataclass\nimport " + LEAF
            + "\n@dataclass\nclass Result:\n    value: int\n"
              "def call():\n    from . import other\n    return Result(other.VALUE)\n")
        self.source(PKG + ".other", "from " + LEAF + " import VALUE\n")
        self.source(PKG + ".entry", "import importlib\nfrom . import child\n"
            "def run():\n    return importlib.import_module('.child', __package__).call()\n")
        with self.loader() as loader:
            entry = loader.module(PKG + ".entry")
            result = entry.run()
            self.assertEqual(result.value, 13)
            self.assertEqual(type(result).__module__, PKG + ".child")
            self.assertIs(loader.module(PKG + ".child").Result, type(result))
            self.assertEqual(sys.modules[PKG].TOKEN, "parent")
        self.assertNotIn(PKG, sys.modules)
        self.assertNotIn(LEAF, sys.modules)

    def test_from_import_dynamic_function_and_dotted_import(self):
        self.source(PKG, "", package=True)
        self.source(PKG + ".child", "VALUE = 21\n")
        self.source(PKG + ".entry", "from importlib import import_module\n"
            "import " + PKG + ".child as child\n"
            "def run():\n    return import_module(__package__ + '.child') is child\n")
        with self.loader() as loader:
            self.assertTrue(loader.module(PKG + ".entry").run())

    def test_stale_parent_and_child_pyc_are_never_executed(self):
        self.source(PKG, "VALUE = 'OLD'\n", package=True)
        child = self.source(PKG + ".child", "VALUE = 'OLD'\n")
        parent = child.parent / "__init__.py"
        for path in (parent, child):
            stat = path.stat()
            py_compile.compile(str(path), doraise=True,
                invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            path.write_bytes(path.read_bytes().replace(b"OLD", b"NEW"))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.sources[path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        before = {p: p.read_bytes() for p in self.base.rglob("*.pyc")}
        with self.loader() as loader:
            self.assertEqual(loader.module(PKG + ".child").VALUE, "NEW")
            self.assertEqual(loader.module(PKG).VALUE, "NEW")
        self.assertEqual(before, {p: p.read_bytes() for p in self.base.rglob("*.pyc")})

    def test_direct_preexisting_cache_denied_even_same_origin_and_hash(self):
        path = self.source(LEAF, "VALUE = 'approved'\n")
        old = types.ModuleType(LEAF)
        old.__file__ = str(path)
        old.VALUE = "stale"
        self.seed(LEAF, old)
        with self.assertRaisesRegex(TrustedImportError, "trusted_preexisting_module"):
            with self.loader() as loader:
                loader.module(LEAF)
        self.assertIs(sys.modules[LEAF], old)
        self.assertEqual(old.VALUE, "stale")

    def test_transitive_cached_leaf_denied_without_replacement(self):
        self.source(LEAF, "VALUE = 'approved'\n")
        self.source(PKG, "import " + LEAF + "\n", package=True)
        old = types.ModuleType(LEAF)
        self.seed(LEAF, old)
        with self.assertRaisesRegex(TrustedImportError, "trusted_preexisting_module:" + LEAF):
            with self.loader() as loader:
                loader.module(PKG)
        self.assertIs(sys.modules[LEAF], old)
        self.assertNotIn(PKG, sys.modules)

    def test_cached_parent_denied_before_any_child_execution(self):
        self.source(PKG, "", package=True)
        self.source(PKG + ".child", "raise AssertionError('must not execute')\n")
        old = types.ModuleType(PKG)
        self.seed(PKG, old)
        with self.assertRaisesRegex(TrustedImportError, "trusted_preexisting_module:" + PKG):
            with self.loader() as loader:
                loader.module(PKG + ".child")
        self.assertIs(sys.modules[PKG], old)

    def test_parent_attribute_cannot_reexport_unverified_cached_child(self):
        self.source(PKG, "import sys\nchild=sys.modules['" + PKG + ".child']\n", package=True)
        self.source(PKG + ".child", "VALUE='approved'\n")
        self.source(LEAF, "from " + PKG + " import child\nVALUE=child.VALUE\n")
        stale = types.ModuleType(PKG + ".child")
        stale.VALUE = "stale"
        self.seed(PKG + ".child", stale)
        with self.assertRaisesRegex(TrustedImportError, "trusted_preexisting_module"):
            with self.loader() as loader:
                loader.module(LEAF)
        self.assertIs(sys.modules[PKG + ".child"], stale)

    def test_missing_parent_pin_denied(self):
        self.source(PKG, "", package=True, register=False)
        self.source(PKG + ".child", "VALUE=1\n")
        with self.assertRaisesRegex(TrustedImportError, "unlisted:" + PKG):
            with self.loader() as loader:
                loader.module(PKG + ".child")

    def test_unlisted_transitive_installed_source_denied(self):
        self.source(LEAF, "raise AssertionError('must not execute')\n", register=False)
        self.source(PKG, "import " + LEAF + "\n", package=True)
        with self.assertRaisesRegex(TrustedImportError, "unlisted:" + LEAF):
            with self.loader() as loader:
                loader.module(PKG)

    def test_no_fallback_to_artifact_or_other_sys_path_source(self):
        path = self.source(LEAF, "VALUE='installed'\n")
        artifact = self.root / "artifact"
        artifact.mkdir()
        (artifact / (LEAF + ".py")).write_text("raise AssertionError('artifact executed')\n")
        with patch.object(sys, "path", [str(artifact), *sys.path]):
            with self.loader() as loader:
                self.assertEqual(loader.module(LEAF).VALUE, "installed")
                self.assertEqual(loader.module(LEAF).__file__, str(path))

    def test_missing_installed_file_cannot_fallback_to_artifact(self):
        path = self.source(LEAF, "VALUE=1\n")
        path.unlink()
        with self.assertRaisesRegex(TrustedImportError, "trusted_source_io"):
            with self.loader() as loader:
                loader.module(LEAF)

    def test_hash_mismatch_stops_before_execution(self):
        path = self.source(LEAF, "VALUE=1\n")
        path.write_text("raise AssertionError('changed code executed')\n")
        with self.assertRaisesRegex(TrustedImportError, "trusted_source_hash"):
            with self.loader() as loader:
                loader.module(LEAF)

    def test_exact_verified_buffer_not_a_second_file_read_for_execution(self):
        path = self.source(LEAF, "VALUE='approved'\n")
        original = TrustedImports.create_module
        def race(loader, spec):
            path.write_text("raise AssertionError('unverified bytes executed')\n")
            return original(loader, spec)
        with patch.object(TrustedImports, "create_module", race):
            with self.assertRaisesRegex(TrustedImportError, "trusted_source_hash"):
                with self.loader() as loader:
                    loader.module(LEAF)

    def test_changed_owned_dependency_denied_on_reuse(self):
        path = self.source(LEAF, "VALUE=1\n")
        with self.assertRaisesRegex(TrustedImportError, "trusted_source_hash"):
            with self.loader() as loader:
                loader.module(LEAF)
                path.write_text("VALUE=2\n")
                loader.module(LEAF)

    def test_legacy_manual_file_loader_is_explicitly_blocked(self):
        self.source(LEAF, "import importlib.util\n"
            "importlib.util.spec_from_file_location('alias', __file__)\n")
        with self.assertRaisesRegex(TrustedImportError, "trusted_file_loader_unsupported:alias"):
            with self.loader() as loader:
                loader.module(LEAF)

    def test_unbound_third_party_dependency_is_not_imported(self):
        self.source(LEAF, "import unbound_external_fixture\n")
        with self.assertRaisesRegex(TrustedImportError, "external_dependency_unbound:unbound_external_fixture"):
            with self.loader() as loader:
                loader.module(LEAF)

    def test_cached_stdlib_shadow_with_project_origin_denied(self):
        self.source(LEAF, "import fractions\n")
        fake = types.ModuleType("fractions")
        fake.__spec__ = importlib.machinery.ModuleSpec("fractions", None,
            origin=str(self.root / "artifact.py"))
        self.seed("fractions", fake)
        with self.assertRaisesRegex(TrustedImportError, "external_origin:fractions"):
            with self.loader() as loader:
                loader.module(LEAF)

    def test_unchanged_global_modules_not_removed_or_replaced(self):
        self.source(LEAF, "import hashlib\nVALUE=hashlib.sha256(b'').hexdigest()\n")
        original = sys.modules["hashlib"]
        with self.loader() as loader:
            loader.module(LEAF)
            self.assertIs(sys.modules["hashlib"], original)
        self.assertIs(sys.modules["hashlib"], original)

    def test_failed_module_restores_hooks_and_preserves_primary_exception(self):
        self.source(LEAF, "raise LookupError('primary fixture failure')\n")
        with self.assertRaisesRegex(LookupError, "primary fixture failure"):
            with self.loader() as loader:
                loader.module(LEAF)
        self.assertNotIn(LEAF, sys.modules)

    def test_caught_failed_import_cannot_return_success_on_context_exit(self):
        self.source(LEAF, "raise ValueError('failure')\n")
        with self.assertRaisesRegex(TrustedImportError, "session_inactive"):
            with self.loader() as loader:
                try:
                    loader.module(LEAF)
                except ValueError:
                    pass

    def test_nested_session_is_denied_without_disturbing_outer(self):
        self.source(LEAF, "VALUE=1\n")
        with self.loader() as loader:
            with self.assertRaisesRegex(TrustedImportError, "session_busy"):
                with self.loader():
                    pass
            self.assertEqual(loader.module(LEAF).VALUE, 1)

    def test_existing_custom_import_hook_is_not_overwritten(self):
        self.source(LEAF, "VALUE=1\n")
        original = builtins.__import__
        def prior_hook(*args, **kwargs):
            return original(*args, **kwargs)
        with patch.object(builtins, "__import__", prior_hook):
            with self.assertRaisesRegex(TrustedImportError, "preexisting_import_hook"):
                with self.loader():
                    pass
            self.assertIs(builtins.__import__, prior_hook)

    def test_concurrent_process_thread_denied_before_global_mutation(self):
        self.source(LEAF, "VALUE=1\n")
        stop = threading.Event()
        thread = threading.Thread(target=stop.wait)
        thread.start()
        try:
            with self.assertRaisesRegex(TrustedImportError, "session_busy_or_concurrent"):
                with self.loader():
                    pass
            self.assertEqual(builtins.__import__, self.initial_hooks[0])
        finally:
            stop.set()
            thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_lazy_import_after_scope_closed_is_denied(self):
        self.source(LEAF, "def later():\n    import json\n    return json\n")
        with self.loader() as loader:
            module = loader.module(LEAF)
        with self.assertRaisesRegex(TrustedImportError, "session_inactive"):
            module.later()

    def test_bound_module_rejects_different_root_or_source_inventory(self):
        self.source(LEAF, "VALUE=1\n")
        with self.assertRaisesRegex(TrustedImportError, "context_binding"):
            with self.loader() as loader:
                loader.bound_module(LEAF, self.root, {})

    def test_module_replacement_and_import_hook_tampering_fail_closed(self):
        self.source(LEAF, "VALUE=1\n")
        for mode in ("module", "hook"):
            with self.subTest(mode=mode):
                loader = self.loader()
                with self.assertRaises(TrustedImportError):
                    with loader:
                        loader.module(LEAF)
                        if mode == "module":
                            sys.modules[LEAF] = types.ModuleType(LEAF)
                        else:
                            importlib.import_module = lambda *args: None
                if mode == "module":
                    self.assertIsNot(sys.modules[LEAF], loader.owned[LEAF])
                    del sys.modules[LEAF]

    def test_adapter_unchanged_public_trusted_api_joins_entire_session(self):
        package = "quota_candidate_v1"
        self.source(package, "", package=True)
        self.source(package + ".runtime_exported_terminal",
                    (HERE / "quota_candidate_v1/runtime_exported_terminal.py").read_text())
        self.source(LEAF, "VALUE=31\n")
        with self.loader() as loader:
            reader = loader.module(package + ".runtime_exported_terminal")
            trusted = reader.Trusted(self.root, self.sources)
            self.assertEqual(trusted.module(LEAF).VALUE, 31)
            self.assertIs(trusted.module(LEAF), loader.module(LEAF))

    def test_aliasing_or_traversal_source_inventory_rejected(self):
        self.source(LEAF, "VALUE=1\n")
        for key in ("../escape.py", PREFIX + "a/../escape.py", "/" + LEAF,
                    PREFIX + "CON.py", PREFIX + "ending./file.py"):
            with self.subTest(key=key), self.assertRaisesRegex(TrustedImportError, "source_entry"):
                TrustedImports(self.root, {key: "0"*64})

    def test_symbolic_source_link_denied_without_execution(self):
        target = self.source(LEAF, "VALUE=1\n")
        alias = self.base / "a_verified_fixture_alias.py"
        try:
            alias.symlink_to(target)
        except OSError:
            self.skipTest("OS does not permit unprivileged symlink creation")
        self.sources[alias.relative_to(self.root).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        with self.assertRaisesRegex(TrustedImportError, "source_origin"):
            with self.loader() as loader:
                loader.module("a_verified_fixture_alias")


if __name__ == "__main__":
    unittest.main()
