"""Read-only accounting of the actual two early bootstrap fault prefixes.

This revision recognizes the current producer, including its missing CLI1..44
and driver accounting. A terminal absence witness is not a consumption proof.
No receipt is written and no imported candidate code is executed.
"""
import ast
import hashlib
import json
import pathlib
import re
import uuid

PREFIX = "_offline/phase6e11/endchain_v1/"
BOOTSTRAP = PREFIX + "case_stack_v1/bootstrap.py"
BOUNDARY = PREFIX + "migration_failure_boundaries.py"
HARNESS = "_offline/phase6e11/ci41/runner.py"
PINS = {
    BOOTSTRAP: "c78c8bbccbd4223726519dd170ccfd37c8ac6fe53f3bb5dc4072cd5cba891f73",
    BOUNDARY: "cbc2a69b25a6842ceae0052a90b5eb0e43e90a5ed52e928b16d19333a65510db",
    HARNESS: "18f8efaa9dfc91be59926a40c805499cacce73f5717975b0756a52720839dc45",
    PREFIX + "native_runtime.py": "9d086efe38a5b42b83684754cdc644ed461fbb9ee0311d5ca53fff5445b5ac3a",
}
STAGES = {"pre_migration": "before45", "post_migration": "after45"}
LABELS = ("begin_read_only", "metadata", "rollback")
CLOSEOUT = PREFIX + "quota_candidate_v1/runtime_bootstrap_closeout.py"
CLOSEOUT_SHA = "abb06aeaaaddcd588ee933445aa6f641861989b4edcb704890e0229852b4db61"
PREFIX_PRODUCER = PREFIX + "cli_predispatch/prefix.py"
POLICY_SOURCE = PREFIX + "cli_predispatch/policy.cjs"
POLICY_SHA = "2fc1f9e977aa340245321a87f6f6dbdf92e126512a3eecb6700083fa33924fad"
FROZEN_MANIFEST = "docs/PHASE6E_RELEASE_MANIFEST_20261102.json"
FROZEN_MANIFEST_SHA = "07f6c0e9ac519ee2d055937b06978613dbced11287a75f67c6867e428128885c"
PREFIX_INVENTORY_PINS = {
    PREFIX_PRODUCER: "a4d20abb8a583dab4f9c683d3d515efc86e32c8e23a5298194e72048f4706546",
    PREFIX + "cli_predispatch/pending.py": "29de9b8d0697161a459e436d5c2dc7b08174d36862558efc95470f36527a11ad",
}
REVIEWED_BYTE_PAIRS = PREFIX + "assembly_checks/byte_pairs_20261111.json"
REVIEWED_BYTE_PAIRS_SHA = "ca1684d1139f600c94b871cc2376602738ef103c5ea6f3d35666ea09abd345f2"


class PrefixBlocked(ValueError):
    def __init__(self, code, report=None):
        super().__init__(code)
        self.report = report


def require(value, code):
    if not value:
        raise PrefixBlocked(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "bootstrap_duplicate_json_key")
        result[key] = value
    return result


def _raw(root, name, limit=1400000):
    require(type(name) is str and name and "\\" not in name and ":" not in name,
            "bootstrap_original_path")
    rel = pathlib.PurePosixPath(name)
    require(not rel.is_absolute() and ".." not in rel.parts, "bootstrap_original_path")
    root = pathlib.Path(root).resolve(strict=True)
    path = root / name
    require(all(not p.is_symlink() and not (hasattr(p, "is_junction") and p.is_junction())
                for p in (path, *path.parents) if p != root and p.is_relative_to(root)),
            "bootstrap_original_link")
    require(path.resolve(strict=True).is_relative_to(root), "bootstrap_original_path")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(0 < len(raw) <= limit, "bootstrap_original_size")
    return raw


def reviewed_byte_pairs_raw(root):
    raw = _raw(root, REVIEWED_BYTE_PAIRS, 131072)
    require(sha(raw) == REVIEWED_BYTE_PAIRS_SHA, "bootstrap_byte_pairs_changed")
    return raw


def reviewed_raw_matches(root, name, raw, expected, expected_bytes=None):
    """Keep original pins; admit only a second independently reviewed raw variant."""
    actual = sha(raw)
    if actual == expected and (expected_bytes is None or len(raw) == expected_bytes):
        return True
    try:
        table_raw = reviewed_byte_pairs_raw(root)
    except FileNotFoundError:
        return False
    table = json.loads(table_raw, object_pairs_hook=_pairs)
    # The exact table pin fixes all sixteen paths, both sizes and both raw hashes.
    rows = [row for row in table["pairs"] if row["path"] == name]
    if len(rows) != 1:
        return False
    variants = rows[0]["variants"]
    original = any(v["sha256"] == expected and
                   (expected_bytes is None or (type(expected_bytes) is int and
                                               v["bytes"] == expected_bytes)) for v in variants)
    return original and any(v["sha256"] == actual and v["bytes"] == len(raw) for v in variants)


def inspect_source_checkpoint(root):
    """Read-only drift inventory. Newly present producer bytes are NOT approved."""
    rows, blockers = [], []
    for name, expected in {**PINS, PREFIX_PRODUCER: None}.items():
        try:
            raw = _raw(root, name)
        except FileNotFoundError:
            rows.append(dict(path=name, present=False, expected_sha256=expected,
                             actual_sha256=None, bytes=None, reviewed_match=False))
            blockers.append("missing_source:" + name)
            continue
        actual = sha(raw)
        rows.append(dict(path=name, present=True, expected_sha256=expected,
                         actual_sha256=actual, bytes=len(raw), reviewed_match=actual == expected))
        if expected is not None and actual != expected:
            blockers.append("changed_reviewed_source:" + name)
        elif expected is None:
            blockers.append("new_producer_not_reviewed_or_numerically_verified:" + name)
    return dict(format="admission-bootstrap-source-checkpoint-v1", files=rows,
        reviewed_prefix_sources_match=all(r["reviewed_match"] for r in rows if r["path"] in PINS),
        missing_inputs=blockers, positive_prefix_validator_available=False,
        numeric_total=None, bound_complete=False, runtime_admitted=False, hosted_admitted=False,
        note="Presence/hash identity never establishes protocol coverage or driver consumption.")


def inspect_canonical_policy_inventory(root):
    """Parse frozen bytes offline; policy reservations are NOT execution bounds.

    Uses the installed PG17 parser as an independent statement-count check,
    not as proof of equivalence to the CLI's JavaScript parser or transport.
    The old manifest is a read-only identity reference, never authorization.
    """
    import pglast
    import pglast.parser
    require(pglast.__version__ == "v7.20", "bootstrap_inventory_parser_version")
    paths = (FROZEN_MANIFEST, POLICY_SOURCE, PREFIX_PRODUCER, PREFIX + "cli_predispatch/pending.py")
    originals = {name: _raw(root, name) for name in paths}
    originals[REVIEWED_BYTE_PAIRS] = reviewed_byte_pairs_raw(root)
    require(sha(originals[FROZEN_MANIFEST]) == FROZEN_MANIFEST_SHA, "bootstrap_frozen_manifest_changed")
    require(sha(originals[POLICY_SOURCE]) == POLICY_SHA, "bootstrap_policy_source_changed")
    require(all(sha(originals[name]) == expected for name, expected in PREFIX_INVENTORY_PINS.items()),
            "bootstrap_prefix_inventory_source_changed")
    # The exact source pin, not a permissive regex, binds this policy expression.
    require(b"policy.cap = migrations[0].ast_hashes.length + 16;" in originals[POLICY_SOURCE],
            "bootstrap_prefix_cap_expression")
    manifest = json.loads(originals[FROZEN_MANIFEST], object_pairs_hook=_pairs)
    migrations = manifest["canonical_migrations"]
    require(type(migrations) is list and len(migrations) == 45
            and migrations[-1]["ordinal"] == 45, "bootstrap_frozen_count")
    migrations = migrations[:44]
    rows, seen = [], set()
    for ordinal, migration in enumerate(migrations, 1):
        name = migration["path"]
        require(type(migration["ordinal"]) is int and migration["ordinal"] == ordinal
                and type(name) is str and re.fullmatch(r"supabase/migrations/[a-z0-9_]+\.sql", name)
                and name not in seen, "bootstrap_frozen_order")
        seen.add(name)
        raw = _raw(root, name, 131072)
        require(reviewed_raw_matches(root, name, raw, migration["sha256"], migration["bytes"]),
                "bootstrap_frozen_bytes:" + str(ordinal))
        originals[name] = raw
        count = len(pglast.parse_sql(raw.decode("utf-8")))
        rows.append(dict(ordinal=ordinal, path=name, sha256=sha(raw), bytes=len(raw),
            body_statement_count=count, declared_cli_policy_cap=count + 16,
            policy_scope="local_ci_canonical_prefix", hosted_command=False))
    parser_path = pathlib.Path(pglast.parser.__file__)
    parser_raw = parser_path.read_bytes()
    result = dict(format="admission-canonical-prefix-policy-inventory-v1", migrations=rows,
        source_hashes={name: sha(raw) for name, raw in originals.items()},
        parser=dict(version=pglast.__version__, binary_name=parser_path.name, binary_sha256=sha(parser_raw),
                    independent_statement_count_only=True, cli_parser_equivalence_proven=False),
        body_statement_count=sum(r["body_statement_count"] for r in rows),
        declared_cli_policy_cap_sum=sum(r["declared_cli_policy_cap"] for r in rows),
        policy_formula="each AST body count + 16", invocation_count=44,
        observer_success_commands_per_invocation=8, isolation_success_commands_options=[4, 8],
        additional_costs_not_in_policy_sum=["history_provision_and_rollback",
            "catalog_before41", "all_observers", "isolation_and_restore", "implicit_driver_commands",
            "native_preflight", "migration_boundaries", "platform_epochs", "failure_closeout"],
        total_local_ci_upper_bound=None, total_hosted_equivalent_upper_bound=None,
        hosted_limit=2349, historical_normal=2338, historical_closing=731,
        observed_commands=None, bound_complete=False, minimal_cap=None,
        frozen_reference_is_authorization=False, runtime_admitted=False, hosted_admitted=False,
        actual_execution_evidence=False)
    require(all(_raw(root, name) == raw for name, raw in originals.items())
            and parser_path.read_bytes() == parser_raw, "bootstrap_inventory_source_raced")
    return result


def source_program(root):
    """Exact reviewed call order, including the otherwise hidden pre-M41 read."""
    raw = {name: _raw(root, name) for name in PINS}
    from admission_budget_prefix_originals import CURRENT_PINS, PRODUCER
    current = reviewed_raw_matches(root, BOOTSTRAP, raw[BOOTSTRAP], CURRENT_PINS[BOOTSTRAP])
    selected = dict(PINS)
    if current:
        selected.update(CURRENT_PINS)
        raw.update({name: _raw(root, name) for name in CURRENT_PINS})
        selected[REVIEWED_BYTE_PAIRS] = REVIEWED_BYTE_PAIRS_SHA
        raw[REVIEWED_BYTE_PAIRS] = reviewed_byte_pairs_raw(root)
    if not all(reviewed_raw_matches(root, name, raw[name], expected) for name, expected in selected.items()):
        raise PrefixBlocked("bootstrap_prefix_source_changed", inspect_source_checkpoint(root))
    tree = ast.parse(raw[BOOTSTRAP])
    if current:
        unknown_totals = [value for node in ast.walk(tree) if isinstance(node, ast.Dict)
                          for key, value in zip(node.keys, node.values)
                          if isinstance(key, ast.Constant) and key.value == "bootstrap_total_sql_commands"]
        require(len(unknown_totals) == 2 and all(isinstance(value, ast.Constant) and value.value is None
                                               for value in unknown_totals), "bootstrap_prefix_producer_changed")
    else:
        require(any(isinstance(n, ast.Constant) and n.value == "NOT_MEASURED_BY_THIS_HELPER"
                    for n in ast.walk(tree)), "bootstrap_prefix_producer_changed")
    def row(ident, explicit=None, **fields):
        return dict(command_id=ident, explicit_sql_commands=explicit,
                    total_sql_commands=None, **fields)
    base = [row("bootstrap.native.before", 3, connections=1, closes=1)]
    if current:
        base.append(row("bootstrap.history.provision", 7, reserved_explicit=8, connections=1, closes=1,
                        missing="original_ref_closure_is_not_driver_or_protocol_replay"))
    for index in range(1, 45):
        if index == 41:
            base.append(row("bootstrap.catalog.before41", 1, caller="Gate.catalog -> Gate.rows -> Gate.sql"))
        base.append(row("bootstrap.canonical." + str(index), cli_calls=1,
                        missing="original_frontend_numeric_driver_replay_required" if current else
                                "legacy_cli_protocol_and_observers_not_measured"))
    base.append(row("bootstrap.boundary.pre", 8, connections=2, closes=2, reserved_explicit=12))
    post = base + [row("bootstrap.canonical.45", cli_calls=1,
        protocol_cap=64, observer_cap=8, isolation_normal_options=[4, 8],
        missing="original_CLI_replay_and_driver_partitions_required"),
        row("bootstrap.boundary.post", 8, connections=2, closes=2, reserved_explicit=12)]
    closeout = dict(command_id="case.bootstrap.failure_closeout", explicit_sql_commands=4,
        driver_sql_commands=None, total_sql_commands=None, connections=1, closes=1,
        process_calls=3, process_sources=["collect:docker_inventory", "NativeRuntime.disposable:password",
                                        "NativeRuntime.disposable:port"],
        hosted_equivalent_sql_commands=0, distinct_precharge=True,
        failure_rollback="one attempt iff BEGIN attempted; no retry", auth_started=False)
    result = dict(format="admission-bootstrap-prefix-source-v1",
        source_hashes={name: sha(raw[name]) for name in selected},
        canonical_originals_producer=current,
        cases={name: dict(stage=stage, prefix=base if name == "pre_migration" else post,
            source_known_explicit_sql_excluding_cli=(12 if name == "pre_migration" else 20) + (7 if current else 0),
            failure_closeout=closeout, next_normal=None, auth_context_permitted=False,
            complete_upper_bound=None, hosted_equivalent_sql_commands=0)
            for name, stage in STAGES.items()},
        platform_install="separate original root ticket, never folded into bootstrap",
        counters_are_source_inventory_not_actual_execution=True, full_chain_admission=False)
    require(all(_raw(root, name) == value for name, value in raw.items()),
            "bootstrap_prefix_source_raced")
    return result


class Originals:
    def __init__(self, folder):
        self.folder, self.refs = pathlib.Path(folder), {}

    def read(self, name, expected=None):
        raw = _raw(self.folder, name)
        ref = dict(path=name, sha256=sha(raw), bytes=len(raw))
        if expected is not None:
            require(type(expected) is dict and expected == ref, "bootstrap_original_reference")
        if name in self.refs:
            require(self.refs[name] == ref, "bootstrap_original_changed")
        self.refs[name] = ref
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda _: require(False, "bootstrap_json_nonfinite"))

    def finish(self):
        for name, ref in self.refs.items():
            raw = _raw(self.folder, name)
            require(sha(raw) == ref["sha256"] and len(raw) == ref["bytes"], "bootstrap_original_changed")
        return list(self.refs.values())


def _identity(gate, binding, case_name, fault, originals):
    require(case_name in STAGES and type(binding) is dict, "bootstrap_case")
    run = binding.get("run_id")
    require(type(run) is str and str(uuid.UUID(run)) == run and uuid.UUID(run).version == 4
            and run not in ("6f8c8909-9b79-4011-a9d1-db5e23c6b6c1", "11a909f4-7113-424a-aa4b-ce9964720a3e")
            and binding.get("environment") == "disposable_ci", "bootstrap_fresh_local_binding")
    for key, pattern in (("source_commit", "[a-f0-9]{40}"), ("candidate_sha", "[a-f0-9]{64}"),
                         ("ci_run", "[1-9][0-9]{0,18}")):
        require(type(binding.get(key)) is str and re.fullmatch(pattern, binding[key]), "bootstrap_binding")
    require(gate.result.get("candidate_sha256") == binding["candidate_sha"]
            and gate.result.get("commit", gate.result.get("head")) == binding["source_commit"]
            and str(gate.result.get("run_id")) == binding["ci_run"], "bootstrap_gate_binding")
    require(fault.case == case_name and fault.binding == binding, "bootstrap_fault_owner")
    fired = originals.read("case-fault-boundary.json")
    require(fired == fault.fired and fired.get("case") == case_name and fired.get("run_id") == run
            and fired.get("original_error_code") == "case_injected_" + case_name
            and fired.get("event", {}).get("stage") == STAGES[case_name]
            and fired.get("automatic_retry") is False, "bootstrap_fault_original")
    identity = dict(source_commit=binding["source_commit"], ci_run=binding["ci_run"],
                    candidate_sha256=binding["candidate_sha"])
    require(all(fired.get(k if k != "candidate_sha256" else "candidate_sha") == v
                for k, v in identity.items()), "bootstrap_fault_identity")
    return dict(run_id=run, case_name=case_name, **identity)


def inspect_bootstrap_fault_prefix(gate, *, binding, case_name, fault):
    originals = Originals(gate.out)
    identity = _identity(gate, binding, case_name, fault, originals)
    program = source_program(gate.sources)
    attempt = originals.read("case-stack-attempt.json")
    failure = originals.read("case-stack-failure.json")
    for value in (attempt, failure):
        require(all(value.get(k) == v for k, v in identity.items() if k not in ("run_id", "case_name")),
                "bootstrap_receipt_identity")
    candidate = originals.read("candidate.json")
    require(candidate.get("sha256") == binding["candidate_sha"]
            and originals.refs["candidate.json"]["sha256"] == attempt.get("candidate_manifest_sha256")
            and all(candidate.get("sources", {}).get(name) == expected
                    for name, expected in program["source_hashes"].items() if name != HARNESS), "bootstrap_candidate_sources")
    canonical = None
    if program["canonical_originals_producer"]:
        from admission_budget_prefix_originals import inspect_canonical_prefix
        canonical = inspect_canonical_prefix(gate, binding=binding)
        require(attempt.get("run_id") == identity["run_id"] and failure.get("run_id") == identity["run_id"],
                "bootstrap_attempt_case_identity")
        for ref in canonical["evidence_refs"]:
            raw = _raw(gate.out, ref["path"])
            require(sha(raw) == ref["sha256"] and len(raw) == ref["bytes"], "bootstrap_original_changed")
            originals.refs[ref["path"]] = ref
    require(failure.get("stage") == "canonical45" and failure.get("boundary_stage") == STAGES[case_name]
            and failure.get("status") == "NO_GO" and failure.get("history_commands") == []
            and failure.get("admin_sql_reserved") == 0 and failure.get("admin_sql_confirmed") is None,
            "bootstrap_fault_prefix_stage")
    reserve_name = "case-stack-reserve-native-before.json"
    reserve = originals.read(reserve_name)
    require(reserve.get("commands") == list(LABELS) and type(reserve.get("reserved")) is int
            and reserve["reserved"] == 3, "bootstrap_native_reservation")
    trace = failure.get("native_commands")
    require(type(trace) is list and len(trace) == 3, "bootstrap_native_trace")
    for label, row in zip(LABELS, trace):
        require(row.get("stage") == "before" and row.get("command") == label
                and row.get("confirmed") is True, "bootstrap_native_unconfirmed")
        originals.read(reserve_name, row.get("reservation_ref"))
        intent = originals.read("case-stack-native-before-" + label + "-intent.json")
        confirmed = originals.read("case-stack-native-before-" + label + "-confirmed.json")
        require(confirmed == row and intent == {**row, "confirmed": False}, "bootstrap_native_original")
    stages = ("before45",) if case_name == "pre_migration" else ("before45", "after45")
    for stage in stages:
        boundary = originals.read("case-stack-boundary-" + stage + ".json")
        require(boundary.get("stage") == stage and all(boundary.get(k) == v
                for k, v in identity.items() if k not in ("run_id", "case_name")), "bootstrap_boundary_identity")
        expected_names = (["migration-boundary-pre.json"] if stage == "before45" else
                          ["cli-predispatch-canonical-45.json", "migration-boundary-post.json"])
        if canonical is not None:
            expected_names.insert(0, "case-stack-canonical-prefix.json")
        refs = boundary.get("evidence_refs")
        require(type(refs) is list and [r.get("path") for r in refs] == expected_names,
                "bootstrap_boundary_references")
        for ref in refs:
            originals.read(ref["path"], ref)
        if stage == STAGES[case_name]:
            require(refs == fault.fired["event"].get("evidence_refs"), "bootstrap_fault_boundary_references")
    # Native rows are individually evidenced. Boundary/CLI summaries are retained
    # as originals, not promoted to independent protocol replay or driver proof.
    missing = ["canonical_1_44:original_complete_protocol_prefix_missing",
               "catalog_before41:original_wrapped_psql_dispatch_not_joined",
               "native_connections:effective_driver_binary_environment_and_close_cost_unproven",
               "migration_boundary:original_protocol_and_driver_partitions_not_joined"]
    if canonical is not None:
        missing = canonical["missing_costs"] + missing[2:]
    if case_name == "post_migration":
        missing.append("canonical45:original_frontend_ledger_numeric_observers_isolation_replay_required")
    report = dict(format="admission-bootstrap-fault-prefix-audit-v1", **identity,
        status="NO_GO_INCOMPLETE_BOOTSTRAP_PREFIX", complete_numeric_prefix=False,
        observed_sql_commands=None, individually_confirmed_native_commands=len(trace),
        source_program=program["cases"][case_name], source_hashes=program["source_hashes"],
        canonical_original_audit=canonical,
        original_fault_code=fault.fired["original_error_code"], missing_costs=missing,
        failure_closeout_included=False, platform_install_included=False,
        full_chain_admission=False, hosted_admitted=False, evidence_refs=originals.finish())
    return report


def validate_bootstrap_fault_prefix(gate, *, binding, case_name, fault):
    report = inspect_bootstrap_fault_prefix(gate, binding=binding, case_name=case_name, fault=fault)
    # Original sidecars alone do not prove complete protocol/driver consumption.
    raise PrefixBlocked("bootstrap_prefix_incomplete", report)


def inspect_bootstrap_failure_closeout(gate, *, binding, case_name, fault, isolation, proof):
    originals = Originals(gate.out)
    identity = _identity(gate, binding, case_name, fault, originals)
    program = source_program(gate.sources)
    require(type(isolation) is dict and type(proof) is dict
            and isolation.get("run_id") == binding["run_id"], "bootstrap_closeout_owner")
    source = _raw(gate.sources, CLOSEOUT)
    require(sha(source) == CLOSEOUT_SHA, "bootstrap_closeout_source_changed")
    literals = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("IDENTITY", "ACCOUNTS"):
                literals[node.targets[0].id] = ast.literal_eval(node.value)
    sql = ["BEGIN TRANSACTION READ ONLY", literals["IDENTITY"], literals["ACCOUNTS"], "ROLLBACK"]
    refs = isolation.get("auth_absence", {})
    require(type(refs.get("account_inventory_ref")) is dict
            and type(refs.get("container_inventory_ref")) is dict, "bootstrap_closeout_original_refs")
    accounts = originals.read("case-preauth-account-absence.json", refs.get("account_inventory_ref"))
    originals.read("case-preauth-container-absence.json", refs.get("container_inventory_ref"))
    require(all(accounts.get(k) == v for k, v in identity.items()) and accounts.get("complete") is True
            and accounts.get("rollback_confirmed") is True and accounts.get("connection_closed") is True,
            "bootstrap_closeout_unconfirmed")
    commands = accounts.get("commands")
    require(type(commands) is list and len(commands) == 4 and
            [r.get("ordinal") for r in commands] == [1, 2, 3, 4]
            and all(r.get("confirmed") is True and r.get("sql_sha256") == sha(text.encode())
                    for r, text in zip(commands, sql)), "bootstrap_closeout_trace")
    return dict(format="admission-bootstrap-closeout-audit-v1", **identity,
        status="NO_GO_DRIVER_PARTITION_UNPROVEN", explicit_sql_commands=4,
        driver_sql_commands=None, observed_sql_commands=None, complete_numeric_closeout=False,
        process_calls=3, bootstrap_prefix_included=False,
        missing_costs=["closeout_connect_and_close:effective_driver_binary_environment_bound_missing"],
        source_hashes={**program["source_hashes"], CLOSEOUT: CLOSEOUT_SHA},
        full_chain_admission=False, hosted_admitted=False, evidence_refs=originals.finish())


def validate_bootstrap_failure_closeout(gate, *, binding, case_name, fault, isolation, proof):
    report = inspect_bootstrap_failure_closeout(gate, binding=binding, case_name=case_name,
        fault=fault, isolation=isolation, proof=proof)
    raise PrefixBlocked("bootstrap_closeout_driver_incomplete", report)
