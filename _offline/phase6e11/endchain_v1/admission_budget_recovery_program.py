"""Finite probes of the actual D finally dispatcher; never a SQL execution.

Only hash-pinned selected functions run, with all external capabilities replaced
by recording boundaries. Explicit dispatch bounds and implicit connection costs
remain separate. These traces are a source derivation, not runtime evidence.
"""
import ast
import builtins
import copy
import contextlib
import hashlib
import itertools
import json
import pathlib
import re
from types import SimpleNamespace as NS

PINS = {
    "runtime_recovery.py": "44d315a22a782871f3c1cc4a825537814b80f266f1bfb114ccb0b14234d189a9",
    "runtime_worker_evidence.py": "57c4737921d87abc1bfe9cc62bfc67236359c79e0d66fdd109fae2f422bf6e5d",
    "control_recovery.py": "28489db090803bb1df868570c87a9f2a3dbc5c842fbbb81faa5ea837b55520eb",
}
CHANNELS = ("setup", "writer", "reader", "workflow")
WORKERS = ("live", "dead", "stuck", "wait_unknown", "wait_timeout", "kill_error", "pipe_error", "reaped", "nonzero")
WATCHDOGS = ("pending", "fired", "alive", "unknown", "join_error", "deadline")


class ProbeFailure(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise ValueError("recovery_program_" + code)


def _functions(path, names, namespace):
    raw = pathlib.Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PINS[pathlib.Path(path).name], "source_changed")
    tree = ast.parse(raw)
    found = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    require({node.name for node in found} == set(names), "function_missing")
    safe = {name: getattr(builtins, name) for name in (
        "dict", "list", "tuple", "bool", "len", "type", "getattr", "setattr", "any",
        "Exception", "BaseException", "RuntimeError", "ValueError", "int", "str", "min", "max", "property", "__build_class__")}
    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "json" and level == 0:
            return json
        if name == "runtime_http" and level == 1:
            return namespace["offline_http"]
        if name == "runtime_worker_evidence" and level == 1:
            return namespace["offline_worker"]
        raise ValueError("recovery_program_import_denied:" + name)
    safe["__import__"] = restricted_import
    namespace = dict(namespace, __builtins__=safe, __name__="offline_recovery_source_probe")
    exec(compile(ast.Module(body=found, type_ignores=[]), str(path), "exec"), namespace)
    return {name: namespace[name] for name in names}


class Boundary:
    def __init__(self, failure=None, edge="after"):
        self.events, self.failure, self.edge = [], failure, edge

    def call(self, kind, label, value=None):
        row = dict(kind=kind, label=label, attempted=False, returned=False)
        index = len(self.events)
        self.events.append(row)
        if index == self.failure and self.edge == "before":
            raise ProbeFailure("offline_before_boundary")
        row["attempted"] = True
        if index == self.failure:
            raise ProbeFailure("offline_lost_response")
        row["returned"] = True
        return value


class Connection:
    def __init__(self, probe, name, state):
        self.probe, self.name, self.state = probe, name, state

    @property
    def info(self):
        self.probe.call("validation", self.name + ":transaction_status")
        if self.state == "unreadable":
            raise ProbeFailure("offline_transaction_status_unknown")
        return NS(transaction_status=0 if self.state == "idle" else 2)

    def close(self):
        self.probe.call("connection_close", self.name)


class Process:
    def __init__(self, probe, state):
        self.probe, self.state = probe, state

    def poll(self):
        return self.probe.call("process", "poll", 0 if self.state == "dead" else None)

    def kill(self):
        self.probe.call("process", "kill")
        if self.state != "stuck":
            self.state = "dead"

    def communicate(self, *, timeout):
        self.probe.call("process", "communicate")


class ObservedProcess:
    """Recording boundary for the pinned WaitEvidence, never an OS process."""
    def __init__(self, probe, state):
        self.probe, self.state, self.pid = probe, state, 1
        self.returncode = 7 if state == "nonzero" else 0 if state in ("dead", "reaped") else None
        self.timeout_used = False
        for name in ("stdin", "stdout", "stderr"):
            setattr(self, name, NS(close=lambda name=name: self.close_pipe(name)))

    def close_pipe(self, name):
        self.probe.call("process", "pipe_close:" + name)
        if self.state == "pipe_error" and name == "stdout":
            raise ProbeFailure("offline_pipe_close")

    def poll(self):
        return self.probe.call("process", "poll", self.returncode)

    def kill(self):
        self.probe.call("process", "kill")
        if self.state == "kill_error":
            raise ProbeFailure("offline_kill")
        if self.state != "stuck":
            self.returncode = -9

    def wait(self, *, timeout):
        require(timeout == 5, "wait_timeout_changed")
        self.probe.call("process", "wait:5")
        if self.state == "wait_timeout" and not self.timeout_used:
            self.timeout_used = True
            raise ProbeFailure("offline_wait_timeout")
        if self.state == "wait_unknown":
            return None
        if self.returncode is None:
            raise ProbeFailure("offline_not_reaped")
        return self.returncode


class ObservedTimer:
    def __init__(self, probe, state):
        self.probe, self.state = probe, state

    def start(self):
        self.probe.call("process", "timer_start")

    def cancel(self):
        self.probe.call("process", "timer_cancel")

    def join(self, *, timeout):
        require(0 <= timeout <= 5, "watchdog_join_bound")
        self.probe.call("process", "timer_join:" + str(timeout))
        if self.state == "join_error":
            raise ProbeFailure("offline_timer_join")

    def is_alive(self):
        return self.probe.call("process", "timer_is_alive",
                               None if self.state == "unknown" else self.state == "alive")


class RecordedFilesystem:
    """In-memory capabilities for the pinned save(); no filesystem is accessed."""
    def __init__(self, probe):
        self.probe, self.raw, self.opened = probe, b"", False
        self.root = self.Path(self, False)

    def call(self, operation, value=None):
        return self.probe.call("filesystem", "workflow-worker-wait.json:" + operation, value)

    class Path:
        def __init__(self, owner, member):
            self.owner, self.member = owner, member

        def __truediv__(self, name):
            require(name == "workflow-worker-wait.json", "worker_save_name")
            return type(self)(self.owner, True)

        @property
        def parent(self):
            return self.owner.root

        def resolve(self, *, strict):
            require(strict is True, "resolve_strict")
            return self.owner.call("member_resolve" if self.member else "root_resolve", self)

        def exists(self):
            return self.owner.call("exists", False)

        def stat(self, *, follow_symlinks):
            require(follow_symlinks is False, "nofollow_stat")
            return self.owner.call("named_stat", self.owner.identity())

        def is_symlink(self):
            return self.owner.call("is_symlink", False)

    def identity(self):
        return NS(st_mode=1, st_dev=1, st_ino=1, st_size=len(self.raw))

    def open(self, path, flags, mode):
        require(path.member and mode == 0o600, "exclusive_open")
        self.call("exclusive_open")
        self.opened = True
        return 1

    def fdopen(self, fd, mode):
        require(fd == 1 and mode == "w+b" and self.opened, "fdopen")
        return self.call("fdopen", self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.call("close")

    def write(self, raw):
        self.raw = raw
        return self.call("write", len(raw))

    def flush(self):
        self.call("flush")

    def fileno(self):
        return 1

    def seek(self, offset):
        require(offset == 0, "seek_offset")
        self.call("seek")

    def read(self, size):
        require(size == len(self.raw) + 1, "readback_size")
        return self.call("readback", self.raw)

    def canonical(self, value):
        return self.call("canonicalize", json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

    def capabilities(self):
        return dict(pathlib=NS(Path=lambda out: self.root), re=re, require=require,
            canonical=self.canonical, sha=lambda raw: hashlib.sha256(raw).hexdigest(),
            stat=NS(S_ISREG=lambda mode: mode == 1),
            os=NS(O_RDWR=1, O_CREAT=2, O_EXCL=4, O_BINARY=8, O_NOFOLLOW=16,
                  open=self.open, fdopen=self.fdopen,
                  fsync=lambda fd: self.call("fsync"), fstat=lambda fd: self.call("fstat", self.identity())))


class RecoveryProgram:
    def __init__(self, source_root, runtime_dir):
        base = pathlib.Path(source_root) / "_offline/phase6e11/endchain_v1"
        control = base / "control_recovery.py"
        tree = ast.parse(control.read_bytes())
        constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("CLOSED", "CONTROL_SQL"):
                        constants[target.id] = ast.literal_eval(node.value)
        self.closed = constants["CLOSED"]
        functions = _functions(control, ("replace_setup", "recover"),
                               dict(constants, hashlib=hashlib))
        self._http_boundary = None
        self._save_boundary = None
        http = NS(workflow_receipt=lambda *a, **kw: self._http_boundary())
        worker = NS(save=lambda *a, **kw: self._save_boundary(*a, **kw))
        self.WaitEvidence = _functions(pathlib.Path(runtime_dir) / "runtime_worker_evidence.py", ("WaitEvidence",),
            dict(require=require, copy=copy, threading=NS(Lock=contextlib.nullcontext),
                 time=NS(monotonic=lambda: 0)))["WaitEvidence"]
        self.worker_source = pathlib.Path(runtime_dir) / "runtime_worker_evidence.py"
        self.filesystem = RecordedFilesystem(None)
        self.save_original = _functions(self.worker_source, ("save",), self.filesystem.capabilities())["save"]
        self.finish = _functions(pathlib.Path(runtime_dir) / "runtime_recovery.py", ("finish",),
            dict(functions, CHANNELS=CHANNELS, time=NS(monotonic=lambda: 0),
                 offline_http=http, offline_worker=worker))["finish"]

    def trace(self, *, states=("active",)*4, controls=True, worker="live",
              failure=None, edge="after", foreign_controls=False, watchdog="pending", worker_evidence=True,
              primary_failure=True):
        require(type(primary_failure) is bool, "primary_failure")
        require(len(states) == 4 and all(s in ("absent", "idle", "active", "unreadable") for s in states), "states")
        require(worker in ("absent", *WORKERS), "worker")
        require(watchdog in WATCHDOGS or worker == "absent" and watchdog == "none", "watchdog")
        p = Boundary(None, edge)
        observed, process, timer, prefix_events = None, None, None, []
        if worker_evidence:
            observed = self.WaitEvidence({"offline_simulation_only": True}, "offline_probe", "workflow")
            if worker != "absent":
                process = ObservedProcess(p, worker)
                observed.attach(process)
                timer = ObservedTimer(p, watchdog)
                observed.start_timer(timer, deadline=0 if watchdog == "deadline" else 125)
                if watchdog == "fired":
                    observed.kill(watchdog=True)
                if worker in ("wait_unknown", "wait_timeout", "reaped", "nonzero"):
                    try: observed.wait()
                    except Exception: pass  # The actual WaitEvidence latches this failed prefix.
            prefix_events, p.events = p.events, []
        else:
            require(worker in ("absent", "dead", "live", "stuck"), "legacy_worker")
            process = None if worker == "absent" else Process(p, worker)
            timer = NS(cancel=lambda: p.call("process", "timer_cancel"))
        p.failure = failure
        connections = {name: Connection(p, name, state) for name, state in zip(CHANNELS, states)
                       if state != "absent"}
        composition = NS(commands=[], events=[], started=0, fault=None, injected=False,
            safety_label=None, workflow_dispatch=object(),
            meter=NS(setup_connection_owned="setup" in connections,
                     confirm_controls_restored=lambda: p.call("validation", "controls_confirmed")),
            abort=lambda reason: p.call("validation", "abort:" + reason))
        original = copy.deepcopy(self.closed)
        expected = dict(config=dict(id=True, enabled=True, proof_hash="offline-proof"),
                        request=dict(id=True, enabled=True, expires_at="offline-expiry"))
        def query(channel, phase, sql, args=()):
            row = dict(channel=channel, phase=phase, confirmed=False,
                       sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),
                       safety_label=composition.safety_label)
            composition.commands.append(row)
            p.call("sql", channel + ":" + phase)
            row["confirmed"] = True
            value = expected if phase == "safety_control_before" else original
            if foreign_controls and phase == "safety_control_before":
                value = dict(config={"not_owned": True}, request={"not_owned": True})
            return [dict(value=copy.deepcopy(value))]
        def connect():
            p.call("connection_open", "replacement_setup")
            return Connection(p, "replacement_setup", "idle")
        gate = NS(out="offline-only", save=lambda name, value: p.call("filesystem", name))
        saved_wait = None
        self.filesystem.probe, self.filesystem.raw, self.filesystem.opened = p, b"", False
        def save_original(gate, name, value):
            nonlocal saved_wait
            reference = self.save_original(gate, name, value)
            saved_wait = copy.deepcopy(value)
            return reference
        self._save_boundary = save_original
        self._http_boundary = lambda: p.call("validation", "workflow_http_terminal", {})
        original_error = ProbeFailure("offline_original_failure") if primary_failure else None
        escaped_error = None
        outcome = None
        try:
            outcome = self.finish(composition, gate, NS(connect=connect), connections, query, query,
                process=process, timer=timer, worker_evidence=observed,
                enable_attempted=controls, original=original,
                enabled=expected if controls else None, restored=None, primary=original_error)
        except Exception as error:
            escaped_error = error
            outcome = getattr(composition, "workflow_recovery", dict(probe_exception=type(error).__name__))
        return dict(states=list(states), controls=controls, worker=worker, watchdog=watchdog,
            worker_evidence_branch=worker_evidence, worker_prefix_events=prefix_events,
            worker_wait=observed.receipt() if observed is not None else None,
            worker_known=observed.known if observed is not None else None,
            saved_worker_wait=saved_wait, primary_failure=primary_failure,
            raised_exception_class=type(escaped_error).__name__ if escaped_error is not None else None,
            original_failure_preserved=(escaped_error is None or escaped_error is original_error)
                if original_error is not None else None,
            foreign_controls=foreign_controls, failure=failure, edge=edge,
            events=p.events, commands=composition.commands, outcome=outcome,
            explicit_sql_slots=len(composition.commands),
            connection_open_attempts=sum(e["kind"] == "connection_open" for e in p.events),
            connection_close_attempts=sum(e["kind"] == "connection_close" for e in p.events),
            process_calls=sum(e["kind"] == "process" for e in p.events),
            worker_prefix_process_calls=sum(e["kind"] == "process" for e in prefix_events),
            total_process_calls=sum(e["kind"] == "process" for e in (*prefix_events, *p.events)),
            filesystem_calls=sum(e["kind"] == "filesystem" for e in p.events),
            durable_save_model="source_pinned_filesystem_boundaries_not_actual_durability",
            actual_execution_evidence=False)

    def enumerate(self):
        """Finite connection/worker/watchdog states and each recovery fault edge.

        Single-failure probes establish branch reachability, not simultaneous
        transport success. The per-channel loop and straight-line four-control
        program provide the independent at-most-once syntactic ceiling.
        """
        traces, summaries = 0, {}
        maximum = dict(explicit_sql_slots=0, connection_open_attempts=0,
                       connection_close_attempts=0, process_calls=0,
                       worker_prefix_process_calls=0, total_process_calls=0, filesystem_calls=0)
        def consume(trace):
            nonlocal traces
            traces += 1
            for key in maximum:
                maximum[key] = max(maximum[key], trace[key])
            shape = {key: trace[key] for key in maximum}
            shape["sql_order"] = [(c["channel"], c["phase"], c["sql_sha256"], c["safety_label"])
                                  for c in trace["commands"]]
            key = hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()
            summaries.setdefault(key, shape)
        profiles = [("absent", "none"), *itertools.product(WORKERS, WATCHDOGS)]
        for states in itertools.product(("absent", "idle", "active", "unreadable"), repeat=4):
            for controls, (worker, watchdog), primary in itertools.product((False, True), profiles, (False, True)):
                consume(self.trace(states=states, controls=controls, worker=worker, watchdog=watchdog,
                                   primary_failure=primary))
        base_states = traces
        for controls, (worker, watchdog), foreign, primary in itertools.product(
                (False, True), profiles, (False, True), (False, True)):
            normal = self.trace(controls=controls, worker=worker, watchdog=watchdog,
                                foreign_controls=foreign, primary_failure=primary)
            consume(normal)
            for index in range(len(normal["events"])):
                for edge in ("before", "after"):
                    consume(self.trace(controls=controls, worker=worker, watchdog=watchdog, foreign_controls=foreign,
                                       failure=index, edge=edge, primary_failure=primary))
        require(maximum["explicit_sql_slots"] == 8, "explicit_bound_changed")
        require(maximum["connection_open_attempts"] == 1 and maximum["connection_close_attempts"] == 5,
                "connection_bound_changed")
        return dict(format="actual-workflow-recovery-source-program-v1", source_hashes=dict(PINS),
            base_states=base_states, worker_watchdog_profiles=len(profiles), traces=traces, unique_shapes=len(summaries),
            actual_worker_evidence_branch=True, worker_prefix_process_calls_separately_visible=True,
            maxima=maximum, shapes=list(summaries.values()),
            covered_by="case.core", additional_parent_charge=False,
            rollback_slots={channel: 1 for channel in CHANNELS}, compare_restore_slots=4,
            native_explicit_bound_complete=True, full_sql_upper_bound=None,
            unresolved=["replacement_connection_implicit_sql", "close_connection_implicit_sql",
                        "caller_prefix_shared_allowance_composition"],
            actual_execution_evidence=False, hosted_admitted=False)
