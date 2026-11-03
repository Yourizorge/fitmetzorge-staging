"""Concrete assembly tests, not database or real Auth evidence."""
import copy
import collections
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import admission_budget_register as register
from admission_budget import PHASE_BUDGETS


class ConcreteRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = register.assemble()
        cls.normal = cls.report["normal_register"]
        cls.rows = cls.normal["rows"]
        cls.prefixes = {(p["node"], p["outcome"]): p for p in cls.report["fault_prefixes"]}

    def prefix(self, node, outcome="confirmed"):
        return self.prefixes[node, outcome]

    def safety_actions(self, prefix):
        return {r["action"] for r in self.report["reference_safety_paths"][prefix["safety_path"]]["commands"]}

    def test_precharge_rejection_and_transport_rejection_have_distinct_consumption(self):
        for group, capacity in (("cli_quota", 72), ("cli_pre_auth", 36), ("cli_final", 36),
                                ("guard_install", 7), ("metadata_install", 6), ("remove_0", 5), ("remove_1", 5)):
            with self.subTest(group=group):
                before = self.prefix("precharge:" + group, "rejected")
                paid = self.prefix("precharge:" + group)
                self.assertEqual(paid["consumed_capacity"] - before["consumed_capacity"], capacity)
                for ident in self.normal["charge_groups"][group]["nodes"]:
                    for outcome in ("confirmed", "before_send", "duplicate_rejected", "lost_response", "timeout"):
                        fault = self.prefix(ident, outcome)
                        self.assertEqual(fault["consumed_capacity"], paid["consumed_capacity"])
                        self.assertFalse(fault["unknown_dispatch_refunded"])
                        edge = self.report["command_graph"]["nodes"][ident]["next"][outcome]
                        self.assertEqual(edge["charge"], 0)

    def test_removal_attempt_is_recorded_at_first_charge_and_never_replayed(self):
        for group, name in (("remove_0", "observer"), ("remove_1", "guard")):
            with self.subTest(object=name):
                flag, action = name + "_remove_attempted", name + "_exact_remove"
                rejected = self.prefix("precharge:" + group, "rejected")
                self.assertFalse(rejected["state"][flag])
                self.assertIn(action, self.safety_actions(rejected))
                paid = self.prefix("precharge:" + group)
                self.assertTrue(paid["state"][flag])
                self.assertNotIn(action, self.safety_actions(paid))
                self.assertIn(name + "_inspect", self.safety_actions(paid))
                self.assertIn(name + "_absent", self.safety_actions(paid))
                for ident in self.normal["charge_groups"][group]["nodes"]:
                    for outcome in ("confirmed", "before_send", "duplicate_rejected", "lost_response", "timeout"):
                        prefix = self.prefix(ident, outcome)
                        self.assertTrue(prefix["state"][flag])
                        self.assertNotIn(action, self.safety_actions(prefix))
                        self.assertEqual(prefix["consumed_capacity"], paid["consumed_capacity"])
        first = self.prefix("precharge:remove_0")
        self.assertIn("guard_exact_remove", self.safety_actions(first))

    def test_sql_confirmation_does_not_release_controls_or_temporary_obligations(self):
        for action, flags in (("control_restored", ("controls",)),
                              ("gates_final_post_metadata", ("guard", "observer"))):
            with self.subTest(action=action):
                row = next(r for r in self.rows if r["action"] == action)
                sql = self.prefix(row["id"])
                validation = "validate:" + row["id"]
                self.assertTrue(all(sql["state"][f] for f in flags))
                self.assertEqual(self.report["command_graph"]["nodes"][row["id"]]["next"]["confirmed"]["to"], validation)
                for outcome in ("rejected", "interrupted"):
                    prefix = self.prefix(validation, outcome)
                    self.assertEqual(prefix["state"], sql["state"])
                    self.assertEqual(prefix["consumed_capacity"], sql["consumed_capacity"])
                validated = self.prefix(validation)
                self.assertTrue(all(not validated["state"][f] for f in flags))
                self.assertEqual(validated["consumed_capacity"], sql["consumed_capacity"])
                # The durable run claim has no validated release contract in this register.
                self.assertEqual(validated["state"]["claimed"], sql["state"]["claimed"])

    def test_later_io_failure_does_not_reactivate_validated_temporary_absence(self):
        index = next(i for i, r in enumerate(self.rows) if r["action"] == "gates_final_post_metadata")
        row = self.rows[index + 1]
        self.assertEqual(row["action"], "gates_final_post_io_sample")
        for outcome in ("before_send", "lost_response", "timeout"):
            prefix = self.prefix(row["id"], outcome)
            self.assertFalse(prefix["state"]["guard"])
            self.assertFalse(prefix["state"]["observer"])
            self.assertTrue(prefix["state"]["claimed"])
            self.assertIn("close_stopped_run", self.safety_actions(prefix))

    def test_upfront_workflow_rows_are_local_reservations_not_http_dispatches(self):
        events = register.normal_events(self.normal)
        prepaid = [e for e in events if e.get("workflow_prepaid")]
        checkpoints = [e for e in events if e.get("event_kind") == "local_reservation_checkpoint"]
        self.assertEqual(len(prepaid), 72)
        self.assertEqual(sum(e["cost"] for e in prepaid), 360)
        self.assertEqual(len(checkpoints), 72)
        self.assertTrue(all(e["cost"] == 0 and "before_send" not in e["outcomes"] for e in checkpoints))
        for index, event in enumerate(prepaid):
            self.assertFalse(event["dispatch_attempted"])
            self.assertEqual(self.prefix(event["id"], "rejected")["workflow_prepaid_consumed"], index * 5)
            self.assertEqual(self.prefix(event["id"])["workflow_prepaid_consumed"], (index + 1) * 5)

    def test_real_workflow_precharge_survives_failure_before_any_transport(self):
        from integral_ci import Composition
        from metered_composition import MeteredComposition
        from scenario import capture
        charged, confirmed = [], []

        def charge(phase, count, **kwargs):
            charged.append(dict(phase=phase, cost=count, **kwargs))
            return len(charged)

        instance = MeteredComposition.__new__(MeteredComposition)
        instance.meter = SimpleNamespace(charge=charge, confirm=lambda *a, **k: confirmed.append(a))
        instance.scenario = capture()["workflow_actions"]
        # No constructor, frozen authorization, database or historical run is invoked.
        with patch.object(Composition, "workflow", side_effect=RuntimeError("offline pre-transport failure")):
            with self.assertRaisesRegex(RuntimeError, "offline pre-transport"):
                instance.workflow()
        self.assertEqual(len(charged), 72)
        self.assertEqual(sum(r["cost"] for r in charged), 360)
        self.assertEqual(confirmed, [])
        expected = collections.Counter()
        for event in register.normal_events(self.normal):
            if event.get("workflow_prepaid"):
                expected[event["phase"]] += event["cost"]
        actual = collections.Counter()
        for row in charged:
            actual[row["phase"]] += row["cost"]
        self.assertEqual(actual, expected)

    def test_real_cli_adapter_refusal_retains_prepaid_envelope(self):
        from metered_composition import MeteredComposition
        for method, capacity in (("apply_migration", 72), ("pre_auth_dry_run", 36)):
            charged = []
            instance = MeteredComposition.__new__(MeteredComposition)
            instance.meter = SimpleNamespace(charge=lambda phase, count, **kwargs: charged.append(count))

            def refusal(*args, **kwargs):
                raise RuntimeError("offline adapter refusal, no transport")

            gate = SimpleNamespace(apply_endchain_migration=refusal, cli=refusal)
            with self.assertRaisesRegex(RuntimeError, "no transport"):
                getattr(instance, method)(gate)
            self.assertEqual(charged, [capacity])

    def test_real_removal_hook_sets_attempt_before_sql_dispatch_and_rejects_replay(self):
        from metered_composition import MeteredComposition
        for name in ("observer", "guard"):
            instance = MeteredComposition.__new__(MeteredComposition)
            state = {name + "_remove_attempted": False}
            charges = []

            def charge(phase, count, **kwargs):
                charges.append(count)
                state.update(kwargs.get("state_after", {}))
                return len(charges)

            instance.meter = SimpleNamespace(state=state, charge=charge, stopped=False)
            instance.safety_label = name + "_exact_remove"
            instance.closing_receipt = None
            instance.action = None
            instance.scenario = []
            instance.commands, instance.pending, instance.meter_stack = [], [], []
            instance.started = time.monotonic()
            text = "SELECT 1; SELECT 2; SELECT 3; SELECT 4; SELECT 5"
            instance.before_sql("remove", text)
            self.assertEqual(charges, [5])
            self.assertTrue(state[name + "_remove_attempted"])
            self.assertTrue(all(not c["confirmed"] for c in instance.commands))
            with self.assertRaisesRegex(ValueError, "removal_replay"):
                instance.before_sql("remove", text)
            self.assertEqual(charges, [5])

    def test_real_control_validator_does_not_accept_sql_confirmation_alone(self):
        from metered_composition import MeteredComposition
        released = []
        instance = MeteredComposition.__new__(MeteredComposition)
        instance.commands = [dict(phase="control_restored", confirmed=True)]
        instance.meter = SimpleNamespace(confirm_controls_restored=lambda: released.append(True))
        with self.assertRaisesRegex(RuntimeError, "control_restore_mismatch"):
            instance.confirm_controls_restored({"enabled": True}, {"enabled": False})
        self.assertEqual(released, [])
        self.assertNotIn("controls_restored_validated", instance.commands[-1])
        instance.confirm_controls_restored({"enabled": False}, {"enabled": False})
        self.assertEqual(released, [True])
        self.assertTrue(instance.commands[-1]["controls_restored_validated"])

    def test_real_post_metadata_releases_only_after_validation_even_if_later_io_fails(self):
        from metered_composition import MeteredComposition
        for failure in ("history", "metadata", "later_io"):
            with self.subTest(failure=failure):
                trace = []
                instance = MeteredComposition.__new__(MeteredComposition)
                instance.fixture_context, instance.gate_baseline = {}, {}
                instance.commands = []
                instance.native_runtime = lambda gate: SimpleNamespace(environment="disposable_ci")
                instance.meter = SimpleNamespace(confirm_temporary_absence=lambda: trace.append("released"))

                def query(phase, text, args=()):
                    instance.commands.append(dict(phase=phase, confirmed=True))
                    return [dict(value=dict(migrations=[]))]

                def validate(label):
                    def check(*args, **kwargs):
                        trace.append(label)
                        if failure == label:
                            raise ValueError("offline rejected " + label)
                    return check

                def close():
                    trace.append("later_io")
                    raise ValueError("offline rejected later_io")

                monitor = SimpleNamespace(start=lambda: None, bind=lambda *a, **k: 1,
                                          executed=lambda qid: trace.append("sql_confirmed"), close=close)
                gate = SimpleNamespace(sources={}, save=lambda *a: None)
                with patch("integral_io.QueryIO", return_value=monitor), \
                     patch("lifecycle_gates.final_parameters", return_value=([], None, None, {})), \
                     patch("history_pin.validate", side_effect=validate("history")), \
                     patch("lifecycle_gates.check_final", side_effect=validate("metadata")):
                    with self.assertRaisesRegex(ValueError, "offline rejected " + failure):
                        instance.final_metadata(gate, {}, "post", query)
                self.assertEqual(trace[0], "sql_confirmed")
                self.assertEqual("released" in trace, failure == "later_io")
                self.assertEqual(instance.commands[-1].get("temporary_absence_validated", False),
                                 failure == "later_io")
                if failure == "later_io":
                    self.assertEqual(trace, ["sql_confirmed", "history", "metadata", "released", "later_io"])

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
        before = next(p for p in prefixes if p["node"] == "precharge:cli_quota" and p["outcome"] == "rejected")
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
        self.assertEqual(p["timeout"]["consumed_capacity"], p["before_send"]["consumed_capacity"])
        before_charge = next(p for p in self.report["fault_prefixes"]
                             if p["node"] == "precharge:guard_install" and p["outcome"] == "rejected")
        self.assertEqual(p["timeout"]["consumed_capacity"] - before_charge["consumed_capacity"], 7)

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
        events = register.normal_events(self.normal)
        self.assertEqual(len(self.report["fault_prefixes"]), 1 + sum(len(e["outcomes"]) for e in events))
        prefixes = {(p["node"], p["outcome"]) for p in self.report["fault_prefixes"]}
        for event in events:
            for outcome in event["outcomes"]:
                self.assertIn((event["id"], outcome), prefixes)

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

    def test_negative_control_five_commands_are_ordered_and_only_diagnostic(self):
        component = self.report["components"]["fixture_diagnostic"]
        case = next(c for c in component["cases"] if c["case"] == "foreign_row")
        rows = case["rows"]
        witness = [r for r in rows if r["source"]["path"] == "fixture_control_ownership.py"]
        self.assertEqual([r["action"] for r in witness], ["foreign_row_parent_ownership",
            "foreign_row_parent_check_begin", "foreign_row_parent_check_limits",
            "foreign_row_parent_check_inventory", "foreign_row_parent_check_rollback"])
        self.assertEqual(sum(r["cost"] for r in witness), 5)
        actions = [r["action"] for r in rows]
        self.assertLess(actions.index("foreign_row_parent_ownership"), actions.index("foreign_row_writer_commit"))
        self.assertLess(actions.index("rollback"), actions.index("foreign_row_parent_check_begin"))
        self.assertFalse(any(a.startswith("delete_") for a in actions))
        self.assertEqual(case["intended_native_commands"], 33)
        self.assertEqual(component["intended_protocol_commands"], 364)
        self.assertFalse(component["negative_control_original_claim_promoted"])
        self.assertFalse(case["full_unexpected_fault_bound"])
        self.assertEqual(self.normal["normal_capacity"], 2338)
        self.assertEqual(self.normal["charge_groups"]["cli_quota"]["capacity"], 72)
        graph = self.report["command_graph"]["diagnostic_graphs"]["fixture_ci_foreign_row"]
        self.assertEqual(graph["intended_consumed_capacity"], 33)
        self.assertFalse(graph["full_fault_bound"])

    def test_negative_control_cost_drift_fails_closed(self):
        import fixture_control_ownership
        with patch.object(fixture_control_ownership, "CONTROL_LIMIT", 6):
            with self.assertRaisesRegex(ValueError, "negative_control_cost_contract_drift"):
                register.fixture_diagnostic_component(self.report["components"]["fixture"])

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
