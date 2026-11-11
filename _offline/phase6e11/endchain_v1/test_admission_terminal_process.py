"""Actual child IPC/import tests. No DB, network, artifact code or CI."""
import hashlib
import gc
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import uuid

import admission_matrix_ops as ops
import admission_terminal_process as process

HERE = Path(__file__).resolve().parent
HEAD, CANDIDATE, RUN = "a"*40, "b"*64, "123"
READER = """import hashlib
import admission_case_archive as installed
def verify_exported_terminal(payloads, case, *, originals, source_commit, ci_run,
                             candidate_sha256, expected_sources, trusted_root):
    installed.validate(originals)
    assert source_commit == '""" + HEAD + """' and ci_run == '""" + RUN + """'
    assert candidate_sha256 == '""" + CANDIDATE + """'
    assert str(trusted_root) == str(__import__('pathlib').Path(__file__).resolve().parents[4])
    return {'status':'CASE_TERMINAL_UNVERIFIED', 'case_name':case['case_name'],
        'run_id':case['run_id'], 'case_sha256':hashlib.sha256(payloads['case-execution.json']).hexdigest(),
        'missing':['numeric_originals_pending'], 'invalid':[], 'checks':{},
        'full_chain_admission':False, 'hosted_admitted':False}
"""


class TerminalInspectionTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(Path(ops.__file__).resolve(), HERE / "admission_matrix_ops.py")
        self.directory = tempfile.TemporaryDirectory(prefix="ti-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.sources = {}
        for name in ("admission_trusted_loader.py", "admission_terminal_process.py"):
            self.put(process.PREFIX + name, (HERE / name).read_bytes())
        self.put(ops.TERMINAL_PACKAGE, b"# pinned installed parent\n")
        self.put(ops.TERMINAL_SOURCE, READER.encode())
        self.put(process.PREFIX + "admission_case_archive.py",
                 b"def validate(originals):\n    assert originals == {'original.json': b'{}'}\n")
        self.case = {"case_name": "normal", "run_id": str(uuid.uuid4())}
        self.payloads = {"case-execution.json": json.dumps(self.case).encode()}
        self.originals = {"original.json": b"{}"}

    def put(self, name, raw, pin=True):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        if pin:
            self.sources[name] = hashlib.sha256(raw).hexdigest()
        return path

    def inspect(self):
        return ops.inspect_terminal(self.payloads, self.case, self.originals,
            head=HEAD, candidate=CANDIDATE, run=RUN, expected_sources=self.sources, trusted_root=self.root)

    def no_go(self, value, reason=None):
        self.assertEqual(value["status"], "CASE_TERMINAL_UNVERIFIED")
        self.assertFalse(value["full_chain_admission"])
        self.assertFalse(value["hosted_admitted"])
        self.assertEqual(value["reader_process"]["status"], "NO_GO")
        if reason:
            self.assertIn(reason, value["missing"])
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(value))

    def test_checked_originals_binding_actual_wait_and_parent_cache_preserved(self):
        parent_archive = sys.modules["admission_case_archive"]
        parent_import = __import__
        value = self.inspect()
        self.assertEqual(value["missing"], ["numeric_originals_pending"])
        state = value["reader_process"]
        self.assertEqual(state["status"], "INSPECTED_UNVERIFIED")
        self.assertTrue(state["wait"]["wait_completed"])
        self.assertEqual(type(state["wait"]["returncode"]), int)
        self.assertEqual(state["wait"]["returncode"], 0)
        self.assertFalse(state["wait"]["kill_requested"])
        self.assertEqual(state["private_cleanup"], "completed")
        self.assertIs(sys.modules["admission_case_archive"], parent_archive)
        self.assertIs(__import__, parent_import)

    def test_changed_parent_reader_loader_or_helper_denied_before_child(self):
        for name in (ops.TERMINAL_PACKAGE, ops.TERMINAL_SOURCE, process.LOADER, process.SELF):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(b"raise RuntimeError('PRIVATE_SENTINEL')\n")
                with self.assertRaises(ValueError):
                    self.inspect()
                path.write_bytes(original)

    def test_missing_installed_source_does_not_import_artifact_fallback(self):
        (self.root / ops.TERMINAL_SOURCE).unlink()
        self.payloads["runtime_exported_terminal.py"] = READER.encode()
        with self.assertRaises((ValueError, OSError)):
            self.inspect()

    def test_stale_parent_and_reader_bytecode_never_executes(self):
        for name in (ops.TERMINAL_PACKAGE, ops.TERMINAL_SOURCE):
            path = self.root / name
            approved = path.read_bytes()
            stale = b"raise RuntimeError('PRIVATE_SENTINEL')\n"
            approved = approved + b"\n" * max(0, len(stale) - len(approved))
            stale = stale + b"\n" * (len(approved) - len(stale))
            path.write_bytes(stale)
            stat = path.stat()
            py_compile.compile(str(path), doraise=True,
                invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            path.write_bytes(approved)
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.sources[name] = hashlib.sha256(approved).hexdigest()
        self.assertEqual(self.inspect()["reader_process"]["status"], "INSPECTED_UNVERIFIED")

    def test_unlisted_transitive_helper_returns_sanitized_no_go(self):
        self.put(process.PREFIX + "unlisted_fixture.py", b"raise RuntimeError('PRIVATE_SENTINEL')\n", pin=False)
        self.put(ops.TERMINAL_SOURCE, ("import unlisted_fixture\n" + READER).encode())
        self.no_go(self.inspect(), "unsupported_or_unbound_replay")

    def test_exact_bound_legacy_file_alias_is_executable(self):
        self.put(process.PREFIX + "legacy.py", b"VALUE='approved'\n")
        self.put(ops.TERMINAL_SOURCE, ("""import importlib.util,pathlib
spec=importlib.util.spec_from_file_location('exact_legacy_fixture',pathlib.Path(__file__).parents[1]/'legacy.py')
bound=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bound)
assert bound.VALUE=='approved'
""" + READER).encode())
        self.assertEqual(self.inspect()["reader_process"]["status"], "INSPECTED_UNVERIFIED")

    def test_legacy_alias_reuse_is_not_silently_replaced(self):
        self.put(process.PREFIX + "legacy.py", b"VALUE=1\n")
        self.put(ops.TERMINAL_SOURCE, ("""import importlib.util,pathlib
path=pathlib.Path(__file__).parents[1]/'legacy.py'
spec=importlib.util.spec_from_file_location('exact_legacy_fixture',path)
bound=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bound)
importlib.util.spec_from_file_location('exact_legacy_fixture',path)
""" + READER).encode())
        self.no_go(self.inspect(), "legacy_cached_alias")

    def test_changed_legacy_source_is_no_go(self):
        path = self.put(process.PREFIX + "legacy.py", b"VALUE=1\n")
        path.write_bytes(b"raise RuntimeError('PRIVATE_SENTINEL')\n")
        self.put(ops.TERMINAL_SOURCE, ("""import importlib.util,pathlib
spec=importlib.util.spec_from_file_location('exact_legacy_fixture',pathlib.Path(__file__).parents[1]/'legacy.py')
""" + READER).encode())
        self.no_go(self.inspect(), "unsupported_or_unbound_replay")

    def test_caught_legacy_validation_errors_latch_failure(self):
        self.put(process.PREFIX + "legacy.py", b"VALUE=1\n")
        for action in (
                "importlib.util.spec_from_file_location('bad.alias', path)",
                "importlib.util.spec_from_file_location('missing_alias', path.with_name('missing.py'))",
                "importlib.util.spec_from_file_location('null_alias', None)",
                "importlib.util.spec_from_file_location('sys', path)"):
            with self.subTest(action=action):
                body = "import importlib.util,pathlib\npath=pathlib.Path(__file__).parents[1]/'legacy.py'\n"
                body += "try:\n    " + action + "\nexcept Exception:\n    pass\n"
                self.put(ops.TERMINAL_SOURCE, (body + READER).encode())
                self.no_go(self.inspect(), "unsupported_or_unbound_replay")

    def test_caught_legacy_exec_cached_alias_latches_failure(self):
        self.put(process.PREFIX + "legacy.py", b"VALUE=1\n")
        self.put(ops.TERMINAL_SOURCE, ("""import importlib.util,pathlib,sys
spec=importlib.util.spec_from_file_location('exact_legacy_fixture',pathlib.Path(__file__).parents[1]/'legacy.py')
bound=importlib.util.module_from_spec(spec)
sys.modules['exact_legacy_fixture']=bound
try:
    spec.loader.exec_module(bound)
except Exception:
    pass
del sys.modules['exact_legacy_fixture']
""" + READER).encode())
        self.no_go(self.inspect(), "unsupported_or_unbound_replay")

    def test_caught_audit_errors_cannot_return_inspected(self):
        for action in (
                "subprocess.Popen([sys.executable, '-c', 'pass'])",
                "pathlib.Path(__file__).with_name('MUST_NOT_EXIST').write_text('x')",
                "exec(compile('VALUE=99', __file__, 'exec'))"):
            with self.subTest(action=action):
                # Catch inside the reader, after its ordinary imports succeeded.
                body = READER.replace("    installed.validate(originals)",
                    "    import subprocess,sys,pathlib\n    try:\n        " + action
                    + "\n    except Exception:\n        pass\n    installed.validate(originals)")
                self.put(ops.TERMINAL_SOURCE, body.encode())
                self.no_go(self.inspect(), "unsupported_or_unbound_replay")
                self.assertFalse((self.root / ops.TERMINAL_SOURCE).with_name("MUST_NOT_EXIST").exists())

    def test_verified_ast_subset_is_explicitly_unsupported_not_full_reader_pass(self):
        self.put(process.PREFIX + "fragment.py", b"def one():\n    return 1\ndef two():\n    return 2\n")
        body = READER.replace("    installed.validate(originals)", """    import ast,pathlib
    path=pathlib.Path(__file__).parents[1]/'fragment.py'
    tree=ast.parse(path.read_bytes(),filename=str(path))
    tree.body=tree.body[:1]
    try:
        exec(compile(tree,str(path),'exec'),{})
    except Exception:
        pass
    installed.validate(originals)""")
        self.put(ops.TERMINAL_SOURCE, body.encode())
        self.no_go(self.inspect(), "unsupported_or_unbound_replay")

    def test_unconfirmed_reap_retains_inputs_and_detaches_finalizer(self):
        path = self.root / process.SELF
        namespace = {"__name__": "_fixture_installed_parent", "__file__": str(path)}
        exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), namespace)
        created = []
        real_directory = tempfile.TemporaryDirectory
        def directory(**kwargs):
            value = real_directory(dir=self.root, **kwargs)
            created.append(value)
            return value
        for failure in (False, True):
            with self.subTest(wait_raises=failure):
                def wait(*args):
                    if failure:
                        raise OSError("PRIVATE_SENTINEL")
                    return {"accepted": False, "wait_completed": False, "kill_requested": True}
                namespace["wait_child"] = wait
                with patch.object(tempfile, "TemporaryDirectory", side_effect=directory):
                    value = namespace["inspect_terminal"](self.payloads, self.case, self.originals,
                        head=HEAD, candidate=CANDIDATE, run=RUN,
                        expected_sources=self.sources, trusted_root=self.root)
                self.no_go(value, "terminal_child_reap_unconfirmed")
                owned = created.pop()
                retained = Path(owned.name)
                self.assertFalse(owned._finalizer.alive)
                self.assertEqual(value["reader_process"]["private_cleanup"], "deferred_unconfirmed_reap")
                self.assertEqual(value["reader_process"]["retained_directory_id"], retained.name)
                self.assertNotIn(str(retained), json.dumps(value))
                del owned
                gc.collect()
                self.assertTrue((retained / "rq.json").is_file())
                # This test never started a process. Only its own fixture is removed.
                shutil.rmtree(retained)

    def test_originals_are_not_discarded_and_exception_message_is_not_exported(self):
        self.originals = {"original.json": b'{"not":"expected"}'}
        self.no_go(self.inspect(), "reader_exception")
        self.put(ops.TERMINAL_SOURCE, b"print('PRIVATE_SENTINEL')\nraise ValueError('PRIVATE_SENTINEL')\n")
        self.no_go(self.inspect(), "reader_exception")

    def test_reader_pass_claim_is_no_go(self):
        self.put(ops.TERMINAL_SOURCE, READER.replace("CASE_TERMINAL_UNVERIFIED", "CASE_TERMINAL_VERIFIED").encode())
        self.no_go(self.inspect(), "reader_claim")

    def test_binding_and_false_flags_are_checked_in_child(self):
        for old, new in (("'run_id':case['run_id']", "'run_id':'wrong'"),
                         ("'full_chain_admission':False", "'full_chain_admission':True"),
                         ("'hosted_admitted':False", "'hosted_admitted':True")):
            with self.subTest(new=new):
                self.put(ops.TERMINAL_SOURCE, READER.replace(old, new).encode())
                self.no_go(self.inspect(), "reader_claim")

    def test_oversized_reader_result_becomes_small_no_go(self):
        body = READER.replace("'checks':{}", "'checks':{'oversize':'x'*2000001}")
        self.put(ops.TERMINAL_SOURCE, body.encode())
        value = self.inspect()
        self.no_go(value, "report_limit")
        self.assertLess(len(json.dumps(value)), 8192)

    def test_zero_exit_without_original_response_is_no_go(self):
        self.put(ops.TERMINAL_SOURCE, b"import os\nos._exit(0)\n")
        value = self.inspect()
        self.no_go(value, "terminal_child_incomplete")
        self.assertEqual(value["reader_process"]["wait"]["returncode"], 0)

    def test_inherited_pg_python_credentials_not_available_in_child(self):
        self.put(ops.TERMINAL_SOURCE, ("""import os,sys
assert not any(k.upper().startswith('PG') for k in os.environ)
assert 'PYTHONPATH' not in os.environ and 'GITHUB_TOKEN' not in os.environ
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
""" + READER).encode())
        with patch.dict(os.environ, {"PGHOSTADDR": "192.0.2.1", "PGSERVICE": "PRIVATE_SENTINEL",
                                     "PYTHONPATH": "PRIVATE_SENTINEL", "GITHUB_TOKEN": "PRIVATE_SENTINEL"}):
            self.assertEqual(self.inspect()["reader_process"]["status"], "INSPECTED_UNVERIFIED")

    def test_offline_audit_blocks_process_creation_before_dispatch(self):
        self.put(ops.TERMINAL_SOURCE, b"import subprocess,sys\nsubprocess.Popen([sys.executable,'-c','pass'])\n")
        self.no_go(self.inspect(), "offline_action_denied")

    def test_replay_cannot_write_installed_project(self):
        self.put(ops.TERMINAL_SOURCE, b"import pathlib\npathlib.Path(__file__).with_name('MUST_NOT_EXIST').write_text('x')\n")
        self.no_go(self.inspect(), "private_write_only")
        self.assertFalse((self.root / ops.TERMINAL_SOURCE).with_name("MUST_NOT_EXIST").exists())

    def test_input_member_limit_is_checked_without_child(self):
        self.originals = {"original.json": b"x"*(process.MAX_MEMBER+1)}
        with self.assertRaisesRegex(ValueError, "member_size"):
            self.inspect()

    def test_duplicate_or_traversal_member_name_denied(self):
        for value in ({"a": b"", "A": b""}, {"../outside": b""}, {"CON.json": b""}):
            self.originals = value
            with self.assertRaises(ValueError):
                self.inspect()


class ChildWaitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tw-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def wait(self, code, timeout=3):
        return process.wait_child([sys.executable, "-I", "-S", "-B", "-c", code],
            process.child_environment(self.root), str(self.root), timeout=timeout)

    def test_actual_zero_and_nonzero_waited_exits(self):
        zero = self.wait("raise SystemExit(0)")
        nonzero = self.wait("raise SystemExit(7)")
        self.assertTrue(zero["accepted"])
        self.assertTrue(zero["wait_completed"])
        self.assertFalse(nonzero["accepted"])
        self.assertEqual(nonzero["returncode"], 7)

    def test_actual_timeout_is_killed_and_reaped_never_success(self):
        value = self.wait("import time; time.sleep(30)", timeout=0.2)
        self.assertTrue(value["timed_out"])
        self.assertTrue(value["kill_requested"])
        self.assertTrue(value["wait_completed"])
        self.assertFalse(value["accepted"])

    def test_reap_failure_stays_unknown_and_no_second_kill(self):
        child = Mock(pid=123)
        child.wait.side_effect = [subprocess.TimeoutExpired("fixture", 1), OSError("PRIVATE_SENTINEL")]
        with patch.object(process.subprocess, "Popen", return_value=child), \
                patch.object(process.os, "killpg", create=True) as kill:
            value = process.wait_child(["fixture"], {}, str(self.root), timeout=1)
        self.assertFalse(value["accepted"])
        self.assertFalse(value["wait_completed"])
        self.assertEqual(child.wait.call_count, 2)
        self.assertEqual(child.kill.call_count if os.name == "nt" else kill.call_count, 1)
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(value))

    def test_boolean_exit_is_not_numeric_zero(self):
        child = Mock(pid=123, returncode=False)
        child.wait.side_effect = [False, 1]
        with patch.object(process.subprocess, "Popen", return_value=child), \
                patch.object(process.os, "killpg", create=True):
            value = process.wait_child(["fixture"], {}, str(self.root), timeout=1)
        self.assertFalse(value["accepted"])


if __name__ == "__main__":
    unittest.main()
