"""Offline contract simulations only; no database, HTTP, Docker or CI calls."""
import copy
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import admission_budget_root_runtime as budget


class RootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gate = types.SimpleNamespace(out=pathlib.Path(self.temp.name), sources="unused")
        self.binding = {"run_id": "27a12427-d515-4210-8ca2-39702a80dc35"}
        self.program = [dict(command_id="unit:managed", units=128, reserve_after=1,
                             domain="disposable_auth"),
                        dict(command_id="unit:native", units=1, reserve_after=0,
                             domain="local_pg_case")]

    def ledger(self, **kwargs):
        program = copy.deepcopy(kwargs.get("program", self.program))
        def fixtures(value):
            for row in value if isinstance(value, list) else value["events"]:
                row.setdefault("hosted_units", row["units"])
                row.setdefault("hosted_reserve_after", row["reserve_after"])
                if row.get("children") is not None:
                    fixtures(row["children"])
        fixtures(program)
        return budget._Ledger(budget._KEY, self.gate, program=program,
            binding=kwargs.get("binding", self.binding), register_sha256="a"*64)

    def core(self):
        dag = dict(events=[{"event_id": "core:one"}], charge_groups={"one": {"capacity": 1}},
                   fault_cases={str(n): {} for n in range(12)},
                   bootstrap_fault_cases={"pre_migration": {}, "post_migration": {}})
        return dict(dag=dag, dag_sha256=budget.digest(dag), model=dict(approved_limit=2349,
            historical_normal=2338, historical_closing=731, normal_capacity=2340,
            meter_required_limit=2352, missing_costs=["core_recovery_incomplete"]))

    def test_root_retains_every_core_event_and_fourteen_cases(self):
        core = self.core()
        report = budget.assemble_root_register(core, source_hashes={"unit": "a"*64})
        self.assertEqual(report["core"], core)
        self.assertEqual(len(report["core_fault_cases"])+len(report["bootstrap_fault_cases"]), 14)
        self.assertEqual(report["core_events"], core["dag"]["events"])
        self.assertEqual(report["core_charge_groups"], core["dag"]["charge_groups"])

    def test_outer_domains_never_excluded_or_assumed_zero(self):
        report = budget.assemble_root_register(self.core(), source_hashes={})
        self.assertEqual(report["commands_excluded_by_domain"], [])
        self.assertEqual(len(report["root_obligations"]), 13)
        local = [r for r in report["root_obligations"] if r["hosted_equivalent"] is False]
        self.assertEqual({r["command_id"] for r in local}, {"root:platform_install", "root:clean47"})
        self.assertTrue(all(r["included_in_root"] and r["upper_bound"] is None
                            for r in report["root_obligations"]))
        self.assertIsNone(report["minimal_cap"])
        self.assertFalse(report["bound_complete"])

    def test_register_hash_covers_full_export(self):
        report = budget.assemble_root_register(self.core(), source_hashes={})
        expected = report.pop("full_register_sha256")
        self.assertEqual(budget.digest(report), expected)

    def test_declared_complete_core_does_not_complete_root(self):
        core = self.core()
        core["model"].update(bound_complete=True, minimal_cap=2340, fits=True, missing_costs=[])
        self.assertFalse(budget.assemble_root_register(core, source_hashes={})["fits"])

    def test_changed_historical_limit_rejected(self):
        core = self.core()
        core["model"]["historical_normal"] = 2340
        with self.assertRaisesRegex(budget.RootBlocked, "historical"):
            budget.assemble_root_register(core, source_hashes={})

    def test_forged_core_hash_rejected(self):
        core = self.core()
        core["dag"]["events"].clear()
        with self.assertRaisesRegex(budget.RootBlocked, "digest"):
            budget.assemble_root_register(core, source_hashes={})

    def test_public_open_refuses_complete_caller_flags(self):
        rebuilt = budget.assemble_root_register(self.core(), source_hashes={})
        caller = copy.deepcopy(rebuilt)
        caller.update(bound_complete=True, fits=True, minimal_cap=1)
        with patch.object(budget, "build_root_register", return_value=rebuilt):
            with self.assertRaisesRegex(budget.RootBlocked, "authoritative"):
                budget.open_execution_ledger(self.gate, dag=caller, model={}, binding=self.binding)

    def test_public_open_refuses_exact_incomplete_model(self):
        rebuilt = budget.assemble_root_register(self.core(), source_hashes={})
        model = {k: rebuilt[k] for k in budget.MODEL_FIELDS}
        with patch.object(budget, "build_root_register", return_value=rebuilt):
            with self.assertRaisesRegex(budget.RootBlocked, "bound_incomplete"):
                budget.open_execution_ledger(self.gate, dag=rebuilt, model=model, binding=self.binding)
        self.assertEqual(list(self.gate.out.iterdir()), [])

    def test_constructor_requires_internal_origin(self):
        with self.assertRaisesRegex(budget.RootBlocked, "origin"):
            budget._Ledger(None, self.gate, program=self.program,
                           binding=self.binding, register_sha256="a"*64)

    def test_old_uuid_rejected_before_journal(self):
        with self.assertRaisesRegex(budget.RootBlocked, "fresh"):
            self.ledger(binding={"run_id": "6f8c8909-9b79-4011-a9d1-db5e23c6b6c1"})
        self.assertEqual(list(self.gate.out.iterdir()), [])

    def test_precharge_published_before_return_and_no_refund(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        rows = [json.loads(line) for line in ledger._journal.read_text().splitlines()]
        self.assertEqual(rows[0]["event"]["state"], "precharged")
        self.assertEqual(rows[0]["reserved_consumed"], 128)
        ledger.confirm(ticket, observed_sql_commands=3)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 128)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=1)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 4)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 129)

    def test_unknown_keeps_charge_and_blocks_next(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        ledger.unknown(ticket, reason="lost_response")
        self.assertEqual(ledger.receipt()["reserved_consumed"], 128)
        self.assertFalse(ledger.receipt()["events"][0]["numeric_confirmed"])
        with self.assertRaises(budget.RootBlocked):
            ledger.precharge("unit:native")

    def recovery_program(self):
        def row(ident, units, reserve, confirmed=None, unknown=None, safety=False):
            return dict(command_id=ident, units=units, reserve_after=reserve, domain="unit",
                        next_confirmed=confirmed, next_unknown=unknown, safety_only=safety)
        return dict(entry="create", events=[row("create", 128, 11, "done", "cleanup"),
            row("done", 0, 0), row("cleanup", 10, 1, "stop", "stop", True),
            row("stop", 1, 0, safety=True)])

    def test_only_source_selected_cleanup_after_unknown(self):
        ledger = self.ledger(program=self.recovery_program())
        ticket = ledger.precharge("create")
        ledger.unknown(ticket, reason="not_terminal")
        with self.assertRaises(budget.RootBlocked):
            ledger.precharge("done")
        ledger.confirm(ledger.precharge("cleanup"), observed_sql_commands=10)
        ledger.confirm(ledger.precharge("stop"), observed_sql_commands=1)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 139)
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertFalse(ledger.receipt()["full_chain_admission"])

    def test_cleanup_unknown_has_only_its_safe_successor(self):
        ledger = self.ledger(program=self.recovery_program())
        ledger.unknown(ledger.precharge("create"), reason="lost_response")
        ledger.unknown(ledger.precharge("cleanup"), reason="interrupted")
        ledger.confirm(ledger.precharge("stop"), observed_sql_commands=1)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 139)

    def test_recovery_may_not_resume_normal(self):
        program = self.recovery_program()
        program["events"][2]["next_confirmed"] = "done"
        with self.assertRaisesRegex(budget.RootBlocked, "resume_normal"):
            self.ledger(program=program)

    def test_recovery_reserve_cannot_be_omitted(self):
        program = self.recovery_program()
        program["events"][0]["reserve_after"] = 10
        with self.assertRaisesRegex(budget.RootBlocked, "underreserved"):
            self.ledger(program=program)

    def test_recovery_cycle_rejected(self):
        program = self.recovery_program()
        program["events"][3]["next_unknown"] = "cleanup"
        with self.assertRaisesRegex(budget.RootBlocked, "cycle"):
            self.ledger(program=program)

    def test_numeric_fault_is_not_success_and_keeps_allocation(self):
        ledger = self.ledger(program=self.recovery_program())
        ledger.fault(ledger.precharge("create"), observed_sql_commands=3)
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertEqual(ledger.receipt()["reserved_consumed"], 128)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 3)
        self.assertTrue(ledger.receipt()["events"][0]["numeric_confirmed"])
        self.assertEqual(ledger.receipt()["events"][0]["state"], "fault_numeric_confirmed")

    def test_startup_measurement_requires_foreground_end_not_health(self):
        program = copy.deepcopy(self.program)
        program[0]["defer"] = True
        ledger = self.ledger(program=program)
        ticket = ledger.precharge("unit:managed")
        ledger.defer(ticket)
        with self.assertRaisesRegex(budget.RootBlocked, "before_foreground_close"):
            ledger.settle_deferred(ticket, observed_sql_commands=3)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=1)
        ledger.settle_deferred(ticket, observed_sql_commands=3)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 129)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 4)
        self.assertEqual(ledger.receipt()["deferred_observations"], 0)

    def test_unknown_background_never_becomes_zero(self):
        program = copy.deepcopy(self.program)
        program[0]["defer"] = True
        ledger = self.ledger(program=program)
        ticket = ledger.precharge("unit:managed")
        ledger.defer(ticket)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=1)
        ledger.settle_deferred(ticket)
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertEqual(ledger.receipt()["reserved_consumed"], 129)
        self.assertFalse(ledger.receipt()["events"][0]["numeric_confirmed"])

    def test_defer_requires_source_flag(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        with self.assertRaisesRegex(budget.RootBlocked, "defer_not_registered"):
            ledger.defer(ticket)

    def envelope_program(self):
        return [dict(command_id="unit:lifetime", units=129, reserve_after=0, domain="unit",
                     children=copy.deepcopy(self.program))]

    def test_envelope_counts_children_once(self):
        ledger = self.ledger(program=self.envelope_program())
        ticket, child = ledger.open_envelope("unit:lifetime")
        child.confirm(child.precharge("unit:managed"), observed_sql_commands=3)
        child.confirm(child.precharge("unit:native"), observed_sql_commands=1)
        ledger.close_envelope(ticket, child, observed_sql_commands=4)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 129)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 4)
        self.assertEqual(len(list(self.gate.out.iterdir())), 2)

    def test_envelope_cannot_forget_live_child(self):
        ledger = self.ledger(program=self.envelope_program())
        ticket, child = ledger.open_envelope("unit:lifetime")
        child.precharge("unit:managed")
        with self.assertRaisesRegex(budget.RootBlocked, "envelope_incomplete"):
            ledger.close_envelope(ticket, child, observed_sql_commands=0)
        with self.assertRaisesRegex(budget.RootBlocked, "requires_close"):
            ledger.unknown(ticket, reason="interrupted")

    def test_parent_must_cover_child_source_bound(self):
        program = self.envelope_program()
        program[0]["units"] = 128
        with self.assertRaisesRegex(budget.RootBlocked, "child_coverage_underreserved"):
            self.ledger(program=program)

    def grouped_program(self):
        program = copy.deepcopy(self.program)
        for row in program:
            row.update(defer=True, observation_group="unit:managed_lifetime")
        return program

    def test_one_union_no_invented_per_request_counts(self):
        ledger = self.ledger(program=self.grouped_program())
        tickets = []
        for ident in ("unit:managed", "unit:native"):
            ticket = ledger.precharge(ident)
            tickets.append(ticket)
            ledger.defer(ticket)
        ledger.settle_union(tickets, observed_sql_commands=17)
        receipt = ledger.receipt()
        self.assertEqual(receipt["observed_sql_commands"], 17)
        self.assertEqual(receipt["reserved_consumed"], 129)
        self.assertEqual(receipt["deferred_observations"], 0)
        self.assertTrue(all(not e["numeric_confirmed"] for e in receipt["events"]))
        self.assertEqual(len(receipt["numeric_unions"]), 1)
        with self.assertRaises(budget.RootBlocked):
            ledger.settle_union(tickets, observed_sql_commands=17)

    def test_group_cannot_be_settled_individually_or_partially(self):
        ledger = self.ledger(program=self.grouped_program())
        first = ledger.precharge("unit:managed")
        ledger.defer(first)
        second = ledger.precharge("unit:native")
        ledger.defer(second)
        with self.assertRaisesRegex(budget.RootBlocked, "requires_union"):
            ledger.settle_deferred(first, observed_sql_commands=3)
        with self.assertRaisesRegex(budget.RootBlocked, "union_incomplete"):
            ledger.settle_union([first], observed_sql_commands=3)

    def test_deferred_fault_can_follow_only_safety_path(self):
        program = self.recovery_program()
        program["events"][0]["defer"] = True
        ledger = self.ledger(program=program)
        ticket = ledger.precharge("create")
        ledger.defer_fault(ticket)
        ledger.confirm(ledger.precharge("cleanup"), observed_sql_commands=10)
        ledger.confirm(ledger.precharge("stop"), observed_sql_commands=1)
        ledger.settle_deferred(ticket, observed_sql_commands=3)
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 14)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 139)

    def test_union_write_failure_cannot_double_count_on_retry(self):
        ledger = self.ledger(program=self.grouped_program())
        tickets = []
        for ident in ("unit:managed", "unit:native"):
            ticket = ledger.precharge(ident)
            tickets.append(ticket)
            ledger.defer(ticket)
        with patch.object(budget.os, "fsync", side_effect=OSError("unit disk failure")):
            with self.assertRaises(OSError):
                ledger.settle_union(tickets, observed_sql_commands=17)
        with self.assertRaisesRegex(budget.RootBlocked, "journal_failed"):
            ledger.settle_union(tickets, observed_sql_commands=17)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 17)

    def test_native_partition_and_managed_union_count_once(self):
        program = copy.deepcopy(self.program)
        program[0].update(defer=True, observation_units=100, observation_group="unit:lifetime")
        ledger = self.ledger(program=program)
        ticket = ledger.precharge("unit:managed")
        ledger.defer(ticket, partial_observed_sql_commands=15)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=1)
        ledger.settle_union([ticket], observed_sql_commands=20)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 36)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 129)
        self.assertEqual(ledger.receipt()["events"][0]["partial_observed_sql_commands"], 15)

    def test_partial_native_cannot_spend_managed_reservation(self):
        program = copy.deepcopy(self.program)
        program[0].update(defer=True, observation_units=100, observation_group="unit:lifetime")
        ledger = self.ledger(program=program)
        ticket = ledger.precharge("unit:managed")
        with self.assertRaisesRegex(budget.RootBlocked, "partial_observation_bound"):
            ledger.defer(ticket, partial_observed_sql_commands=29)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 0)

    def test_terminal_fields_and_original_journal_refs(self):
        ledger = self.ledger(program=self.envelope_program())
        ticket, child = ledger.open_envelope("unit:lifetime")
        self.assertEqual(ledger.receipt()["active_envelopes"], 1)
        self.assertFalse(ledger.receipt()["program_exhausted"])
        child.confirm(child.precharge("unit:managed"), observed_sql_commands=3)
        child.confirm(child.precharge("unit:native"), observed_sql_commands=1)
        ledger.close_envelope(ticket, child, observed_sql_commands=4)
        receipt = ledger.receipt()
        self.assertIsNone(receipt["remaining_command_id"])
        self.assertTrue(receipt["program_exhausted"])
        self.assertEqual(receipt["active_envelopes"], 0)
        self.assertFalse(receipt["journal_failed"])
        self.assertEqual(len(receipt["journal_refs"]), 2)
        for ref in receipt["journal_refs"]:
            self.assertTrue(ref["path"].endswith(".ledger.txt"))
            raw = (self.gate.out / ref["path"]).read_bytes()
            self.assertEqual(ref["sha256"], budget.hashlib.sha256(raw).hexdigest())
            self.assertEqual(ref["size"], len(raw))

    def test_no_second_precharge_while_pending(self):
        ledger = self.ledger()
        ledger.precharge("unit:managed")
        with self.assertRaises(budget.RootBlocked):
            ledger.precharge("unit:managed")

    def test_no_replay_after_confirmation(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        ledger.confirm(ticket, observed_sql_commands=3)
        with self.assertRaises(budget.RootBlocked):
            ledger.confirm(ticket, observed_sql_commands=3)

    def test_mutated_ticket_cannot_increase_allowance(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        ticket.units = 500
        with self.assertRaisesRegex(budget.RootBlocked, "ticket_changed"):
            ledger.confirm(ticket, observed_sql_commands=400)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 0)

    def test_wrong_order_no_charge(self):
        ledger = self.ledger()
        with self.assertRaises(budget.RootBlocked):
            ledger.precharge("unit:native")
        self.assertEqual(ledger.receipt()["reserved_consumed"], 0)

    def test_numeric_bool_is_not_count(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        with self.assertRaises(budget.RootBlocked):
            ledger.confirm(ticket, observed_sql_commands=True)

    def test_observed_overrun_retained_and_stops(self):
        ledger = self.ledger()
        ticket = ledger.precharge("unit:managed")
        with self.assertRaisesRegex(budget.RootBlocked, "overrun"):
            ledger.confirm(ticket, observed_sql_commands=129)
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 129)

    def test_real_limit_not_raised_for_prefix(self):
        program = [dict(command_id="unit:over", units=2340, reserve_after=12, domain="unit")]
        ledger = self.ledger(program=program)
        with self.assertRaisesRegex(budget.RootBlocked, "prefix_capacity"):
            ledger.precharge("unit:over")
        self.assertEqual(ledger.receipt()["reserved_consumed"], 0)

    def test_local_only_setup_not_misclassified_as_hosted_capacity(self):
        program = [dict(command_id="unit:local_setup", units=2350, reserve_after=0,
                        hosted_units=0, hosted_reserve_after=0, domain="local_pg_build47")]
        ledger = self.ledger(program=program)
        ledger.confirm(ledger.precharge("unit:local_setup"), observed_sql_commands=2350)
        self.assertEqual(ledger.receipt()["reserved_consumed"], 2350)
        self.assertEqual(ledger.receipt()["hosted_equivalent_reserved"], 0)
        self.assertEqual(ledger.receipt()["hosted_limit"], 2349)
        self.assertFalse(ledger.receipt()["runtime_admitted"])

    def test_journal_failure_prevents_dispatch_ticket(self):
        ledger = self.ledger()
        with patch.object(budget.os, "fsync", side_effect=OSError("unit disk failure")):
            with self.assertRaises(OSError):
                ledger.precharge("unit:managed")
        self.assertTrue(ledger.receipt()["stopped"])
        self.assertEqual(ledger.receipt()["reserved_consumed"], 128)

    def test_existing_journal_preserved(self):
        ledger = self.ledger()
        ledger.precharge("unit:managed")
        original = ledger._journal.read_bytes()
        with self.assertRaises(FileExistsError):
            self.ledger()
        self.assertEqual(ledger._journal.read_bytes(), original)

    def test_one_member_and_strict_size_limit(self):
        ledger = self.ledger()
        with patch.object(type(ledger._journal), "stat", return_value=types.SimpleNamespace(st_size=1_999_999)):
            with self.assertRaisesRegex(budget.RootBlocked, "member_limit"):
                ledger.precharge("unit:managed")
        self.assertEqual(len(list(self.gate.out.iterdir())), 1)

    def test_journal_external_mutation_is_not_rehashed_as_original(self):
        ledger = self.ledger()
        ledger.confirm(ledger.precharge("unit:managed"), observed_sql_commands=3)
        with ledger._journal.open("ab") as stream:
            stream.write(b"{}\n")
        with self.assertRaisesRegex(budget.RootBlocked, "journal_modified"):
            ledger.journal_refs()
        self.assertTrue(ledger._journal_failed)

    def test_terminal_journal_replays_exact_memory_and_totals(self):
        ledger = self.ledger()
        ledger.confirm(ledger.precharge("unit:managed"), observed_sql_commands=3)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=1)
        ledger.close()
        proof = ledger.validate_journal()
        self.assertEqual(proof["sequence"], 5)
        self.assertEqual(proof["sha256"], ledger.journal_refs()[0]["sha256"])
        ledger._observed += 1
        with self.assertRaisesRegex(budget.RootBlocked, "totals_mismatch"):
            ledger.validate_journal()

    def test_terminal_journal_checks_original_numeric_union(self):
        ledger = self.ledger(program=self.grouped_program())
        for ident in ("unit:managed", "unit:native"):
            ledger.defer(ledger.precharge(ident))
        ledger.settle_union(ledger.deferred_group("unit:managed_lifetime"), observed_sql_commands=17)
        ledger.close()
        ledger.validate_journal()
        ledger._unions[0]["observed_sql_commands"] = 18
        with self.assertRaisesRegex(budget.RootBlocked, "memory_mismatch"):
            ledger.validate_journal()

    def test_public_terminal_and_runtime_guards_deny_private_unit_ledger(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(budget.RootBlocked, "actual_owner"):
            budget.require_runtime_ledger(self.gate, ledger, command_id="unit:managed")
        with self.assertRaisesRegex(budget.RootBlocked, "actual_owner"):
            budget.validate_terminal(ledger, self.gate, self.binding)

    def test_selector_reserves_max_branch_and_uses_internal_node_identity(self):
        state = dict(owned_roles=[])
        row = lambda node, command, cost, reserve, **kw: dict(node_id=node, command_id=command,
            units=cost, reserve_after=reserve, hosted_units=0, hosted_reserve_after=0,
            domain="local_ci", next_confirmed=None, next_unknown=None, safety_only=True, **kw)
        program = dict(entry="begin", events=[
            dict(command_id="begin", units=0, reserve_after=5, hosted_units=0, hosted_reserve_after=0,
                 domain="local_ci", next_confirmed="selector", next_unknown="selector", safety_only=False),
            row("selector", "auth.cleanup.select", 0, 5,
                selection_cases={budget.digest(state): "stop-empty", budget.digest(dict(owned_roles=["a"])): "stop-owned"}),
            row("stop-empty", "auth.auth_stop", 1, 0), row("stop-owned", "auth.auth_stop", 5, 0)])
        ledger = self.ledger(program=program)
        ledger.confirm(ledger.precharge("begin"), observed_sql_commands=0)
        selected = ledger._select_cleanup_state(budget._KEY, state)
        self.assertEqual(selected["next_command_id"], "auth.auth_stop")
        ledger.confirm(ledger.precharge("auth.auth_stop"), observed_sql_commands=1)
        self.assertEqual(ledger.close()["reserved_consumed"], 1)
        self.assertEqual(ledger._local_bound, 5)
        ledger.validate_journal()

    def test_public_cleanup_selector_rejects_ducktyped_context(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(budget.RootBlocked, "actual_context"):
            ledger.select_cleanup(types.SimpleNamespace())

    def test_selected_ci_counts_are_observations_not_authority(self):
        values = {
            "result.json": dict(status="NO_GO", run_id="unit", full_chain_admission=False,
                                private_material="must not appear"),
            "admission-auth-auth-failure-component.json": dict(cases=[{}, {}],
                diagnostic_totals=dict(native_sql_dispatched=95, observed_managed_sql=344,
                    parent_environment_setup_and_teardown_included=False)),
            "integral-component-auth-cleanup.json": dict(bootstrap_and_cleanup_units=1182),
            "fixture-producer-scope-before-result.json": dict(status="NO_GO", admitted_attempts=10),
        }
        for name, value in values.items():
            (self.gate.out / name).write_text(json.dumps(value))
        result = budget.inspect_ci_components(self.gate.out)
        self.assertEqual(result["files"]["admission-auth-auth-failure-component.json"]["case_count"], 2)
        self.assertNotIn("private_material", json.dumps(result))
        self.assertFalse(result["bound_complete"])
        self.assertTrue(result["parent_setup_teardown_must_be_added"])
        self.assertTrue(result["cross_case_totals_not_single_case"])
        self.assertFalse(result["proves_current_source"])

    def original_evidence(self, padding=""):
        register = dict(executable_program=self.program, source_hashes={"unit.py": "a"*64}, padding=padding)
        register["full_register_sha256"] = budget.digest(register)
        refs = budget._register_evidence(self.gate.out, register, self.binding)
        return register, refs

    def test_original_payload_is_lossless_bounded_and_not_authority(self):
        register, refs = self.original_evidence("x" * 1_600_000)
        self.assertEqual(len(refs), 3)
        self.assertTrue(all(r["bytes"] <= 1_400_000 for r in refs))
        self.assertTrue(all(pathlib.Path(r["path"]).suffix in (".json", ".txt") for r in refs))
        value = budget.read_register_evidence(self.gate.out, refs,
            register_sha256=register["full_register_sha256"], binding=self.binding)
        self.assertEqual(value["register"], register)
        self.assertEqual(value["program"], self.program)
        self.assertNotIn("runtime_admitted", value)

    def test_original_payload_never_overwrites_and_tamper_denied(self):
        register, refs = self.original_evidence()
        path = self.gate.out / refs[0]["path"]
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            budget._register_evidence(self.gate.out, register, self.binding)
        self.assertEqual(path.read_bytes(), original)
        path.write_bytes(original.replace(b"unit.py", b"edit.py"))
        with self.assertRaisesRegex(budget.RootBlocked, "modified"):
            budget.read_register_evidence(self.gate.out, refs,
                register_sha256=register["full_register_sha256"], binding=self.binding)

    def test_original_payload_wrong_binding_or_order_denied(self):
        register, refs = self.original_evidence()
        with self.assertRaisesRegex(budget.RootBlocked, "binding"):
            budget.read_register_evidence(self.gate.out, refs,
                register_sha256=register["full_register_sha256"], binding=dict(run_id="other"))
        with self.assertRaisesRegex(budget.RootBlocked, "index_members"):
            budget.read_register_evidence(self.gate.out, list(reversed(refs)),
                register_sha256=register["full_register_sha256"], binding=self.binding)

    def test_original_payload_rejects_bad_digest_before_publication(self):
        with self.assertRaisesRegex(budget.RootBlocked, "register_digest"):
            budget._register_evidence(self.gate.out, dict(full_register_sha256="a"*64), self.binding)
        self.assertEqual(list(self.gate.out.iterdir()), [])

    def test_original_payload_fsync_failure_prevents_handoff(self):
        register = dict(executable_program=self.program)
        register["full_register_sha256"] = budget.digest(register)
        with patch.object(budget.os, "fsync", side_effect=OSError("unit durability")):
            with self.assertRaises(OSError):
                budget._register_evidence(self.gate.out, register, self.binding)
        self.assertFalse((self.gate.out / "root-original-index.json").exists())

    def test_missing_ci_receipt_not_synthesized(self):
        with self.assertRaises(FileNotFoundError):
            budget.inspect_ci_components(self.gate.out)

    @unittest.skipUnless(os.name == "nt", "Windows MAX_PATH regression")
    def test_windows_preserved_long_member(self):
        path = self.gate.out / ("x" * 190 + ".json")
        self.assertGreater(len(str(path)), 260)
        extended = pathlib.Path("\\\\?\\" + str(path))
        extended.write_bytes(b"{}")
        self.addCleanup(extended.unlink)
        self.assertEqual(budget._read_bytes(path), b"{}")

    def test_deferred_group_returns_ordered_immutable_view(self):
        ledger = self.ledger(program=self.grouped_program())
        tickets = []
        for ident in ("unit:managed", "unit:native"):
            ticket = ledger.precharge(ident)
            ledger.defer(ticket)
            tickets.append(ticket)
        self.assertEqual(ledger.deferred_group("unit:managed_lifetime"), tuple(tickets))
        self.assertEqual(ledger.deferred_group("other"), ())

    def test_unknown_core_partition_cannot_disappear_from_lifetime_union(self):
        program = self.recovery_program()
        for row in program["events"]:
            if row["command_id"] in ("create", "cleanup"):
                row.update(defer=True, observation_group=budget.MANAGED_OBSERVATION_GROUP)
        ledger = self.ledger(program=program)
        ledger.unknown(ledger.precharge("create"), reason="not_terminal")
        ticket = ledger.precharge("cleanup")
        ledger.defer(ticket)
        ledger.confirm(ledger.precharge("stop"), observed_sql_commands=1)
        with self.assertRaisesRegex(budget.RootBlocked, "unknown_or_already_counted"):
            ledger.settle_union(ledger.deferred_group(budget.MANAGED_OBSERVATION_GROUP),
                                observed_sql_commands=3)

    def test_close_does_not_promote_unknown_accounting(self):
        ledger = self.ledger()
        ledger.unknown(ledger.precharge("unit:managed"), reason="not_terminal")
        receipt = ledger.close()
        self.assertTrue(receipt["closed"])
        self.assertTrue(receipt["stopped"])
        self.assertFalse(receipt["runtime_admitted"])
        self.assertFalse(receipt["hosted_admitted"])
        with self.assertRaisesRegex(budget.RootBlocked, "closed"):
            ledger.precharge("unit:native")
        with self.assertRaisesRegex(budget.RootBlocked, "close_unavailable"):
            ledger.close()

    def test_close_requires_foreground_and_deferred_terminal(self):
        ledger = self.ledger(program=self.grouped_program())
        with self.assertRaisesRegex(budget.RootBlocked, "close_incomplete"):
            ledger.close()
        for ident in ("unit:managed", "unit:native"):
            ledger.defer(ledger.precharge(ident))
        with self.assertRaisesRegex(budget.RootBlocked, "close_incomplete"):
            ledger.close()
        ledger.settle_union(ledger.deferred_group("unit:managed_lifetime"), observed_sql_commands=3)
        self.assertTrue(ledger.close()["closed"])

    def test_close_publication_failure_stays_failed(self):
        ledger = self.ledger()
        ledger.unknown(ledger.precharge("unit:managed"), reason="not_terminal")
        with patch.object(budget.os, "fsync", side_effect=OSError("offline failure")):
            with self.assertRaises(OSError):
                ledger.close()
        self.assertTrue(ledger.receipt()["journal_failed"])

    def test_nullable_suffix_does_not_add_only_known_costs(self):
        rows = [dict(units=1, hosted_units=0), dict(units=None, hosted_units=0),
                dict(units=3, hosted_units=None)]
        result = budget._nullable_suffix(rows)
        self.assertIsNone(result["local_upper_bound"])
        self.assertIsNone(result["hosted_upper_bound"])
        self.assertIsNone(rows[0]["reserve_after"])
        self.assertEqual(rows[1]["reserve_after"], 3)

    def test_exclusive_source_snapshot_export(self):
        report = dict(blocked_stage="unit", rows=[dict(units=None)])
        report["source_program_sha256"] = budget.digest(report)
        path = self.gate.out / "new.json"
        receipt = budget.write_source_snapshot(path, report)
        self.assertEqual(receipt["sha256"], budget.hashlib.sha256(path.read_bytes()).hexdigest())
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            budget.write_source_snapshot(path, report)
        self.assertEqual(path.read_bytes(), original)

    def test_snapshot_rejects_mutated_rows_before_write(self):
        report = dict(blocked_stage="unit")
        report["source_program_sha256"] = budget.digest(report)
        report["blocked_stage"] = "changed"
        with self.assertRaisesRegex(budget.RootBlocked, "snapshot_digest"):
            budget.write_source_snapshot(self.gate.out / "new.json", report)
        self.assertEqual(list(self.gate.out.iterdir()), [])


class ActualSourceTests(unittest.TestCase):
    def test_new_cost_contract_is_bound_not_executed_or_promoted(self):
        value = self.report["current_declared_startup_inventory"]["derived_cost_contract"]
        self.assertFalse(value["evaluated"])
        self.assertFalse(value["numeric_bound_accepted"])
        self.assertEqual(self.report["source_hashes"][value["source"]], value["source_sha256"])
        self.assertEqual(value["function"], "source_bound_contract")
        startup = next(r for r in self.report["context_normal"] if r["command_id"] == "auth.auth_start")
        self.assertIsNone(startup["units"])
        self.assertIn("auth.derived_cost_contract:effective_native_driver_and_OCI_startup_provenance",
                      self.report["missing_costs"])

    """Current source inspection only: no imports of candidate runtime modules."""
    @classmethod
    def setUpClass(cls):
        root = pathlib.Path(os.environ.get("A_RECOVERY_SOURCE_ROOT",
            str(pathlib.Path(__file__).resolve().parents[3]))).resolve(strict=True)
        runtime = pathlib.Path(os.environ.get("A_RECOVERY_RUNTIME_DIR",
            str(root / budget.PREFIX / "quota_candidate_v1"))).resolve(strict=True)
        cls.report = budget.source_program(root,
            runtime_dir=runtime, context_dir=runtime,
            dependency_paths={budget.PREFIX + name: root / budget.PREFIX / name for name in (
                "auth_failure_parent_finalizer.py", "admission_auth_runtime_profile.py",
                "quota_candidate_v1/runtime_registered_fixture_closeout.py", "install_platform.py")})

    def test_new_validations_and_profile_placement_are_not_omitted(self):
        rows = self.report["context_normal"]
        validations = [r for r in rows if r["command_id"].startswith("auth.validate.")]
        self.assertEqual(len(validations), 6)
        self.assertTrue(all(r["units"] == r["explicit_sql"] == 0 for r in validations))
        ids = [r["command_id"] for r in rows]
        self.assertLess(ids.index("auth.validate.target"), ids.index("auth.profile"))
        self.assertLess(ids.index("auth.profile"), ids.index("auth.managed_stats_before_start"))
        profile = rows[ids.index("auth.profile")]
        self.assertEqual((profile["explicit_sql"], profile["protocol_explicit_limit"], profile["connection_calls"]), (10, 11, 2))
        self.assertIsNone(profile["units"])
        self.assertEqual(profile["hosted_units"], 0)

    def test_fixture_and_parent_remain_separate_source_bound_unknown_macros(self):
        rows = {r["command_id"]: r for r in self.report["context_normal"]}
        fixture = rows["auth.fixture_closeout"]
        self.assertEqual((fixture["explicit_sql"], fixture["protocol_explicit_limit"],
                          fixture["original_unknown_zero_only_explicit_sql"]), (36, 37, 23))
        self.assertIsNone(fixture["units"])
        self.assertIsNone(rows["auth.parent_cleanup"]["units"])
        self.assertTrue(all(r["selected"] for r in self.report["component_source_bindings"].values()))

    def test_passive_readiness_counts_process_not_concurrent_auth_as_zero(self):
        rows = self.report["context_normal"]
        ids = [r["command_id"] for r in rows]
        item = rows[ids.index("auth.auth_listen_ready")]
        self.assertEqual((item["units"], item["explicit_sql"], item["process_invocations"]), (0, 0, 1))
        self.assertEqual((item["passive_poll_ceiling"], item["process_deadline_seconds"]), (40, 12))
        self.assertEqual(item["concurrent_managed_sql_covered_by"], budget.MANAGED_OBSERVATION_GROUP)
        self.assertLess(ids.index("auth.validate.auth"), ids.index("auth.auth_listen_ready"))
        self.assertLess(ids.index("auth.auth_listen_ready"), ids.index("auth.health"))

    def test_actual_order_and_first_blocked_stage(self):
        self.assertEqual([r["command_id"] for r in self.report["root_order"]],
            ["case.platform.install", "case.bootstrap.clean47", "case.auth.context", "case.terminal"])
        self.assertEqual(self.report["blocked_stage"], "case.platform.install")
        self.assertIsNone(self.report["root_order"][0]["units"])
        self.assertIsNone(self.report["root_order"][0]["reserve_after"])

    def test_actual_context_source_has_nine_seed_and_twenty_quota_dispatches(self):
        rows = self.report["context_normal"]
        self.assertEqual(sum(r["explicit_sql"] for r in rows if r["command_id"].startswith("auth.seed.")), 9)
        quota = next(r for r in rows if r["command_id"] == "case.quota_read")
        self.assertEqual(quota["explicit_sql"], 20)
        self.assertIsNone(quota["units"])
        self.assertEqual(len(self.report["quota_read"]["commands"]), 20)

    def test_conditional_parent_reservation_is_not_observed_bound(self):
        for n in range(4):
            case = self.report["fault_suffixes"]["preseed_owned_" + str(n)]
            self.assertEqual(case["declared_scope_parent_total"], 13 + 133*n)
            self.assertEqual(case["native_scope_and_parent"], 13 + 5*n)
            self.assertIsNone(case["local_upper_bound"])
            self.assertTrue(case["excludes_startup_seed_stop_connections"])

    def test_parent_all_ownership_reads_precede_delete(self):
        rows = self.report["fault_suffixes"]["preseed_owned_3"]["commands"]
        ids = [r["command_id"] for r in rows]
        self.assertLess(ids.index("auth.engine.b:before"), ids.index("auth.engine.a:delete"))

    def test_no_canonical45_replay_or_lifecycle_double_charge(self):
        life = self.report["source_joins"]["lifecycle"]
        self.assertFalse(life["canonical45_replayed"])
        self.assertEqual(life["covered_by"], "case.core")
        self.assertEqual(life["gate_commands"], dict(before=20, after_migration=20, pre=11, post=9))
        self.assertEqual(life["label_operations"]["final_post"], ["gate_final_post9"])

    def test_current_dependency_and_workflow_pair_pinned(self):
        hashes = self.report["source_hashes"]
        for path in ("admission_budget_register.py", "scenario.py", "admission_budget_current_recovery.py"):
            self.assertRegex(hashes[budget.PREFIX + path], "^[0-9a-f]{64}$")
        self.assertIn("_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py", hashes)
        self.assertTrue(self.report["source_joins"]["context"]["parent_registered_bootstrap_hook"])

    def test_snapshot_binds_all_rows_and_dispatch_sites(self):
        report = copy.deepcopy(self.report)
        expected = report.pop("source_program_sha256")
        self.assertEqual(budget.digest(report), expected)
        self.assertTrue(any(r["dispatch_sites"] for r in report["source_records"].values()))
        report["context_normal"][0]["units"] = 3000
        self.assertNotEqual(budget.digest(report), expected)

    def test_no_source_snapshot_promoted_to_execution_or_hosted_claim(self):
        self.assertFalse(self.report["bound_complete"])
        self.assertFalse(self.report["source_inventory_complete"])
        self.assertFalse(self.report["actual_execution_evidence"])
        self.assertFalse(self.report["hosted_admitted"])
        self.assertIsNone(self.report["executable_program"])
        self.assertIsNone(self.report["total_local_ci_upper_bound"])
        self.assertIsNone(self.report["total_hosted_equivalent_upper_bound"])
        self.assertFalse(self.report["local_ci_compared_to_hosted_limit"])

    def test_every_context_instruction_has_retained_fault_prefix(self):
        rows = self.report["context_normal"]
        prefixes = self.report["instruction_fault_prefixes"]
        self.assertEqual(len(rows), len(prefixes))
        for index, prefix in enumerate(prefixes):
            self.assertEqual(prefix["retained_command_ids"], [r["command_id"] for r in rows[:index+1]])
            self.assertEqual(prefix["refunds"], 0)
            self.assertFalse(prefix["complete"])


if __name__ == "__main__":
    unittest.main()
