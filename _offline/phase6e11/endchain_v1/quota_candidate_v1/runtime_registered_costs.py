"""Reviewed source-derived bounds, guarded before native connection dispatch.

These are SQL command bounds, not WAL/IO bounds or observed counts. Upstream
release-source analysis does not independently attest the image build chain.
"""
import base64
import hashlib
import importlib.metadata
import os
import pathlib

UPSTREAM = [
    {
        "url": "https://raw.githubusercontent.com/supabase/auth/v2.197.0/cmd/serve_cmd.go",
        "sha256": "86a19a36523bb568c9853eeedf01ac34a9bb3d9ce80b9599d38defe325526ff7"
    },
    {
        "url": "https://raw.githubusercontent.com/supabase/auth/v2.197.0/internal/storage/dial.go",
        "sha256": "fcdee7df9849a19a37100fbba79952ecb534a9b2bb7edc1a4b21708ec3172087"
    },
    {
        "url": "https://raw.githubusercontent.com/supabase/auth/v2.197.0/internal/api/apiworker/apiworker.go",
        "sha256": "33fcd5d4edffdea225a5b69efc824a8cf7bbc7251570d9f1102e3ec4afd05edc"
    },
    {
        "url": "https://raw.githubusercontent.com/supabase/auth/v2.197.0/internal/api/api.go",
        "sha256": "806ea39c37b8ea189cffc9361073c792f80993b5849f3d50a8ea9a25f3ef92fc"
    },
    {
        "url": "https://raw.githubusercontent.com/gobuffalo/pop/v6.1.1/connection.go",
        "sha256": "f0db0a072084713058ab7d176d36ed150b1149820c8f31b9471d5a73598c1737"
    },
    {
        "url": "https://raw.githubusercontent.com/gobuffalo/pop/v6.1.1/connection_instrumented.go",
        "sha256": "d6cc8247e3a8e755cbf7812446b4cdd9f22bedeb621190764b1e9b05b4f9758c"
    },
    {
        "url": "https://raw.githubusercontent.com/gobuffalo/pop/v6.1.1/dialect_common.go",
        "sha256": "2993ac5eb3e7d27a9642e7b870c204369ace81d10b2bcbc6dc042191646859a2"
    },
    {
        "url": "https://raw.githubusercontent.com/jackc/pgx/v4.18.2/stdlib/sql.go",
        "sha256": "40d39e0e134a9231bebc810a2bc9220dad583a294e95d12ecb882cd00ed23a69"
    },
    {
        "url": "https://raw.githubusercontent.com/jackc/pgx/v4.18.2/conn.go",
        "sha256": "51b276f6bbbbe9fa63aa5d588696018ccea7b6ce6c5b04d0680633cb2a7c37f1"
    },
    {
        "url": "https://raw.githubusercontent.com/jackc/pgx/v4.18.2/tx.go",
        "sha256": "4b637698b6f9cd341a150feb55b18f85b95fbbfee4ca0a60ea7d04109db545de"
    },
    {
        "url": "https://raw.githubusercontent.com/jackc/pgconn/v1.14.3/config.go",
        "sha256": "567c93a8018eada07e2c73bb411f0e8fd98e4828c78e874703dca592901f23fe"
    },
    {
        "url": "https://raw.githubusercontent.com/jackc/pgconn/v1.14.3/pgconn.go",
        "sha256": "e66cef24242803d916af0a4fb53f41bbd188082affdfa2b8b6ce6442f58c83ad"
    },
    {
        "url": "https://raw.githubusercontent.com/postgres/postgres/REL_16_9/src/interfaces/libpq/fe-connect.c",
        "sha256": "9201ede8e247bdf9f5b6a661268623bf533b5b89f656051df423d807da3be351"
    },
    {
        "url": "https://raw.githubusercontent.com/postgres/postgres/REL_17_6/src/interfaces/libpq/fe-connect.c",
        "sha256": "3d6d86498961f84be36b06061565c8ad21d9945d3b4bc2badfab4f4b439e8452"
    },
    {
        "url": "https://raw.githubusercontent.com/psycopg/psycopg/3.2.10/psycopg/psycopg/connection.py",
        "sha256": "026f05838e6198b52a2f7fb2d72e60029fee4937f2fa80d4d2b6400387729ecf"
    },
    {
        "url": "https://raw.githubusercontent.com/psycopg/psycopg/3.2.10/psycopg/psycopg/_connection_base.py",
        "sha256": "047afac6019de9f1d3313e1c35ac1d76d6a985b50d9dd96144814bfcb8cf645b"
    },
    {
        "url": "https://raw.githubusercontent.com/psycopg/psycopg/3.2.10/psycopg/psycopg/generators.py",
        "sha256": "9ff3f4e458f13dd6c9597ce78d15f8a9fc32a90c2a76bdc9ea4981123b4f8f63"
    },
    {
        "url": "https://raw.githubusercontent.com/psycopg/psycopg/3.2.10/psycopg/psycopg/_conninfo_attempts.py",
        "sha256": "d4302f31e6a38c2b0b254721119dfe106bb490e2beb15d8e9744d6c83af0767a"
    },
    {
        "url": "https://raw.githubusercontent.com/psycopg/psycopg/3.2.10/psycopg/psycopg/_conninfo_utils.py",
        "sha256": "008bda02cdd0a7c7b029fcfced01ba9fdbbd67da0e862f1089306c799b013575"
    }
]
DRIVER_SOURCES = {
    "connection.py": "026f05838e6198b52a2f7fb2d72e60029fee4937f2fa80d4d2b6400387729ecf",
    "_connection_base.py": "047afac6019de9f1d3313e1c35ac1d76d6a985b50d9dd96144814bfcb8cf645b",
    "generators.py": "9ff3f4e458f13dd6c9597ce78d15f8a9fc32a90c2a76bdc9ea4981123b4f8f63",
    "_conninfo_attempts.py": "d4302f31e6a38c2b0b254721119dfe106bb490e2beb15d8e9744d6c83af0767a",
    "_conninfo_utils.py": "008bda02cdd0a7c7b029fcfced01ba9fdbbd67da0e862f1089306c799b013575"
}
NATIVE_SOURCES = {
    "native_runtime.py": "9d086efe38a5b42b83684754cdc644ed461fbb9ee0311d5ca53fff5445b5ac3a",
    "auth_failure.py": "cef5c102f726c672e3dafea05835f19549c355a15825375bf094eb31f89e8f02",
}


def require(value, code):
    if not value:
        raise ValueError("registered_cost_" + code)


def source_bound_contract():
    return {
        "format": "registered-startup-derived-cost-v1",
        "source_hashes": {item["url"]: item["sha256"] for item in UPSTREAM},
        "normal_max": 3,
        "normal_commands": ["BEGIN", "SHOW max_connections", "COMMIT"],
        "fault_prefixes": [[], ["BEGIN"], ["BEGIN", "ROLLBACK"],
                          ["BEGIN", "SHOW max_connections", "ROLLBACK"]],
        "managed_startup_full_bound": 3,
        "connection_open_sql": 0, "connection_close_sql": 0,
        "driver_implicit_sql_bound": 0,
        "covered_managed_group": "auth.managed_lifetime",
        "native_guard": "native_proof before every connection operation",
        "preconditions": [
            "exact pinned v2.197.0 image and serve-only argv; no config/watch flags",
            "configured cleanup/index/reload/metrics/tracing/background workers disabled",
            "single ApplyConfig; lazy Pop Open; SQLx Get not PrepareNamed",
            "pgx standard connector with target_session_attrs any and no custom hooks",
            "native psycopg 3.2.10 binary, reviewed libpq, exact source hashes",
            "single loopback target, autocommit True, prepare_threshold None"],
        "limitations": [
            "release-source derivation, not independent OCI build provenance",
            "not measured SQL; no WAL/temp or future writer quiescence claim",
            "managed HTTP costs and explicit native commands remain separate",
            "startup may overlap requests; settle whole lifetime once after stop",
            "unknown connections/HTTP outcomes are never converted to numeric zero"],
        "full_chain_admission": False, "hosted_admitted": False}


def native_proof(parameters):
    """Read local driver identity only; never open a connection or export a DSN."""
    import psycopg
    import psycopg.pq
    import native_runtime
    import auth_failure
    require(psycopg.__version__ == "3.2.10" and psycopg.pq.__impl__ == "binary",
            "driver_version")
    require(psycopg.pq.version() in (160009, 170006), "libpq_unreviewed")
    require(os.environ.get("PGTARGETSESSIONATTRS", "any") == "any"
            and not any(os.environ.get(k) for k in ("PGSERVICE", "PGSERVICEFILE")),
            "implicit_target_probe_or_service")
    require(type(parameters) is dict
            and parameters.get("target_session_attrs", "any") == "any"
            and not any(k in parameters for k in ("service", "servicefile"))
            and parameters.get("host") == "127.0.0.1"
            and parameters.get("hostaddr", "127.0.0.1") == "127.0.0.1",
            "actual_connection_parameters")
    sources = {}
    folder = pathlib.Path(psycopg.__file__).resolve().parent
    for name, expected in DRIVER_SOURCES.items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        require(actual == expected, "driver_source_changed")
        sources["psycopg/" + name] = actual
    for module in (native_runtime, auth_failure):
        path = pathlib.Path(module.__file__)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == NATIVE_SOURCES[path.name], "native_source_changed")
        sources[path.name] = actual
    distribution = importlib.metadata.distribution("psycopg-binary")
    require(distribution.version == "3.2.10", "binary_version")
    binaries = {}
    for item in distribution.files or ():
        if str(item).startswith("psycopg_binary/") and str(item).endswith((".so", ".pyd")):
            raw = pathlib.Path(distribution.locate_file(item)).read_bytes()
            digest = hashlib.sha256(raw).digest()
            require(item.hash is not None and item.hash.mode == "sha256"
                and base64.urlsafe_b64encode(digest).decode().rstrip("=") == item.hash.value,
                    "binary_record_changed")
            binaries[str(item)] = digest.hex()
    require(len(binaries) == 2, "binary_inventory")
    return {"psycopg_version": psycopg.__version__, "implementation": psycopg.pq.__impl__,
        "libpq_version": psycopg.pq.version(), "source_hashes": sources,
        "binary_hashes": binaries, "connection_open_sql": 0, "connection_close_sql": 0,
        "parameter_scope": "direct_loopback_connect_close_no_context_exit",
        "target_session_attrs": "any", "service_absent": True,
        "server_connection_executed": False, "hosted_admitted": False}

