"""Actual source joins for the opt-in compiler, independent of caller flags."""
import ast
import copy
import hashlib
import json
import pathlib

from admission_budget_recovery_program import RecoveryProgram
from admission_budget_lifecycle_native import lifecycle_program
from admission_budget_bootstrap_prefix import source_program as bootstrap_source_program

PREFIX = "_offline/phase6e11/endchain_v1/"
PINS = {
    "runtime_lifecycle.py:prepare_prefix": "ca8a74be32f20dc1d24fac0534106e92d38f94a7acfd1a4b3862220cde7c6d20",
    "runtime_lifecycle.py:_gate": "926b9e6a8261f32f66b4fb2f4f7aa55359a2a7ed3534e38a2441fcd4e5390167",
    "runtime_lifecycle.py:_final": "78792662e9a7ec6d1fe85c76f33e0fde9b9c43e9f701ef0e48b1034ad859d707",
    "runtime_lifecycle.py:run": "bcb8d75d529ba51ba2d6dcc2d43cba315bd37088701ac1ec3e7d41e551f84796",
    "runtime_lifecycle.py:_monitor": "2e328bd4508f7b9890d284122e9c0766e600e5d64bde179b21ba49440fe3a988",
    "runtime_lifecycle.py:_readonly": "fecb258b05ece1e6fc744a1f4a7f7b4ff6c2cafd988b7a96260f94f1b224faf9",
    "runtime_case_entry.py:execute_bootstrap": "aeab373782a954cf3edc93844f8824a008bcca79d8b4e060b0dd662477d7d54d",
    "runtime_case_entry.py:bootstrap_fault_prefix": "ff46a45f34a91b59cd6248b358f827057124f811aa6c241360a9ba7fad1699c1",
    "runtime_case_entry.py:bootstrap_closeout_numeric": "07e51bdb68d4984ad66c44a4652c5d162abe53b3c8ccabefc2ab48c3201ce3ee",
    "runtime_prefix.py:run_pending": "3be7c43a4b423fbd5240f49dcf7c5e06f9556a1f8d3bcc83b9a09972dd9dc510",
    "runtime_history.py:preflight": "41c9f04b7457e5f1a089742fa6bd3ed5c056e6689b06e65ed4f8a660802776bf",
}
GATES = {"gates_before_": (20, "_gate"), "gates_after_migration_": (20, "_gate"),
         "gates_final_pre_": (11, "_final"), "gates_final_post_": (9, "_final")}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def sources(runtime):
    hashes, functions = {}, {}
    for name in sorted({key.split(":")[0] for key in PINS}):
        raw = (pathlib.Path(runtime) / name).read_bytes()
        hashes[PREFIX + "quota_candidate_v1/" + name] = sha(raw)
        for node in ast.walk(ast.parse(raw)):
            if not isinstance(node, ast.FunctionDef):
                continue
            key = name + ":" + node.name
            if key in PINS:
                if key in functions:
                    raise ValueError("release_join_ambiguous_function:" + key)
                functions[key] = sha(ast.dump(node, include_attributes=False).encode())
    for key, expected in PINS.items():
        if functions.get(key) != expected:
            raise ValueError("release_join_source_changed:" + key)
    return hashes, functions


def bind_lifecycle(normal, *, runtime_dir, source_root=None):
    """Retain charges/states and derive actual ordered template identities."""
    if source_root is None:
        from admission_budget import HERE
        source_root = HERE.parents[2]
    hashes, functions = sources(runtime_dir)
    native = lifecycle_program(source_root, runtime_dir)
    hashes.update(native["source_hashes"])
    result = copy.deepcopy(normal)
    counts = dict.fromkeys(GATES, 0)
    for event in result["events"]:
        if event.get("stage") != "dispatch":
            continue
        action = event.get("selector", {}).get("action", "")
        matches = [prefix for prefix in GATES if action.startswith(prefix)]
        if not matches:
            continue
        if len(matches) != 1:
            raise ValueError("release_join_gate_ambiguous")
        prefix = matches[0]
        label = prefix.removeprefix("gates_").removesuffix("_")
        command = native["profiles"][label][counts[prefix]]
        if event["capacity_use"] != command["protocol_commands"]:
            raise ValueError("release_join_lifecycle_protocol_cost")
        counts[prefix] += event["capacity_use"]
        method = "CasePreservation." + GATES[prefix][1]
        source = PREFIX + "quota_candidate_v1/runtime_lifecycle.py"
        event.update(source=source, source_sha256=hashes[source], method=method,
                     lifecycle_method_ast_sha256=functions["runtime_lifecycle.py:" + GATES[prefix][1]],
                     native_template_revalidated=True,
                     actual_native_binding=copy.deepcopy(command),
                     source_selector=dict(phase=command["phase"], method=method,
                                          source_order=command["index"]))
        event.pop("native_template_pending", None)
    if counts != {prefix: bound for prefix, (bound, _) in GATES.items()}:
        raise ValueError("release_join_lifecycle_count_changed:" + repr(counts))
    preflight = [e for e in result["events"] if e.get("stage") == "dispatch"
                 and e.get("selector", {}).get("action") == "project_tls_and_quota_history"]
    if len(preflight) != 4:
        raise ValueError("release_join_preflight_count")
    for event, command in zip(preflight, native["ancillary_profiles"]["preflight"]):
        source = PREFIX + "quota_candidate_v1/runtime_history.py"
        event.update(source=source, source_sha256=hashes[source], method="preflight",
            actual_native_binding=copy.deepcopy(command), native_template_revalidated=True,
            source_selector=dict(method="preflight", source_order=command["index"],
                meter_action="preflight_" + command["statement_sha256"]))
    observer_groups = {}
    for event in result["events"]:
        action = event.get("selector", {}).get("action", "")
        if event.get("stage") == "dispatch" and action.startswith("cli_") and "_observer_" in action:
            observer_groups.setdefault(action, []).append(event)
    if len(observer_groups) != 6 or any(len(v) != 4 for v in observer_groups.values()):
        raise ValueError("release_join_cli_observer_groups")
    for action, events in observer_groups.items():
        for event, command in zip(events, native["ancillary_profiles"]["cli_observer"]):
            if event["capacity_use"] != 1 or event["reference_sql_sha256"] != command["statement_sha256"]:
                raise ValueError("release_join_cli_observer_identity")
            event.update(actual_native_binding=copy.deepcopy(command), native_template_revalidated=True,
                source_selector=dict(method="snapshot", caller=action, source_order=command["index"]))
    result["source_hashes"].update(hashes)
    result["actual_lifecycle_join"] = dict(counts=counts, source_function_hashes=functions,
        canonical45_replayed=False, statement_identity_proven=True,
        native_source_hashes=native["source_hashes"], read_wal_proven=False,
        preflight_commands=4, cli_observer_commands=24,
        prefix_order=["history47_preflight", "stream_before", "gate_before", "append48",
                      "gate_after_migration", "preauth_cli"])
    return result


def derive_release_joins(root, runtime_dir, plan, normal):
    """Regenerate proofs from authoritative normal rows and actual dispatchers.

    No caller-supplied complete flag, case receipt or old fixed missing list can
    satisfy this boundary. Local startup remains a mandatory separate root gate.
    """
    hashes, functions = sources(runtime_dir)
    expected = bind_lifecycle(normal, runtime_dir=runtime_dir, source_root=root)
    lifecycle_match = normal.get("actual_lifecycle_join") == expected["actual_lifecycle_join"]
    for actual, regenerated in zip(normal["events"], expected["events"]):
        if actual != regenerated:
            lifecycle_match = False
    native_joined = {event["selector"]["register_row"]: event["actual_native_binding"]
        for event in expected["events"] if event.get("actual_native_binding")}
    native_missing = [row["id"] for row in plan["normal"]["rows"]
        if row.get("kind") in ("native", "observer")
        and row.get("classification") == "historical_read_only_reference" and row["id"] not in native_joined]
    native_missing += [event["event_id"] for event in normal["events"]
        if event.get("native_template_pending") and event.get("stage") == "dispatch"]
    recovery_missing = []
    nodes = {event["event_id"]: event for event in normal["events"]}
    for event in normal["events"]:
        for outcome in event.get("outcomes", []):
            if outcome == "confirmed":
                continue
            target = event.get("next", {}).get(outcome)
            if target not in nodes:
                recovery_missing.append(dict(event_id=event["event_id"], outcome=outcome))
    recovery = RecoveryProgram(root, runtime_dir).enumerate()
    hashes[PREFIX + "quota_candidate_v1/runtime_recovery.py"] = recovery["source_hashes"]["runtime_recovery.py"]
    hashes[PREFIX + "control_recovery.py"] = recovery["source_hashes"]["control_recovery.py"]
    for name in ("runtime_history.py", "runtime_catalog.py", "runtime_stream.py", "runtime_adapter.py"):
        hashes[PREFIX + "quota_candidate_v1/" + name] = sha((pathlib.Path(runtime_dir) / name).read_bytes())
    hashes.update(expected["actual_lifecycle_join"]["native_source_hashes"])
    bootstrap = bootstrap_source_program(root)
    hashes.update(bootstrap["source_hashes"])
    for name in ("admission_budget_release_joins.py", "admission_budget_recovery_program.py", "admission_budget_lifecycle_native.py", "admission_budget_bootstrap_prefix.py"):
        hashes[PREFIX + name] = sha(pathlib.Path(__file__).with_name(name).read_bytes())
    proofs = dict(
        lifecycle=dict(complete=lifecycle_match, scope="actual dispatcher/order and explicit gate capacities",
            evidence=expected["actual_lifecycle_join"], statement_identity_proven=lifecycle_match,
            read_wal_proven=False, runtime_arguments_observed=False),
        native=dict(complete=not native_missing, unmatched_row_ids=sorted(set(native_missing)),
            joined_rows=native_joined, joined_count=len(native_joined),
            missing_count=len(set(native_missing)), source_matches_are_not_runtime_evidence=True),
        exception=dict(complete=not recovery_missing and not recovery["unresolved"],
            workflow_finally=recovery, unjoined_prefix_outcomes=recovery_missing,
            missing_count=len(recovery_missing)),
        bootstrap=dict(complete=functions["runtime_case_entry.py:execute_bootstrap"]
                == PINS["runtime_case_entry.py:execute_bootstrap"],
            scope="source-bound entry dispatch only; local setup costs belong to mandatory root ledger",
            precharged_instruction="case.bootstrap.clean47", root_full_bound_required=True,
            local_sql_upper_bound=None, counted_as_hosted_setup=False,
            fault_prefix_source_program=bootstrap,
            fault_numeric_requires_original_complete_prefix=True,
            failure_closeout_separately_precharged=True,
            implicit_driver_zero_assumed=False))
    missing = []
    for name, proof in proofs.items():
        if not proof["complete"]:
            missing.append("actual_join:" + name + ":" + str(proof.get("missing_count", "source_mismatch")))
    value = dict(format="actual-release-join-proofs-v1", source_hashes=hashes, proofs=proofs,
        complete=not missing, missing_costs=missing, actual_execution_evidence=False,
        root_disposable_gate_required=True, hosted_limit=2349, historical_normal=2338, historical_closing=731)
    value["proofs_sha256"] = canonical(value)
    return value
