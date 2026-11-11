"""Authoritative opt-in release boundary, separate from graph arithmetic.

Only a regenerated source plan may reach this boundary. A hash of caller data
is not evidence of coverage, and a finite graph is not an executor contract.
All work in this module is local source inspection and deterministic assembly.
"""
import copy
import hashlib
import pathlib

from admission_budget import APPROVED, HERE, require
from admission_budget_current_dag import FORMAT, assemble_current_dag
from admission_budget_current_inventory import derive_current_plan
from admission_budget_current_hooks import attach_case_hooks
from admission_budget_current_order import (PREFIX, assemble_normal_contract,
    derive_stream_order, meter_requirements)
from admission_budget_register import assemble, canonical_sha
from admission_budget_release_joins import bind_lifecycle, derive_release_joins

RELEASE_FORMAT = "admission-actual-execution-release-v1"
BOOTSTRAP_CASES = ("pre_migration", "post_migration")
CASE_HOOKS = ("mid_auth", "controller", "route_a", "route_b", "restore", "lost_response",
              "duplicate", "timeout", "partial_fixture_cleanup", "cleanup_failure",
              "final_check_failure", "closure_failure")


def _authoritative(root, runtime_dir):
    root = pathlib.Path(root).resolve(strict=True)
    require(root / PREFIX.rstrip("/") == HERE.resolve(), "release_loaded_source_root")
    require(pathlib.Path(__file__).resolve() == root / PREFIX / "admission_budget_current_release.py",
            "release_loaded_compiler_origin")
    runtime = pathlib.Path(runtime_dir) if runtime_dir is not None else root / PREFIX / "quota_candidate_v1"
    plan = derive_stream_order(derive_current_plan(assemble()), runtime_dir=runtime)
    normal = assemble_normal_contract(plan, runtime_dir=runtime)
    from complete_register import scenario_source
    normal = attach_case_hooks(normal, plan, scenario_source.capture()["workflow_actions"], runtime_dir=runtime)
    normal = bind_lifecycle(normal, runtime_dir=runtime, source_root=root)
    return root, runtime, plan, normal


def _source_snapshot(plan, normal, joins=None):
    values = {**plan["current_source_hashes"], **normal["source_hashes"]}
    for name in ("admission_budget_current_release.py", "admission_budget_current_order.py",
                 "admission_budget_current_dag.py", "admission_budget_current_inventory.py",
                 "admission_budget_current_hooks.py"):
        values[PREFIX + name] = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    if joins is not None:
        values.update(joins["source_hashes"])
    values[PREFIX + "admission_budget_current_release.py"] = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    return values


def _normal_projection(event):
    # Recovery routing may extend outcomes; it may not move an act, substitute a
    # source, refund a charge, release state earlier or move a confirmed edge.
    return {k: copy.deepcopy(v) for k, v in event.items() if k not in ("next", "outcomes")}


def _validate_normal(dag, expected):
    require(dag.get("normal_event_ids") == expected["normal_event_ids"], "release_actual_normal_order")
    actual = {e["event_id"]: e for e in dag.get("events", [])}
    require(len(actual) == len(dag.get("events", [])), "release_duplicate_event")
    for item in expected["events"]:
        ident = item["event_id"]
        require(ident in actual, "release_missing_normal_event:" + ident)
        require(_normal_projection(actual[ident]) == _normal_projection(item),
                "release_normal_contract_changed:" + ident)
        require(actual[ident].get("next", {}).get("confirmed") == item["next"]["confirmed"],
                "release_normal_edge_changed:" + ident)
        require(set(item["outcomes"]) <= set(actual[ident].get("outcomes", [])),
                "release_normal_outcomes_missing:" + ident)
    require(dag.get("charge_groups") == expected["charge_groups"], "release_charge_groups_changed")
    require(dag.get("coverage") == {}, "release_register_remap_forbidden")


def _compile(dag, sources, root, runtime, plan, normal):
    require(dag.get("format") == FORMAT and dag.get("release_format") == RELEASE_FORMAT,
            "release_authoritative_contract_required")
    require(dag.get("plan_sha256") == plan["plan_sha256"], "release_authoritative_plan_changed")
    require(dag.get("register_source_hashes") == plan["current_source_hashes"],
            "release_register_sources_changed")
    expected = assemble_current_dag(normal, report={"current_plan": plan}, current_plan=plan)
    for field in ("register_events", "register_charge_groups", "register_recovery_paths",
                  "workflow_dispatch_requirements", "historical_reference", "approved_limit"):
        require(dag.get(field) == expected[field], "release_authoritative_" + field)
    joins = derive_release_joins(root, runtime, plan, normal)
    require(dag.get("actual_join_proofs") == joins, "release_actual_join_proofs_changed")
    authoritative_sources = _source_snapshot(plan, normal, joins)
    require(dag.get("source_hashes") == authoritative_sources, "release_source_inventory_changed")
    for name, digest in authoritative_sources.items():
        full = name if name.startswith(PREFIX) else PREFIX + name
        require(sources.get(name, sources.get(full)) == digest, "release_source_snapshot_changed:" + name)
    _validate_normal(dag, normal)
    for field in ("fault_cases", "bootstrap_fault_cases", "hook_inventory"):
        require(dag.get(field) == normal[field], "release_actual_" + field)
    require(dag.get("approved_limit") == APPROVED, "release_cap_changed")
    predicates = meter_requirements(plan, normal, runtime_dir=runtime)
    require(dag.get("meter_requirements") == predicates, "release_meter_predicate_changed")

    # Proofs come from the regenerated source program, not caller flags.
    missing = list(joins["missing_costs"])
    bound_complete = joins["complete"]
    required = max(normal["normal_accounting"]["capacity"], predicates["required_limit"])
    if predicates["required_limit"] > APPROVED:
        missing.append("actual_meter_requires_" + str(predicates["required_limit"]))
    return dict(format=RELEASE_FORMAT, dag_sha256=canonical_sha(dag), plan_sha256=plan["plan_sha256"],
        normal_capacity=normal["normal_accounting"]["capacity"],
        phase_capacities=copy.deepcopy(plan["normal"]["phase_capacities"]),
        normal_event_count=len(normal["events"]), normal_dispatch_inventory=normal["normal_accounting"],
        case_fault_count=len(normal["fault_cases"]), bootstrap_fault_count=len(normal["bootstrap_fault_cases"]),
        bootstrap_closeout_sql_reserve=4, bootstrap_closeout_docker_inventory_calls=1,
        meter_required_limit=predicates["required_limit"], first_meter_denial=predicates["first_denied"],
        bound_complete=bound_complete, minimal_cap=required if bound_complete else None,
        fits=bound_complete and required <= APPROVED,
        status="SOURCE_BOUND" if bound_complete and required <= APPROVED else "NO_GO",
        missing_costs=missing, join_evidence=joins, root_disposable_gate_required=True,
        approved_limit=APPROVED, historical_normal=2338, historical_closing=731,
        actual_executor_and_real_ci_proven=False, hosted_admitted=False)


def compile_release(dag, source_hashes, *, source_root, runtime_dir=None):
    """Rebuild authority from loaded, candidate-bound source before any verdict."""
    require(isinstance(dag, dict) and dag.get("release_format") == RELEASE_FORMAT,
            "release_authoritative_contract_required")
    root, runtime, plan, normal = _authoritative(source_root, runtime_dir)
    return _compile(dag, source_hashes, root, runtime, plan, normal)


def build_current_execution(root, *, runtime_dir=None):
    """Source-only pre-bootstrap API. It never makes an incomplete model fit."""
    root, runtime, plan, normal = _authoritative(root, runtime_dir)
    dag = assemble_current_dag(normal, report={"current_plan": plan}, current_plan=plan)
    joins = derive_release_joins(root, runtime, plan, normal)
    dag.update(release_format=RELEASE_FORMAT, source_hashes=_source_snapshot(plan, normal, joins),
               actual_join_proofs=joins,
               meter_requirements=meter_requirements(plan, normal, runtime_dir=runtime))
    model = _compile(dag, dag["source_hashes"], root, runtime, plan, normal)
    return dict(dag=dag, dag_sha256=canonical_sha(dag), model=model)
