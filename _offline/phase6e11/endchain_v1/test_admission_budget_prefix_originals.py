"""A-reader adversarial fixtures, not the producer's orchestration tests."""
import ast
import copy
import hashlib
import json
import pathlib
import tempfile
import types
import unittest
import uuid
from unittest.mock import patch

import admission_budget_prefix_originals as audit


class OriginalReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        folder = pathlib.Path(self.temp.name)
        self.out, self.sources = folder / "out", folder / "source"
        self.out.mkdir()
        (self.sources / "supabase/migrations").mkdir(parents=True)
        self.binding = dict(run_id=str(uuid.uuid4()), source_commit="a"*40, ci_run="123",
                            candidate_sha="b"*64, environment="disposable_ci")
        self.identity = dict(run_id=self.binding["run_id"], source_commit="a"*40, ci_run="123", candidate_sha256="b"*64)
        self.gate = types.SimpleNamespace(out=self.out, sources=self.sources,
            result=dict(commit="a"*40, run_id="123", candidate_sha256="b"*64))
        source_hashes = {}
        for i in range(1, 46):
            name = "supabase/migrations/%014d_unit.sql" % i
            raw = b"SELECT 1;\n"
            (self.sources / name).write_bytes(raw)
            source_hashes[name] = audit.prefix.sha(raw)
        candidate = self.save("candidate.json", dict(sha256="b"*64, sources=source_hashes))
        invocations = []
        for i, path in enumerate(sorted(source_hashes)[:44], 1):
            ident = str(uuid.uuid4())
            policy = dict(**self.identity, invocation_id=ident, slot="ci_prefix")
            tag = "cli-predispatch-prefix-" + str(i)
            refs = dict(policy=self.save(tag + ".policy.json", policy),
                        ledger=self.save(tag + ".ledger.txt", dict(**self.identity, synthetic=True,
                            event="preregister", invocation_id=ident, slot="ci_prefix", prefix_index=i)),
                        isolation=self.save("prefix-" + str(i) + "-cli-predispatch-cli-isolation-0.json", {"restored": True}))
            receipt = dict(**self.identity, profile="canonical_prefix",
                prefix_index=i, invocation_id=ident, expected_migration=path,
                expected_migration_sha256=source_hashes[path], policy=policy, complete=False,
                local_bootstrap_only=True, actual_migration_execution=False)
            refs["preregister"] = self.save(tag + "-preregister.json", receipt)
            receipt.update(complete=True, actual_migration_execution=True, numeric_before={}, numeric_after={},
                observer_trace=[], terminal={}, isolation_receipt=refs["isolation"]["path"],
                isolation_receipt_sha256=refs["isolation"]["sha256"])
            for key in ("policy", "ledger"):
                receipt[key + "_ref"] = {k: refs[key][k] for k in ("path", "sha256")}
            refs["receipt"] = self.save(tag + ".json", receipt)
            invocations.append(dict(ordinal=i, migration_path=path, migration_sha256=source_hashes[path],
                invocation_id=ident, requested_arguments=audit.ARGS, executed_argument_shape=audit.EXECUTED,
                original_refs=refs))
        reserve = self.save("case-stack-reserve-catalog-before41.json", dict(commands=["catalog"], reserved=1))
        catalog = dict(**self.identity, migrations_applied=40, attempted=True, confirmed=False,
            implicit_driver_sql_commands=None, sql_sha256="c"*64, command_serial_before=9, reservation_ref=reserve)
        intent_ref = self.save("case-stack-catalog-before41-intent.json", catalog)
        catalog.update(confirmed=True, command_serial_after=10,
            command_ref=self.save("010-psql.json", dict(phase="migration_41", exitcode=0)))
        catalog_ref = self.save("case-stack-catalog-before41.json", catalog)
        self.setup_sql = ("BEGIN", "SELECT 1", "SELECT 2", "SELECT 3", "SELECT 4", "SELECT 5", "COMMIT")
        provision = dict(**self.identity,
            complete=False, implicit_driver_sql_proven=False, explicit_reserve=8, protocol=[])
        prepaid = self.save("cli-prefix-history-provision-reserve.json", provision)
        sidecars = []
        for i, sql in enumerate(self.setup_sql, 1):
            row = dict(ordinal=i, sql_sha256=audit.prefix.sha(sql.encode()), confirmed=True)
            provision["protocol"].append(row)
            for suffix, value in (("intent", {**row, "confirmed": False}), ("confirmed", row)):
                sidecars.append(self.save("cli-prefix-history-provision-" + str(i) + "-" + suffix + ".json", value))
        provision.update(complete=True, secondary_error_classes=[])
        refs = [self.save("cli-prefix-history-provision.json", provision), prepaid, *sidecars]
        self.summary = dict(**self.identity, format="case-stack-canonical-prefix-v1",
            candidate_manifest_sha256=candidate["sha256"], original_refs_complete=True,
            independent_numeric_validation=False, implicit_driver_sql_commands=None, total_sql_commands=None,
            hosted_admission=False, producer_sources={}, invocations=invocations,
            catalog_before41_ref=catalog_ref, history_provision_refs=refs,
            catalog_original_refs=dict(command=catalog["command_ref"], reservation=reserve, intent=intent_ref))
        source = patch.object(audit, "_source_contract", return_value=({}, {}, "c"*64, self.setup_sql))
        source.start()
        self.addCleanup(source.stop)

    def save(self, name, value):
        raw = json.dumps(value, sort_keys=True).encode()
        (self.out / name).write_bytes(raw)
        return dict(path=name, sha256=audit.prefix.sha(raw), bytes=len(raw))

    def run_reader(self):
        self.save(audit.NAME, self.summary)
        return audit.inspect_canonical_prefix(self.gate, binding=self.binding)

    def mutate(self, ref, change):
        value = json.loads((self.out / ref["path"]).read_bytes())
        change(value)
        new = self.save(ref["path"], value)
        ref.update(new)

    def test_hashed_reference_closure_is_never_numeric_protocol_pass(self):
        result = self.run_reader()
        self.assertEqual(result["invocation_count"], 44)
        self.assertEqual(result["explicit_auxiliary_confirmed"], 8)
        self.assertFalse(result["independent_numeric_validation"])
        self.assertFalse(result["protocol_replay_complete"])
        self.assertFalse(result["hosted_admitted"])
        self.assertIsNone(result["total_sql_commands"])

    def test_catalog_missing_transitive_command_ref_denied(self):
        self.mutate(self.summary["catalog_before41_ref"], lambda v: v.pop("command_ref"))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_command_ref"):
            self.run_reader()

    def test_catalog_summary_cannot_omit_originals(self):
        self.summary.pop("catalog_original_refs")
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_summary_originals"):
            self.run_reader()

    def test_catalog_summary_cannot_substitute_rehashed_reference(self):
        self.summary["catalog_original_refs"]["command"] = self.save("other-command.json", dict(phase="migration_41", exitcode=0))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_summary_originals"):
            self.run_reader()

    def test_catalog_reservation_alias_denied_even_with_same_content(self):
        ref = self.summary["catalog_before41_ref"]
        reserve = self.save("other-reserve.json", dict(commands=["catalog"], reserved=1))
        self.mutate(ref, lambda v: v.update(reservation_ref=reserve))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_reservation_name"):
            self.run_reader()

    def test_cross_case_preregister_same_commit_candidate_denied(self):
        ref = self.summary["invocations"][0]["original_refs"]["preregister"]
        self.mutate(ref, lambda v: v.update(run_id=str(uuid.uuid4())))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "invocation_source_binding"):
            self.run_reader()

    def test_cross_ci_final_receipt_denied(self):
        ref = self.summary["invocations"][0]["original_refs"]["receipt"]
        self.mutate(ref, lambda v: v.update(ci_run="124"))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "invocation_source_binding"):
            self.run_reader()

    def test_cross_case_policy_cannot_be_rebound_in_receipts(self):
        refs = self.summary["invocations"][0]["original_refs"]
        self.mutate(refs["policy"], lambda v: v.update(run_id=str(uuid.uuid4())))
        policy = json.loads((self.out / refs["policy"]["path"]).read_bytes())
        for name in ("receipt", "preregister"):
            self.mutate(refs[name], lambda v: v.update(policy=policy))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "invocation_state"):
            self.run_reader()

    def test_cross_case_raw_ledger_header_denied_even_after_rehash(self):
        refs = self.summary["invocations"][0]["original_refs"]
        self.mutate(refs["ledger"], lambda v: v.update(run_id=str(uuid.uuid4())))
        self.mutate(refs["receipt"], lambda v: v.update(ledger_ref={k: refs["ledger"][k]
                                                               for k in ("path", "sha256")}))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "ledger_header_identity"):
            self.run_reader()

    def test_cross_ci_ledger_header_denied(self):
        ref = self.summary["invocations"][0]["original_refs"]["ledger"]
        self.mutate(ref, lambda v: v.update(ci_run="124"))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "ledger_header_identity"):
            self.run_reader()

    def test_cross_case_provision_receipt_denied(self):
        self.mutate(self.summary["history_provision_refs"][0], lambda v: v.update(run_id=str(uuid.uuid4())))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "provision_state"):
            self.run_reader()

    def test_cross_case_provision_reserve_denied(self):
        self.mutate(self.summary["history_provision_refs"][1], lambda v: v.update(run_id=str(uuid.uuid4())))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "provision_state"):
            self.run_reader()


    def test_catalog_raw_exit_failure_denied(self):
        catalog = json.loads((self.out / "case-stack-catalog-before41.json").read_bytes())
        self.mutate(catalog["command_ref"], lambda v: v.update(exitcode=1))
        self.summary["catalog_before41_ref"] = self.save("case-stack-catalog-before41.json", catalog)
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_command_failure"):
            self.run_reader()

    def test_catalog_nonconsecutive_command_order_denied(self):
        self.mutate(self.summary["catalog_before41_ref"], lambda v: v.update(command_serial_after=11))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_order"):
            self.run_reader()

    def test_catalog_wrong_sql_identity_denied(self):
        self.mutate(self.summary["catalog_before41_ref"], lambda v: v.update(sql_sha256="d"*64))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "catalog_witness"):
            self.run_reader()

    def test_changed_preregistration_cannot_hide_behind_final_complete(self):
        ref = self.summary["invocations"][0]["original_refs"]["preregister"]
        self.mutate(ref, lambda v: v.update(complete=True))
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "invocation_state"):
            self.run_reader()

    def test_duplicate_invocation_identity_denied(self):
        self.summary["invocations"][1]["invocation_id"] = self.summary["invocations"][0]["invocation_id"]
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "invocation_identity"):
            self.run_reader()

    def test_boolean_ordinal_denied(self):
        self.summary["invocations"][0]["ordinal"] = True
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "migration_order"):
            self.run_reader()

    def test_unreferenced_missing_provision_confirmation_denied(self):
        self.summary["history_provision_refs"].pop()
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "provision_ref_count"):
            self.run_reader()

    def test_forged_numeric_total_denied(self):
        self.summary["total_sql_commands"] = 2256
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "summary_not_numeric_authority"):
            self.run_reader()

    def test_preparation_uuid_is_not_case_identity(self):
        self.binding["run_id"] = "11a909f4-7113-424a-aa4b-ce9964720a3e"
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "fresh_case"):
            self.run_reader()

    def test_original_bytes_changed_denied(self):
        path = self.out / self.summary["invocations"][0]["original_refs"]["ledger"]["path"]
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(audit.prefix.PrefixBlocked, "ref_changed"):
            self.run_reader()


class CurrentSourceContractTests(unittest.TestCase):
    def test_reserved_uuid_source_guards_precede_case_binding(self):
        from test_admission_budget_recovery_program import ROOT
        reserved = ("6f8c8909-9b79-4011-a9d1-db5e23c6b6c1", "11a909f4-7113-424a-aa4b-ce9964720a3e")
        for name, method_name, code in ((audit.prefix.BOOTSTRAP, "bootstrap", "case_stack_run_id"),
                                       (audit.prefix.PREFIX_PRODUCER, "plan", "case_run_id")):
            with self.subTest(source=name):
                raw = (ROOT / name).read_bytes()
                self.assertTrue(audit.prefix.reviewed_raw_matches(ROOT, name, raw, audit.CURRENT_PINS[name]))
                method = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == method_name)
                guard = next(n for n in ast.walk(method) if isinstance(n, ast.Call)
                             and isinstance(n.func, ast.Name) and n.func.id == "require"
                             and len(n.args) == 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == code)
                self.assertIsInstance(guard.args[0], ast.BoolOp)
                self.assertIsInstance(guard.args[0].op, ast.And)
                exclusion = next(n for n in guard.args[0].values if isinstance(n, ast.Compare)
                                 and isinstance(n.left, ast.Name) and n.left.id == "run_id"
                                 and len(n.ops) == 1 and isinstance(n.ops[0], ast.NotIn))
                self.assertEqual(ast.literal_eval(exclusion.comparators[0]), reserved)
                if method_name == "bootstrap":
                    source_calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
                                    and isinstance(n.func, ast.Name) and n.func.id in ("_dependencies", "_source")]
                    self.assertEqual(len(source_calls), 2)
                    self.assertTrue(all(guard.lineno < n.lineno for n in source_calls))
                    binding = next(n for n in ast.walk(method) if isinstance(n, ast.Assign)
                                   and any(isinstance(t, ast.Attribute) and t.attr == "_case_stack_run_id" for t in n.targets))
                else:
                    binding = next(n for n in ast.walk(method) if isinstance(n, ast.Return))
                self.assertLess(guard.lineno, binding.lineno)

    def test_actual_producer_source_pin_and_wrapped_catalog_query(self):
        from test_admission_budget_recovery_program import ROOT
        candidate = dict(sources={})
        for relative in ("case_stack_v1/bootstrap.py", "case_stack_v1/prefix_receipt.py",
                         "cli_predispatch/prefix.py", "cli_predispatch/pending.py", "cli_predispatch/ci.py",
                         "cli_predispatch/hook.cjs", "cli_predispatch/entry.mjs", "cli_predispatch/policy.cjs",
                         "assembly_checks/byte_pairs_20261111.json"):
            name = audit.prefix.PREFIX + relative
            candidate["sources"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        raw, hashes, catalog_sha, setup = audit._source_contract(ROOT, candidate)
        self.assertEqual(hashes, {p:h for p,h in candidate["sources"].items()
                                  if p != audit.prefix.REVIEWED_BYTE_PAIRS})
        self.assertEqual(hashlib.sha256(raw[audit.prefix.REVIEWED_BYTE_PAIRS]).hexdigest(),
                         candidate["sources"][audit.prefix.REVIEWED_BYTE_PAIRS])
        self.assertEqual(len(catalog_sha), 64)
        self.assertEqual(len(setup), 7)
        program = audit.prefix.source_program(ROOT)
        self.assertTrue(program["canonical_originals_producer"])
        pre = program["cases"]["pre_migration"]
        self.assertEqual(pre["prefix"][1]["command_id"], "bootstrap.history.provision")
        self.assertEqual(pre["source_known_explicit_sql_excluding_cli"], 19)
        self.assertIsNone(pre["complete_upper_bound"])


if __name__ == "__main__":
    unittest.main()
