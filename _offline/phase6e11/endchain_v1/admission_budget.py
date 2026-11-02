"""Offline finite-path budget compiler; never a hosted admission authority.

Main supplies a source-bound dispatch graph once the CLI/Auth/fixture interfaces
are settled. Each node is one native command, one local gate, or one indivisible
prepaid Auth/CLI reservation. Expand state-dependent paths into separate nodes.
Every node, including recovery nodes, needs all OUTCOMES. No cycles or replays.
Unknown dispatches consume their full reservation, even on a failed cleanup.

compile_graph computes an exact maximum for the supplied finite model only.
compile_release additionally requires the full cost/case coverage contract.
Neither function proves that an executor exported every command. Main's real,
same-source trace/coverage tests remain necessary. No filesystem writes or I/O
other than explicit local source/JSON reads are performed.
"""
import argparse
import ast
import collections
import hashlib
import itertools
import json
import pathlib

APPROVED = 2349
NORMAL = 2338
CLOSING = 731
PHASE_BUDGETS = dict(
    preflight=4, migration=128, baseline=61, setup=33, guard=13, auth=318,
    controller=286, route_a=191, route_b=286, restore=54, measurements=136,
    io=97, cleanup=633, final=97, closure=1)
CLOSING_PHASES = ("cleanup", "final", "closure")
OUTCOMES = ("confirmed", "before_send", "lost_response", "timeout",
            "duplicate_rejected")
UNSENT = ("before_send", "duplicate_rejected")
KINDS = ("native", "observer", "auth_reserved", "cli_reserved", "local")
CASES = ("pre_migration", "post_migration", "mid_auth", "controller",
         "route_a", "route_b", "restore", "lost_response", "duplicate",
         "timeout", "partial_fixture_cleanup", "cleanup_failure",
         "final_check_failure", "closure_failure")
COST_DOMAINS = ("native_protocol", "cli_dispatch", "cli_observers",
                "auth_normal", "auth_partial_cleanup", "fixture_inventory_13",
                "fixture_partial_cleanup", "control_restore", "rollback",
                "final_checks", "closure", "writer_barrier", "ownership",
                "bounded_streams")
HERE = pathlib.Path(__file__).resolve().parent


class ModelError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ModelError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(row, source_hashes):
    name, sha = row.get("source"), row.get("source_sha256")
    require(isinstance(name, str) and bool(name), "source_missing")
    require(isinstance(sha, str) and len(sha) == 64
            and all(c in "0123456789abcdef" for c in sha),
            "source_hash_invalid:" + name)
    require(source_hashes.get(name) == sha, "source_binding_changed:" + name)


def _cost(node, outcome):
    return 0 if outcome in UNSENT else node["cost"]


def compile_graph(plan, source_hashes):
    """Enumerate all dispatch prefixes using a DAG, without path explosion.

    before_send/duplicate_rejected mean proven pre-dispatch rejection only.
    A transport with uncertain send must use lost_response/timeout instead.
    Distinct nodes may share a dispatch_id only on mutually exclusive paths.
    Each reservation is charged once, before its first possible dispatch;
    observation cannot refund it. All recovery commands need their own nodes.
    """
    require(plan.get("version") == 1, "model_version")
    rows, terminals = plan.get("nodes"), plan.get("terminals")
    require(isinstance(rows, list) and bool(rows), "commands_missing")
    require(isinstance(terminals, dict) and bool(terminals), "terminals_missing")
    nodes = {}
    for row in rows:
        ident = row.get("id")
        require(isinstance(ident, str) and bool(ident) and ident not in nodes,
                "duplicate_or_missing_node")
        require(ident not in terminals, "terminal_node_collision")
        nodes[ident] = row
        _binding(row, source_hashes)
        require(row.get("kind") in KINDS, "command_kind:" + ident)
        cost = row.get("cost")
        require(type(cost) is int and cost >= 0, "missing_or_invalid_cost:" + ident)
        if row["kind"] == "local":
            require(cost == 0 and row.get("mutation") is False, "local_gate_cost")
        elif row["kind"] in ("native", "observer"):
            require(cost == 1, "native_command_must_be_individual:" + ident)
        else:
            require(cost > 0, "empty_reservation:" + ident)
        require(type(row.get("mutation")) is bool, "mutation_flag:" + ident)
        require(row.get("phase") in (*PHASE_BUDGETS, "safety"), "phase:" + ident)
        require(row.get("stage") in ("normal", "recovery"), "stage:" + ident)
        require(row.get("retry") is False, "retry_not_forbidden:" + ident)
        require(isinstance(row.get("dispatch_id"), str) and bool(row["dispatch_id"]),
                "dispatch_identity:" + ident)
        require(isinstance(row.get("next"), dict) and set(row["next"]) == set(OUTCOMES),
                "fault_cost_or_edge_missing:" + ident)
    for ident, terminal in terminals.items():
        require(terminal.get("status") in ("normal_complete", "NO_GO"),
                "terminal_status:" + ident)
        require(isinstance(terminal.get("pending_evidence"), list),
                "terminal_evidence_missing:" + ident)
        if terminal["status"] == "normal_complete":
            require(not terminal["pending_evidence"], "normal_terminal_unresolved")
    entry = plan.get("entry")
    require(entry in nodes, "entry_missing")
    all_ids = set(nodes) | set(terminals)
    indegree = dict.fromkeys(sorted(all_ids), 0)
    for row in rows:
        for target in row["next"].values():
            require(target in all_ids, "unknown_edge_target:" + str(target))
            indegree[target] += 1
    queue = collections.deque(k for k, n in indegree.items() if n == 0)
    order = []
    while queue:
        ident = queue.popleft()
        order.append(ident)
        for target in nodes.get(ident, {}).get("next", {}).values():
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    require(len(order) == len(all_ids), "retry_or_cycle")
    # Max-prefix propagation includes faults inside recovery, not just one fault.
    used = {entry: 0}
    fault_reachable = {entry: False}
    for ident in order:
        if ident not in used:
            continue
        if ident in terminals:
            require(not fault_reachable[ident]
                    or terminals[ident]["status"] == "NO_GO", "fault_laundered_to_pass")
            continue
        node = nodes[ident]
        require(not fault_reachable[ident] or node["stage"] == "recovery",
                "dependent_normal_work_after_fault:" + ident)
        for outcome, target in node["next"].items():
            used[target] = max(used.get(target, 0), used[ident] + _cost(node, outcome))
            fault_reachable[target] = (fault_reachable.get(target, False)
                                       or fault_reachable[ident] or outcome != "confirmed")
    require(set(used) == all_ids, "unreachable_commands_or_terminals")
    by_dispatch = collections.defaultdict(set)
    for row in rows:
        by_dispatch[row["dispatch_id"]].add(row["id"])
    for group in by_dispatch.values():
        if len(group) == 1:
            continue
        for ident in group:
            pending = list(nodes[ident]["next"].values())
            visited = set()
            while pending:
                target = pending.pop()
                if target in visited:
                    continue
                require(target not in group, "dispatch_replay:" + ident)
                visited.add(target)
                pending.extend(nodes.get(target, {}).get("next", {}).values())
    remaining = dict.fromkeys(terminals, 0)
    for ident in reversed(order):
        if ident in nodes:
            node = nodes[ident]
            remaining[ident] = max(_cost(node, outcome) + remaining[target]
                                   for outcome, target in node["next"].items())
    prefixes = []
    for ident in order:
        if ident not in nodes:
            continue
        node = nodes[ident]
        for outcome, target in node["next"].items():
            consumed = used[ident] + _cost(node, outcome)
            prefixes.append(dict(node=ident, outcome=outcome,
                                 consumed_capacity=consumed,
                                 suffix_capacity=remaining[target],
                                 required_total=consumed + remaining[target],
                                 within_approved=consumed + remaining[target] <= APPROVED))
    normal, phase, kind = [], collections.Counter(), collections.Counter()
    ident = entry
    while ident in nodes:
        row = nodes[ident]
        require(row["stage"] == "normal", "normal_path_enters_recovery")
        normal.append(ident)
        phase[row["phase"]] += row["cost"]
        kind[row["kind"]] += row["cost"]
        ident = row["next"]["confirmed"]
    require(terminals[ident]["status"] == "normal_complete", "normal_path_incomplete")
    return dict(model_bound=remaining[entry], normal_capacity=sum(phase.values()),
                phase_capacities=dict(phase), kind_capacities=dict(kind),
                normal_nodes=normal, prefixes=prefixes,
                mutation_gates=[dict(node=n["id"], consumed_before=used[n["id"]],
                                     required_suffix=remaining[n["id"]],
                                     allowed_by_budget=used[n["id"]] + remaining[n["id"]] <= APPROVED)
                                for n in rows if n["mutation"]],
                fits=remaining[entry] <= APPROVED,
                scope="Complete bound of supplied graph only; not executor completeness.",
                hosted_admitted=False, executable=False, approved_limit=APPROVED)


def compile_release(plan, source_hashes):
    """Fail closed on any absent cost, source binding or integration contract.

    source_hashes must be Main's independently verified current source hashes.
    Coverage maps are exports from Main's executor/case integration, not labels
    invented by this compiler. A numeric minimum is conditional on that complete
    source-bound model and never changes the authorized ceiling.
    """
    try:
        from admission_binding import NEW_RUN
        require(plan.get("preparation_run_id") == NEW_RUN, "preparation_binding_missing_or_changed")
        result = compile_graph(plan, source_hashes)
        require(result["phase_capacities"] == PHASE_BUDGETS, "normal_phase_register_drift")
        require(result["normal_capacity"] == NORMAL, "normal_capacity_drift")
        require(sum(result["phase_capacities"][p] for p in CLOSING_PHASES) == CLOSING,
                "closing_reserve_drift")
        for kind, cost in (("auth_reserved", 594), ("cli_reserved", 120), ("observer", 24)):
            require(result["kind_capacities"].get(kind) == cost, "capacity_domain:" + kind)
        nodes = {row["id"]: row for row in plan["nodes"]}
        coverage = plan.get("cost_coverage", {})
        require(set(coverage) == set(COST_DOMAINS), "cost_coverage_incomplete")
        for name, contract in coverage.items():
            _binding(contract, source_hashes)
            require(isinstance(contract.get("nodes"), list) and bool(contract["nodes"])
                    and all(n in nodes for n in contract["nodes"]), "missing_cost_domain:" + name)
        require(set(n for c in coverage.values() for n in c["nodes"]) == set(nodes),
                "commands_not_covered")
        cases = plan.get("fault_cases", {})
        require(set(cases) == set(CASES), "fault_matrix_incomplete")
        for name, case in cases.items():
            _binding(case, source_hashes)
            require(case.get("node") in nodes and case.get("outcome") in OUTCOMES[1:],
                    "fault_case_edge_missing:" + name)
        _binding(plan.get("executor_inventory", {}), source_hashes)
        require(plan["executor_inventory"].get("complete") is True,
                "executor_inventory_incomplete")
        require(plan.get("missing_costs") == [], "unresolved_costs")
        return dict(result, bound_complete=True, minimal_cap=result["model_bound"],
                    status="MODEL_BOUND_FITS" if result["fits"] else "NO_GO_OVER_CAP",
                    actual_executor_and_real_ci_proven=False, cleanup_safety_proven=False,
                    preparation_run_id=NEW_RUN, quota_activated=False)
    except (ModelError, TypeError, KeyError, AttributeError) as error:
        return dict(status="NO_GO_INCOMPLETE_BOUND", bound_complete=False,
                    minimal_cap=None, approved_limit=APPROVED,
                    missing=[str(error)], hosted_admitted=False)


def account(events):
    """Pure ledger verifier: reserved is consumed, not an emitted-count claim."""
    seen, unresolved, overruns = set(), [], []
    used, observed = collections.Counter(), collections.Counter()
    for event in events:
        ident = event.get("dispatch_id")
        require(isinstance(ident, str) and bool(ident) and ident not in seen,
                "duplicate_or_missing_dispatch")
        seen.add(ident)
        kind, cost = event.get("kind"), event.get("cost")
        require(kind in KINDS and type(cost) is int and cost >= 0, "ledger_cost")
        require(cost == 0 if kind == "local" else cost == 1
                if kind in ("native", "observer") else cost > 0, "ledger_cost_kind")
        outcome = event.get("outcome")
        require(outcome in OUTCOMES, "ledger_outcome")
        if outcome in UNSENT:
            require(event.get("pre_dispatch_rejection_proven") is True,
                    "uncertain_send_cannot_be_refunded")
            require(event.get("observed_commands") in (None, 0), "unsent_observation")
            continue
        actual = event.get("observed_commands")
        require(actual is None or type(actual) is int and actual >= 0, "ledger_observation")
        used[kind] += max(cost, actual or 0)
        if actual is not None and actual > cost:
            overruns.append(ident)
        if outcome != "confirmed" or actual is None:
            unresolved.append(ident)
        else:
            observed[kind] += actual
    total = sum(used.values())
    return dict(consumed_capacity=total, consumed_by_kind=dict(used),
                confirmed_observed_by_kind=dict(observed),
                unresolved_dispatches=unresolved, all_counts_known=not unresolved,
                reservation_overruns=overruns,
                status="NO_GO" if unresolved or overruns or total > APPROVED else "COUNTS_KNOWN_ONLY",
                within_approved=total <= APPROVED, hosted_admitted=False)


def _literal_assignment(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    matches = [n.value for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    require(len(matches) == 1, "source_assignment_missing:" + name)
    value = matches[0]
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "dict":
        require(not value.args and all(k.arg is not None for k in value.keywords), "nonliteral_limits")
        return {k.arg: ast.literal_eval(k.value) for k in value.keywords}
    return ast.literal_eval(value)


def inspect_current(register_folder=None):
    """Read current register sources; optional explicit historical folder only."""
    from complete_register import AUTH_CALLS, safety_path
    from cli_envelope import SLOTS, OBSERVERS
    from admission_binding import NEW_RUN
    limits = _literal_assignment(HERE / "metered_composition.py", "LIMITS")
    names = ("complete_register.py", "metered_composition.py", "runtime_budget.py",
             "cli_envelope.py", "safety_auth_budget.py", "safety_auth.py",
             "closure_budget.json", "authorization.json", "admission_budget.py",
             "admission_binding.py")
    sources = {name: digest(HERE / name) for name in names}
    state_names = ("guard", "observer", "controls", "claimed", "auth_maybe_live",
                   "guard_remove_attempted", "observer_remove_attempted")
    safety = []
    for bits in itertools.product((False, True), repeat=len(state_names)):
        state = dict(zip(state_names, bits))
        commands = safety_path(**state)
        safety.append(dict(state=state, commands=commands,
                           capacity=sum(row["sql"] for row in commands)))
    missing = [
        "Current ordered per-dispatch normal register bound to executor precharges.",
        "CLI exact dispatch/reconnect/lost-response costs and observer ordering.",
        "Partial Auth/admin/logout cleanup command costs and unknown-outcome branches.",
        "13-table owned partial-fixture inventory/delete/commit/absence costs.",
        "Every stopping prefix including faults during cleanup/final/closure.",
        "Parent barrier, rollback, control restore and terminal evidence costs per path.",
        "Same-source executor inventory and real fault-matrix coverage exports.",
    ]
    report = dict(status="NO_GO_INCOMPLETE_BOUND", bound_complete=False, minimal_cap=None,
                  hosted_admitted=False, source_hashes=sources, approved_limit=APPROVED,
                  normal_capacity=sum(limits.values()), phase_capacities=limits,
                  closing_capacity=sum(limits[p] for p in CLOSING_PHASES),
                  expected=dict(normal=NORMAL, approved=APPROVED, closing=CLOSING),
                  current_phase_limits_match=limits == PHASE_BUDGETS,
                  auth=dict(matrix=3 * sum(AUTH_CALLS.values()), workflow_prepaid=360,
                            cleanup_prepaid_inside_workflow=130, total=594),
                  cli=dict(reserved_slots=dict(SLOTS), unknown_capacity=sum(SLOTS.values()),
                           observers=len(SLOTS) * OBSERVERS),
                  existing_safety_states=safety, missing_costs=missing,
                  observed_hosted_counts=None, automatic_retries=0, executable=False,
                  preparation_run_id=NEW_RUN, quota_activated=False,
                  legacy_registry_scope="Read-only reference; never an execution identity.",
                  integration_interface=dict(
                      compiler="admission_budget.compile_release(plan, source_hashes)",
                      graph_version=1, outcomes=list(OUTCOMES), cost_domains=list(COST_DOMAINS),
                      required_cases=list(CASES),
                      requirements=["Ordered, source-bound dispatch/reservation DAG, not phase totals.",
                                    "Explicit edges and costs for every recovery outcome.",
                                    "Unknown and prepaid capacity remain consumed; no retries.",
                                    "Main-verified source hashes and exhaustive executor inventory.",
                                    "Fresh disposable case IDs; preparation UUID is not execution permission."]),
                  scope="Local source inventory, not new CI or hosted evidence.")
    if register_folder is not None:
        folder = pathlib.Path(register_folder)
        metadata = json.loads((folder / "complete-command-register.json").read_text())
        rows = []
        for phase in PHASE_BUDGETS:
            rows.extend(json.loads((folder / ("register-phase-" + phase + ".json")).read_text())["rows"])
        rows.sort(key=lambda row: row["id"])
        require(len({r["id"] for r in rows}) == len(rows), "historical_duplicate_rows")
        require(all(type(r["sql"]) is int and r["sql"] >= 0 for r in rows), "historical_cost")
        totals = collections.Counter()
        for row in rows:
            totals[row["phase"]] += row["sql"]
        report["historical_register"] = dict(
            sha256=digest(folder / "complete-command-register.json"),
            phase_file_hashes={p: digest(folder / ("register-phase-" + p + ".json"))
                               for p in PHASE_BUDGETS},
            source_bundle_sha=metadata.get("source_bundle_sha"), rows=rows,
            phase_capacities=dict(totals), normal_capacity=sum(totals.values()),
            closing_capacity=sum(totals[p] for p in CLOSING_PHASES),
            matches_current_phase_limits=dict(totals) == limits,
            current_execution_order_proven=False, fresh_execution_claim=False)
    return report


def run(gate):
    """Parent CI adapter: complete bounded local receipts, never hosted admission."""
    from admission_budget_receipts import run as publish
    return publish(gate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register-folder", type=pathlib.Path)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--section", choices=("all", "summary", "normal", "faults", "components", "graph"), default="all")
    parser.add_argument("--phase", choices=tuple(PHASE_BUDGETS))
    args = parser.parse_args()
    if args.inventory_only:
        value = inspect_current(args.register_folder)
    else:
        from admission_budget_register import assemble, export, REFERENCE
        value = export(assemble(args.register_folder or REFERENCE), args.section, args.phase)
    print(json.dumps(value, indent=None if args.compact else 2, sort_keys=True))
    return 2  # Inventory alone cannot complete the bound or admit a run.


if __name__ == "__main__":
    raise SystemExit(main())
