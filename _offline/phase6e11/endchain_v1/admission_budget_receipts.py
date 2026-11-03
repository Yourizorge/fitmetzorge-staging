"""Parent-callable lossless budget receipts. No SQL, HTTP, CLI or CI dispatch."""
import base64
import collections
import copy
import difflib
import hashlib
import json
import pathlib
import re

from admission_budget import PHASE_BUDGETS, require
from admission_budget_register import assemble, canonical_sha

MAX_MEMBER = 2000000
CHUNK_RAW = 1000000
MAX_FILES = 50
INDEX = "admission-budget-index.json"
CI_FILES = ("admission_budget.py", "admission_budget_register.py", "admission_budget_graph.py",
            "admission_budget_receipts.py", "admission_budget_test.py",
            "admission_budget_register_test.py", "admission_budget_receipts_test.py")
REFERENCE_FILES = tuple("receipts/reserved-ci-39109482869/" + name for name in
    ("complete-command-register.json",) + tuple("register-phase-" + phase + ".json" for phase in PHASE_BUDGETS))


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def _read(path):
    require(not path.is_symlink(), "budget_receipt_symlink")
    require(path.stat().st_size < MAX_MEMBER, "budget_input_member_size")
    data = path.read_bytes()
    require(len(data) < MAX_MEMBER, "budget_input_member_size")
    return json.loads(data), sha(data)


def actual_receipts(folder):
    """Only named sanitized component results, never an old bulk receipt glob."""
    folder = pathlib.Path(folder)
    selected = {}
    names = {
        "auth": ("admission-auth-auth-failure-component.json", "auth-failure-component.json"),
        "parent_bootstrap": ("admission-auth-admission-fixture-bootstrap.json", "admission-fixture-bootstrap.json"),
        "fixture": ("fixture-cleanup-component-detail.json",),
        "workflow": ("integral-component-matrix.json",),
        "cli_predispatch": ("cli-predispatch.json",),
        "cli_pending_0": ("cli-predispatch-pending-0.json",),
        "cli_pending_2": ("cli-predispatch-pending-2.json",),
        "cli_canonical_45": ("cli-predispatch-canonical-45.json",),
        "migration_boundary_pre": ("migration-boundary-pre.json",),
        "migration_boundary_post": ("migration-boundary-post.json",),
        "migration_boundary_claim": ("migration-boundary-claim.json",),
        "producer_scope_before": ("fixture-producer-scope-before-result.json",),
        "producer_scope_after": ("fixture-producer-scope-after-result.json",),
        "physical_suffix": ("fixture-parent-physical-zero.json",),
        "parent_auth_finalizer": ("auth-parent-finalizer.json",),
    }
    for component, candidates in names.items():
        available = [folder / name for name in candidates if (folder / name).is_file()]
        require(len(available) <= 1, "budget_ambiguous_component_receipt:" + component)
        if available:
            value, digest = _read(available[0])
            selected[component] = (value, dict(path=available[0].name, sha256=digest))
    journal_path = folder / "admission-fixture-journal-index.json"
    if journal_path.is_file():
        from admission_journal import verify
        index, index_sha = _read(journal_path)
        wanted = "fixture-cleanup-component-detail.json"
        matches = []

        def chunk(name):
            require(bool(re.fullmatch(r"admission-fixture-journal-\d{3}\.json", name)), "budget_journal_chunk_name")
            value, _ = _read(folder / name)
            if wanted in value.get("entries", {}):
                entry = value["entries"][wanted]
                data = base64.b64decode(entry["base64"], validate=True)
                matches.append((json.loads(data), dict(path=wanted, sha256=sha(data),
                    journal_index=journal_path.name, journal_index_sha256=index_sha)))
            return value

        verify(index, chunk)
        require(len(matches) == 1, "budget_fixture_detail_missing")
        require("fixture" not in selected, "budget_ambiguous_fixture_receipt")
        selected["fixture"] = matches[0]
    result = {}
    for component in names:
        if component not in selected:
            result[component] = dict(status="PENDING_NAMED_RECEIPT", actual_counts=None)
            continue
        value, binding = selected[component]
        if component.startswith("cli_"):
            result[component] = cli_receipt(value, binding)
            if component == "cli_canonical_45":
                result[component].update(canonical_references(folder, value, binding, selected))
                if not result[component]["canonical_references_complete"]:
                    result[component]["status"] = "NO_GO_CANONICAL_RECEIPT_INCOMPLETE"
            if component in ("cli_pending_0", "cli_pending_2"):
                index = int(component.rsplit("_", 1)[1])
                result[component]["expected_app_profile_index"] = index
                result[component]["app_profile_index_matches"] = value.get("app_index") == index
                protocol_path = folder / ("cli-protocol-" + str(index) + ".json")
                protocol = dict(status="PENDING_NAMED_RECEIPT", additional_charge=0,
                                accounting="SAME_DISPATCH_COMPATIBILITY_VIEW_NOT_ADDITIONAL_EXECUTION")
                if protocol_path.is_file():
                    compatible, compatible_sha = _read(protocol_path)
                    protocol.update(status="PARENT_COMPATIBILITY_RECEIPT", path=protocol_path.name,
                        sha256=compatible_sha, complete=compatible.get("complete"),
                        protocol_commands=compatible.get("protocol_commands"), total_commands=compatible.get("total_commands"),
                        instrumented_receipt_matches=compatible.get("instrumented_receipt") == binding["path"],
                        source_commit_matches=compatible.get("source_commit") == value.get("source_commit")
                            if value.get("source_commit") is not None else None,
                        candidate_sha256_matches=compatible.get("candidate_sha256") == value.get("candidate_sha256")
                            if value.get("candidate_sha256") is not None else None)
                result[component]["compatibility_receipt"] = protocol
            continue
        if component.startswith("migration_boundary_"):
            result[component] = migration_boundary_receipt(value, binding)
            continue
        if component.startswith("producer_scope_") or component in ("physical_suffix", "parent_auth_finalizer"):
            result[component] = dict(status=value.get("status", "MISSING_STATUS"), receipt=binding,
                component_classification=value.get("classification", value.get("suffix_status")),
                preparation_run=value.get("preparation_run"),
                actual_counts={k:value.get(k) for k in ("protocol_limit", "admitted_attempts", "emitted_attempts",
                    "expected_protocol_commands", "prepaid_consumed", "native_dispatches", "http_attempts")},
                source_binding=value.get("source_binding"),
                registry_deletion_proven=value.get("registry_deletion_proven"),
                original_commit_reclassified=value.get("original_commit_reclassified"),
                receipt_is_not_complete_job_bound=True, changes_hosted_bound=False,
                full_hosted_bound_proven=False, evidence_class="PARENT_LOCAL_DIAGNOSTIC_RECEIPT")
            continue
        source_hashes = value.get("source_sha256", value.get("source_hashes", {}))
        counts = {}
        if component == "auth":
            counts = value.get("diagnostic_totals", {})
        elif component == "fixture":
            counts = {k: value.get(k) for k in ("local_diagnostic_sql_count", "local_setup_sql_count",
                       "local_component_sql_count", "counts_are_protocol_only_not_nested_sql_or_io")}
        elif component == "parent_bootstrap":
            counts = dict(native_dispatched=len(value.get("dispatches", [])), limit=value.get("limit"),
                          confirmed=sum(r.get("confirmed") is True for r in value.get("dispatches", [])))
        else:
            counts = {k: value.get(k) for k in ("local_diagnostic_prepaid_units", "local_native_dispatches",
                                               "local_managed_sql_observed")}
        result[component] = dict(status=value.get("status", "MISSING_STATUS"), receipt=binding,
            preparation_run=value.get("preparation_run_id", value.get("preparation_run")),
            source_hashes=source_hashes, source_binding_sha256=value.get("source_binding_sha256"),
            actual_counts=counts, evidence_class="PARENT_LOCAL_RECEIPT_NOT_INDEPENDENT_EXECUTION_PROOF",
            changes_hosted_bound=False)
    return result


NORMAL_SOURCE_GROUPS = {
    "native": ("integral_ci.py", "metered_composition.py", "registered_runner.py", "registered_lifecycle.py",
        "fixture_lifecycle.py", "session_transport.mjs", "request_transport.mjs", "integral_workflow.mjs",
        "integral_io.py", "integral_stream.py", "lifecycle_gates.py", "sql_protocol.py", "native_runtime.py",
        "runtime_budget.py", "complete_register.py", "workflow_composition.mjs", "composed_handler.mjs"),
    "preflight": ("lifecycle_gates.py", "sql_protocol.py", "native_runtime.py", "metered_composition.py"),
    "workflow": ("metered_composition.py", "integral_ci.py", "integral_workflow.mjs", "auth_protocol.py",
                 "execution_context.mjs", "workflow_composition.mjs", "composed_handler.mjs"),
    "auth": ("metered_composition.py", "auth_evidence.py", "auth_protocol.py", "registered_lifecycle.py",
             "integral_auth.mjs", "execution_context.mjs"),
    "cli": ("cli_meter.py", "cli_envelope.py", "cli_stat_reader.py"),
    "removal": ("_offline/phase6e11/auth_metadata_v1/audit.py",
                "_offline/phase6e11/controller_guard_v1/guard.py"),
}
NORMAL_RECEIPTS = ("integral-complete-protocol-trace.json", "integral-preflight.json",
    "runtime-command-meter.json", "workflow-auth-protocol.json", "endchain-sources.json",
    "cli-predispatch-canonical-45.json", "migration-boundary-post.json") + tuple(
    "auth-protocol-%02d.json" % i for i in range(18)) + tuple(
    name % i for i in range(3) for name in ("cli-protocol-%d.json", "cli-numeric-coverage-%d.json"))


def source_reconciliation(report, recorded):
    """Compare exact known paths; never accept a basename alias from another root."""
    result = {}
    for group, names in NORMAL_SOURCE_GROUPS.items():
        rows = []
        for name in names:
            expected = report["source_hashes"][name]
            recorded_hash = recorded.get(name if name.startswith("_offline/") else
                                         "_offline/phase6e11/endchain_v1/" + name)
            rows.append(dict(path=name, expected_sha256=expected, recorded_sha256=recorded_hash,
                status="MISSING" if recorded_hash is None else "MATCH" if recorded_hash == expected else "CHANGED"))
        result[group] = dict(rows=rows, all_match=all(r["status"] == "MATCH" for r in rows),
                             scope="NAMED_EXECUTOR_SUBSET_NOT_TRANSITIVE_SOURCE_OR_EXECUTION_PROOF")
    return result


def _ordered_trace(expected, actual, *, preflight=False):
    require(isinstance(actual, list) and len(actual) <= 4096, "budget_reconcile_trace_shape")
    require(all(isinstance(row, dict) for row in actual), "budget_reconcile_trace_row")
    def key(row, reference=False):
        if reference and row.get("binding_required"):
            return "UNBOUND_CURRENT_TEMPLATE:" + row["id"]
        if preflight:
            return row.get("sql_sha256")
        return canonical_sha(dict(phase=row.get("action") if reference else row.get("phase"),
            action=row.get("action_binding", {}) if reference else row.get("action") or {},
            sql_sha256=row.get("sql_sha256")))
    expected_keys = [key(r, True) for r in expected]
    actual_keys = [key(r) for r in actual]
    joins = [dict(row_id=r["id"], status="BINDING_REQUIRED" if r.get("binding_required") else
                  "MISSING_OR_CHANGED", actual_command=None) for r in expected]
    used = set()
    # Ordered matching exposes inserted/deleted/reordered commands without cascading all later mismatches.
    for a, b, size in difflib.SequenceMatcher(None, expected_keys, actual_keys, autojunk=False).get_matching_blocks():
        for offset in range(size):
            i, j = a + offset, b + offset
            joins[i].update(status="MATCH" if actual[j].get("confirmed") is True else "UNCONFIRMED",
                            actual_command=actual[j].get("command", j + 1))
            used.add(j)
    for i, join in enumerate(joins):
        if join["status"] != "MISSING_OR_CHANGED":
            continue
        candidates = [j for j, value in enumerate(actual_keys) if j not in used and value == expected_keys[i]]
        if candidates:
            j = candidates[0]
            join.update(status="ORDER_CHANGED", actual_command=actual[j].get("command", j + 1))
            used.add(j)
    extras = [dict(index=i, phase=r.get("phase"), sql_sha256=r.get("sql_sha256"))
              for i, r in enumerate(actual) if i not in used]
    return dict(expected_count=len(expected), actual_count=len(actual), rows=joins,
        matched_count=sum(r["status"] == "MATCH" for r in joins), unexpected=extras,
        moved_count=sum(r["status"] == "ORDER_CHANGED" for r in joins),
        ordered_complete=not extras and all(r["status"] == "MATCH" for r in joins))


def _numeric(receipt, expected):
    if not isinstance(receipt, dict) or type(expected) is not int or expected < 1:
        return False
    rows = receipt.get("statements")
    if not isinstance(rows, list) or not 0 < len(rows) <= 1024:
        return False
    if not all(isinstance(r, dict) and isinstance(r.get("queryid"), str)
               and type(r.get("calls")) is int and r["calls"] >= 0
               and type(r.get("temp_written")) is int and r["temp_written"] == 0
               and type(r.get("temp_read")) is int and r["temp_read"] == 0 for r in rows):
        return False
    return (len({r["queryid"] for r in rows}) == len(rows)
        and type(receipt.get("commands")) is int and receipt["commands"] == expected
        and sum(r["calls"] for r in rows) == expected
        and type(receipt.get("temp_written")) is int and receipt["temp_written"] == 0)


def reconcile_normal(report, records, *, historical=False, workflow_dispatches=None, canonical=None):
    """Reconcile existing receipt shapes. Optional dispatches are caller-supplied evidence.

    workflow_dispatches, when available: 72 ordered dictionaries with action,
    ticket_number, method='GET', path='/user', confirmed=True, unknown_consumed=0.
    No current executor emits that per-call ledger; aggregate 360 never fills it.
    This API reads data only; even complete joins grant no admission/full bound.
    """
    require(type(historical) is bool, "budget_reconcile_history_flag")
    sources = source_reconciliation(report, records.get("endchain-sources.json", {}).get("sources", {}))
    normal = report["normal_register"]["rows"]
    by_id = {r["id"]: r for r in normal}
    streams = collections.defaultdict(list)
    for row in report["normal_dispatch_mapping"]["rows"]:
        streams[row["stream"]].append(by_id[row["row_id"]])
    from complete_register import BOOTSTRAP
    trace = records.get("integral-complete-protocol-trace.json", {}).get("commands", [])
    require(isinstance(trace, list) and len(trace) <= 4096, "budget_reconcile_trace_shape")
    sequence = all(type(c.get("command")) is int and c["command"] == i + 1 for i, c in enumerate(trace))
    native = _ordered_trace(streams["integral_complete_protocol_trace"],
                            [r for r in trace if r.get("phase") not in BOOTSTRAP])
    native.update(trace_sequence_valid=sequence, ci_bootstrap_excluded=sum(r.get("phase") in BOOTSTRAP for r in trace))
    native["ordered_complete"] = native["ordered_complete"] and sequence
    preflight = _ordered_trace(streams["integral_preflight"],
        records.get("integral-preflight.json", {}).get("commands", []), preflight=True)
    for result, name in ((native, "integral-complete-protocol-trace.json"),
                         (preflight, "integral-preflight.json")):
        result["receipt_present"] = name in records
        if not result["receipt_present"]:
            result["actual_count"] = None

    events = records.get("runtime-command-meter.json", {}).get("events", [])
    require(isinstance(events, list) and len(events) <= 4096, "budget_reconcile_meter_shape")
    ticket_sequence = all(type(e.get("number")) is int and e["number"] == i + 1 for i, e in enumerate(events))
    def tickets(row):
        matches = [e for e in events if e.get("action") == row["action"]]
        ok = (ticket_sequence and len(matches) == 1 and matches[0].get("kind") == "managed_auth"
            and type(matches[0].get("commands")) is int and matches[0]["commands"] == row["cost"]
            and matches[0].get("phase") == row["phase"])
        return dict(action=row["action"], row_id=row["id"], expected_capacity=row["cost"],
            ticket_number=matches[0].get("number") if len(matches) == 1 else None,
            ticket_matches=ok, confirmed=ok and matches[0].get("confirmed") is True,
            consumed_capacity=matches[0]["commands"] if ok else None,
            unknown_dispatch_refunded=False)
    user_rows = [tickets(row) for row in streams["workflow_auth_protocol"]]
    anchors = [e["number"] for e in events if e.get("action") == "lifecycle_reader_begin"]
    upfront = bool(anchors) and all(r["ticket_matches"] and r["ticket_number"] < min(anchors) for r in user_rows)
    aggregate = records.get("workflow-auth-protocol.json", {})
    aggregate_ok = _numeric(aggregate, 360) and type(aggregate.get("verified_calls")) is int and aggregate["verified_calls"] == 72
    require(workflow_dispatches is None or isinstance(workflow_dispatches, list) and len(workflow_dispatches) <= 72,
            "budget_reconcile_user_dispatch_shape")
    calls = workflow_dispatches if workflow_dispatches is not None else []
    for i, row in enumerate(user_rows):
        call = calls[i] if i < len(calls) else {}
        row["dispatch_joined"] = (row["ticket_matches"] and call.get("action") == row["action"]
            and type(call.get("ticket_number")) is int and call["ticket_number"] == row["ticket_number"]
            and call.get("method") == "GET" and call.get("path") == "/user" and call.get("confirmed") is True
            and type(call.get("unknown_consumed")) is int and call["unknown_consumed"] == 0)
        row["per_call_managed_sql_observed"] = None
    workflow = dict(rows=user_rows, expected_calls=72, expected_prepaid=360, upfront_order_matches=upfront,
        matched_tickets=sum(r["ticket_matches"] for r in user_rows), aggregate_numeric_matches=aggregate_ok,
        dispatches_joined=sum(r["dispatch_joined"] for r in user_rows),
        aggregate_is_not_dispatch_ledger=True, per_call_managed_bound_proven=False)

    auth = []
    for i, row in enumerate(streams["auth_protocol_operation"]):
        name = "auth-protocol-%02d.json" % i
        value = records.get(name, {})
        identity = "gotrue_" + str(value.get("role")) + "_" + str(value.get("operation"))
        auth.append(dict(tickets(row), receipt=name, identity_matches=identity == row["action"],
                         numeric_matches=identity == row["action"] and _numeric(value, row["cost"])))
    cli = []
    from cli_envelope import charged
    for i, (slot, capacity) in enumerate((("quota", 64), ("pre_auth", 28), ("final", 28))):
        name = "cli-protocol-%d.json" % i
        value = records.get(name, {})
        entry = dict(slot=slot, receipt=name, reference_capacity=capacity + 8, actual_protocol_commands=None,
                     slot_matches=value.get("slot") == slot, reservation_matches=False, numeric_matches=False,
                     post_migration_confirmed=False)
        if slot == "quota" and canonical is not None and canonical.get("receipt"):
            entry.update(receipt=canonical["receipt"]["path"], slot_matches=canonical.get("slot") == "quota",
                actual_protocol_commands=canonical.get("actual_counts", {}).get("sql_dispatches"),
                reservation_matches=canonical.get("reserved_cap") == capacity,
                numeric_matches=canonical.get("numeric_confirmation", {}).get("counters_consistent") is True,
                raw_references_verified=all(canonical.get("raw_references", {}).get(k, {}).get("verified") is True
                                            for k in ("ledger", "policy", "isolation")),
                post_migration_confirmed=canonical.get("canonical_references_complete") is True)
        elif value:
            try:
                entry["reservation_matches"] = charged(value) == capacity + 8 and entry["slot_matches"]
            except (ValueError, TypeError, KeyError):
                pass
            n = value.get("protocol_commands")
            numeric = records.get("cli-numeric-coverage-%d.json" % i, {})
            entry["actual_protocol_commands"] = n
            entry["numeric_matches"] = (type(n) is int and 0 < n <= capacity
                and type(numeric.get("numeric_calls_minus_reader")) is int and numeric["numeric_calls_minus_reader"] == n
                and numeric.get("all_protocol_visible") is True
                and type(numeric.get("temp_written")) is int and numeric["temp_written"] == 0)
        cli.append(entry)
    return dict(status="NO_GO_RECONCILIATION_ONLY", historical_read_only_reference=historical,
        source_bindings=sources, native=native, preflight=preflight, workflow=workflow, auth=auth, cli=cli,
        optional_stream_capacity=sum(r["cost"] for r in streams["optional_stream_capacity_not_dispatch"]),
        optional_slots_not_promoted_to_observed_dispatches=True,
        current_source_subset_matches=not historical and all(s["all_match"] for s in sources.values()),
        full_bound_proven=False, minimal_cap=None, hosted_admitted=False)


def reconcile_folder(report, folder, *, historical=False, workflow_dispatches=None):
    """Named offline ingestion only. Returns data; never creates or overwrites exports."""
    folder = pathlib.Path(folder)
    records, bindings = {}, {}
    manifest = _read(folder / "artifact-manifest.json")[0] if (folder / "artifact-manifest.json").is_file() else None
    for name in NORMAL_RECEIPTS:
        if (folder / name).is_file():
            value, digest = _read(folder / name)
            if manifest is not None:
                require(manifest.get(name) == digest, "budget_reconcile_artifact_hash:" + name)
            records[name] = value
            bindings[name] = dict(sha256=digest, artifact_manifest_match=True if manifest is not None else None)
    canonical = None
    name = "cli-predispatch-canonical-45.json"
    if name in records:
        binding = dict(path=name, sha256=bindings[name]["sha256"])
        post = "migration-boundary-post.json"
        selected = {"migration_boundary_post": (records[post], dict(path=post, sha256=bindings[post]["sha256"]))} if post in records else {}
        canonical = cli_receipt(records[name], binding)
        canonical.update(canonical_references(folder, records[name], binding, selected))
    result = reconcile_normal(report, records, historical=historical,
                              workflow_dispatches=workflow_dispatches, canonical=canonical)
    result["receipt_bindings"] = bindings
    result["missing_receipts"] = [name for name in NORMAL_RECEIPTS if name not in records]
    return result


def reconcile_current_folder(report, folder, *, plan=None, historical=False, workflow_dispatches=None):
    """Compare new CI to v2 without mutating the retained normal register or receipts."""
    from admission_budget_register import PLAN_VERSION
    plan = report["current_plan"] if plan is None else plan
    require(plan["version"] == PLAN_VERSION and plan["plan_sha256"] ==
            canonical_sha({k:v for k,v in plan.items() if k != "plan_sha256"}), "budget_current_plan_binding")
    require(plan["historical_register_sha256"] == canonical_sha(report["normal_register"]),
            "budget_current_plan_reference")
    require(plan["current_source_hashes"] == report["source_hashes"], "budget_current_plan_sources")
    view = dict(report, normal_register=copy.deepcopy(plan["normal"]))
    result = reconcile_folder(view, folder, historical=historical, workflow_dispatches=workflow_dispatches)
    result.update(plan_version=plan["version"], plan_sha256=plan["plan_sha256"],
        source_derived_rows=len(plan["source_derived_row_ids"]),
        unbound_normal_rows=[r["id"] for r in plan["normal"]["rows"] if r.get("binding_required")],
        recovery_prefixes=len(plan["prefix_bindings"]), recovery_setup_reservation=1,
        runtime_recovery_wiring_proven=False, remaining_retained_rows_require_revalidation=True)
    return result


def cli_receipt(value, binding):
    """Preserve diagnostic counts, not a hosted or pending-migration bound."""
    failure = value.get("failure_ledger", {})
    ledger = value if "terminal" in value else failure
    terminal = ledger.get("terminal", {})
    header = ledger.get("header", {})
    build = value.get("build", {})
    hooks = build.get("hook_sources", {})
    allowed = {"hook.cjs", "entry.mjs", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml"}
    require(isinstance(hooks, dict) and set(hooks) <= allowed, "budget_cli_hook_source_names")
    require(all(isinstance(h, str) and re.fullmatch("[a-f0-9]{64}", h) for h in hooks.values()),
            "budget_cli_hook_source_hash")
    complete = value.get("complete") is True
    local = value.get("scope") == "DISPOSABLE_CI_ONLY" and value.get("hosted_admission") is False
    counts = {key: terminal.get(key) for key in (
        "sql_dispatches", "confirmed_sql", "unknown_consumed", "connection_attempts",
        "frontend_frames_by_type", "frontend_write_returned_by_type")}
    counts.update({key: value.get(key) for key in (
        "observer_commands", "ci_bootstrap_sql_commands", "reserved_sql_consumed_on_failure")})
    return dict(status="PARENT_CLI_LOCAL_COMPONENT_COMPLETE" if complete and local else "NO_GO_CLI_COMPONENT",
        receipt=binding, actual_counts=counts, source_commit=value.get("source_commit"),
        candidate_sha256=value.get("candidate_sha256"),
        source_hashes={"cli_predispatch/" + name: digest for name, digest in hooks.items()},
        source_binding_coverage="RECEIPT_BUILD_HOOK_SUBSET_ONLY_NOT_ALL_DEPENDENCIES",
        build_sha256=canonical_sha(build), upstream_commit=build.get("upstream_commit"),
        upstream_source_pins=build.get("source_before_lf", {}),
        ledger_scope="failure_prefix" if ledger is failure else "main",
        terminal_recorded=ledger.get("terminal_recorded"), terminal_complete=terminal.get("complete"),
        journal_sha256=ledger.get("journal_sha256"), event_count=ledger.get("event_count"),
        slot=header.get("slot"), reserved_cap=header.get("cap"),
        app_index=value.get("app_index"), phase=value.get("phase"),
        actual_empty_dry_run=value.get("actual_empty_dry_run"),
        actual_migration_execution=value.get("actual_migration_execution"),
        migration_evidence_status="PARENT_REPORTS_EXECUTED_NOT_FULL_BOUND" if value.get("actual_migration_execution") is True
                                  else "PENDING_ACTUAL_MIGRATION_EVIDENCE",
        numeric_coverage=value.get("numeric_coverage"), ci_cron_restored=value.get("ci_cron_restored"),
        failure_ledger_unverifiable=value.get("failure_ledger_unverifiable"),
        evidence_class="PARENT_LOCAL_RECEIPT_NOT_INDEPENDENT_EXECUTION_PROOF",
        full_hosted_bound_proven=False, changes_hosted_bound=False)


def raw_reference(folder, ref, name, limit):
    """Verify fixed-name original bytes, including incomplete ledgers; never replay."""
    result = dict(path=name, additional_sql=0, verified=False)
    if ref is None:
        return dict(result, status="MISSING_REFERENCE")
    if (not isinstance(ref, dict) or set(ref) != {"path", "sha256"} or ref["path"] != name
            or not isinstance(ref["sha256"], str) or not re.fullmatch("[a-f0-9]{64}", ref["sha256"])):
        return dict(result, status="INVALID_REFERENCE")
    result["expected_sha256"] = ref["sha256"]
    path = pathlib.Path(folder) / name
    try:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            return dict(result, status="UNSAFE_REFERENCE")
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            return dict(result, status="OVERSIZED_REFERENCE")
    except OSError:
        return dict(result, status="UNAVAILABLE_REFERENCE")
    result.update(sha256=sha(data), raw_bytes=len(data))
    matches = result["sha256"] == ref["sha256"]
    return dict(result, status="RAW_BYTES_VERIFIED" if matches else "HASH_MISMATCH", verified=matches)


def canonical_references(folder, value, binding, selected):
    refs = {
        "ledger": raw_reference(folder, value.get("ledger_ref"), "cli-predispatch-canonical-45.ledger.txt", 262144),
        "policy": raw_reference(folder, value.get("policy_ref"), "cli-predispatch-canonical-45.policy.json", 16384),
        "isolation": raw_reference(folder, dict(path=value.get("isolation_receipt"),
            sha256=value.get("isolation_receipt_sha256")),
            "canonical-45-cli-predispatch-cli-isolation-0.json", 16384),
    }
    terminal, numeric = value.get("terminal", {}), value.get("numeric_coverage", {})
    count = terminal.get("sql_dispatches")
    numeric_consistent = (type(count) is int and 0 < count <= 64
        and type(terminal.get("confirmed_sql")) is int and terminal["confirmed_sql"] == count
        and type(terminal.get("unknown_consumed")) is int and terminal["unknown_consumed"] == 0
        and type(numeric.get("numeric_calls_minus_reader")) is int and numeric["numeric_calls_minus_reader"] == count
        and type(numeric.get("protocol_commands")) is int and numeric["protocol_commands"] == count
        and numeric.get("all_protocol_visible") is True
        and type(numeric.get("temp_written")) is int and numeric["temp_written"] == 0)
    confirmation = dict(status="PENDING_BOUNDARY_CONFIRMATION", references_match=False, additional_charge=0)
    if "migration_boundary_post" in selected:
        post, post_ref = selected["migration_boundary_post"]
        actual = post.get("actual_migration_result", {})
        matches = (post.get("component_verified") is True
            and actual.get("receipt") == binding["path"] and actual.get("receipt_sha256") == binding["sha256"]
            and all(refs[key]["verified"] and actual.get(field) == refs[key].get("sha256")
                    for key, field in (("ledger", "ledger_sha256"), ("policy", "policy_file_sha256"),
                                       ("isolation", "isolation_receipt_sha256")))
            and actual.get("protocol_commands") == count and actual.get("observer_commands") == 8
            and actual.get("isolation_commands") == value.get("ci_bootstrap_sql_commands"))
        confirmation.update(status="PARENT_BOUNDARY_CONFIRMATION", receipt=post_ref,
                            references_match=matches, component_verified=post.get("component_verified"))
    complete = (value.get("complete") is True and value.get("profile") == "canonical_45"
        and value.get("phase") == "migration_45" and value.get("actual_migration_execution") is True
        and numeric_consistent and all(ref["verified"] for ref in refs.values())
        and confirmation["references_match"])
    return dict(profile=value.get("profile"), expected_migration=value.get("expected_migration"),
        expected_migration_sha256=value.get("expected_migration_sha256"), raw_references=refs,
        numeric_confirmation=dict(receipt=binding, field="numeric_coverage",
                                  counters_consistent=numeric_consistent, independent_execution_proof=False),
        boundary_confirmation=confirmation, canonical_references_complete=complete,
        confirmation_scope="BYTE_REFERENCES_AND_REPORTED_COUNTERS_NOT_INDEPENDENT_CLI_REPLAY",
        reference_charge_group="cli_quota", reference_capacity=72, additional_reference_charge=0,
        isolation_accounting="SEPARATE_LOCAL_DIAGNOSTIC_NOT_HOSTED_REFERENCE",
        runtime_recovery_bound_complete=False, full_hosted_bound_proven=False)


def migration_boundary_receipt(value, binding):
    source_binding = value.get("source_binding", {})
    prefix = "_offline/phase6e11/endchain_v1/"
    subset = {name: source_binding.get("sources", {}).get(prefix + name) for name in (
        "migration_failure_boundaries.py", "test_migration_failure_boundaries.py")}
    return dict(status="PARENT_LOCAL_BOUNDARY_RECEIPT", receipt=binding,
        component_verified=value.get("component_verified"), execution_status=value.get("execution_status"),
        terminal_complete=value.get("terminal_complete"),
        source_commit=source_binding.get("source_commit"), candidate_sha256=source_binding.get("candidate_sha256"),
        source_binding_sha256=value.get("source_binding_sha256"),
        source_hashes={name: h for name, h in subset.items() if h is not None},
        source_binding_coverage="BOUNDARY_MODULE_SUBSET_ONLY_NOT_ALL_DEPENDENCIES",
        actual_counts={k: value.get(k) for k in ("local_diagnostic_commands", "command_limit", "cleanup_reserve",
                                                "refunds", "migration_dispatches_by_helper")},
        declared_pair_allowances={k: value.get(k) for k in (
            "normal_diagnostic_sql_commands", "maximum_diagnostic_sql_commands")},
        accounting_scope=value.get("accounting_scope"), unknown_outcome=value.get("unknown_outcome"),
        reader_connections_closed=value.get("reader_connections_closed"),
        actual_migration_result={k: value.get("actual_migration_result", {}).get(k) for k in (
            "receipt", "receipt_sha256", "execution_mode", "invocation_id", "protocol_commands",
            "observer_commands", "isolation_commands", "ledger_sha256", "policy_file_sha256",
            "isolation_receipt_sha256")},
        evidence_class="PARENT_LOCAL_RECEIPT_NOT_INDEPENDENT_EXECUTION_PROOF",
        full_hosted_bound_proven=False, changes_hosted_bound=False)


def package(report):
    data = raw(report)
    full_sha = sha(data)
    require(full_sha == canonical_sha(report), "budget_canonical_hash_drift")
    count = (len(data) + CHUNK_RAW - 1) // CHUNK_RAW
    require(count + 1 <= MAX_FILES, "budget_package_capacity_not_truncated")
    members, refs = {}, []
    for index, offset in enumerate(range(0, len(data), CHUNK_RAW)):
        part = data[offset:offset + CHUNK_RAW]
        name = "admission-budget-chunk-%03d.json" % (index + 1)
        value = dict(format="admission-budget-lossless-chunk-v1", ordinal=index + 1,
            full_register_sha256=full_sha, raw_bytes=len(part), raw_sha256=sha(part),
            base64=base64.b64encode(part).decode("ascii"))
        require(len(raw(value)) < MAX_MEMBER, "budget_package_member_size")
        members[name] = value
        refs.append(dict(name=name, ordinal=index + 1, raw_bytes=len(part), raw_sha256=sha(part),
                         member_canonical_sha256=sha(raw(value))))
    result = dict(format="admission-budget-lossless-index-v1", status=report["status"],
        full_register_sha256=full_sha, raw_bytes=len(data), chunks=refs,
        complete=True, contents_omitted=False, file_count=count + 1,
        normal_capacity=report["normal_register"]["normal_capacity"], closing_reserve=731,
        approved_limit=report["approved_limit"], minimal_cap=None, hosted_admitted=False,
        parent_artifact_cap_changed=False, preparation_run_id=report["preparation_run_id"],
        source_hashes=report["source_hashes"], unresolved_inputs=report["unresolved_inputs"],
        actual_component_evidence=report.get("actual_component_evidence", {}))
    require(len(raw(result)) < MAX_MEMBER, "budget_index_member_size")
    members[INDEX] = result
    return members


def verify(index, load_member):
    require(index.get("format") == "admission-budget-lossless-index-v1"
            and index.get("complete") is True and index.get("contents_omitted") is False, "budget_index")
    chunks = index["chunks"]
    require(0 < len(chunks) < MAX_FILES and index["file_count"] == len(chunks) + 1, "budget_chunk_count")
    parts = []
    for ordinal, expected in enumerate(chunks, 1):
        require(expected["name"] == "admission-budget-chunk-%03d.json" % ordinal
                and expected["ordinal"] == ordinal, "budget_chunk_sequence")
        value = load_member(expected["name"])
        require(len(raw(value)) < MAX_MEMBER and sha(raw(value)) == expected["member_canonical_sha256"],
                "budget_chunk_changed")
        require(value.get("format") == "admission-budget-lossless-chunk-v1"
                and value["ordinal"] == ordinal and value["full_register_sha256"] == index["full_register_sha256"],
                "budget_chunk_binding")
        require(isinstance(value["base64"], str) and len(value["base64"]) <= 4 * ((CHUNK_RAW + 2) // 3),
                "budget_encoded_size")
        part = base64.b64decode(value["base64"], validate=True)
        require(len(part) <= CHUNK_RAW and len(part) == expected["raw_bytes"] == value["raw_bytes"]
                and sha(part) == expected["raw_sha256"] == value["raw_sha256"], "budget_chunk_payload")
        parts.append(part)
    data = b"".join(parts)
    require(len(data) == index["raw_bytes"] and sha(data) == index["full_register_sha256"], "budget_full_binding")
    report = json.loads(data)
    require(report["status"] == index["status"] and report["minimal_cap"] is None
            and report["hosted_admitted"] is False, "budget_admission_claim")
    return report


def run(gate):
    """Emit complete assembly after parent components; return NO_GO receipt index.

    Required Gate interface: out (path), save(name, JSON value). Main must package
    CI_FILES plus REFERENCE_FILES and their existing imported source dependencies.
    Reference files are retained read-only, not executed or copied in bulk.
    """
    report = assemble()
    report["actual_component_evidence"] = actual_receipts(gate.out)
    report["normal_reconciliation"] = reconcile_folder(report, gate.out)
    report["current_plan_reconciliation"] = reconcile_current_folder(report, gate.out)
    for evidence in report["actual_component_evidence"].values():
        hashes = evidence.get("source_hashes", {})
        evidence["source_hashes_match_current"] = (all(report["source_hashes"].get(k) == v
            for k, v in hashes.items()) if hashes else None)
        binding = evidence.get("preparation_run")
        evidence["preparation_binding_matches"] = binding == report["preparation_run_id"] if binding else None
    parent_result = getattr(gate, "result", {})
    for name, evidence in report["actual_component_evidence"].items():
        if name.startswith(("cli_", "migration_boundary_")):
            for field, parent_field in (("source_commit", "commit"), ("candidate_sha256", "candidate_sha256")):
                expected = parent_result.get(parent_field)
                evidence[field + "_matches_parent"] = evidence.get(field) == expected if expected is not None else None
    members = package(report)
    require(all(not (pathlib.Path(gate.out) / name).exists() for name in members), "budget_existing_receipts_preserved")
    for name, value in members.items():
        gate.save(name, value)
    return members[INDEX]
