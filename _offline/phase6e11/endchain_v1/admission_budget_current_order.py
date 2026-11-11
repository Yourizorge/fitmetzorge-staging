"""Offline source-order joins for the opt-in disposable executor.

The retained register supplies identities, not observations. Managed tickets
are not HTTP calls, and the bounded stream path is not an observed page count.
No runtime module is imported and no connection or subprocess is opened.
"""
import ast
import collections
import copy
import functools
import hashlib
import pathlib
import types

from admission_budget import HERE, OUTCOMES, require
from admission_budget_register import canonical_sha, normal_events

PREFIX = "_offline/phase6e11/endchain_v1/"
ROLES = ("a_member", "a_trainer", "b_member")
AUTH = dict(issue=11, verify=21, getUser=5, refresh=27, logout=10, revoked_denial=4)


def _source(name, runtime_dir):
    root = pathlib.Path(runtime_dir) if name.startswith("quota_candidate_v1/") else HERE
    relative = name.removeprefix("quota_candidate_v1/") if name.startswith("quota_candidate_v1/") else name
    path = root / relative
    raw = path.read_bytes()
    return dict(source=PREFIX + name, source_sha256=hashlib.sha256(raw).hexdigest())


def _method(name, method, runtime_dir):
    value = _source(name, runtime_dir)
    if name.endswith(".py"):
        path = pathlib.Path(runtime_dir) / name.split("/", 1)[1] if name.startswith("quota_candidate_v1/") else HERE / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        require(method.split(".")[-1] in names, "current_dispatch_method_missing:" + method)
    return dict(value, method=method)


def auth_dispatch_requirements(plan):
    """Join each real Auth act to the controller/identity-lock native boundary."""
    rows = plan["normal"]["rows"]
    result = []
    for role in ROLES:
        for operation, capacity in AUTH.items():
            ticket = [r for r in rows if r["action"] == "gotrue_" + role + "_" + operation]
            require(len(ticket) == 1 and ticket[0]["cost"] == capacity, "auth_ticket_shape")
            selected = [(i, r) for i, r in enumerate(rows)
                        if r.get("action_binding") == dict(kind="auth", role=role, operation=operation)]
            require([r["action"] for _, r in selected[:5]] == ["before"] * 3 + ["evidence_query"] * 2,
                    "auth_controller_before_order")
            lock = [(i, r) for i, r in selected if r["action"] == "auth_identity_lock"]
            guarded = operation in ("issue", "verify", "refresh")
            require(len(lock) == (6 if guarded else 0), "auth_identity_guard_shape")
            # GuardedIssuance calls the HTTP action before its finally ROLLBACK.
            # Unguarded actions precede action_completed, not AuthEvidence.after.
            index = lock[-1][0] if guarded else selected[5][0]
            require(rows[index]["action"] == ("auth_identity_lock" if guarded else "evidence_query"),
                    "auth_act_anchor")
            after = [r for _, r in selected if r["action"] == "after"]
            require(len(after) == 3, "auth_evidence_after_shape")
            result.append(dict(dispatch_id="auth:" + role + ":" + operation,
                role=role, operation=operation, capacity_use=capacity,
                charge_group=ticket[0]["charge_group"], local_ticket_checkpoint_id=ticket[0]["id"],
                before_register_row=rows[index]["id"], after_register_row=rows[index - 1]["id"],
                after_evidence_row=after[-1]["id"], phase=ticket[0]["phase"],
                guarded=guarded, actual_method="action.act", actual_dispatch_observed=False))
    require(len(result) == 18 and len({r["charge_group"] for r in result}) == 18, "auth_distinct_tickets")
    return sorted(result, key=lambda r: next(i for i, x in enumerate(rows) if x["id"] == r["before_register_row"]))


def derive_stream_order(plan, *, runtime_dir):
    """Move optional page slots inside FETCH, retaining all 3*41 capacities.

    This is the maximum-page path. A shorter page loop is a proper prefix of
    these FETCH/sample pairs followed by the identical CLOSE/validation suffix.
    The old file's capacity slots after final_guard are not actual dispatches.
    """
    from integral_stream import ROWS, PAGE, PAGES, PROTOCOL_CAPACITY
    require(PAGES == (ROWS + PAGE - 1) // PAGE and PROTOCOL_CAPACITY == 15 + 2 * PAGES,
            "stream_capacity_source_changed")
    binding = _method("quota_candidate_v1/runtime_stream.py", "_run", runtime_dir)
    tree = ast.parse((pathlib.Path(runtime_dir) / "runtime_stream.py").read_text(encoding="utf-8"))
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run")
    loops = [n for n in ast.walk(run) if isinstance(n, ast.While)]
    require(len(loops) == 1 and ast.unparse(loops[0].test) == "total < required", "stream_page_loop_changed")
    calls = [n for n in ast.walk(loops[0]) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "utility"]
    require(len(calls) == 1 and "FETCH FORWARD " in ast.unparse(calls[0]), "stream_fetch_count_changed")
    value = copy.deepcopy(plan)
    rows = value["normal"]["rows"]
    derivations = []
    for label in ("before", "before_cleanup", "after_cleanup"):
        prefix = "stream_" + label + "_"
        start = next(i for i, r in enumerate(rows) if r["action"] == prefix + "begin")
        end = next(i for i, r in enumerate(rows) if r["action"] == prefix + "rollback")
        block = rows[start:end + 1]
        optional = [r for r in block if r.get("optional_capacity_only")]
        actual = [r for r in block if not r.get("optional_capacity_only")]
        require(len(block) == PROTOCOL_CAPACITY and len(optional) == 2 * (PAGES - 1)
                and len(actual) == 17, "stream_reference_capacity_shape:" + label)
        require([r["action"].removeprefix(prefix) for r in actual] ==
                ["begin", "guard", "canonical", "inventory", "reader_bind", "io",
                 "utility", "io", "utility", "io", "utility", "io", "utility", "io",
                 "io_terminal", "final_guard", "rollback"], "stream_reference_order:" + label)
        reordered = actual[:12] + optional + actual[12:]
        for index, row in enumerate(reordered):
            row["dispatch_source"] = dict(path=binding["source"], sha256=binding["source_sha256"], symbol="_run")
            row["stream_label"] = label
            row["stream_command_index"] = index
            row["source_capacity_only"] = row.get("optional_capacity_only", False)
            if 10 <= index < 10 + 2 * PAGES:
                row["stream_page"] = (index - 10) // 2
                row["stream_method"] = "FETCH" if index % 2 == 0 else "sample"
            row["execution_ready"] = False
        rows[start:end + 1] = reordered
        derivations.append(dict(label=label, source=binding, row_ids=[r["id"] for r in reordered],
            maximum_pages=PAGES, maximum_rows=ROWS, page_size=PAGE,
            commands=PROTOCOL_CAPACITY, actual_pages_observed=False, normal_delta=0))
    for index, row in enumerate(rows):
        row["ordinal"] = index
    value.update(version="admission-current-plan-v4", parent_plan_sha256=plan["plan_sha256"],
                 stream_derivations=derivations)
    value["current_source_hashes"][binding["source"]] = binding["source_sha256"]
    own = _source("admission_budget_current_order.py", runtime_dir)
    value["current_source_hashes"][own["source"]] = own["source_sha256"]
    value["plan_sha256"] = canonical_sha({k: v for k, v in value.items() if k != "plan_sha256"})
    return value


def current_normal_events(plan):
    """All managed reservations become local checkpoints; actual calls join later."""
    events = normal_events(plan["normal"])
    managed = {r["id"] for r in plan["normal"]["rows"] if r["kind"] == "auth_reserved"}
    for event in events:
        if event["id"] in managed:
            event.update(event_kind="local_reservation_checkpoint", outcomes=("confirmed", "interrupted"))
    return events


def _dispatch_binding(row, bind):
    action = row["action"]
    if row.get("stream_label"):
        return bind("quota_candidate_v1/runtime_stream.py", "_run.q")
    if action.startswith("cli_"):
        return bind("quota_candidate_v1/runtime_prefix.py", "PendingPrefix.run") if row["kind"] == "cli_reserved" else bind("cli_stat_reader.py", "snapshot")
    if action == "project_tls_and_quota_history":
        return bind("lifecycle_gates.py", "preflight")
    if action in ("before", "after"):
        return bind("auth_evidence.py", "AuthEvidence." + action)
    if action == "auth_identity_lock":
        return bind("registered_runner.py", "IdentitySession.query")
    if action == "evidence_query" or action == "final_closure":
        return bind("integral_ci.py", "Composition.evidence_query")
    if action in ("guard_install", "metadata_install", "remove"):
        return bind("registered_lifecycle.py", "RegisteredLifecycle.close_temporary"
                    if action == "remove" else "RegisteredLifecycle._dispatch")
    if action.startswith("gates_"):
        return bind("integral_ci.py", "Composition.final_metadata" if action.startswith("gates_final_")
                    else "Composition.preservation")
    context = row.get("action_binding", {})
    require(context.get("kind") == "workflow" or context == dict(kind="lifecycle", operation="workflow"),
            "native_source_join:" + row["id"])
    return bind("quota_candidate_v1/runtime_parent_workflow.py", "WorkflowBridge.workflow.raw_query")


def assemble_normal_contract(plan, *, runtime_dir):
    """Executable event assembly with concrete dispatch positions and sources.

    Recovery/lifecycle exports join separately. Their absence never authorizes
    execution. SQL hashes retained from old observations are labelled as such.
    """
    from admission_budget_current_dag import workflow_dispatch_requirements, CONTRACT_FORMAT
    @functools.lru_cache(maxsize=None)
    def bind(name, method):
        return _method(name, method, runtime_dir)
    require(plan.get("version") == "admission-current-plan-v4", "current_stream_order_required")
    require(canonical_sha({k: v for k, v in plan.items() if k != "plan_sha256"}) == plan["plan_sha256"],
            "current_order_plan_changed")
    rows = {r["id"]: r for r in plan["normal"]["rows"]}
    expected = current_normal_events(plan)
    auth = auth_dispatch_requirements(plan)
    workflow = workflow_dispatch_requirements(plan)["rows"]
    before, after = collections.defaultdict(list), collections.defaultdict(list)
    for item in auth + workflow:
        is_auth = "role" in item
        event = dict(event_id=item["dispatch_id"], dispatch_id=item["dispatch_id"], stage="dispatch",
            event_kind="dispatch", phase=item["phase"], charge_group=item["charge_group"], cost=0,
            capacity_use=item["capacity_use"], selector=copy.deepcopy(item), outcomes=list(OUTCOMES),
            next={}, state_after={}, **_source("quota_candidate_v1/runtime_auth.mjs" if is_auth
                else "quota_candidate_v1/" + item["source_file"], runtime_dir))
        event["method"] = item["actual_method"]
        event["managed_auth" if is_auth else "managed_workflow_identity"] = True
        before[item["before_register_row"]].append(event)
    for item in auth:
        # AuthEvidence.after validates the response before auth_after releases a
        # reservation, and only the final three-role zero proof releases safety.
        changes = {"auth_maybe_live": False} if (item["role"], item["operation"]) == ("b_member", "revoked_denial") else {}
        event = dict(event_id="validate:" + item["dispatch_id"], stage="validation", event_kind="validation",
            phase=item["phase"], cost=0, capacity_use=0, selector=dict(role=item["role"], operation=item["operation"]),
            outcomes=["confirmed", "rejected", "interrupted"], next={},
            state_after_by_outcome={"confirmed": changes},
            **_method("registered_lifecycle.py", "RegisteredLifecycle._dispatch", runtime_dir))
        after[item["after_evidence_row"]].append(event)
    result = []
    for ref in expected:
        row = rows[ref["owner_node"]]
        if ref["id"] == row["id"]:
            result.extend(before[row["id"]])
        stage = ref["stage"]
        kind = "precharge" if stage == "precharge" else "validation" if stage == "validation" else ref["event_kind"]
        if stage == "precharge":
            name, method = "metered_composition.py", "MeteredComposition.before_sql"
            if row["kind"] == "auth_reserved":
                name, method = ("quota_candidate_v1/runtime_adapter.py", "CaseComposition.workflow") if ref.get("workflow_prepaid") else (name, "MeteredComposition.auth_before")
            elif row["charge_group"].startswith("cli_"):
                name, method = ("quota_candidate_v1/runtime_prefix.py", "PendingPrefix.run") if row["charge_group"] == "cli_quota" else (name, "MeteredComposition.pre_auth_dry_run" if row["charge_group"] == "cli_pre_auth" else "MeteredComposition.finalize")
            binding = bind(name, method)
        elif stage == "validation":
            binding = bind("integral_ci.py", ref["source"]["symbol"])
        elif kind == "local_reservation_checkpoint":
            binding = bind("quota_candidate_v1/runtime_adapter.py", "CaseComposition.workflow") if ref.get("action", "").startswith(("gotrue_fixture_identity", "gotrue_workflow_identity_")) else bind("metered_composition.py", "MeteredComposition.auth_before")
        else:
            binding = _dispatch_binding(row, bind)
        event = dict(event_id=ref["id"], stage="dispatch" if stage == "normal" and kind not in ("validation", "local_reservation_checkpoint") else "checkpoint" if stage == "normal" else stage,
            event_kind=kind, phase=ref["phase"], cost=ref["cost"], charge_group=ref["charge_group"],
            capacity_use=row["cost"] if kind in ("dispatch", "opaque_cli_envelope") else 0,
            selector=dict(register_row=row["id"], action=row["action"], action_binding=row.get("action_binding", {}),
                          source_capacity_only=row.get("source_capacity_only", False)),
            outcomes=list(ref["outcomes"]), next={}, **binding)
        if kind in ("dispatch", "opaque_cli_envelope"):
            event["dispatch_id"] = row["id"]
            event["reference_sql_sha256"] = row.get("sql_sha256")
            event["native_template_revalidated"] = row.get("classification") in ("current_source_template", "source_template_not_execution_evidence")
        if kind == "opaque_cli_envelope":
            event["cli_slot"] = row["action"].removeprefix("cli_")
        if stage == "validation":
            event["state_after_by_outcome"] = {"confirmed": copy.deepcopy(ref.get("state_after", {}))}
        else:
            event["state_after"] = copy.deepcopy(ref.get("state_after", {}))
        result.append(event)
        if ref["id"] == row["id"]:
            result.extend(after[row["id"]])
    sources = {e["source"]: e["source_sha256"] for e in result}
    for name, digest in sources.items():
        require(_source(name.removeprefix(PREFIX), runtime_dir)["source_sha256"] == digest,
                "source_changed_during_assembly:" + name)
    state = dict(guard=False, observer=False, controls=False, claimed=False, auth_maybe_live=False,
                 guard_remove_attempted=False, observer_remove_attempted=False)
    for index, event in enumerate(result):
        event["state_before"] = copy.deepcopy(state)
        state.update(event.get("state_after", {}))
        state.update(event.get("state_after_by_outcome", {}).get("confirmed", {}))
        event["next"]["confirmed"] = result[index + 1]["event_id"] if index + 1 < len(result) else "normal_complete"
    return dict(format=CONTRACT_FORMAT, plan_sha256=plan["plan_sha256"], source_hashes=sources,
        events=result, normal_event_ids=[e["event_id"] for e in result], entry=result[0]["event_id"],
        terminals={"normal_complete": "normal", "no_go": "NO_GO"},
        charge_groups=copy.deepcopy(plan["normal"]["charge_groups"]), coverage={}, fault_cases={},
        normal_accounting=dict(capacity=sum(e["cost"] for e in result), auth_dispatches=len(auth),
                               workflow_dispatches=len(workflow), cli_envelopes=3, native_observed=False),
        missing_hooks=["source_native_template_reconciliation", "actual_case_lifecycle_order",
                       "sourcebound_all_prefix_recovery", "actual_14_hook_positions"],
        missing_costs=[], recovery_edges_complete=False, full_chain_admission=False)


def meter_requirements(plan, contract, *, runtime_dir):
    """Evaluate the actual mutation admission predicate on every normal charge.

    A reserve is not a dispatch count. An over-cap result here proves that this
    maximum-page normal path cannot finish under the current meter, irrespective
    of whether the later exception-path coverage has been completed.
    """
    from runtime_budget import RuntimeBudget
    tree = ast.parse((pathlib.Path(runtime_dir) / "runtime_adapter.py").read_text(encoding="utf-8"))
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CaseBudget")
    reserve = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "_reserve")
    expressions = [n.value for n in reserve.body if isinstance(n, ast.Return)]
    require(len(expressions) == 1 and ast.unparse(expressions[0]) == "super()._reserve(phases, state) + 1",
            "case_reserve_implementation_changed")
    meter = types.SimpleNamespace(limits=plan["normal"]["phase_capacities"])
    used, phases, rows = 0, collections.Counter(), []
    for event in contract["events"]:
        if event["event_kind"] != "precharge":
            continue
        used += event["cost"]
        phases[event["phase"]] += event["cost"]
        state = dict(event["state_before"], **event.get("state_after", {}))
        mutation = event["method"] not in ("CaseComposition.workflow", "MeteredComposition.pre_auth_dry_run",
            "MeteredComposition.finalize") and event["phase"] != "preflight"
        reserved = RuntimeBudget._reserve(meter, phases, state) + 1
        required = used + (reserved if mutation else 0)
        rows.append(dict(event_id=event["event_id"], charged_after=used, reserve=reserved,
                         mutation=mutation, required_limit=required, fits=required <= plan["approved_limit"]))
    require(used == plan["normal"]["normal_capacity"], "normal_meter_total_changed")
    sources = [_source(n, runtime_dir) for n in ("runtime_budget.py", "complete_register.py",
        "metered_composition.py", "quota_candidate_v1/runtime_adapter.py")]
    return dict(format="current-meter-admission-predicates-v1", source_bindings=sources,
        rows=rows, normal_capacity=used, required_limit=max(r["required_limit"] for r in rows),
        first_denied=next((r for r in rows if not r["fits"]), None),
        approved_limit=plan["approved_limit"], reserve_is_not_observed_dispatch=True,
        full_recovery_bound=False, hosted_admitted=False)
