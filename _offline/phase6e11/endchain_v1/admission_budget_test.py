"""Pure compiler tests. Synthetic graphs are not real SQL/Auth/CLI evidence."""
import copy
import hashlib
import itertools
import json
import pathlib
import subprocess
import sys
import unittest

import admission_budget as budget
from admission_binding import NEW_RUN

SHA = hashlib.sha256(b"synthetic compiler test, not an executor export").hexdigest()
BINDING = dict(source="synthetic", source_sha256=SHA)
SOURCES = {"synthetic": SHA}


def node(ident, *, cost=1, kind="native", phase="setup", stage="normal",
         success="done", failure="rollback", mutation=False):
    edges = dict.fromkeys(budget.OUTCOMES, failure)
    edges["confirmed"] = success
    return dict(id=ident, dispatch_id=ident, cost=cost, kind=kind, phase=phase,
                stage=stage, mutation=mutation, retry=False, next=edges, **BINDING)


def fixture():
    return dict(version=1, preparation_run_id=NEW_RUN, entry="first", nodes=[
        node("first", mutation=True, success="auth"),
        node("auth", kind="auth_reserved", cost=5, phase="auth"),
        node("rollback", phase="safety", stage="recovery", success="final", failure="final"),
        node("final", phase="final", stage="recovery", success="close", failure="close"),
        node("close", phase="closure", stage="recovery", success="stopped", failure="stopped")],
        terminals={"done": dict(status="normal_complete", pending_evidence=[]),
                   "stopped": dict(status="NO_GO", pending_evidence=["original fault retained"])})


def exhaustive(plan):
    """Small, deliberately independent oracle for the DAG dynamic program."""
    nodes = {n["id"]: n for n in plan["nodes"]}
    def visit(ident, used):
        if ident not in nodes:
            return used
        row = nodes[ident]
        return max(visit(target, used + (0 if result in budget.UNSENT else row["cost"]))
                   for result, target in row["next"].items())
    return visit(plan["entry"], 0)


def nominal_sized_fixture():
    """Abstract graph with nominal totals, NOT a declaration of actual costs."""
    nodes = []
    for phase, total in budget.PHASE_BUDGETS.items():
        chunks = []
        if phase == "auth":
            chunks.append(("auth_reserved", 318))
        if phase == "cleanup":
            chunks.append(("auth_reserved", 276))
        if phase == "migration":
            chunks.append(("cli_reserved", 120))
            chunks.extend([("observer", 1)] * 8)
        if phase == "final":
            chunks.extend([("observer", 1)] * 16)
        chunks.extend([("native", 1)] * (total - sum(cost for _, cost in chunks)))
        for kind, cost in chunks:
            nodes.append(node("n" + str(len(nodes)), kind=kind, cost=cost, phase=phase))
    for first, second in zip(nodes, nodes[1:]):
        first["next"]["confirmed"] = second["id"]
    recovery = node("rollback", phase="safety", stage="recovery",
                    success="stopped", failure="stopped")
    nodes.append(recovery)
    contracts = {name: dict(BINDING, nodes=[recovery["id"]]) for name in budget.COST_DOMAINS}
    contracts["native_protocol"]["nodes"] = [n["id"] for n in nodes]
    return dict(version=1, entry=nodes[0]["id"], preparation_run_id=NEW_RUN, nodes=nodes,
                terminals=fixture()["terminals"], cost_coverage=contracts,
                fault_cases={name: dict(BINDING, node=nodes[0]["id"], outcome="lost_response")
                             for name in budget.CASES},
                executor_inventory=dict(BINDING, complete=True), missing_costs=[])


class GraphTests(unittest.TestCase):
    def test_normal_and_every_fault_prefix(self):
        result = budget.compile_graph(fixture(), SOURCES)
        self.assertEqual(result["normal_capacity"], 6)
        self.assertEqual(result["model_bound"], 9)
        self.assertEqual(len(result["prefixes"]), 5 * 5)
        self.assertEqual({p["node"] for p in result["prefixes"]},
                         {"first", "auth", "rollback", "final", "close"})
        self.assertTrue(all(p["within_approved"] for p in result["prefixes"]))
        self.assertFalse(result["hosted_admitted"])

    def test_unknown_and_timeout_keep_whole_auth_reserve(self):
        result = budget.compile_graph(fixture(), SOURCES)
        for outcome in ("lost_response", "timeout"):
            p = next(p for p in result["prefixes"] if (p["node"], p["outcome"]) == ("auth", outcome))
            self.assertEqual((p["consumed_capacity"], p["suffix_capacity"]), (6, 3))

    def test_pre_dispatch_rejection_does_not_dispatch(self):
        result = budget.compile_graph(fixture(), SOURCES)
        for outcome in budget.UNSENT:
            p = next(p for p in result["prefixes"] if (p["node"], p["outcome"]) == ("auth", outcome))
            self.assertEqual(p["consumed_capacity"], 1)

    def test_differential_all_paths_including_faults_during_cleanup(self):
        for costs in itertools.product((1, 4), repeat=3):
            plan = fixture()
            for row, cost in zip(plan["nodes"][-3:], costs):
                row.update(kind="auth_reserved", cost=cost)
            self.assertEqual(budget.compile_graph(plan, SOURCES)["model_bound"], exhaustive(plan))

    def test_gate_rejects_mutation_whose_closure_would_exceed_cap(self):
        plan = fixture()
        plan["nodes"][1]["cost"] = budget.APPROVED
        result = budget.compile_graph(plan, SOURCES)
        self.assertFalse(result["fits"])
        self.assertFalse(result["mutation_gates"][0]["allowed_by_budget"])
        self.assertEqual(result["approved_limit"], 2349)

    def test_exact_ceiling_is_not_raised(self):
        plan = fixture()
        plan["nodes"][1]["cost"] = budget.APPROVED - 4
        self.assertEqual(budget.compile_graph(plan, SOURCES)["model_bound"], 2349)
        self.assertTrue(budget.compile_graph(plan, SOURCES)["fits"])
        plan["nodes"][1]["cost"] += 1
        self.assertFalse(budget.compile_graph(plan, SOURCES)["fits"])

    def test_cli_reserved_kind_is_not_observed_protocol(self):
        plan = fixture()
        plan["nodes"][1].update(kind="cli_reserved", cost=64)
        result = budget.compile_graph(plan, SOURCES)
        self.assertEqual(result["kind_capacities"]["cli_reserved"], 64)
        self.assertNotIn("observed_commands", result)

    def test_missing_unknown_negative_bool_and_native_batch_costs_fail_closed(self):
        for cost in (None, -1, True, 2):
            plan = fixture()
            plan["nodes"][0]["cost"] = cost
            with self.subTest(cost=cost), self.assertRaises(budget.ModelError):
                budget.compile_graph(plan, SOURCES)

    def test_missing_recovery_edge_fails_closed(self):
        plan = fixture()
        del plan["nodes"][-1]["next"]["timeout"]
        with self.assertRaisesRegex(budget.ModelError, "fault_cost_or_edge_missing"):
            budget.compile_graph(plan, SOURCES)

    def test_missing_source_binding_fails_closed(self):
        with self.assertRaisesRegex(budget.ModelError, "source_binding_changed"):
            budget.compile_graph(fixture(), {"synthetic": "0" * 64})

    def test_retry_cycles_fail_closed(self):
        plan = fixture()
        plan["nodes"][1]["next"]["timeout"] = "first"
        with self.assertRaisesRegex(budget.ModelError, "retry_or_cycle"):
            budget.compile_graph(plan, SOURCES)

    def test_retry_flag_fails_closed(self):
        plan = fixture()
        plan["nodes"][0]["retry"] = True
        with self.assertRaisesRegex(budget.ModelError, "retry_not_forbidden"):
            budget.compile_graph(plan, SOURCES)

    def test_same_dispatch_cannot_be_replayed_along_one_path(self):
        plan = fixture()
        plan["nodes"][1]["dispatch_id"] = "first"
        with self.assertRaisesRegex(budget.ModelError, "dispatch_replay"):
            budget.compile_graph(plan, SOURCES)

    def test_fault_never_becomes_pass(self):
        plan = fixture()
        plan["nodes"][1]["next"]["timeout"] = "done"
        with self.assertRaisesRegex(budget.ModelError, "fault_laundered_to_pass"):
            budget.compile_graph(plan, SOURCES)

    def test_fault_cannot_continue_dependent_normal_work(self):
        plan = fixture()
        plan["nodes"][0]["next"]["lost_response"] = "auth"
        with self.assertRaisesRegex(budget.ModelError, "dependent_normal_work_after_fault"):
            budget.compile_graph(plan, SOURCES)

    def test_unreachable_commands_cannot_pad_a_coverage_contract(self):
        plan = fixture()
        plan["nodes"].append(node("unused"))
        with self.assertRaisesRegex(budget.ModelError, "unreachable"):
            budget.compile_graph(plan, SOURCES)

    def test_input_is_not_mutated(self):
        plan = fixture()
        original = copy.deepcopy(plan)
        budget.compile_graph(plan, SOURCES)
        self.assertEqual(plan, original)


class ReleaseTests(unittest.TestCase):
    def test_bound_requires_complete_interfaces_not_phase_totals(self):
        result = budget.compile_release(fixture(), SOURCES)
        self.assertFalse(result["bound_complete"])
        self.assertIsNone(result["minimal_cap"])

    def test_preparation_binding_is_required(self):
        plan = nominal_sized_fixture()
        plan["preparation_run_id"] = "not-authorized"
        self.assertIsNone(budget.compile_release(plan, SOURCES)["minimal_cap"])

    def test_complete_abstract_model_has_bound_but_never_hosted_permission(self):
        result = budget.compile_release(nominal_sized_fixture(), SOURCES)
        self.assertTrue(result["bound_complete"], result)
        self.assertEqual(result["normal_capacity"], 2338)
        self.assertEqual(sum(result["phase_capacities"][p] for p in budget.CLOSING_PHASES), 731)
        self.assertEqual(result["minimal_cap"], 2339)  # This synthetic graph only.
        self.assertFalse(result["hosted_admitted"])
        self.assertFalse(result["actual_executor_and_real_ci_proven"])
        self.assertFalse(result["quota_activated"])

    def test_over_cap_model_reports_bound_without_increasing_authorization(self):
        plan = nominal_sized_fixture()
        plan["nodes"][-1].update(cost=20, kind="auth_reserved")
        result = budget.compile_release(plan, SOURCES)
        self.assertEqual(result["minimal_cap"], 2358)  # Deliberate synthetic overflow.
        self.assertEqual(result["status"], "NO_GO_OVER_CAP")
        self.assertEqual(result["approved_limit"], 2349)

    def test_each_missing_domain_blocks_minimum(self):
        for domain in budget.COST_DOMAINS:
            plan = nominal_sized_fixture()
            del plan["cost_coverage"][domain]
            result = budget.compile_release(plan, SOURCES)
            self.assertFalse(result["bound_complete"])
            self.assertIsNone(result["minimal_cap"])

    def test_missing_case_and_unpriced_action_block_minimum(self):
        for mutation in ("case", "cost", "inventory", "coverage"):
            plan = nominal_sized_fixture()
            if mutation == "case":
                del plan["fault_cases"]["partial_fixture_cleanup"]
            elif mutation == "cost":
                plan["missing_costs"] = ["parent ownership query"]
            elif mutation == "inventory":
                plan["executor_inventory"]["complete"] = False
            else:
                plan["cost_coverage"]["native_protocol"]["nodes"].pop(0)
            result = budget.compile_release(plan, SOURCES)
            self.assertIsNone(result["minimal_cap"], mutation)

    def test_historical_phase_allocation_cannot_pass_as_current(self):
        plan = nominal_sized_fixture()
        candidates = [n for n in plan["nodes"] if n["phase"] == "migration"]
        candidates[0]["phase"] = "final"
        self.assertIn("normal_phase_register_drift",
                      budget.compile_release(plan, SOURCES)["missing"])


class AccountingTests(unittest.TestCase):
    def event(self, ident="e", kind="auth_reserved", cost=21, outcome="lost_response", **extra):
        return dict(dispatch_id=ident, kind=kind, cost=cost, outcome=outcome, **extra)

    def test_unknown_auth_and_cli_stay_consumed(self):
        result = budget.account([self.event(), self.event("cli", "cli_reserved", 64),
                                 self.event("observer", "observer", 1, "confirmed", observed_commands=1)])
        self.assertEqual(result["consumed_capacity"], 86)
        self.assertEqual(result["confirmed_observed_by_kind"], {"observer": 1})
        self.assertEqual(result["status"], "NO_GO")

    def test_confirmed_lower_count_does_not_refund_prepaid_auth(self):
        result = budget.account([self.event(outcome="confirmed", observed_commands=4)])
        self.assertEqual(result["consumed_capacity"], 21)
        self.assertEqual(result["confirmed_observed_by_kind"], {"auth_reserved": 4})

    def test_overshoot_is_retained_even_below_global_cap(self):
        result = budget.account([self.event(outcome="confirmed", observed_commands=22)])
        self.assertEqual(result["consumed_capacity"], 22)
        self.assertEqual(result["reservation_overruns"], ["e"])
        self.assertEqual(result["status"], "NO_GO")

    def test_missing_counts_are_not_confirmed_counts(self):
        self.assertFalse(budget.account([self.event(outcome="confirmed")])["all_counts_known"])

    def test_repeated_dispatch_id_is_rejected(self):
        with self.assertRaisesRegex(budget.ModelError, "duplicate_or_missing"):
            budget.account([self.event(), self.event()])

    def test_unknown_send_cannot_be_called_unsent(self):
        for outcome in budget.UNSENT:
            with self.assertRaisesRegex(budget.ModelError, "uncertain_send"):
                budget.account([self.event(outcome=outcome)])

    def test_proven_pre_dispatch_stop_has_no_sql(self):
        result = budget.account([self.event(outcome="before_send", pre_dispatch_rejection_proven=True)])
        self.assertEqual(result["consumed_capacity"], 0)
        self.assertFalse(result["hosted_admitted"])

    def test_all_failure_outcomes_keep_prior_prepaid_capacity(self):
        for outcome in budget.OUTCOMES:
            result = budget.account([
                self.event("prepaid", cost=360),
                self.event("following", "native", 1, outcome,
                           pre_dispatch_rejection_proven=True)])
            self.assertGreaterEqual(result["consumed_capacity"], 360)
            self.assertEqual(result["status"], "NO_GO")


class SourceInventoryTests(unittest.TestCase):
    def test_current_source_inventory_is_incomplete_without_interfaces(self):
        result = budget.inspect_current()
        self.assertEqual(result["normal_capacity"], 2338)
        self.assertEqual(result["approved_limit"], 2349)
        self.assertEqual(result["closing_capacity"], 731)
        self.assertEqual(result["auth"]["total"], 594)
        self.assertEqual(result["cli"]["unknown_capacity"], 120)
        self.assertEqual(result["cli"]["observers"], 24)
        self.assertEqual(len(result["existing_safety_states"]), 128)
        self.assertIsNone(result["minimal_cap"])
        self.assertTrue(result["missing_costs"])
        self.assertFalse(result["hosted_admitted"])
        self.assertEqual(result["preparation_run_id"], NEW_RUN)

    def test_cli_emits_json_and_returns_incomplete_exit_code(self):
        result = subprocess.run([sys.executable, "-B", str(pathlib.Path(budget.__file__))],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "NO_GO_INCOMPLETE_BOUND")

    def test_current_audit_does_not_write_preserved_sources(self):
        paths = [budget.HERE / "closure_budget.json", budget.HERE / "authorization.json"]
        before = {str(path): budget.digest(path) for path in paths}
        budget.inspect_current()
        self.assertEqual(before, {str(path): budget.digest(path) for path in paths})


if __name__ == "__main__":
    unittest.main()
