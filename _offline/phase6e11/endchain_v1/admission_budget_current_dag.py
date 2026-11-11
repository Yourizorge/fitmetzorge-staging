"""Opt-in current executor DAG, separate from the frozen historical compiler.

Pure offline assembly/validation. A bound is for the supplied finite model, not
proof of runtime coverage, CI success, database cleanup or hosted permission.
Prepayment and dispatch are separate events; uncertain sends never refund it.
"""
import collections
import copy

from admission_budget import APPROVED, CASES, CLOSING, NORMAL, OUTCOMES, require, _binding
from admission_budget_register import canonical_sha

FORMAT = "admission-current-dispatch-dag-v1"
CONTRACT_FORMAT = "current-dispatch-contract-v1"
DISPATCH_KINDS = ("dispatch", "opaque_cli_envelope")
LOCAL_KINDS = ("local_reservation_checkpoint", "validation")


def workflow_dispatch_requirements(current_plan):
    """Concrete join keys for D's 1 parent + 71 child HTTP recorder sites.

    The anchor rows come from the retained/current ordered plan. They are exact
    matching requirements, not a claim that retained native templates have been
    revalidated or that an HTTP response confirms its underlying SQL cost.
    """
    rows = current_plan["normal"]["rows"]
    by_action = collections.defaultdict(list)
    for index, row in enumerate(rows):
        by_action[row["action"]].append((index, row))
    result = []
    for index in range(72):
        action = "gotrue_fixture_identity" if index == 0 else "gotrue_workflow_identity_" + str(index - 1)
        tickets = by_action[action]
        require(len(tickets) == 1 and tickets[0][1]["cost"] == 5, "workflow_ticket_shape:" + action)
        ticket = tickets[0][1]
        if index == 0:
            matches = by_action["workflow_auth_before"]
            require(len(matches) == 1, "workflow_seed_anchor")
            before_index = matches[0][0] + 1
        else:
            matches = [(i, r) for i, r in enumerate(rows)
                       if r.get("action_binding") == {"kind": "workflow", "step": index - 1}
                       and r["action"] in ("begin", "read_begin")]
            require(bool(matches), "workflow_transport_anchor:" + str(index - 1))
            before_index = matches[0][0]
        require(0 < before_index < len(rows), "workflow_anchor_bounds")
        result.append(dict(dispatch_id="workflow_user_" + str(index), workflow_index=index,
            step=None if index == 0 else index - 1, phase=ticket["phase"],
            charge_group=ticket["charge_group"], capacity_use=5,
            precharge_event_id="precharge:" + ticket["charge_group"],
            local_ticket_checkpoint_id=ticket["id"],
            after_register_row=rows[before_index - 1]["id"],
            before_register_row=rows[before_index]["id"],
            before_action=rows[before_index]["action"],
            actual_method="WorkflowBridge.workflow" if index == 0 else "auth.fetcher",
            source_file="runtime_parent_workflow.py" if index == 0 else "runtime_integral_workflow.mjs",
            actual_dispatch_observed=False, native_order_revalidated=False))
    require(len({row["charge_group"] for row in result}) == 72, "workflow_distinct_tickets")
    return dict(plan_sha256=current_plan["plan_sha256"], rows=result, upfront_capacity=360,
                actual_call_sql_bound_proven=False, complete_bound=False)


def assemble_current_dag(contract=None, *, report=None, current_plan=None):
    """Join D's actual export to every event in the current ordered register.

    No dispatch method, edge, source hash or recovery edge is synthesized from
    a historical row. Unmatched rows are returned as concrete missing inputs.
    """
    from admission_budget_register import assemble, normal_events
    report = assemble() if report is None else report
    current = report["current_plan"] if current_plan is None else current_plan
    require(canonical_sha({k: v for k, v in current.items() if k != "plan_sha256"})
            == current["plan_sha256"], "current_plan_hash")
    expected = normal_events(current["normal"])
    value = copy.deepcopy(contract or {})
    if contract is not None:
        require(value.get("format") == CONTRACT_FORMAT, "dispatch_contract_format")
        require(value.get("plan_sha256") == current["plan_sha256"], "dispatch_plan_changed")
    coverage = value.get("coverage", {})
    events = {e["event_id"]: e for e in value.get("events", [])}
    missing = list(value.get("missing_hooks", []))
    for event in expected:
        target = coverage.get(event["id"], event["id"])
        if target not in events:
            missing.append("register_event:" + event["id"])
    return dict(value, format=FORMAT,
        plan_sha256=current["plan_sha256"],
        register_source_hashes=copy.deepcopy(current["current_source_hashes"]),
        register_events=expected,
        register_charge_groups=copy.deepcopy(current["normal"]["charge_groups"]),
        register_recovery_paths=copy.deepcopy(current["recovery_paths"]),
        workflow_dispatch_requirements=workflow_dispatch_requirements(current),
        historical_reference=dict(normal=NORMAL, closing=CLOSING, read_only=True),
        approved_limit=APPROVED, missing_hooks=sorted(set(missing)),
        missing_costs=copy.deepcopy(value.get("missing_costs", [])),
        unresolved_inputs=copy.deepcopy(value.get("unresolved_inputs", [])),
        normal_event_ids=value.get("normal_event_ids", []),
        events=value.get("events", []), fault_cases=value.get("fault_cases", {}),
        hosted_admitted=False)


def _nonnegative(value, reason):
    require(type(value) is int and value >= 0, reason)


def _lane(event):
    return event.get("lane", "recovery" if event["stage"] == "recovery" else "normal")


def _event(event, sources, groups):
    ident = event["event_id"]
    _binding(event, sources)
    require(isinstance(event.get("method"), str) and bool(event["method"]), "method:" + ident)
    require(isinstance(event.get("selector"), dict) and bool(event["selector"]), "selector:" + ident)
    require(event.get("retry", False) is False, "retry:" + ident)
    require(event.get("stage") in ("precharge", "dispatch", "validation", "recovery", "checkpoint"),
            "stage:" + ident)
    require(_lane(event) in ("normal", "recovery"), "lane:" + ident)
    require(isinstance(event.get("phase"), str) and bool(event["phase"]), "phase:" + ident)
    kind = event.get("event_kind")
    require(kind in DISPATCH_KINDS + LOCAL_KINDS + ("precharge",), "event_kind:" + ident)
    _nonnegative(event.get("cost"), "cost:" + ident)
    use = event.get("capacity_use", 0)
    _nonnegative(use, "capacity_use:" + ident)
    outcomes = event.get("outcomes")
    require(isinstance(outcomes, list) and "confirmed" in outcomes
            and len(outcomes) == len(set(outcomes)), "outcomes:" + ident)
    require(set(outcomes) <= set(OUTCOMES) | {"rejected", "interrupted", "injected"},
            "unsupported_outcome:" + ident)
    require(set(event.get("next", {})) == set(outcomes), "missing_edges:" + ident)
    group = event.get("charge_group")
    require(group is None or group in groups, "unknown_group:" + ident)
    if kind == "precharge":
        require(event["stage"] == "precharge" and group is not None
                and event["cost"] == groups[group]["capacity"] and use == 0,
                "precharge_capacity:" + ident)
        require(not event.get("dispatch_id"), "precharge_is_not_dispatch:" + ident)
    elif kind in LOCAL_KINDS:
        require(event["cost"] == 0 and use == 0 and not event.get("dispatch_id"),
                "local_is_not_dispatch:" + ident)
    else:
        require(isinstance(event.get("dispatch_id"), str) and bool(event["dispatch_id"]),
                "dispatch_identity:" + ident)
        require(set(OUTCOMES) <= set(outcomes), "dispatch_outcomes:" + ident)
        require((group is not None and event["cost"] == 0 and use > 0)
                or (group is None and event["cost"] == 1 and use == 0 and kind == "dispatch"),
                "dispatch_accounting:" + ident)
    if event.get("state_after"):
        require(all(v is True for v in event["state_after"].values()),
                "release_requires_validated_outcome:" + ident)
    for outcome, changes in event.get("state_after_by_outcome", {}).items():
        require(outcome in outcomes and isinstance(changes, dict), "state_outcome:" + ident)
        require(all(type(v) is bool for v in changes.values()), "state_boolean:" + ident)
        if any(v is False for v in changes.values()):
            require(kind == "validation" and outcome == "confirmed",
                    "release_requires_validated_outcome:" + ident)
    return event


def _graph(plan, sources):
    groups = plan.get("charge_groups", {})
    require(isinstance(groups, dict), "charge_groups")
    for group in groups.values():
        require(type(group.get("capacity")) is int and group["capacity"] > 0, "group_capacity")
    rows, terminals = plan["events"], plan.get("terminals", {})
    require(isinstance(terminals, dict) and set(terminals.values()) <= {"normal", "NO_GO"}
            and list(terminals.values()).count("normal") == 1, "terminals")
    nodes = {}
    for event in rows:
        ident = event.get("event_id")
        require(isinstance(ident, str) and ident and ident not in nodes and ident not in terminals,
                "duplicate_event")
        nodes[ident] = _event(event, sources, groups)
    require(plan.get("entry") in nodes, "entry")
    indegree = collections.Counter({key: 0 for key in nodes})
    for event in rows:
        for target in set(event["next"].values()):
            require(target in nodes or target in terminals, "edge_target:" + str(target))
            if target in nodes:
                indegree[target] += 1
    queue = collections.deque(key for key, degree in indegree.items() if degree == 0)
    order = []
    while queue:
        ident = queue.popleft()
        order.append(ident)
        for target in set(nodes[ident]["next"].values()):
            if target in nodes:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
    require(len(order) == len(nodes), "cycle_or_retry")
    group_bits = {name: 1 << i for i, name in enumerate(groups)}
    dispatch_bits = {name: 1 << i for i, name in enumerate(sorted({
        e["dispatch_id"] for e in rows if e.get("dispatch_id")}))}
    # Intersections prove dominance; unions detect a duplicate on ANY path.
    states = {plan["entry"]: (0, 0, 0, 0, False)}
    prefix, totals = {}, {}
    for ident in order:
        require(ident in states, "unreachable_event:" + ident)
        maximum, charged_all, charged_any, dispatched_any, fault = states[ident]
        event = nodes[ident]
        require(not fault or _lane(event) == "recovery", "fault_resumes_normal:" + ident)
        group = event.get("charge_group")
        bit = group_bits.get(group, 0)
        if event["event_kind"] == "precharge":
            require(not charged_any & bit, "double_precharge:" + ident)
            charged_all |= bit
            charged_any |= bit
        elif event["event_kind"] in DISPATCH_KINDS and group is not None:
            require(charged_all & bit, "dispatch_before_precharge:" + ident)
        if event.get("dispatch_id"):
            bit = dispatch_bits[event["dispatch_id"]]
            require(not dispatched_any & bit, "duplicate_dispatch:" + ident)
            dispatched_any |= bit
        prefix[ident] = maximum
        maximum += event["cost"]
        for outcome, target in event["next"].items():
            failed = fault or outcome != "confirmed"
            if target in terminals:
                require(not failed or terminals[target] == "NO_GO", "fault_terminal_pass")
                totals[target] = max(totals.get(target, 0), maximum)
            else:
                incoming = (maximum, charged_all, charged_any, dispatched_any, failed)
                if target in states:
                    previous = states[target]
                    incoming = (max(previous[0], maximum), previous[1] & charged_all,
                                previous[2] | charged_any, previous[3] | dispatched_any,
                                previous[4] or failed)
                states[target] = incoming
    # Check consumption within each prepaid envelope, including shared suffixes.
    consumers = collections.defaultdict(list)
    for event in rows:
        if event.get("capacity_use", 0):
            consumers[event["charge_group"]].append(event)
    for group, values in consumers.items():
        limit = groups[group]["capacity"]
        if sum(e["capacity_use"] for e in values) <= limit:
            continue
        used = {plan["entry"]: 0}
        for ident in order:
            event = nodes[ident]
            total = used[ident] + (event.get("capacity_use", 0)
                                  if event.get("charge_group") == group else 0)
            require(total <= limit, "envelope_exceeded:" + group)
            for target in event["next"].values():
                if target in nodes:
                    used[target] = max(used.get(target, 0), total)
    suffix = {}
    for ident in reversed(order):
        suffix[ident] = nodes[ident]["cost"] + max(suffix.get(t, 0) for t in nodes[ident]["next"].values())
    phases = collections.Counter()
    normal, ident = [], plan["entry"]
    while ident in nodes:
        event = nodes[ident]
        require(_lane(event) == "normal", "normal_enters_recovery")
        normal.append(ident)
        phases[event["phase"]] += event["cost"]
        ident = event["next"]["confirmed"]
    require(terminals[ident] == "normal", "normal_incomplete")
    require(normal == plan.get("normal_event_ids"), "normal_order_mismatch")
    prefixes = [dict(event_id=ident, outcome=outcome, prepaid_before=prefix[ident],
                     charge=nodes[ident]["cost"], suffix=suffix.get(target, 0),
                     capacity=prefix[ident] + nodes[ident]["cost"] + suffix.get(target, 0))
                for ident in order for outcome, target in nodes[ident]["next"].items()]
    return dict(normal_capacity=sum(phases.values()), phase_capacities=dict(phases),
                modeled_maximum=max(totals.values()), fault_prefixes=prefixes,
                event_count=len(nodes), prefix_count=len(prefixes))


def _recovery_coverage(plan, nodes, sources):
    """Require actual exception/finally provenance for EVERY normal stop edge."""
    missing = []
    bindings = plan.get("prefix_recovery", {})
    for ident in plan.get("normal_event_ids", []):
        if ident not in nodes:
            continue
        event = nodes[ident]
        for outcome, target in event.get("next", {}).items():
            if outcome == "confirmed":
                continue
            key = ident + "|" + outcome
            binding = bindings.get(key)
            if not binding:
                missing.append("prefix_recovery:" + key)
                continue
            _binding(binding, sources)
            require(isinstance(binding.get("method"), str) and binding["method"], "recovery_method:" + key)
            require(binding.get("entry") == target, "recovery_entry:" + key)
            state = dict(event.get("state_before", {}), **event.get("state_after", {}))
            state.update(event.get("state_after_by_outcome", {}).get(outcome, {}))
            require(binding.get("state_sha256") == canonical_sha(state), "recovery_state:" + key)
            pending, reached = [target], set()
            while pending:
                at = pending.pop()
                if at in reached or at not in nodes:
                    continue
                reached.add(at)
                require(_lane(nodes[at]) == "recovery", "recovery_lane:" + key)
                pending.extend(nodes[at]["next"].values())
            require(isinstance(binding.get("event_ids"), list)
                    and len(binding["event_ids"]) == len(set(binding["event_ids"]))
                    and set(binding["event_ids"]) == reached, "recovery_coverage:" + key)
    return missing


def compile_current_release(plan, source_hashes, *, source_root=None, runtime_dir=None):
    """Public admission boundary; finite graph arithmetic alone is insufficient."""
    from admission_budget import HERE
    from admission_budget_current_release import compile_release
    return compile_release(plan, source_hashes,
        source_root=HERE.parents[2] if source_root is None else source_root,
        runtime_dir=runtime_dir)


def _compile_finite_model(plan, source_hashes):
    """Compile the current model without imposing historical phase equalities.

    Private arithmetic/test helper, NOT the public release admission boundary.
    Missing supplied-model coverage returns NO_GO. Source-derived executor
    completeness is checked independently by compile_current_release.
    """
    require(plan.get("format") == FORMAT, "current_dag_format")
    require(plan.get("approved_limit") == APPROVED, "approved_limit_changed")
    missing = list(plan.get("missing_costs", [])) + list(plan.get("missing_hooks", []))
    missing += list(plan.get("unresolved_inputs", []))
    for name, digest in plan.get("register_source_hashes", {}).items():
        require(source_hashes.get(name) == digest, "register_source_changed:" + name)
    events = plan.get("events", [])
    nodes = {e["event_id"]: e for e in events}
    require(len(nodes) == len(events), "duplicate_event")
    graph_ready = bool(events)
    for event in events:
        _binding(event, source_hashes)
        _nonnegative(event.get("cost"), "cost:" + event["event_id"])
        if ("confirmed" not in event.get("outcomes", [])
                or set(event.get("next", {})) != set(event.get("outcomes", []))):
            missing.append("event_edges:" + event["event_id"])
            graph_ready = False
    normal_ids = plan.get("normal_event_ids", [])
    if events and not normal_ids:
        missing.append("actual_normal_order")
        graph_ready = False
    coverage = plan.get("coverage", {})
    expected = plan.get("register_events", [])
    if not expected:
        missing.append("current_ordered_register")
    joined = []
    for ref in expected:
        ident = coverage.get(ref["id"], ref["id"])
        if ident not in nodes or ident not in normal_ids:
            missing.append("register_event:" + ref["id"])
            continue
        event = nodes[ident]
        joined.append(ident)
        require(event["cost"] == ref["cost"] and event["phase"] == ref["phase"],
                "register_charge_mismatch:" + ref["id"])
        if ref["stage"] == "precharge":
            require(event.get("event_kind") == "precharge", "register_precharge_kind")
            require(event.get("charge_group") == ref.get("charge_group"), "register_precharge_group")
        elif ref.get("event_kind") == "local_reservation_checkpoint":
            require(event.get("event_kind") == "local_reservation_checkpoint", "ticket_not_dispatch")
    require(len(joined) == len(set(joined)), "coverage_not_injective")
    positions = {ident: i for i, ident in enumerate(normal_ids)}
    require([positions[i] for i in joined] == sorted(positions[i] for i in joined), "register_order_changed")
    for name, group in plan.get("register_charge_groups", {}).items():
        actual = plan.get("charge_groups", {}).get(name)
        if actual is None:
            missing.append("register_group:" + name)
        else:
            require(actual["capacity"] == group["capacity"], "register_group_capacity:" + name)
    for event in events:
        if not isinstance(event.get("state_before"), dict):
            missing.append("state_prefix:" + event["event_id"])
            continue
        for outcome, target in event.get("next", {}).items():
            if target in nodes and isinstance(nodes[target].get("state_before"), dict):
                after = dict(event["state_before"], **event.get("state_after", {}))
                after.update(event.get("state_after_by_outcome", {}).get(outcome, {}))
                require(after == nodes[target]["state_before"], "state_edge:" + event["event_id"])
    for label, flag, count in (("workflow_actual_calls", "managed_workflow_identity", 72),
                               ("auth_actual_calls", "managed_auth", 18)):
        selected = [e for e in events if e.get(flag) is True and e["event_id"] in normal_ids]
        if len(selected) != count:
            missing.append(label + ":" + str(len(selected)) + "/" + str(count))
        for event in selected:
            require(event.get("event_kind") == "dispatch" and event.get("charge_group") is not None,
                    "managed_call_not_prepaid_dispatch")
            if flag == "managed_workflow_identity":
                require(event.get("capacity_use") == 5, "workflow_call_capacity")
        require(len({e.get("dispatch_id") for e in selected}) == len(selected), "managed_dispatch_duplicate")
    slots = [e for e in events if e.get("cli_slot") is not None and e["event_id"] in normal_ids]
    if sorted(e["cli_slot"] for e in slots) != ["final", "pre_auth", "quota"]:
        missing.append("three_actual_cli_slots")
    for event in slots:
        require(event.get("event_kind") == "opaque_cli_envelope"
                and event.get("capacity_use") == (64 if event["cli_slot"] == "quota" else 28),
                "cli_envelope_capacity")
    if plan.get("recovery_edges_complete") is not True:
        missing.append("actual_recovery_edges")
    missing.extend(_recovery_coverage(plan, nodes, source_hashes))
    for case in CASES:
        item = plan.get("fault_cases", {}).get(case)
        if not item:
            missing.append("fault_hook:" + case)
            continue
        _binding(item, source_hashes)
        require(item.get("event_id") in nodes, "fault_event:" + case)
        require(item.get("outcome") != "confirmed"
                and item.get("outcome") in nodes[item["event_id"]]["outcomes"], "fault_outcome:" + case)
        require(isinstance(item.get("hook_case"), str) and item["hook_case"], "fault_selector:" + case)
    model = _graph(plan, source_hashes) if graph_ready else {}
    if not events:
        missing.append("actual_dispatch_graph")
    missing = sorted(set(missing))
    complete = not missing
    maximum = model.get("modeled_maximum")
    fits = complete and maximum is not None and maximum <= APPROVED
    return dict(model, format=FORMAT, plan_sha256=plan.get("plan_sha256"),
                dag_sha256=canonical_sha(plan), bound_complete=complete,
                minimal_cap=maximum if complete else None, fits=fits,
                approved_limit=APPROVED, historical_normal=NORMAL, historical_closing=CLOSING,
                normal_delta_from_reference=(model["normal_capacity"] - NORMAL) if model else None,
                missing_costs=missing,
                missing_summary=dict(collections.Counter(item.split(":", 1)[0] for item in missing)),
                status="FINITE_MODEL_BOUND" if fits else "NO_GO", admission_eligible=False,
                actual_executor_and_real_ci_proven=False, hosted_admitted=False)
