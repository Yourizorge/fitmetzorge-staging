"""Offline control-flow probes of pinned recovery sources; never SQL evidence.

Only selected functions execute, with transport/validation boundaries replaced by
finite probes. These enumerate local suffixes, not the still-unjoined lifecycle.
"""
import ast
import copy
import hashlib
import itertools
import json
import pathlib
from types import SimpleNamespace as NS

from admission_budget import HERE, require

PINS = {
    "safety_auth_native.py": "2ef9dc3c10a6ca3ad7c1070026e9e025e3772f92866c140b36e76e2de274c6e4",
    "registered_lifecycle.py": "5474bfbc4c99b4f25fbb80d3f68eb4a2005ae1786cbc1d2a9bf6c699fe90a3d8",
    "control_recovery.py": "28489db090803bb1df868570c87a9f2a3dbc5c842fbbb81faa5ea837b55520eb",
    "runtime_recovery.py": "84121ebea00868a824b378357c0ea8e5f4f2ac2c10da1ebf550c7139fc68cca5",
}


def _function(path, name, namespace):
    raw = pathlib.Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == PINS[pathlib.Path(path).name], "recovery_source_version_changed")
    tree = ast.parse(raw.decode("utf-8"))
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(found) == 1, "recovery_function_identity")
    function = found[0]
    require(not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(function)),
            "recovery_probe_import")
    builtins = {k: v for k, v in dict(ValueError=ValueError, RuntimeError=RuntimeError,
        Exception=Exception, type=type, len=len, getattr=getattr, setattr=setattr,
        any=any, bool=bool, dict=dict, list=list).items()}
    namespace = dict(namespace, __builtins__=builtins)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name], dict(file=pathlib.Path(path).name, method=name, sha256=digest)


class Probe:
    """A call attempt is not a confirmed command, even in the offline model."""
    def __init__(self, failure=None, failure_edge="after"):
        self.events = []
        self.failure = failure
        self.failure_edge = failure_edge

    def call(self, kind, label, value=None, commands=0):
        event = dict(index=len(self.events), kind=kind, label=label,
                     protocol_commands=commands, outcome="returned",
                     simulated_dispatch=False, numeric_confirmation=False)
        self.events.append(event)
        fail = event["index"] == self.failure
        if fail and self.failure_edge == "before":
            event["outcome"] = "before_send" if commands else "raised"
            raise ValueError("offline_probe_boundary")
        event["simulated_dispatch"] = commands > 0
        if fail:
            event["outcome"] = "lost_response" if commands else "raised"
            raise ValueError("offline_probe_boundary")
        return value

    def result(self, **extra):
        return dict(events=self.events,
            sql_call_commands=sum(e["protocol_commands"] for e in self.events),
            simulated_dispatched_commands=sum(e["protocol_commands"] for e in self.events
                                              if e["simulated_dispatch"]),
            numeric_confirmed_commands=0, actual_execution_evidence=False, **extra)


def native_trace(*, mint_terminal=True, failure=None, failure_edge="after", source_dir=HERE):
    p = Probe(failure, failure_edge)
    snapshot = dict(rows=[], events=[], io={})
    def boundary(name, result=None):
        return lambda *a, **k: p.call("validation", name, copy.deepcopy(result))
    bindings = NS(observe=boundary("utility.observe", {"queryid": 2}),
                  confirm=boundary("utility.confirm"))
    def sql(value):
        result = ([{"Execution Time": 0}] if value.startswith("EXPLAIN (ANALYZE")
                  else {} if value.startswith("EXPLAIN") else snapshot)
        return p.call("sql", value, json.dumps(result), 1)
    namespace = dict(json=json, check_plan=boundary("check_plan", 1),
        read_sql=boundary("read_sql", "SELECT offline_probe"),
        validate_snapshot=boundary("validate_snapshot"), UtilityBindings=lambda: bindings,
        sha=lambda value: hashlib.sha256(value.encode()).hexdigest(),
        delta=boundary("delta", {}),
        revoke_sql=boundary("revoke_sql", ("DO offline_probe", set())),
        validate_deletes=boundary("validate_deletes"))
    function, source = _function(pathlib.Path(source_dir) / "safety_auth_native.py", "native_suffix", namespace)
    result = function(NS(run_id="offline-control-flow-only", sql=sql),
                      lambda name, value: p.call("save", name), {}, mint_terminal)
    return p.result(simulated_result=result, source=source, mint_terminal=mint_terminal)


def native_prefixes(*, source_dir=HERE):
    traces = []
    for terminal in (False, True):
        normal = native_trace(mint_terminal=terminal, source_dir=source_dir)
        traces.append(normal)
        for event in normal["events"]:
            for edge in (("before", "after") if event["kind"] == "sql" else ("after",)):
                traces.append(native_trace(mint_terminal=terminal, failure=event["index"],
                    failure_edge=edge, source_dir=source_dir))
    return dict(component="native_auth_suffix", traces=traces,
                max_sql_call_commands=max(t["sql_call_commands"] for t in traces),
                configured_reservation_unchanged=12, full_bound=False)


def removal_trace(states, *, failure=None, failure_edge="after", source_dir=HERE):
    """States: not_installed, attempted, receipt, inspected, absent, unowned."""
    require(set(states) == {"audit", "guard"} and all(v in
        ("not_installed", "attempted", "receipt", "inspected", "absent", "unowned")
        for v in states.values()), "removal_probe_state")
    from admission_budget_register import current_removal_rows
    rows = current_removal_rows()
    sizes = {name: sum(r["owner"] == ("observer" if name == "audit" else name)
                      for r in rows) for name in states}
    require(all(size == 5 for size in sizes.values()), "removal_probe_batch_shape")
    p = Probe(failure, failure_edge)
    def module(name):
        def validate(*args, **kwargs):
            p.call("validation", name + ".validate")
            if states[name] in ("absent", "unowned"):
                raise ValueError("offline_unvalidated_receipt")
            return {"offline_receipt": name}
        return NS(inspect=lambda *a: "inspect:" + name, validate=validate,
                  scope=lambda *a: "offline_" + name, remove=lambda *a: "remove:" + name)
    def sql(value):
        if value.startswith("remove:"):
            return p.call("sql_batch", value, "", sizes[value.split(":")[1]])
        if value.startswith("inspect:"):
            return p.call("sql", value, "{}", 1)
        name = "audit" if "offline_audit" in value else "guard"
        return p.call("sql", "absent:" + name, "true" if states[name] == "absent" else "false", 1)
    owner = NS(worker_owned=False, failed=True, composition=NS(),
        audit=module("audit"), guard=module("guard"), expiry=None,
        run_id="offline-control-flow-only", ids={}, sql=sql,
        metadata_receipt={} if states["audit"] == "receipt" else None,
        receipt={} if states["guard"] == "receipt" else None,
        install_attempted={n: v != "not_installed" for n, v in states.items()},
        removal_attempted={n: v == "attempted" for n, v in states.items()},
        gate=NS(save=lambda name, value: p.call("save", name)))
    function, source = _function(pathlib.Path(source_dir) / "registered_lifecycle.py",
                                 "close_temporary", dict(json=json))
    error = None
    try: function(owner)
    except ValueError as exc: error = type(exc).__name__
    before_replay = len(p.events)
    try: function(owner)
    except ValueError: pass
    require(not any(e["protocol_commands"] for e in p.events[before_replay:]), "removal_replayed")
    return p.result(source=source, states=dict(states), error=error,
                    removal_attempted=owner.removal_attempted, removed=owner.removed,
                    replay_sql_commands=0,
                    batch_source_hashes={r["source"]["path"]: r["source"]["sha256"] for r in rows},
                    batch_templates=[dict(owner=r["owner"], index=r["statement_index"],
                        template_sha256=r["template_sha256"], binding_required=r["binding_required"],
                        binding_inputs=r["binding_inputs"]) for r in rows])


def removal_prefixes(*, source_dir=HERE):
    states = ("not_installed", "attempted", "receipt", "inspected", "absent", "unowned")
    traces = []
    for pair in itertools.product(states, repeat=2):
        state = dict(zip(("audit", "guard"), pair))
        normal = removal_trace(state, source_dir=source_dir)
        traces.append(normal)
        for event in normal["events"]:
            for edge in (("before", "after") if event["protocol_commands"] else ("after",)):
                traces.append(removal_trace(state, failure=event["index"], failure_edge=edge,
                                            source_dir=source_dir))
    return dict(component="temporary_removal", traces=traces,
                max_sql_call_commands=max(t["sql_call_commands"] for t in traces),
                batch_interior_dispatch_requires_meter_join=True, full_bound=False)


def workflow_trace(transaction_states, *, controls_required=True, worker_reaped=True,
                   failure=None, failure_edge="after", runtime_dir, source_dir=HERE):
    """Execute D's actual finally and its actual four-command restore helper."""
    channels = ("setup", "writer", "reader", "workflow")
    require(set(transaction_states) == set(channels) and all(type(v) is bool for v in
            transaction_states.values()), "recovery_transaction_states")
    p = Probe(failure, failure_edge)
    original = {"config": {}, "request": {}}
    expected = {"config": {"proof_hash": "offline"}, "request": {"expires_at": "offline"}}
    c = NS(commands=[], events=[], started=0, fault=None, injected=False,
           abort=lambda reason: None, meter=NS(confirm_controls_restored=lambda: None))
    def query(channel, phase, sql, *args):
        value = p.call("sql", phase + ":" + channel, [{"value": original}], 1)
        c.commands.append(dict(phase=phase, confirmed=True))
        return value
    recover, recovery_source = _function(pathlib.Path(source_dir) / "control_recovery.py", "recover",
        dict(CONTROL_SQL="SELECT offline_control", CLOSED=original, hashlib=hashlib,
             __import__=lambda name: json if name == "json" else None))
    def connection(active=False):
        return NS(info=NS(transaction_status=int(active)), close=lambda: None)
    connections = {n: connection(transaction_states[n]) for n in channels}
    replace, replace_source = _function(pathlib.Path(source_dir) / "control_recovery.py", "replace_setup", {})
    function, source = _function(pathlib.Path(runtime_dir) / "runtime_recovery.py", "finish",
        dict(CHANNELS=channels, recover=recover, replace_setup=replace, time=NS(monotonic=lambda: 0)))
    process = NS(poll=lambda: 0 if worker_reaped else None, kill=lambda: None,
                 communicate=lambda **k: None)
    result = function(c, NS(save=lambda name, value: p.call("save", name)),
        NS(connect=lambda: connection()), connections, query, query, process=process,
        timer=None, enable_attempted=controls_required, original=original, enabled=expected,
        restored=None, primary=ValueError("offline_parent_failure"))
    return p.result(simulated_result=result, source=source, dependencies=[recovery_source, replace_source],
                    transaction_states=dict(transaction_states), controls_required=controls_required,
                    worker_reaped=worker_reaped)


def workflow_prefixes(*, runtime_dir, source_dir=HERE):
    traces = []
    for flags in itertools.product((False, True), repeat=6):
        kwargs = dict(transaction_states=dict(zip(("setup", "writer", "reader", "workflow"), flags[:4])),
                      controls_required=flags[4], worker_reaped=flags[5], runtime_dir=runtime_dir,
                      source_dir=source_dir)
        normal = workflow_trace(**kwargs)
        traces.append(normal)
        for event in normal["events"]:
            for edge in (("before", "after") if event["protocol_commands"] else ("after",)):
                traces.append(workflow_trace(**kwargs, failure=event["index"], failure_edge=edge))
    return dict(component="workflow_parent_finally", traces=traces,
                max_sql_call_commands=max(t["sql_call_commands"] for t in traces), full_bound=False)


def derive_recovery_components(*, runtime_dir, source_dir=HERE):
    components = [native_prefixes(source_dir=source_dir), removal_prefixes(source_dir=source_dir),
                  workflow_prefixes(runtime_dir=runtime_dir, source_dir=source_dir)]
    sources = dict(PINS)
    sources.update(components[1]["traces"][0]["batch_source_hashes"])
    return dict(format="source-recovery-control-flow-v1", components=components,
        source_hashes=sources, full_bound=False, minimal_cap=None, hosted_admitted=False,
        actual_execution_evidence=False, cap_unchanged=2349, historical_normal_unchanged=2338,
        pending=["outer_lifecycle_exception_composition", "controller_after_measure_and_queryio",
                 "actual_meter_admission_each_suffix_command", "dynamic_sql_template_binding",
                 "bootstrap_and_auth_context_entry"])
