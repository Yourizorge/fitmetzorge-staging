"""Linux-only C probe adapter. Synthetic loopback TLS, never admission evidence."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import socket
import ssl
import sys
import uuid
from unittest.mock import patch

PROBE_SHA = "715a5ca9335a68e346f010d122b13652703926cd03b2d67604af3bfb34176daf"
NATIVE_SHA = "9d086efe38a5b42b83684754cdc644ed461fbb9ee0311d5ca53fff5445b5ac3a"
SAFE_PARAMS = ("host", "hostaddr", "port", "dbname", "user", "sslmode", "connect_timeout",
               "gssencmode", "options", "target_session_attrs")
FILE_PARAMS = ("sslrootcert", "sslcert", "sslkey", "passfile")
RESERVED = {"6f8c8909-9b79-4011-a9d1-db5e23c6b6c1", "11a909f4-7113-424a-aa4b-ce9964720a3e"}
CASE_SECONDS = 15


def require(ok, code):
    if not ok:
        raise ValueError("native_component_" + code)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_probe(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PROBE_SHA, "probe_source")
    spec = importlib.util.spec_from_file_location("saved_c_native_probe", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def scrub_environment(environment):
    # Do not retain values, hashes or names of ambient PG credentials in receipts.
    return {key: value for key, value in environment.items() if not key.upper().startswith("PG")}


def network_guard():
    require(sys.platform == "linux" and os.geteuid() != 0, "unprivileged_linux_required")
    require([name for _, name in socket.if_nameindex()] == ["lo"], "loopback_namespace_required")
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    require(status.get("NoNewPrivs", "").strip() == "1" and
            all(int(status[key].strip(), 16) == 0 for key in ("CapEff", "CapPrm", "CapAmb", "CapBnd")),
            "privileges_not_dropped")
    return {"interface_names": ["lo"], "unprivileged": True, "no_new_privileges": True,
            "capabilities_zero": True, "network_namespace": os.readlink("/proc/self/ns/net")}


class CaseDeadline(TimeoutError):
    pass


@contextmanager
def case_deadline():
    def expired(*_):
        raise CaseDeadline("native_component_case_deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, CASE_SECONDS)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def mapped_binary(path, maps):
    path = Path(path).resolve(strict=True)
    current = path.stat()
    rows = [line.split(maxsplit=5) for line in maps.splitlines()]
    selected = [row for row in rows if len(row) == 6 and row[5] == str(path)]
    require(bool(selected), "binary_not_loaded")
    for row in selected:
        major, minor = (int(n, 16) for n in row[3].split(":"))
        require(int(row[4]) == current.st_ino and
                (major, minor) == (os.major(current.st_dev), os.minor(current.st_dev)), "mapped_binary_identity")
    digest = file_hash(path)
    after = path.stat()
    require((current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "binary_changed")
    return {"name": path.name, "sha256": digest, "bytes": current.st_size,
            "mapped_inode_matches": True}


def client_identity(probe, native_path):
    require(sys.platform == "linux", "linux_required")
    import psycopg
    import psycopg_binary.pq as binary_pq
    import psycopg_binary._psycopg as binary_driver
    import _ssl
    import _cffi_backend
    import cryptography.hazmat.bindings._rust as crypto_binary
    from psycopg import pq
    client = probe.identity(native_path)
    require((client["psycopg"], client["binary_package"], client["implementation"]) ==
            ("3.2.10", "3.2.10", "binary"), "client_version")
    require(pq.PGconn is binary_pq.PGconn, "loaded_pq_implementation")
    maps = Path("/proc/self/maps").read_text()
    libs = Path(psycopg.__file__).resolve().parent.parent / "psycopg_binary.libs"
    loaded = []
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            path = Path(fields[5])
            if path.name.startswith("libpq"):
                loaded.append(path)
    loaded = sorted(set(loaded))
    require(len(loaded) == 1 and loaded[0].parent.resolve() == libs.resolve(), "loaded_libpq")
    binary_paths = {Path(module.__file__).resolve() for module in
                    (binary_pq, binary_driver, _ssl, _cffi_backend, crypto_binary)} | {loaded[0]}
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            path = Path(fields[5])
            if path.name.startswith(("libssl", "libcrypto")):
                binary_paths.add(path)
    client["loaded_binaries"] = [mapped_binary(path, maps) for path in sorted(binary_paths)]
    client["python_version"] = sys.version.split()[0]
    client["python_executable_sha256"] = file_hash(sys.executable)
    client["python_openssl"] = ssl.OPENSSL_VERSION
    client["support_packages"] = {name: importlib.metadata.version(name)
                                  for name in ("cryptography", "cffi", "pycparser", "typing_extensions")}
    client["reviewed_windows_libpq_version"] = 160009
    client["matches_C_reviewed_libpq_version"] = client["libpq_runtime"] == 160009
    client["build_attestation_proven"] = False
    return client


def validate_dispatch(kwargs, expected, row_factory, ambient):
    require(set(kwargs) == set(expected) | {"autocommit", "prepare_threshold", "row_factory"}, "dispatch_fields")
    require(all(kwargs[key] == value for key, value in expected.items()), "dispatch_parameters")
    require(kwargs["autocommit"] is True and kwargs["prepare_threshold"] is None
            and kwargs["row_factory"] is row_factory, "driver_configuration")
    pg = {k: v for k, v in os.environ.items() if k.upper().startswith("PG")}
    require(pg == ({"PGTARGETSESSIONATTRS": ambient} if ambient else {}), "ambient_pg")


def effective_parameters(connection, requested, target):
    allowed = set(SAFE_PARAMS) | set(FILE_PARAMS) | {"service", "servicefile"}
    values = {}
    for option in connection.pgconn.info:
        key = option.keyword.decode("ascii")
        if key in allowed:
            require(key not in values, "duplicate_effective_parameter")
            values[key] = option.val.decode("ascii") if option.val is not None else None
    require(not values.get("service") and not values.get("servicefile"), "effective_service")
    for key in (*SAFE_PARAMS, *FILE_PARAMS):
        wanted = target if key == "target_session_attrs" else str(requested[key])
        require(values.get(key) == wanted, "effective_parameters")
    require(connection.pgconn.ssl_in_use is True, "effective_tls")
    return {key: values[key] for key in SAFE_PARAMS}


def observe_case(probe, native, cert, key, case, recheck):
    import psycopg
    from psycopg.rows import dict_row
    actual_connect, parameters = psycopg.connect, probe.parameters
    observed = {"attempts": [], "wire": None}
    expected = {}

    def capture_parameters(peer):
        require(peer.sock.getsockname() == ("127.0.0.1", peer.port), "peer_binding")
        value = parameters(peer)
        expected.update(value)
        if case[3]:
            expected["target_session_attrs"] = case[3]
        return value

    def connect(*args, **kwargs):
        require(not args and bool(expected), "positional_conninfo")
        require(not observed["attempts"], "connect_dispatch_limit")
        validate_dispatch(kwargs, expected, dict_row, case[2])
        recheck()
        target = case[3] or case[2] or "any"
        item = {"requested": {k: str(expected[k]) for k in SAFE_PARAMS if k in expected},
                "controlled_target_session_attrs": target, "ambient_PG_scrubbed": True,
                "effective": None, "driver_returned_connection": False, "error_class": None,
                "autocommit": True, "prepare_threshold": None, "row_factory": "psycopg.rows.dict_row"}
        observed["attempts"].append(item)
        connection = None
        try:
            connection = actual_connect(**kwargs)
            item["driver_returned_connection"] = True
            item["effective"] = effective_parameters(connection, expected, target)
            return connection
        except BaseException as error:
            item["error_class"] = type(error).__name__
            if connection is not None:
                try:
                    connection.close()
                except Exception as secondary:
                    error.add_note("component_close_secondary:" + type(secondary).__name__)
            raise

    try:
        with patch.object(probe, "parameters", capture_parameters), patch.object(psycopg, "connect", connect):
            observed["wire"] = probe.exercise(native, cert, key, case)
        require(len(observed["attempts"]) == 1, "attempt_count")
        return observed
    except BaseException as error:
        # Caller persists the sanitized partial record, not exception messages.
        error.component_partial = observed
        raise


def save(probe, output, name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    require(len(raw) < 1_400_000, "receipt_size")
    path = output / name
    probe.save(path, value)
    require(path.read_bytes() == raw, "receipt_readback")
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run(probe_path, native_path, output, work, binding):
    require(set(binding) == {"run_id", "source_commit", "candidate_sha", "ci_run"}, "binding_fields")
    ident = uuid.UUID(binding["run_id"])
    require(ident.version == 4 and str(ident) == binding["run_id"] and str(ident) not in RESERVED, "case_uuid")
    require(re.fullmatch("[a-f0-9]{40}", binding["source_commit"]) and
            re.fullmatch("[a-f0-9]{64}", binding["candidate_sha"]) and
            re.fullmatch("[0-9]{1,24}", binding["ci_run"]), "binding")
    probe = load_probe(probe_path)
    require(file_hash(native_path) == NATIVE_SHA, "native_source")
    sources = {"native_connect_probe.py": PROBE_SHA, "native_runtime.py": NATIVE_SHA,
               "native_connect_component.py": file_hash(__file__)}
    output, work = Path(output).resolve(), Path(work).resolve()
    require(not output.is_relative_to(work) and not work.is_relative_to(output), "private_work_separation")
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    result = {"format": "linux-native-connect-component-v1", "binding": binding, "source_hashes": sources,
              "status": "INCOMPLETE", "phase": "preflight", "refs": [], "error_class": None,
              "full_admission": False, "hosted_admitted": False, "actual_postgres_test": False,
              "driver_implicit_sql_bound": None, "wal_observed": False,
              "limits": {"cases": 15, "connect_dispatches_per_case": 1,
                         "peer_accepts_per_case": 1, "case_alarm_seconds": CASE_SECONDS,
                         "libpq_internal_attempts": None},
              "authentication": "synthetic_AuthenticationOk_not_SCRAM_or_GoTrue"}
    primary = None
    try:
        result["refs"].append(save(probe, output, "component-start.json", dict(result)))
        require(sys.platform == "linux", "linux_required")
        result["isolation"] = network_guard()
        work.mkdir(mode=0o700, parents=True, exist_ok=False)
        with patch.dict(os.environ, scrub_environment(os.environ), clear=True):
            native = probe.load_native(native_path, NATIVE_SHA)
            before = client_identity(probe, native_path)
            result["refs"].append(save(probe, output, "client-before.json", before))
            cert, key = probe.certificates(work)
            cert.chmod(0o600)
            key.chmod(0o600)

            def recheck():
                require(file_hash(probe_path) == PROBE_SHA and file_hash(native_path) == NATIVE_SHA
                        and file_hash(__file__) == sources["native_connect_component.py"], "source_drift")
                require(client_identity(probe, native_path) == before, "client_drift")

            for index, case in enumerate(probe.CASES):
                result["phase"] = case[0]
                row, case_error = None, None
                try:
                    with case_deadline():
                        row = observe_case(probe, native, cert, key, case, recheck)
                except BaseException as error:
                    case_error = error
                    row = getattr(error, "component_partial", {"attempts": [], "wire": None})
                    raise
                finally:
                    if row is not None:
                        try:
                            result["refs"].append(save(probe, output, "case-%02d.json" % index,
                                {"binding": binding, "case": case[0], **row}))
                        except Exception as secondary:
                            if case_error is None:
                                raise
                            case_error.add_note("component_case_receipt_secondary:" + type(secondary).__name__)
            recheck()
            result["refs"].append(save(probe, output, "client-after.json", client_identity(probe, native_path)))
        result["status"], result["phase"] = "SYNTHETIC_COMPONENT_OBSERVED", "terminal"
    except BaseException as error:
        primary = error
        result["error_class"] = type(error).__name__
        raise
    finally:
        try:
            save(probe, output, "component-result.json", result)
        except Exception as secondary:
            if primary is None:
                raise
            primary.add_note("component_receipt_secondary:" + type(secondary).__name__)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe-source", "native-source", "output", "work", "run-id", "source-commit", "candidate-sha", "ci-run"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        value = run(args.probe_source, args.native_source, args.output, args.work,
                    {name: getattr(args, name) for name in ("run_id", "source_commit", "candidate_sha", "ci_run")})
        print(json.dumps({"status": value["status"], "full_admission": False}))
    except Exception as error:
        print(json.dumps({"status": "INCOMPLETE", "exception_class": type(error).__name__, "full_admission": False}))
        raise SystemExit(1) from None
