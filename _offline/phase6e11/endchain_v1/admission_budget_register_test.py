"""Concrete assembly tests, not database or real Auth evidence."""
import copy
import unittest
import uuid
from unittest.mock import patch

import admission_budget_register as register
from admission_budget import PHASE_BUDGETS


class ConcreteRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = register.assemble()
        cls.normal = cls.report["normal_register"]
        cls.rows = cls.normal["rows"]

    def test_all_2338_retained_capacity_rows_accounted_once(self):
        ids = [i for row in self.rows for i in row["retained_ids"]]
        for replacement in self.normal["replacements"]:
            ids += replacement.get("retained_ids", [])
        self.assertEqual(sorted(ids), ["cmd_%05d" % i for i in range(1, 2339)])

    def test_current_phases_reconcile_without_rewriting_historical_totals(self):
        self.assertEqual(self.normal["phase_capacities"], PHASE_BUDGETS)
        self.assertEqual(self.normal["reference"]["historical_closing"], 767)
        self.assertEqual(sum(PHASE_BUDGETS[p] for p in ("cleanup", "final", "closure")), 731)
        self.assertEqual(self.normal["normal_capacity"], 2338)

    def test_each_cli_observer_is_separate_from_unknown_reserve(self):
        self.assertEqual(self.normal["kind_capacities"],
                         dict(native=1600, observer=24, cli_reserved=120, auth_reserved=594))
        reserves = [r for r in self.rows if r["kind"] == "cli_reserved"]
        self.assertEqual([(r["id"], r["cost"]) for r in reserves],
                         [("cli_quota_reserved", 64), ("cli_pre_auth_reserved", 28),
                          ("cli_final_reserved", 28)])
        self.assertTrue(all(not r["execution_ready"] for r in reserves))

    def test_cli_whole_envelope_is_consumed_on_first_unknown_observer(self):
        prefixes = self.report["fault_prefixes"]
        before = next(p for p in prefixes if p["node"] == "cli_quota_before_0" and p["outcome"] == "before_send")
        unknown = next(p for p in prefixes if p["node"] == "cli_quota_before_0" and p["outcome"] == "lost_response")
        self.assertEqual(unknown["consumed_capacity"] - before["consumed_capacity"], 72)
        after = next(p for p in prefixes if p["node"] == "cli_quota_after_3" and p["outcome"] == "confirmed")
        self.assertEqual(after["consumed_capacity"], unknown["consumed_capacity"])

    def test_install_and_removal_groups_are_not_refunded_on_partial_failure(self):
        groups = self.normal["charge_groups"]
        self.assertEqual([groups[k]["capacity"] for k in ("guard_install", "metadata_install", "remove_0", "remove_1")],
                         [7, 6, 5, 5])
        first = groups["guard_install"]["nodes"][0]
        p = {r["outcome"]: r for r in self.report["fault_prefixes"] if r["node"] == first}
        self.assertEqual(p["timeout"]["consumed_capacity"] - p["before_send"]["consumed_capacity"], 7)

    def test_upfront_workflow_precharge_matches_current_executor_not_old_row_order(self):
        reader = next(i for i, r in enumerate(self.rows) if r["action"] == "lifecycle_reader_begin")
        prepaid = [r for r in self.rows[:reader] if r["action"] == "gotrue_fixture_identity"
                   or r["action"].startswith("gotrue_workflow_identity_")]
        self.assertEqual(len(prepaid), 72)
        self.assertEqual(sum(r["cost"] for r in prepaid), 360)
        self.assertEqual(sum(r["cost"] for r in prepaid if r["phase"] == "cleanup"), 130)
        row = self.rows[reader]
        prefix = next(p for p in self.report["fault_prefixes"] if p["node"] == row["id"] and p["outcome"] == "lost_response")
        self.assertEqual(prefix["workflow_prepaid_consumed"], 360)

    def test_final_source_sequence_is_pre_dry_remove_post_close(self):
        ids = [r["id"] for r in self.rows]
        pre = [i for i, r in enumerate(self.rows) if r["action"].startswith("gates_final_pre")]
        post = [i for i, r in enumerate(self.rows) if r["action"].startswith("gates_final_post")]
        removes = [i for i, r in enumerate(self.rows) if r["action"] == "remove"]
        self.assertEqual((len(pre), len(post), len(removes)), (11, 9, 10))
        self.assertLess(max(pre), ids.index("cli_final_before_0"))
        self.assertLess(ids.index("cli_final_after_3"), min(removes))
        self.assertLess(max(removes), min(post))
        self.assertEqual(self.rows[-1]["action"], "final_closure")

    def test_every_dispatch_boundary_has_all_five_outcomes(self):
        self.assertEqual(len(self.report["fault_prefixes"]), 1 + 5 * len(self.rows))
        for outcome in ("confirmed", "before_send", "lost_response", "timeout", "duplicate_rejected"):
            self.assertEqual(sum(p["outcome"] == outcome for p in self.report["fault_prefixes"]), len(self.rows))

    def test_unknown_full_bounds_never_admit_mutation_or_publish_minimum(self):
        self.assertIsNone(self.report["minimal_cap"])
        self.assertTrue(all(p["required_total"] is None and not p["mutation_admitted"]
                            for p in self.report["fault_prefixes"]))
        self.assertFalse(self.report["executable"])

    def test_all_fourteen_actual_fault_families_have_reference_anchors(self):
        self.assertEqual(len(self.report["fault_cases"]), 14)
        self.assertTrue(all(case["candidate_anchors"] for case in self.report["fault_cases"]))
        self.assertTrue(all(not case["full_source_adapter_bound"] for case in self.report["fault_cases"]))

    def test_actual_fixture_plan_and_every_unknown_failure_prefix(self):
        component = self.report["components"]["fixture"]
        self.assertEqual(len(component["tables"]), 13)
        self.assertEqual(component["preparation_capacity"], 4)
        self.assertEqual(component["normal_cleanup_capacity"], 22)
        self.assertEqual(component["failure_cleanup_max"], 22)
        self.assertEqual(len(component["fault_paths"]), 22)
        self.assertEqual(component["capture_hook_count"], 74)
        self.assertTrue(all(p["cost"] == 1 for p in component["candidate_capture_anchors"]))

    def test_fixture_rollback_is_not_replayed_after_unknown_commit(self):
        component = self.report["components"]["fixture"]
        commit = next(p for p in component["fault_paths"] if p["at"] == "fixture_commit")
        self.assertNotIn("fixture_rollback", commit["suffix"])
        deleted = next(p for p in component["fault_paths"] if p["at"] == "fixture_delete_windows")
        self.assertIn("fixture_rollback", deleted["suffix"])
        self.assertTrue(all(p["original_fault_retained"] and not p["retry"] for p in component["fault_paths"]))

    def test_auth_diagnostic_128_is_never_substituted_into_release_costs(self):
        component = self.report["components"]["auth"]
        self.assertEqual(component["native_slots"], 12)
        managed = [r for r in component["rows"] if r["kind"] == "auth_reserved"]
        self.assertEqual({r["action"] for r in managed}, {"create", "login", "logout", "delete"})
        self.assertTrue(all(r["cost"] is None for r in managed))
        self.assertFalse(component["managed_costs_proven"])

    def test_component_insertion_and_overlap_stay_explicitly_unresolved(self):
        unresolved = {row["id"] for row in self.report["unresolved_inputs"]}
        self.assertEqual(unresolved, {"normal_source_revalidation", "cli_predispatch",
                                    "auth_partial_costs", "fixture_placement", "recovery_orchestration"})
        self.assertFalse(self.report["new_component_costs_silently_added"])
        self.assertFalse(self.report["components"]["fixture"]["normal_and_failure_placement_proven"])

    def test_assembler_never_mutates_normal_rows_in_component_adapters(self):
        normal = copy.deepcopy(self.normal)
        register.fixture_component(normal["rows"])
        register.prefix_register(normal)
        self.assertEqual(normal, self.normal)

    def test_phase_exports_are_complete_disjoint_and_bind_full_register(self):
        normals, faults = [], []
        hashes = set()
        for phase in PHASE_BUDGETS:
            normal = register.export(self.report, "normal", phase)
            fault = register.export(self.report, "faults", phase)
            normals += normal["content"]
            faults += fault["content"]
            hashes.update((normal["full_register_sha256"], fault["full_register_sha256"]))
        self.assertEqual(len(normals), len(self.rows))
        self.assertEqual(len(faults) + 1, len(self.report["fault_prefixes"]))
        self.assertEqual(len(hashes), 1)

    def test_duplicate_diagnostic_dispatch_is_not_costed_as_rejection(self):
        case = next(c for c in self.report["fault_cases"] if c["case"]["id"] == "duplicate")
        self.assertEqual(case["actual_boundary_invocations"], 2)
        self.assertTrue(case["duplicate_test_is_not_zero_dispatch"])
        self.assertIsNone(case["required_total"])

    def test_auth_symbolic_paths_match_real_component_control_flow_in_memory(self):
        import auth_failure as auth
        from auth_failure_test import FakeBackend

        class MemoryJournal(auth.Journal):
            def __init__(self, folder, run_id, case, costs):
                self.plan = auth.contract(costs)
                self.charges = {**costs, **dict.fromkeys(auth.NATIVE_SLOTS, 1)}
                self.entries, self.spent, self.dispatched = [], 0, set()
                self.saved = {}

            def write(self, name, value):
                self.saved[name] = copy.deepcopy(value)

            def receipt(self):
                return {"scope": "IN_MEMORY_CONTROL_FLOW_TEST_ONLY", "files": {}}

        paths = self.report["components"]["auth"]["diagnostic_paths"]
        with patch.object(auth, "Journal", MemoryJournal):
            for path in paths:
                case = auth.Case(FakeBackend(), None, str(uuid.uuid4()), path["case"],
                                 dict.fromkeys(auth.OPERATIONS, 10))
                result = case.execute()
                self.assertEqual(result["native_sql_dispatches"], path["native_commands"], path["case"])
                self.assertEqual(result["http_dispatches"], path["http_actions"], path["case"])
                dispatched = [e["key"] for e in case.journal.entries if e["phase"] == "before_dispatch"]
                self.assertEqual(dispatched, [r["action"] for r in path["rows"]], path["case"])
                self.assertEqual(result["execution_status"], "NO_GO")
                self.assertIsNone(path["consumed_capacity"])

    def test_fixture_all_failure_prefix_counts_match_component_in_memory(self):
        from fixture_cleanup_runtime import Cleanup
        from fixture_cleanup_runtime_test import Database, row
        import fixture_cleanup_runtime_sql as sql

        expected = self.report["components"]["fixture"]["fault_paths"]
        for failure_index, path in enumerate(expected):
            with self.subTest(at=path["at"]):
                database = Database()
                context = {k: str(uuid.uuid4()) for k in ("window", "a", "b")}
                cleanup = Cleanup(database, context, database.save, lambda event: None)
                cleanup.prepare()
                database.rows = [row(table) for table in sql.ORDER]
                cleanup.capture(database.connect())
                before = len(cleanup.protocol.events)
                connect = database.connect
                dispatched = [0]

                def failing_connect():
                    connection = connect()
                    execute = connection.execute

                    def failing_execute(text, args=None):
                        index = dispatched[0]
                        dispatched[0] += 1
                        if index == failure_index:
                            if index == 0:
                                execute(text, args)  # Lost BEGIN reply after server-side entry.
                            raise ConnectionError("synthetic unknown dispatch")
                        return execute(text, args)

                    connection.execute = failing_execute
                    return connection

                database.connect = failing_connect
                result = cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
                self.assertEqual(len(cleanup.protocol.events) - before, path["total"])
                self.assertEqual(result["status"], "NO_GO")
                self.assertFalse(result["hosted_admitted"])


if __name__ == "__main__":
    unittest.main()
