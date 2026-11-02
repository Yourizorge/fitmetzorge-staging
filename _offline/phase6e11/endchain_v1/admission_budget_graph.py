"""Concrete accounting graphs; unresolved joins are nodes, never zero costs."""
from admission_budget import OUTCOMES, UNSENT, require


def diagnostic_graph(rows, name, cap=None):
    nodes, prefixes = {}, []
    consumed = 0
    for index, row in enumerate(rows):
        ident = name + ":" + str(index)
        following = name + ":" + str(index + 1) if index + 1 < len(rows) else "intended_path_end"
        edges = {}
        for outcome in OUTCOMES:
            charge = 0 if outcome in UNSENT else row["cost"]
            total = None if consumed is None or charge is None else consumed + charge
            edges[outcome] = dict(to=following if outcome == "confirmed" else "unresolved_recovery",
                                  charge=charge, consumed_capacity=total, refunds=0)
            prefixes.append(dict(node=ident, outcome=outcome, consumed_capacity=total,
                                 full_required_capacity=None, admits_hosted=False))
        nodes[ident] = dict(id=ident, stage="diagnostic", action=row["action"], kind=row["kind"],
                            cost=row["cost"], source=row["source"], next=edges)
        consumed = None if consumed is None or row["cost"] is None else consumed + row["cost"]
    return dict(entry=name + ":0" if rows else "intended_path_end", nodes=nodes, prefixes=prefixes,
                terminals={"intended_path_end": "LOCAL_CONTROL_FLOW_ONLY",
                           "unresolved_recovery": "NO_GO_UNBOUNDED_SUFFIX"},
                intended_consumed_capacity=consumed, diagnostic_cap=cap, full_fault_bound=False,
                observed_execution=False, shares_hosted_run_capacity=False)


def assemble_graph(report):
    normal = report["normal_register"]
    rows, nodes = normal["rows"], {}
    prefixes = {(p["node"], p["outcome"]): p for p in report["fault_prefixes"]}
    seen = set()
    for index, row in enumerate(rows):
        group = row["charge_group"]
        charge = normal["charge_groups"][group]["capacity"] if group not in seen else 0
        following = rows[index + 1]["id"] if index + 1 < len(rows) else "normal_bound_gap"
        edges = {}
        for outcome in OUTCOMES:
            prefix = prefixes[row["id"], outcome]
            target = following if outcome == "confirmed" else "recovery_gap_" + prefix["safety_path"]
            edges[outcome] = dict(to=target, charge=0 if outcome in UNSENT else charge,
                                  consumed_capacity=prefix["consumed_capacity"],
                                  normal_closing_unspent=prefix["normal_closing_unspent"], refunds=0)
        nodes[row["id"]] = dict(id=row["id"], stage="normal", phase=row["phase"],
            action=row["action"], kind=row["kind"], cost=row["cost"], charge_group=group,
            source=row["source"], next=edges, execution_ready=False)
        seen.add(group)
    nodes["normal_bound_gap"] = dict(id="normal_bound_gap", stage="unresolved", cost=None,
        reason="Current source identity, component placement and managed costs are not fully bound.",
        required_inputs=[m["id"] for m in report["unresolved_inputs"]],
        next={"blocked": {"to": "NO_GO"}})
    reference_entries = {}
    for key, path in report["reference_safety_paths"].items():
        gap = "recovery_gap_" + key
        commands = path["commands"]
        entry = "reference_safety_" + key + "_0"
        reference_entries[key] = entry
        nodes[gap] = dict(id=gap, stage="unresolved", cost=None,
            reason="No complete source-bound ordering/replacement contract for this recovery state.",
            reference_only_candidate=entry, required_component_suffixes=path["required_component_suffixes"],
            next={"blocked": {"to": "NO_GO"}})
        for index, command in enumerate(commands):
            ident = "reference_safety_" + key + "_" + str(index)
            following = "reference_safety_" + key + "_" + str(index + 1) if index + 1 < len(commands) else gap
            nodes[ident] = dict(id=ident, stage="reference_recovery", action=command["action"],
                cost=command["sql"], kind=command["kind"], reference_only=True,
                source=dict(path="complete_register.py", sha256=report["source_hashes"]["complete_register.py"],
                            symbol="safety_path"),
                next={outcome: dict(to=following if outcome == "confirmed" else gap,
                                    charge=0 if outcome in UNSENT else command["sql"], refunds=0)
                      for outcome in OUTCOMES})
    diagnostics = {}
    components = report["components"]
    for path in components["auth"]["diagnostic_paths"]:
        name = "auth_" + path["case"]
        diagnostics[name] = diagnostic_graph(path["rows"], name, path["diagnostic_reserved"])
    parent = components["parent_bootstrap"]
    diagnostics["parent_bootstrap"] = diagnostic_graph(parent["rows"], "parent_bootstrap", parent["diagnostic_cap"])
    diagnostics["parent_bootstrap"]["failure_only_commands"] = parent["failure_only"]
    for name, commands in components["fixture"]["groups"].items():
        key = "fixture_" + name
        diagnostics[key] = diagnostic_graph(commands, key)
    diagnostics["fixture_normal"]["source_bound_unknown_prefix_suffixes"] = components["fixture"]["fault_paths"]
    fixture_ci = components["fixture_diagnostic"]
    for path in fixture_ci["cases"]:
        name = "fixture_ci_" + path["case"]
        diagnostics[name] = diagnostic_graph(path["rows"], name)
    diagnostics["fixture_ci_setup"] = diagnostic_graph(fixture_ci["setup"], "fixture_ci_setup")
    diagnostics["fixture_ci_closing"] = diagnostic_graph(fixture_ci["closing"], "fixture_ci_closing")
    for case in components["workflow"]["cases"]:
        name = "workflow_" + case["case"]
        # Delegated Auth interleaves native and HTTP; do not append HTTP after native observations.
        if case["managed_rows"]:
            auth_case = "partial_session" if case["case"] == "mid_auth" else "create_lost_reply"
            auth_rows = next(p["rows"] for p in components["auth"]["diagnostic_paths"] if p["case"] == auth_case)
            commands = auth_rows + case["native_rows"][-4:]
        else:
            commands = case["native_rows"]
        diagnostics[name] = diagnostic_graph(commands, name)
        diagnostics[name]["delegated_auth_reservation"] = components["auth"]["diagnostic_contract"]["reserved_units"] if case["managed_rows"] else 0
        diagnostics[name]["native_session_allowance"] = dict(limit=128, cleanup_reserve=16)
    for role in ("member", "trainer", "b"):
        name = "workflow_actor_" + role
        diagnostics[name] = diagnostic_graph(components["workflow"]["bootstrap"]["diagnostic_per_actor_rows"],
                                             name, components["auth"]["diagnostic_contract"]["reserved_units"])
    require(all(edge["to"] in nodes or edge["to"] == "NO_GO"
                for node in nodes.values() for edge in node["next"].values()), "graph_dangling_edge")
    return dict(format="concrete-admission-accounting-graph-v1", entry=rows[0]["id"], nodes=nodes,
                terminals={"NO_GO": "NO_GO_INCOMPLETE_BOUND"},
                reference_recovery_entries=reference_entries, diagnostic_graphs=diagnostics,
                normal_capacity=normal["normal_capacity"], approved_limit=report["approved_limit"],
                closing_reserve=731, minimal_cap=None, full_bound_complete=False,
                recovery_gap_count=len(reference_entries),
                runtime_dispatcher=False, hosted_admitted=False)
