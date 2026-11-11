"""Audit the new 44-invocation sidecar without granting numeric admission.

Original hashes and explicit auxiliary witnesses are checked independently.
Frontend protocol/numeric interval replay and driver costs remain separate,
mandatory inputs. No original is written and no candidate code is imported.
"""
import ast
import json
import re
import uuid

import admission_budget_bootstrap_prefix as prefix

PRODUCER = prefix.PREFIX + "case_stack_v1/prefix_receipt.py"
CURRENT_PINS = {
    prefix.BOOTSTRAP: "6e3f2b1ecaa1945a0bd20256c4fec91f9c25310153ae499eebcc6e4c986b3c33",
    PRODUCER: "aaa3e8991d4b3f3914a7f461dd93c28ceeb513de5317b9b570df8bc80f72c8d3",
    prefix.PREFIX_PRODUCER: "a4d20abb8a583dab4f9c683d3d515efc86e32c8e23a5298194e72048f4706546",
    prefix.PREFIX + "cli_predispatch/pending.py": "29de9b8d0697161a459e436d5c2dc7b08174d36862558efc95470f36527a11ad",
    prefix.PREFIX + "cli_predispatch/ci.py": "02d7a231cc645c5d69e0442ec4357c9e10182892a651c3e0da4f7f0d0a534ca9",
    prefix.PREFIX + "cli_predispatch/hook.cjs": "d8813529e17d4e471c1f4aeb34c8c572932d781d427574f51d610e67120a078a",
    prefix.PREFIX + "cli_predispatch/entry.mjs": "776c838b01c3ca4c297d0226b54154e79204c175a2d59d72d4b95bd99903023d",
    prefix.POLICY_SOURCE: "2fc1f9e977aa340245321a87f6f6dbdf92e126512a3eecb6700083fa33924fad",
}
NAME = "case-stack-canonical-prefix.json"
ARGS = ["migration", "up", "--local"]
EXECUTED = ["db", "push", "--db-url", "<private-loopback-verify-full>",
            "--skip-vault", "--yes", "--include-all", "--output-format", "json"]


def need(value, code):
    prefix.require(value, "canonical_originals_" + code)


def _uuid(value):
    try:
        return type(value) is str and str(uuid.UUID(value)) == value and uuid.UUID(value).version == 4
    except ValueError:
        return False


def _hash(value):
    return type(value) is str and re.fullmatch("[a-f0-9]{64}", value) is not None


def _same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


class Evidence(prefix.Originals):
    def raw_ref(self, ref):
        need(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}
             and type(ref["bytes"]) is int and 0 < ref["bytes"] <= 1400000, "ref_shape")
        raw = prefix._raw(self.folder, ref["path"])
        actual = dict(path=ref["path"], sha256=prefix.sha(raw), bytes=len(raw))
        need(actual == ref and self.refs.get(ref["path"], actual) == actual, "ref_changed")
        self.refs[ref["path"]] = actual
        return raw

    def json_ref(self, ref):
        return json.loads(self.raw_ref(ref), object_pairs_hook=prefix._pairs,
                          parse_constant=lambda _: need(False, "nonfinite"))


def _source_contract(source_root, candidate):
    raw = {name: prefix._raw(source_root, name) for name in CURRENT_PINS}
    need(all(prefix.reviewed_raw_matches(source_root, name, raw[name], expected)
             for name, expected in CURRENT_PINS.items()), "producer_revision")
    tree = ast.parse(raw[PRODUCER])
    producers = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "PRODUCERS" for t in n.targets))
    need({prefix.PREFIX + relative for relative in producers} == set(CURRENT_PINS), "producer_inventory")
    hashes = {}
    for relative in producers:
        name = prefix.PREFIX + relative
        data = prefix._raw(source_root, name)
        need(data == raw[name], "source_raced")
        need(candidate.get("sources", {}).get(name) == prefix.sha(data), "candidate_producer_binding")
        raw[name], hashes[name] = data, prefix.sha(data)
    table = prefix.reviewed_byte_pairs_raw(source_root)
    need(candidate.get("sources", {}).get(prefix.REVIEWED_BYTE_PAIRS) == prefix.sha(table),
         "candidate_byte_pairs_binding")
    raw[prefix.REVIEWED_BYTE_PAIRS] = table
    harness = prefix._raw(source_root, prefix.HARNESS)
    need(prefix.sha(harness) == prefix.PINS[prefix.HARNESS], "catalog_caller_source")
    raw[prefix.HARNESS] = harness
    catalog = next(n for n in ast.walk(ast.parse(harness)) if isinstance(n, ast.FunctionDef) and n.name == "catalog")
    call = catalog.body[0].value
    need(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
         and call.func.attr == "rows" and len(call.args) == 1, "catalog_caller_shape")
    sql = "select coalesce(json_agg(q),'[]') from (" + ast.literal_eval(call.args[0]) + ") q;"
    tree = ast.parse(raw[prefix.PREFIX_PRODUCER])
    setup = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "HISTORY_SETUP" for t in n.targets))
    need(len(setup) == 7 and setup[0] == "BEGIN" and setup[-1] == "COMMIT", "provision_source")
    return raw, hashes, prefix.sha(sql.encode()), setup


def inspect_canonical_prefix(gate, *, binding):
    """Original-ref closure only; always returns incomplete numeric accounting."""
    need(type(binding) is dict and _uuid(binding.get("run_id"))
         and binding["run_id"] not in ("6f8c8909-9b79-4011-a9d1-db5e23c6b6c1",
                                      "11a909f4-7113-424a-aa4b-ce9964720a3e")
         and binding.get("environment") == "disposable_ci", "fresh_case")
    identity = dict(source_commit=binding["source_commit"], candidate_sha256=binding["candidate_sha"],
                    ci_run=binding["ci_run"], run_id=binding["run_id"])
    need(gate.result.get("candidate_sha256") == binding["candidate_sha"]
         and gate.result.get("commit", gate.result.get("head")) == binding["source_commit"]
         and str(gate.result.get("run_id")) == binding["ci_run"], "gate_binding")
    evidence = Evidence(gate.out)
    summary, candidate = evidence.read(NAME), evidence.read("candidate.json")
    need(summary.get("format") == "case-stack-canonical-prefix-v1"
         and all(summary.get(k) == v for k, v in identity.items())
         and candidate.get("sha256") == binding["candidate_sha"]
         and summary.get("candidate_manifest_sha256") == evidence.refs["candidate.json"]["sha256"], "identity")
    need(summary.get("original_refs_complete") is True and summary.get("independent_numeric_validation") is False
         and summary.get("total_sql_commands") is None and summary.get("implicit_driver_sql_commands") is None
         and summary.get("hosted_admission") is False, "summary_not_numeric_authority")
    raw, sources, catalog_sha, setup = _source_contract(gate.sources, candidate)
    need(summary.get("producer_sources") == sources, "producer_sources")
    migrations = sorted(n for n in candidate["sources"] if n.startswith("supabase/migrations/"))
    need(len(migrations) == 45, "canonical_inventory")
    invocations = summary.get("invocations")
    need(type(invocations) is list and len(invocations) == 44, "invocation_count")
    identifiers = set()
    for index, row in enumerate(invocations, 1):
        path = migrations[index-1]
        migration = prefix._raw(gate.sources, path, 131072)
        need(type(row.get("ordinal")) is int and row["ordinal"] == index and row.get("migration_path") == path
             and row.get("migration_sha256") == candidate["sources"][path] == prefix.sha(migration), "migration_order")
        raw[path] = migration
        identifier = row.get("invocation_id")
        need(_uuid(identifier) and identifier not in identifiers, "invocation_identity")
        identifiers.add(identifier)
        need(row.get("requested_arguments") == ARGS and row.get("executed_argument_shape") == EXECUTED,
             "argument_shape")
        refs = row.get("original_refs")
        need(type(refs) is dict and set(refs) == {"receipt", "preregister", "policy", "ledger", "isolation"},
             "invocation_refs")
        tag = "cli-predispatch-prefix-" + str(index)
        names = dict(receipt=tag + ".json", preregister=tag + "-preregister.json", policy=tag + ".policy.json",
                     ledger=tag + ".ledger.txt", isolation="prefix-" + str(index) + "-cli-predispatch-cli-isolation-0.json")
        need(all(refs[k].get("path") == name for k, name in names.items()), "invocation_ref_names")
        receipt, pre, policy, isolation = (evidence.json_ref(refs[k]) for k in
                                           ("receipt", "preregister", "policy", "isolation"))
        ledger = evidence.raw_ref(refs["ledger"])
        first = ledger.splitlines()[0]
        need(len(first) <= 8192, "ledger_header_bound")
        header = json.loads(first, object_pairs_hook=prefix._pairs,
                            parse_constant=lambda _: need(False, "nonfinite"))
        # Identity only: neither subsequent events nor numeric intervals are replayed here.
        need(type(header) is dict and header.get("event") == "preregister"
             and all(header.get(k) == v for k, v in identity.items())
             and header.get("invocation_id") == identifier and header.get("slot") == "ci_prefix"
             and type(header.get("prefix_index")) is int and header["prefix_index"] == index,
             "ledger_header_identity")
        for value in (receipt, pre):
            need(all(value.get(k) == v for k, v in identity.items())
                 and value.get("profile") == "canonical_prefix" and type(value.get("prefix_index")) is int
                 and value["prefix_index"] == index and value.get("invocation_id") == identifier
                 and value.get("expected_migration") == path and value.get("expected_migration_sha256") == prefix.sha(migration)
                 and _same(value.get("policy"), policy), "invocation_source_binding")
        need(receipt.get("complete") is True and pre.get("complete") is False
             and receipt.get("local_bootstrap_only") is True and receipt.get("actual_migration_execution") is True
             and policy.get("invocation_id") == identifier and policy.get("slot") == "ci_prefix"
             and all(policy.get(k) == v for k, v in identity.items()), "invocation_state")
        for kind in ("policy", "ledger"):
            need(receipt.get(kind + "_ref") == {k: refs[kind][k] for k in ("path", "sha256")}, "nested_ref")
        need(receipt.get("isolation_receipt") == names["isolation"]
             and receipt.get("isolation_receipt_sha256") == refs["isolation"]["sha256"]
             and isolation.get("restored") is True, "isolation_ref")
        need(all(k in receipt for k in ("numeric_before", "numeric_after", "observer_trace", "terminal")),
             "numeric_originals_absent")
    catalog = evidence.json_ref(summary["catalog_before41_ref"])
    need(all(catalog.get(k) == v for k, v in identity.items()) and type(catalog.get("migrations_applied")) is int
         and catalog["migrations_applied"] == 40
         and catalog.get("attempted") is True and catalog.get("confirmed") is True
         and "failure_class" not in catalog and catalog.get("implicit_driver_sql_commands") is None
         and catalog.get("sql_sha256") == catalog_sha, "catalog_witness")
    before, after = catalog.get("command_serial_before"), catalog.get("command_serial_after")
    need(type(before) is int and before >= 0 and type(after) is int and after == before+1, "catalog_order")
    need(catalog.get("command_ref", {}).get("path") == "%03d-psql.json" % after, "catalog_command_ref")
    command = evidence.json_ref(catalog["command_ref"])
    need(command.get("phase") == "migration_41" and type(command.get("exitcode")) is int
         and command["exitcode"] == 0, "catalog_command_failure")
    need(catalog.get("reservation_ref", {}).get("path") == "case-stack-reserve-catalog-before41.json",
         "catalog_reservation_name")
    reserve = evidence.json_ref(catalog["reservation_ref"])
    need(reserve.get("commands") == ["catalog"] and type(reserve.get("reserved")) is int
         and reserve["reserved"] == 1, "catalog_reserve")
    intent = evidence.read("case-stack-catalog-before41-intent.json")
    expected_intent = {k: v for k, v in catalog.items() if k not in ("command_serial_after", "command_ref")}
    expected_intent["confirmed"] = False
    need(_same(intent, expected_intent), "catalog_intent")
    expected_originals = dict(command=catalog["command_ref"], reservation=catalog["reservation_ref"],
                              intent=evidence.refs["case-stack-catalog-before41-intent.json"])
    need(_same(summary.get("catalog_original_refs"), expected_originals), "catalog_summary_originals")
    provision_refs = summary.get("history_provision_refs")
    need(type(provision_refs) is list and len(provision_refs) == 16, "provision_ref_count")
    names = ["cli-prefix-history-provision.json", "cli-prefix-history-provision-reserve.json"]
    names += ["cli-prefix-history-provision-" + str(i) + "-" + suffix + ".json"
              for i in range(1, 8) for suffix in ("intent", "confirmed")]
    need([r.get("path") for r in provision_refs] == names, "provision_ref_order")
    provision, prepaid, *pairs = [evidence.json_ref(r) for r in provision_refs]
    need(all(value.get(k) == v for value in (provision, prepaid) for k, v in identity.items())
         and provision.get("complete") is True and provision.get("implicit_driver_sql_proven") is False
         and provision.get("secondary_error_classes") == [] and type(provision.get("explicit_reserve")) is int
         and provision["explicit_reserve"] == 8
         and prepaid.get("complete") is False and prepaid.get("protocol") == []
         and type(prepaid.get("explicit_reserve")) is int and prepaid["explicit_reserve"] == 8, "provision_state")
    need(type(provision.get("protocol")) is list and len(provision["protocol"]) == 7, "provision_count")
    for i, (row, sql) in enumerate(zip(provision["protocol"], setup)):
        expected = dict(ordinal=i+1, sql_sha256=prefix.sha(sql.encode()), confirmed=True)
        need(_same(row, expected) and _same(pairs[2*i+1], expected)
             and _same(pairs[2*i], {**expected, "confirmed": False}), "provision_original")
    need(all(prefix._raw(gate.sources, name) == data for name, data in raw.items()), "source_raced")
    return dict(format="admission-canonical-prefix-original-audit-v1", **identity,
        invocation_count=44, original_ref_closure_verified=True, explicit_auxiliary_confirmed=8,
        catalog_confirmed=1, provision_confirmed=7, implicit_driver_sql_commands=None,
        independent_numeric_validation=False, total_sql_commands=None, complete_numeric_prefix=False,
        protocol_replay_complete=False, source_hashes={n: prefix.sha(v) for n, v in raw.items()},
        evidence_refs=evidence.finish(), missing_costs=["44_CLI_frontend_and_numeric_interval_replay",
            "all_CLI_observer_isolation_and_driver_partitions", "provision_catalog_driver_partitions"],
        status="ORIGINAL_REFS_VERIFIED_NUMERIC_NO_GO", full_chain_admission=False, hosted_admitted=False)
