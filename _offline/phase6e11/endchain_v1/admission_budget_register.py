"""Concrete offline register assembly, never a dispatcher.

Retained rows are read-only reference material, not current execution evidence.
Only explicit source-backed replacements are made. New component commands stay
separate until their caller placement/replacement contract is supplied by Main.
This module does not execute a workflow, SQL, Auth, CLI or a historical binding.
"""
import ast
import collections
import copy
import hashlib
import json
import pathlib
import uuid

from admission_binding import NEW_RUN
from admission_budget import HERE, PHASE_BUDGETS, APPROVED, digest, require

REFERENCE = HERE / "receipts" / "reserved-ci-39109482869"
REFERENCE_SHA = "5061786166c8bd153fdc333a708636a1d0f7c538e6b7a5d3aea2f359f9778da1"
CLI_SOURCE_FILES = tuple("cli_predispatch/" + name for name in (
    "ci.py", "entry.mjs", "hook.cjs", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    "policy.cjs", "prepare.py", "README.md", "smoke.py", "test_ci.py", "test_hook.cjs", "test_policy.cjs",
    "pending.py", "test_pending.py"))


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source(name, symbol):
    return dict(path=name, sha256=digest(HERE / name), symbol=symbol)


def sql_row(ident, phase, action, text, filename, symbol):
    return dict(id=ident, phase=phase, action=action, cost=1, kind="native",
                sql_sha256=hashlib.sha256(text.encode()).hexdigest(),
                source=source(filename, symbol), retained_ids=[],
                classification="source_template_not_execution_evidence", execution_ready=False)


def retained(folder=REFERENCE):
    folder = pathlib.Path(folder)
    meta = json.loads((folder / "complete-command-register.json").read_text())
    if folder.resolve() == REFERENCE.resolve():
        require(digest(folder / "complete-command-register.json") == REFERENCE_SHA, "reference_manifest_changed")
    rows, hashes = [], {}
    for phase in PHASE_BUDGETS:
        path = folder / ("register-phase-" + phase + ".json")
        hashes[path.name] = digest(path)
        values = json.loads(path.read_text())["rows"]
        require(all(r["phase"] == phase and type(r["sql"]) is int and r["sql"] == 1 for r in values),
                "reference_phase_or_unit_cost")
        rows.extend(values)
    rows.sort(key=lambda row: row["id"])
    require([r["id"] for r in rows] == ["cmd_%05d" % i for i in range(1, len(rows) + 1)],
            "reference_command_sequence")
    totals = dict(collections.Counter(r["phase"] for r in rows))
    require(totals == meta["phase_budgets"] and len(rows) == meta["normal_capacity"],
            "reference_phase_totals")
    normalized = []
    for row in rows:
        normalized.append(dict(
            id="retained_" + row["id"], retained_ids=[row["id"]], action=row["action"],
            phase=row["phase"], cost=row["sql"], kind="auth_reserved" if row.get("managed")
            else "cli_reserved" if row.get("reservation_only") else "native",
            sql_sha256=row.get("template_sha"), state_after=row.get("state_after", {}),
            optional_capacity_only=row.get("optional", False),
            action_binding=row.get("action_binding", {}),
            source=dict(path="register-phase-" + row["phase"] + ".json",
                        sha256=hashes["register-phase-" + row["phase"] + ".json"],
                        row_sha256=canonical_sha(row), source_bundle_sha=meta["source_bundle_sha"]),
            classification="historical_read_only_reference", execution_ready=False))
    return normalized, dict(manifest_sha256=digest(folder / "complete-command-register.json"),
                            phase_file_hashes=hashes, historical_normal=len(rows),
                            historical_phase_capacities=totals,
                            historical_closing=sum(totals[p] for p in ("cleanup", "final", "closure")),
                            original_binding_read_only=True, current_execution_proven=False)


def cli_slot(slot, phase):
    import cli_envelope
    import cli_stat_reader
    capacity = cli_envelope.capacity(slot)
    templates = ("BEGIN TRANSACTION READ ONLY",
                 "select current_setting('transaction_read_only')='on' readonly",
                 cli_stat_reader.SQL, "ROLLBACK")
    rows = []
    for side in ("before", "after"):
        if side == "after":
            rows.append(dict(id="cli_" + slot + "_reserved", phase=phase,
                             action="cli_" + slot, cost=capacity, kind="cli_reserved",
                             retained_ids=[], source=source("cli_envelope.py", "capacity"),
                             classification="unknown_capacity_not_exact_dispatches",
                             execution_ready=False))
        for i, text in enumerate(templates):
            row = sql_row("cli_%s_%s_%d" % (slot, side, i), phase,
                          "cli_" + slot + "_observer_" + side, text,
                          "cli_stat_reader.py", "snapshot")
            row["kind"] = "observer"
            rows.append(row)
    return rows


def final_gate(stage):
    from integral_io import SNAPSHOT
    from lifecycle_gates import FINAL
    prefix = "gates_final_" + stage
    texts = [("begin", "BEGIN TRANSACTION READ ONLY")]
    if stage == "pre":
        texts += [("timeout", "SET LOCAL statement_timeout='5s'"),
                  ("readonly", "select current_setting('transaction_read_only')='on' readonly")]
    texts += [("io_bind", "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) " + SNAPSHOT),
              ("io_sample", SNAPSHOT),
              ("io_bind", "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) " + FINAL),
              ("io_sample", SNAPSHOT), ("metadata", FINAL), ("io_sample", SNAPSHOT),
              ("io_closing_witness", "EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) " + SNAPSHOT),
              ("rollback", "ROLLBACK")]
    return [sql_row(prefix + "_" + str(i), "final", prefix + "_" + action,
                    text, "integral_ci.py", "Composition.final_metadata")
            for i, (action, text) in enumerate(texts)]


def assemble_normal(folder=REFERENCE):
    """Reconcile retained ordering with explicit current source operations."""
    original, reference = retained(folder)
    rows = copy.deepcopy(original)
    replacements = []

    def remove(predicate):
        selected = [row for row in rows if predicate(row)]
        rows[:] = [row for row in rows if not predicate(row)]
        return selected

    def before(action, values):
        hits = [i for i, row in enumerate(rows) if row["action"] == action]
        require(bool(hits), "assembly_anchor_missing:" + action)
        rows[hits[0]:hits[0]] = values

    def replacement(name, old, new, binding):
        replacements.append(dict(name=name, retained_ids=[i for r in old for i in r["retained_ids"]],
                                 old_capacity=sum(r["cost"] for r in old),
                                 new_ids=[r["id"] for r in new],
                                 new_capacity=sum(r["cost"] for r in new), source=binding))

    old_quota = remove(lambda row: row["action"] == "candidate_quota_migration_aware_cli")
    quota = cli_slot("quota", "migration")
    require(sum(r["cost"] for r in old_quota) == 72, "reference_quota_shape")
    before("gates_after_migration_begin", quota)
    replacement("quota_slot_explicit_observers_and_unknown_reserve", old_quota, quota,
                source("complete_register.py", "build.add_cli"))
    old_cli = remove(lambda row: row["action"] == "empty_cli_dry_run")
    require(sum(r["cost"] for r in old_cli) == 72, "reference_final_cli_shape")
    pre_cli, final_cli = cli_slot("pre_auth", "migration"), cli_slot("final", "final")
    before("guard_install", pre_cli)
    old_gate = remove(lambda row: row["action"].startswith("gates_after_cleanup_"))
    require(len(old_gate) == 20, "reference_final_gate_shape")
    removes = remove(lambda row: row["action"] == "remove")
    require(len(removes) == 10, "reference_removal_shape")
    pre, post = final_gate("pre"), final_gate("post")
    before("final_closure", pre + final_cli + removes + post)
    replacement("split_old_final_72_into_pre_auth_36_and_final_36", old_cli, pre_cli + final_cli,
                source("metered_composition.py", "pre_auth_dry_run/finalize"))
    replacement("final_metadata_pre11_post9", old_gate, pre + post,
                source("integral_ci.py", "Composition.final_metadata"))
    # The executor prepays all 72 workflow Auth calls before entering workflow.
    prepaid = remove(lambda row: row["action"] == "gotrue_fixture_identity"
                     or row["action"].startswith("gotrue_workflow_identity_"))
    require(len(prepaid) == 360, "reference_workflow_auth_capacity")
    prepaid.sort(key=lambda row: (-1 if row["action"] == "gotrue_fixture_identity"
                                 else int(row["action"].rsplit("_", 1)[1]), row["id"]))
    before("lifecycle_reader_begin", prepaid)
    replacements.append(dict(name="move_workflow_360_prepaid_before_entire_workflow",
                             ids=[r["id"] for r in prepaid], capacity=360,
                             cleanup_capacity_not_refundable=130,
                             source=source("metered_composition.py", "workflow")))
    # Managed SQL reservations are indivisible at the HTTP dispatch boundary.
    compact = []
    for row in rows:
        if (compact and row["kind"] == "auth_reserved"
                and compact[-1]["kind"] == row["kind"] and compact[-1]["action"] == row["action"]):
            compact[-1]["cost"] += row["cost"]
            compact[-1]["retained_ids"] += row["retained_ids"]
        else:
            compact.append(copy.deepcopy(row))
    phases, kinds = collections.Counter(), collections.Counter()
    for position, row in enumerate(compact):
        row["ordinal"] = position
        phases[row["phase"]] += row["cost"]
        kinds[row["kind"]] += row["cost"]
    # Runtime charges each CLI envelope and multi-statement install/removal
    # before its first statement. An unknown first send consumes the whole group.
    groups = {}
    removal_index = 0
    for row in compact:
        ident, action = row["id"], row["action"]
        if ident.startswith("cli_"):
            group = next("cli_" + slot for slot in ("quota", "pre_auth", "final")
                         if ident.startswith("cli_" + slot + "_"))
        elif action in ("guard_install", "metadata_install"):
            group = action
        elif action == "remove":
            group = "remove_" + str(removal_index // 5)
            removal_index += 1
        else:
            group = ident
        row["charge_group"] = group
        spec = groups.setdefault(group, dict(capacity=0, nodes=[], phase=row["phase"]))
        require(spec["phase"] == row["phase"], "charge_group_phase_drift")
        spec["capacity"] += row["cost"]
        spec["nodes"].append(ident)
    for group, name in (("remove_0", "observer"), ("remove_1", "guard")):
        groups[group]["state_after_charge"] = {name + "_remove_attempted": True}
        groups[group]["accounting_source"] = source("metered_composition.py", "MeteredComposition.before_sql")
        groups[group]["ordering_source"] = source("registered_lifecycle.py", "close_temporary")
    require(dict(phases) == PHASE_BUDGETS, "assembled_current_phase_mismatch")
    require(kinds["auth_reserved"] == 594 and kinds["cli_reserved"] == 120
            and kinds["observer"] == 24, "assembled_domain_mismatch")
    accounted = [i for r in compact for i in r["retained_ids"]]
    for item in replacements:
        accounted += item.get("retained_ids", [])
    require(sorted(accounted) == sorted(i for r in original for i in r["retained_ids"]),
            "reference_rows_dropped_or_double_counted")
    return dict(rows=compact, charge_groups=groups, normal_capacity=sum(phases.values()),
                phase_capacities=dict(phases), kind_capacities=dict(kinds),
                reference=reference, replacements=replacements,
                execution_order_source=source("metered_composition.py", "workflow"),
                current_execution_proven=False)


def fixture_component(normal_rows):
    import fixture_cleanup_runtime_sql as sql
    plan = sql.plan()
    groups = {key: [sql_row("fixture_" + action, "safety", action, text,
                            "fixture_cleanup_runtime_sql.py", "plan/" + key)
                   for action, text in pairs] for key, pairs in plan.items()}
    # These are concrete candidate hook sites, not an assertion they are wired.
    anchors = [dict(before=row["id"], action=row["action"], phase=row["phase"],
                    action_binding=row.get("action_binding", {}), cost=1)
               for row in normal_rows if row["action"] in ("commit", "lifecycle_commit")]
    actions = [r["action"] for r in groups["normal"]]
    commit = actions.index("commit")
    absence = actions.index("absence_begin")
    fault_paths = []
    for index, row in enumerate(groups["normal"]):
        # Protocol charges before execute: unknown send always includes this row.
        suffix = (groups["failure_only"] + groups["normal"][absence:] if index < commit
                  else groups["normal"][absence:] if index == commit else [])
        fault_paths.append(dict(at=row["id"], outcome="unknown_after_precharge",
                               spent=index + 1, suffix=[r["id"] for r in suffix],
                               total=index + 1 + len(suffix),
                               original_fault_retained=True, retry=False))
    require(len(groups["normal"]) == 22 and len(groups["prepare"]) == 4
            and len(sql.ORDER) == 13, "fixture_component_plan_drift")
    return dict(groups=groups, tables=list(sql.ORDER), normal_cleanup_capacity=22,
                failure_cleanup_max=max(p["total"] for p in fault_paths),
                fault_paths=fault_paths, preparation_capacity=4,
                capture_capacity_per_writer_transaction=1,
                candidate_capture_anchors=anchors, capture_hook_count=len(anchors),
                normal_and_failure_placement_proven=False, global_bound_complete=False,
                sources=[source("fixture_cleanup_runtime.py", "Cleanup.prepare/capture/run"),
                         source("fixture_cleanup_runtime_sql.py", "plan")])


def auth_component():
    import auth_failure
    rows = [dict(id="auth_partial_" + key, action=key, kind="native", cost=1,
                 source=source("auth_failure.py", "NATIVE_SLOTS"))
            for key in auth_failure.NATIVE_SLOTS]
    rows += [dict(id="auth_partial_" + op, action=op, kind="auth_reserved", cost=None,
                  source=source("auth_failure.py", "contract"),
                  unresolved="Measured and source-bound release cost required; no diagnostic 128 substitution.")
             for op in auth_failure.OPERATIONS]
    # Exact diagnostic control-flow schedules, not GoTrue SQL cost observations.
    schedules = {
        "before_dispatch": ([], 4), "create_lost_reply": (["create", "delete"], 8),
        "partial_user": (["create", "delete"], 8),
        "partial_session": (["create", "login", "delete"], 10),
        "login_timeout": (["create", "login", "delete"], 10),
        "logout_timeout": (["create", "login", "logout", "delete"], 12),
        "admin_unknown": (["create", "login", "delete"], 10),
        "duplicate_request": (["create", "login", "delete"], 10),
        "cleanup_interrupted": (["create", "login"], 7),
        "missing_mint_barrier": (["create", "login"], 6),
        "duplicate_cleanup": (["create", "login", "delete"], 10),
    }
    require(set(schedules) == set(auth_failure.CASES), "auth_case_contract_drift")
    paths = [dict(case=name, http_actions=actions, native_commands=native,
                  consumed_expression=str(native) + "".join(" + " + a for a in actions),
                  consumed_capacity=None, source=source("auth_failure.py", "Case.execute/cleanup/auth"),
                  observed_managed_counts=False)
             for name, (actions, native) in schedules.items()]
    diagnostic_contract = auth_failure.contract(dict.fromkeys(auth_failure.OPERATIONS, 128))
    for path in paths:
        names = ["preflight"]
        for op in path["http_actions"]:
            if op != "delete":
                names += ["stats_before_" + op, op, "stats_after_" + op]
        names += ["prefix"]
        if path["case"] != "missing_mint_barrier":
            names += ["cleanup_before"]
        if "delete" in path["http_actions"]:
            names += ["stats_before_delete", "delete", "stats_after_delete"]
        if path["case"] not in ("missing_mint_barrier", "cleanup_interrupted"):
            names += ["final"]
        path["rows"] = [dict(id="auth_case_" + path["case"] + "_" + name, action=name,
                             kind="auth_reserved" if name in auth_failure.OPERATIONS else "native",
                             cost=128 if name in auth_failure.OPERATIONS else 1,
                             source=source("auth_failure.py", "Case.execute/auth/cleanup")) for name in names]
        require(sum(r["kind"] == "native" for r in path["rows"]) == path["native_commands"],
                "auth_native_schedule_drift")
        path["diagnostic_prepaid_consumed"] = sum(r["cost"] for r in path["rows"])
        path["diagnostic_reserved"] = diagnostic_contract["reserved_units"]
        path["counts_are_observed"] = False
    return dict(rows=rows, cases=list(auth_failure.CASES), diagnostic_paths=paths,
                diagnostic_contract=diagnostic_contract,
                diagnostic_binding=source("admission_ci.py", "Gate.run_components managed_costs=128"),
                diagnostic_reserved_all_cases=len(paths) * diagnostic_contract["reserved_units"],
                diagnostic_intended_prepaid_consumed=sum(p["diagnostic_prepaid_consumed"] for p in paths),
                native_slots=len(auth_failure.NATIVE_SLOTS),
                managed_operations=list(auth_failure.OPERATIONS),
                managed_costs_proven=False,
                normal_register_replacement_proven=False,
                reservation_expression="12 + create + login + logout + delete",
                classification="separate_local_diagnostic_not_release_cost_contract")


def normal_events(normal):
    """Local accounting, transport and validation are distinct boundaries.

    A successful precharge is not an SQL/HTTP confirmation. Workflow identity
    reservations are local checkpoints here, not 72 upfront HTTP dispatches.
    """
    from admission_budget import OUTCOMES
    events, seen = [], set()
    for row in normal["rows"]:
        group = row["charge_group"]
        spec = normal["charge_groups"][group]
        workflow = row["action"] == "gotrue_fixture_identity" or row["action"].startswith("gotrue_workflow_identity_")
        common = dict(owner_node=row["id"], phase=row["phase"], action=row["action"],
                      kind=row["kind"], charge_group=group, source=row["source"])
        if group not in seen:
            state = {k: v for k, v in row.get("state_after", {}).items() if v is True}
            state.update(spec.get("state_after_charge", {}))
            if row["action"].startswith("gotrue_") and row["action"].endswith("_issue"):
                state["auth_maybe_live"] = True
            binding = spec.get("accounting_source", row["source"])
            if group.startswith("cli_") or workflow or group in ("guard_install", "metadata_install"):
                binding = source("metered_composition.py", "workflow" if workflow else
                                 {"cli_quota": "apply_migration", "cli_pre_auth": "pre_auth_dry_run",
                                  "cli_final": "finalize"}.get(group, "before_sql"))
            events.append(dict(common, id="precharge:" + group, stage="precharge",
                               cost=spec["capacity"], outcomes=("confirmed", "rejected"),
                               state_after=state, workflow_prepaid=workflow,
                               source=binding, dispatch_attempted=False))
            seen.add(group)
        events.append(dict(common, id=row["id"], stage="normal", cost=0,
                           event_kind="local_reservation_checkpoint" if workflow else
                           "opaque_cli_envelope" if row["kind"] == "cli_reserved" else "dispatch",
                           outcomes=("confirmed", "interrupted") if workflow else OUTCOMES,
                           state_after={}, dispatch_count_proven=False))
        release = ({"controls": False} if row["action"] == "control_restored" else
                   {"guard": False, "observer": False} if row["action"] == "gates_final_post_metadata" else None)
        if release is not None:
            events.append(dict(common, id="validate:" + row["id"], stage="validation", cost=0,
                               outcomes=("confirmed", "rejected", "interrupted"), state_after=release,
                               source=source("integral_ci.py", "Composition.confirm_controls_restored"
                                             if "controls" in release else "Composition.final_metadata"),
                               dispatch_attempted=False))
    require(len({e["id"] for e in events}) == len(events), "normal_event_identity_collision")
    return events


def prefix_register(normal):
    from complete_register import safety_path
    state = dict(guard=False, observer=False, controls=False, claimed=False,
                 auth_maybe_live=False, guard_remove_attempted=False, observer_remove_attempted=False)
    prefixes, paths = [], {}
    used = 0
    closing = sum(spec["capacity"] for spec in normal["charge_groups"].values()
                  if spec["phase"] in ("cleanup", "final", "closure"))
    prepaid = 0

    def path_ref(value):
        commands = safety_path(**value)
        key = canonical_sha(commands)
        if key not in paths:
            paths[key] = dict(commands=commands, reference_capacity=sum(r["sql"] for r in commands),
                              classification="legacy_safety_not_full_partial_cleanup",
                              replacement_required_for_partial_auth=value["auth_maybe_live"],
                              required_component_suffixes=["fixture", "auth", "parent_orchestration"],
                              bound_complete=False)
        return key

    prefixes.append(dict(node=None, owner_node=None, stage="entry", outcome="entry", consumed_capacity=0,
                         normal_closing_unspent=closing, workflow_prepaid_consumed=0,
                         safety_path=path_ref(state), required_total=None, mutation_admitted=False))
    for event in normal_events(normal):
        charge = event["cost"]
        closing_charge = charge if event["phase"] in ("cleanup", "final", "closure") else 0
        workflow_charge = charge if event.get("workflow_prepaid") else 0
        confirmed = {**state, **event["state_after"]}
        for outcome in event["outcomes"]:
            accepted = outcome == "confirmed"
            suffix_state = confirmed if accepted else state
            prefixes.append(dict(node=event["id"], owner_node=event["owner_node"], stage=event["stage"],
                                 outcome=outcome, consumed_capacity=used + (charge if accepted else 0),
                                 normal_closing_unspent=closing - (closing_charge if accepted else 0),
                                 workflow_prepaid_consumed=prepaid + (workflow_charge if accepted else 0),
                                 state=dict(suffix_state),
                                 safety_path=path_ref(suffix_state),
                                 unknown_dispatch_refunded=False, required_total=None,
                                 mutation_admitted=False))
        used += charge
        closing -= closing_charge
        prepaid += workflow_charge
        state = confirmed
    require(used == normal["normal_capacity"] and closing == 0 and prepaid == 360,
            "prefix_precharge_accounting")
    return prefixes, paths


def fault_case_register(normal):
    import integral_failure_runtime as failures
    predicates = {
        "pre_migration": lambda r: r["id"] == "cli_quota_before_0",
        "post_migration": lambda r: r["id"] == "cli_quota_after_3",
        "mid_auth": lambda r: r["kind"] == "auth_reserved" and r["phase"] == "auth",
        "mid_controller": lambda r: r["phase"] == "controller",
        "mid_route_a": lambda r: r["phase"] == "route_a" and r["action"] == "call",
        "mid_route_b": lambda r: r["phase"] == "route_b" and r["action"] == "call",
        "mid_restore": lambda r: r["phase"] == "restore" and r["action"] == "call",
        "lost_reply": lambda r: r["action"] == "commit",
        "duplicate": lambda r: r["action"] == "call",
        "timeout": lambda r: r["action"] == "call",
        "partial_cleanup": lambda r: r["phase"] == "cleanup" and r["action"] == "call",
        "cleanup_failure": lambda r: r["phase"] == "cleanup" and r["action"] == "call",
        "final_check_failure": lambda r: r["action"] == "gates_final_post_metadata",
        "closure_failure": lambda r: r["action"] == "final_closure",
    }
    require(set(predicates) == set(failures.REQUIRED), "fault_registry_case_drift")
    return [dict(case=entry, candidate_anchors=[r["id"] for r in normal["rows"] if predicates[entry["id"]](r)],
                 source=source("integral_failure_runtime.py", "registry/Session"),
                 actual_boundary_invocations=2 if entry["id"] == "duplicate" else 1,
                 duplicate_test_is_not_zero_dispatch=entry["id"] == "duplicate",
                 full_source_adapter_bound=False, required_total=None)
            for entry in failures.registry()]


def timeout_component():
    import integral_failure_runtime as failures
    names = [("timeout_begin", "BEGIN TRANSACTION READ ONLY"), ("timeout_check", failures.CHECK),
             ("timeout", failures.TIMEOUT_SQL), ("terminal_rollback", "ROLLBACK"),
             ("snapshot_begin", "BEGIN TRANSACTION READ ONLY"), ("snapshot_check", failures.CHECK),
             ("snapshot", "SELECT count(*)::integer remaining_case_backends FROM pg_stat_activity WHERE pid = %s"),
             ("snapshot_rollback", "ROLLBACK")]
    return dict(rows=[sql_row("timeout_" + str(i), "safety", name, text,
                              "integral_failure_runtime.py", "TimeoutDriver/Session")
                      for i, (name, text) in enumerate(names)],
                expected_successful_negative_test_commands=8,
                diagnostic_allowance=failures.TimeoutDriver().describe()["cases"]["timeout"],
                extra_finally_rollback_possible=True,
                release_bound_proven=False, scope="standalone local timeout, not full workflow timeout")


def workflow_component(auth):
    """Compile the newly supplied rollback-isolated driver's named call sites.

    These are the intended negative-test paths. A failed prerequisite may stop
    earlier; unknown cleanup/close paths are not silently treated as successful.
    The matrix is a separate local diagnostic, not one hosted 2349 execution.
    """
    import integral_failure_runtime as rt
    import integral_failure_runtime_workflow as workflow
    from scenario import capture
    scenario = capture()
    actions = scenario["workflow_actions"]
    binding = source("integral_failure_runtime_workflow.py", "WorkflowDriver")

    def native(names):
        return [dict(action=name, cost=1, kind="native", source=binding) for name in names]

    setup = native(["workflow_begin", "workflow_limits", "workflow_fixture_barrier", "workflow_baseline"]
                   + [name for _ in range(3) for name in ("profile_fixture", "identity_fixture")]
                   + ["operator_fixture", "transaction_local_control", "bind_actual_session",
                      "existing_fixture_seed", "bind_actual_session", "existing_product_call"])
    observation = native(["snapshot_begin", "snapshot_check", "snapshot", "snapshot_rollback"])
    rollback = native(["terminal_rollback"])
    invoke = native(["bind_actual_session", "existing_product_call", "prefix_numeric"])

    def prepare_action(action):
        names = ["request_state", "request_proposals"]
        if action["request"]["action"] == "b_build":
            names += ["bind_actual_session", "existing_product_call"]
        return native(names)

    result = []
    auth_paths = {p["case"]: p for p in auth["diagnostic_paths"]}
    for case in workflow.SUPPORTED:
        managed = []
        if case == "timeout":
            rows = native(["timeout_begin", "timeout_check", "timeout"]) + rollback + observation
        elif case in ("mid_controller", "closure_failure"):
            ipc = ["controller_claim", "controller_close"] if case == "closure_failure" else [
                "controller_claim", "controller_before_measure", "controller_before",
                "controller_action_started", "controller_halt"]
            rows = native(["controller_begin", "controller_guard", "controller_absence"] + ipc
                          + ["controller_terminal_prefix"]) + rollback + observation
        elif case in ("mid_auth", "lost_reply"):
            key = "partial_session" if case == "mid_auth" else "create_lost_reply"
            path = auth_paths[key]
            rows = native(["delegated_" + key + "_native_" + str(i) for i in range(path["native_commands"])]) + observation
            managed = [dict(action=op, cost=None, kind="auth_reserved",
                            source=source("auth_failure.py", "Case.auth")) for op in path["http_actions"]]
        elif case in ("partial_cleanup", "cleanup_failure"):
            names = ["cleanup_owned_inventory", "cleanup_b_states"]
            if rt.MODES[case] != "before":
                names += ["cleanup_owned_inventory", "cleanup_requests" if case == "partial_cleanup" else "cleanup_windows"]
            rows = setup + native(names) + rollback + observation
        elif case == "final_check_failure":
            rows = setup + rollback + observation + observation
        else:
            target_name = "b_build" if case == "mid_route_b" else "restore" if case == "mid_restore" else "source_append"
            target = next(a for a in actions if a["request"]["action"] == target_name)
            rows = list(setup)
            if case == "mid_restore":
                for action in actions[:target["step"]]:
                    rows += prepare_action(action) + invoke
            rows += prepare_action(target) + invoke * (2 if case == "duplicate" else 1) + rollback + observation
        rows = copy.deepcopy(rows)
        for index, row in enumerate(rows):
            row["id"] = "component_" + case + "_" + str(index)
        result.append(dict(case=case, native_rows=rows, managed_rows=managed,
                           intended_native_commands=len(rows), total_capacity=None if managed else len(rows),
                           full_fault_prefix_bound=False, extra_finally_close_paths_unresolved=True,
                           includes_shared_actor_bootstrap=False, real_execution_proven=False))
    bootstrap = dict(actor_count=3, per_actor_native=10,
                     per_actor_managed_operations=["create", "login", "delete"],
                     per_actor_expression="10 + create + login + delete", total_capacity=None,
                     scope="Shared actor open/close once, separately counted; no diagnostic 128 substitution.")
    bootstrap["diagnostic_per_actor_rows"] = copy.deepcopy(auth_paths["partial_session"]["rows"])
    for row in bootstrap["diagnostic_per_actor_rows"]:
        row["source"] = source("integral_failure_runtime_workflow.py", "WorkflowDriver.open/close via auth_failure.Case")
    bootstrap["diagnostic_reserved_all_actors"] = 3 * auth["diagnostic_contract"]["reserved_units"]
    bootstrap["diagnostic_intended_prepaid_all_actors"] = 3 * sum(r["cost"] for r in bootstrap["diagnostic_per_actor_rows"])
    bootstrap["not_parent_fixture_bootstrap"] = True
    return dict(cases=result, bootstrap=bootstrap,
                source=source("integral_failure_runtime_workflow.py", "WorkflowDriver.open/close/run_case"),
                worker_source=source("integral_failure_runtime_worker.mjs", "IPC controller/closure"),
                scenario_source_sha256=scenario["source_sha256"],
                unsupported_migration_cases=["pre_migration", "post_migration"],
                separate_local_diagnostic=True, global_2349_proven=False)


def parent_bootstrap_component():
    """Read query call sites without opening the disposable environment."""
    import admission_fixture_context as parent
    tree = ast.parse((HERE / "admission_fixture_context.py").read_text())
    calls = sorted((n for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "query"), key=lambda n: n.lineno)
    labels = [ast.literal_eval(n.args[1]) for n in calls]
    require(labels == ["begin", "empty_registry", "actor_ownership", "register_owned", "operator_owned",
                       "commit", "after_begin", "after_readonly", "after_registry", "after_rollback",
                       "safety_rollback"], "parent_bootstrap_dispatch_shape_changed")
    rows = [sql_row("parent_bootstrap_" + label, "diagnostic", label, ast.literal_eval(call.args[2]),
                    "admission_fixture_context.py", "run") for label, call in zip(labels, calls)]
    return dict(rows=rows[:-1], failure_only=rows[-1:], normal_native_dispatches=10,
                diagnostic_cap=parent.LIMIT, actual_execution_observed=False,
                parent_environment_auth_setup_and_teardown_included=False,
                separate_local_diagnostic=True, hosted_run_capacity_changed=False,
                rollback_suffix_bound=1, full_parent_environment_bound=None)


def fixture_diagnostic_component(component):
    """Enumerate the CI driver's setup/writer/cleanup SQL, without running it."""
    import fixture_cleanup_runtime_ci as ci
    import fixture_cleanup_runtime_sql as sql
    context = {key: str(uuid.uuid4()) for key in ("window", "a", "b")}
    ids = {key: str(uuid.uuid4()) for key in ci.ROLES}
    templates = ci.inserts(context, ids)

    def row(label, text):
        return sql_row("fixture_diagnostic_" + label, "diagnostic", label, text,
                       "fixture_cleanup_runtime_ci.py", "run/inserts")

    setup = [row("prerequisite", sql.CHECK), row("identity_registry", ci.REGISTRY),
             row("protected_before", ci.PROTECTED)]
    closing = [row("protected_after", ci.PROTECTED)]
    groups = component["groups"]
    cleanup = groups["normal"]
    absence = next(i for i, r in enumerate(cleanup) if r["action"] == "absence_begin")
    cases = []
    names = ("full", "partial", "parent_only", "dependent_without_workspace", "zero", "lost_writer_commit",
             "missing_barrier", "foreign_row", "lost_commit", "interrupted_delete", "lock_timeout")
    for name in names:
        selected = templates
        if name in ("partial", "parent_only", "dependent_without_workspace", "zero"):
            selected = templates[:3] if name == "partial" else templates[:1] if name == "parent_only" else (
                [templates[0], templates[-1]] if name == "dependent_without_workspace" else [])
        rows = list(groups["prepare"])
        if selected:
            rows += [row(name + "_writer_begin", "BEGIN")]
            rows += [row(name + "_insert_" + table, text) for table, text, _ in selected]
            if name != "foreign_row":
                rows += groups["per_writer_transaction"]
            rows += [row(name + "_writer_commit", "COMMIT")]
        if name == "lock_timeout":
            rows += [row("fault_locker_begin", "BEGIN"),
                     row("fault_locker_lock", "LOCK TABLE fmz6e11_private.windows IN ROW EXCLUSIVE MODE")]
        if name == "missing_barrier":
            pass  # Source rejects before any cleanup dispatch.
        elif name in ("foreign_row", "interrupted_delete", "lock_timeout"):
            action = {"foreign_row": "inventory", "interrupted_delete": "delete_events", "lock_timeout": "barrier"}[name]
            stop = next(i for i, r in enumerate(cleanup) if r["action"] == action)
            rows += cleanup[:stop + 1] + groups["failure_only"] + cleanup[absence:]
        else:
            rows += cleanup
        if name == "lock_timeout":
            rows += [row("fault_locker_rollback", "ROLLBACK")]
        rows = copy.deepcopy(rows)
        for index, command in enumerate(rows):
            command["id"] = "fixture_diagnostic_" + name + "_" + str(index)
        cases.append(dict(case=name, rows=rows, intended_native_commands=len(rows),
                          observed_execution=False, full_unexpected_fault_bound=False))
    return dict(setup=setup, cases=cases, closing=closing,
                intended_protocol_commands=len(setup) + sum(len(c["rows"]) for c in cases) + len(closing),
                includes_parent_bootstrap=False, includes_parent_auth_environment=False,
                separate_local_diagnostic=True, full_bound=None,
                source=source("fixture_cleanup_runtime_ci.py", "run"))


def assemble(folder=REFERENCE):
    normal = assemble_normal(folder)
    fixture = fixture_component(normal["rows"])
    auth = auth_component()
    missing = [
        dict(id="normal_source_revalidation", owner="Main", inputs=[
            "Retained native SQL/template identity against current executor and fresh disposable binding.",
            "Current same-source trace including upfront workflow 360 precharge."]),
        dict(id="cli_predispatch", owner="Role1", inputs=[
            "Ordered quota/pre_auth/final dispatch rows and exact protocol costs, including failed startup/reconnect.",
            "Per-dispatch unknown/timeout/duplicate suffix and observer order; reservations are not counts."]),
        dict(id="auth_partial_costs", owner="Role2", inputs=[
            "Source-bound measured create/login/logout/delete costs and stopping-prefix schedules.",
            "Map partial cleanup to existing issue/verify/getUser/refresh/logout/revoked_denial identities."]),
        dict(id="fixture_placement", owner="Role3/Main", inputs=[
            "Prepare before first fixture write; capture at each owned writer transaction before COMMIT.",
            "Explicitly additive versus replacement normal cleanup and parent failure ordering.",
            "Writer/mint barrier and ownership evidence must survive unknown commit."]),
        dict(id="recovery_orchestration", owner="Role4/Main", inputs=[
            "All real phase adapters, with command lists for cleanup/final/closure failures.",
            "No duplicated rollback, existing safety Auth, or prepaid 130 cleanup slots."]),
    ]
    prefixes, safety_paths = prefix_register(normal)
    sources = {name: digest(HERE / name) for name in (
        "admission_budget.py", "admission_budget_register.py", "admission_binding.py",
        "complete_register.py", "metered_composition.py", "registered_lifecycle.py", "integral_ci.py", "integral_io.py",
        "lifecycle_gates.py", "cli_envelope.py", "cli_meter.py", "cli_stat_reader.py", "auth_failure.py",
        "auth_failure_transport.py", "fixture_cleanup_runtime.py", "fixture_cleanup_runtime_sql.py",
        "integral_failure_runtime.py", "integral_failure_runtime_workflow.py",
        "integral_failure_runtime_worker.mjs", "fixture_cleanup_runtime_ci.py",
        "fixture_cleanup_evidence.py", "sql_protocol.py", "native_runtime.py",
        "admission_fixture_context.py", "admission_ci.py", "admission_journal.py",
        "admission_budget_graph.py", "admission_budget_receipts.py",
        "migration_failure_boundaries.py", "test_migration_failure_boundaries.py") + CLI_SOURCE_FILES}
    sources["_offline/phase6e_server_v1/cli_isolation.py"] = digest(
        HERE.parents[1] / "phase6e_server_v1" / "cli_isolation.py")
    sources["_offline/phase6e_server_v1/ci_profile.py"] = digest(
        HERE.parents[1] / "phase6e_server_v1" / "ci_profile.py")
    report = dict(status="NO_GO_INCOMPLETE_BOUND", preparation_run_id=NEW_RUN,
                source_hashes=sources, approved_limit=APPROVED, minimal_cap=None,
                normal_register=normal, fault_prefixes=prefixes, reference_safety_paths=safety_paths,
                fault_cases=fault_case_register(normal),
                components=dict(fixture=fixture, auth=auth, timeout=timeout_component(),
                                workflow=workflow_component(auth),
                                parent_bootstrap=parent_bootstrap_component(),
                                fixture_diagnostic=fixture_diagnostic_component(fixture)), unresolved_inputs=missing,
                bound_complete=False, hosted_admitted=False, executable=False,
                historical_reference_read_only=True, new_component_costs_silently_added=False,
                scope="Concrete ordered reference reconciliation plus actual component contracts; not full-chain evidence.")
    from admission_budget_graph import assemble_graph
    report["command_graph"] = assemble_graph(report)
    def check_bindings(value):
        if isinstance(value, dict):
            if value.get("path") in sources and "sha256" in value:
                require(value["sha256"] == sources[value["path"]], "assembly_source_changed:" + value["path"])
            for child in value.values():
                check_bindings(child)
        elif isinstance(value, list):
            for child in value:
                check_bindings(child)
    check_bindings(report)
    return report


def export(report, section="all", phase=None):
    """Split stdout receipts by phase without filesystem writes or lost binding."""
    require(section in ("all", "summary", "normal", "faults", "components", "graph"), "export_section")
    require(phase is None or phase in PHASE_BUDGETS, "export_phase")
    require(phase is None or section in ("normal", "faults", "graph"), "phase_requires_normal_or_faults")
    if section == "all":
        return report
    nodes = report["normal_register"]["rows"]
    selected = {r["id"] for r in nodes if phase is None or r["phase"] == phase}
    if section == "normal":
        content = [r for r in nodes if r["id"] in selected]
    elif section == "faults":
        content = [r for r in report["fault_prefixes"] if r["owner_node"] in selected
                   or phase is None and r["node"] is None]
    elif section == "components":
        content = report["components"]
    elif section == "graph":
        content = copy.deepcopy(report["command_graph"])
        if phase is not None:
            content["nodes"] = {k: v for k, v in content["nodes"].items()
                                if v.get("owner_node") in selected or v["stage"] not in ("normal", "precharge", "validation")}
            content["external_next_nodes"] = sorted({edge["to"] for n in content["nodes"].values()
                for edge in n["next"].values() if edge["to"] not in content["nodes"]
                and edge["to"] not in content["terminals"]})
    else:
        content = {k: v for k, v in report.items() if k not in ("normal_register", "fault_prefixes", "components", "command_graph")}
        content["graph"] = {k: v for k, v in report["command_graph"].items() if k not in ("nodes", "diagnostic_graphs")}
        content["normal"] = {k: v for k, v in report["normal_register"].items() if k not in ("rows", "charge_groups")}
        content["row_count"] = len(nodes)
        content["fault_prefix_count"] = len(report["fault_prefixes"])
    return dict(status=report["status"], full_register_sha256=canonical_sha(report),
                preparation_run_id=NEW_RUN, section=section, phase=phase, content=content,
                source_hashes=report["source_hashes"], minimal_cap=None, hosted_admitted=False)
