"""Source-only joins. No caller-signed completion or positive runtime admission."""
import ast
import copy
import importlib.util
import pathlib
import sys
import unittest

from admission_budget_release_joins import bind_lifecycle, derive_release_joins, GATES
from admission_budget_lifecycle_native import Strings, lifecycle_program
from test_admission_budget_recovery_program import ROOT, RUNTIME


class JoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / "_offline/phase6e11/endchain_v1"
        sys.path.append(str(base))
        parser = ROOT / "supabase/.temp/phase6e11-pg17-parser"
        sys.path.append(str(parser))
        spec = importlib.util.spec_from_file_location("original_release_source_probe",
                                                     base / "admission_budget_current_release.py")
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        _, _, cls.plan, cls.before = original._authoritative(ROOT, RUNTIME)
        cls.normal = bind_lifecycle(cls.before, runtime_dir=RUNTIME)
        cls.proof = derive_release_joins(ROOT, RUNTIME, cls.plan, cls.normal)

    def test_lifecycle_binding_preserves_all_costs_and_order(self):
        self.assertEqual([e["event_id"] for e in self.before["events"]],
                         [e["event_id"] for e in self.normal["events"]])
        self.assertEqual([e["cost"] for e in self.before["events"]],
                         [e["cost"] for e in self.normal["events"]])
        self.assertEqual(self.before["charge_groups"], self.normal["charge_groups"])
        self.assertEqual(self.normal["actual_lifecycle_join"]["counts"],
                         {k: v[0] for k, v in GATES.items()})

    def test_actual_sixty_templates_do_not_complete_other_native_rows(self):
        self.assertTrue(self.proof["proofs"]["lifecycle"]["complete"])
        self.assertTrue(self.proof["proofs"]["lifecycle"]["statement_identity_proven"])
        self.assertEqual(self.proof["proofs"]["native"]["joined_count"], 88)
        self.assertFalse(self.proof["proofs"]["native"]["complete"])
        self.assertGreater(self.proof["proofs"]["native"]["missing_count"], 0)
        self.assertFalse(self.proof["complete"])

    def test_static_templates_preserve_each_actual_phase_and_cold_cache_count(self):
        program = lifecycle_program(ROOT, RUNTIME)
        self.assertEqual({k: len(v) for k, v in program["profiles"].items()},
                         dict(before=20, after_migration=20, final_pre=11, final_post=9))
        joined = self.proof["proofs"]["native"]["joined_rows"]
        self.assertEqual(sum(v["protocol_commands"] for v in joined.values()), 88)
        self.assertFalse(program["read_wal_proven"])
        self.assertEqual(program["sql_executed"], 0)
        before = next(r for r in program["profiles"]["before"] if r["phase"] == "gates_before_catalog")
        after = next(r for r in program["profiles"]["after_migration"] if r["phase"] == "gates_after_migration_catalog")
        self.assertNotEqual(before["sql_sha256"], after["sql_sha256"])
        self.assertTrue(all(not r["runtime_values_observed"] for r in joined.values()))

    def test_preflight_uses_actual_history_and_each_cli_reader_exact_order(self):
        events = [e for e in self.normal["events"] if e.get("stage") == "dispatch"]
        preflight = [e for e in events if e.get("phase") == "preflight"]
        self.assertEqual(len(preflight), 4)
        self.assertTrue(all(e["source"].endswith("runtime_history.py") for e in preflight))
        self.assertEqual([e["actual_native_binding"]["index"] for e in preflight], list(range(4)))
        readers = [e for e in events if e["method"] == "snapshot"]
        self.assertEqual(len(readers), 24)
        self.assertTrue(all(e["reference_sql_sha256"] == e["actual_native_binding"]["statement_sha256"] for e in readers))

    def test_actual_binding_cannot_be_replaced_by_retained_sql_hash(self):
        normal = copy.deepcopy(self.normal)
        event = next(e for e in normal["events"] if e.get("actual_native_binding"))
        event["actual_native_binding"]["sql_sha256"] = "0" * 64
        proof = derive_release_joins(ROOT, RUNTIME, self.plan, normal)
        self.assertFalse(proof["proofs"]["lifecycle"]["complete"])

    def test_static_expression_language_cannot_import_or_dispatch(self):
        strings = Strings()
        for text in ("__import__('os')", "path.read_bytes()", "run('SELECT 1')", "(lambda: 1)()"):
            with self.assertRaises(ValueError):
                strings.expression(ast.parse(text, mode="eval").body, {})

    def test_static_expression_language_bounds_and_preserves_builder_strings(self):
        strings = Strings()
        value = strings.expression(ast.parse("','.join(k+':'+v for k,v in data.items())", mode="eval").body,
                                   dict(data={"x": "one", "y": "two"}))
        self.assertEqual(value, "x:one,y:two")
        with self.assertRaisesRegex(ValueError, "generator_bound"):
            strings.expression(ast.parse("','.join(x for x in rows)", mode="eval").body,
                               dict(rows=["x"] * 257))

    def test_actual_exception_prefixes_not_replaced_by_eight_command_probe(self):
        proof = self.proof["proofs"]["exception"]
        self.assertGreater(proof["missing_count"], 0)
        self.assertEqual(proof["workflow_finally"]["maxima"]["explicit_sql_slots"], 8)
        self.assertFalse(proof["complete"])

    def test_bootstrap_dispatch_join_keeps_local_root_cost_gate(self):
        proof = self.proof["proofs"]["bootstrap"]
        self.assertTrue(proof["complete"])
        self.assertTrue(proof["root_full_bound_required"])
        self.assertFalse(proof["counted_as_hosted_setup"])
        self.assertIsNone(proof["local_sql_upper_bound"])
        self.assertTrue(proof["fault_numeric_requires_original_complete_prefix"])
        self.assertTrue(proof["failure_closeout_separately_precharged"])
        self.assertFalse(proof["implicit_driver_zero_assumed"])
        early = proof["fault_prefix_source_program"]["cases"]
        self.assertEqual(set(early), {"pre_migration", "post_migration"})
        self.assertTrue(all(case["auth_context_permitted"] is False for case in early.values()))

    def test_missing_gate_instruction_is_rejected(self):
        changed = copy.deepcopy(self.before)
        ident = next(e["event_id"] for e in changed["events"]
                     if e.get("stage") == "dispatch" and e.get("selector", {}).get("action", "").startswith("gates_before_"))
        changed["events"] = [e for e in changed["events"] if e["event_id"] != ident]
        with self.assertRaisesRegex(ValueError, "count_changed"):
            bind_lifecycle(changed, runtime_dir=RUNTIME)

    def test_source_proofs_are_derived_not_fixed_four_missing_strings(self):
        path = pathlib.Path(__file__).with_name("admission_budget_current_release.py")
        tree = ast.parse(path.read_bytes())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_compile")
        self.assertFalse(any(isinstance(n, ast.keyword) and n.arg == "bound_complete"
                            and isinstance(n.value, ast.Constant) and n.value.value is False
                            for n in ast.walk(function)))
        self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                            and n.func.id == "derive_release_joins" for n in ast.walk(function)))


if __name__ == "__main__":
    unittest.main()
