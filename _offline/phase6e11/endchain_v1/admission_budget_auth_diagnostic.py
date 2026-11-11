"""Separate source-bound preparation for B's eleven-case local Auth job.

No normal-case admission is borrowed. Known reservations remain visible even
when their physical SQL upper bounds and cleanup predicates are unresolved.
This module imports no candidate Auth implementation and never starts resources.
"""
import ast
import copy
import hashlib
import json
import pathlib
import uuid

import admission_budget_root_runtime as root_budget

PREFIX = root_budget.PREFIX
KEY = object()
COMPONENT = "quota_candidate_v1/runtime_auth_failure_component.py"
CONTEXT = "quota_candidate_v1/runtime_registered_bootstrap.py"
CASES = ("before_dispatch", "create_lost_reply", "partial_user", "partial_session",
         "login_timeout", "logout_timeout", "admin_unknown", "duplicate_request",
         "cleanup_interrupted", "missing_mint_barrier", "duplicate_cleanup")


def _literal(tree, name):
    values = [n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    root_budget.require(len(values) == 1, "auth_diagnostic_literal:" + name)
    return ast.literal_eval(values[0])


def _method(tree, name):
    values = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    root_budget.require(len(values) == 1, "auth_diagnostic_method:" + name)
    return values[0]


def build_auth_failure_register(source_root, *, runtime_dir=None, context_dir=None, dependency_paths=None):
    source_root = pathlib.Path(source_root).resolve(strict=True)
    base = source_root / PREFIX
    context = pathlib.Path(context_dir or runtime_dir or base / "quota_candidate_v1")
    source = root_budget.source_program(source_root, runtime_dir=runtime_dir,
        context_dir=context, dependency_paths={name: path for name, path in (dependency_paths or {}).items()
                                             if name != PREFIX + "auth_failure.py"})
    raw = (context / "runtime_auth_failure_component.py").read_bytes()
    component = ast.parse(raw)
    root_budget.require(_literal(component, "CASES") == CASES, "auth_diagnostic_exact_eleven")
    register = _method(component, "command_register")
    # Preserve the real expression/caller provenance; never eval an engine or
    # accept a caller-supplied total as the managed cost proof.
    calls = [n for n in ast.walk(register) if isinstance(n, ast.Call)]
    root_budget.require(any(isinstance(n.func, ast.Attribute) and n.func.attr == "contract"
                            and isinstance(n.func.value, ast.Name) and n.func.value.id == "engine"
                            for n in calls), "auth_diagnostic_engine_contract")
    allowance = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "fromkeys"]
    root_budget.require(len(allowance) == 1 and len(allowance[0].args) == 2
        and isinstance(allowance[0].args[1], ast.Constant)
        and type(allowance[0].args[1].value) is int, "auth_diagnostic_declared_allowance")
    per_http = allowance[0].args[1].value
    engine_path = pathlib.Path((dependency_paths or {}).get(PREFIX + "auth_failure.py", base / "auth_failure.py"))
    engine_raw = engine_path.read_bytes()
    engine = ast.parse(engine_raw)
    invocation = [n for n in ast.walk(component) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                  and isinstance(n.func.value, ast.Name) and n.func.value.id == "engine"]
    root_budget.require(len(invocation) == 1 and not any(k.arg is None for k in invocation[0].keywords),
                        "auth_diagnostic_engine_invocation")
    engine_run = _method(engine, "run")
    supplied = sorted(k.arg for k in invocation[0].keywords)
    accepted = {a.arg for a in engine_run.args.args + engine_run.args.kwonlyargs}
    missing_keywords = sorted(set(supplied) - accepted)
    engine_interface = dict(supplied_keywords=supplied, missing_keywords=missing_keywords,
        compatible=not missing_keywords, raw_sha256=hashlib.sha256(engine_raw).hexdigest(),
        run_ast_sha256=hashlib.sha256(ast.dump(engine_run, include_attributes=False).encode()).hexdigest(),
        source_only=True, actual_execution_proven=False)
    operations = _literal(engine, "OPERATIONS")
    root_budget.require(_literal(engine, "CASES") == CASES, "auth_diagnostic_engine_cases")
    slots = next(n.value for n in engine.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "NATIVE_SLOTS" for t in n.targets))
    expected_slots = ast.parse("('preflight','prefix','cleanup_before','final') + "
        "tuple(side + '_' + op for op in OPERATIONS for side in ('stats_before','stats_after'))", mode="eval").body
    root_budget.require(ast.dump(slots, include_attributes=False) == ast.dump(expected_slots, include_attributes=False),
                        "auth_diagnostic_native_slot_shape")
    native_count = len(ast.literal_eval(slots.left)) + 2 * len(operations)
    per_case = len(operations) * per_http + native_count
    returns = [n for n in register.body if isinstance(n, ast.Return)]
    root_budget.require(len(returns) == 1 and isinstance(returns[0].value, ast.Dict), "auth_diagnostic_register_shape")
    values = {ast.literal_eval(k): v for k, v in zip(returns[0].value.keys, returns[0].value.values)}
    reconciliation = ast.literal_eval(values["reconciliation_native_capacity"])
    root_budget.require(type(reconciliation) is int and reconciliation == 6, "auth_diagnostic_reconciliation_source")
    context_raw = (context / "runtime_registered_bootstrap.py").read_bytes()
    context_tree = ast.parse(context_raw)
    enter = _method(context_tree, "__enter__")
    direct = [n for n in ast.walk(enter) if isinstance(n, ast.If)
              and isinstance(n.test, ast.Attribute) and n.test.attr == "_diagnostic_mode"]
    root_budget.require(len(direct) == 1 and len(direct[0].body) == 1
                        and isinstance(direct[0].body[0], ast.Return), "auth_diagnostic_no_parent_branch")
    methods = {name: hashlib.sha256(ast.dump(_method(context_tree, name),
                include_attributes=False).encode()).hexdigest()
               for name in ("__enter__", "run_auth_failures", "_finish", "_admit")}
    rows = copy.deepcopy(source["context_normal"])
    startup_end = next(i for i, row in enumerate(rows) if row["command_id"] == "auth.create.a_member")
    stop_start = next(i for i, row in enumerate(rows) if row["command_id"] == "auth.auth_stop")
    startup, stop = rows[:startup_end], rows[stop_start:]
    root_budget.require(startup[-1]["command_id"] == "auth.validate.target_connection"
                        and len(stop) == 5, "auth_diagnostic_start_stop_order")
    for row in startup + stop:
        row.update(hosted_units=0, covered_by="case.auth.failures")
    component_row = dict(command_id="auth.failure_component", units=None,
        declared_reservation=len(CASES) * per_case, native_sql_capacity=len(CASES) * native_count + reconciliation,
        reconciliation_native_capacity=reconciliation, http_capacity=len(CASES) * len(operations) + 1,
        reconciliation_allocation="original unused per-case reserve; requires original reconciliation proof",
        units_are_not_derived_from_absence=True, source=PREFIX + COMPONENT,
        source_sha256=hashlib.sha256(raw).hexdigest(), hosted_units=0,
        observation_group=root_budget.MANAGED_OBSERVATION_GROUP,
        native_partition="actual originals only, then one complete stopped managed union",
        missing="managed_HTTP_execution_bound_and_all_exceptional_partitions", covered_by="case.auth.failures")
    # Registry close is filesystem-only, but only if the source-created registry
    # exists. Its selection predicate cannot be supplied by a job argument.
    selector = dict(command_id="auth.cleanup.select", units=0, hosted_units=0,
        covered_by="case.auth.failures", source=PREFIX + CONTEXT,
        predicate="actual Context._finish state including diagnostic registry existence")
    registry_close = dict(command_id="auth.failure_registry_close", units=0, hosted_units=0,
        covered_by="case.auth.failures", source=PREFIX + CONTEXT, sql_commands=0,
        predicate="actual diagnostic registry exists; seal/drain before process stop")
    context_order = startup + [component_row, selector, registry_close] + stop
    missing = sorted({r["command_id"] + ":" + str(r.get("missing") or "complete_cost_unproven")
                      for r in context_order if r["units"] is None} | {
        "case.platform.install:full_source_bound_first_start_reset_and_shutdown",
        "case.bootstrap.clean47:canonical_protocol_plus_all_driver_partitions",
        "auth.cleanup.select:source_owned_diagnostic_registry_state_branch",
        "auth.failure_component:engine_original_reconciliation_and_native_driver_dependencies",
        "source_inventory:transitive_runtime_and_binary_closure"})
    if missing_keywords:
        missing.append("auth.failure_component:engine_run_missing_keywords:" + ",".join(missing_keywords))
        missing.sort()
    faults = [dict(after_instruction=r["command_id"], retained_prefix=[x["command_id"]
        for x in context_order[:i+1]], next="auth.cleanup.select",
        dynamic_state_inputs=["registry_exists", "db_open", "auth_start_attempted",
            "auth_container_known", "managed_baseline"],
        failure_suffix=[registry_close, *stop], reserve=None, refund=0,
        complete=False, unknown_retained=True)
        for i, r in enumerate(startup + [component_row])]
    hashes = dict(source["source_hashes"])
    hashes[PREFIX + COMPONENT] = hashlib.sha256(raw).hexdigest()
    hashes[PREFIX + "auth_failure.py"] = hashlib.sha256(engine_raw).hexdigest()
    hashes[PREFIX + pathlib.Path(__file__).name] = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    report = dict(format="admission-auth-diagnostic-root-register-v1", scope="LOCAL_DIAGNOSTIC_ONLY",
        case_name="auth_failures", cases=list(CASES), source_hashes=hashes,
        component_register_ast_sha256=hashlib.sha256(ast.dump(register, include_attributes=False).encode()).hexdigest(),
        engine_interface=engine_interface,
        context_method_ast_sha256=methods, context_order=context_order, fault_prefixes=faults,
        root_order=["case.platform.install", "case.bootstrap.clean47", "case.auth.failures", "case.terminal"],
        root_envelope="case.auth.failures", parent_users_created=0, parent_fixture_created=False,
        parent_cleanup_sql=0, parent_zero_basis="source-owned early return before create_all/seed",
        component_declared_reservation=len(CASES) * per_case, native_reconciliation_partition=reconciliation,
        startup_profile_stop_and_clean47_included=True, hosted_limit=2349,
        total_hosted_equivalent_upper_bound=0, total_local_ci_upper_bound=None,
        bound_complete=False, source_inventory_complete=False, prefix_reserves_complete=False,
        executable_program=None, missing_costs=missing, blocked_stage="case.platform.install",
        full_chain_admission=False, hosted_admitted=False, runtime_admitted=False,
        actual_execution_evidence=False)
    root_budget.require((context / "runtime_auth_failure_component.py").read_bytes() == raw
                        and (context / "runtime_registered_bootstrap.py").read_bytes() == context_raw
                        and engine_path.read_bytes() == engine_raw,
                        "auth_diagnostic_source_changed")
    report["full_register_sha256"] = root_budget.digest(report)
    return report


class PreparedAuthFailureExecution:
    __slots__ = ("_key", "_gate", "_binding", "_report", "_used")

    def __init__(self, key, gate, binding, report):
        root_budget.require(key is KEY, "auth_diagnostic_prepared_origin")
        self._key, self._gate = key, gate
        self._binding, self._report = copy.deepcopy(binding), copy.deepcopy(report)
        self._used = False

    @property
    def report(self):
        return copy.deepcopy(self._report)


def prepare_auth_failure_execution(gate, *, binding):
    """Source-only owner before installation; report does not grant admission."""
    run = binding.get("run_id")
    root_budget.require(type(run) is str and str(uuid.UUID(run)) == run and uuid.UUID(run).version == 4
        and run not in ("6f8c8909-9b79-4011-a9d1-db5e23c6b6c1", "11a909f4-7113-424a-aa4b-ce9964720a3e")
        and binding.get("environment") == "disposable_ci", "auth_diagnostic_fresh_binding")
    root_budget.require(binding.get("candidate_sha") == gate.result["candidate_sha256"]
        and binding.get("source_commit") == gate.result.get("commit", gate.result.get("head"))
        and binding.get("ci_run") == gate.result["run_id"], "auth_diagnostic_candidate_binding")
    report = build_auth_failure_register(gate.sources)
    manifest = json.loads((pathlib.Path(gate.out) / "candidate.json").read_bytes())
    root_budget.require(manifest.get("sha256") == binding["candidate_sha"]
        and all(manifest.get("sources", {}).get(name) == digest for name, digest in report["source_hashes"].items()),
        "auth_diagnostic_candidate_sources")
    return PreparedAuthFailureExecution(KEY, gate, binding, report)


def open_auth_failure_ledger(gate, *, prepared):
    """No fallback to normal-case admission; unresolved costs prevent any start."""
    root_budget.require(type(prepared) is PreparedAuthFailureExecution and prepared._key is KEY
        and prepared._gate is gate and not prepared._used, "auth_diagnostic_prepared_owner")
    prepared._used = True
    rebuilt = build_auth_failure_register(gate.sources)
    root_budget.require(rebuilt == prepared._report, "auth_diagnostic_source_changed")
    root_budget.require(rebuilt["bound_complete"] and rebuilt["prefix_reserves_complete"]
        and rebuilt["source_inventory_complete"] and not rebuilt["missing_costs"],
        "auth_diagnostic_bound_incomplete:" + rebuilt["blocked_stage"])
    # This revision intentionally has no private-ledger escape hatch. A future
    # complete proof must be joined to the shared factory, not caller flags.
    raise root_budget.RootBlocked("auth_diagnostic_factory_join_pending")
