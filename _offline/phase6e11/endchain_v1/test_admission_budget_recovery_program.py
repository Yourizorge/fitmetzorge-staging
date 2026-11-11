import pathlib
import os
import tempfile
import unittest

from admission_budget_recovery_program import RecoveryProgram, _functions

ROOT = pathlib.Path(__file__).resolve().parents[3]
RUNTIME = pathlib.Path(__file__).resolve().parent / "quota_candidate_v1"
# Test-only relocation for immutable same-source assemblies; pins still apply.
ROOT = pathlib.Path(os.environ.get("A_RECOVERY_SOURCE_ROOT", str(ROOT))).resolve(strict=True)
RUNTIME = pathlib.Path(os.environ.get("A_RECOVERY_RUNTIME_DIR", str(RUNTIME))).resolve(strict=True)


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = RecoveryProgram(ROOT, RUNTIME)

    def test_actual_four_rollbacks_then_compare_restore(self):
        trace = self.program.trace()
        self.assertEqual(trace["explicit_sql_slots"], 8)
        self.assertEqual([r["safety_label"] for r in trace["commands"][:4]],
                         ["rollback_" + c for c in ("setup", "writer", "reader", "workflow")])
        self.assertEqual([r["phase"] for r in trace["commands"][4:]],
                         ["safety_control_before", "safety_control_restore", "safety_control_restore", "safety_control_after"])

    def test_no_sql_before_actual_worker_reap(self):
        trace = self.program.trace(worker="stuck")
        self.assertEqual(trace["explicit_sql_slots"], 0)
        self.assertFalse(trace["outcome"]["worker_terminated"])

    def test_unknown_transaction_state_is_not_treated_active_or_idle(self):
        trace = self.program.trace(states=("unreadable",)*4, controls=False)
        self.assertEqual(trace["explicit_sql_slots"], 0)
        self.assertTrue(trace["outcome"]["secondary"])

    def test_lost_rollback_does_not_replay_same_channel(self):
        normal = self.program.trace()
        index = next(i for i, e in enumerate(normal["events"]) if e["label"] == "setup:safety_rollback")
        trace = self.program.trace(failure=index)
        self.assertEqual(sum(r["phase"] == "safety_rollback" and r["channel"] == "setup"
                             for r in trace["commands"]), 1)
        self.assertFalse(trace["commands"][0]["confirmed"])

    def test_foreign_controls_prevent_mutation(self):
        trace = self.program.trace(foreign_controls=True)
        self.assertEqual(trace["explicit_sql_slots"], 5)
        self.assertFalse(any(r["phase"] == "safety_control_restore" for r in trace["commands"]))

    def test_no_implicit_connection_cost_assumed_zero(self):
        result = self.program.enumerate()
        self.assertEqual(result["base_states"], 56320)
        self.assertEqual(result["worker_watchdog_profiles"], 55)
        self.assertEqual({k: result["maxima"][k] for k in
            ("explicit_sql_slots", "connection_open_attempts", "connection_close_attempts")},
            dict(explicit_sql_slots=8, connection_open_attempts=1, connection_close_attempts=5))
        self.assertGreater(result["maxima"]["process_calls"], 5)
        self.assertGreater(result["maxima"]["worker_prefix_process_calls"], 0)
        self.assertGreater(result["maxima"]["filesystem_calls"], 0)
        self.assertIsNone(result["full_sql_upper_bound"])
        self.assertFalse(result["additional_parent_charge"])
        self.assertFalse(result["actual_execution_evidence"])

    def test_actual_wait_class_and_original_save_are_executed(self):
        trace = self.program.trace()
        self.assertTrue(trace["worker_evidence_branch"])
        self.assertTrue(trace["worker_known"])
        self.assertEqual(trace["worker_wait"], trace["saved_worker_wait"])
        labels = [e["label"].split(":", 1)[1] for e in trace["events"]
                  if e["label"].startswith("workflow-worker-wait.json:")]
        self.assertEqual(labels, ["root_resolve", "exists", "canonicalize", "exclusive_open", "fdopen",
            "write", "flush", "fsync", "seek", "readback", "fstat", "named_stat", "is_symlink",
            "member_resolve", "close"])
        self.assertIn("worker_wait_ref", trace["outcome"])
        self.assertFalse(trace["actual_execution_evidence"])

    def test_every_original_save_failure_is_incomplete_without_retry(self):
        normal = self.program.trace()
        indices = [i for i, e in enumerate(normal["events"])
                   if e["label"].startswith("workflow-worker-wait.json:")]
        for index in indices:
            for edge in ("before", "after"):
                with self.subTest(label=normal["events"][index]["label"], edge=edge):
                    trace = self.program.trace(failure=index, edge=edge)
                    self.assertIsNone(trace["saved_worker_wait"])
                    self.assertNotIn("worker_wait_ref", trace["outcome"])
                    self.assertFalse(trace["outcome"]["complete"])
                    self.assertTrue(trace["original_failure_preserved"])
                    self.assertIn("worker_wait", [r["stage"] for r in trace["outcome"]["secondary"]])
                    self.assertLessEqual(trace["explicit_sql_slots"], 8)
                    self.assertLessEqual(trace["connection_open_attempts"], 1)
                    self.assertLessEqual(trace["connection_close_attempts"], 5)
                    self.assertLessEqual(sum(e["label"].endswith(":exclusive_open") for e in trace["events"]), 1)

    def test_later_reap_does_not_erase_prior_wait_timeout(self):
        trace = self.program.trace(worker="wait_timeout")
        self.assertTrue(trace["worker_wait"]["reaped"])
        self.assertEqual(trace["worker_wait"]["wait_error_class"], "ProbeFailure")
        self.assertFalse(trace["worker_known"])
        self.assertFalse(trace["outcome"]["complete"])
        self.assertEqual(trace["explicit_sql_slots"], 8)
        self.assertEqual(trace["worker_prefix_process_calls"], 2)

    def test_cleanup_failure_without_primary_raises_and_retains_receipt(self):
        trace = self.program.trace(worker="pipe_error", primary_failure=False)
        self.assertEqual(trace["raised_exception_class"], "RuntimeError")
        self.assertFalse(trace["outcome"]["complete"])
        self.assertIsNone(trace["outcome"]["primary_exception_class"])
        self.assertIsNone(trace["original_failure_preserved"])

    def test_prefix_and_recovery_process_calls_have_one_total(self):
        trace = self.program.trace(worker="wait_timeout", watchdog="fired")
        self.assertEqual(trace["total_process_calls"],
                         trace["process_calls"] + trace["worker_prefix_process_calls"])

    def test_unreaped_or_unknown_exit_never_allows_sql(self):
        for worker in ("stuck", "wait_unknown", "kill_error"):
            with self.subTest(worker=worker):
                trace = self.program.trace(worker=worker)
                self.assertFalse(trace["worker_wait"]["reaped"])
                self.assertFalse(trace["outcome"]["complete"])
                self.assertEqual(trace["explicit_sql_slots"], 0)

    def test_watchdog_faults_remain_unknown_after_reap(self):
        for state in ("fired", "alive", "unknown", "join_error", "deadline"):
            with self.subTest(watchdog=state):
                trace = self.program.trace(watchdog=state)
                self.assertTrue(trace["worker_wait"]["reaped"])
                self.assertFalse(trace["worker_known"])
                self.assertFalse(trace["outcome"]["complete"])
                self.assertTrue(trace["original_failure_preserved"])

    def test_pipe_close_failure_keeps_wait_and_incomplete_outcome(self):
        trace = self.program.trace(worker="pipe_error")
        self.assertTrue(trace["worker_wait"]["wait_completed"])
        self.assertEqual(trace["worker_wait"]["termination_error_class"], "ProbeFailure")
        self.assertFalse(trace["outcome"]["complete"])

    def test_legacy_branch_is_still_separate(self):
        trace = self.program.trace(worker_evidence=False)
        self.assertIsNone(trace["worker_wait"])
        self.assertNotIn("worker_wait_ref", trace["outcome"])
        self.assertEqual(trace["explicit_sql_slots"], 8)
        self.assertEqual(trace["process_calls"], 5)

    def test_source_change_denied_before_executing_class(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "runtime_worker_evidence.py"
            path.write_bytes(b"raise AssertionError('must_not_execute')\n")
            with self.assertRaisesRegex(ValueError, "source_changed"):
                _functions(path, ("WaitEvidence",), {})


if __name__ == "__main__":
    unittest.main()
