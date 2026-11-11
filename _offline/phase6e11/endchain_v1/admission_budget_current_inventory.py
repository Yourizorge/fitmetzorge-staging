"""Current source-derived deltas, separate from frozen reference registers.

Rendering SQL and parsing its statement count are offline operations. No SQL,
Auth, CLI, migration, subprocess, connection or file writer is invoked here.
"""
import ast
import collections
import copy
import hashlib
import importlib.util

from admission_budget import HERE, require
from admission_budget_register import canonical_sha, source
from sql_protocol import statements


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _renderer(name, relative):
    path = (HERE / relative).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def installation_groups():
    """Count real install and inspect calls separately; never prepay an inspect early."""
    run = "41998cee-8026-45fc-b352-40b524f54a85"
    ids = dict(a_member="45a73446-b19e-4f8d-b749-c4c67fb63c4c",
               a_trainer="0241a820-8175-42bb-a077-d50816b330fe",
               b_member="02206841-c0a9-425e-a97d-0d9f12946af2")
    guard = _renderer("budget_source_guard", "../controller_guard_v1/guard.py")
    audit = _renderer("budget_source_audit", "../auth_metadata_v1/audit.py")
    result = []
    for action, module, relative, args in (
            ("guard_install", guard, "../controller_guard_v1/guard.py", (run, ids, 180)),
            ("metadata_install", audit, "../auth_metadata_v1/audit.py",
             (run, ids, "2100-01-01T00:00:00+00:00"))):
        install = statements(module.install(*args))
        inspect = statements(module.inspect(run, ids))
        require(len(inspect) == 1, "installation_inspect_single")
        result.append(dict(action=action, install_commands=len(install), inspect_commands=1,
            source=source(relative, "install/inspect"), rendered_sql_executed=False,
            source_templates=[dict(kind=s["kind"], protocol_commands=1) for s in install]))
    return result


def control_io_delta():
    """A new query family costs exactly bind + sample, never a guessed reserve."""
    from control_recovery import BEFORE_SQL, CONTROL_SQL
    from integral_io import SNAPSHOT
    tree = ast.parse((HERE / "integral_io.py").read_text())
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "QueryIO")
    bind = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "bind")
    calls = [n for n in ast.walk(bind) if isinstance(n, ast.Call)]
    query = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "query"]
    sample = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "sample"]
    require(len(query) == len(sample) == 1
            and isinstance(query[0].args[1], ast.Constant) and query[0].args[1].value == "io_bind",
            "queryio_bind_count_changed")
    require(isinstance(query[0].args[2], ast.BinOp)
            and ast.literal_eval(query[0].args[2].left) == "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) "
            and isinstance(query[0].args[2].right, ast.Name) and query[0].args[2].right.id == "sql",
            "queryio_bind_template_changed")
    require(BEFORE_SQL != CONTROL_SQL, "control_family_not_distinct")
    return dict(before_sql_sha256=_sha(BEFORE_SQL), control_sql_sha256=_sha(CONTROL_SQL),
        additional_commands=2, source=source("integral_io.py", "QueryIO.bind/sample"),
        control_source=source("control_recovery.py", "BEFORE_SQL/CONTROL_SQL"),
        rows=[dict(action="io_bind", text="EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) " + CONTROL_SQL),
              dict(action="io_sample", text=SNAPSHOT)],
        scope="current normal workflow only; no complete recovery or hosted bound")


def derive_current_plan(report):
    """Produce version 3 with proven deltas; preserve the supplied report verbatim."""
    from control_recovery import BEFORE_SQL, CONTROL_SQL
    from integral_io import SNAPSHOT
    original = report["current_plan"]
    require(canonical_sha({k: v for k, v in original.items() if k != "plan_sha256"})
            == original["plan_sha256"], "inventory_input_changed")
    plan = copy.deepcopy(original)
    normal = plan["normal"]
    rows, groups = normal["rows"], normal["charge_groups"]
    changes = []
    installs = installation_groups()
    for item in installs:
        selected = [row for row in rows if row["action"] == item["action"]]
        require(len(selected) == item["install_commands"] + 1, "installation_register_shape")
        old = groups.pop(item["action"])
        install_group, inspect_group = item["action"] + ":batch", item["action"] + ":inspect"
        for index, row in enumerate(selected):
            row["charge_group"] = install_group if index < item["install_commands"] else inspect_group
            row["dispatch_source"] = item["source"]
        for key, selected_rows in ((install_group, selected[:-1]), (inspect_group, selected[-1:])):
            groups[key] = dict(capacity=len(selected_rows), nodes=[r["id"] for r in selected_rows],
                               phase=old["phase"], accounting_source=source("metered_composition.py", "before_sql"))
        changes.append(dict(kind="split_install_and_inspect_tickets", action=item["action"],
                            previous_capacity=old["capacity"], current_capacity=len(selected),
                            tickets=[item["install_commands"], 1], source=item["source"], normal_delta=0))

    # Existing QueryIO samples and explain/closing templates now include the
    # current SNAPSHOT fields. This is a source identity replacement, not SQL.
    sample_hashes = {r["sql_sha256"] for r in rows if r["action"] == "io_sample"}
    require(len(sample_hashes) == 1, "historical_io_sample_family")
    first_reader = next(i for i, row in enumerate(rows) if row["action"] == "lifecycle_reader_check")
    require(rows[first_reader + 1]["action"] == "io_bind", "io_start_anchor")
    replacements = {next(iter(sample_hashes)): SNAPSHOT,
        rows[first_reader + 1]["sql_sha256"]: "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) " + SNAPSHOT}
    closing_hashes = {r["sql_sha256"] for r in rows if r["action"] == "io_closing_witness"}
    require(len(closing_hashes) == 1, "historical_io_closing_family")
    replacements[next(iter(closing_hashes))] = "EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) " + SNAPSHOT
    for row in rows:
        old_sha = row.get("sql_sha256")
        if old_sha in replacements:
            row.update(sql_sha256=_sha(replacements[old_sha]), previous_sql_sha256=old_sha,
                       source=source("integral_io.py", "QueryIO"), classification="current_source_template")

    before = [i for i, row in enumerate(rows) if row["action"] == "control_before"]
    after = [i for i, row in enumerate(rows) if row["action"] == "control_after"]
    require(len(before) == len(after) == 1 and before[0] < after[0], "control_pair_anchors")
    before_index, after_index = before[0], after[0]
    require(rows[before_index]["sql_sha256"] == _sha(CONTROL_SQL)
            and rows[after_index]["sql_sha256"] == _sha(CONTROL_SQL), "reference_control_family")
    require([r["action"] for r in rows[before_index - 2:before_index]] == ["io_bind", "io_sample"],
            "control_first_bind_anchor")
    rows[before_index - 2].update(sql_sha256=_sha("EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) " + BEFORE_SQL),
        source=source("control_recovery.py", "BEFORE_SQL"), classification="current_source_template")
    rows[before_index].update(sql_sha256=_sha(BEFORE_SQL), source=source("control_recovery.py", "BEFORE_SQL"),
                             classification="current_source_template")
    delta = control_io_delta()
    additions = []
    for index, item in enumerate(delta["rows"]):
        ident = "current_control_after_first_family_" + str(index)
        additions.append(dict(id=ident, action=item["action"], phase="io", cost=1, kind="native",
            sql_sha256=_sha(item["text"]), source=delta["source"], retained_ids=[], state_after={},
            action_binding=copy.deepcopy(rows[after_index]["action_binding"]),
            charge_group=ident, classification="current_source_template", execution_ready=False))
        groups[ident] = dict(capacity=1, nodes=[ident], phase="io")
    rows[after_index:after_index] = additions
    changes.append(dict(kind="first_control_sql_query_family", normal_delta=2,
                        row_ids=[r["id"] for r in additions], source=delta["source"],
                        control_source=delta["control_source"]))
    phases, kinds = collections.Counter(), collections.Counter()
    for ordinal, row in enumerate(rows):
        row["ordinal"] = ordinal
        phases[row["phase"]] += row["cost"]
        kinds[row["kind"]] += row["cost"]
    normal.update(normal_capacity=sum(phases.values()), phase_capacities=dict(phases), kind_capacities=dict(kinds))
    plan.update(version="admission-current-plan-v3", parent_plan_sha256=original["plan_sha256"],
                source_derived_changes=changes, reference_prefix_bindings_not_current=True,
                bound_complete=False, minimal_cap=None, runtime_adapter_wired=False)
    for item in changes:
        for field in ("source", "control_source"):
            if field in item:
                binding = item[field]
                plan["current_source_hashes"][binding["path"]] = binding["sha256"]
    for name in ("admission_budget_current_inventory.py", "integral_io.py", "control_recovery.py"):
        binding = source(name, "current_plan_source")
        plan["current_source_hashes"][binding["path"]] = binding["sha256"]
    plan["plan_sha256"] = canonical_sha({k: v for k, v in plan.items() if k != "plan_sha256"})
    return plan
