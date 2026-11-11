"""Bounded, fresh-process installed terminal reader; never artifact execution."""
import ast
import base64
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import types

PREFIX = "_offline/phase6e11/endchain_v1/"
SELF = PREFIX + "admission_terminal_process.py"
LOADER = PREFIX + "admission_trusted_loader.py"
READER = "quota_candidate_v1.runtime_exported_terminal"
READER_PATH = PREFIX + READER.replace(".", "/") + ".py"
PACKAGE = PREFIX + "quota_candidate_v1/__init__.py"
MAX_MEMBER = 2_000_000
MAX_REQUEST = 64 * 1024 * 1024
MAX_RESPONSE = 2_000_000
WAIT_SECONDS = 60
REAP_SECONDS = 5
RECOVERY_FRAGMENTS = {
    PREFIX + 'control_recovery.py': (
        '28489db090803bb1df868570c87a9f2a3dbc5c842fbbb81faa5ea837b55520eb',
        (('replace_setup', 'recover'),)),
    PREFIX + 'quota_candidate_v1/runtime_worker_evidence.py': (
        '57c4737921d87abc1bfe9cc62bfc67236359c79e0d66fdd109fae2f422bf6e5d',
        (('WaitEvidence',), ('save',))),
    PREFIX + 'quota_candidate_v1/runtime_recovery.py': (
        '44d315a22a782871f3c1cc4a825537814b80f266f1bfb114ccb0b14234d189a9',
        (('finish',),)),
}
DENIED = {"subprocess.Popen", "os.system", "os.spawn", "os.posix_spawn", "os.fork",
          "os.exec", "socket.connect", "socket.connect_ex", "socket.bind",
          "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}
BOOTSTRAP = r"""
import hashlib,pathlib,sys
root=pathlib.Path(sys.argv[1])
path=root/'_offline/phase6e11/endchain_v1/admission_terminal_process.py'
assert path.is_file() and path.stat().st_size<=2000000
assert all(not p.is_symlink() and not getattr(p,'is_junction',lambda:False)() for p in (path,*path.parents))
assert path.resolve(strict=True).is_relative_to(root.resolve(strict=True))
raw=path.read_bytes()
assert len(raw)<=2000000 and hashlib.sha256(raw).hexdigest()==sys.argv[2]
namespace={'__name__':'_installed_terminal_child','__file__':str(path)}
exec(compile(raw,str(path),'exec',dont_inherit=True),namespace)
raise SystemExit(namespace['child'](root,sys.argv[2],pathlib.Path(sys.argv[3]),sys.argv[4],pathlib.Path(sys.argv[5])))
"""


class Blocked(ValueError):
    pass


def need(value, code):
    if not value:
        raise Blocked(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "duplicate_json")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: need(False, "nonfinite_json"))


def plain(path):
    return all(not p.is_symlink() and not getattr(p, "is_junction", lambda: False)()
               for p in (path, *path.parents))


def source(root, name, sources):
    need(name in sources and type(sources[name]) is str
         and re.fullmatch("[a-f0-9]{64}", sources[name]), "source_pin")
    path = root / name
    need(plain(path) and path.resolve(strict=True).is_relative_to(root)
         and path.is_file() and path.stat().st_size <= MAX_MEMBER, "source_origin")
    raw = path.read_bytes()
    need(len(raw) <= MAX_MEMBER and sha(raw) == sources[name], "source_hash")
    return raw


def save(path, value, limit):
    raw = encode(value)
    need(len(raw) <= limit, "output_limit")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    need(path.read_bytes() == raw, "output_readback")


def member_name(name):
    need(type(name) is str and 0 < len(name) <= 240
         and re.fullmatch("[A-Za-z0-9_./-]+", name)
         and all(p not in ("", ".", "..") and not p.endswith(".")
                 and not re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
                 for p in name.split("/")), "member_name")


def blob_map(value, maximum, total, *, unpack=False):
    need(type(value) is dict and 0 < len(value) <= maximum, "member_count")
    result, size = {}, 0
    folded = set()
    for name, raw in value.items():
        member_name(name)
        need(name.casefold() not in folded, "member_alias")
        folded.add(name.casefold())
        if unpack:
            need(type(raw) is str and len(raw) <= 4*((MAX_MEMBER+2)//3), "member_encoding")
            raw = base64.b64decode(raw, validate=True)
        need(type(raw) is bytes and len(raw) <= MAX_MEMBER, "member_size")
        size += len(raw)
        need(size <= total, "total_size")
        result[name] = raw if unpack else base64.b64encode(raw).decode("ascii")
    return result


def source_map(value):
    need(type(value) is dict and 0 < len(value) <= 4096, "source_count")
    folded = set()
    for name, digest in value.items():
        member_name(name)
        need(name.casefold() not in folded and type(digest) is str
             and re.fullmatch("[a-f0-9]{64}", digest), "source_map")
        folded.add(name.casefold())
    return value


def binding(case, payloads, head, candidate, run):
    need(type(case) is dict and type(case.get("case_name")) is str
         and re.fullmatch("[a-z_]{1,40}", case["case_name"])
         and type(case.get("run_id")) is str
         and re.fullmatch("[a-f0-9-]{36}", case["run_id"]), "case_binding")
    need(type(head) is str and re.fullmatch("[a-f0-9]{40}", head)
         and type(candidate) is str and re.fullmatch("[a-f0-9]{64}", candidate)
         and re.fullmatch("[0-9]{1,24}", str(run)), "external_binding")
    need("case-execution.json" in payloads, "case_original")
    return {"case_name": case["case_name"], "run_id": case["run_id"],
            "case_sha256": sha(payloads["case-execution.json"])}


def report_ok(value, identity):
    need(type(value) is dict and value.get("status") == "CASE_TERMINAL_UNVERIFIED"
         and all(value.get(k) == v for k, v in identity.items())
         and value.get("full_chain_admission") is False
         and value.get("hosted_admitted") is False, "reader_claim")
    need(len(encode(value)) <= MAX_RESPONSE - 8192, "report_limit")
    return value


def no_go(identity, reason):
    return {"status": "CASE_TERMINAL_UNVERIFIED", **identity, "checks": {},
            "missing": [reason], "invalid": [], "full_chain_admission": False,
            "hosted_admitted": False}


def child_environment(private):
    result = {"PATH": str(Path(sys.executable).parent), "HOME": str(private),
              "USERPROFILE": str(private), "TEMP": str(private), "TMP": str(private)}
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if name in os.environ:
                result[name] = os.environ[name]
    return result


def wait_child(command, environment, cwd, timeout=WAIT_SECONDS):
    result = {"timeout_seconds": timeout, "reap_seconds": REAP_SECONDS,
              "wait_completed": False, "returncode": None, "timed_out": False,
              "kill_requested": False, "accepted": False, "error_class": None}
    process = None
    try:
        kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                  "stderr": subprocess.DEVNULL, "env": environment, "cwd": cwd}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(command, **kwargs)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
            result["kill_requested"] = True
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=REAP_SECONDS)
        need(type(code) is int and process.returncode == code, "wait_result")
        result["wait_completed"], result["returncode"] = True, code
        result["accepted"] = code == 0 and not result["timed_out"]
    except BaseException as error:
        result["error_class"] = type(error).__name__
        if process is not None and not result["kill_requested"] and not result["wait_completed"]:
            result["kill_requested"] = True
            try:
                if os.name == "nt":
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=REAP_SECONDS)
                if type(code) is int and process.returncode == code:
                    result["wait_completed"], result["returncode"] = True, code
            except BaseException as secondary:
                result["reap_error_class"] = type(secondary).__name__
    return result


class AliasLoader:
    def __init__(self, owner):
        self.owner = owner

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        try:
            self.execute(module)
        except BaseException:
            self.owner.failed = True
            raise

    def execute(self, module):
        owner, name = self.owner, module.__spec__.name
        owner.live()
        need(name not in sys.modules, "legacy_cached_alias")
        # module_from_spec normally leaves registration to its caller.
        # Register only this new exact-source object; never overwrite a cache.
        sys.modules[name] = module
        module.__loader__ = owner
        module.__spec__.loader = owner
        owner.exec_module(module)


def enable_legacy(loader):
    def checked_spec(owner, name, location=None, *args, **kwargs):
        owner.live()
        need(not args and not kwargs and type(name) is str
             and re.fullmatch("[A-Za-z_][A-Za-z0-9_]*", name), "legacy_spec_shape")
        need(name not in sys.modules and name not in owner.owned, "legacy_cached_alias")
        path = Path(location).absolute()
        need(plain(path) and path.resolve(strict=True).is_relative_to(owner.root), "legacy_origin")
        path = path.resolve(strict=True)
        relative = path.relative_to(owner.root).as_posix()
        need(relative.endswith(".py") and path.name != "__init__.py", "legacy_python_source")
        need(name not in owner.index or owner.index[name] == (relative, False), "legacy_alias_conflict")
        raw = owner.raw(relative)
        owner.index[name] = (relative, False)
        spec = importlib.machinery.ModuleSpec(name, AliasLoader(owner), origin=str(path))
        spec.has_location = True
        spec.loader_state = raw
        return spec
    def file_spec(owner, name, location=None, *args, **kwargs):
        try:
            return checked_spec(owner, name, location, *args, **kwargs)
        except BaseException:
            owner.failed = True
            raise
    loader.file_spec = types.MethodType(file_spec, loader)


def recovery_fragment(loader, path, code):
    name = path.relative_to(loader.root).as_posix()
    entry = RECOVERY_FRAGMENTS.get(name)
    if entry is None:
        return False
    expected_hash, selections = entry
    raw = loader.raw(name)
    need(sha(raw) == expected_hash, 'recovery_fragment_source')
    tree = ast.parse(raw)
    for names in selections:
        found = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        need(len(found) == len(names) and {node.name for node in found} == set(names),
             'recovery_fragment_definition')
        expected = compile(ast.Module(body=found, type_ignores=[]), str(path), 'exec',
                           dont_inherit=True, optimize=sys.flags.optimize)
        if code == expected:
            return True
    return False


def install_audit(loader, private):
    def checked_audit(event, values):
        if event in DENIED:
            raise Blocked("offline_action_denied")
        if event == "exec" and values:
            code = values[0]
            filename = getattr(code, "co_filename", "")
            if filename and not filename.startswith("<"):
                path = Path(filename).resolve()
                if path.is_relative_to(loader.root):
                    relative = path.relative_to(loader.root).as_posix()
                    raw = loader.raw(relative)
                    need(code == compile(raw, str(path), "exec", dont_inherit=True,
                                         optimize=sys.flags.optimize)
                         or recovery_fragment(loader, path, code), "execution_not_exact_source")
        paths = ()
        if event == "open" and values and isinstance(values[0], (str, bytes, os.PathLike)):
            mode, flags = values[1], values[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")
                    or isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                paths = (values[0],)
        elif event in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.truncate"):
            paths = values[:1]
        elif event in ("os.rename", "os.link", "os.symlink"):
            paths = values[:2]
        for name in paths:
            need(Path(os.fsdecode(name)).resolve().is_relative_to(private), "private_write_only")
    def audit(event, values):
        try:
            checked_audit(event, values)
        except BaseException:
            loader.failed = True
            raise
    sys.addaudithook(audit)


def child(root, own_sha, request_path, request_sha, response_path):
    envelope = {"format": "installed-terminal-child-v1", "status": "NO_GO",
                "request_sha256": request_sha, "phase": "request", "reason": "request_invalid",
                "report": None, "full_chain_admission": False, "hosted_admitted": False}
    try:
        need(request_path.is_file() and request_path.stat().st_size <= MAX_REQUEST, "request_limit")
        raw = request_path.read_bytes()
        need(len(raw) <= MAX_REQUEST and sha(raw) == request_sha, "request_hash")
        request = decode(raw)
        need(set(request) == {"payloads", "case", "originals", "head", "candidate", "run", "sources"},
             "request_fields")
        sources = source_map(request["sources"])
        need(sources.get(SELF) == own_sha, "own_binding")
        root = root.resolve(strict=True)
        source(root, SELF, sources)
        payloads = blob_map(request["payloads"], 1100, 30_000_000, unpack=True)
        originals = blob_map(request["originals"], 4096, 16_000_000, unpack=True)
        identity = binding(request["case"], payloads, request["head"], request["candidate"], request["run"])
        envelope["phase"] = "bootstrap"
        raw = source(root, LOADER, sources)
        namespace = {"__name__": "_installed_loader_bootstrap", "__file__": str(root / LOADER)}
        exec(compile(raw, str(root / LOADER), "exec", dont_inherit=True), namespace)
        stdlib_bootstrap = namespace['bootstrap_reader_stdlib']()
        loader = namespace["TrustedImports"](root, sources)
        enable_legacy(loader)
        private = request_path.parent.resolve(strict=True)
        install_audit(loader, private)
        envelope["phase"] = "replay"
        with loader:
            reader = loader.module(READER)
            report = reader.verify_exported_terminal(payloads, request["case"], originals=originals,
                source_commit=request["head"], ci_run=request["run"], candidate_sha256=request["candidate"],
                expected_sources=sources, trusted_root=root)
            report['reader_stdlib'] = stdlib_bootstrap
            report_ok(report, identity)
        envelope.update(status="INSPECTED_UNVERIFIED", reason=None, report=report, phase="terminal")
    except BaseException as error:
        # Never export exception messages, paths, environment or raw child output.
        name = type(error).__name__
        if name == "TrustedImportError":
            reason = "unsupported_or_unbound_replay"
        elif isinstance(error, Blocked):
            reason = str(error) if str(error) in {
                "reader_claim", "report_limit", "legacy_cached_alias", "legacy_spec_shape",
                "legacy_origin", "legacy_alias_conflict", "legacy_python_source",
                "offline_action_denied", "private_write_only", "execution_not_exact_source"} else "input_or_source_invalid"
        else:
            reason = "reader_exception"
        envelope.update(status="NO_GO", reason=reason, report=None)
    try:
        save(response_path, envelope, MAX_RESPONSE)
        return 0
    except BaseException:
        return 2


def inspect_terminal(payloads, case, originals, *, head, candidate, run, expected_sources, trusted_root):
    """Same Main API; preloaded parent modules never enter the fresh child."""
    identity = binding(case, payloads, head, candidate, run)
    root = Path(trusted_root).absolute()
    need(plain(root), "root_origin")
    root = root.resolve(strict=True)
    sources = dict(source_map(expected_sources))
    for name in (SELF, LOADER, READER_PATH, PACKAGE):
        source(root, name, sources)
    need(Path(__file__).resolve(strict=True) == (root / SELF).resolve(strict=True), "helper_origin")
    request = {"payloads": blob_map(payloads, 1100, 30_000_000),
               "case": case, "originals": blob_map(originals, 4096, 16_000_000),
               "head": head, "candidate": candidate, "run": str(run), "sources": sources}
    raw = encode(request)
    need(len(raw) <= MAX_REQUEST, "request_limit")
    process = {"status": "NO_GO", "phase": "launch", "source_sha256": sources[SELF],
               "loader_sha256": sources[LOADER], "bootstrap_sha256": sha(BOOTSTRAP.encode()),
               "request_sha256": sha(raw), "source_commit": head, "ci_run": str(run),
               "candidate_sha256": candidate, "parent_cache_modified": False,
               "limits": {"input_bytes": MAX_REQUEST, "output_bytes": MAX_RESPONSE,
                          "wait_seconds": WAIT_SECONDS, "reap_seconds": REAP_SECONDS},
               "full_chain_admission": False, "hosted_admitted": False}
    result = no_go(identity, "terminal_child_incomplete")
    directory = tempfile.TemporaryDirectory(prefix="terminal-", ignore_cleanup_errors=True)
    cleanup_allowed = True
    try:
        private = Path(directory.name).resolve(strict=True)
        req, response = private / "rq.json", private / "rp.json"
        save(req, request, MAX_REQUEST)
        command = [sys.executable, "-I", "-S", "-B", "-c", BOOTSTRAP, str(root), sources[SELF],
                   str(req), process["request_sha256"], str(response)]
        environment = child_environment(private)
        # An exception during launch/wait cannot prove that no child is alive.
        cleanup_allowed = False
        waited = wait_child(command, environment, str(private))
        cleanup_allowed = waited.get("wait_completed") is True
        process["wait"] = waited
        need(waited["accepted"] is True, "child_wait_incomplete")
        process["phase"] = "response"
        need(response.is_file() and not response.is_symlink()
             and response.stat().st_size <= MAX_RESPONSE, "response_limit")
        raw = response.read_bytes()
        need(len(raw) <= MAX_RESPONSE, "response_limit")
        value = decode(raw)
        need(type(value) is dict and set(value) == {"format", "status", "request_sha256", "phase",
             "reason", "report", "full_chain_admission", "hosted_admitted"}
             and value["format"] == "installed-terminal-child-v1"
             and value["request_sha256"] == process["request_sha256"]
             and value["full_chain_admission"] is False and value["hosted_admitted"] is False,
             "response_binding")
        process.update(response_sha256=sha(raw), response_bytes=len(raw))
        if value["status"] == "INSPECTED_UNVERIFIED":
            need(value["phase"] == "terminal" and value["reason"] is None, "response_terminal")
            result = report_ok(value["report"], identity)
            process.update(status="INSPECTED_UNVERIFIED", phase="terminal")
        else:
            need(value["status"] == "NO_GO" and value["report"] is None, "response_status")
            need(value["phase"] in ("request", "bootstrap", "replay")
                 and value["reason"] in {"request_invalid", "unsupported_or_unbound_replay",
                 "reader_claim", "report_limit", "legacy_cached_alias", "legacy_spec_shape",
                 "legacy_origin", "legacy_alias_conflict", "legacy_python_source",
                 "offline_action_denied", "private_write_only", "execution_not_exact_source",
                 "input_or_source_invalid", "reader_exception"}, "response_reason")
            result = no_go(identity, value["reason"])
            process.update(phase=value["phase"], reason=value["reason"])
        # Reject changes to the entry sources during child execution.
        for name in (SELF, LOADER, READER_PATH, PACKAGE):
            source(root, name, sources)
    except BaseException as error:
        process["error_class"] = type(error).__name__
        process["status"] = "NO_GO"
        result = no_go(identity, "terminal_child_incomplete")
    finally:
        if not cleanup_allowed:
            # Detach weakref/atexit cleanup too: the child may still use originals.
            directory._finalizer.detach()
            process["private_cleanup"] = "deferred_unconfirmed_reap"
            process["retained_directory_id"] = Path(directory.name).name
            process["status"] = "NO_GO"
            result = no_go(identity, "terminal_child_reap_unconfirmed")
        else:
            try:
                directory.cleanup()
                need(not Path(directory.name).exists(), "private_cleanup_incomplete")
                process["private_cleanup"] = "completed"
            except BaseException:
                process["private_cleanup"] = "incomplete"
                process["status"] = "NO_GO"
                result = no_go(identity, "terminal_private_cleanup_incomplete")
    result["reader_process"] = process
    return result
