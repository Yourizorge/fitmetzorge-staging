"""Pure source/supervision/export tests; no dependency install or CI dispatch."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock

import native_connect_ci as ci


class CITests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def source_tree(self):
        files = {}
        for name in [ci.PREFIX + n for n in ci.SOURCES] + [ci.NATIVE, ci.WORKFLOW]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic fixture")
            files[name] = ci.sha(path.read_bytes())
        path = self.root / ci.PREFIX / "source-manifest.json"
        path.write_text(json.dumps({"format": "native-component-sources-v2", "files": files}))
        return path, ci.sha(path.read_bytes())

    def test_source_set_hash_and_no_extra_member(self):
        path, digest = self.source_tree()
        self.assertEqual(len(ci.verify_sources(self.root, digest)["sources"]), 9)
        value = json.loads(path.read_bytes())
        value["files"]["../other"] = "0" * 64
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "source_set"):
            ci.verify_sources(self.root, ci.sha(path.read_bytes()))

    def test_changed_manifest_or_source_denied(self):
        _, digest = self.source_tree()
        with self.assertRaisesRegex(ValueError, "manifest_hash"):
            ci.verify_sources(self.root, "0" * 64)
        (self.root / ci.NATIVE).write_text("changed")
        with self.assertRaisesRegex(ValueError, "source_hash"):
            ci.verify_sources(self.root, digest)

    def test_skip_expected_failure_or_missing_test_is_not_success(self):
        result = NS(wasSuccessful=lambda: True, testsRun=2, skipped=[], expectedFailures=[])
        self.assertTrue(ci.unit_success(result, 2))
        self.assertFalse(ci.unit_success(result, 3))
        result.skipped = [("synthetic", "skip")]
        self.assertFalse(ci.unit_success(result, 2))
        result.skipped = []
        result.expectedFailures = [("synthetic", "expected")]
        self.assertFalse(ci.unit_success(result, 2))

    def test_child_environment_does_not_inherit_tokens_routes_or_python_hooks(self):
        with patch.dict(os.environ, {"PGHOSTADDR": "192.0.2.1", "PGSERVICE": "DENIED", "GITHUB_TOKEN": "PRIVATE_SENTINEL",
                "LD_PRELOAD": "DENIED", "SSLKEYLOGFILE": "DENIED", "PYTHONPATH": "DENIED"}):
            env = ci.child_environment(self.root)
        self.assertEqual(set(env), {"PATH", "HOME", "TMPDIR", "LANG"})
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(env))

    def process(self, codes):
        process = Mock(pid=321)
        def wait(**_):
            value = codes.pop(0)
            if isinstance(value, BaseException):
                raise value
            process.returncode = value
            return value
        process.wait.side_effect = wait
        return process

    def test_waited_zero_exit_is_required(self):
        for code in (0, 1):
            process = self.process([code])
            with patch.object(ci.subprocess, "Popen", return_value=process) as popen:
                value = ci.wait_child(["synthetic"], {}, 240)
            self.assertEqual(value["accepted"], code == 0)
            self.assertTrue(value["wait_completed"])
            self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.DEVNULL)
            self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_timeout_kills_group_once_and_later_zero_cannot_pass(self):
        process = self.process([subprocess.TimeoutExpired("synthetic", 240), 0])
        with patch.object(ci.subprocess, "Popen", return_value=process), \
                patch.object(ci.os, "killpg", create=True) as kill, patch.object(ci.signal, "SIGKILL", 9, create=True):
            value = ci.wait_child(["synthetic"], {}, 240)
        kill.assert_called_once_with(321, 9)
        self.assertFalse(value["accepted"])
        self.assertTrue(value["timed_out"])
        self.assertTrue(value["wait_completed"])
        self.assertEqual([c.kwargs["timeout"] for c in process.wait.call_args_list], [240, 5])

    def test_reap_failure_is_incomplete_no_retry(self):
        process = self.process([subprocess.TimeoutExpired("synthetic", 240), OSError("synthetic")])
        with patch.object(ci.subprocess, "Popen", return_value=process), \
                patch.object(ci.os, "killpg", create=True) as kill, patch.object(ci.signal, "SIGKILL", 9, create=True):
            value = ci.wait_child(["synthetic"], {}, 240)
        kill.assert_called_once()
        self.assertFalse(value["accepted"])
        self.assertFalse(value["wait_completed"])
        self.assertEqual(value["error_class"], "OSError")

    def test_boolean_returncode_not_numeric_success(self):
        process = self.process([False, 0])
        with patch.object(ci.subprocess, "Popen", return_value=process), \
                patch.object(ci.os, "killpg", create=True), patch.object(ci.signal, "SIGKILL", 9, create=True):
            value = ci.wait_child(["synthetic"], {}, 240)
        self.assertFalse(value["accepted"])
        self.assertEqual(value["error_class"], "ValueError")

    def test_only_allowlisted_bounded_json_is_exported(self):
        output = self.root / "out"
        output.mkdir()
        ci.save(output / "supervisor.json", {"status": "INCOMPLETE", "full_admission": False})
        artifact = self.root / "artifact"
        ci.seal(output, artifact)
        receipt = json.loads((artifact / "artifact-manifest.json").read_bytes())
        self.assertFalse(receipt["full_admission"])
        self.assertEqual(receipt["files"][0]["sha256"], ci.sha((artifact / "supervisor.json").read_bytes()))

    def test_pem_and_private_json_never_export(self):
        output = self.root / "out"
        output.mkdir()
        path = output / "synthetic-key.pem"
        path.write_text("PRIVATE_SENTINEL")
        with self.assertRaisesRegex(ValueError, "artifact_member"):
            ci.seal(output, self.root / "artifact")
        path.unlink()
        ci.save(output / "supervisor.json", {"password": "PRIVATE_SENTINEL"})
        with self.assertRaisesRegex(ValueError, "private_fields"):
            ci.seal(output, self.root / "artifact")
        self.assertFalse((self.root / "artifact").exists())

    def test_component_claims_cannot_be_promoted_by_export(self):
        for value in ({"full_admission": True}, {"actual_postgres_test": True},
                      {"wal_observed": True}, {"driver_implicit_sql_bound": 0}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ci.check_json(value)

    def test_workflow_has_hash_lock_and_network_drop_not_services(self):
        base = Path(__file__).parent
        path = base / "phase6e-native-connect-component.yml"
        if not path.is_file():
            path = base.parents[3] / ci.WORKFLOW
        text = path.read_text()
        for required in ("--net", "--no-new-privs", "--bounding-set=-all", "env -i", "--require-hashes",
                         "--only-binary=:all:", "--retries 0", "persist-credentials: false"):
            self.assertIn(required, text)
        self.assertNotIn("services:", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("*.pem", text)
        lock = (base / "requirements-linux-cp312.lock").read_text()
        rows = [row for row in lock.splitlines() if row and not row.startswith("#")]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all("https://files.pythonhosted.org/" in row and ".whl --hash=sha256:" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
