"""Offline packaging and concrete graph checks, no real transport execution."""
import copy
import base64
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

    def test_cli_future_migration_receipt_cannot_promote_full_bound(self):
        evidence = self.cli_evidence({"scope": "DISPOSABLE_CI_ONLY", "hosted_admission": False,
                                     "complete": True, "actual_migration_execution": True})
        self.assertEqual(evidence["migration_evidence_status"], "PARENT_REPORTS_EXECUTED_NOT_FULL_BOUND")
        self.assertFalse(evidence["full_hosted_bound_proven"])

    def test_cli_build_hook_names_cannot_expand_source_scope(self):
        with self.assertRaisesRegex(ValueError, "hook_source_names"):
            self.cli_evidence({"build": {"hook_sources": {"../outside": "a" * 64}}})

    def test_cli_dependency_hash_inventory_includes_all_fifteen_sources(self):
        self.assertEqual(len(register.CLI_SOURCE_FILES), 15)
        for name in (*register.CLI_SOURCE_FILES, "cli_meter.py", "cli_stat_reader.py", "native_runtime.py",
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
        self.assertEqual(len(visited), 1717)
        self.assertIsNone(graph["nodes"][current]["cost"])
        self.assertEqual(graph["closing_reserve"], 731)

    def test_every_normal_fault_edge_stops_at_explicit_unbounded_recovery(self):
        graph = self.report["command_graph"]
        for node in graph["nodes"].values():
            if node["stage"] != "normal":
                continue
            for outcome in budget.OUTCOMES:
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
            zero=26, lost_writer_commit=42, missing_barrier=20, foreign_row=28, lost_commit=42,
            interrupted_delete=31, lock_timeout=31))
        self.assertEqual(component["intended_protocol_commands"], 359)
        self.assertFalse(component["includes_parent_bootstrap"])
        self.assertIsNone(component["full_bound"])

    def test_fresh_argument_generation_does_not_make_receipt_identity_nondeterministic(self):
        first = register.fixture_diagnostic_component(self.report["components"]["fixture"])
        second = register.fixture_diagnostic_component(self.report["components"]["fixture"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
