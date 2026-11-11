"""Synthetic original-receipt fixtures only; no DB, process, Auth or CI calls."""
import ast
import json
import os
import pathlib
import shutil
import tempfile
import types
import unittest
import uuid

import admission_budget_bootstrap_prefix as prefix
from test_admission_budget_recovery_program import ROOT, RUNTIME

# Retained old-source contract fixtures, not the current Main producer.
HISTORICAL_ROOT = pathlib.Path(os.environ.get("A_BOOTSTRAP_HISTORICAL_ROOT",
    str(pathlib.Path(__file__).resolve().parent / "assembly_checks/historical"))).resolve(strict=True)
if os.name == "nt" and not str(HISTORICAL_ROOT).startswith("\\\\?\\"):
    # The verified historical fixture tree can exceed Windows' legacy path limit.
    text = str(HISTORICAL_ROOT)
    HISTORICAL_ROOT = pathlib.Path("\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\")
                                   else "\\\\?\\" + text)


class PrefixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = pathlib.Path(self.temp.name)
        self.sources = self.folder / "sources"
        for name, expected in prefix.PINS.items():
            dest = self.sources / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            self.assertEqual(prefix.sha((HISTORICAL_ROOT / name).read_bytes()), expected)
            shutil.copyfile(HISTORICAL_ROOT / name, dest)
        dest = self.sources / prefix.CLOSEOUT
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUNTIME / "runtime_bootstrap_closeout.py", dest)
        self.binding = dict(run_id=str(uuid.uuid4()), environment="disposable_ci",
            source_commit="a" * 40, ci_run="123", candidate_sha="b" * 64)
        self.identity = dict(source_commit=self.binding["source_commit"], ci_run="123",
                             candidate_sha256=self.binding["candidate_sha"])
        self.gate = types.SimpleNamespace(out=self.folder, sources=self.sources,
            result=dict(commit=self.binding["source_commit"], run_id="123",
                        candidate_sha256=self.binding["candidate_sha"]))

    def save(self, name, value):
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        (self.folder / name).write_bytes(raw)
        return dict(path=name, sha256=prefix.sha(raw), bytes=len(raw))

    def fixtures(self, case="pre_migration"):
        candidate = self.save("candidate.json", dict(sha256=self.binding["candidate_sha"], sources=prefix.PINS))
        self.save("case-stack-attempt.json", dict(**self.identity,
            candidate_manifest_sha256=candidate["sha256"], bootstrap_total_sql_commands=None))
        reservation = self.save("case-stack-reserve-native-before.json",
            dict(commands=list(prefix.LABELS), reserved=3))
        trace = []
        for label in prefix.LABELS:
            row = dict(stage="before", command=label, confirmed=True, reservation_ref=reservation)
            trace.append(row)
            self.save("case-stack-native-before-" + label + "-intent.json", {**row, "confirmed": False})
            self.save("case-stack-native-before-" + label + "-confirmed.json", row)
        self.save("case-stack-failure.json", dict(**self.identity, status="NO_GO", stage="canonical45",
            boundary_stage=prefix.STAGES[case], native_commands=trace, history_commands=[],
            admin_sql_reserved=0, admin_sql_confirmed=None))
        pre = self.save("migration-boundary-pre.json", {"simulation_only": True})
        self.save("case-stack-boundary-before45.json", dict(**self.identity, stage="before45", evidence_refs=[pre]))
        refs = [pre]
        if case == "post_migration":
            cli = self.save("cli-predispatch-canonical-45.json", {"simulation_only": True,
                "complete": True, "terminal": {"sql_dispatches": 14}})
            post = self.save("migration-boundary-post.json", {"simulation_only": True})
            refs = [cli, post]
            self.save("case-stack-boundary-after45.json", dict(**self.identity, stage="after45", evidence_refs=refs))
        fired = dict(case=case, run_id=self.binding["run_id"],
            source_commit=self.binding["source_commit"], ci_run="123", candidate_sha=self.binding["candidate_sha"],
            original_error_code="case_injected_" + case, automatic_retry=False,
            event=dict(stage=prefix.STAGES[case], evidence_refs=refs))
        self.save("case-fault-boundary.json", fired)
        self.fault = types.SimpleNamespace(case=case, binding=self.binding, fired=fired)
        self.args = dict(binding=self.binding, case_name=case, fault=self.fault)

    def test_source_order_includes_catalog_between_cli40_and41(self):
        program = prefix.source_program(self.sources)
        rows = program["cases"]["pre_migration"]["prefix"]
        ids = [r["command_id"] for r in rows]
        pos = ids.index("bootstrap.catalog.before41")
        self.assertEqual(ids[pos-1:pos+2], ["bootstrap.canonical.40", "bootstrap.catalog.before41",
                                          "bootstrap.canonical.41"])
        self.assertEqual(sum(r.get("cli_calls", 0) for r in rows), 44)
        self.assertEqual(sum(r["explicit_sql_commands"] or 0 for r in rows), 12)
        self.assertTrue(all(r["total_sql_commands"] is None for r in rows))

    def test_post_is_prefix_plus_canonical_and_post_boundary_without_app_or_auth(self):
        cases = prefix.source_program(self.sources)["cases"]
        before, after = cases["pre_migration"], cases["post_migration"]
        self.assertEqual(after["prefix"][:-2], before["prefix"])
        self.assertEqual([r["command_id"] for r in after["prefix"][-2:]],
                         ["bootstrap.canonical.45", "bootstrap.boundary.post"])
        self.assertEqual(after["source_known_explicit_sql_excluding_cli"], 20)
        for case in cases.values():
            self.assertIsNone(case["next_normal"])
            self.assertFalse(case["auth_context_permitted"])
            self.assertEqual(case["hosted_equivalent_sql_commands"], 0)
            self.assertIsNone(case["complete_upper_bound"])

    def test_prefix_audit_preserves_originals_without_numeric_promotion(self):
        self.fixtures()
        before = {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}
        audit = prefix.inspect_bootstrap_fault_prefix(self.gate, **self.args)
        self.assertEqual(audit["individually_confirmed_native_commands"], 3)
        self.assertIsNone(audit["observed_sql_commands"])
        self.assertFalse(audit["complete_numeric_prefix"])
        self.assertFalse(audit["failure_closeout_included"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()})
        self.assertIn("catalog_before41:original_wrapped_psql_dispatch_not_joined", audit["missing_costs"])
        for ref in audit["evidence_refs"]:
            self.assertEqual(prefix.sha(before[ref["path"]]), ref["sha256"])

    def test_declared_complete_and_total_cannot_replace_missing_protocol(self):
        self.fixtures()
        value = json.loads((self.folder / "case-stack-attempt.json").read_bytes())
        value.update(bootstrap_total_sql_commands=12, complete_numeric_prefix=True)
        self.save("case-stack-attempt.json", value)
        with self.assertRaisesRegex(prefix.PrefixBlocked, "bootstrap_prefix_incomplete") as caught:
            prefix.validate_bootstrap_fault_prefix(self.gate, **self.args)
        self.assertIsNone(caught.exception.report["observed_sql_commands"])

    def test_post_cli14_is_not_full_prefix(self):
        self.fixtures("post_migration")
        with self.assertRaises(prefix.PrefixBlocked) as caught:
            prefix.validate_bootstrap_fault_prefix(self.gate, **self.args)
        self.assertIn("canonical45:original_frontend_ledger_numeric_observers_isolation_replay_required",
                      caught.exception.report["missing_costs"])

    def test_lost_native_confirmation_rejected(self):
        self.fixtures()
        (self.folder / "case-stack-native-before-rollback-confirmed.json").unlink()
        with self.assertRaises(FileNotFoundError):
            prefix.inspect_bootstrap_fault_prefix(self.gate, **self.args)

    def test_changed_referenced_original_rejected(self):
        self.fixtures()
        self.save("migration-boundary-pre.json", {"simulation_only": False})
        with self.assertRaisesRegex(prefix.PrefixBlocked, "reference"):
            prefix.inspect_bootstrap_fault_prefix(self.gate, **self.args)

    def test_wrong_candidate_and_fault_binding_rejected(self):
        self.fixtures()
        self.gate.result["candidate_sha256"] = "c" * 64
        with self.assertRaisesRegex(prefix.PrefixBlocked, "gate_binding"):
            prefix.inspect_bootstrap_fault_prefix(self.gate, **self.args)

    def test_fault_cannot_move_before45_to_after45(self):
        self.fixtures()
        self.fault.fired["event"]["stage"] = "after45"
        with self.assertRaisesRegex(prefix.PrefixBlocked, "fault_original"):
            prefix.inspect_bootstrap_fault_prefix(self.gate, **self.args)

    def test_paths_duplicate_keys_and_member_limit_rejected(self):
        with self.assertRaises(prefix.PrefixBlocked):
            prefix._raw(self.folder, "../outside.json")
        (self.folder / "duplicate.json").write_text('{"n":1,"n":2}')
        with self.assertRaisesRegex(prefix.PrefixBlocked, "duplicate_json"):
            prefix.Originals(self.folder).read("duplicate.json")
        (self.folder / "big.json").write_bytes(b"x" * 1400001)
        with self.assertRaisesRegex(prefix.PrefixBlocked, "size"):
            prefix.Originals(self.folder).read("big.json")

    def test_closeout4_never_hides_driver_or_doublecounts_bootstrap(self):
        self.fixtures()
        literals = {n.targets[0].id: ast.literal_eval(n.value) for n in
            ast.parse((RUNTIME / "runtime_bootstrap_closeout.py").read_bytes()).body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in ("IDENTITY", "ACCOUNTS")}
        sql = ["BEGIN TRANSACTION READ ONLY", literals["IDENTITY"], literals["ACCOUNTS"], "ROLLBACK"]
        accounts = self.save("case-preauth-account-absence.json", dict(**self.identity,
            run_id=self.binding["run_id"], case_name="pre_migration", complete=True,
            rollback_confirmed=True, connection_closed=True,
            commands=[dict(ordinal=n, confirmed=True, sql_sha256=prefix.sha(text.encode()))
                      for n, text in enumerate(sql, 1)]))
        containers = self.save("case-preauth-container-absence.json", {"simulation_only": True})
        isolation = dict(run_id=self.binding["run_id"], auth_absence=dict(
            account_inventory_ref=accounts, container_inventory_ref=containers))
        with self.assertRaisesRegex(prefix.PrefixBlocked, "closeout_driver_incomplete") as caught:
            prefix.validate_bootstrap_failure_closeout(self.gate, **self.args, isolation=isolation, proof={})
        audit = caught.exception.report
        self.assertEqual(audit["explicit_sql_commands"], 4)
        self.assertEqual(audit["process_calls"], 3)
        self.assertIsNone(audit["driver_sql_commands"])
        self.assertIsNone(audit["observed_sql_commands"])
        self.assertFalse(audit["bootstrap_prefix_included"])


if __name__ == "__main__":
    unittest.main()
