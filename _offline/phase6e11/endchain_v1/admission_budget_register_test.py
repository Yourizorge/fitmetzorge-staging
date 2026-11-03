"""Concrete assembly tests, not database or real Auth evidence."""
import copy
import collections
import time
import unittest
import uuid
import sys
import pathlib
import tempfile
from types import SimpleNamespace, ModuleType
from unittest.mock import patch

import admission_budget_register as register
from admission_budget import PHASE_BUDGETS


class ScenarioSourceTests(unittest.TestCase):
    def test_cached_checkout_scenario_cannot_replace_candidate_source(self):
        cached = ModuleType('scenario')
        calls = []
        def unavailable():
            calls.append('cached_checkout')
            raise FileNotFoundError('workflow_only_exists_in_candidate')
        cached.capture = unavailable
        with patch.dict(sys.modules, {'scenario': cached}):
            value = register.workflow_component(register.auth_component())
        self.assertEqual(calls, [])
        self.assertEqual(len(value['cases']), 12)
        expected = register.HERE.parents[2] / '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'
        self.assertEqual(value['scenario_source_sha256'], register.digest(expected))

    def test_missing_workflow_source_never_falls_back_to_checkout(self):
        raw = (register.HERE / 'scenario.py').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            here = pathlib.Path(directory) / '_offline/phase6e11/endchain_v1'
            here.mkdir(parents=True)
            (here / 'scenario.py').write_bytes(raw)
            with patch.object(register, 'HERE', here), self.assertRaises(FileNotFoundError):
                register.workflow_capture()

    def test_source_change_during_capture_is_rejected(self):
        workflow = register.HERE.parents[2] / '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'
        read = pathlib.Path.read_bytes
        seen = []
        def changing(path):
            value = read(path)
            if path == workflow:
                seen.append(path)
                if len(seen) == 3:
                    return value + b'\n'
            return value
        with patch.object(pathlib.Path, 'read_bytes', changing):
            with self.assertRaisesRegex(ValueError, 'budget_scenario_changed_during_capture'):
                register.workflow_capture()


class ConcreteRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = register.assemble()
        cls.normal = cls.report["normal_register"]
        cls.rows = cls.normal["rows"]
        cls.prefixes = {(p["node"], p["outcome"]): p for p in cls.report["fault_prefixes"]}

    def prefix(self, node, outcome="confirmed"):
        return self.prefixes[node, outcome]

    def test_composed_cleanup_all_source_bounded_parameter_shapes_are_registered(self):
        import fixture_parent_physical_zero as physical
        model = self.report["components"]["cleanup_composition"]
        self.assertEqual(len(model["parameter_cases"]), 286)
        self.assertEqual(len(model["physical_shapes"]), 66)
        for case in model["parameter_cases"]:
            n,e,u = case["cases"],case["eligible"],case["unknown"]
            shape = model["physical_shapes"][case["physical_shape"]]
            expected = physical.protocol_plan(n,e)
            self.assertEqual([r["action"] for r in shape["rows"]], [label for label,_ in expected])
            self.assertEqual([r["sql_sha256"] for r in shape["rows"]],
                             [register.hashlib.sha256(sql.encode()).hexdigest() for _,sql in expected])
            self.assertEqual(case["normal_prepaid_capacity"], 20 + len(expected) + 5*u + 402)
            self.assertEqual(case["declared_meter_caps"], case["normal_prepaid_capacity"] + 1)
        self.assertFalse(model["bound_complete"])
        self.assertTrue(model["not_a_total_for_the_parent_ci_job"])

    def test_composed_cleanup_command_order_and_all_fault_prefixes_stop_later_blocks(self):
        plan = register.cleanup_composition_plan(3,1,1)
        self.assertEqual(plan["graph_order"], ["scope_before","scope_after","unknown_zero_0","physical_suffix","parent_auth"])
        self.assertEqual([b["normal_capacity"] for b in plan["blocks"]], [10,10,5,40,402])
        self.assertEqual(plan["normal_prepaid_capacity"], 467)
        self.assertEqual(plan["declared_meter_caps"], 468)
        self.assertTrue(all(p["later_blocks_admitted"] is False for p in plan["fault_prefixes"]))
        self.assertTrue(all(p["composition_required_capacity"] <= 468 for p in plan["fault_prefixes"]))
        self.assertFalse(plan["external_interval"]["counted_here"])
        self.assertTrue(plan["external_interval"]["not_zero_cost"])

    def test_composed_unknown_commit_no_rollback_or_auth_and_no_claim_release(self):
        plan = register.cleanup_composition_plan(2,0,2)
        physical = next(b for b in plan["blocks"] if b["id"] == "physical_suffix")
        commit = next(r["id"] for r in physical["rows"] if r["action"] == "registry_commit")
        faults = [p for p in physical["fault_prefixes"] if p["at"] == commit]
        self.assertTrue(all(not p["suffix"] and not p["later_blocks_admitted"] for p in faults))
        self.assertTrue(all(p["unknown_commit_reclassified"] is False for p in faults))
        self.assertFalse(plan["original_unknown_claims_released"])

    def test_composed_persistence_failure_distinguishes_producer_poison_from_zero_meter(self):
        plan = register.cleanup_composition_plan(1,0,1)
        for block in plan["blocks"][:3]:
            failure = next(p for p in block["fault_prefixes"] if p["at"] == block["rows"][0]["id"]
                           and p["outcome"] == "charge_storage_failed")
            self.assertEqual(failure["consumed_capacity"], 1)
            self.assertEqual(failure["suffix_capacity"], 1 if block["id"].startswith("unknown_zero") else 0)

    def test_composed_suspend_admin_has_no_invented_startup_cost_or_extra_observer_charge(self):
        plan = register.cleanup_composition_plan(1,0,1)
        transport = plan["transport_boundaries"]
        self.assertEqual(transport["close_attempts"], 2)
        self.assertEqual(transport["reconnect_attempts"], 2)
        self.assertEqual(transport["explicit_new_sql"], 0)
        self.assertIsNone(transport["startup_protocol_cost"])
        self.assertEqual(plan["wrapper_final_observers"]["commands"], 3)
        self.assertFalse(plan["wrapper_final_observers"]["additive"])
        self.assertEqual(self.report["normal_register"]["normal_capacity"], 2338)
        self.assertEqual(self.report["approved_limit"], 2349)

    def test_composed_case_counts_reject_bool_overlap_zero_unknown_and_excess(self):
        for args in ((True,0,1),(0,0,1),(12,0,1),(3,2,2),(3,0,0),(3,-1,1)):
            with self.assertRaises(ValueError):
                register.cleanup_composition_plan(*args)

    def test_current_v2_reserves_setup_at_every_prefix_without_touching_reference(self):
        plan = self.report["current_plan"]
        self.assertEqual(plan["version"], "admission-current-plan-v2")
        self.assertEqual(plan["previous_file_checkpoint"], register.PREVIOUS_CHECKPOINT)
        self.assertEqual(plan["historical_register_sha256"], register.canonical_sha(self.normal))
        self.assertEqual(len(plan["prefix_bindings"]), len(self.report["fault_prefixes"]))
        for binding in plan["prefix_bindings"]:
            old = self.report["reference_safety_paths"][binding["reference_path"]]
            new = plan["recovery_paths"][binding["recovery_path"]]
            self.assertNotIn("rollback_setup", [r["action"] for r in old["commands"]])
            self.assertEqual(new["reserved_capacity"], old["reference_capacity"] + 1)
            self.assertEqual(sum(r["action"] == "rollback_setup" for r in new["commands"]), 1)
        self.assertEqual(plan["historical_normal"], 2338)
        self.assertEqual(plan["historical_headroom"], 11)
        self.assertEqual(plan["setup_increment_only_headroom"], 10)
        self.assertFalse(plan["bound_complete"])
        self.assertIsNone(plan["minimal_cap"])

    def test_new_recovery_reservation_is_callable_unknown_consumed_no_retry(self):
        plan = self.report["current_plan"]
        key = next(iter(plan["recovery_paths"]))
        for outcome in ("confirmed", "unknown", "failed"):
            receipt = register.recovery_reservations(plan, key, [dict(action="rollback_setup", outcome=outcome)])
            self.assertEqual(receipt["consumed_capacity"], 1)
            self.assertEqual(receipt["refunds"], 0)
            self.assertEqual(receipt["dispatches_executed"], 0)
        with self.assertRaisesRegex(ValueError, "unknown_or_duplicate"):
            register.recovery_reservations(plan, key, [dict(action="rollback_setup", outcome="unknown")] * 2)
        with self.assertRaisesRegex(ValueError, "unknown_or_duplicate"):
            register.recovery_reservations(plan, key, [dict(action="invented", outcome="confirmed")])

    def test_current_thirty_rows_have_source_templates_and_only_two_receipt_inputs(self):
        plan = self.report["current_plan"]
        self.assertEqual(len(plan["source_derived_row_ids"]), 30)
        rows = plan["normal"]["rows"]
        removals = [r for r in rows if r["action"] == "remove"]
        self.assertEqual([r["owner"] for r in removals], ["observer"] * 5 + ["guard"] * 5)
        self.assertEqual([r["statement_index"] for r in removals if r["binding_required"]], [3, 3])
        self.assertTrue(all(r["sql_sha256"] is None for r in removals if r["binding_required"]))
        self.assertEqual(sum(r["sql_sha256"] is not None for r in removals), 8)
        actions = [r["action"] for r in rows]
        self.assertLess(actions.index("gates_final_pre_begin"), actions.index("cli_final"))
        self.assertLess(actions.index("cli_final"), actions.index("remove"))
        self.assertLess(max(i for i,r in enumerate(rows) if r["action"] == "remove"),
                        actions.index("gates_final_post_begin"))
        for stage in ("pre", "post"):
            actual = register.current_final_rows(stage)
            old = register.final_gate(stage)
            self.assertEqual([(r["action"],r["sql_sha256"]) for r in actual],
                             [(r["action"],r["sql_sha256"]) for r in old])
            self.assertTrue(all(r["derivation"] == "AST_call_order_and_PG17_statement_parser" for r in actual))

    def test_current_plan_rejects_final_source_schedule_drift(self):
        original = register._method
        def changed(filename, name, cls=None):
            node = original(filename, name, cls)
            if name == "final_metadata":
                node.body.append(register.ast.parse("query(phase+'_unexpected', 'SELECT 1')").body[0])
            return node
        with patch.object(register, "_method", changed), self.assertRaisesRegex(ValueError, "final_call_order_drift"):
            register.current_final_rows("pre")

    def test_current_removal_binding_uses_existing_pure_renderers_fresh_case_only(self):
        from complete_register import bound_module
        audit = bound_module("budget_test_audit", register.HERE / register.REMOVAL_SOURCES["observer"])
        run_id = str(uuid.uuid4())
        ids = {r:str(uuid.uuid4()) for r in audit.g.ROLES}
        schema, deadline = audit.scope(run_id, ids), "2026-11-03T12:00:00+00:00"
        # Synthetic renderer inputs, not database or CI evidence.
        observer = dict(schema=schema, lease=dict(run=run_id, expires_at=deadline, version=1),
            secure_function=True, function_count=1, relations=audit.RELATIONS, dependencies=7,
            body_sha=register.hashlib.sha256(audit.function_body(schema, ids, deadline).encode()).hexdigest(),
            function_sha="a"*64, triggers=[dict(name=schema+'_'+str(i),table='auth.'+table,enabled='O',type=29,sha='b'*64)
                for i,table in enumerate(audit.TABLES)])
        guard_schema = audit.g.scope(run_id, ids)
        guard = dict(schema=guard_schema, run=run_id, function_sha='c'*64,
                     trigger_shas={guard_schema+suffix:'d'*64 for suffix in ('_i','_u','_d')})
        plan = self.report["current_plan"]
        before = register.canonical_sha(plan)
        bound = register.bind_current_plan(plan, run_id=run_id, ids=ids,
                                           observer_receipt=observer, guard_receipt=guard)
        self.assertEqual(register.canonical_sha(plan), before)
        self.assertFalse(any(r.get("binding_required") for r in bound["normal"]["rows"]))
        self.assertNotEqual(bound["plan_sha256"], plan["plan_sha256"])
        self.assertFalse(bound["hosted_admitted"])
        from admission_binding import OLD_RUN, NEW_RUN
        for forbidden in (OLD_RUN, NEW_RUN):
            with self.assertRaisesRegex(ValueError, "fresh_case_binding"):
                register.bind_current_plan(plan, run_id=forbidden, ids=ids,
                                           observer_receipt=observer, guard_receipt=guard)
        observer["function_count"] = 2
        with self.assertRaisesRegex(ValueError, "audit_objects"):
            register.bind_current_plan(plan, run_id=run_id, ids=ids,
                                       observer_receipt=observer, guard_receipt=guard)

    def test_setup_rollback_is_explicit_missing_cost_not_identity_lock_alias(self):
        mapping = self.report["components"]["rollback_dispatch_mapping"]
        self.assertEqual(mapping["missing_labels"], ["rollback_setup"])
        self.assertEqual(mapping["missing_conditional_commands"], 1)
        rows = {r["action"]: r for r in mapping["rows"]}
        self.assertEqual(rows["rollback_auth_lock"]["reserved_capacity"], 1)
        self.assertIsNone(rows["rollback_setup"]["reserved_capacity"])
        self.assertIsNone(rows["rollback_setup"]["equivalent_alias"])
        self.assertEqual(rows["rollback_setup"]["source_dispatch_cost"], 1)
        self.assertFalse(mapping["inner_and_finally_deduplicated"])
        self.assertFalse(mapping["approved_limit_changed"])
        self.assertIsNone(mapping["full_required_capacity"])

    def test_final_metadata_templates_bind_the_actual_remove_dispatch_context(self):
        for row in register.final_gate("pre") + register.final_gate("post"):
            self.assertEqual(row["action_binding"], {"kind": "lifecycle", "operation": "remove"})

    def test_parent_auth_finalizer_has_source_ordered_18_native_and_three_prepaid_deletes(self):
        import auth_failure_parent_finalizer as parent
        component = self.report["components"]["parent_auth_finalizer"]
        rows = component["rows"]
        self.assertEqual([r["action"] for r in rows if r["kind"] == "native"], list(parent.NATIVE))
        self.assertEqual(len(rows), 21)
        self.assertEqual(component["native_commands"], 18)
        self.assertEqual(component["http_maximum"], 3)
        self.assertEqual(sum(r["cost"] for r in rows), 402)
        deletes = [r for r in rows if r["kind"] == "auth_reserved"]
        self.assertEqual([r["cost"] for r in deletes], [128, 128, 128])
        self.assertTrue(all(r["second_transport_charge"] == 0 for r in deletes))
        self.assertTrue(all(r["observed_managed_cost"] is None for r in deletes))
        self.assertFalse(component["actual_execution_observed"])
        self.assertFalse(component["hosted_reference_changed"])
        self.assertEqual(component["source"]["sha256"], self.report["source_hashes"]["auth_failure_parent_finalizer.py"])

    def test_parent_auth_delete_unknown_keeps_measurement_and_absence_but_stops_later_roles(self):
        component = self.report["components"]["parent_auth_finalizer"]
        faults = {p["at"]: p for p in component["fault_paths"]}
        for role, total in (("a", 136), ("trainer", 267), ("b", 398)):
            prefix = faults["parent_auth_" + role + ":delete"]
            self.assertEqual(prefix["suffix"], ["parent_auth_" + role + ":stats_after_delete",
                                                 "parent_auth_" + role + ":after"])
            self.assertEqual(prefix["required_capacity"], total)
            self.assertFalse(prefix["later_role_delete_admitted"])
            self.assertFalse(prefix["retry"])
            self.assertEqual(prefix["refunds"], 0)
            self.assertEqual(len(faults["parent_auth_" + role + ":stats_after_delete"]["suffix"]), 1)
        self.assertEqual(max(p["required_capacity"] for p in faults.values()), 402)
        self.assertEqual(self.normal["normal_capacity"], 2338)
        self.assertIsNone(self.report["minimal_cap"])

    def test_parent_auth_costs_are_explicit_not_a_default_or_release_bound(self):
        from auth_failure_tracked import Blocked
        for costs in ({}, dict(a=128, trainer=128), dict(a=True, trainer=128, b=128)):
            with self.assertRaisesRegex(Blocked, "explicit_delete_costs"):
                register.parent_auth_finalizer_component(costs)
        self.assertFalse(self.report["components"]["parent_auth_finalizer"]["managed_release_costs_proven"])

    def test_opt_in_registration_anchors_are_exact_business_connection_sites(self):
        component = self.report["components"]["opt_in_diagnostics"]
        db = component["tracked_db"]
        counts = collections.Counter(r["case"] for r in db["registration_anchors"])
        self.assertEqual(dict(counts), dict(setup=1, full=4, partial=4, parent_only=4,
            dependent_without_workspace=4, zero=3, lost_writer_commit=4, missing_barrier=2,
            foreign_row=5, lost_commit=4, interrupted_delete=4, lock_timeout=5, closing=1))
        self.assertEqual(db["intended_component_registrations"], 45)
        self.assertEqual(db["component_additional_protocol_commands"], 47)
        self.assertEqual(len({r["before"] for r in db["registration_anchors"]}), 45)
        self.assertTrue(db["registration_before_component_not_counted_twice"])
        self.assertFalse(component["observed_execution"])
        self.assertIsNone(component["native_startup_protocol_bound"])

    def test_opt_in_sql_templates_and_limits_are_source_bound(self):
        import fixture_db_terminality as db
        component = self.report["components"]["opt_in_diagnostics"]["tracked_db"]
        self.assertEqual(component["registration_rows"][0]["sql_sha256"],
                         register.hashlib.sha256(db.REGISTER.encode()).hexdigest())
        self.assertEqual([r["action"] for r in component["terminal_rows"]],
                         ["observer_identity", "backend_absence"])
        self.assertEqual([r["action"] for r in component["physical_zero_rows"]],
                         ["zero_begin", "zero_session", "backend_absence", "zero_inventory", "zero_rollback"])
        self.assertEqual([p["total"] for p in component["physical_zero_faults"]], [2, 3, 4, 5, 5])
        self.assertTrue(all(not p["retry"] for p in component["physical_zero_faults"]))
        self.assertFalse(component["original_claims_released"])
        self.assertFalse(component["registry_cleanup_admitted"])
        for name in ("fixture_db_terminality.py", "test_fixture_db_terminality.py"):
            self.assertEqual(self.report["source_hashes"][name], register.digest(register.HERE / name))
        with patch.object(db, "ZERO_LIMIT", 6):
            with self.assertRaisesRegex(ValueError, "tracked_db_contract_drift"):
                register.opt_in_diagnostics(self.report["components"]["fixture"],
                    self.report["components"]["fixture_diagnostic"], self.report["components"]["auth"])

    def test_parent_suffix_has_22_case_11_registry_with_no_unknown_commit_replay(self):
        parent = self.report["components"]["opt_in_diagnostics"]["parent_closure"]
        self.assertEqual(len(parent["case_rows"]), 22)
        self.assertEqual(len(parent["registry_rows"]), 11)
        self.assertEqual([p["total"] for p in parent["registry_faults"]],
                         [6, 7, 8, 9, 10, 11, 11, 8, 9, 10, 11])
        self.assertNotIn("parent_registry_rollback", parent["registry_faults"][6]["suffix"])
        self.assertFalse(parent["original_unknown_commit_replayed"])
        self.assertFalse(parent["tracked_factory_used"])
        self.assertIn("mint_barrier", parent["barrier_required"])

    def test_reconciliation_uses_remaining_524_not_a_second_allocation(self):
        component = self.report["components"]["opt_in_diagnostics"]
        paths = {p["case"]: p for p in component["auth_reconciliation"]}
        self.assertEqual({k: p["diagnostic_capacity"] for k, p in paths.items()},
                         dict(admin_unknown=1, cleanup_interrupted=132, missing_mint_barrier=1))
        for p in paths.values():
            self.assertEqual(p["original_reservation"], 524)
            self.assertEqual(p["additional_reservation"], 0)
            self.assertFalse(p["original_claim_released"])
            self.assertFalse(p["journal_durability_verified"])
            self.assertIsNone(p["managed_release_cost"])
        self.assertEqual([r["action"] for r in paths["cleanup_interrupted"]["rows"]],
                         ["observe", "stats_before_delete", "delete", "stats_after_delete", "verify_zero"])
        self.assertEqual(component["auth_transport"]["extra_sql_dispatched_by_relay"], 0)
        self.assertFalse(component["auth_transport"]["full_normal_transport_mapping_proven"])

    def test_expected_dispatch_mapping_is_lossless_not_current_execution_proof(self):
        contract = self.report["normal_dispatch_mapping"]
        self.assertEqual([r["row_id"] for r in contract["rows"]], [r["id"] for r in self.rows])
        for mapped, row in zip(contract["rows"], self.rows):
            self.assertEqual(mapped["expected"]["action_binding"], row.get("action_binding", {}))
            self.assertEqual(mapped["expected"]["sql_sha256"], row.get("sql_sha256"))
            self.assertFalse(mapped["matching_current_dispatch_observed"])
        counts = collections.Counter(r["stream"] for r in contract["rows"])
        self.assertEqual(counts["workflow_auth_protocol"], 72)
        self.assertEqual(counts["auth_protocol_operation"], 18)
        self.assertEqual(counts["cli_protocol_slot"], 27)
        self.assertEqual(counts["integral_preflight"], 4)
        self.assertFalse(contract["complete_dispatch_bound"])
        self.assertEqual(self.normal["normal_capacity"], 2338)
        self.assertEqual(self.report["approved_limit"], 2349)
        self.assertIsNone(self.report["minimal_cap"])
        self.assertEqual(self.report["status"], "NO_GO_INCOMPLETE_BOUND")

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
                                    "auth_partial_costs", "fixture_placement", "recovery_orchestration", "setup_rollback"})
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
