"""One root accounting domain for disposable cases, without runtime authority.

The core export is retained verbatim. Bootstrap, isolation, managed startup and
cleanup are not free because another module or PostgreSQL instance owns them.
Current source cannot establish their complete bound, so public opening stops.
The ticket engine is independently executable for offline contract tests only.
"""
import ast
import copy
import hashlib
import json
import os
import pathlib
import re
import uuid

LIMIT = 2349
PREFIX = "_offline/phase6e11/endchain_v1/"
FORMAT = "admission-disposable-root-register-v1"
MODEL_FIELDS = ("bound_complete", "total_local_ci_upper_bound",
    "total_hosted_equivalent_upper_bound", "hosted_scope_complete",
    "source_inventory_complete", "missing_costs", "hosted_limit")
_KEY = object()
_ADMITTED = object()
MANAGED_OBSERVATION_GROUP = "auth.managed_lifetime"
COMPONENT_SOURCES = {
    "admission_auth_runtime_profile.py": "a212dae2b7195835592d32342f653b184fc8309e60bcccd427ede1d272b7adcc",
    "quota_candidate_v1/runtime_registered_fixture_closeout.py": "e30062436d1b41428215fcf1afb55c70a2ec0da59d59d1df1b9d6be54a76e57a",
    "install_platform.py": "8e6e73d34c6191ec4cc3bd40977301044f20b6f792d89dc777e98b73d0c7e351",
}
QUOTA_FUNCTION_SHA = "6d21ce62c861cc201fa09a84cbb09786af8fb5155cb8df50efacbd4f454568e5"
QUOTA_PROGRAM_SHA = "e149a651571f03a76754b3cf1d922075418216b6709f17a45f57ef3755a289ba"
QUOTA_SOURCE_SHA = "861a1e58acc3d15a036641cbcfd70afb97871b5a5d4aec8f9b4fe476023fc2a3"
IO_SOURCE_SHA = "f3f78e4540931cd1a067f7baba69ef4dc8985a419d285768f7961e4bd27c0de3"


class RootBlocked(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise RootBlocked(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _read_bytes(path):
    # Preserved Windows CI artifact members can exceed MAX_PATH.
    value = str(path.absolute())
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return pathlib.Path(value).read_bytes()


def _program(value):
    if type(value) is list:
        rows = copy.deepcopy(value)
        for index, row in enumerate(rows):
            row.update(next_confirmed=rows[index+1]["command_id"] if index+1 < len(rows) else None,
                       next_unknown=None, safety_only=False)
        entry = rows[0]["command_id"] if rows else None
    else:
        require(type(value) is dict and set(value) == {"entry", "events"}, "root_program_shape")
        rows, entry = copy.deepcopy(value["events"]), value["entry"]
    require(type(rows) is list and rows, "root_program_empty")
    nodes = {}
    for row in rows:
        required = {"command_id", "units", "reserve_after",
            "domain", "hosted_units", "hosted_reserve_after", "next_confirmed",
            "next_unknown", "safety_only"}
        require(type(row) is dict and required <= set(row)
                and set(row) <= required | {"defer", "children", "observation_group", "observation_units",
                                           "node_id", "selection_cases"},
                "root_instruction_shape")
        row.setdefault("defer", False)
        row.setdefault("children", None)
        row.setdefault("observation_group", None)
        row.setdefault("observation_units", row["units"] if row["defer"] else 0)
        row.setdefault("node_id", row["command_id"])
        row.setdefault("selection_cases", None)
        require(type(row["defer"]) is bool and not (row["defer"] and row["children"] is not None),
                "root_instruction_defer")
        require(row["observation_group"] is None or row["defer"]
                and isinstance(row["observation_group"], str) and row["observation_group"],
                "root_observation_group")
        ident = row["node_id"]
        require(isinstance(ident, str) and ident and ident not in nodes, "root_instruction_duplicate")
        require(type(row["units"]) is int and row["units"] >= 0
                and type(row["reserve_after"]) is int and row["reserve_after"] >= 0,
                "root_instruction_cost")
        require(type(row["observation_units"]) is int
                and 0 <= row["observation_units"] <= row["units"]
                and (row["defer"] or row["observation_units"] == 0), "root_observation_units")
        require(type(row["hosted_units"]) is int and 0 <= row["hosted_units"] <= row["units"]
                and type(row["hosted_reserve_after"]) is int
                and 0 <= row["hosted_reserve_after"] <= row["reserve_after"],
                "root_hosted_projection_cost")
        require(isinstance(row["domain"], str) and row["domain"]
                and type(row["safety_only"]) is bool, "root_instruction_domain")
        nodes[ident] = row
        if row["selection_cases"] is not None:
            require(row["command_id"] == "auth.cleanup.select" and row["units"] == 0
                    and row["hosted_units"] == 0 and row["safety_only"]
                    and row["next_confirmed"] is None and row["next_unknown"] is None
                    and row["children"] is None and not row["defer"]
                    and type(row["selection_cases"]) is dict and row["selection_cases"]
                    and all(re.fullmatch("[a-f0-9]{64}", key) for key in row["selection_cases"]),
                    "root_cleanup_selector_shape")
        if row["children"] is not None:
            _, _, child_bound, child_hosted = _program(row["children"])
            require(child_bound <= row["units"] and child_hosted <= row["hosted_units"],
                    "root_child_coverage_underreserved")
    require(entry in nodes and not nodes[entry]["safety_only"], "root_program_entry")
    for row in rows:
        for field in ("next_confirmed", "next_unknown"):
            target = row[field]
            require(target is None or isinstance(target, str) and target in nodes, "root_program_edge")
            if target is not None and (field == "next_unknown" or row["safety_only"]):
                require(nodes[target]["safety_only"], "root_recovery_cannot_resume_normal")
        for target in (row["selection_cases"] or {}).values():
            require(target in nodes and nodes[target]["safety_only"], "root_cleanup_selector_edge")
    visiting, visited, bounds, hosted_bounds = set(), set(), {}, {}
    def visit(ident):
        if ident is None:
            return 0, 0
        require(ident not in visiting, "root_program_cycle")
        if ident in visited:
            return bounds[ident], hosted_bounds[ident]
        visiting.add(ident)
        row = nodes[ident]
        branches = [visit(row["next_confirmed"]), visit(row["next_unknown"])]
        branches += [visit(target) for target in (row["selection_cases"] or {}).values()]
        suffix = max(v[0] for v in branches)
        hosted_suffix = max(v[1] for v in branches)
        require(row["reserve_after"] >= suffix, "root_recovery_underreserved")
        require(row["hosted_reserve_after"] >= hosted_suffix, "root_hosted_recovery_underreserved")
        bounds[ident] = row["units"] + max(suffix, row["reserve_after"])
        hosted_bounds[ident] = row["hosted_units"] + max(hosted_suffix, row["hosted_reserve_after"])
        visiting.remove(ident)
        visited.add(ident)
        return bounds[ident], hosted_bounds[ident]
    visit(entry)
    require(visited == set(nodes), "root_unreachable_instruction")
    return nodes, entry, bounds[entry], hosted_bounds[entry]


def _source(root, relative):
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root), "root_source_escape")
    return hashlib.sha256(_read_bytes(path)).hexdigest()


def quota_sample_contract(source_root, runtime_dir):
    """Source-pinned explicit execute-call bound, not hidden connection SQL."""
    root, runtime = pathlib.Path(source_root), pathlib.Path(runtime_dir)
    entry = _read_bytes(runtime / "runtime_case_entry.py")
    functions = [n for n in ast.parse(entry).body
                 if isinstance(n, ast.FunctionDef) and n.name == "quota_samples"]
    require(len(functions) == 1, "root_quota_function_missing")
    fn_sha = hashlib.sha256(ast.dump(functions[0], include_attributes=False).encode()).hexdigest()
    require(fn_sha == QUOTA_FUNCTION_SHA, "root_quota_dispatcher_changed")
    exports = [n for n in ast.parse(entry).body
               if isinstance(n, ast.FunctionDef) and n.name == "quota_read_program"]
    require(len(exports) == 1 and hashlib.sha256(ast.dump(exports[0],
            include_attributes=False).encode()).hexdigest() == QUOTA_PROGRAM_SHA,
            "root_quota_program_changed")
    queries_raw = _read_bytes(root / PREFIX / "admission_quota_readonly.py")
    io_raw = _read_bytes(root / PREFIX / "integral_io.py")
    require(hashlib.sha256(queries_raw).hexdigest() == QUOTA_SOURCE_SHA
            and hashlib.sha256(io_raw).hexdigest() == IO_SOURCE_SHA, "root_quota_dependency_changed")
    assignments = [n.value for n in ast.parse(queries_raw).body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "QUERIES" for t in n.targets)]
    require(len(assignments) == 1, "root_quota_queries_missing")
    queries = ast.literal_eval(assignments[0])
    require(tuple(queries) == ("constraint", "function", "trigger", "empty")
            and len(set(queries.values())) == 4, "root_quota_queries_changed")
    parts = dict(begin_timeout_identity=3, io_start=2,
                 bind_sample_read=3*len(queries), io_close=2, rollback=1)
    def literal(raw, name):
        values = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        require(len(values) == 1, "root_quota_literal_missing")
        return ast.literal_eval(values[0])
    stream_raw = _read_bytes(root / PREFIX / "integral_stream.py")
    guard, snapshot = literal(stream_raw, "GUARD"), literal(io_raw, "SNAPSHOT")
    commands = [("begin", "BEGIN TRANSACTION READ ONLY"),
        ("timeout", "SET LOCAL statement_timeout='5s'"), ("identity", guard),
        ("io_bind", "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) "+snapshot),
        ("io_sample", snapshot)]
    for name, sql in queries.items():
        commands.extend([("io_bind", "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) "+sql),
                         ("io_sample", snapshot), (name, sql)])
    commands.extend([("io_sample", snapshot), ("io_closing_witness",
        "EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) "+snapshot),
        ("rollback", "ROLLBACK")])
    counts, rows = {}, []
    for phase, sql in commands:
        counts[phase] = counts.get(phase, 0)+1
        rows.append(dict(command_id="case.quota_read."+phase+"."+str(counts[phase]),
                         sql_sha256=hashlib.sha256(sql.encode()).hexdigest()))
    require(len(rows) == sum(parts.values()) == 20, "root_quota_command_count")
    return dict(command_id="case.quota_read", source_method="quota_samples",
        normal_explicit_commands=sum(parts.values()), maximum_explicit_commands=20,
        parts=parts, commands=rows, caller="runtime_case_entry.run", physical_world="local_ci",
        hosted_equivalent_bound=None, normal_and_fault_ceiling_enforced=True,
        lost_rollback_retried=False, implicit_connection_sql_bound=None,
        source_hashes={"runtime_case_entry.py": hashlib.sha256(entry).hexdigest(),
                       PREFIX+"admission_quota_readonly.py": QUOTA_SOURCE_SHA,
                       PREFIX+"integral_io.py": IO_SOURCE_SHA,
                       PREFIX+"integral_stream.py": hashlib.sha256(stream_raw).hexdigest()},
        selected_function_sha256=fn_sha, selected_program_sha256=QUOTA_PROGRAM_SHA,
        actual_runtime_observed=False)


def assemble_root_register(core, *, source_hashes):
    """Export all current core events plus explicit unbound outer dispatchers.

    This is an audit assembly, not a release compiler. Numeric observations and
    declarations such as 128/create do not discharge managed-SQL upper bounds.
    No user-supplied completion flag can turn this export into an admission.
    """
    require(type(core) is dict and set(("dag", "dag_sha256", "model")) <= core.keys(),
            "root_core_shape")
    dag, model = core["dag"], core["model"]
    require(digest(dag) == core["dag_sha256"], "root_core_digest")
    require(model.get("approved_limit") == LIMIT, "root_cap_changed")
    require(model.get("historical_normal") == 2338
            and model.get("historical_closing") == 731, "root_historical_changed")
    require(type(source_hashes) is dict and all(isinstance(k, str)
            and isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
            for k, v in source_hashes.items()), "root_source_hashes")
    # These are independent obligations, not disjoint amounts to add blindly.
    # Child rows link to the retained core DAG instead of charging it twice.
    rows = [
        ("platform_install", "local_pg_install", "case_stack_v1.ci.main -> Gate.install",
         "platform/base install and configure_local_tls precede adapter.run; local prefix not yet joined"),
        ("clean47", "local_pg_build47", "bootstrap(migrations)",
         "startup/DDL/protocol/health/teardown command inventory not joined"),
        ("auth_start", "disposable_auth", "Context.__enter__",
         "GoTrue startup migrations and health SQL not bounded"),
        ("auth_target", "disposable_auth", "Context.__enter__",
         "target attestation, profile seeding and rollback not implemented"),
        ("auth_create", "disposable_auth", "BootstrapRequests.create_all",
         "three create calls reserve 128 each; managed SQL bound unproven"),
        ("quota_read", "local_pg_case", "compile_candidate samples",
         "actual QueryIO dispatcher requires 20 explicit commands; source contract and root hooks must join"),
        ("cli_isolation", "local_pg_case", "PendingPrefix.run",
         "actual 4/8 isolation commands per reached slot outside core require root tickets"),
        ("core_recovery", "local_pg_case", "execute_registered/registered_runner",
         "recovery prefixes, cache state and shared rollback allowances not fully joined"),
        ("fixture_tracking", "local_pg_case", "TrackedRuntime/Scope",
         "tracking, terminality and producer scope protocol not joined to root prefixes"),
        ("fixture_closure", "local_pg_case", "physical.run",
         "physical suffix depends on owned records and exceptional outcomes"),
        ("auth_closure", "disposable_auth", "Context.__exit__",
         "create-only ownership prerequisite and parent cleanup adapter not implemented"),
        ("auth_stop", "disposable_auth", "Context.__exit__",
         "managed teardown SQL bound unknown"),
        ("case_finally", "local_pg_case", "execute_registered finally",
         "identity/scalar rollback state must share already consumed runner allowances"),
    ]
    obligations = [dict(command_id="root:"+ident, domain=domain, source_method=method,
                        upper_bound=None, included_in_root=True,
                        hosted_equivalent=False if ident in ("platform_install", "clean47") else None,
                        missing=reason)
                   for ident, domain, method, reason in rows]
    value = dict(format=FORMAT, approved_limit=LIMIT,
        historical_reference=dict(normal=2338, closing=731, read_only=True),
        core=copy.deepcopy(core), core_events=copy.deepcopy(dag.get("events", [])),
        core_charge_groups=copy.deepcopy(dag.get("charge_groups", {})),
        core_fault_cases=copy.deepcopy(dag.get("fault_cases", {})),
        bootstrap_fault_cases=copy.deepcopy(dag.get("bootstrap_fault_cases", {})),
        root_obligations=obligations, source_hashes=copy.deepcopy(source_hashes),
        core_normal_capacity=model.get("normal_capacity"),
        core_meter_required_limit=model.get("meter_required_limit"),
        total_normal_upper_bound=None, total_fault_upper_bound=None,
        total_local_ci_upper_bound=None, total_hosted_equivalent_upper_bound=None,
        hosted_scope_complete=False, hosted_limit=LIMIT,
        local_ci_compared_to_hosted_limit=False,
        prefix_reserves_complete=False, bound_complete=False, minimal_cap=None,
        fits=False, status="NO_GO", hosted_admitted=False,
        source_inventory_complete=False, commands_excluded_by_domain=[],
        missing_costs=list(model.get("missing_costs", [])) + [r["command_id"] for r in obligations])
    value["full_register_sha256"] = digest(value)
    return value


def build_root_register(source_root, *, runtime_dir=None):
    """Rebuild from the actual loaded candidate, never from caller PASS flags."""
    import admission_budget_current_release as current
    root = pathlib.Path(source_root).resolve(strict=True)
    # The existing strict source-root equality remains intact. Use the candidate
    # import worker when checkout and candidate are different directories.
    core = current.build_current_execution(root, runtime_dir=runtime_dir)
    hashes = dict(core["dag"]["source_hashes"])
    own = pathlib.Path(__file__).resolve()
    require(own == root / PREFIX / own.name, "root_loaded_source_root")
    hashes[PREFIX + own.name] = _source(root, PREFIX + own.name)
    for name in ("runtime_case_entry", "runtime_prefix", "runtime_lifecycle",
                 "runtime_catalog", "runtime_registered_bootstrap"):
        relative = PREFIX + "quota_candidate_v1/" + name + ".py"
        hashes[relative] = _source(root, relative)
    report = assemble_root_register(core, source_hashes=hashes)
    report["quota_read_source_contract"] = quota_sample_contract(root,
        runtime_dir or root / PREFIX / "quota_candidate_v1")
    joined = source_program(root, runtime_dir=runtime_dir)
    report["actual_source_program"] = joined
    report["source_hashes"].update(joined["source_hashes"])
    report["blocked_stage"] = joined["blocked_stage"]
    report["executable_program"] = joined["executable_program"]
    report["missing_costs"] = sorted(set(report["missing_costs"] + joined["missing_costs"]))
    report.pop("full_register_sha256")
    report["full_register_sha256"] = digest(report)
    return report


def _source_record(path):
    raw = _read_bytes(path)
    tree = ast.parse(raw)
    functions, calls = {}, []
    def visit(body, parent=""):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = parent + node.name
                functions[name] = hashlib.sha256(ast.dump(node,
                    include_attributes=False).encode()).hexdigest()
                visit(node.body, name + ".")
    visit(tree.body)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else None
        if name in ("execute", "query", "_sql", "_call", "_local_call", "precharge",
                    "rollback", "connect", "close", "run", "request", "dispatch"):
            literals = [arg.value for arg in node.args[:2] if isinstance(arg, ast.Constant)
                        and isinstance(arg.value, (str, int))]
            # Hash literal SQL/labels instead of exporting source bodies.
            calls.append(dict(line=node.lineno, method=name,
                literal_sha256=[digest(value) for value in literals],
                dynamic_arguments=len(literals) != min(len(node.args), 2)))
    return dict(sha256=hashlib.sha256(raw).hexdigest(), functions=functions,
                dispatch_sites=sorted(calls, key=lambda row: row["line"])), tree


def _literal(tree, name):
    values = [node.value for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
    require(len(values) == 1, "root_source_literal:" + name)
    return ast.literal_eval(values[0])


def _nullable_suffix(rows):
    """Unknown suffixes stay null, not a smaller sum of only known commands."""
    suffix = hosted = 0
    for row in reversed(rows):
        row["reserve_after"] = suffix
        row["hosted_reserve_after"] = hosted
        suffix = None if suffix is None or row["units"] is None else suffix + row["units"]
        hosted = None if hosted is None or row["hosted_units"] is None else hosted + row["hosted_units"]
    return dict(local_upper_bound=suffix, hosted_upper_bound=hosted)


def source_program(source_root, *, runtime_dir=None, context_dir=None, dependency_paths=None):
    """Read-only actual-checkpoint program, with explicit unresolved instructions.

    Separate directories are for offline source handoff only. Public admission
    uses the single candidate tree through build_root_register. This function
    imports no candidate code and performs no process/network/database action.
    """
    root = pathlib.Path(source_root).resolve(strict=True)
    base = root / PREFIX
    runtime = pathlib.Path(runtime_dir or base / "quota_candidate_v1").resolve(strict=True)
    context = pathlib.Path(context_dir or runtime).resolve(strict=True)
    selected = {}
    for path in sorted(runtime.glob("*.py")):
        if not path.name.startswith("test"):
            selected[PREFIX + "quota_candidate_v1/" + path.name] = path
    for name in ("runtime_registered_bootstrap.py", "runtime_registered_startup.py",
                 "runtime_registered_cleanup.py", "runtime_registered_costs.py"):
        selected[PREFIX + "quota_candidate_v1/" + name] = context / name
    for name in ("admission_budget_current_release.py", "admission_budget_current_recovery.py",
                 "admission_budget_register.py", "scenario.py",
                 "registered_runner.py", "registered_lifecycle.py", "safety_auth_native.py",
                 "control_recovery.py", "lifecycle_gates.py",
                 "auth_failure_parent_finalizer.py", "auth_pre_fixture_closure.py",
                 "fixture_producer_scope.py", "native_runtime.py",
                 "case_stack_v1/bootstrap.py", "case_stack_v1/ci.py"):
        selected[PREFIX + name] = base / name
    workflow = "_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py"
    selected[workflow] = root / workflow
    for name in COMPONENT_SOURCES:
        relative = PREFIX + name
        if (base / name).is_file() or relative in (dependency_paths or {}):
            selected[relative] = base / name
    for relative, path in (dependency_paths or {}).items():
        require(relative in selected, "root_unknown_dependency_override")
        selected[relative] = pathlib.Path(path).resolve(strict=True)
    records, trees, paths = {}, {}, {}
    for relative, path in selected.items():
        require(path.is_file() and not path.is_symlink(), "root_source_missing:" + relative)
        records[relative], trees[relative] = _source_record(path)
        paths[relative] = path
    component_bindings = {}
    for name, expected in COMPONENT_SOURCES.items():
        relative = PREFIX + name
        present = relative in records
        if present:
            require(records[relative]["sha256"] == expected, "root_component_source_changed:" + name)
        component_bindings[name] = dict(source=relative, selected=present,
            reviewed_sha256=expected, actual_sha256=records[relative]["sha256"] if present else None)
    own = pathlib.Path(__file__).resolve()
    records[PREFIX + own.name], _ = _source_record(own)
    paths[PREFIX + own.name] = own
    def record(name):
        return records[PREFIX + "quota_candidate_v1/" + name + ".py"]
    def tree(name):
        return trees[PREFIX + "quota_candidate_v1/" + name + ".py"]
    quota = quota_sample_contract(root, runtime)
    life = record("runtime_lifecycle")
    require(all(name in life["functions"] for name in (
        "CasePreservation.prepare_prefix", "CasePreservation.run", "CasePreservation._gate",
        "CasePreservation._final")), "root_actual_lifecycle_missing")
    entry = record("runtime_case_entry")
    require(all(name in entry["functions"] for name in ("execute_registered", "execute_context",
        "execute_bootstrap", "quota_samples", "terminal_witness")), "root_actual_entry_missing")
    entry_functions = {n.name: n for n in tree("runtime_case_entry").body
                       if isinstance(n, ast.FunctionDef)}
    core_deferred = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "defer" and any(k.arg == "partial_observed_sql_commands"
                        for k in n.keywords) for n in ast.walk(entry_functions["execute_context"]))
    native_only = not any(isinstance(n, ast.Constant) and n.value == "managed_auth"
                          for n in ast.walk(entry_functions["observed_core"]))
    startup = tree("runtime_registered_startup")
    declared = [node for node in startup.body
                if isinstance(node, ast.FunctionDef) and node.name == "source_program"]
    require(len(declared) == 1, "root_startup_inventory_missing")
    returns = [node for node in declared[0].body if isinstance(node, ast.Return)]
    require(len(returns) == 1 and isinstance(returns[0].value, ast.Dict), "root_startup_inventory_shape")
    # Only literal inventory fields are extracted. IMAGE is resolved locally;
    # no arbitrary AST expression or module initialization is executed.
    literals = {}
    class InventoryNames(ast.NodeTransformer):
        def visit_Name(self, node):
            require(node.id in ("IMAGE", "READINESS_POLLS", "READINESS_TIMEOUT"), "root_inventory_name")
            return ast.copy_location(ast.Constant(value=_literal(startup, node.id)), node)
    for key, value in zip(returns[0].value.keys, returns[0].value.values):
        name = ast.literal_eval(key)
        if name == "derived_cost_contract":
            expected = ast.parse("costs.source_bound_contract()", mode="eval").body
            require(ast.dump(value, include_attributes=False) == ast.dump(expected, include_attributes=False),
                    "root_derived_contract_call_changed")
            source = record("runtime_registered_costs")
            require("source_bound_contract" in source["functions"], "root_derived_contract_missing")
            literals[name] = dict(source=PREFIX + "quota_candidate_v1/runtime_registered_costs.py",
                source_sha256=source["sha256"], function="source_bound_contract",
                function_ast_sha256=source["functions"]["source_bound_contract"],
                evaluated=False, numeric_bound_accepted=False,
                missing="effective_native_driver_and_OCI_startup_provenance")
        else:
            literals[name] = ast.literal_eval(InventoryNames().visit(copy.deepcopy(value)))
    require(literals["explicit_native_read_ceiling"] == 6
            and literals["seed_normal_explicit_commands"] == 9
            and literals["preseed_scope_explicit_commands"] == 10
            and literals["create_ceiling"] == 3
            and literals["parent_engine_native_formula"] == "3+5*N"
            and literals["parent_engine_delete_declared_formula"] == "128*N",
            "root_startup_inventory_changed")
    missing = (["auth.derived_cost_contract:effective_native_driver_and_OCI_startup_provenance"]
               if "derived_cost_contract" in literals else [])
    def row(ident, units, source, *, explicit=None, process=0, hosted=0, reason=None, group=None):
        if reason:
            missing.append(ident + ":" + reason)
        return dict(command_id=ident, units=units, explicit_sql=explicit,
            process_invocations=process, hosted_units=hosted, source=source,
            physical_world="local_ci", observation_group=group,
            missing=reason, covered_by="case.auth.context" if ident.startswith("auth.")
                or ident in ("case.quota_read", "case.prepare", "case.core") else None)
    startup_rows = []
    native = set(literals["native_reads"])
    sequence = ("pg_inspect", "validate.pg", "pg_password", "validate.connection",
        "observer_connect", "target_before", "auth_backend_before", "validate.target",
        "profile", "managed_stats_before_start", "image_pull", "image_inspect", "validate.image",
        "auth_start", "auth_inspect", "validate.auth", "auth_listen_ready", "health", "auth_target_connection",
        "validate.target_connection")
    startup_calls = {n.args[0].value for n in ast.walk(startup)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "_call"
        and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)}
    require({name for name in sequence if name.startswith("validate.")} <= startup_calls,
            "root_startup_validation_hooks_missing")
    listener = [n for n in ast.walk(startup) if isinstance(n, ast.FunctionDef) and n.name == "_wait_listener"]
    require(len(listener) == 1 and hashlib.sha256(ast.dump(listener[0], include_attributes=False).encode()).hexdigest()
            == "7f01f599eff8f7025dfea64e87d6cdb3c1c93ff3f3c3649f54e2621076581b4c"
            and hashlib.sha256(_literal(startup, "READINESS_SCRIPT").encode()).hexdigest()
            == "0ae4c6f40ea0c1382adaee00278e608620afd056a2bcaa0f90a890fe917f561e",
            "root_passive_readiness_source_changed")
    require(literals["readiness"] == dict(command_id="auth_listen_ready", kind="docker",
            process_attempts=1, passive_poll_ceiling=40, poll_interval_seconds=0.25,
            process_deadline_seconds=12, http_attempts=0, sql_commands=0, mint_barrier=False),
            "root_passive_readiness_inventory")
    for name in sequence:
        if name == "profile":
            bound = component_bindings["admission_auth_runtime_profile.py"]
            startup_rows.append(row("auth.profile", None, "admission_auth_runtime_profile.run",
                explicit=literals["preauth_profile_normal_commands"] if bound["selected"] else None,
                reason="profile_connections_suspend_reconnect_and_fault_edges"))
            startup_rows[-1].update(protocol_explicit_limit=literals["preauth_profile_limit_including_rollback"],
                connection_calls=literals["preauth_profile_connection_calls"],
                source_binding=bound, observation_not_execution=True)
            continue
        unknown = name in ("observer_connect", "auth_start", "health")
        startup_rows.append(row("auth." + name, None if unknown else int(name in native),
            "runtime_registered_startup.LocalServer.open", explicit=int(name in native),
            process=int(name in ("pg_inspect", "pg_password", "image_pull", "image_inspect",
                                "auth_start", "auth_inspect", "auth_listen_ready")),
            reason=("driver_implicit_sql" if name == "observer_connect" else "managed_sql_bound")
                if unknown else None,
            group=MANAGED_OBSERVATION_GROUP if name == "auth_start" else None))
        if name == "auth_listen_ready":
            startup_rows[-1].update(passive_poll_ceiling=40, process_deadline_seconds=12,
                direct_sql_only=True, concurrent_managed_sql_covered_by=MANAGED_OBSERVATION_GROUP)
    create_rows = [row("auth.create." + role, None, "BootstrapRequests._create_owned",
        reason="128_is_declared_reservation_not_managed_upper_bound", group=MANAGED_OBSERVATION_GROUP)
        for role in ("a_member", "a_trainer", "b_member")]
    for item in create_rows:
        item["declared_reservation"] = literals["create_declared_capacity_each"]
    seed_names = ["begin"] + [part + "." + role for role in
        ("a_trainer", "a_member", "b_member") for part in ("profile", "identity")] + ["operator", "commit"]
    seed = [row("auth.seed." + name, 1, "Context._seed", explicit=1) for name in seed_names]
    body = [row("case.quota_read", None, "runtime_case_entry.quota_samples", explicit=20,
                hosted=None, reason="20_explicit_plus_unbound_connection"),
            row("case.prepare", 0, "runtime_case_entry.execute_context", explicit=0),
            row("case.core", None, "runtime_case_entry.execute_registered", hosted=None,
                reason="actual_prefix_recovery_and_managed_partition_join", group=MANAGED_OBSERVATION_GROUP)]
    stop = [row("auth." + name, None if name in ("auth_stop", "observer_close") else int(name in native),
        "runtime_registered_startup.LocalServer.close", explicit=int(name in native),
        process=int(name in ("auth_stop", "auth_stopped_inspect")),
        reason="managed_stop_or_driver_close_sql" if name in ("auth_stop", "observer_close") else None)
        for name in ("auth_stop", "auth_stopped_inspect", "auth_backend_after_stop",
                     "managed_stats_after_stop", "observer_close")]
    normal = startup_rows + create_rows + [row("auth.bootstrap_close", 0, "Context.__enter__", explicit=0)]
    normal += seed + body
    fixture_binding = component_bindings["quota_candidate_v1/runtime_registered_fixture_closeout.py"]
    normal += [row("auth.cleanup.select", 0, "Context._finish -> Ledger.select_cleanup", explicit=0),
        row("auth.fixture_closeout", None, "runtime_registered_fixture_closeout.run",
            explicit=36 if fixture_binding["selected"] else None,
            reason="fixture_connections_suspend_reconnect_and_fault_edges"),
        row("auth.parent_cleanup", None, "Context._finish -> runtime_registered_cleanup.run",
            reason="actual_parent_engine_and_shared_fixture_proof_prefix_join")] + stop
    normal[-len(stop)-2].update(source_binding=fixture_binding,
        protocol_explicit_limit=37 if fixture_binding["selected"] else None,
        original_unknown_zero_only_explicit_sql=23 if fixture_binding["selected"] else None,
        connection_calls=2 if fixture_binding["selected"] else None)
    normal_bound = _nullable_suffix(normal)
    root_order = [row("case.platform.install", None, "case_stack_v1.ci.main -> Gate.install",
                     reason="platform_startup_implicit_SQL_and_process_inventory"),
        row("case.bootstrap.clean47", None, "runtime_case_entry.execute_bootstrap -> bootstrap",
            reason="canonical47_rebuild_CLI_protocol_observers_and_isolation"),
        row("case.auth.context", normal_bound["local_upper_bound"], "Context.__enter__/__exit__",
            hosted=normal_bound["hosted_upper_bound"], reason="child_normal_and_all_fault_suffixes"),
        row("case.terminal", 0, "runtime_case_entry.terminal_witness", explicit=0)]
    root_bound = _nullable_suffix(root_order)
    # Source control predicates are retained, not converted into arbitrary
    # caller-chosen skip edges. A suffix is unreachable until its predicate is
    # witnessed by the source owner and compiled into a fixed case program.
    faults = {
        "bootstrap_selected_pre_or_post": dict(after="case.bootstrap.clean47",
            predicate="PhaseFaults pre_migration/post_migration fired",
            commands=[row("case.bootstrap.failure_closeout", None,
                "runtime_bootstrap_closeout.collect", explicit=4, process=3,
                reason="fresh_connection_implicit_SQL")]),
        "seed_before_commit": dict(predicate="BEGIN attempted and COMMIT not attempted",
            commands=[row("auth.seed.rollback", 1, "Context._seed", explicit=1)] + copy.deepcopy(stop)),
        "seed_commit_unknown": dict(predicate="COMMIT attempted; never retry or rollback", commands=copy.deepcopy(stop)),
        "quota_or_prepare_or_core": dict(predicate="source ticket fault before Context.__exit__",
            commands=[row("auth.fixture_closeout", None, "Context._finish",
                reason="C_physical_suffix_actual_state_and_terminal_join")] + copy.deepcopy(stop)),
    }
    for owners in range(4):
        suffix = [row("auth.observer_suspend", None, "LocalServer.suspend", reason="driver_close_sql"),
            row("auth.scope", None, "runtime_registered_cleanup._State.attest", explicit=10,
                reason="scope_connection_implicit_SQL"),
            row("auth.observer_reconnect", None, "LocalServer.suspend", reason="driver_implicit_SQL"),
            row("auth.engine.connect", None, "Prerequisite.connect", reason="driver_implicit_SQL")]
        roles = ("a", "trainer", "b")[:owners]
        names = ["boundary", "fk_before"] + [role + ":before" for role in roles]
        for role in roles:
            names.extend(role + ":" + phase for phase in
                         ("stats_before_delete", "delete", "stats_after_delete", "after"))
        names += ["fk_after"] + [role + ":final" for role in roles]
        for name in names:
            managed = name.endswith(":delete")
            item = row("auth.engine." + name, None if managed else 1,
                "auth_failure_parent_finalizer.Engine via Prerequisite",
                explicit=0 if managed else 1,
                reason="128_delete_reservation_not_managed_upper_bound" if managed else None,
                group=MANAGED_OBSERVATION_GROUP if managed else None)
            if managed:
                item["declared_reservation"] = 128
            suffix.append(item)
        suffix += [row("auth.engine.close", None, "Prerequisite.close_backend", reason="driver_close_SQL")]
        suffix += copy.deepcopy(stop)
        faults["preseed_owned_" + str(owners)] = dict(
            predicate="complete ownership/seal, not seed_attempted, C Scope PASS; roles in source order",
            owners=owners, commands=suffix,
            native_scope_and_parent=13 + 5*owners,
            declared_delete_reservation=128*owners,
            declared_scope_parent_total=13 + 133*owners,
            excludes_startup_seed_stop_connections=True)
    for fault in faults.values():
        fault.update(_nullable_suffix(fault["commands"]))
    prefixes = []
    for index, item in enumerate(normal):
        ident = item["command_id"]
        if ident.startswith("auth.seed."):
            choices = ["seed_commit_unknown" if ident == "auth.seed.commit" else "seed_before_commit"]
        elif ident in ("case.quota_read", "case.prepare", "case.core", "auth.fixture_closeout"):
            choices = ["quota_or_prepare_or_core"]
        elif ident.startswith("auth.create.") or ident == "auth.bootstrap_close":
            choices = ["preseed_owned_" + str(n) for n in range(4)]
        else:
            choices = []
        retained = normal[:index+1]
        prefix_units = None if any(r["units"] is None for r in retained) else sum(r["units"] for r in retained)
        prefixes.append(dict(after_instruction=ident,
            retained_command_ids=[r["command_id"] for r in retained],
            consumed_reservation=prefix_units, source_conditioned_suffixes=choices,
            rollback_or_stop_state_required=True, refunds=0,
            complete=False, missing="source-owned predicate/zero-SQL validation edge and suffix-failure expansion"))
    joins = dict(
        lifecycle=dict(source_sha256=life["sha256"], methods=life["functions"],
            gate_commands=_literal(tree("runtime_lifecycle"), "GATE_COMMANDS"),
            labels=_literal(tree("runtime_lifecycle"), "LABELS"), covered_by="case.core",
            prefix_order=["history47_preflight4", "stream_before", "gate_before20",
                "append48_pending", "gate_after20", "preauth_cli"],
            label_operations={"before": ["stream", "gate20"], "after_migration": ["gate20"],
                "before_cleanup": ["stream"], "after_cleanup": ["stream", "gate_final_pre11"],
                "final_post": ["gate_final_post9"]}, canonical45_replayed=False),
        recovery=dict(covered_by="case.core", source_methods={name: record(name)["functions"]
            for name in ("runtime_case_entry", "runtime_parent_workflow", "runtime_recovery")},
            known_standalone_probes_not_additive=True,
            missing="shared rollback/cache/meter state and full exceptional prefix expansion"),
        bootstrap=dict(source_sha256=records[PREFIX + "case_stack_v1/bootstrap.py"]["sha256"],
            observed_total_field="bootstrap_total_sql_commands", observed_total=None,
            canonical_history=47, hosted_equivalent=False),
        context=dict(source_sha256=record("runtime_registered_bootstrap")["sha256"],
            managed_group=MANAGED_OBSERVATION_GROUP,
            actual_core_native_defer=core_deferred and native_only,
            missing="postseed C closure and native/managed nonoverlap failure partitions"))
    if not (core_deferred and native_only):
        missing.append("case.core:actual_native_partition_defer_not_in_selected_source")
    missing += ["case.core:actual_recovery_state_expansion", "case.auth.context:conditional_cleanup_edges",
                "case.core:hosted_projection_requires_exact_caller_scope",
                "source_inventory:transitive_dynamic_import_and_subprocess_input_closure"]
    parent = [n for n in trees[PREFIX + "auth_failure_parent_finalizer.py"].body
              if isinstance(n, ast.FunctionDef) and n.name == "finalize"]
    parent_hook = len(parent) == 1 and any(arg.arg == "registered_bootstrap_proof"
                                          for arg in parent[0].args.kwonlyargs)
    joins["context"]["parent_registered_bootstrap_hook"] = parent_hook
    joins["context"]["missing"] = "actual registered hooks exist; state-conditioned SQL/driver/managed fault reserves not fully joined"
    for name, value in component_bindings.items():
        if not value["selected"]:
            missing.append("source_inventory:component_not_selected:" + name)
    if not parent_hook:
        missing.append("auth.engine:parent_finalizer_registered_bootstrap_proof_not_in_selected_source")
    # Reject a mixed snapshot if another owner edited a dependency while read.
    for relative, path in paths.items():
        require(hashlib.sha256(_read_bytes(path)).hexdigest() == records[relative]["sha256"],
                "root_checkpoint_changed:" + relative)
    value = dict(format="admission-actual-root-source-program-v1", model_fields=list(MODEL_FIELDS),
        source_hashes={name: value["sha256"] for name, value in records.items()},
        source_records=records, root_order=root_order, context_normal=normal,
        fault_suffixes=faults, instruction_fault_prefixes=prefixes,
        source_joins=joins, quota_read=quota,
        component_source_bindings=component_bindings,
        current_declared_startup_inventory=literals, managed_observation_group=MANAGED_OBSERVATION_GROUP,
        root_normal=root_bound, context_normal_bounds=normal_bound,
        missing_costs=sorted(set(missing)), blocked_stage="case.platform.install",
        executable_program=None, source_inventory_complete=False, bound_complete=False,
        hosted_scope_complete=False, minimal_cap=None,
        total_local_ci_upper_bound=None, total_hosted_equivalent_upper_bound=None,
        hosted_limit=LIMIT, local_ci_compared_to_hosted_limit=False,
        hosted_admitted=False, actual_execution_evidence=False)
    value["source_program_sha256"] = digest(value)
    return value


def write_source_snapshot(path, report):
    """Exclusive bounded offline export. Existing evidence is never replaced."""
    value = copy.deepcopy(report)
    expected = value.pop("source_program_sha256")
    require(digest(value) == expected, "root_snapshot_digest")
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    require(len(raw) < 2_000_000, "root_snapshot_member_limit")
    path = pathlib.Path(path)
    with path.open("xb") as output:
        require(output.write(raw) == len(raw), "root_snapshot_short_write")
        output.flush()
        os.fsync(output.fileno())
    return dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest(),
                size=len(raw), source_program_sha256=expected,
                blocked_stage=report["blocked_stage"], actual_execution_evidence=False)


def inspect_ci_components(folder):
    """Selected immutable evidence, not an inferred full-case cost or release."""
    root = pathlib.Path(folder).resolve(strict=True)
    selected = {
        "result.json": ("run_id", "commit", "candidate_sha256", "status", "error",
            "clean_rebuild", "admission_components", "admission_secondary_failures",
            "full_chain_admission", "hosted_admitted"),
        "admission-auth-auth-failure-component.json": ("status", "diagnostic_totals",
            "reconciliation_diagnostic_totals", "full_chain_admission"),
        "integral-component-auth-cleanup.json": ("bootstrap_and_cleanup_units",
            "bootstrap_managed_sql_observed", "bootstrap_native_dispatches",
            "full_chain_admission"),
        "fixture-producer-scope-before-result.json": ("status", "reason",
            "admitted_attempts", "emitted_attempts", "protocol_limit"),
    }
    files = {}
    for name, fields in selected.items():
        path = root / name
        require(path.resolve().is_relative_to(root), "root_receipt_escape")
        raw = _read_bytes(path)
        require(len(raw) < 2_000_000, "root_receipt_member_limit")
        value = json.loads(raw)
        require(type(value) is dict, "root_receipt_shape")
        row = dict(sha256=hashlib.sha256(raw).hexdigest(),
                   selected={key: copy.deepcopy(value[key]) for key in fields if key in value})
        if name == "admission-auth-auth-failure-component.json":
            require(type(value.get("cases")) is list, "root_auth_cases_shape")
            row["case_count"] = len(value["cases"])
        files[name] = row
    return dict(format="admission-root-selected-ci-observations-v1", files=files,
        observed_not_upper_bound=True, cross_case_totals_not_single_case=True,
        reservations_not_observed_sql=True, parent_setup_teardown_must_be_added=True,
        proves_current_source=False, bound_complete=False, hosted_admitted=False)


def _register_evidence(out, register, binding):
    """Retain original source proof before any dispatch, never replace a file.

    Fifteen payload members plus one index leave room for 32 ledger journals.
    This is a lossless export, not an independent authorization signature.
    """
    unsigned = {k: v for k, v in register.items() if k != "full_register_sha256"}
    require(digest(unsigned) == register.get("full_register_sha256"), "root_evidence_register_digest")
    value = dict(format="admission-root-original-evidence-v1", register=register,
                 program=register["executable_program"], binding=binding)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(0 < len(raw) <= 15 * 1_000_000, "root_evidence_total_limit")
    out = pathlib.Path(out).resolve(strict=True)
    refs = []
    def write(name, data):
        require(len(data) <= 1_400_000, "root_evidence_member_limit")
        with (out / name).open("xb", buffering=0) as stream:
            require(stream.write(data) == len(data), "root_evidence_short_write")
            os.fsync(stream.fileno())
        require(_read_bytes(out / name) == data, "root_evidence_readback")
        return dict(path=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    for offset in range(0, len(raw), 1_000_000):
        refs.append(write("root-original-%02d.txt" % len(refs), raw[offset:offset+1_000_000]))
    index = dict(format="admission-root-original-index-v1", members=refs,
                 payload_sha256=hashlib.sha256(raw).hexdigest(), payload_bytes=len(raw),
                 register_sha256=register["full_register_sha256"], binding_sha256=digest(binding))
    refs = refs + [write("root-original-index.json", json.dumps(index, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode())]
    return refs


def read_register_evidence(out, refs, *, register_sha256, binding):
    """Pure original-payload validation for archive replay; no admission claim."""
    require(type(refs) is list and 2 <= len(refs) <= 16, "root_evidence_refs")
    root = pathlib.Path(out).resolve(strict=True)
    members = {}
    for ref in refs:
        require(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "root_evidence_ref_shape")
        name = ref["path"]
        require(isinstance(name, str) and (name == "root-original-index.json"
            or re.fullmatch(r"root-original-[0-9]{2}\.txt", name)), "root_evidence_path")
        path = root / name
        require(name not in members and not path.is_symlink() and path.resolve(strict=True).parent == root,
                "root_evidence_duplicate_or_escape")
        require(type(ref["bytes"]) is int and 0 < ref["bytes"] <= 1_400_000
                and path.stat().st_size == ref["bytes"], "root_evidence_size")
        raw = _read_bytes(path)
        require(hashlib.sha256(raw).hexdigest() == ref["sha256"], "root_evidence_modified")
        members[name] = raw
    require("root-original-index.json" in members, "root_evidence_index_missing")
    index = json.loads(members["root-original-index.json"])
    require(index.get("format") == "admission-root-original-index-v1"
            and index.get("members") == refs[:-1]
            and refs[-1]["path"] == "root-original-index.json"
            and [r["path"] for r in refs[:-1]] == ["root-original-%02d.txt" % i for i in range(len(refs)-1)],
            "root_evidence_index_members")
    raw = b"".join(members[r["path"]] for r in index["members"])
    require(len(raw) == index.get("payload_bytes") <= 15 * 1_000_000
            and hashlib.sha256(raw).hexdigest() == index.get("payload_sha256"), "root_evidence_payload_digest")
    value = json.loads(raw)
    register = value["register"]
    require(value.get("format") == "admission-root-original-evidence-v1"
            and value["binding"] == binding and index["binding_sha256"] == digest(binding)
            and value["program"] == register["executable_program"]
            and register["full_register_sha256"] == register_sha256 == index["register_sha256"]
            and digest({k: v for k, v in register.items() if k != "full_register_sha256"}) == register_sha256,
            "root_evidence_binding")
    return value


def open_execution_ledger(gate, *, dag, model, binding):
    """Public pre-bootstrap boundary; current incomplete sources cannot open it."""
    rebuilt = build_root_register(gate.sources)
    require(dag == rebuilt and model == {k: rebuilt[k] for k in MODEL_FIELDS},
        "root_authoritative_register_changed")
    require(rebuilt["bound_complete"] is True and rebuilt["prefix_reserves_complete"] is True
            and rebuilt["source_inventory_complete"] is True
            and rebuilt["hosted_scope_complete"] is True and not rebuilt["missing_costs"]
            and type(rebuilt["total_local_ci_upper_bound"]) is int
            and rebuilt["total_local_ci_upper_bound"] >= 0
            and type(rebuilt["total_hosted_equivalent_upper_bound"]) is int
            and 0 <= rebuilt["total_hosted_equivalent_upper_bound"] <= LIMIT,
            "root_bound_incomplete:" + rebuilt.get("blocked_stage", "source_join"))
    program = rebuilt.get("executable_program")
    require(program is not None, "root_executable_program_join_pending")
    _, _, local, hosted = _program(program)
    require(local == rebuilt["total_local_ci_upper_bound"]
            and hosted == rebuilt["total_hosted_equivalent_upper_bound"],
            "root_program_totals_changed")
    require(binding.get("candidate_sha") == gate.result["candidate_sha256"]
            and binding.get("source_commit") == gate.result.get("commit", gate.result.get("head"))
            and binding.get("ci_run") == gate.result["run_id"], "root_candidate_binding")
    refs = _register_evidence(gate.out, rebuilt, binding)
    return _Ledger(_KEY, gate, program=program, binding=binding,
                   register_sha256=rebuilt["full_register_sha256"], _runtime_origin=_ADMITTED,
                   _source_hashes=rebuilt["source_hashes"], _evidence_refs=refs)


def require_runtime_ledger(gate, ledger, *, command_id):
    """Public source-owner guard before a wrapper starts any external action."""
    require(type(ledger) is _Ledger and ledger._gate is gate
            and ledger._runtime_origin is _ADMITTED and ledger._source_hashes,
            "root_runtime_actual_owner")
    require(not ledger._closed and not ledger._journal_failed
            and ledger._pending is None and ledger._next is not None,
            "root_runtime_not_dispatchable")
    row = ledger._program[ledger._next]
    require(row["command_id"] == command_id and (not ledger._stopped or row["safety_only"]),
            "root_runtime_instruction")
    root = pathlib.Path(gate.sources).resolve(strict=True)
    for name, expected in ledger._source_hashes.items():
        relative = name if name.startswith("_offline/") else PREFIX + name
        require(_source(root, relative) == expected, "root_runtime_source_changed:" + name)
    return dict(command_id=command_id, units=row["units"], reserve_after=row["reserve_after"],
        hosted_units=row["hosted_units"], hosted_reserve_after=row["hosted_reserve_after"],
        register_sha256=ledger._sha, run_id=ledger._binding["run_id"])


def install_platform(gate, *, ledger):
    require_runtime_ledger(gate, ledger, command_id="case.platform.install")
    from install_platform import install_platform as execute
    return execute(gate, ledger=ledger)


def validate_terminal(ledger, gate, binding):
    """Validate numeric accounting, never substitute for D/B/C termination proofs."""
    require(type(ledger) is _Ledger and ledger._gate is gate
            and ledger._binding == binding and ledger._runtime_origin is _ADMITTED,
            "root_terminal_actual_owner")
    require(ledger._source_hashes, "root_terminal_sources_missing")
    original = read_register_evidence(gate.out, ledger._evidence_refs,
                                     register_sha256=ledger._sha, binding=binding)
    program = original["program"]
    for node_id in ledger._program_path:
        program = _program(program)[0][node_id]["children"]
    require(_program(program)[0] == ledger._program,
            "root_terminal_original_program_changed")
    root = pathlib.Path(gate.sources).resolve(strict=True)
    for name, expected in ledger._source_hashes.items():
        relative = name if name.startswith("_offline/") else PREFIX + name
        require(_source(root, relative) == expected, "root_terminal_source_changed:" + name)
    def check(current):
        current.validate_journal()
        receipt = current.receipt()
        require(current._runtime_origin is _ADMITTED and current._sha == ledger._sha
                and current._binding == binding and receipt["closed"]
                and receipt["program_exhausted"] and receipt["remaining_command_id"] is None
                and not receipt["journal_failed"] and not receipt["pending"]
                and receipt["deferred_observations"] == 0 and receipt["active_envelopes"] == 0,
                "root_terminal_not_closed")
        unions = {u["sha256"]: u for u in receipt["numeric_unions"]}
        for event in receipt["events"]:
            state = event["state"]
            require(state in ("confirmed", "fault_numeric_confirmed", "covered_by_numeric_union"),
                    "root_terminal_unknown_consumption")
            if state == "covered_by_numeric_union":
                union = unions.get(event.get("numeric_union_sha256"))
                require(union is not None and event["command_id"] in union["command_ids"],
                        "root_terminal_union_reference")
            else:
                require(event["numeric_confirmed"] is True, "root_terminal_numeric_missing")
        require(receipt["observed_sql_commands"] <= receipt["reserved_consumed"] <= current._local_bound
                and receipt["hosted_equivalent_reserved"] <= current._hosted_limit,
                "root_terminal_capacity")
        for child in current._children:
            check(child)
        return receipt
    receipt = check(ledger)
    return dict(format="admission-root-numeric-terminal-v1", status="NUMERIC_ACCOUNTING_CLOSED",
        register_sha256=ledger._sha, run_id=binding["run_id"],
        reserved_consumed=receipt["reserved_consumed"], observed_sql_commands=receipt["observed_sql_commands"],
        hosted_equivalent_reserved=receipt["hosted_equivalent_reserved"], hosted_limit=LIMIT,
        local_source_bound=receipt["local_source_bound"], fault_retained=receipt["stopped"],
        journal_refs=receipt["journal_refs"], evidence_refs=copy.deepcopy(ledger._evidence_refs),
        program_path=list(ledger._program_path),
        full_chain_admission=False, hosted_admitted=False)


class _Ticket:
    __slots__ = ("owner", "ordinal", "command_id", "units", "terminal", "node_id")

    def __init__(self, owner, ordinal, command_id, units):
        self.owner, self.ordinal, self.command_id = owner, ordinal, command_id
        self.units, self.terminal = units, False
        self.node_id = owner._next


class _Ledger:
    """Offline-tested ticket mechanics, not a caller-constructible admission.

    Each instruction is an authoritative dispatch with a remaining-prefix
    reserve. Managed children are covered by their one parent instruction;
    callers cannot choose units, successors, domains, refunds or reserve drops.
    """
    def __init__(self, key, gate, *, program, binding, register_sha256,
                 _journal_name="root-ledger-private", _hosted_limit=LIMIT, _depth=0,
                 _journals=None, _runtime_origin=None, _source_hashes=None, _evidence_refs=None,
                 _program_path=()):
        require(key is _KEY, "root_compiler_origin_required")
        require(type(_depth) is int and 0 <= _depth < 8, "root_envelope_depth")
        require(type(_hosted_limit) is int and 0 <= _hosted_limit <= LIMIT, "root_projection_limit")
        nodes, entry, local_bound, _ = _program(program)
        require(type(binding) is dict and isinstance(binding.get("run_id"), str), "root_binding")
        parsed = uuid.UUID(binding["run_id"])
        require(str(parsed) == binding["run_id"] and binding["run_id"] !=
                "6f8c8909-9b79-4011-a9d1-db5e23c6b6c1", "root_fresh_binding_required")
        require(isinstance(register_sha256, str)
                and re.fullmatch(r"[0-9a-f]{64}", register_sha256), "root_register_hash")
        self._gate, self._program, self._next = gate, nodes, entry
        self._binding, self._sha = copy.deepcopy(binding), register_sha256
        self._index, self._used, self._observed = 0, 0, 0
        self._hosted_used, self._local_bound = 0, local_bound
        self._hosted_limit, self._depth = _hosted_limit, _depth
        self._journals = [0] if _journals is None else _journals
        require(self._journals[0] < 32, "root_journal_member_count")
        self._journals[0] += 1
        self._pending, self._stopped, self._events = None, False, []
        self._deferred, self._envelopes = {}, {}
        self._children = []
        self._unions = []
        self._journal_failed = False
        self._closed = False
        self._runtime_origin = _runtime_origin
        self._source_hashes = copy.deepcopy(_source_hashes or {})
        self._evidence_refs = copy.deepcopy(_evidence_refs or [])
        self._program_path = tuple(_program_path)
        self._sequence = 0
        self._journal = pathlib.Path(gate.out) / (_journal_name + ".ledger.txt")
        # A fresh artifact directory is required. Never truncate an old ledger.
        fd = os.open(self._journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        self._journal_sha256 = hashlib.sha256(b"").hexdigest()

    def receipt(self):
        return dict(format="admission-root-ledger-unit-contract-v1",
            register_sha256=self._sha, binding=copy.deepcopy(self._binding),
            hosted_limit=LIMIT, local_source_bound=self._local_bound,
            reserved_consumed=self._used, hosted_equivalent_reserved=self._hosted_used,
            covered_child_allocations_not_added=True, deferred_observations=len(self._deferred),
            numeric_unions=copy.deepcopy(self._unions),
            remaining_command_id=self._next, active_envelopes=len(self._envelopes),
            journal_failed=self._journal_failed, program_exhausted=self._next is None,
            journal_refs=self.journal_refs(),
            observed_sql_commands=self._observed, refundable_units=0,
            pending=self._pending is not None, stopped=self._stopped,
            events=copy.deepcopy(self._events),
            closed=self._closed,
            runtime_admitted=self._runtime_origin is _ADMITTED,
            full_chain_admission=False, hosted_admitted=False)

    def deferred_group(self, group):
        """Stable ticket order; no caller access to mutable program internals."""
        require(isinstance(group, str) and group, "root_union_group")
        return tuple(sorted((t for t in self._deferred
            if self._program[t.node_id]["observation_group"] == group),
            key=lambda t: t.ordinal))

    def select_cleanup(self, context):
        """Only the bound B finalizer can select its preregistered state branch."""
        import inspect
        import sys
        module = sys.modules.get("quota_candidate_v1.runtime_registered_bootstrap")
        require(module is not None and type(context) is getattr(module, "Context", None),
                "root_cleanup_actual_context")
        frame = inspect.currentframe().f_back
        try:
            require(frame.f_code is module.Context._finish.__code__
                    and frame.f_locals.get("self") is context, "root_cleanup_actual_finalizer")
            primary = frame.f_locals.get("primary")
        finally:
            del frame
        require(context.execution_ledger is self and context.gate is self._gate
                and context.binding == self._binding and context._closing
                and not context._cleanup_selected, "root_cleanup_owner_binding")
        require_runtime_ledger(self._gate, self, command_id="auth.cleanup.select")
        relative = PREFIX + "quota_candidate_v1/runtime_registered_bootstrap.py"
        require(hashlib.sha256(_read_bytes(pathlib.Path(module.__file__))).hexdigest()
                == self._source_hashes.get(relative), "root_cleanup_loaded_source")
        context._validate()
        server, producer = context.server, context.producer
        owned = tuple(producer._owned) if producer is not None else ()
        require(set(owned) <= {"a_member", "a_trainer", "b_member"}, "root_cleanup_owner_roles")
        state = dict(server=server is not None, producer=producer is not None,
            db_open=server is not None and server.db is not None and not server.db.closed,
            auth_start_attempted=server is not None and server.start_attempted,
            auth_container_known=server is not None and server.container_id is not None,
            managed_baseline=server is not None and server.started_stats is not None,
            owned_roles=sorted(owned), seed_attempted=context._seed_attempted,
            yielded=context._yielded, case_bound=context._case is not None,
            primary_failure=primary is not None)
        return self._select_cleanup_state(_KEY, state)

    def _select_cleanup_state(self, key, state):
        require(key is _KEY, "root_cleanup_source_origin")
        require(self._pending is None and self._next is not None, "root_cleanup_pending")
        row = self._program[self._next]
        cases = row["selection_cases"]
        state_sha = digest(state)
        require(cases is not None and state_sha in cases, "root_cleanup_state_unregistered")
        ticket = self.precharge("auth.cleanup.select")
        self._events[-1].update(state="confirmed", numeric_confirmed=True,
            observed_sql_commands=0, cleanup_state=copy.deepcopy(state), selected_node=cases[state_sha])
        ticket.terminal = True
        self._save()
        self._pending = None
        self._next = cases[state_sha]
        self._index += 1
        return dict(state_sha256=state_sha, next_command_id=self._program[self._next]["command_id"],
                    source_selected=True, refunds=0)

    def close(self):
        """Seal accounting only, never infer SQL completion or case admission."""
        require(not self._journal_failed and not self._closed, "root_close_unavailable")
        require(self._next is None and self._pending is None
                and not self._deferred and not self._envelopes, "root_close_incomplete")
        self._closed = True
        self._save()
        return self.receipt()

    def journal_refs(self):
        raw = self._journal_bytes()
        refs = [dict(path=self._journal.name, sha256=hashlib.sha256(raw).hexdigest(),
                     size=len(raw), encoding="unchanged-ndjson-bytes")]
        for child in self._children:
            refs.extend(child.journal_refs())
        return refs

    def _journal_bytes(self):
        raw = _read_bytes(self._journal)
        if hashlib.sha256(raw).hexdigest() != self._journal_sha256 and not self._journal_failed:
            self._journal_failed = self._stopped = True
            raise RootBlocked("root_journal_modified")
        return raw

    def validate_journal(self):
        raw = self._journal_bytes()
        events, unions = {}, {}
        previous = b""
        records = raw.splitlines(keepends=True)
        for index, line in enumerate(records):
            value = json.loads(line)
            require(value["sequence"] == index + 1
                    and value["register_sha256"] == self._sha
                    and value["previous_bytes_sha256"] == hashlib.sha256(previous).hexdigest(),
                    "root_journal_chain")
            if value["event"] is not None:
                events[value["event_ordinal"]] = value["event"]
            if "numeric_union" in value:
                union = value["numeric_union"]
                unsigned = {k: v for k, v in union.items() if k != "sha256"}
                require(digest(unsigned) == union["sha256"], "root_journal_union_digest")
                unions[union["sha256"]] = union
            previous += line
        require(len(records) == self._sequence
                and events == dict(enumerate(self._events))
                and unions == {u["sha256"]: u for u in self._unions}, "root_journal_memory_mismatch")
        if records:
            require(value["reserved_consumed"] == self._used
                    and value["observed_sql_commands"] == self._observed
                    and value["hosted_equivalent_reserved"] == self._hosted_used
                    and value["stopped"] == self._stopped and value["closed"] == self._closed,
                    "root_journal_totals_mismatch")
        return dict(sequence=self._sequence, sha256=self._journal_sha256, size=len(raw))

    def _save(self, event_index=None):
        try:
            # State may already be mutated; every publication failure is terminal.
            previous = self._journal_bytes()
            self._sequence += 1
            # One bounded append-only member, not thousands of artifact members.
            value = dict(sequence=self._sequence, register_sha256=self._sha,
                previous_bytes_sha256=self._journal_sha256,
                event_ordinal=(event_index if event_index is not None else len(self._events)-1),
                reserved_consumed=self._used, observed_sql_commands=self._observed,
                hosted_equivalent_reserved=self._hosted_used,
                stopped=self._stopped, closed=self._closed,
                event=self._events[event_index if event_index is not None else -1] if self._events else None)
            if value["event"] is not None and value["event"].get("numeric_union_sha256"):
                value["numeric_union"] = next(u for u in self._unions
                    if u["sha256"] == value["event"]["numeric_union_sha256"])
            data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
            require(self._journal.stat().st_size + len(data) <= 1_400_000,
                    "root_journal_member_limit")
            with self._journal.open("ab", buffering=0) as stream:
                require(stream.write(data) == len(data), "root_journal_short_write")
                os.fsync(stream.fileno())
            expected = hashlib.sha256(previous + data).hexdigest()
            require(hashlib.sha256(_read_bytes(self._journal)).hexdigest() == expected,
                    "root_journal_append_readback")
            self._journal_sha256 = expected
        except BaseException:
            self._stopped = True
            self._journal_failed = True
            raise

    def precharge(self, command_id):
        require(not self._journal_failed, "root_journal_failed")
        require(not self._closed, "root_ledger_closed")
        require(self._pending is None, "root_not_dispatchable")
        require(self._next is not None, "root_program_exhausted")
        row = self._program[self._next]
        require(not self._stopped or row["safety_only"], "root_not_dispatchable")
        require(command_id == row["command_id"], "root_command_order")
        require(self._used + row["units"] + row["reserve_after"] <= self._local_bound,
                "root_local_source_bound")
        require(self._hosted_used + row["hosted_units"] + row["hosted_reserve_after"] <= self._hosted_limit,
                "root_prefix_capacity")
        self._used += row["units"]
        self._hosted_used += row["hosted_units"]
        ticket = _Ticket(self, self._index, command_id, row["units"])
        self._pending = ticket
        event = {key: copy.deepcopy(value) for key, value in row.items() if key != "children"}
        if row["children"] is not None:
            event["child_program_sha256"] = digest(row["children"])
        self._events.append(dict(event, state="precharged", numeric_confirmed=False))
        self._save()
        return ticket

    def _ticket(self, ticket):
        require(not self._journal_failed, "root_journal_failed")
        require(not self._closed, "root_ledger_closed")
        require(type(ticket) is _Ticket and ticket.owner is self
                and ticket is self._pending and not ticket.terminal, "root_ticket_identity")
        row = self._program[self._next]
        require(ticket.ordinal == self._index and ticket.units == row["units"]
                and ticket.command_id == row["command_id"] and ticket.node_id == self._next,
                "root_ticket_changed")
        require(not self._stopped or row["safety_only"], "root_stopped")

    def confirm(self, ticket, *, observed_sql_commands):
        self._ticket(ticket)
        require(ticket not in self._envelopes, "root_envelope_requires_close")
        require(type(observed_sql_commands) is int and observed_sql_commands >= 0,
                "root_numeric_count")
        self._observed += observed_sql_commands
        if observed_sql_commands > ticket.units:
            self._stopped = True
            self._events[-1].update(state="overrun", observed_sql_commands=observed_sql_commands)
            self._save()
            raise RootBlocked("root_observed_overrun")
        self._events[-1].update(state="confirmed", numeric_confirmed=True,
                               observed_sql_commands=observed_sql_commands)
        ticket.terminal = True
        self._save()
        self._pending = None
        self._next = self._program[self._next]["next_confirmed"]
        self._index += 1

    def unknown(self, ticket, *, reason):
        self._ticket(ticket)
        require(ticket not in self._envelopes, "root_envelope_requires_close")
        require(reason in ("lost_response", "interrupted", "not_terminal", "validation_failed"),
                "root_unknown_reason")
        state = "fault_numeric_confirmed" if self._events[-1]["numeric_confirmed"] else "unknown_consumed"
        self._events[-1].update(state=state, reason=reason)
        self._stopped = True
        ticket.terminal = True
        self._save()
        self._pending = None
        self._next = self._program[self._next]["next_unknown"]
        self._index += 1

    def fault(self, ticket, *, observed_sql_commands, reason="validation_failed"):
        """Known numeric consumption is compatible with a failed case, not PASS."""
        self._ticket(ticket)
        require(type(observed_sql_commands) is int and 0 <= observed_sql_commands <= ticket.units,
                "root_fault_numeric_count")
        require(reason in ("lost_response", "interrupted", "not_terminal", "validation_failed"),
                "root_unknown_reason")
        self._observed += observed_sql_commands
        self._events[-1].update(observed_sql_commands=observed_sql_commands, numeric_confirmed=True)
        self.unknown(ticket, reason=reason)

    def defer(self, ticket, *, partial_observed_sql_commands=0):
        """Only source-declared asynchronous work; no health-as-terminal claim."""
        self._defer(ticket, failed=False, partial=partial_observed_sql_commands)

    def defer_fault(self, ticket, *, partial_observed_sql_commands=0):
        self._defer(ticket, failed=True, partial=partial_observed_sql_commands)

    def _defer(self, ticket, *, failed, partial):
        self._ticket(ticket)
        row = self._program[self._next]
        require(row["defer"] and ticket not in self._envelopes, "root_defer_not_registered")
        require(type(partial) is int and 0 <= partial <= row["units"]-row["observation_units"],
                "root_partial_observation_bound")
        self._observed += partial
        if failed:
            self._stopped = True
        self._events[-1].update(state="fault_measurement_pending" if failed else "dispatched_measurement_pending",
                               partial_observed_sql_commands=partial)
        self._save()
        self._deferred[ticket] = ticket.ordinal
        self._pending = None
        self._next = row["next_unknown"] if failed else row["next_confirmed"]
        self._index += 1

    def settle_deferred(self, ticket, *, observed_sql_commands=None):
        require(not self._journal_failed, "root_journal_failed")
        require(type(ticket) is _Ticket and ticket.owner is self and ticket in self._deferred
                and not ticket.terminal, "root_deferred_ticket")
        require(self._next is None and self._pending is None, "root_deferred_before_foreground_close")
        row = self._program[ticket.node_id]
        require(row["observation_group"] is None, "root_group_requires_union")
        require(ticket.units == row["units"] and ticket.ordinal == self._deferred[ticket],
                "root_ticket_changed")
        event = self._events[ticket.ordinal]
        if observed_sql_commands is None:
            self._stopped = True
            event.update(state="unknown_consumed", numeric_confirmed=False)
        else:
            require(type(observed_sql_commands) is int
                    and 0 <= observed_sql_commands <= row["observation_units"],
                    "root_deferred_numeric_count")
            self._observed += observed_sql_commands
            event.update(state="confirmed", numeric_confirmed=True,
                         observed_sql_commands=observed_sql_commands)
        self._save(ticket.ordinal)
        ticket.terminal = True
        del self._deferred[ticket]

    def settle_union(self, tickets, *, observed_sql_commands):
        """A single caller-validated non-overlapping managed lifetime interval.

        No per-request numeric value is manufactured. Group members retain
        reservations and link to the one aggregate observation instead.
        """
        require(not self._journal_failed, "root_journal_failed")
        require(type(tickets) in (list, tuple) and tickets and len(set(tickets)) == len(tickets),
                "root_union_members")
        require(self._next is None and self._pending is None, "root_deferred_before_foreground_close")
        require(all(type(t) is _Ticket and t.owner is self and t in self._deferred
                    and not t.terminal for t in tickets), "root_union_tickets")
        group = self._program[tickets[0].node_id]["observation_group"]
        require(group is not None and all(self._program[t.node_id]["observation_group"] == group
                for t in tickets), "root_union_group")
        require(set(tickets) == {t for t in self._deferred
                if self._program[t.node_id]["observation_group"] == group}, "root_union_incomplete")
        require(not any(e.get("observation_group") == group
                and e["state"] in ("unknown_consumed", "overrun", "fault_numeric_confirmed", "confirmed")
                for e in self._events), "root_union_unknown_or_already_counted_partition")
        require(all(t.units == self._program[t.node_id]["units"]
                    and t.ordinal == self._deferred[t] for t in tickets), "root_ticket_changed")
        units = sum(self._program[t.node_id]["observation_units"] for t in tickets)
        require(type(observed_sql_commands) is int and 0 <= observed_sql_commands <= units,
                "root_union_numeric_bound")
        union = dict(group=group, command_ids=[t.command_id for t in tickets],
                     observed_sql_commands=observed_sql_commands, reserved_consumed=units,
                     per_request_attribution=False)
        union["sha256"] = digest(union)
        self._observed += observed_sql_commands
        self._unions.append(union)
        for ticket in tickets:
            self._events[ticket.ordinal].update(state="covered_by_numeric_union",
                numeric_confirmed=False, numeric_union_sha256=union["sha256"])
            self._save(ticket.ordinal)
            ticket.terminal = True
            del self._deferred[ticket]

    def open_envelope(self, command_id):
        require(self._next == command_id and self._program[command_id]["children"] is not None,
                "root_envelope_not_registered")
        row = self._program[command_id]
        ticket = self.precharge(command_id)
        name = "root-ledger-" + digest([self._journal.name, command_id])[:24]
        child = _Ledger(_KEY, self._gate, program=row["children"], binding=self._binding,
                        register_sha256=self._sha, _journal_name=name,
                        _hosted_limit=row["hosted_units"], _depth=self._depth+1,
                        _journals=self._journals, _runtime_origin=self._runtime_origin,
                        _source_hashes=self._source_hashes, _evidence_refs=self._evidence_refs,
                        _program_path=self._program_path + (ticket.node_id,))
        self._envelopes[ticket] = child
        self._children.append(child)
        return ticket, child

    def close_envelope(self, ticket, child, *, observed_sql_commands=None):
        self._ticket(ticket)
        require(self._envelopes.get(ticket) is child and child._next is None
                and child._pending is None and not child._deferred and not child._envelopes,
                "root_envelope_incomplete")
        # An aggregate numeric union is validated by the source-owned caller;
        # it is never calculated by summing overlapping parent/child samples.
        if observed_sql_commands is not None:
            require(type(observed_sql_commands) is int
                    and child._observed <= observed_sql_commands <= ticket.units,
                    "root_envelope_numeric_union")
        del self._envelopes[ticket]
        if child._stopped or observed_sql_commands is None:
            if observed_sql_commands is None:
                self.unknown(ticket, reason="not_terminal")
            else:
                self.fault(ticket, observed_sql_commands=observed_sql_commands)
        else:
            self.confirm(ticket, observed_sql_commands=observed_sql_commands)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Source-only root checkpoint; never launches a runtime")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--runtime-dir")
    parser.add_argument("--context-dir")
    parser.add_argument("--parent-finalizer")
    parser.add_argument("--case-entry", help="Explicit isolated A1 entry checkpoint, audit only")
    parser.add_argument("--out", required=True, help="New unique JSON member; never overwrite")
    args = parser.parse_args()
    overrides = {}
    if args.parent_finalizer:
        overrides[PREFIX + "auth_failure_parent_finalizer.py"] = args.parent_finalizer
    if args.case_entry:
        overrides[PREFIX + "case_stack_v1/ci.py"] = args.case_entry
    report = source_program(args.source_root, runtime_dir=args.runtime_dir,
                            context_dir=args.context_dir, dependency_paths=overrides)
    print(json.dumps(write_source_snapshot(args.out, report), sort_keys=True))


if __name__ == "__main__":
    main()
