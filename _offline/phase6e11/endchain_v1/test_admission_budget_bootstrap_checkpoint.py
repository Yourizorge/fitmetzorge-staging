"""Synthetic source-drift receipts; no protocol or DB execution."""
import pathlib
import os
import ast
import copy
import hashlib
import tempfile
import unittest
import sys
from unittest.mock import patch

import admission_budget_bootstrap_prefix as prefix


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = pathlib.Path(self.temp.name)
        self.path = self.folder / prefix.BOOTSTRAP
        self.path.parent.mkdir(parents=True)
        self.raw = b"# synthetic source fixture\n"
        self.path.write_bytes(self.raw)
        self.pins = {prefix.BOOTSTRAP: prefix.sha(self.raw)}
        self.override = patch.object(prefix, "PINS", self.pins)
        self.override.start()
        self.addCleanup(self.override.stop)

    def test_missing_producer_is_not_numeric_zero(self):
        result = prefix.inspect_source_checkpoint(self.folder)
        self.assertTrue(result["reviewed_prefix_sources_match"])
        self.assertIn("missing_source:" + prefix.PREFIX_PRODUCER, result["missing_inputs"])
        self.assertIsNone(result["numeric_total"])
        self.assertFalse(result["positive_prefix_validator_available"])

    def test_new_file_presence_never_approves_it(self):
        path = self.folder / prefix.PREFIX_PRODUCER
        path.parent.mkdir(parents=True)
        path.write_bytes(b"# no coverage\n")
        result = prefix.inspect_source_checkpoint(self.folder)
        self.assertIn("new_producer_not_reviewed_or_numerically_verified:" + prefix.PREFIX_PRODUCER,
                      result["missing_inputs"])
        self.assertFalse(result["bound_complete"])
        self.assertFalse(result["runtime_admitted"])

    def test_changed_source_exception_contains_exact_hashes_no_body(self):
        self.path.write_bytes(b"# changed fixture\n")
        with self.assertRaisesRegex(prefix.PrefixBlocked, "source_changed") as caught:
            prefix.source_program(self.folder)
        report = caught.exception.report
        self.assertEqual(report["files"][0]["expected_sha256"], self.pins[prefix.BOOTSTRAP])
        self.assertEqual(report["files"][0]["actual_sha256"], prefix.sha(b"# changed fixture\n"))
        self.assertFalse(report["reviewed_prefix_sources_match"])
        self.assertNotIn("changed fixture", str(report))

    def test_missing_reviewed_source_not_hidden(self):
        self.pins[prefix.HARNESS] = "a"*64
        result = prefix.inspect_source_checkpoint(self.folder)
        self.assertFalse(result["reviewed_prefix_sources_match"])
        self.assertIn("missing_source:" + prefix.HARNESS, result["missing_inputs"])


class FrozenPolicyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(os.environ.get("A_BOOTSTRAP_POLICY_ROOT",
            str(pathlib.Path(__file__).resolve().parents[3]))).resolve(strict=True)
        cls.report = prefix.inspect_canonical_policy_inventory(cls.root)

    def test_all_44_frozen_files_and_actual_body_counts(self):
        rows = self.report["migrations"]
        self.assertEqual([r["ordinal"] for r in rows], list(range(1, 45)))
        self.assertEqual(sum(r["body_statement_count"] for r in rows), 1552)
        self.assertEqual(sum(r["declared_cli_policy_cap"] for r in rows), 2256)
        self.assertTrue(all(r["declared_cli_policy_cap"] == r["body_statement_count"] + 16 for r in rows))

    def test_local_reservation_never_becomes_hosted_total_or_full_bound(self):
        report = self.report
        self.assertIsNone(report["total_hosted_equivalent_upper_bound"])
        self.assertIsNone(report["total_local_ci_upper_bound"])
        self.assertIsNone(report["observed_commands"])
        self.assertIsNone(report["minimal_cap"])
        self.assertFalse(report["bound_complete"])
        self.assertEqual(report["hosted_limit"], 2349)
        self.assertFalse(report["frozen_reference_is_authorization"])

    def test_raw_identity_and_parser_provenance_not_execution(self):
        report = self.report
        for row in report["migrations"]:
            self.assertEqual(report["source_hashes"][row["path"]], row["sha256"])
        self.assertFalse(report["parser"]["cli_parser_equivalence_proven"])
        self.assertFalse(report["actual_execution_evidence"])
        self.assertEqual(len(report["parser"]["binary_sha256"]), 64)

    def test_policy_drift_denied_before_any_promotion(self):
        with patch.object(prefix, "POLICY_SHA", "f"*64):
            with self.assertRaisesRegex(prefix.PrefixBlocked, "policy_source_changed"):
                prefix.inspect_canonical_policy_inventory(self.root)

    def test_manifest_drift_denied(self):
        with patch.object(prefix, "FROZEN_MANIFEST_SHA", "f"*64):
            with self.assertRaisesRegex(prefix.PrefixBlocked, "frozen_manifest_changed"):
                prefix.inspect_canonical_policy_inventory(self.root)


class ActualEntryBindingTests(unittest.TestCase):
    def test_d_delta_is_only_fresh_case_guard_and_run_id_argument(self):
        from test_admission_budget_recovery_program import RUNTIME
        from admission_budget_release_joins import PINS
        tree = ast.parse((RUNTIME / "runtime_case_entry.py").read_bytes())
        method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute_bootstrap")
        self.assertEqual(hashlib.sha256(ast.dump(method, include_attributes=False).encode()).hexdigest(),
                         PINS["runtime_case_entry.py:execute_bootstrap"])
        charge = next(i for i, n in enumerate(method.body) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "active" for t in n.targets))
        leading = method.body[1:charge]
        self.assertTrue(any(isinstance(n, ast.Name) and n.id == "parsed" for s in leading for n in ast.walk(s)))
        calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == "bootstrap"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.dump(next(k.value for k in calls[0].keywords if k.arg == "run_id")),
                         ast.dump(ast.Name(id="run_id", ctx=ast.Load())))
        retained = copy.deepcopy(method)
        retained.body = retained.body[:1] + retained.body[charge:]
        for node in ast.walk(retained):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bootstrap":
                node.keywords = [k for k in node.keywords if k.arg != "run_id"]
        self.assertEqual(hashlib.sha256(ast.dump(retained, include_attributes=False).encode()).hexdigest(),
                         "a633f6911d1f12123e2f66958d8eb8861777695651a4af210f0abd22e67bc5b8")

if __name__ == "__main__":
    unittest.main()
