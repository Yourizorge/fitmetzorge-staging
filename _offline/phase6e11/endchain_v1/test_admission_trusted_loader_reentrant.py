"""Reproduce Python 3.12 pathlib lazy imports without bypassing import guards."""
import builtins
import hashlib
import importlib.machinery
import json
import ntpath
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from admission_trusted_loader import PREFIX, TrustedImports, TrustedImportError


class ReentrantTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="loader-reentrant-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.relative = PREFIX + "reentrant_verified_fixture.py"
        self.file = self.root / self.relative
        self.file.parent.mkdir(parents=True)
        self.raw = b"VALUE = 42\n"
        self.file.write_bytes(self.raw)
        self.loader = TrustedImports(self.root, {
            self.relative: hashlib.sha256(self.raw).hexdigest()})

    def lazy_path_import(self, name):
        original = Path.__truediv__

        def divide(path, key):
            # Python 3.12 Path construction imports ntpath even when cached.
            builtins.__import__(name)
            return original(path, key)

        return patch.object(Path, "__truediv__", divide)

    def test_cached_stdlib_reentry_during_source_path_checks(self):
        with self.lazy_path_import("ntpath"):
            with self.loader as loader:
                module = loader.module("reentrant_verified_fixture")
                self.assertEqual(module.VALUE, 42)
                self.assertIs(sys.modules["ntpath"], ntpath)

    def test_source_stdlib_origin_checks_do_not_reenter_pathlib(self):
        with self.lazy_path_import("ntpath"):
            with self.loader as loader:
                loader.guard("json")
                self.assertIs(loader.imported("json"), json)

    def test_reentry_cannot_import_unbound_dependency(self):
        with self.assertRaisesRegex(TrustedImportError, "external_dependency_unbound"):
            with self.lazy_path_import("unbound_reentrant_dependency"):
                with self.loader as loader:
                    loader.module("reentrant_verified_fixture")
        self.assertTrue(self.loader.failed)
        self.assertNotIn("unbound_reentrant_dependency", sys.modules)

    def test_reentry_cannot_import_unlisted_project(self):
        (self.file.parent / "unlisted_reentrant_project.py").write_bytes(b"EXECUTED = True\n")
        with self.assertRaisesRegex(TrustedImportError, "project_module_unlisted"):
            with self.lazy_path_import("unlisted_reentrant_project"):
                with self.loader as loader:
                    loader.module("reentrant_verified_fixture")
        self.assertTrue(self.loader.failed)
        self.assertNotIn("unlisted_reentrant_project", sys.modules)

    def test_cached_stdlib_project_origin_is_still_denied(self):
        impostor = types.ModuleType("ntpath")
        impostor.__spec__ = importlib.machinery.ModuleSpec(
            "ntpath", None, origin=str(self.file))
        with patch.dict(sys.modules, {"ntpath": impostor}):
            with self.assertRaisesRegex(TrustedImportError, "external_origin"):
                with self.lazy_path_import("ntpath"):
                    with self.loader as loader:
                        loader.module("reentrant_verified_fixture")
        self.assertTrue(self.loader.failed)
        self.assertIs(sys.modules["ntpath"], ntpath)


if __name__ == "__main__":
    unittest.main()
