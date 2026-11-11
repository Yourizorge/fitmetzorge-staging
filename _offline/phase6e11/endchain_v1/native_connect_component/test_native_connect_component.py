"""Offline adapter tests; fake connection objects are not Linux wire evidence."""
import hashlib
from contextlib import nullcontext
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock
import uuid

import native_connect_component as component

PROBE = Path(os.environ.get("C_NATIVE_PROBE_SOURCE", str(Path(__file__).with_name("native_connect_probe.py"))))
NATIVE = Path(os.environ.get("C_NATIVE_RUNTIME_SOURCE",
    "C:/Users/Fitme/OneDrive/Documenten/Fit Met Zorge/Zip github fitmetzorge staging/fitmetzorge-staging-main/supabase/.temp/phase4fb-staging-deploy/_offline/phase6e11/endchain_v1/native_runtime.py"))


class ComponentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.probe = component.load_probe(PROBE)
        self.cert = self.root / "cert.pem"
        self.cert.write_text("SYNTHETIC_PUBLIC_TEST_CERT")
        self.peer = NS(port=12345, cert=self.cert, sock=NS(getsockname=lambda: ("127.0.0.1", 12345)))
        self.params = self.probe.parameters(self.peer)
        self.factory = object()
        self.binding = dict(run_id=str(uuid.uuid4()), source_commit="a"*40, candidate_sha="b"*64, ci_run="1")

    def connection(self, **overrides):
        values = {key: str(value) for key, value in self.params.items()}
        values.update(target_session_attrs="any", password="PRIVATE_TEST_SENTINEL", service=None)
        values.update(overrides)
        return NS(pgconn=NS(ssl_in_use=True, info=[NS(keyword=k.encode(), val=v.encode() if v is not None else None)
            for k, v in values.items()]), close=Mock())

    def test_saved_source_pins_match_without_running_peer(self):
        self.assertEqual(component.file_hash(PROBE), component.PROBE_SHA)
        self.assertEqual(component.file_hash(NATIVE), component.NATIVE_SHA)
        self.assertEqual(len(self.probe.CASES), 15)
        self.assertEqual(self.probe.CONDITIONAL_CONTRACT["reviewed_libpq"], 160009)

    def test_source_drift_rejected_before_execution(self):
        path = self.root / "changed.py"
        path.write_text("raise AssertionError('must_not_execute')")
        with self.assertRaisesRegex(ValueError, "probe_source"):
            component.load_probe(path)

    def test_pg_environment_is_removed_case_insensitively(self):
        values = {"PGHOSTADDR": "192.0.2.1", "PGSERVICE": "not-used", "pgservicefile": "not-read",
                  "PGPASSWORD": "PRIVATE_TEST_SENTINEL", "PATH": "tools"}
        self.assertEqual(component.scrub_environment(values), {"PATH": "tools"})

    def test_connect_refuses_ambient_service_and_hostaddr(self):
        kw = dict(self.params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
        for key in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGPASSWORD"):
            with self.subTest(key=key), patch.dict(os.environ, {key: "DENIED"}, clear=True):
                with self.assertRaisesRegex(ValueError, "ambient_pg"):
                    component.validate_dispatch(kw, self.params, self.factory, None)

    def test_only_exact_case_controlled_target_environment_allowed(self):
        kw = dict(self.params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
        with patch.dict(os.environ, {"PGTARGETSESSIONATTRS": "primary"}, clear=True):
            component.validate_dispatch(kw, self.params, self.factory, "primary")
            with self.assertRaisesRegex(ValueError, "ambient_pg"):
                component.validate_dispatch(kw, self.params, self.factory, "any")

    def test_dispatch_rejects_changed_endpoint_or_driver_flags(self):
        for key, value in (("host", "192.0.2.1"), ("port", 1), ("autocommit", False),
                           ("prepare_threshold", 5), ("row_factory", object()), ("service", "DENIED")):
            kw = dict(self.params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
            kw[key] = value
            with self.subTest(key=key), patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError):
                    component.validate_dispatch(kw, self.params, self.factory, None)

    def test_effective_info_allowlist_never_exports_password_or_paths(self):
        result = component.effective_parameters(self.connection(), self.params, "any")
        self.assertEqual(set(result), set(component.SAFE_PARAMS))
        self.assertEqual(result["target_session_attrs"], "any")
        self.assertNotIn("PRIVATE_TEST_SENTINEL", json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_effective_mismatch_or_service_never_becomes_zero(self):
        for change in ({"target_session_attrs": "primary"}, {"hostaddr": "192.0.2.1"},
                       {"service": "DENIED"}, {"sslmode": "prefer"}, {"passfile": "other"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                component.effective_parameters(self.connection(**change), self.params, "any")

    def test_tls_and_duplicate_parameter_rejected(self):
        conn = self.connection()
        conn.pgconn.ssl_in_use = False
        with self.assertRaisesRegex(ValueError, "effective_tls"):
            component.effective_parameters(conn, self.params, "any")
        conn = self.connection()
        conn.pgconn.info.append(conn.pgconn.info[0])
        with self.assertRaisesRegex(ValueError, "duplicate_effective"):
            component.effective_parameters(conn, self.params, "any")

    def test_mapped_binary_must_match_loaded_inode(self):
        path = self.root / "libpq-test.so"
        path.write_bytes(b"synthetic binary bytes")
        inode = path.stat().st_ino
        row = "1000-2000 r-xp 00000000 01:02 %d %s" % (inode, path.resolve())
        with patch.object(component.os, "major", return_value=1, create=True), \
                patch.object(component.os, "minor", return_value=2, create=True):
            result = component.mapped_binary(path, row)
            self.assertEqual(result["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError, "mapped_binary_identity"):
                component.mapped_binary(path, row.replace(str(inode), str(inode + 1), 1))
            with self.assertRaisesRegex(ValueError, "binary_not_loaded"):
                component.mapped_binary(path, "")

    def test_observer_records_actual_accessor_values_and_one_dispatch(self):
        driver = NS(connect=Mock(return_value=self.connection()))
        def exercise(native, cert, key, case):
            params = self.probe.parameters(self.peer)
            connection = driver.connect(**params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
            connection.close()
            return {"sql_messages": 0, "database_contacted": False}
        recheck = Mock()
        modules = {"psycopg": driver, "psycopg.rows": NS(dict_row=self.factory)}
        with patch.dict("sys.modules", modules), patch.object(self.probe, "exercise", exercise), \
                patch.dict(os.environ, {}, clear=True):
            result = component.observe_case(self.probe, None, self.cert, None, self.probe.CASES[0], recheck)
        self.assertEqual(result["attempts"][0]["effective"]["hostaddr"], "127.0.0.1")
        driver.connect.assert_called_once()
        recheck.assert_called_once()

    def test_failed_connect_has_no_effective_parameter_claim(self):
        original = RuntimeError("PRIVATE_TEST_SENTINEL")
        driver = NS(connect=Mock(side_effect=original))
        def exercise(*args):
            params = self.probe.parameters(self.peer)
            driver.connect(**params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
        with patch.dict("sys.modules", {"psycopg": driver, "psycopg.rows": NS(dict_row=self.factory)}), \
                patch.object(self.probe, "exercise", exercise), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as caught:
                component.observe_case(self.probe, None, self.cert, None, self.probe.CASES[0], lambda: None)
        self.assertIs(caught.exception, original)
        record = original.component_partial
        self.assertIsNone(record["attempts"][0]["effective"])
        self.assertNotIn("PRIVATE_TEST_SENTINEL", json.dumps(record))

    def test_nonlinux_preserves_incomplete_receipt_without_peer(self):
        output = self.root / "evidence"
        with patch.object(component.sys, "platform", "not-linux"), self.assertRaisesRegex(ValueError, "linux_required"):
            component.run(PROBE, NATIVE, output, self.root / "private", self.binding)
        result = json.loads((output / "component-result.json").read_bytes())
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIsNone(result["driver_implicit_sql_bound"])
        self.assertFalse(result["full_admission"])
        self.assertFalse((self.root / "private").exists())

    def test_separate_private_directory_and_fresh_identity_required(self):
        for ident in component.RESERVED:
            with self.subTest(ident=ident), self.assertRaisesRegex(ValueError, "case_uuid"):
                component.run(PROBE, NATIVE, self.root / "out", self.root / "work", dict(self.binding, run_id=ident))
        with self.assertRaisesRegex(ValueError, "private_work_separation"):
            component.run(PROBE, NATIVE, self.root / "out", self.root / "out/private", self.binding)
        self.assertFalse((self.root / "out").exists())

    def test_receipt_exclusive_size_and_readback(self):
        component.save(self.probe, self.root, "receipt.json", {"component": True})
        with self.assertRaises(FileExistsError):
            component.save(self.probe, self.root, "receipt.json", {"component": False})
        with self.assertRaisesRegex(ValueError, "receipt_size"):
            component.save(self.probe, self.root, "large.json", {"large": "x" * 1_400_000})

    def test_case_and_final_save_failures_preserve_original(self):
        original = RuntimeError("PRIVATE_TEST_SENTINEL")
        original.component_partial = {"attempts": [], "wire": None}
        real_save = component.save
        def save(probe, output, name, value):
            if name in ("case-00.json", "component-result.json"):
                raise OSError("PRIVATE_TEST_SENTINEL")
            return real_save(probe, output, name, value)
        with patch.object(component, "load_probe", return_value=self.probe), \
                patch.object(component.sys, "platform", "linux"), \
                patch.object(component, "network_guard", return_value={"test_only": True}), \
                patch.object(component, "case_deadline", side_effect=nullcontext), \
                patch.object(self.probe, "load_native", return_value=object()), \
                patch.object(self.probe, "certificates", return_value=(self.cert, self.cert)), \
                patch.object(component, "client_identity", return_value={"test_only": True}), \
                patch.object(component, "observe_case", side_effect=original), patch.object(component, "save", side_effect=save):
            with self.assertRaises(RuntimeError) as caught:
                component.run(PROBE, NATIVE, self.root / "out", self.root / "private", self.binding)
        self.assertIs(caught.exception, original)
        self.assertIn("component_case_receipt_secondary:OSError", original.__notes__)
        self.assertIn("component_receipt_secondary:OSError", original.__notes__)

    def test_other_linux_libpq_version_cannot_inherit_windows_zero_bound(self):
        def certificates(work):
            cert, key = work / "synthetic-cert.pem", work / "synthetic-key.pem"
            cert.write_text("SYNTHETIC_PUBLIC_TEST_CERT")
            key.write_text("SYNTHETIC_TEST_KEY_NOT_A_CREDENTIAL")
            return cert, key
        def observe(*args):
            self.assertFalse(any(k.upper().startswith("PG") for k in os.environ))
            return {"attempts": [], "wire": {"test_only": True}}
        identity = {"libpq_runtime": 170006, "matches_C_reviewed_libpq_version": False, "test_only": True}
        output = self.root / "out"
        with patch.object(component, "load_probe", return_value=self.probe), \
                patch.object(component.sys, "platform", "linux"), \
                patch.object(component, "network_guard", return_value={"test_only": True}), \
                patch.object(component, "case_deadline", side_effect=nullcontext), \
                patch.object(self.probe, "load_native", return_value=object()), \
                patch.object(self.probe, "certificates", side_effect=certificates), \
                patch.object(component, "client_identity", return_value=identity), \
                patch.object(component, "observe_case", side_effect=observe) as observe_mock, \
                patch.dict(os.environ, {"PGHOSTADDR": "192.0.2.1", "PGSERVICE": "DENIED"}):
            result = component.run(PROBE, NATIVE, output, self.root / "private", self.binding)
        self.assertEqual(observe_mock.call_count, 15)
        self.assertEqual(result["status"], "SYNTHETIC_COMPONENT_OBSERVED")
        self.assertIsNone(result["driver_implicit_sql_bound"])
        self.assertFalse(result["full_admission"])
        self.assertEqual(json.loads((output / "client-before.json").read_bytes())["libpq_runtime"], 170006)
        self.assertEqual(len(list(output.iterdir())), 19)
        self.assertFalse(list(output.glob("*.pem")))
        self.assertEqual(result["authentication"], "synthetic_AuthenticationOk_not_SCRAM_or_GoTrue")

    def test_second_dispatch_rejected_before_driver(self):
        driver = NS(connect=Mock(return_value=self.connection()))
        def exercise(*_):
            params = self.probe.parameters(self.peer)
            for _ in range(2):
                driver.connect(**params, autocommit=True, prepare_threshold=None, row_factory=self.factory)
        with patch.dict("sys.modules", {"psycopg": driver, "psycopg.rows": NS(dict_row=self.factory)}), \
                patch.object(self.probe, "exercise", exercise), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "connect_dispatch_limit"):
                component.observe_case(self.probe, None, self.cert, None, self.probe.CASES[0], lambda: None)
        driver.connect.assert_called_once()

    def test_nonloopback_interface_is_rejected(self):
        with patch.object(component.sys, "platform", "linux"), \
                patch.object(component.os, "geteuid", return_value=1000, create=True), \
                patch.object(component.socket, "if_nameindex", return_value=[(1, "lo"), (2, "eth0")]):
            with self.assertRaisesRegex(ValueError, "loopback_namespace"):
                component.network_guard()

    def test_case_alarm_is_armed_once_and_cleared_on_failure(self):
        with patch.object(component.signal, "SIGALRM", 14, create=True), \
                patch.object(component.signal, "ITIMER_REAL", 0, create=True), \
                patch.object(component.signal, "signal", return_value="old") as handler, \
                patch.object(component.signal, "setitimer", create=True) as timer:
            with self.assertRaises(component.CaseDeadline):
                with component.case_deadline():
                    handler.call_args.args[1]()
        self.assertEqual([call.args for call in timer.call_args_list], [(0, 15), (0, 0)])
        self.assertEqual(handler.call_args.args, (14, "old"))


if __name__ == "__main__":
    unittest.main()
