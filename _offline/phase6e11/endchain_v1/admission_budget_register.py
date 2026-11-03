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
import types
import uuid

from admission_binding import NEW_RUN
from admission_budget import HERE, PHASE_BUDGETS, APPROVED, digest, require

REFERENCE = HERE / "receipts" / "reserved-ci-39109482869"
REFERENCE_SHA = "5061786166c8bd153fdc333a708636a1d0f7c538e6b7a5d3aea2f359f9778da1"
CLI_SOURCE_FILES = tuple("cli_predispatch/" + name for name in (
    "ci.py", "entry.mjs", "hook.cjs", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    "policy.cjs", "prepare.py", "README.md", "smoke.py", "test_ci.py", "test_hook.cjs", "test_policy.cjs",
    "pending.py", "test_pending.py", "test_canonical.py"))


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source(name, symbol):
    path = (HERE / name).resolve()
    key = path.relative_to(HERE.parents[2]).as_posix() if name.startswith("../") else name
    return dict(path=key, sha256=digest(path), symbol=symbol)


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
    return [dict(sql_row(prefix + "_" + str(i), "final", prefix + "_" + action,
                    text, "integral_ci.py", "Composition.final_metadata"),
                 action_binding={"kind": "lifecycle", "operation": "remove"})
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


def workflow_capture():
    """Load this register's source pair without a cached checkout module or pyc."""
    root = HERE.resolve().parents[2]
    paths = (HERE / 'scenario.py', root / '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py')
    from admission_module_binding import checked_path
    for path in paths:
        require(checked_path(path).is_relative_to(root), 'budget_scenario_path')
    before = [path.read_bytes() for path in paths]
    module = types.ModuleType('_budget_bound_scenario')
    module.__file__ = str(paths[0])
    exec(compile(before[0], module.__file__, 'exec'), module.__dict__)
    require(module.ROOT == root and module.SOURCE == paths[1], 'budget_scenario_origin')
    value = module.capture()
    require(all(path.read_bytes() == raw for path, raw in zip(paths, before)),
            'budget_scenario_changed_during_capture')
    require(value.get('status') == 'OFFLINE_SCENARIO_CAPTURE_ONLY'
            and value.get('placeholder_only') is True and value.get('hosted_calls') == 0
            and len(value.get('workflow_actions', [])) == 45
            and value.get('source_sha256') == hashlib.sha256(before[1]).hexdigest(),
            'budget_scenario_contract')
    return value


def workflow_component(auth):
    """Compile the newly supplied rollback-isolated driver's named call sites.

    These are the intended negative-test paths. A failed prerequisite may stop
    earlier; unknown cleanup/close paths are not silently treated as successful.
    The matrix is a separate local diagnostic, not one hosted 2349 execution.
    """
    import integral_failure_runtime as rt
    import integral_failure_runtime_workflow as workflow
    scenario = workflow_capture()
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
    import fixture_control_ownership as control
    require(control.CONTROL_LIMIT == 5, "negative_control_cost_contract_drift")
    context = {key: str(uuid.uuid4()) for key in ("window", "a", "b")}
    ids = {key: str(uuid.uuid4()) for key in ci.ROLES}
    templates = ci.inserts(context, ids)

    def row(label, text):
        return sql_row("fixture_diagnostic_" + label, "diagnostic", label, text,
                       "fixture_cleanup_runtime_ci.py", "run/inserts")

    def witness(label, text):
        return sql_row("negative_control_" + label, "diagnostic", label, text,
                       "fixture_control_ownership.py", "NegativeControl.capture/check_after_case")

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
            else:
                rows += [witness("foreign_row_parent_ownership", sql.INVENTORY)]
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
        if name == "foreign_row":
            rows += [witness(label, text) for label, text in (
                ("foreign_row_parent_check_begin", "BEGIN TRANSACTION READ ONLY"),
                ("foreign_row_parent_check_limits", sql.CHECK),
                ("foreign_row_parent_check_inventory", sql.INVENTORY),
                ("foreign_row_parent_check_rollback", "ROLLBACK"))]
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
                negative_control_additional_commands=control.CONTROL_LIMIT,
                negative_control_original_claim_promoted=False,
                separate_local_diagnostic=True, full_bound=None,
                source=source("fixture_cleanup_runtime_ci.py", "run"))


def opt_in_diagnostics(fixture, diagnostic, auth):
    """Additional local protocol templates, never an increase to the run limit."""
    import fixture_db_terminality as db
    import fixture_parent_closure as parent
    import fixture_cleanup_runtime_sql as sql
    require((db.MAX_CONNECTIONS, db.TERMINAL_LIMIT, db.ZERO_LIMIT, db.MAX_ZERO_CASES)
            == (64, 2, 5, 11), "tracked_db_contract_drift")
    require(parent.CASE_LIMIT == 22 and parent.REGISTRY_LIMIT == 11, "parent_suffix_contract_drift")

    def rows(prefix, pairs, filename, symbol):
        return [sql_row(prefix + "_" + label, "diagnostic", label, text, filename, symbol)
                for label, text in pairs]

    registration = rows("tracked", [("register", db.REGISTER)], "fixture_db_terminality.py", "TrackedRuntime.connect")
    terminal = rows("tracked", [("observer_identity", db.SESSION), ("backend_absence", db.ACTIVITY)],
                    "fixture_db_terminality.py", "TrackedRuntime.terminal/_activity")
    zero = rows("tracked", [("zero_begin", "BEGIN TRANSACTION READ ONLY"), ("zero_session", db.SESSION),
        ("backend_absence", db.ACTIVITY), ("zero_inventory", sql.INVENTORY), ("zero_rollback", "ROLLBACK")],
        "fixture_db_terminality.py", "TrackedRuntime.physical_zero/_activity")
    # Each anchor follows a successful factory connect, before the first business query.
    connections = [dict(case="setup", before=diagnostic["setup"][0]["id"])]
    for case in diagnostic["cases"]:
        for row in case["rows"]:
            if row["action"] in ("prepare_begin", "begin", "absence_begin", "fault_locker_begin",
                                 "foreign_row_parent_check_begin", case["case"] + "_writer_begin"):
                connections.append(dict(case=case["case"], before=row["id"]))
    connections.append(dict(case="closing", before=diagnostic["closing"][0]["id"]))
    require(len(connections) == 45, "tracked_fixture_connect_schedule_drift")
    registry = rows("parent", [("registry_begin", "BEGIN"), ("registry_check", sql.CHECK),
        ("registry_lock", parent.REGISTRY_LOCK), ("registry_before", parent.REGISTRY),
        ("registry_delete_operator", parent.DELETE_OPERATOR), ("registry_delete_identities", parent.DELETE_IDENTITIES),
        ("registry_commit", "COMMIT"), ("registry_absence_begin", "BEGIN TRANSACTION READ ONLY"),
        ("registry_check_after", sql.CHECK), ("registry_absence", parent.REGISTRY),
        ("registry_absence_rollback", "ROLLBACK")], "fixture_parent_closure.py", "close_registry")
    registry[8]["action"] = "registry_check"
    rollback = rows("parent", [("registry_rollback", "ROLLBACK")], "fixture_parent_closure.py", "close_registry")
    registry_faults = []
    for index, row in enumerate(registry):
        suffix = rollback + registry[7:] if index < 6 else registry[7:] if index == 6 else []
        registry_faults.append(dict(at=row["id"], outcome="unknown_after_precharge", spent=index + 1,
            suffix=[r["id"] for r in suffix], total=index + 1 + len(suffix), retry=False))
    reconciliation = []
    for case in ("admin_unknown", "cleanup_interrupted", "missing_mint_barrier"):
        labels = ["observe"] if case != "cleanup_interrupted" else [
            "observe", "stats_before_delete", "delete", "stats_after_delete", "verify_zero"]
        commands = [dict(id="reconcile_" + case + "_" + label, action=label,
            kind="auth_reserved" if label == "delete" else "native", cost=128 if label == "delete" else 1,
            source=source("auth_failure.py", "ReconciliationJournal/reconcile_retained")) for label in labels]
        original = next(p for p in auth["diagnostic_paths"] if p["case"] == case)
        required = sum(r["cost"] for r in commands)
        require(required <= original["diagnostic_reserved"] - original["diagnostic_prepaid_consumed"],
                "reconciliation_original_reserve_exceeded")
        reconciliation.append(dict(case=case, rows=commands, diagnostic_capacity=required,
            original_reservation=original["diagnostic_reserved"], additional_reservation=0,
            eligibility="retained eligible receipt, complete measurements and unused original reservation",
            delete_requires="previously unsent, terminal mint barrier, unchanged owned scope",
            original_claim_released=False, managed_release_cost=None, journal_durability_verified=False))
    return dict(separate_local_diagnostic=True, observed_execution=False, hosted_run_capacity_changed=False,
        command_scope="Explicit top-level SQL only; connection/startup and nested managed SQL not inferred.",
        native_startup_protocol_bound=None, journal_file_io_sql_commands=0,
        tracked_db=dict(registration_rows=registration, terminal_rows=terminal, physical_zero_rows=zero,
            registration_anchors=connections, intended_component_registrations=len(connections),
            component_additional_protocol_commands=len(connections) + len(terminal),
            connection_limit=db.MAX_CONNECTIONS, terminal_limit=db.TERMINAL_LIMIT,
            zero_limit_per_case=db.ZERO_LIMIT, maximum_zero_cases=db.MAX_ZERO_CASES,
            additional_expression="successful_registration_attempts + terminal_attempts + physical_zero_attempts",
            registration_before_component_not_counted_twice=True,
            physical_zero_faults=[dict(at=row["id"], spent=i + 1,
                suffix=[zero[-1]["id"]] if i < 4 else [], total=i + 2 if i < 4 else 5,
                retry=False) for i, row in enumerate(zero)],
            zero_requires="durable tracked terminality and immutable scoped unknown-COMMIT receipt",
            close_is_not_server_terminality=True, auth_barrier_proven=False,
            registry_cleanup_admitted=False, original_claims_released=False,
            source=source("fixture_cleanup_runtime_ci.py", "run/finish/observe_terminal")),
        parent_closure=dict(case_rows=copy.deepcopy(fixture["groups"]["normal"]),
            case_faults=copy.deepcopy(fixture["fault_paths"]), registry_rows=registry,
            registry_failure_only=rollback, registry_faults=registry_faults,
            per_eligible_case_limit=parent.CASE_LIMIT, registry_limit=parent.REGISTRY_LIMIT,
            planned_limit_expression="22 * eligible_cases + (11 if no_unresolved_cases else 0)",
            original_unknown_commit_replayed=False, tracked_factory_used=False,
            barrier_required=["worker_joined", "writers_closed", "mint_barrier"],
            registry_requires="every case resolved and exact committed bootstrap ownership",
            source=source("fixture_parent_closure.py", "run/ownership/close_registry")),
        auth_reconciliation=reconciliation,
        auth_transport=dict(source=source("auth_failure_transport.py", "LocalTransport.request/complete_body"),
            upstream_requests_per_call=1, automatic_retry=False, extra_sql_dispatched_by_relay=0,
            framing_is_not_managed_sql_bound=True, full_normal_transport_mapping_proven=False),
        full_bound=None, minimal_cap=None)


def normal_dispatch_mapping(normal):
    """Reusable expected trace keys, not a new replay of a historical executor."""
    mapping = []
    for row in normal["rows"]:
        if row.get("optional_capacity_only", False):
            stream = "optional_stream_capacity_not_dispatch"
        elif row["id"].startswith("cli_"):
            stream = "cli_protocol_slot"
        elif row["kind"] == "auth_reserved":
            stream = "workflow_auth_protocol" if row["action"].startswith((
                "gotrue_workflow_identity_", "gotrue_fixture_identity")) else "auth_protocol_operation"
        elif row["phase"] == "preflight":
            stream = "integral_preflight"
        else:
            stream = "integral_complete_protocol_trace"
        key = dict(action=row["action"], action_binding=row.get("action_binding", {}),
                   sql_sha256=row.get("sql_sha256"))
        mapping.append(dict(row_id=row["id"], register_ordinal=row["ordinal"], stream=stream,
            expected=key, phase=row["phase"], charge_group=row["charge_group"],
            matching_current_dispatch_observed=False))
    return dict(rows=mapping, source=source("integral_ci.py", "Composition.before_sql/after_sql"),
        meter_source=source("metered_composition.py", "before_sql/workflow/auth_before/auth_after"),
        dispatch_sources=[source("session_transport.mjs", "createProtocolSessionTransport/query/invoke/read"),
            source("integral_workflow.mjs", "execution.fetcher/private SQL IPC"),
            source("fixture_lifecycle.py", "perform"),
            source("registered_lifecycle.py", "_dispatch/parent_auth_cleanup/close_temporary")],
        concrete_gaps=[
            dict(stream="integral_complete_protocol_trace",
                 needed="Ordered phase/action/sql_sha256 plus confirmed flags; retain fresh-binding differences, never normalize UUIDs blindly."),
            dict(stream="workflow_auth_protocol",
                 needed="72 /user dispatch identities (seed plus steps 0..70) joined to 72 upfront tickets; aggregate 360 is not a dispatch trace."),
            dict(stream="auth_protocol_operation",
                 needed="18 role/operation receipts for issue, verify, getUser, refresh, logout, revoked_denial; diagnostic create/login/delete are not substitutes."),
            dict(stream="cli_protocol_slot",
                 needed="Quota/pre_auth/final attempt and numeric ledgers joined once to 72/36/36 reservations; app0/2 apply receipts do not fill dry-run slots."),
            dict(stream="fixture_capture",
                 needed="Prepare4 before first write; capture1 at every listed commit anchor; choose additive vs replacement of existing 123-delete workflow."),
            dict(stream="recovery",
                 needed="Per-connection finally rollback and control recovery, parent Auth, exact removal and final close ordering; no replay of spent cleanup tickets.")],
        current_source_revalidated=False, complete_dispatch_bound=False)


def rollback_dispatch_mapping():
    """A setup transaction is not the separate identity-lock connection."""
    from complete_register import safety_path
    tree = ast.parse((HERE / "integral_ci.py").read_text())
    workflow = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "workflow")
    channels = [ast.literal_eval(n.iter) for n in ast.walk(workflow) if isinstance(n, ast.For)
                and isinstance(n.target, ast.Name) and n.target.id == "channel" and isinstance(n.iter, ast.Tuple)]
    require(channels == [("setup", "writer", "reader", "workflow")], "workflow_connection_shape_drift")
    allowed = {r["action"]: r["sql"] for r in safety_path() if r["action"].startswith("rollback_")}
    requested = ["rollback_" + channel for channel in channels[0]] + ["rollback_auth_lock"]
    rows = []
    for label in requested:
        row = sql_row(label, "safety", label, "ROLLBACK", "registered_runner.py" if label == "rollback_auth_lock"
                      else "integral_ci.py", "IdentitySession.close" if label == "rollback_auth_lock"
                      else "Composition.workflow/finally")
        row.update(reserved_capacity=allowed.get(label), source_dispatch_cost=1,
                   status="MAPPED_EXISTING_LABEL" if label in allowed else "MISSING_SAFETY_LABEL_AND_COST",
                   equivalent_alias=None, condition="connection transaction_status != 0; one attempted rollback")
        rows.append(row)
    return dict(rows=rows, missing_labels=[r["action"] for r in rows if r["reserved_capacity"] is None],
        missing_conditional_commands=sum(r["cost"] for r in rows if r["reserved_capacity"] is None),
        lifecycle_inner_rollback=source("fixture_lifecycle.py", "perform/except BaseException"),
        inner_and_finally_deduplicated=False,
        reason="setup is created separately from IdentitySession; lifecycle_rollback may fail before finally. No alias or replay credit.",
        runtime_source=source("runtime_budget.py", "RuntimeBudget.safety"),
        safety_source=source("complete_register.py", "safety_path"),
        reference_modified=False, approved_limit_changed=False, full_required_capacity=None)


def parent_auth_finalizer_component(delete_costs):
    """Compile B's actual one-shot order; explicit local costs, no HTTP execution."""
    import auth_failure_parent_finalizer as parent
    from auth_protocol import STATS
    plan = parent.plan(delete_costs)
    tree = ast.parse((HERE / "auth_failure.py").read_text())
    backend = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RealBackend")
    snapshot = next(n for n in backend.body if isinstance(n, ast.FunctionDef) and n.name == "snapshot")
    literals = [ast.literal_eval(n.value) for n in snapshot.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "sql" for t in n.targets)]
    require(len(literals) == 1 and isinstance(literals[0], str), "parent_auth_snapshot_template_drift")
    rows = []
    def native(label, text, filename, symbol):
        rows.append(sql_row("parent_auth_" + label, "diagnostic", label, text, filename, symbol))
    native("boundary", parent.BOUNDARY, "auth_failure_parent_finalizer.py", "finalize/BOUNDARY")
    native("fk_before", parent.FK, "auth_failure_parent_finalizer.py", "finalize/fk")
    for role in parent.ROLES:
        native(role + ":before", literals[0], "auth_failure.py", "RealBackend.snapshot")
    for role in parent.ROLES:
        native(role + ":stats_before_delete", "select " + STATS + " value", "auth_failure.py", "RealBackend.stats")
        rows.append(dict(id="parent_auth_" + role + ":delete", phase="diagnostic", action=role + ":delete",
            cost=delete_costs[role], kind="auth_reserved", method="DELETE", path="/admin/users/{owned_subject}",
            source=source("auth_failure_parent_finalizer.py", "finalize/ledger.before/delete_owned"),
            transport_source=source("auth_failure_tracked.py", "TrackedAuth.delete_owned/existing_prepaid"),
            second_transport_charge=0, observed_managed_cost=None, execution_ready=False))
        native(role + ":stats_after_delete", "select " + STATS + " value", "auth_failure.py", "RealBackend.stats")
        native(role + ":after", literals[0], "auth_failure.py", "RealBackend.snapshot")
    native("fk_after", parent.FK, "auth_failure_parent_finalizer.py", "finalize/fk")
    for role in parent.ROLES:
        native(role + ":final", literals[0], "auth_failure.py", "RealBackend.snapshot")
    require([r["action"] for r in rows if r["kind"] == "native"] == list(parent.NATIVE),
            "parent_auth_native_dispatch_order_drift")
    require({r["action"]: r["cost"] for r in rows} == plan["charges"], "parent_auth_charge_plan_drift")
    faults, consumed = [], 0
    for i, row in enumerate(rows):
        consumed += row["cost"]
        suffix = rows[i + 1:i + 3] if row["kind"] == "auth_reserved" else (
            rows[i + 1:i + 2] if row["action"].endswith(":stats_after_delete") else [])
        faults.append(dict(at=row["id"], outcome="unknown_after_precharge", consumed_capacity=consumed,
            suffix=[r["id"] for r in suffix], required_capacity=consumed + sum(r["cost"] for r in suffix),
            retry=False, refunds=0, later_role_delete_admitted=False))
    require(consumed == plan["reserved_units"], "parent_auth_total_drift")
    return dict(rows=rows, fault_paths=faults, plan=plan, native_commands=plan["native_sql_maximum"],
        http_maximum=plan["http_maximum"], diagnostic_capacity=plan["reserved_units"],
        preconditions=["same live three-owner registry seal", "sealed scoped C closure and FK absence",
                       "tracked DB terminality", "durable original ownership and source binding"],
        separate_local_diagnostic=True, hosted_reference_changed=False, actual_execution_observed=False,
        full_bound_proven=False, managed_release_costs_proven=False,
        source=source("auth_failure_parent_finalizer.py", "plan/finalize"))


PLAN_VERSION = "admission-current-plan-v2"
PREVIOUS_CHECKPOINT = {
    "admission_budget_register.py": "724a390459129affee71cdc938ab45e5b20845d8e68b9baf18ede89eeac30d12",
    "admission_budget_register_test.py": "f4ab0f8b473135890e15e65c052001732304bec43905c3a580bd2cb0a0aead34",
    "admission_budget_receipts.py": "3fce0c862b9d54ca82a7a4e563a600a295f7d2247e00c0d1c1f22963783fb13e",
    "admission_budget_receipts_test.py": "e39ef098a77252d7f2b5e43e6ebf53ad5d9f4c19756cf5a9ebd0dcfa1e26dc71",
}
REMOVAL_SOURCES = {"observer": "../auth_metadata_v1/audit.py", "guard": "../controller_guard_v1/guard.py"}


def _method(filename, name, cls=None):
    tree = ast.parse((HERE / filename).read_text())
    if cls:
        tree = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def current_final_rows(stage):
    """Static extraction of the current fresh QueryIO path, never call the executor."""
    require(stage in ("pre", "post"), "plan_final_stage")
    from integral_io import SNAPSHOT
    from lifecycle_gates import FINAL
    from sql_protocol import statements
    method = _method("integral_ci.py", "final_metadata", "Composition")
    monitor_calls = sorted([n for n in ast.walk(method) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "monitor"], key=lambda n:n.lineno)
    require([n.func.attr for n in monitor_calls] == ["start", "bind", "executed", "close"],
            "plan_final_monitor_order_drift")
    pre = next(n for n in method.body if isinstance(n, ast.If) and ast.unparse(n.test) == "stage == 'pre'")
    def text(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if ast.unparse(node) in ("SNAPSHOT", "sql", "gates.FINAL"):
            return SNAPSHOT if ast.unparse(node) == "SNAPSHOT" else FINAL
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return text(node.left) + text(node.right)
        raise ValueError("plan_final_sql_expression_drift")
    def io_query(name):
        calls = [n for n in ast.walk(_method("integral_io.py", name, "QueryIO"))
                 if isinstance(n, ast.Call) and ast.unparse(n.func) == "self.query"]
        require(len(calls) == 1, "plan_io_query_shape:" + name)
        return ast.literal_eval(calls[0].args[1]), text(calls[0].args[2])
    calls = sorted([n for n in ast.walk(method) if isinstance(n, ast.Call)
        and (ast.unparse(n.func) in ("monitor.start", "monitor.bind", "monitor.close")
             or ast.unparse(n.func) == "query" and isinstance(n.args[0], ast.BinOp)
             and isinstance(n.args[0].right, ast.Constant))], key=lambda n:(n.lineno, n.col_offset))
    require([ast.unparse(n.func) for n in calls] ==
        ["query", "query", "query", "monitor.start", "monitor.bind", "query", "monitor.close", "query"],
        "plan_final_call_order_drift")
    # Validate the expanded fresh-monitor call edges against their actual AST.
    for method_name, expected in (("start", ["self.query", "self.sample"]),
                                  ("bind", ["self.query", "self.sample"]),
                                  ("checkpoint", ["self.sample"]),
                                  ("close", ["self.checkpoint", "self.query"])):
        found = sorted([n for n in ast.walk(_method("integral_io.py", method_name, "QueryIO"))
            if isinstance(n, ast.Call) and ast.unparse(n.func) in
            ("self.query", "self.sample", "self.checkpoint")], key=lambda n:n.lineno)
        require([ast.unparse(n.func) for n in found] == expected, "plan_io_call_order_drift:" + method_name)
    pairs = []
    for call in calls:
        if stage == "post" and pre.lineno <= call.lineno <= pre.end_lineno:
            continue
        name = ast.unparse(call.func)
        if name == "query":
            pairs.append((ast.literal_eval(call.args[0].right).lstrip("_"), text(call.args[1])))
        elif name == "monitor.start":
            pairs.extend((io_query("start"), io_query("sample")))
        elif name == "monitor.bind":
            require(ast.unparse(call.args[0]) == "gates.FINAL", "plan_final_bind_drift")
            pairs.extend((io_query("bind"), io_query("sample")))
        else:
            pairs.extend((io_query("sample"), io_query("close")))
    rows = []
    for i, (label, sql) in enumerate(pairs):
        parsed = statements(sql)
        require(len(parsed) == 1, "plan_final_single_dispatch")
        row = sql_row("gates_final_" + stage + "_" + str(i), "final", "gates_final_" + stage + "_" + label,
                      parsed[0]["sql"], "integral_ci.py", "Composition.final_metadata")
        row.update(action_binding={"kind": "lifecycle", "operation": "remove"},
                   derivation="AST_call_order_and_PG17_statement_parser",
                   dependencies=[source("integral_io.py", "QueryIO.start/bind/checkpoint/close"),
                                 source("lifecycle_gates.py", "FINAL")])
        rows.append(row)
    require(len(rows) == (11 if stage == "pre" else 9), "plan_final_dispatch_count_drift")
    return rows


def current_removal_rows():
    """Eight fixed statements and two receipt-bound DO templates, no invented hashes."""
    from sql_protocol import statements
    method = _method("registered_lifecycle.py", "close_temporary", "RegisteredLifecycle")
    loop = next(n for n in method.body if isinstance(n, ast.For))
    require([n.elts[0].value for n in loop.iter.elts] == ["audit", "guard"], "plan_removal_order_drift")
    rows = []
    for owner, filename in REMOVAL_SOURCES.items():
        remove = _method(filename, "remove")
        templates = [n.value for n in remove.body if isinstance(n, ast.Return)]
        require(len(templates) == 1 and isinstance(templates[0], ast.JoinedStr), "plan_removal_template_drift")
        fields, parts = {}, []
        for part in templates[0].values:
            if isinstance(part, ast.Constant):
                parts.append(part.value)
            else:
                require(isinstance(part, ast.FormattedValue) and part.conversion == -1 and part.format_spec is None,
                        "plan_removal_format_drift")
                token = "__budget_binding_%d__" % len(fields)
                fields[token] = ast.unparse(part.value)
                parts.append(token)
        parsed = statements("".join(parts))
        require(len(parsed) == 5 and [r["kind"] for r in parsed] ==
                ["TransactionStmt", "VariableSetStmt", "VariableSetStmt", "DoStmt", "TransactionStmt"],
                "plan_removal_statement_shape")
        for i, statement in enumerate(parsed):
            row = sql_row("current_remove_" + owner + "_" + str(i), "final", "remove", statement["sql"],
                          filename, "remove")
            inputs = {token: expression for token, expression in fields.items() if token in statement["sql"]}
            row.update(owner=owner, statement_index=i, action_binding={"kind": "lifecycle", "operation": "remove"},
                template_sha256=statement["sha256"], binding_inputs=inputs, binding_required=bool(inputs),
                sql_sha256=None if inputs else statement["sha256"],
                ordering_source=source("registered_lifecycle.py", "close_temporary"))
            rows.append(row)
    return rows


def current_plan(report):
    """Executable offline comparison/reservation model, never hosted authority."""
    normal = copy.deepcopy(report["normal_register"])
    finals = {r["id"]: r for stage in ("pre", "post") for r in current_final_rows(stage)}
    removes = iter(current_removal_rows())
    derived = []
    for row in normal["rows"]:
        new = next(removes) if row["action"] == "remove" else finals.get(row["id"])
        if new is not None:
            # Keep event/group identities, but never the old receipt-bound SQL hash.
            row.update({k:v for k,v in new.items() if k not in ("id", "retained_ids")})
            row["derivation_id"] = new["id"]
            derived.append(row["id"])
    require(len(derived) == 30 and next(removes, None) is None, "plan_replacement_shape")
    paths, mapping = {}, {}
    setup = next(r for r in report["components"]["rollback_dispatch_mapping"]["rows"]
                 if r["action"] == "rollback_setup")
    for old_key, path in report["reference_safety_paths"].items():
        commands = copy.deepcopy(path["commands"])
        require(all(r["action"] != "rollback_setup" for r in commands), "plan_setup_already_reserved")
        commands.insert(0, dict(action="rollback_setup", sql=1, kind="native", retry=False,
            identity_bound=True, source=setup["source"], sql_sha256=setup["sql_sha256"],
            dispatch_condition="setup_connection_exists_and_transaction_status_nonzero",
            precharge_before_attempt=True, unknown_consumed=1, inner_rollback_credit=0))
        key = canonical_sha(commands)
        paths[key] = dict(commands=commands, reserved_capacity=sum(r["sql"] for r in commands),
            reference_path=old_key, reference_capacity=path["reference_capacity"], added_reservation=1,
            runtime_wired=False, bound_complete=False)
        mapping[old_key] = key
    result = dict(version=PLAN_VERSION, previous_file_checkpoint=dict(PREVIOUS_CHECKPOINT),
        current_source_hashes=copy.deepcopy(report["source_hashes"]),
        historical_register_sha256=canonical_sha(report["normal_register"]), normal=normal,
        source_derived_row_ids=derived, remaining_retained_rows_require_revalidation=True,
        recovery_paths=paths, prefix_bindings=[dict(prefix=i, reference_path=p["safety_path"],
            recovery_path=mapping[p["safety_path"]]) for i,p in enumerate(report["fault_prefixes"])],
        fault_prefixes_reference_sha256=canonical_sha(report["fault_prefixes"]),
        historical_normal=2338, approved_limit=APPROVED, historical_headroom=APPROVED-2338,
        setup_increment_only_headroom=APPROVED-2338-1, remaining_headroom_is_not_full_bound=True,
        dynamic_inputs=[
            dict(id="temporary_object_receipts", owner="Main/normal executor", implementation="IMPLEMENTED_RENDERERS",
                 needed="Fresh guard run/three ids; validated observer and guard receipts for two DO hashes.",
                 source=source("registered_lifecycle.py", "close_temporary")),
            dict(id="full_adapter_fault_position", owner="D", implementation="MISSING_FULL_ENDCHAIN_ADAPTER",
                 needed="Map each fault to actual precharge/dispatch/confirmation event, not rollback-isolated component boundary.",
                 source=source("integral_failure_runtime_workflow.py", "WorkflowDriver")),
            dict(id="full_adapter_recovery_ownership", owner="D/Main", implementation="MISSING_JOIN",
                 needed="Ordered child termination, connection transaction states, original error, Auth mint barrier and one-shot cleanup ownership; join inner rollback and parent finally without assuming success.",
                 source=source("registered_runner.py", "execute/finally")),
            dict(id="full_adapter_fixture_placement", owner="D/C/Main", implementation="MISSING_JOIN",
                 needed="Exact committed writer/capture prefix and backend terminality before parent cleanup; additive/replacement mapping to prepaid cleanup130 and existing safety rows.",
                 source=source("fixture_parent_closure.py", "parent closure")),
            dict(id="managed_cli_runtime_evidence", owner="A/B/Main", implementation="PENDING_SAME_SOURCE_RECEIPTS",
                 needed="72 per-user dispatch/ticket joins, 18 Auth identities, three CLI slots and unknown-startup/cleanup suffixes. Not supplied by D rollback isolation.")],
        executable_offline_model=True, runtime_adapter_wired=False, bound_complete=False,
        minimal_cap=None, hosted_admitted=False)
    result["plan_sha256"] = canonical_sha(result)
    return result


def bind_current_plan(plan, *, run_id, ids, observer_receipt, guard_receipt):
    """Pure existing SQL renderers validate caller receipts; no database/HTTP calls."""
    from admission_binding import OLD_RUN
    from complete_register import bound_module
    from sql_protocol import statements
    require(str(uuid.UUID(run_id)) == run_id and run_id not in (OLD_RUN, NEW_RUN), "plan_fresh_case_binding")
    require(plan["plan_sha256"] == canonical_sha({k:v for k,v in plan.items() if k != "plan_sha256"}),
            "plan_digest_changed")
    result = copy.deepcopy(plan)
    for owner, receipt in (("observer", observer_receipt), ("guard", guard_receipt)):
        filename = REMOVAL_SOURCES[owner]
        module = bound_module("budget_current_" + owner, HERE / filename)
        parsed = statements(module.remove(run_id, ids, receipt))
        rows = [r for r in result["normal"]["rows"] if r.get("owner") == owner and r["action"] == "remove"]
        require(len(rows) == len(parsed) == 5, "plan_bound_removal_shape")
        for row, actual in zip(rows, parsed):
            require(row["source"]["sha256"] == digest(HERE / filename), "plan_removal_source_changed")
            if not row["binding_required"]:
                require(row["sql_sha256"] == actual["sha256"], "plan_removal_fixed_sql_changed")
            row.update(sql_sha256=actual["sha256"], binding_required=False,
                       binding_input_sha256=canonical_sha(dict(run_id=run_id, ids=ids, receipt=receipt)))
    result["parent_plan_sha256"] = plan["plan_sha256"]
    result["plan_sha256"] = canonical_sha({k:v for k,v in result.items() if k != "plan_sha256"})
    return result


def recovery_reservations(plan, path_key, attempts):
    """Run the one-shot reservation model only; an unknown attempt consumes its charge."""
    require(plan["plan_sha256"] == canonical_sha({k:v for k,v in plan.items() if k != "plan_sha256"}),
            "plan_digest_changed")
    path = plan["recovery_paths"][path_key]
    labels = {r["action"]: r["sql"] for r in path["commands"]}
    used, seen = 0, set()
    require(isinstance(attempts, list) and len(attempts) <= len(labels), "plan_recovery_attempts")
    for attempt in attempts:
        label = attempt["action"]
        require(label in labels and label not in seen, "plan_recovery_unknown_or_duplicate")
        require(attempt["outcome"] in ("confirmed", "unknown", "failed"), "plan_recovery_outcome")
        seen.add(label)
        used += labels[label]
    return dict(consumed_capacity=used, reserved_capacity=path["reserved_capacity"], refunds=0,
                dispatches_executed=0, hosted_admitted=False, minimal_cap=None)


def cleanup_composition_plan(case_count, eligible_count, unknown_count):
    """Instantiate every added C/B command and stopping suffix; no live objects."""
    import fixture_producer_scope as producer
    import fixture_parent_physical_zero as physical
    import fixture_db_terminality as db
    import fixture_cleanup_runtime_sql as sql
    require(all(type(n) is int for n in (case_count, eligible_count, unknown_count)), "cleanup_plan_integer_counts")
    require(1 <= case_count <= physical.MAX_CASES and 1 <= unknown_count <= case_count
            and 0 <= eligible_count <= case_count - unknown_count, "cleanup_plan_disjoint_case_sets")
    method = _method("admission_cleanup_composition.py", "finalize", "Closure")
    calls = [n for n in ast.walk(method) if isinstance(n, ast.Call) and ast.unparse(n.func) == "auth_parent.finalize"]
    require(len(calls) == 1, "cleanup_parent_call_drift")
    costs = [ast.literal_eval(k.value) for k in calls[0].keywords if k.arg == "delete_costs"]
    require(len(costs) == 1, "cleanup_parent_cost_binding")
    auth = parent_auth_finalizer_component(costs[0])
    scope = [("begin", "BEGIN TRANSACTION READ ONLY"), *producer.QUERIES, ("rollback", "ROLLBACK")]
    zero = [("zero_begin", "BEGIN TRANSACTION READ ONLY"), ("zero_session", db.SESSION),
            ("backend_absence", db.ACTIVITY), ("zero_inventory", sql.INVENTORY), ("zero_rollback", "ROLLBACK")]
    suffix = physical.protocol_plan(case_count, eligible_count)
    require(len(scope) == producer.LIMIT == 10 and len(zero) == db.ZERO_LIMIT == 5,
            "cleanup_scope_zero_cost_drift")
    require(len(suffix) == 20 + 2 * case_count + (1 + len(sql.ORDER)) * eligible_count
            and len(sql.ORDER) == 13 and physical.FIXED_LIMIT == 21, "cleanup_physical_cost_drift")
    blocks = []
    for name, pairs, filename, cap, mode in (
        ("scope_before", scope, "fixture_producer_scope.py", producer.LIMIT, "scope"),
        ("scope_after", scope, "fixture_producer_scope.py", producer.LIMIT, "scope"),
        *(("unknown_zero_%d" % i, zero, "fixture_db_terminality.py", db.ZERO_LIMIT, "zero")
          for i in range(unknown_count)),
        ("physical_suffix", suffix, "fixture_parent_physical_zero.py", len(suffix) + 1, "physical")):
        binding = source(filename, "Scope._observe/collect" if mode == "scope" else
                         "TrackedRuntime.physical_zero" if mode == "zero" else "protocol_plan/run")
        rows = [dict(id=name + ":" + str(i), phase="safety", action=action, cost=1, kind="native",
            sql_sha256=hashlib.sha256(text.encode()).hexdigest(), source=binding,
            precharge_before_send=True, execution_ready=False) for i,(action,text) in enumerate(pairs)]
        rollback = dict(id=name + ":failure_rollback", phase="safety", action="failure_rollback",
            cost=1, kind="native", sql_sha256=hashlib.sha256(b"ROLLBACK").hexdigest(), source=binding)
        faults = []
        for i,row in enumerate(rows):
            action = row["action"]
            # Physical COMMIT uncertainty closes without a second SQL attempt.
            rollback_eligible = i < len(rows) - 1 and (mode != "physical" or action != "registry_commit")
            for outcome in ("before_charge_rejected", "charge_storage_failed", "unknown_after_charge", "validation_failed"):
                charged = 0 if outcome == "before_charge_rejected" else 1
                suffix_rows = [rollback] if rollback_eligible else []
                if outcome == "charge_storage_failed" and mode != "zero":
                    suffix_rows = []  # producer.Meter poisons itself before any dispatch.
                if mode == "physical" and action == "registry_commit" and outcome == "validation_failed":
                    suffix_rows = []  # Confirmed commit has began=False before later checks.
                faults.append(dict(at=row["id"], outcome=outcome, consumed_capacity=i + charged,
                    suffix=[r["id"] for r in suffix_rows], suffix_capacity=len(suffix_rows),
                    required_capacity=i + charged + len(suffix_rows), later_blocks_admitted=False,
                    unknown_commit_reclassified=False, retry=False, refunds=0))
        blocks.append(dict(id=name, rows=rows, failure_only=[rollback], fault_prefixes=faults,
            normal_capacity=len(rows), meter_cap=cap, maximum_modeled_path=max([len(rows)]+[
                f["required_capacity"] for f in faults]), source=binding))
    blocks.append(dict(id="parent_auth", rows=auth["rows"], fault_prefixes=auth["fault_paths"],
        normal_capacity=auth["diagnostic_capacity"], meter_cap=auth["diagnostic_capacity"],
        maximum_modeled_path=auth["diagnostic_capacity"], failure_only=[], source=auth["source"]))
    prefixes, spent = [], 0
    for block in blocks:
        for fault in block["fault_prefixes"]:
            prefixes.append(dict(fault, block=block["id"],
                composition_consumed_capacity=spent + fault["consumed_capacity"],
                composition_required_capacity=spent + fault["required_capacity"],
                later_blocks_admitted=False))
        spent += block["normal_capacity"]
    return dict(format="admission-cleanup-composition-plan-v1",
        counts=dict(cases=case_count, eligible=eligible_count, unknown=unknown_count),
        blocks=blocks, fault_prefixes=prefixes, normal_prepaid_capacity=spent,
        declared_meter_caps=sum(b["meter_cap"] for b in blocks),
        maximum_modeled_path=max([spent]+[p["composition_required_capacity"] for p in prefixes]),
        accounting_domain="additional_disposable_diagnostic_not_2349",
        graph_order=[b["id"] for b in blocks],
        external_interval=dict(after="scope_before", before="scope_after",
            existing_component_refs=["parent_bootstrap", "fixture_diagnostic", "opt_in_diagnostics.tracked_db"],
            counted_here=False, not_zero_cost=True),
        transport_boundaries=dict(admin_suspend_calls=2, close_attempts=2, reconnect_attempts=2,
            explicit_new_sql=0, startup_protocol_cost=None,
            source=source("../../phase6e_server_v1/ci_auth.py", "environment/suspend_admin")),
        wrapper_final_observers=dict(commands=3, additive=False, already_existing_ci_auth=True,
            source=source("../../phase6e_server_v1/ci_auth.py", "environment/finally/numeric_final_observers")),
        scopes_are_not_global_barriers=True, observed_execution=False,
        original_unknown_claims_released=False, bound_complete=False, minimal_cap=None, hosted_admitted=False)


def cleanup_composition_register():
    """Finite parameter domain plus source-backed template graphs, not one guessed total."""
    import fixture_parent_physical_zero as physical
    shapes, cases = {}, []
    for n in range(1, physical.MAX_CASES + 1):
        for eligible in range(n):
            key = "%d:%d" % (n, eligible)
            exemplar = cleanup_composition_plan(n, eligible, 1)
            shapes[key] = exemplar["blocks"][-2]
            for unknown in range(1, n - eligible + 1):
                normal = exemplar["normal_prepaid_capacity"] + (unknown - 1) * 5
                cases.append(dict(cases=n, eligible=eligible, unknown=unknown,
                    physical_shape=key, normal_prepaid_capacity=normal, declared_meter_caps=normal + 1))
    template = cleanup_composition_plan(1, 0, 1)
    return dict(format="admission-cleanup-composition-register-v1",
        compile_api="admission_budget_register.cleanup_composition_plan(N,E,U)",
        shared_blocks={b["id"]:b for b in template["blocks"] if b["id"] != "physical_suffix"},
        physical_shapes=shapes, parameter_cases=cases, graph_program=[
            dict(block="scope_before", repeat=1),
            dict(external_interval=template["external_interval"]),
            dict(block="scope_after", repeat=1), dict(block="unknown_zero_0", repeat="U"),
            dict(block="physical_shapes[N:E]", repeat=1), dict(block="parent_auth", repeat=1)],
        transport_boundaries=template["transport_boundaries"], wrapper_final_observers=template["wrapper_final_observers"],
        actual_case_selection_pending=True, complete_parameterized_protocol_model=True,
        source=source("admission_cleanup_composition.py", "Closure.begin/bind_terminal/finalize"),
        accounting_domain="additional_disposable_diagnostic_not_2349",
        not_a_total_for_the_parent_ci_job=True, bound_complete=False, minimal_cap=None, hosted_admitted=False)


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
            "No duplicated rollback, existing safety Auth, or prepaid 130 cleanup slots.",
            "Auth reconciliation and parent fixture suffix eligibility, barrier and actual receipts remain unbound."]),
        dict(id="setup_rollback", owner="Main", source_dispatch_cost=1, inputs=[
            "New plan v2 reserves rollback_setup=1; wire its label into runtime without changing historical safety rows.",
            "Bind lifecycle_rollback versus workflow.finally with no double dispatch or fictitious alias."]),
    ]
    prefixes, safety_paths = prefix_register(normal)
    sources = {name: digest(HERE / name) for name in (
        "admission_budget.py", "admission_budget_register.py", "admission_binding.py", "scenario.py",
        "complete_register.py", "metered_composition.py", "registered_lifecycle.py", "integral_ci.py", "integral_io.py",
        "lifecycle_gates.py", "cli_envelope.py", "cli_meter.py", "cli_stat_reader.py", "auth_failure.py",
        "auth_failure_transport.py", "fixture_cleanup_runtime.py", "fixture_cleanup_runtime_sql.py",
        "integral_failure_runtime.py", "integral_failure_runtime_workflow.py",
        "integral_failure_runtime_worker.mjs", "fixture_cleanup_runtime_ci.py",
        "fixture_cleanup_evidence.py", "sql_protocol.py", "native_runtime.py",
        "fixture_control_ownership.py", "test_fixture_control_ownership.py",
        "fixture_parent_closure.py", "test_fixture_parent_closure.py",
        "fixture_db_terminality.py", "test_fixture_db_terminality.py",
        "admission_module_binding.py", "auth_protocol.py", "auth_evidence.py", "fixture_lifecycle.py",
        "runtime_budget.py", "registered_runner.py", "control_recovery.py", "integral_stream.py",
        "auth_failure_parent_finalizer.py", "auth_failure_parent_finalizer_test.py",
        "auth_failure_tracked.py", "auth_failure_tracked_test.py",
        "admission_cleanup_composition.py", "test_admission_cleanup_composition.py",
        "fixture_producer_scope.py", "test_fixture_producer_scope.py",
        "fixture_parent_physical_zero.py", "test_fixture_parent_physical_zero.py",
        "execution_context.mjs", "workflow_composition.mjs", "composed_handler.mjs", "integral_auth.mjs",
        "session_transport.mjs", "request_transport.mjs", "integral_workflow.mjs",
        "admission_fixture_context.py", "admission_ci.py", "admission_journal.py",
        "admission_budget_graph.py", "admission_budget_receipts.py",
        "migration_failure_boundaries.py", "test_migration_failure_boundaries.py") + CLI_SOURCE_FILES}
    sources["_offline/phase6e_server_v1/cli_isolation.py"] = digest(
        HERE.parents[1] / "phase6e_server_v1" / "cli_isolation.py")
    sources["_offline/phase6e_server_v1/ci_profile.py"] = digest(
        HERE.parents[1] / "phase6e_server_v1" / "ci_profile.py")
    for filename in REMOVAL_SOURCES.values():
        binding = source(filename, "remove")
        sources[binding["path"]] = binding["sha256"]
    sources["_offline/phase6e_server_v1/ci_auth.py"] = digest(HERE.parents[1] / "phase6e_server_v1" / "ci_auth.py")
    sources["_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py"] = digest(
        HERE.parents[2] / "_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py")
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
    report["components"]["opt_in_diagnostics"] = opt_in_diagnostics(
        fixture, report["components"]["fixture_diagnostic"], auth)
    report["normal_dispatch_mapping"] = normal_dispatch_mapping(normal)
    report["components"]["rollback_dispatch_mapping"] = rollback_dispatch_mapping()
    report["components"]["parent_auth_finalizer"] = parent_auth_finalizer_component(
        {role: 128 for role in ("a", "trainer", "b")})
    report["components"]["cleanup_composition"] = cleanup_composition_register()
    report["current_plan"] = current_plan(report)
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
