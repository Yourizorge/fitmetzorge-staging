"""Actual pinned client against a synthetic peer; no database or Docker."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import native_connect_probe as probe


class WireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ["NATIVE_CONNECT_SOURCE"])
        cls.digest = os.environ["NATIVE_CONNECT_SHA"]
        cls.native = probe.load_native(cls.path, cls.digest)
        cls.directory = Path(tempfile.mkdtemp(prefix="native-connect-synthetic-"))
        cls.cert, cls.key = probe.certificates(cls.directory)

    def test_actual_binary_version(self):
        result = probe.identity(self.path)
        self.assertEqual((result["psycopg"], result["binary_package"], result["implementation"]),
                         ("3.2.10", "3.2.10", "binary"))
        self.assertIsInstance(result["libpq_runtime"], int)
        self.assertTrue(any("psycopg_binary/" in p["path"] and p["path"].endswith((".pyd", ".so"))
                            for p in result["files"]))
        self.assertTrue(any("psycopg_binary.libs/" in p["path"] and "libpq" in p["path"]
                            for p in result["files"]))

    def test_source_hash_mismatch_rejected_before_execution(self):
        with self.assertRaisesRegex(ValueError, "native_source_hash"):
            probe.load_native(self.path, "0" * 64)

    def test_missing_origin_rejected(self):
        with self.assertRaises(FileNotFoundError):
            probe.load_native(self.directory / "absent.py", "0" * 64)

    def runtime(self):
        class Endpoint:
            cert = self.cert
            port = 1
        return self.native(probe.parameters(Endpoint), "http://127.0.0.1:59999",
                           environment="disposable_ci")

    def test_clear_rejects_before_driver_dispatch(self):
        with patch.dict(os.environ, {}, clear=True):
            runtime = self.runtime()
            runtime.clear()
            with patch("psycopg.connect") as connect:
                with self.assertRaisesRegex(ValueError, "native_runtime_closed"):
                    runtime.connect()
                connect.assert_not_called()

    def test_postconstruction_environment_guards(self):
        for name, value in (("PGSERVICE", "synthetic"), ("PGSERVICEFILE", "synthetic"),
                            ("PGHOSTADDR", "192.0.2.1")):
            with self.subTest(name=name), patch.dict(os.environ, {}, clear=True):
                runtime = self.runtime()
                with patch.dict(os.environ, {name: value}), patch("psycopg.connect") as connect:
                    with self.assertRaisesRegex(ValueError, "native_loopback"):
                        runtime.connect()
                    connect.assert_not_called()
                runtime.clear()

    def test_service_parameters_rejected_before_driver(self):
        for name in ("service", "servicefile"):
            with self.subTest(name=name), patch.dict(os.environ, {}, clear=True):
                class Endpoint:
                    cert = self.cert
                    port = 1
                params = probe.parameters(Endpoint)
                params[name] = "synthetic"
                with patch("psycopg.connect") as connect:
                    with self.assertRaisesRegex(ValueError, "native_loopback"):
                        self.native(params, "http://127.0.0.1:59999", environment="disposable_ci")
                    connect.assert_not_called()

    def test_prefer_standby_doubles_driver_attempts_without_network(self):
        from psycopg._conninfo_attempts import conninfo_attempts
        with patch.dict(os.environ, {}, clear=True):
            params = {"host": "127.0.0.1", "hostaddr": "127.0.0.1", "port": "5432"}
            self.assertEqual(len(conninfo_attempts(params)), 1)
            attempts = conninfo_attempts({**params, "target_session_attrs": "prefer-standby"})
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]["target_session_attrs"], "standby")

    def test_record_exclusive_and_no_overwrite(self):
        path = self.directory / "exclusive-test.json"
        probe.save(path, {"original": True})
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            probe.save(path, {"original": False})
        self.assertEqual(path.read_bytes(), original)

    def test_actual_source_raw_hash_bound(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), self.digest)


def wire_test(case):
    def check(self):
        result = probe.exercise(self.native, self.cert, self.key, case)
        self.assertEqual(result["sql"], case[-1])
        self.assertFalse(result["database_contacted"])
        self.assertTrue(result["peer_terminal"])
    return check


for case in probe.CASES:
    setattr(WireTests, "test_wire_" + case[0], wire_test(case))


if __name__ == "__main__":
    unittest.main()
