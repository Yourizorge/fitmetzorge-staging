"""Source assembly and admission denial tests only; no Auth or DB execution."""
import copy
import pathlib
import types
import unittest
from unittest.mock import patch

import admission_budget_auth_diagnostic as diagnostic
import admission_budget_root_runtime as root
from test_admission_budget_recovery_program import ROOT, RUNTIME


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home = RUNTIME.parents[1]
        cls.context = home / "agent-b-tracked-context-20261103/quota_candidate_v1"
        cls.dependencies = {root.PREFIX + "auth_failure_parent_finalizer.py":
                home / "agent-b-tracked-context-20261103" / root.PREFIX / "auth_failure_parent_finalizer.py",
                root.PREFIX + "admission_auth_runtime_profile.py":
                    home / "agent-c-auth-runtime-profile-20261103/admission_auth_runtime_profile.py",
                root.PREFIX + "quota_candidate_v1/runtime_registered_fixture_closeout.py":
                    home / "agent-c-registered-fixture-closeout-20261103/quota_candidate_v1/runtime_registered_fixture_closeout.py",
                root.PREFIX + "install_platform.py": home / "agent-a1-platform-install-20261104/install_platform.py"}
        cls.report = diagnostic.build_auth_failure_register(ROOT, runtime_dir=RUNTIME,
            context_dir=cls.context, dependency_paths=cls.dependencies)

    def test_old_engine_missing_read_witness_is_explicit_not_silent_join(self):
        self.assertFalse(self.report["engine_interface"]["compatible"])
        self.assertEqual(self.report["engine_interface"]["missing_keywords"], ["read_witness"])
        self.assertIn("auth.failure_component:engine_run_missing_keywords:read_witness",
                      self.report["missing_costs"])

    def test_saved_b_engine_binds_exact_override_without_completing_bound(self):
        engine = RUNTIME.parents[1] / "agent-b-registered-auth-delivery-20261104-v2" / root.PREFIX / "auth_failure.py"
        report = diagnostic.build_auth_failure_register(ROOT, runtime_dir=RUNTIME,
            context_dir=self.context, dependency_paths={**self.dependencies, root.PREFIX + "auth_failure.py": engine})
        self.assertTrue(report["engine_interface"]["compatible"])
        self.assertEqual(report["source_hashes"][root.PREFIX + "auth_failure.py"],
                         "cef5c102f726c672e3dafea05835f19549c355a15825375bf094eb31f89e8f02")
        self.assertFalse(report["bound_complete"])
        self.assertIsNone(report["executable_program"])

    def test_own_envelope_exact_eleven_and_all_local_setup_visible(self):
        report = self.report
        self.assertEqual(report["cases"], list(diagnostic.CASES))
        self.assertEqual(report["root_order"], ["case.platform.install", "case.bootstrap.clean47",
                                              "case.auth.failures", "case.terminal"])
        self.assertEqual(report["hosted_limit"], 2349)
        self.assertEqual(report["total_hosted_equivalent_upper_bound"], 0)
        self.assertIsNone(report["total_local_ci_upper_bound"])

    def test_no_parent_users_fixture_core_or_borrowed_normal_rows(self):
        ids = [r["command_id"] for r in self.report["context_order"]]
        self.assertFalse(any(i.startswith(("auth.create.", "auth.seed.", "case.core")) for i in ids))
        self.assertNotIn("auth.parent_cleanup", ids)
        self.assertNotIn("auth.fixture_closeout", ids)
        self.assertEqual(self.report["parent_users_created"], 0)
        self.assertEqual(self.report["parent_cleanup_sql"], 0)

    def test_derived_reservation_not_promoted_or_reconciliation_hidden(self):
        row = next(r for r in self.report["context_order"] if r["command_id"] == "auth.failure_component")
        self.assertEqual(row["declared_reservation"], 5764)
        self.assertEqual(row["native_sql_capacity"], 138)
        self.assertEqual(row["reconciliation_native_capacity"], 6)
        self.assertEqual(row["http_capacity"], 45)
        self.assertIsNone(row["units"])
        self.assertEqual(row["observation_group"], root.MANAGED_OBSERVATION_GROUP)
        self.assertFalse(self.report["bound_complete"])

    def test_registry_drain_precedes_stop_and_all_fault_prefixes_retain_unknown(self):
        ids = [r["command_id"] for r in self.report["context_order"]]
        self.assertLess(ids.index("auth.cleanup.select"), ids.index("auth.failure_registry_close"))
        self.assertLess(ids.index("auth.failure_registry_close"), ids.index("auth.auth_stop"))
        for fault in self.report["fault_prefixes"]:
            self.assertEqual(fault["retained_prefix"][-1], fault["after_instruction"])
            self.assertTrue(fault["unknown_retained"])
            self.assertEqual(fault["refund"], 0)
            self.assertIsNone(fault["reserve"])

    def test_hash_covers_actual_whole_register(self):
        report = copy.deepcopy(self.report)
        expected = report.pop("full_register_sha256")
        self.assertEqual(root.digest(report), expected)

    def test_public_opener_cannot_borrow_normal_admission_or_caller_flags(self):
        gate = types.SimpleNamespace(sources="unit")
        prepared = diagnostic.PreparedAuthFailureExecution(diagnostic.KEY, gate, {}, self.report)
        advertised = prepared.report
        advertised.update(bound_complete=True, source_inventory_complete=True, missing_costs=[])
        with patch.object(diagnostic, "build_auth_failure_register", return_value=self.report):
            with self.assertRaisesRegex(root.RootBlocked, "bound_incomplete"):
                diagnostic.open_auth_failure_ledger(gate, prepared=prepared)
            with self.assertRaisesRegex(root.RootBlocked, "prepared_owner"):
                diagnostic.open_auth_failure_ledger(gate, prepared=prepared)

    def test_normal_or_ducktyped_owner_rejected(self):
        with self.assertRaisesRegex(root.RootBlocked, "prepared_owner"):
            diagnostic.open_auth_failure_ledger(types.SimpleNamespace(), prepared=types.SimpleNamespace(
                report={"bound_complete": True, "runtime_admitted": True}))


if __name__ == "__main__":
    unittest.main()
