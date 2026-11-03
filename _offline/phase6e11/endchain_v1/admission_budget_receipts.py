"""Parent-callable lossless budget receipts. No SQL, HTTP, CLI or CI dispatch."""
import base64
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
