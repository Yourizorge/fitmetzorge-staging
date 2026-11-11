"""Concrete twelve case positions and two separate pre-Auth bootstrap hooks."""
import ast
import copy
import hashlib
import pathlib

from admission_budget import require
from admission_budget_current_order import _source, _method
from admission_budget_register import canonical_sha

BOOTSTRAP = ("pre_migration", "post_migration")


def source_selectors(scenario, *, runtime_dir):
    """Evaluate only D's bounded, pure selector function, never its runtime."""
    path = pathlib.Path(runtime_dir) / "runtime_faults.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "selectors")
    for node in ast.walk(function):
        require(not isinstance(node, (ast.Import, ast.ImportFrom, ast.While, ast.With, ast.Try)),
                "fault_selector_nonlocal_operation")
        if isinstance(node, ast.Call):
            require(isinstance(node.func, ast.Name) and node.func.id in
                    ("require", "len", "list", "range", "bool", "first", "predicate"), "fault_selector_call_changed")
    namespace = {"__builtins__": {"len": len, "list": list, "range": range, "bool": bool}, "require": require}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["selectors"](copy.deepcopy(scenario))


def bootstrap_closeout_contract(*, runtime_dir):
    """All four actual SQL calls plus Docker inventory, never a fake Auth id."""
    path = pathlib.Path(runtime_dir) / "runtime_bootstrap_closeout.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = {}
    def literal(node):
        if isinstance(node, ast.Name):
            require(node.id in constants, "bootstrap_unknown_constant")
            return constants[node.id]
        if isinstance(node, ast.Tuple):
            return tuple(literal(item) for item in node.elts)
        return ast.literal_eval(node)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("IDENTITY", "ACCOUNTS", "COMMANDS", "SCOPE"):
                constants[name] = literal(node.value)
    commands = constants["COMMANDS"]
    from sql_protocol import statements
    require(len(commands) == 4 and all(len(statements(sql)) == 1 for sql in commands)
            and commands[0] == "BEGIN TRANSACTION READ ONLY" and commands[-1] == "ROLLBACK",
            "bootstrap_closeout_command_shape")
    collect = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "collect")
    calls = [n for n in ast.walk(collect) if isinstance(n, ast.Call)]
    query_calls = [ast.literal_eval(n.args[0]) for n in calls
                   if isinstance(n.func, ast.Name) and n.func.id == "query"]
    inventory = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "command"]
    require(sorted(query_calls) == [0, 1, 2, 3] and len(inventory) == 1, "bootstrap_closeout_dispatch_changed")
    binding = _method("quota_candidate_v1/runtime_bootstrap_closeout.py", "collect", runtime_dir)
    return dict(scope=constants["SCOPE"], binding=binding, reserved_sql_commands=4,
        commands=[dict(index=i, sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),
                       protocol_commands=1, finally_command=i == 3) for i, sql in enumerate(commands)],
        docker_inventory_calls=1, case_meter_commands=0,
        auth_state="not_started", auth_container=None, auth_database_bound=False,
        requires_actual_negative_container_inventory=True, requires_actual_zero_account_witness=True,
        receipt_is_execution_evidence=False, hosted_admitted=False)


def hook_bindings(plan, scenario, *, runtime_dir):
    selectors = source_selectors(scenario, runtime_dir=runtime_dir)
    rows = plan["normal"]["rows"]
    faults = _source("quota_candidate_v1/runtime_faults.py", runtime_dir)
    bindings = {}
    for case, selector in selectors.items():
        if case == "normal":
            continue
        item = dict(case=case, selector=selector, **faults, hook_sql_commands=0)
        stage = selector["stage"]
        if case in BOOTSTRAP:
            require(selector == dict(stage="before45" if case == "pre_migration" else "after45",
                                     history_count=44 if case == "pre_migration" else 45),
                    "bootstrap_hook_relabelled")
            item.update(scope="canonical_bootstrap_before_auth", outside_case_limit=True,
                        case_event_id=None, closeout=bootstrap_closeout_contract(runtime_dir=runtime_dir))
        elif stage == "auth_confirmed":
            item.update(after_event="validate:auth:" + selector["role"] + ":" + selector["operation"])
        elif stage == "controller_before":
            require(selector["controller_step"] == 2 and selector["pair_phase"] == "pair_validated",
                    "controller_hook_contract_changed")
            hits = [r for r in rows if r["action"] == "evidence_query" and
                    r.get("action_binding") == dict(kind="auth", role="a_member", operation="getUser")]
            require(len(hits) == 5, "controller_hook_query_shape")
            item.update(before_event="precharge:" + hits[-1]["charge_group"])
        elif stage in ("native_after", "native_timeout"):
            hits = [r for r in rows if r["action"] == selector["phase"] and
                    r.get("action_binding") == dict(kind="workflow", step=selector["step"])]
            require(len(hits) == 1 and selector["channel"] == "workflow", "native_hook_query_shape:" + case)
            if stage == "native_timeout":
                item.update(case_event_id=hits[0]["id"], outcome="timeout",
                            replacement_not_additional=True, replacement_protocol_commands=1)
            else:
                item.update(after_event=hits[0]["id"])
        elif stage == "pair_confirmed":
            hits = [r for r in rows if r.get("action_binding") == dict(kind="workflow", step=selector["step"])]
            require(hits[-1]["action"] == "io_sample", "pair_hook_after_checkpoint")
            item.update(after_event=hits[-1]["id"])
        elif stage == "outer_before":
            hits = [r for r in rows if r["action"] == selector["phase"]]
            require(bool(hits), "outer_before_hook_missing")
            item.update(before_event="precharge:" + hits[0]["charge_group"])
        elif stage == "outer_after":
            hits = [r for r in rows if r["action"] == selector["phase"]]
            require(len(hits) == 1, "outer_after_hook_shape")
            item.update(after_event=hits[0]["id"])
        else:
            require(False, "unsupported_actual_hook:" + stage)
        if case not in BOOTSTRAP:
            item.update(scope="disposable_case", outside_case_limit=False)
        bindings[case] = item
    require(len(bindings) == 14, "actual_hook_inventory")
    return dict(bindings=bindings, scenario_sha256=canonical_sha(scenario),
                source_binding=faults, full_chain_admission=False)


def attach_case_hooks(contract, plan, scenario, *, runtime_dir):
    """Place zero-SQL hooks at real boundaries, leaving stop edges for recovery."""
    value = copy.deepcopy(contract)
    inventory = hook_bindings(plan, scenario, runtime_dir=runtime_dir)
    before, after = {}, {}
    cases = {}
    original_ids = {e["event_id"] for e in value["events"]}
    for case, binding in inventory["bindings"].items():
        if case in BOOTSTRAP:
            continue
        if case == "timeout":
            require(binding["case_event_id"] in original_ids, "timeout_event_missing")
            cases[case] = dict(binding, event_id=binding["case_event_id"], hook_case=case)
            continue
        key = "before_event" if "before_event" in binding else "after_event"
        require(binding[key] in original_ids, "hook_anchor_missing:" + case)
        selected = before if key == "before_event" else after
        require(binding[key] not in selected, "hook_boundary_collision")
        selected[binding[key]] = case
        cases[case] = dict(binding, event_id="hook:" + case, outcome="injected", hook_case=case)
    events = []
    def hook(case, anchor, state):
        spec = inventory["bindings"][case]
        return dict(event_id="hook:" + case, stage="checkpoint", event_kind="local_reservation_checkpoint",
            phase=anchor["phase"], cost=0, capacity_use=0, selector=copy.deepcopy(spec["selector"]),
            source=spec["source"], source_sha256=spec["source_sha256"], method="PhaseFaults._fire",
            state_before=copy.deepcopy(state), state_after={}, outcomes=["confirmed", "injected"], next={})
    for event in value["events"]:
        ident = event["event_id"]
        if ident in before:
            events.append(hook(before[ident], event, event["state_before"]))
        events.append(event)
        if ident in after:
            state = dict(event["state_before"], **event.get("state_after", {}))
            state.update(event.get("state_after_by_outcome", {}).get("confirmed", {}))
            events.append(hook(after[ident], event, state))
    for index, event in enumerate(events):
        event["next"]["confirmed"] = events[index + 1]["event_id"] if index + 1 < len(events) else "normal_complete"
    value.update(events=events, normal_event_ids=[e["event_id"] for e in events], fault_cases=cases,
        bootstrap_fault_cases={k: inventory["bindings"][k] for k in BOOTSTRAP}, hook_inventory=inventory)
    for spec in inventory["bindings"].values():
        value["source_hashes"][spec["source"]] = spec["source_sha256"]
        if "closeout" in spec:
            binding = spec["closeout"]["binding"]
            value["source_hashes"][binding["source"]] = binding["source_sha256"]
    return value
