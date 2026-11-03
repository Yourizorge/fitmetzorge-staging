"""Offline packaging and concrete graph checks, no real transport execution."""
import copy
import base64
import io
import pathlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import admission_budget as budget
import admission_budget_receipts as receipts
import admission_budget_register as register


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = register.assemble()
        cls.members = receipts.package(cls.report)
        cls.index = cls.members[receipts.INDEX]

    def test_complete_roundtrip_no_truncation(self):
        recovered = receipts.verify(self.index, self.members.__getitem__)
        self.assertEqual(recovered, self.report)
        self.assertEqual(self.index["full_register_sha256"], register.canonical_sha(self.report))

    def normal_records(self):
        """Synthetic in-memory receipt shapes, never actual CI evidence."""
        from complete_register import AUTH_CALLS
        streams = {}
        by_id = {r["id"]: r for r in self.report["normal_register"]["rows"]}
        for mapped in self.report["normal_dispatch_mapping"]["rows"]:
            streams.setdefault(mapped["stream"], []).append(by_id[mapped["row_id"]])
        records = {"endchain-sources.json": {"sources": {
            (name if name.startswith("_offline/") else "_offline/phase6e11/endchain_v1/" + name): digest
            for name, digest in self.report["source_hashes"].items()}},
            "integral-complete-protocol-trace.json": {"commands": [dict(command=i + 1,
                phase=r["action"], action=copy.deepcopy(r.get("action_binding", {})),
                sql_sha256=r["sql_sha256"], confirmed=True)
                for i, r in enumerate(streams["integral_complete_protocol_trace"])]},
            "integral-preflight.json": {"commands": [dict(sql_sha256=r["sql_sha256"], confirmed=True)
                for r in streams["integral_preflight"]]}}
        def numeric(n):
            return dict(commands=n, temp_written=0, statements=[dict(queryid="1", calls=n, temp_written=0, temp_read=0)])
        events = []
        for r in streams["workflow_auth_protocol"] + streams["auth_protocol_operation"]:
            events.append(dict(number=len(events) + 1, action=r["action"], phase=r["phase"],
                commands=r["cost"], kind="managed_auth", confirmed=True))
        events.append(dict(number=len(events) + 1, action="lifecycle_reader_begin", commands=1, kind="native"))
        records["runtime-command-meter.json"] = dict(events=events)
        records["workflow-auth-protocol.json"] = dict(numeric(360), verified_calls=72)
        for i, r in enumerate(streams["auth_protocol_operation"]):
            operation = next(op for op in AUTH_CALLS if r["action"].endswith("_" + op))
            role = r["action"][len("gotrue_"):-len(operation) - 1]
            records["auth-protocol-%02d.json" % i] = dict(numeric(r["cost"]), role=role, operation=operation)
        for i, (slot, cap) in enumerate((("quota", 64), ("pre_auth", 28), ("final", 28))):
            records["cli-protocol-%d.json" % i] = dict(slot=slot, capacity_reserved=cap, charged_commands=cap + 8,
                complete=True, dry_run=slot != "quota", environment="disposable_ci", protocol_commands=7,
                numeric_protocol_coverage=True, observer_commands=[dict(confirmed=True) for _ in range(8)])
            records["cli-numeric-coverage-%d.json" % i] = dict(numeric_calls_minus_reader=7,
                all_protocol_visible=True, temp_written=0)
        return records

    def test_exact_native_and_preflight_reconciliation_has_real_rows_not_a_total(self):
        result = receipts.reconcile_normal(self.report, self.normal_records())
        self.assertEqual(result["native"]["matched_count"], 1524)
        self.assertEqual(result["preflight"]["matched_count"], 4)
        self.assertTrue(result["native"]["ordered_complete"])
        self.assertEqual(len(result["native"]["rows"]), 1524)
        self.assertTrue(result["current_source_subset_matches"])
        self.assertEqual(result["optional_stream_capacity"], 72)
        self.assertFalse(result["full_bound_proven"])
        self.assertIsNone(result["minimal_cap"])

    def test_native_mutation_duplicate_and_order_drift_are_not_accepted(self):
        for mutation in (lambda x: x[5].update(sql_sha256="0" * 64),
                         lambda x: x.insert(5, copy.deepcopy(x[5])), lambda x: x.reverse(),
                         lambda x: x[5].update(confirmed=False)):
            records = self.normal_records()
            mutation(records["integral-complete-protocol-trace.json"]["commands"])
            result = receipts.reconcile_normal(self.report, records)
            self.assertFalse(result["native"]["ordered_complete"])
        records = self.normal_records()
        records["integral-preflight.json"]["commands"][0]["confirmed"] = False
        self.assertFalse(receipts.reconcile_normal(self.report, records)["preflight"]["ordered_complete"])

    def test_moved_commands_are_identified_without_accepting_changed_order(self):
        expected = [dict(id="a", action="first", sql_sha256="a", action_binding={}),
                    dict(id="b", action="second", sql_sha256="b", action_binding={})]
        actual = [dict(command=1, phase="second", sql_sha256="b", confirmed=True),
                  dict(command=2, phase="first", sql_sha256="a", confirmed=True)]
        result = receipts._ordered_trace(expected, actual)
        self.assertEqual(result["matched_count"], 1)
        self.assertEqual(result["moved_count"], 1)
        self.assertFalse(result["ordered_complete"])
        self.assertEqual(result["unexpected"], [])

    def test_receipt_match_and_current_source_match_are_independent(self):
        records = self.normal_records()
        records["endchain-sources.json"]["sources"]["_offline/phase6e11/endchain_v1/integral_ci.py"] = "0" * 64
        result = receipts.reconcile_normal(self.report, records)
        self.assertEqual(result["native"]["matched_count"], 1524)
        self.assertFalse(result["source_bindings"]["native"]["all_match"])
        self.assertFalse(result["current_source_subset_matches"])
        historical = receipts.reconcile_normal(self.report, self.normal_records(), historical=True)
        self.assertFalse(historical["current_source_subset_matches"])
        self.assertTrue(historical["historical_read_only_reference"])

    def test_360_aggregate_never_creates_72_user_dispatches(self):
        result = receipts.reconcile_normal(self.report, self.normal_records())["workflow"]
        self.assertEqual(result["matched_tickets"], 72)
        self.assertTrue(result["upfront_order_matches"])
        self.assertTrue(result["aggregate_numeric_matches"])
        self.assertEqual(result["dispatches_joined"], 0)
        self.assertTrue(all(r["per_call_managed_sql_observed"] is None for r in result["rows"]))

    def test_user_dispatch_join_requires_exact_unique_action_ticket_and_terminal(self):
        records = self.normal_records()
        initial = receipts.reconcile_normal(self.report, records)["workflow"]["rows"]
        dispatches = [dict(action=r["action"], ticket_number=r["ticket_number"], method="GET", path="/user",
                           confirmed=True, unknown_consumed=0) for r in initial]
        result = receipts.reconcile_normal(self.report, records, workflow_dispatches=dispatches)["workflow"]
        self.assertEqual(result["dispatches_joined"], 72)
        self.assertFalse(result["per_call_managed_bound_proven"])
        dispatches[1] = copy.deepcopy(dispatches[0])
        self.assertEqual(receipts.reconcile_normal(self.report, records,
            workflow_dispatches=dispatches)["workflow"]["dispatches_joined"], 71)
        dispatches[0]["unknown_consumed"] = True
        self.assertEqual(receipts.reconcile_normal(self.report, records,
            workflow_dispatches=dispatches)["workflow"]["dispatches_joined"], 70)

    def test_duplicate_late_and_unknown_user_tickets_do_not_receive_refunds(self):
        records = self.normal_records()
        events = records["runtime-command-meter.json"]["events"]
        events[0]["confirmed"] = False
        result = receipts.reconcile_normal(self.report, records)["workflow"]
        self.assertEqual(result["rows"][0]["consumed_capacity"], 5)
        self.assertFalse(result["rows"][0]["confirmed"])
        events.append(dict(events[1], number=len(events) + 1))
        self.assertEqual(receipts.reconcile_normal(self.report, records)["workflow"]["matched_tickets"], 71)
        records = self.normal_records()
        records["runtime-command-meter.json"]["events"][0]["action"] = "lifecycle_reader_begin"
        self.assertFalse(receipts.reconcile_normal(self.report, records)["workflow"]["upfront_order_matches"])

    def test_eighteen_auth_receipts_bind_role_operation_numeric_and_ticket(self):
        records = self.normal_records()
        result = receipts.reconcile_normal(self.report, records)["auth"]
        self.assertEqual(len(result), 18)
        self.assertTrue(all(r["numeric_matches"] and r["ticket_matches"] for r in result))
        for field, value in (("role", "foreign"), ("commands", True), ("temp_written", 1)):
            changed = copy.deepcopy(records)
            changed["auth-protocol-00.json"][field] = value
            self.assertFalse(receipts.reconcile_normal(self.report, changed)["auth"][0]["numeric_matches"])
        records["auth-protocol-00.json"]["statements"][0]["calls"] -= 1
        self.assertFalse(receipts.reconcile_normal(self.report, records)["auth"][0]["numeric_matches"])

    def test_cli_slots_join_reservations_without_spending_capacity_as_actual(self):
        records = self.normal_records()
        cli = receipts.reconcile_normal(self.report, records)["cli"]
        self.assertEqual([r["reference_capacity"] for r in cli], [72, 36, 36])
        self.assertEqual([r["actual_protocol_commands"] for r in cli], [7, 7, 7])
        self.assertTrue(all(r["reservation_matches"] and r["numeric_matches"] for r in cli))
        records["cli-protocol-2.json"]["slot"] = "app_2"
        self.assertFalse(receipts.reconcile_normal(self.report, records)["cli"][2]["reservation_matches"])
        del records["cli-numeric-coverage-1.json"]
        self.assertFalse(receipts.reconcile_normal(self.report, records)["cli"][1]["numeric_matches"])

    def test_missing_all_receipts_is_honest_and_does_not_infer_zero_actual_cost(self):
        result = receipts.reconcile_normal(self.report, {})
        self.assertEqual(result["native"]["matched_count"], 0)
        for component in ("native", "preflight"):
            self.assertIsNone(result[component]["actual_count"])
            self.assertFalse(result[component]["receipt_present"])
        self.assertFalse(result["native"]["ordered_complete"])
        self.assertEqual(result["workflow"]["matched_tickets"], 0)
        self.assertTrue(all(r["consumed_capacity"] is None for r in result["workflow"]["rows"]))
        self.assertTrue(all(r["actual_protocol_commands"] is None for r in result["cli"]))
        self.assertFalse(result["current_source_subset_matches"])

    def test_current_plan_unbound_removal_cannot_match_null_or_old_receipt_hash(self):
        plan = self.report["current_plan"]
        expected = [r for r in plan["normal"]["rows"] if r.get("binding_required")]
        actual = [dict(phase="remove", action=r["action_binding"], sql_sha256=None, confirmed=True) for r in expected]
        result = receipts._ordered_trace(expected, actual)
        self.assertEqual(result["matched_count"], 0)
        self.assertTrue(all(r["status"] == "BINDING_REQUIRED" for r in result["rows"]))

    def test_current_folder_api_retains_missing_evidence_and_checks_plan_digest(self):
        with patch.object(pathlib.Path, "is_file", return_value=False):
            result = receipts.reconcile_current_folder(self.report, pathlib.Path("memory"))
        self.assertEqual(result["plan_version"], register.PLAN_VERSION)
        self.assertEqual(result["source_derived_rows"], 30)
        self.assertEqual(len(result["unbound_normal_rows"]), 2)
        self.assertEqual(result["recovery_setup_reservation"], 1)
        self.assertIsNone(result["native"]["actual_count"])
        self.assertFalse(result["full_bound_proven"])
        changed = copy.deepcopy(self.report["current_plan"])
        changed["normal"]["rows"][0]["cost"] += 1
        with self.assertRaisesRegex(ValueError, "current_plan_binding"):
            receipts.reconcile_current_folder(self.report, pathlib.Path("memory"), plan=changed)

    def test_verified_migration_component_keeps_incomplete_terminal(self):
        result = receipts.migration_boundary_receipt(dict(component_verified=True,
            terminal_complete=False, execution_status="NO_GO"), dict(path="migration-boundary-post.json"))
        self.assertTrue(result["component_verified"])
        self.assertFalse(result["terminal_complete"])
        self.assertEqual(result["execution_status"], "NO_GO")
        self.assertFalse(result["full_hosted_bound_proven"])

    def test_new_cleanup_receipt_keeps_diagnostic_counts_without_parent_pass(self):
        values = dict(status="NO_GO", classification="REGISTRY_CLOSED_WITH_ORIGINAL_COMMIT_UNKNOWN",
                      protocol_limit=41, admitted_attempts=40, registry_deletion_proven=True,
                      original_commit_reclassified=False)
        with patch.object(pathlib.Path, "is_file", lambda p:p.name == "fixture-parent-physical-zero.json"), \
             patch.object(receipts, "_read", return_value=(values,"a"*64)):
            result = receipts.actual_receipts(pathlib.Path("memory"))
        actual = result["physical_suffix"]
        self.assertEqual(actual["actual_counts"]["admitted_attempts"], 40)
        self.assertTrue(actual["registry_deletion_proven"])
        self.assertFalse(actual["original_commit_reclassified"])
        self.assertFalse(actual["changes_hosted_bound"])
        self.assertIsNone(result["parent_auth_finalizer"]["actual_counts"])

    def test_folder_reconciliation_rejects_changed_artifact_before_join(self):
        with patch.object(pathlib.Path, "is_file", lambda p:p.name in (
                "artifact-manifest.json", "integral-preflight.json")), \
             patch.object(receipts, "_read", side_effect=[({"integral-preflight.json":"0"*64}, "f"*64),
                                                        ({"commands":[]}, "1"*64)]):
            with self.assertRaisesRegex(ValueError, "budget_reconcile_artifact_hash"):
                receipts.reconcile_folder(self.report, pathlib.Path("memory"))

    def test_every_member_bounded_and_total_under_fifty(self):
        self.assertLessEqual(len(self.members), 50)
        self.assertTrue(all(len(receipts.raw(value)) < 2000000 for value in self.members.values()))
        self.assertGreater(self.index["raw_bytes"], 2000000)
        self.assertFalse(self.index["parent_artifact_cap_changed"])

    def test_corrupted_chunk_rejected(self):
        members = copy.deepcopy(self.members)
        members["admission-budget-chunk-001.json"]["base64"] = "AA=="
        with self.assertRaises(ValueError):
            receipts.verify(self.index, members.__getitem__)

    def test_reordered_or_missing_chunk_rejected(self):
        for operation in (lambda x: x["chunks"].reverse(), lambda x: x["chunks"].pop()):
            index = copy.deepcopy(self.index)
            operation(index)
            with self.assertRaises(ValueError):
                receipts.verify(index, self.members.__getitem__)

    def test_oversized_package_rejected_not_truncated(self):
        with patch.object(receipts, "MAX_FILES", 2):
            with self.assertRaisesRegex(ValueError, "not_truncated"):
                receipts.package(self.report)

    def test_parent_callable_emits_no_go_and_full_payload(self):
        saved = {}
        gate = SimpleNamespace(out=pathlib.Path("absent-budget-test-output"), save=lambda n, v: saved.__setitem__(n, v))
        with patch.object(receipts, "assemble", return_value=copy.deepcopy(self.report)):
            result = budget.run(gate)
        full = receipts.verify(result, saved.__getitem__)
        self.assertEqual(result["status"], "NO_GO_INCOMPLETE_BOUND")
        self.assertTrue(all(r["status"] == "PENDING_NAMED_RECEIPT"
                            for r in full["actual_component_evidence"].values()))
        self.assertEqual(len(full["normal_register"]["rows"]), 1717)
        self.assertIsNone(full["minimal_cap"])

    def test_existing_receipt_is_never_overwritten(self):
        saved = []
        gate = SimpleNamespace(out=pathlib.Path("memory"), save=lambda n, v: saved.append(n))
        with patch.object(receipts, "assemble", return_value=self.report), \
             patch.object(receipts, "actual_receipts", return_value={}), \
             patch.object(pathlib.Path, "exists", return_value=True):
            with self.assertRaisesRegex(ValueError, "preserved"):
                budget.run(gate)
        self.assertEqual(saved, [])

    def test_named_actual_receipts_replace_pending_counts_only(self):
        auth = {"status": "LOCAL_AUTH_FAILURE_COMPONENT_PASS", "preparation_run_id": register.NEW_RUN,
                "diagnostic_totals": {"native_sql_dispatched": 95, "reserved": 5764},
                "source_sha256": {"auth_failure.py": "memory-only-test"}}
        with patch.object(pathlib.Path, "is_file", lambda p: p.name == "admission-auth-auth-failure-component.json"), \
             patch.object(receipts, "_read", return_value=(auth, "a" * 64)):
            actual = receipts.actual_receipts(pathlib.Path("memory"))
        self.assertEqual(actual["auth"]["actual_counts"]["reserved"], 5764)
        self.assertFalse(actual["auth"]["changes_hosted_bound"])
        self.assertEqual(actual["fixture"]["status"], "PENDING_NAMED_RECEIPT")

    def cli_evidence(self, value):
        with patch.object(pathlib.Path, "is_file", lambda p: p.name == "cli-predispatch.json"), \
             patch.object(receipts, "_read", return_value=(value, "b" * 64)):
            return receipts.actual_receipts(pathlib.Path("memory"))["cli_predispatch"]

    def test_cli_dry_run_counts_never_prove_actual_migration_or_hosted_bound(self):
        evidence = self.cli_evidence({"scope": "DISPOSABLE_CI_ONLY", "hosted_admission": False,
            "complete": True, "actual_empty_dry_run": True, "actual_migration_execution": False,
            "header": {"slot": "final", "cap": 28}, "terminal_recorded": True,
            "terminal": {"complete": True, "sql_dispatches": 7, "confirmed_sql": 7, "unknown_consumed": 0},
            "observer_commands": 8, "ci_bootstrap_sql_commands": 4,
            "build": {"hook_sources": {"hook.cjs": self.report["source_hashes"]["cli_predispatch/hook.cjs"]}}})
        self.assertEqual(evidence["actual_counts"]["sql_dispatches"], 7)
        self.assertEqual(evidence["actual_counts"]["observer_commands"], 8)
        self.assertEqual(evidence["actual_counts"]["ci_bootstrap_sql_commands"], 4)
        self.assertEqual(evidence["migration_evidence_status"], "PENDING_ACTUAL_MIGRATION_EVIDENCE")
        self.assertEqual(evidence["source_hashes"], {"cli_predispatch/hook.cjs": self.report["source_hashes"]["cli_predispatch/hook.cjs"]})
        self.assertFalse(evidence["changes_hosted_bound"])
        self.assertFalse(evidence["full_hosted_bound_proven"])

    def test_cli_failure_prefix_keeps_full_consumed_reservation_and_unknowns(self):
        evidence = self.cli_evidence({"complete": False, "reserved_sql_consumed_on_failure": 28,
            "failure_ledger": {"header": {"cap": 28, "slot": "final"}, "terminal_recorded": False,
                "terminal": {"complete": False, "sql_dispatches": 3, "confirmed_sql": 2, "unknown_consumed": 1}}})
        self.assertEqual(evidence["status"], "NO_GO_CLI_COMPONENT")
        self.assertEqual(evidence["ledger_scope"], "failure_prefix")
        self.assertEqual(evidence["actual_counts"]["reserved_sql_consumed_on_failure"], 28)
        self.assertEqual(evidence["actual_counts"]["unknown_consumed"], 1)
        self.assertFalse(evidence["terminal_recorded"])
        self.assertIsNone(evidence["actual_counts"]["observer_commands"])

    def test_cli_missing_receipt_and_missing_counters_remain_unknown_not_zero(self):
        with patch.object(pathlib.Path, "is_file", return_value=False):
            missing = receipts.actual_receipts(pathlib.Path("memory"))["cli_predispatch"]
        self.assertEqual(missing, {"status": "PENDING_NAMED_RECEIPT", "actual_counts": None})
        evidence = self.cli_evidence({"complete": False, "failure_ledger_unverifiable": True})
        self.assertIsNone(evidence["actual_counts"]["sql_dispatches"])
        self.assertIsNone(evidence["actual_counts"]["unknown_consumed"])
        self.assertTrue(evidence["failure_ledger_unverifiable"])
        self.assertEqual(evidence["migration_evidence_status"], "PENDING_ACTUAL_MIGRATION_EVIDENCE")

    def canonical_inputs(self):
        raw = {"cli-predispatch-canonical-45.ledger.txt": b'{"event":"dispatch"}\r\n{"truncated":',
               "cli-predispatch-canonical-45.policy.json": b'{ "schema": 1 }\r\n',
               "canonical-45-cli-predispatch-cli-isolation-0.json": b'{"commands":8}'}
        refs = {name: dict(path=name, sha256=receipts.sha(data)) for name, data in raw.items()}
        value = dict(scope="DISPOSABLE_CI_ONLY", hosted_admission=False, complete=True,
            phase="migration_45", profile="canonical_45", actual_migration_execution=True,
            source_commit="a" * 40, candidate_sha256="b" * 64,
            header=dict(slot="quota", cap=64), observer_commands=8, ci_bootstrap_sql_commands=8,
            terminal=dict(sql_dispatches=12, confirmed_sql=12, unknown_consumed=0),
            numeric_coverage=dict(protocol_commands=12, numeric_calls_minus_reader=12,
                                  all_protocol_visible=True, temp_written=0),
            ledger_ref=refs["cli-predispatch-canonical-45.ledger.txt"],
            policy_ref=refs["cli-predispatch-canonical-45.policy.json"],
            isolation_receipt="canonical-45-cli-predispatch-cli-isolation-0.json",
            isolation_receipt_sha256=refs["canonical-45-cli-predispatch-cli-isolation-0.json"]["sha256"])
        post = dict(component_verified=True, actual_migration_result=dict(
            receipt="cli-predispatch-canonical-45.json", receipt_sha256="c" * 64,
            protocol_commands=12, observer_commands=8, isolation_commands=8,
            ledger_sha256=value["ledger_ref"]["sha256"], policy_file_sha256=value["policy_ref"]["sha256"],
            isolation_receipt_sha256=value["isolation_receipt_sha256"]))
        return value, post, raw

    def canonical_evidence(self, value, post, raw):
        files = {"cli-predispatch-canonical-45.json": (value, "c" * 64)}
        if post is not None:
            files["migration-boundary-post.json"] = (post, "d" * 64)

        def opened(path, *args, **kwargs):
            if path.name not in raw:
                raise FileNotFoundError(path.name)
            return io.BytesIO(raw[path.name])

        with patch.object(pathlib.Path, "is_file", lambda p: p.name in files), \
             patch.object(pathlib.Path, "is_symlink", return_value=False), \
             patch.object(pathlib.Path, "open", opened), \
             patch.object(receipts, "_read", lambda p: files[p.name]):
            return receipts.actual_receipts(pathlib.Path("memory"))

    def test_canonical_selection_binds_original_sidecars_and_post_confirmation(self):
        value, post, raw = self.canonical_inputs()
        result = self.canonical_evidence(value, post, raw)
        e = result["cli_canonical_45"]
        self.assertTrue(e["canonical_references_complete"])
        self.assertTrue(e["numeric_confirmation"]["counters_consistent"])
        self.assertTrue(e["boundary_confirmation"]["references_match"])
        self.assertTrue(all(r["verified"] and r["additional_sql"] == 0 for r in e["raw_references"].values()))
        self.assertEqual(e["raw_references"]["ledger"]["raw_bytes"], len(raw[value["ledger_ref"]["path"]]))
        self.assertEqual(e["additional_reference_charge"], 0)
        self.assertEqual(e["reference_capacity"], 72)
        self.assertEqual(e["actual_counts"]["sql_dispatches"], 12)
        self.assertEqual(result["cli_pending_0"]["status"], "PENDING_NAMED_RECEIPT")
        self.assertEqual(result["migration_boundary_post"]["actual_migration_result"]["ledger_sha256"],
                         value["ledger_ref"]["sha256"])
        self.assertFalse(e["full_hosted_bound_proven"])
        self.assertFalse(e["runtime_recovery_bound_complete"])

    def test_canonical_unknown_failure_keeps_consumed64_and_missing_sidecars(self):
        value = dict(complete=False, reserved_sql_consumed_on_failure=64,
                     failure_ledger=dict(header=dict(slot="quota", cap=64),
                         terminal=dict(sql_dispatches=3, confirmed_sql=2, unknown_consumed=1)))
        e = self.canonical_evidence(value, None, {})["cli_canonical_45"]
        self.assertFalse(e["canonical_references_complete"])
        self.assertEqual(e["status"], "NO_GO_CANONICAL_RECEIPT_INCOMPLETE")
        self.assertEqual(e["actual_counts"]["reserved_sql_consumed_on_failure"], 64)
        self.assertEqual(e["actual_counts"]["unknown_consumed"], 1)
        self.assertEqual(e["boundary_confirmation"]["status"], "PENDING_BOUNDARY_CONFIRMATION")

    def test_canonical_raw_bytes_are_not_reencoded_or_repaired(self):
        value, post, raw = self.canonical_inputs()
        raw[value["policy_ref"]["path"]] = b'{"schema":1}'
        e = self.canonical_evidence(value, post, raw)["cli_canonical_45"]
        self.assertEqual(e["raw_references"]["policy"]["status"], "HASH_MISMATCH")
        self.assertFalse(e["canonical_references_complete"])

    def test_canonical_missing_and_oversized_sidecars_remain_bounded_failures(self):
        for mode in ("missing", "oversized"):
            value, post, raw = self.canonical_inputs()
            name = value["ledger_ref"]["path"]
            if mode == "missing":
                del raw[name]
            else:
                raw[name] = b'x' * 262145
            e = self.canonical_evidence(value, post, raw)["cli_canonical_45"]
            self.assertEqual(e["raw_references"]["ledger"]["status"],
                             "UNAVAILABLE_REFERENCE" if mode == "missing" else "OVERSIZED_REFERENCE")
            self.assertFalse(e["canonical_references_complete"])

    def test_canonical_unsafe_reference_never_opens_another_path(self):
        for name in ("../ledger.txt", "C:/outside.txt", "cli-predispatch-canonical-45.policy.json"):
            with patch.object(pathlib.Path, "open", side_effect=AssertionError("must not read")):
                e = receipts.raw_reference(pathlib.Path("memory"), dict(path=name, sha256="a" * 64),
                                           "cli-predispatch-canonical-45.ledger.txt", 262144)
            self.assertEqual(e["status"], "INVALID_REFERENCE")

    def test_canonical_symlink_is_not_followed(self):
        with patch.object(pathlib.Path, "is_symlink", return_value=True), \
             patch.object(pathlib.Path, "open", side_effect=AssertionError("must not read")):
            e = receipts.raw_reference(pathlib.Path("memory"), dict(path="ledger", sha256="a" * 64), "ledger", 1)
        self.assertEqual(e["status"], "UNSAFE_REFERENCE")

    def test_canonical_wrong_numeric_or_post_reference_cannot_confirm(self):
        for mode in ("numeric", "post_hash", "unknown", "boolean_count", "missing_post"):
            value, post, raw = self.canonical_inputs()
            if mode == "numeric": value["numeric_coverage"]["numeric_calls_minus_reader"] = 11
            elif mode == "post_hash": post["actual_migration_result"]["receipt_sha256"] = "e" * 64
            elif mode == "unknown": value["terminal"]["unknown_consumed"] = 1
            elif mode == "boolean_count": value["terminal"]["sql_dispatches"] = True
            else: post = None
            e = self.canonical_evidence(value, post, raw)["cli_canonical_45"]
            self.assertFalse(e["canonical_references_complete"], mode)
            self.assertFalse(e["full_hosted_bound_proven"])

    def test_cli_future_migration_receipt_cannot_promote_full_bound(self):
        evidence = self.cli_evidence({"scope": "DISPOSABLE_CI_ONLY", "hosted_admission": False,
                                     "complete": True, "actual_migration_execution": True})
        self.assertEqual(evidence["migration_evidence_status"], "PARENT_REPORTS_EXECUTED_NOT_FULL_BOUND")
        self.assertFalse(evidence["full_hosted_bound_proven"])

    def test_cli_build_hook_names_cannot_expand_source_scope(self):
        with self.assertRaisesRegex(ValueError, "hook_source_names"):
            self.cli_evidence({"build": {"hook_sources": {"../outside": "a" * 64}}})

    def test_cli_dependency_hash_inventory_includes_current_canonical_and_fixture_sources(self):
        self.assertEqual(len(register.CLI_SOURCE_FILES), 16)
        for name in (*register.CLI_SOURCE_FILES, "cli_meter.py", "cli_stat_reader.py", "native_runtime.py",
                     "fixture_control_ownership.py", "test_fixture_control_ownership.py",
                     "fixture_parent_closure.py", "test_fixture_parent_closure.py",
                     "_offline/phase6e_server_v1/cli_isolation.py", "_offline/phase6e_server_v1/ci_profile.py"):
            self.assertRegex(self.report["source_hashes"][name], "^[a-f0-9]{64}$")

    def test_both_pending_cli_receipts_and_compatibility_views_not_double_counted(self):
        files = {}
        for index in (0, 2):
            target = "cli-predispatch-pending-" + str(index) + ".json"
            files[target] = {"scope": "DISPOSABLE_CI_ONLY", "hosted_admission": False,
                "complete": True, "actual_migration_execution": True, "app_index": index,
                "source_commit": "a" * 40, "candidate_sha256": "b" * 64,
                "header": {"slot": "quota", "cap": 64}, "observer_commands": 8,
                "terminal": {"sql_dispatches": 12, "unknown_consumed": 0}}
            files["cli-protocol-" + str(index) + ".json"] = {"instrumented_receipt": target,
                "protocol_commands": 12, "total_commands": 20, "complete": True,
                "source_commit": "a" * 40, "candidate_sha256": "b" * 64}
        with patch.object(pathlib.Path, "is_file", lambda p: p.name in files), \
             patch.object(receipts, "_read", lambda p: (files[p.name], "d" * 64)):
            result = receipts.actual_receipts(pathlib.Path("memory"))
        for index in (0, 2):
            evidence = result["cli_pending_" + str(index)]
            self.assertTrue(evidence["app_profile_index_matches"])
            self.assertEqual(evidence["reserved_cap"], 64)
            self.assertEqual(evidence["actual_counts"]["sql_dispatches"], 12)
            compatible = evidence["compatibility_receipt"]
            self.assertEqual(compatible["additional_charge"], 0)
            self.assertTrue(compatible["instrumented_receipt_matches"])
            self.assertTrue(compatible["source_commit_matches"])
            self.assertTrue(compatible["candidate_sha256_matches"])
            self.assertFalse(evidence["full_hosted_bound_proven"])

    def test_pending_migration_failure_retains_64_and_absent_post_is_pending(self):
        files = {"cli-predispatch-pending-0.json": {"complete": False, "app_index": 0,
            "reserved_sql_consumed_on_failure": 64, "failure_ledger_unverifiable": True}}
        with patch.object(pathlib.Path, "is_file", lambda p: p.name in files), \
             patch.object(receipts, "_read", lambda p: (files[p.name], "e" * 64)):
            result = receipts.actual_receipts(pathlib.Path("memory"))
        self.assertEqual(result["cli_pending_0"]["actual_counts"]["reserved_sql_consumed_on_failure"], 64)
        self.assertIsNone(result["cli_pending_0"]["actual_counts"]["sql_dispatches"])
        self.assertEqual(result["cli_pending_2"]["status"], "PENDING_NAMED_RECEIPT")

    def test_migration_boundary_pair_allowance_separate_from_hosted_counts(self):
        files = {"migration-boundary-claim.json": {"normal_diagnostic_sql_commands": 16,
            "maximum_diagnostic_sql_commands": 24}, "migration-boundary-pre.json": {
                "local_diagnostic_commands": 8, "command_limit": 12, "cleanup_reserve": 4,
                "execution_status": "NO_GO", "component_verified": True,
                "accounting_scope": "local_diagnostic_separate_from_planned_2349"},
            "migration-boundary-post.json": {"local_diagnostic_commands": 8, "command_limit": 12,
                "component_verified": True, "execution_status": "NO_GO"}}
        with patch.object(pathlib.Path, "is_file", lambda p: p.name in files), \
             patch.object(receipts, "_read", lambda p: (files[p.name], "f" * 64)):
            result = receipts.actual_receipts(pathlib.Path("memory"))
        self.assertEqual(result["migration_boundary_claim"]["declared_pair_allowances"],
            {"normal_diagnostic_sql_commands": 16, "maximum_diagnostic_sql_commands": 24})
        for phase in ("pre", "post"):
            evidence = result["migration_boundary_" + phase]
            self.assertEqual(evidence["actual_counts"]["local_diagnostic_commands"], 8)
            self.assertEqual(evidence["execution_status"], "NO_GO")
            self.assertFalse(evidence["changes_hosted_bound"])

    def test_cli_parent_candidate_and_commit_binding_without_changing_bound(self):
        saved = {}
        evidence = self.cli_evidence({"source_commit": "a" * 40, "candidate_sha256": "b" * 64,
            "build": {"hook_sources": {"hook.cjs": "0" * 64}}})
        gate = SimpleNamespace(out=pathlib.Path("absent-budget-test-output"),
            result={"commit": "a" * 40, "candidate_sha256": "c" * 64},
            save=lambda n, v: saved.__setitem__(n, v))
        with patch.object(receipts, "assemble", return_value=copy.deepcopy(self.report)), \
             patch.object(receipts, "actual_receipts", return_value={"cli_predispatch": evidence}):
            result = budget.run(gate)
        cli = result["actual_component_evidence"]["cli_predispatch"]
        self.assertTrue(cli["source_commit_matches_parent"])
        self.assertFalse(cli["candidate_sha256_matches_parent"])
        self.assertFalse(cli["source_hashes_match_current"])
        self.assertEqual(result["status"], "NO_GO_INCOMPLETE_BOUND")
        self.assertIsNone(result["minimal_cap"])

    def test_reference_allowlist_is_sixteen_named_readonly_files_not_bulk(self):
        self.assertEqual(len(receipts.REFERENCE_FILES), 16)
        self.assertEqual(len(set(receipts.REFERENCE_FILES)), 16)
        self.assertTrue(all("*" not in p for p in receipts.REFERENCE_FILES))

    def test_actual_fixture_detail_read_from_verified_lossless_journal(self):
        from admission_journal import raw, sha
        detail = {"status": "COMPONENT_PASS", "preparation_run": register.NEW_RUN,
                  "local_diagnostic_sql_count": 359, "local_setup_sql_count": 116,
                  "local_component_sql_count": 243, "counts_are_protocol_only_not_nested_sql_or_io": True}
        data = raw(detail)
        name = "fixture-cleanup-component-detail.json"
        chunk_name = "admission-fixture-journal-001.json"
        chunk = {"format": "fmz-lossless-journal-chunk-v1", "entries": {name: {
            "bytes": len(data), "sha256": sha(data), "base64": base64.b64encode(data).decode()}}}
        index = {"format": "fmz-lossless-journal-index-v1", "complete": True, "contents_omitted": False,
            "hosted_calls": 0, "records": {name: {"bytes": len(data), "sha256": sha(data)}},
            "chunks": {chunk_name: {"canonical_content_sha256": sha(raw(chunk)), "records": 1}},
            "record_count": 1, "raw_bytes": len(data)}
        inputs = {"admission-fixture-journal-index.json": index, chunk_name: chunk}
        with patch.object(pathlib.Path, "is_file", lambda p: p.name in inputs), \
             patch.object(receipts, "_read", lambda p: (inputs[p.name], sha(raw(inputs[p.name])))):
            evidence = receipts.actual_receipts(pathlib.Path("memory"))["fixture"]
        self.assertEqual(evidence["actual_counts"]["local_diagnostic_sql_count"], 359)
        self.assertEqual(evidence["receipt"]["sha256"], sha(data))
        self.assertEqual(evidence["receipt"]["journal_index"], "admission-fixture-journal-index.json")

    def test_concrete_normal_graph_charges_2338_and_ends_at_gap(self):
        graph = self.report["command_graph"]
        current, consumed, visited = graph["entry"], 0, []
        while current != "normal_bound_gap":
            self.assertNotIn(current, visited)
            visited.append(current)
            node = graph["nodes"][current]
            edge = node["next"]["confirmed"]
            consumed += edge["charge"]
            self.assertEqual(consumed, edge["consumed_capacity"])
            current = edge["to"]
        self.assertEqual(consumed, 2338)
        self.assertEqual(sum(graph["nodes"][n]["stage"] == "normal" for n in visited), 1717)
        self.assertEqual(sum(graph["nodes"][n]["stage"] == "precharge" for n in visited),
                         len(self.report["normal_register"]["charge_groups"]))
        self.assertEqual(sum(graph["nodes"][n]["stage"] == "validation" for n in visited), 2)
        self.assertIsNone(graph["nodes"][current]["cost"])
        self.assertEqual(graph["closing_reserve"], 731)

    def test_every_normal_fault_edge_stops_at_explicit_unbounded_recovery(self):
        graph = self.report["command_graph"]
        for node in graph["nodes"].values():
            if node["stage"] not in ("normal", "precharge", "validation"):
                continue
            for outcome in node["next"]:
                if outcome == "confirmed":
                    continue
                edge = node["next"][outcome]
                target = graph["nodes"][edge["to"]]
                self.assertEqual(target["stage"], "unresolved")
                self.assertIsNone(target["cost"])
                self.assertEqual(target["next"]["blocked"]["to"], "NO_GO")
                self.assertEqual(edge["refunds"], 0)

    def test_auth_524_diagnostic_reservation_never_replaces_hosted_costs(self):
        auth = self.report["components"]["auth"]
        self.assertEqual(auth["diagnostic_contract"]["reserved_units"], 524)
        self.assertEqual(auth["diagnostic_reserved_all_cases"], 5764)
        self.assertEqual(auth["diagnostic_intended_prepaid_consumed"], 3551)
        self.assertTrue(all(r["cost"] is None for r in auth["rows"] if r["kind"] == "auth_reserved"))
        graphs = self.report["command_graph"]["diagnostic_graphs"]
        self.assertEqual(sum(graphs["auth_" + p["case"]]["intended_consumed_capacity"]
                             for p in auth["diagnostic_paths"]), 3551)

    def test_bootstrap_ten_actual_source_dispatches_twelve_cap_separate(self):
        parent = self.report["components"]["parent_bootstrap"]
        self.assertEqual(parent["normal_native_dispatches"], 10)
        self.assertEqual(parent["diagnostic_cap"], 12)
        self.assertEqual(len(parent["failure_only"]), 1)
        self.assertFalse(parent["actual_execution_observed"])
        self.assertFalse(parent["hosted_run_capacity_changed"])
        actors = self.report["components"]["workflow"]["bootstrap"]
        self.assertEqual(actors["diagnostic_reserved_all_actors"], 1572)
        self.assertEqual(actors["diagnostic_intended_prepaid_all_actors"], 1182)
        self.assertTrue(actors["not_parent_fixture_bootstrap"])
        self.assertIsNone(actors["total_capacity"])

    def test_workflow_includes_new_barrier_and_controller_terminal_query(self):
        cases = {p["case"]: p for p in self.report["components"]["workflow"]["cases"]}
        for key in ("mid_route_a", "mid_route_b", "mid_restore", "duplicate", "partial_cleanup"):
            self.assertIn("workflow_fixture_barrier", [r["action"] for r in cases[key]["native_rows"]])
        for key in ("mid_controller", "closure_failure"):
            self.assertIn("controller_terminal_prefix", [r["action"] for r in cases[key]["native_rows"]])

    def test_graph_phase_export_marks_cross_phase_links(self):
        value = register.export(self.report, "graph", "auth")["content"]
        self.assertTrue(value["external_next_nodes"])
        self.assertTrue(all(n.get("phase") == "auth" for n in value["nodes"].values() if n["stage"] == "normal"))

    def test_fixture_diagnostic_includes_actual_writer_setup_and_fault_cleanup(self):
        component = self.report["components"]["fixture_diagnostic"]
        counts = {p["case"]: p["intended_native_commands"] for p in component["cases"]}
        self.assertEqual(counts, dict(full=42, partial=32, parent_only=30, dependent_without_workspace=31,
            zero=26, lost_writer_commit=42, missing_barrier=20, foreign_row=33, lost_commit=42,
            interrupted_delete=31, lock_timeout=31))
        self.assertEqual(component["intended_protocol_commands"], 364)
        self.assertFalse(component["includes_parent_bootstrap"])
        self.assertIsNone(component["full_bound"])

    def test_fresh_argument_generation_does_not_make_receipt_identity_nondeterministic(self):
        first = register.fixture_diagnostic_component(self.report["components"]["fixture"])
        second = register.fixture_diagnostic_component(self.report["components"]["fixture"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
