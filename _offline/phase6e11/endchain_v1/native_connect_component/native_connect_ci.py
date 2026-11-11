"""Bounded local component supervision, source check and JSON-only export."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import unittest
import uuid

PREFIX = "_offline/phase6e11/endchain_v1/native_connect_component/"
NATIVE = "_offline/phase6e11/endchain_v1/native_runtime.py"
WORKFLOW = ".github/workflows/phase6e-native-connect-component.yml"
SOURCES = ("native_connect_component.py", "native_connect_ci.py", "native_connect_probe.py",
           "test_native_connect_component.py", "test_native_connect_ci.py", "test_native_connect_probe.py",
           "requirements-linux-cp312.lock")
NEGATIVE_TESTS = ("test_actual_binary_version", "test_source_hash_mismatch_rejected_before_execution",
    "test_missing_origin_rejected", "test_clear_rejects_before_driver_dispatch",
    "test_postconstruction_environment_guards", "test_service_parameters_rejected_before_driver",
    "test_prefer_standby_doubles_driver_attempts_without_network", "test_record_exclusive_and_no_overwrite",
    "test_actual_source_raw_hash_bound")


def require(value, code):
    if not value:
        raise ValueError("native_ci_" + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    require(len(raw) < 1_400_000, "member_size")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    require(Path(path).read_bytes() == raw, "readback")


def verify_sources(root, expected):
    require(re.fullmatch("[a-f0-9]{64}", expected), "manifest_sha")
    root = Path(root).resolve(strict=True)
    manifest_path = root / PREFIX / "source-manifest.json"
    require(not manifest_path.is_symlink(), "manifest_symlink")
    raw = manifest_path.read_bytes()
    require(sha(raw) == expected, "manifest_hash")
    manifest = json.loads(raw)
    require(set(manifest) == {"format", "files"} and manifest["format"] == "native-component-sources-v2", "manifest_fields")
    files = manifest["files"]
    require(set(files) == {PREFIX + name for name in SOURCES} | {NATIVE, WORKFLOW}, "source_set")
    for name, digest in files.items():
        path = root / name
        require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root), "source_origin")
        require(all(not p.is_symlink() for p in path.parents if p != root and p.is_relative_to(root)), "parent_origin")
        require(sha(path.read_bytes()) == digest, "source_hash")
    return {"source_manifest_sha256": expected, "sources": files, "full_admission": False}


def child_environment(private):
    private = str(Path(private).resolve(strict=True))
    return {"PATH": "/usr/bin:/bin", "HOME": private, "TMPDIR": private, "LANG": "C.UTF-8"}


def wait_child(command, environment, seconds):
    record = {"timeout_seconds": seconds, "timed_out": False, "wait_completed": False,
              "returncode": None, "error_class": None, "kill_requested": False, "accepted": False}
    process = None
    try:
        process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            code = process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            record["kill_requested"] = True
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=5)
        require(type(code) is int and process.returncode == code, "wait_result")
        record["returncode"], record["wait_completed"] = code, True
        record["accepted"] = code == 0 and not record["timed_out"]
    except BaseException as error:
        record["error_class"] = type(error).__name__
        if process is not None and not record["wait_completed"] and not record["kill_requested"]:
            try:
                record["kill_requested"] = True
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=5)
                if type(code) is int and process.returncode == code:
                    record["returncode"], record["wait_completed"] = code, True
            except BaseException as secondary:
                record["close_error_class"] = type(secondary).__name__
    return record


def unit_success(result, expected):
    return (result.wasSuccessful() and result.testsRun == expected and expected > 0
            and not result.skipped and not result.expectedFailures)


def unit_checks(root, output):
    component = Path(root) / PREFIX
    sys.path.insert(0, str(component))
    os.environ.update(C_NATIVE_PROBE_SOURCE=str(component / "native_connect_probe.py"),
        C_NATIVE_RUNTIME_SOURCE=str(Path(root) / NATIVE), NATIVE_CONNECT_SOURCE=str(Path(root) / NATIVE),
        NATIVE_CONNECT_SHA="9d086efe38a5b42b83684754cdc644ed461fbb9ee0311d5ca53fff5445b5ac3a")
    suite = unittest.TestSuite()
    for name in ("test_native_connect_component", "test_native_connect_ci"):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    from test_native_connect_probe import WireTests
    suite.addTests(WireTests(name) for name in NEGATIVE_TESTS)
    expected = suite.countTestCases()
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    value = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
             "skipped": len(result.skipped), "expected_tests": expected,
             "successful": unit_success(result, expected),
             "scope": "adapter_unit_and_original_C_negative_tests_not_full_wire_or_admission",
             "full_admission": False}
    save(Path(output) / "unit-result.json", value)
    return value["successful"]


def supervise(root, output, private, expected, commit, ci_run, host_network):
    require(sys.platform == "linux" and sys.version_info[:2] == (3, 12), "linux_cp312_required")
    require(re.fullmatch("[a-f0-9]{40}", commit) and re.fullmatch("[0-9]{1,24}", ci_run), "ci_identity")
    root, output, private = Path(root).resolve(), Path(output).resolve(), Path(private).resolve(strict=True)
    component = root / PREFIX
    sys.path.insert(0, str(component))
    from native_connect_component import network_guard
    record = {"status": "INCOMPLETE", "phase": "source", "source_commit": commit, "ci_run": ci_run,
              "source_manifest_sha256": expected, "full_admission": False, "hosted_admitted": False,
              "actual_postgres_test": False, "wal_observed": False}
    try:
        verify_sources(root, expected)
        isolation = network_guard()
        require(re.fullmatch(r"net:\[[0-9]+\]", host_network)
                and isolation["network_namespace"] != host_network, "fresh_network_namespace")
        record["isolation"] = isolation
        environment = child_environment(private)
        record["phase"] = "negative_tests"
        tests = wait_child([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "units",
            "--root", str(root), "--output", str(output)], environment, 60)
        save(output / "unit-wait.json", tests)
        require(tests["accepted"], "unit_child_incomplete")
        record["phase"] = "synthetic_wire"
        binding = {"run_id": str(uuid.uuid4()), "source_commit": commit, "candidate_sha": expected, "ci_run": ci_run}
        command = [sys.executable, "-I", "-B", str(component / "native_connect_component.py"),
            "--probe-source", str(component / "native_connect_probe.py"), "--native-source", str(root / NATIVE),
            "--output", str(output / "component"), "--work", str(private / "tls")]
        for name, value in binding.items():
            command.extend(["--" + name.replace("_", "-"), value])
        terminal = wait_child(command, environment, 240)
        save(output / "component-wait.json", terminal)
        require(terminal["accepted"], "component_child_incomplete")
        result = json.loads((output / "component/component-result.json").read_bytes())
        require(result["status"] == "SYNTHETIC_COMPONENT_OBSERVED" and result["binding"] == binding
                and result["full_admission"] is False and result["driver_implicit_sql_bound"] is None,
                "component_result")
        verify_sources(root, expected)
        record["status"], record["phase"] = "SYNTHETIC_COMPONENT_OBSERVED", "terminal"
        return True
    except BaseException as error:
        record["error_class"] = type(error).__name__
        return False
    finally:
        save(output / "supervisor.json", record)


def check_json(value):
    if isinstance(value, dict):
        require(not ({"password", "raw_env", "environment_variables", "private_key", "dsn"} & set(value)), "private_fields")
        for key in ("full_admission", "hosted_admitted", "actual_postgres_test", "wal_observed"):
            if key in value:
                require(value[key] is False, "unreviewed_admission")
        if "driver_implicit_sql_bound" in value:
            require(value["driver_implicit_sql_bound"] is None, "unreviewed_numeric_bound")
        for item in value.values():
            check_json(item)
    elif isinstance(value, list):
        for item in value:
            check_json(item)
    elif isinstance(value, str):
        require("-----BEGIN" not in value and "synthetic-key.pem" not in value, "private_material")


def seal(output, artifact):
    output, artifact = Path(output), Path(artifact)
    require(not output.is_symlink() and not artifact.is_relative_to(output), "artifact_root")
    allowed = {"source-verification.json", "unit-result.json", "unit-wait.json", "component-wait.json", "supervisor.json"}
    allowed |= {"component/" + name for name in ("component-start.json", "component-result.json", "client-before.json", "client-after.json")}
    allowed |= {"component/case-%02d.json" % index for index in range(15)}
    members = []
    for path in sorted(output.rglob("*")):
        require(not path.is_symlink(), "artifact_symlink")
        if path.is_dir():
            require(path == output / "component", "artifact_directory")
            continue
        name = path.relative_to(output).as_posix()
        require(name in allowed and path.is_file(), "artifact_member")
        raw = path.read_bytes()
        require(0 < len(raw) < 1_400_000, "artifact_size")
        value = json.loads(raw)
        require(type(value) is dict, "artifact_object")
        check_json(value)
        members.append((name.replace("/", "--"), raw))
    require(0 < len(members) <= 24, "artifact_count")
    artifact.mkdir(exist_ok=False)
    refs = []
    for name, raw in members:
        with (artifact / name).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require((artifact / name).read_bytes() == raw, "artifact_readback")
        refs.append({"path": name, "sha256": sha(raw), "bytes": len(raw)})
    save(artifact / "artifact-manifest.json", {"format": "native-component-artifact-v2", "files": refs,
        "full_admission": False, "hosted_admitted": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "run", "units", "seal"))
    for key in ("root", "output", "artifact", "private", "expected", "commit", "ci-run", "host-network"):
        parser.add_argument("--" + key)
    args = parser.parse_args()
    if args.mode == "verify":
        value = verify_sources(args.root, args.expected)
        Path(args.output).mkdir(exist_ok=False)
        save(Path(args.output) / "source-verification.json", value)
    elif args.mode == "units":
        return 0 if unit_checks(args.root, args.output) else 1
    elif args.mode == "seal":
        seal(args.output, args.artifact)
    else:
        return 0 if supervise(args.root, args.output, args.private, args.expected, args.commit,
                              args.ci_run, args.host_network) else 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "INCOMPLETE", "error_class": type(error).__name__, "full_admission": False}))
        raise SystemExit(1) from None
