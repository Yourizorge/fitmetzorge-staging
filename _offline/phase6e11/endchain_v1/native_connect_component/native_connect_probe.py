"""Synthetic TLS wire evidence for NativeRuntime; never opens a database.

The peer implements a deliberately small PostgreSQL protocol, not PostgreSQL.
Only client SQL messages are counted. This cannot prove server work/WAL/temp,
GoTrue compatibility, an OCI binary provenance chain, or full admission.
Use the same entrypoint on the CI platform before transferring binary evidence.
"""
import argparse
import datetime
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import socket
import ssl
import struct
import threading
import time
from unittest.mock import patch


SOURCE_REFERENCES = {
    "driver": "https://github.com/psycopg/psycopg/tree/3.2.10",
    "libpq_local": "https://github.com/postgres/postgres/blob/REL_16_9/src/interfaces/libpq/fe-connect.c",
    "protocol": "https://www.postgresql.org/docs/17/protocol-flow.html",
}

# A source conclusion, not an admission capability. Consumers must establish
# these preconditions on the actual call, not trust this descriptive document.
CONDITIONAL_CONTRACT = {
    "scope": "client_emitted_SQL_during_connect_and_direct_close_only",
    "reviewed_psycopg": "3.2.10", "reviewed_libpq": 160009,
    "preconditions": [
        "actual_NativeRuntime_driver_and_loaded_libpq_bound_to_reviewed_bytes",
        "effective_target_session_attrs_any_in_actual_parameters_and_environment",
        "no_explicit_service_or_PGSERVICE_or_PGSERVICEFILE_override",
        "explicit_single_host_hostaddr_port_dbname_postgres_no_conninfo_expansion",
        "autocommit_True_prepare_threshold_None_builtin_dict_row_unmodified",
        "parameters_environment_and_driver_identity_unchanged_until_dispatch",
        "no_caller_callbacks_context_exit_or_query_execution_in_connect_scope",
    ],
    "conditional_sql_upper_bound": 0,
    "excluded": ["context_exit_active_transaction", "application_SQL",
                 "server_startup_internal_work", "WAL", "temporary_bytes",
                 "network_handshake_packets", "server_authentication_side_effects"],
    "unmet_precondition_sql_bound": None,
    "attempt_deadline": "connect_timeout_5_is_per_driver_attempt_not_global_multi_host_deadline",
    "startup_options": "startup_protocol_parameters_not_SET_SQL",
    "context_idle_exit_sql": 0,
    "context_active_exit_sql": "COMMIT_or_ROLLBACK_requires_separate_accounting",
    "binary_provenance": "local_file_hashes_and_reported_version_not_OCI_to_upstream_build_attestation",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_native(path, expected_sha):
    path = Path(path).resolve(strict=True)
    data = path.read_bytes()
    if sha(data) != expected_sha:
        raise ValueError("native_source_hash")
    # Execute the very bytes hashed, not a cached checkout import or .pyc.
    spec = importlib.util.spec_from_file_location("_c_synthetic_native", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module.NativeRuntime


def identity(native_path):
    import psycopg
    import psycopg_binary
    from psycopg import pq
    root = Path(psycopg.__file__).parent.parent
    paths = [Path(native_path)]
    for package in ("psycopg", "psycopg_binary", "psycopg_binary.libs"):
        paths.extend(p for p in (root / package).rglob("*")
                     if p.is_file() and any(s in (".py", ".pyd", ".so", ".dll") for s in p.suffixes))
    return {
        "psycopg": psycopg.__version__, "binary_package": psycopg_binary.__version__,
        "implementation": pq.__impl__, "libpq_runtime": pq.version(),
        "libpq_build": getattr(pq, "__build_version__", None),
        "platform": os.name,
        "files": [{"path": p.relative_to(root).as_posix() if p.is_relative_to(root)
                   else "native_runtime.py", "sha256": sha(p.read_bytes())}
                  for p in sorted(set(paths))],
    }


def certificates(directory):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    directory = Path(directory)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "synthetic-loopback-only")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
            .sign(key, hashes.SHA256()))
    cert_path, key_path = directory / "synthetic-cert.pem", directory / "synthetic-key.pem"
    for path, data in (
        (cert_path, cert.public_bytes(serialization.Encoding.PEM)),
        (key_path, key.private_bytes(serialization.Encoding.PEM,
                                    serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption())),
    ):
        with path.open("xb") as stream:
            stream.write(data)
    return cert_path, key_path


def packet(kind, body=b""):
    return kind + struct.pack("!I", len(body) + 4) + body


def receive(sock, size):
    data = b""
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise EOFError("synthetic_peer_eof")
        data += part
    return data


class Peer:
    """One bounded loopback connection; never forwards bytes anywhere."""

    def __init__(self, cert, key, *, statuses=True, failure=None):
        self.cert, self.key = cert, key
        self.statuses, self.failure = statuses, failure
        self.frames, self.queries, self.startup = [], [], {}
        self.error = None
        self.stop = threading.Event()
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(1)
        self.sock.settimeout(8)
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        self.thread.join(9)
        self.sock.close()
        if self.thread.is_alive():
            raise AssertionError("synthetic_peer_not_terminal")
        if self.error:
            raise AssertionError("synthetic_peer_" + type(self.error).__name__) from self.error

    def _run(self):
        try:
            with self.sock.accept()[0] as raw:
                raw.settimeout(8)
                if receive(raw, 8) != struct.pack("!II", 8, 80877103):
                    raise AssertionError("expected_ssl_request")
                raw.sendall(b"S")
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(self.cert, self.key)
                with context.wrap_socket(raw, server_side=True) as conn:
                    size = struct.unpack("!I", receive(conn, 4))[0]
                    if not 8 <= size <= 8192:
                        raise AssertionError("startup_bound")
                    data = receive(conn, size - 4)
                    if data[:4] != struct.pack("!I", 196608):
                        raise AssertionError("startup_protocol")
                    parts = data[4:].rstrip(b"\0").split(b"\0")
                    self.startup = dict(zip((p.decode() for p in parts[::2]),
                                            (p.decode() for p in parts[1::2])))
                    if self.failure == "eof":
                        return
                    if self.failure == "timeout":
                        self._read_frames(conn)
                        return
                    if self.failure == "auth":
                        conn.sendall(packet(b"E", b"SFATAL\0VFATAL\0C28000\0Msynthetic rejection\0\0"))
                        self._read_frames(conn)
                        return
                    parameters = {"server_version": "17.6", "server_encoding": "UTF8",
                                  "client_encoding": "UTF8", "standard_conforming_strings": "on"}
                    if self.statuses:
                        parameters.update(default_transaction_read_only="off", in_hot_standby="off")
                    reply = packet(b"R", struct.pack("!I", 0))
                    for k, v in parameters.items():
                        reply += packet(b"S", k.encode() + b"\0" + v.encode() + b"\0")
                    reply += packet(b"K", struct.pack("!II", 123, 456)) + packet(b"Z", b"I")
                    conn.sendall(reply)
                    self._read_frames(conn)
        except Exception as exc:
            self.error = exc

    def _read_frames(self, conn):
        for _ in range(16):
            try:
                kind = receive(conn, 1)
            except EOFError:
                return
            size = struct.unpack("!I", receive(conn, 4))[0]
            if not 4 <= size <= 8192:
                raise AssertionError("frame_bound")
            body = receive(conn, size - 4)
            self.frames.append(kind.decode("ascii"))
            if kind == b"X":
                return
            if kind != b"Q":
                raise AssertionError("unexpected_extended_or_auth_frame")
            query = body.rstrip(b"\0").decode("ascii")
            self.queries.append(query)
            if self.failure:
                raise AssertionError("unexpected_failure_path_sql")
            if query == "SHOW transaction_read_only":
                self._row(conn, b"off", b"SHOW")
            elif query == "SELECT pg_catalog.pg_is_in_recovery()":
                self._row(conn, b"f", b"SELECT 1")
            elif query in ("BEGIN", "COMMIT", "ROLLBACK"):
                conn.sendall(packet(b"C", query.encode() + b"\0")
                             + packet(b"Z", b"T" if query == "BEGIN" else b"I"))
            elif query == "SELECT 1":
                self._row(conn, b"1", b"SELECT 1")
            else:
                raise AssertionError("unexpected_sql")
        raise AssertionError("frame_count_bound")

    @staticmethod
    def _row(conn, value, command):
        field = b"result\0" + struct.pack("!IhIhih", 0, 0, 25, -1, -1, 0)
        conn.sendall(packet(b"T", struct.pack("!h", 1) + field)
                     + packet(b"D", struct.pack("!hi", 1, len(value)) + value)
                     + packet(b"C", command + b"\0") + packet(b"Z", b"I"))


def parameters(peer):
    return {"host": "127.0.0.1", "hostaddr": "127.0.0.1", "port": peer.port,
            "dbname": "postgres", "user": "synthetic_probe", "password": "synthetic-only",
            "sslmode": "verify-full", "sslrootcert": str(peer.cert), "connect_timeout": 5,
            "sslcert": str(peer.cert.parent / "no-client-certificate"),
            "sslkey": str(peer.cert.parent / "no-client-key"),
            "passfile": str(peer.cert.parent / "no-password-file"),
            "gssencmode": "disable", "options": "-c statement_timeout=5000 -c lock_timeout=1000"}


CASES = (
    ("ordinary", True, None, None, None, None, []),
    ("ordinary_missing_status", False, None, None, None, None, []),
    ("ambient_readwrite_probe", False, "read-write", None, None, None,
     ["SHOW transaction_read_only"]),
    ("ambient_primary_probe", False, "primary", None, None, None,
     ["SELECT pg_catalog.pg_is_in_recovery()"]),
    ("reported_pg17_status", True, "read-write", None, None, None, []),
    ("explicit_any_overrides", False, "read-write", "any", None, None, []),
    ("auth_rejection", True, None, None, "auth", None, []),
    ("startup_eof", True, None, None, "eof", None, []),
    ("startup_timeout_5s", True, None, None, "timeout", None, []),
    ("autocommit_select", True, None, None, None, "select", ["SELECT 1"]),
    ("no_prepare_after_threshold", True, None, None, None, "repeat", ["SELECT 1"] * 7),
    ("close_active", True, None, None, None, "close_active", ["BEGIN"]),
    ("context_idle", True, None, None, None, "context_idle", []),
    ("context_commit", True, None, None, None, "context_commit", ["BEGIN", "COMMIT"]),
    ("context_rollback", True, None, None, None, "context_rollback", ["BEGIN", "ROLLBACK"]),
)


def exercise(native, cert, key, case):
    import psycopg
    from psycopg.rows import dict_row
    name, statuses, ambient, explicit, failure, action, expected = case
    # Preserve non-PG environment; do not read service/pass files or owner secrets.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
    if ambient:
        env["PGTARGETSESSIONATTRS"] = ambient
    error_class = None
    with patch.dict(os.environ, env, clear=True), Peer(cert, key, statuses=statuses, failure=failure) as peer:
        params = parameters(peer)
        if explicit:
            params["target_session_attrs"] = explicit
        runtime = native(params, "http://127.0.0.1:59999", environment="disposable_ci")
        connection = None
        started = time.monotonic()
        try:
            try:
                connection = runtime.connect()
            except psycopg.OperationalError as exc:
                error_class = type(exc).__name__
                if not failure:
                    raise
            connect_seconds = time.monotonic() - started
            if failure and error_class is None:
                raise AssertionError("failure_not_observed")
            if connection:
                if not connection.autocommit or connection.prepare_threshold is not None or connection.row_factory is not dict_row:
                    raise AssertionError("native_configuration")
                if action in ("select", "repeat"):
                    for _ in range(7 if action == "repeat" else 1):
                        if connection.execute("SELECT 1").fetchone() != {"result": "1"}:
                            raise AssertionError("row_factory_result")
                if action == "close_active":
                    connection.execute("BEGIN")
                if action in ("context_commit", "context_idle"):
                    with connection:
                        if action == "context_commit":
                            connection.execute("BEGIN")
                if action == "context_rollback":
                    try:
                        with connection:
                            connection.execute("BEGIN")
                            raise ValueError("synthetic_primary")
                    except ValueError as exc:
                        if str(exc) != "synthetic_primary":
                            raise
        finally:
            if connection is not None:
                connection.close()
                connection.close()
            runtime.clear()
    if peer.queries != expected:
        raise AssertionError("wire_sql_mismatch:" + name)
    if peer.startup.get("options") != params["options"]:
        raise AssertionError("startup_options_missing")
    return {"case": name, "client_frames": peer.frames, "sql": peer.queries,
            "sql_messages": len(peer.queries), "startup_options": peer.startup["options"],
            "error_class": error_class, "peer_terminal": not peer.thread.is_alive(),
            "capture_to_client_termination": failure != "eof",
            "connect_elapsed_seconds": round(connect_seconds, 6),
            "authentication": "synthetic_AuthenticationOk_not_SCRAM_or_GoTrue",
            "tls": "verify-full", "database_contacted": False}


def run(native_path, expected_sha, output):
    native = load_native(native_path, expected_sha)
    client = identity(native_path)
    if (client["psycopg"], client["binary_package"], client["implementation"]) != ("3.2.10", "3.2.10", "binary"):
        raise ValueError("driver_version")
    output = Path(output)
    output.mkdir(exist_ok=False, parents=True)
    cert, key = certificates(output)
    receipt = {"format": "native-connect-synthetic-wire-v1", "client": client,
               "source_references": SOURCE_REFERENCES, "source_contract": CONDITIONAL_CONTRACT,
               "cases": [],
               "driver_implicit_sql_bound": None, "full_admission": False,
               "actual_postgres_test": False, "wal_observed": False,
               "reason": "conditional_wire_diagnostic_requires_consumer_source_environment_binding"}
    for index, case in enumerate(CASES):
        observation = exercise(native, cert, key, case)
        save(output / ("case-%02d.json" % index), observation)
        receipt["cases"].append(observation)
    save(output / "receipt.json", receipt)
    return receipt


def save(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-source", required=True)
    parser.add_argument("--native-sha", required=True)
    parser.add_argument("--output-directory", required=True)
    args = parser.parse_args()
    result = run(args.native_source, args.native_sha, args.output_directory)
    print(json.dumps({"cases": len(result["cases"]), "libpq": result["client"]["libpq_runtime"],
                      "actual_postgres_test": False, "full_admission": False}))
