"""Synthetic original bytes only; no admission, SQL, processes or networking."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
import uuid
from unittest.mock import patch

import admission_budget_root_runtime as root
import admission_budget_root_replay as replay


def row(name, units=1, reserve=0, hosted=None, **extra):
    return dict(command_id=name, units=units, reserve_after=reserve, domain="unit_local",
        hosted_units=units if hosted is None else hosted,
        hosted_reserve_after=reserve if hosted is None else 0, **extra)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gate = types.SimpleNamespace(out=pathlib.Path(self.temp.name))
        self.binding = dict(run_id=str(uuid.uuid4()), candidate_sha="b"*64, source_commit="c"*40,
                            ci_run="123", environment="disposable_ci")
        self.sources = {"unit_source.py": "a"*64}

    def start(self, program):
        _, _, local, hosted = root._program(program)
        self.register = dict(executable_program=program, source_hashes=self.sources,
            bound_complete=True, prefix_reserves_complete=True, source_inventory_complete=True,
            hosted_scope_complete=True, missing_costs=[], hosted_limit=2349,
            total_local_ci_upper_bound=local, total_hosted_equivalent_upper_bound=hosted)
        self.register["full_register_sha256"] = root.digest(self.register)
        self.evidence = root._register_evidence(self.gate.out, self.register, self.binding)
        self.ledger = root._Ledger(root._KEY, self.gate, program=program, binding=self.binding,
            register_sha256=self.register["full_register_sha256"])
        return self.ledger

    def capture(self):
        self.refs = dict(evidence_refs=self.evidence, journal_refs=self.ledger.journal_refs())
        self.originals = {r["path"]: (self.gate.out / r["path"]).read_bytes()
                          for r in self.evidence + self.refs["journal_refs"]}

    def verify(self, **args):
        values = dict(trusted_root=self.register, expected_sources=self.sources,
                      binding=self.binding, root_refs=self.refs)
        values.update(args)
        return replay.verify_exported_root(self.originals, **values)

    def normal(self):
        ledger = self.start([row("one", 3, 2), row("two", 2)])
        ledger.confirm(ledger.precharge("one"), observed_sql_commands=2)
        ledger.confirm(ledger.precharge("two"), observed_sql_commands=1)
        ledger.close()
        self.capture()

    def rewrite_journal(self, mutate, name="root-ledger-private.ledger.txt"):
        values = [json.loads(line) for line in self.originals[name].splitlines()]
        mutate(values)
        raw = b""
        for index, value in enumerate(values, 1):
            value.update(sequence=index, previous_bytes_sha256=replay.sha(raw))
            raw += (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.originals[name] = raw
        ref = next(r for r in self.refs["journal_refs"] if r["path"] == name)
        ref.update(sha256=replay.sha(raw), size=len(raw))

    def test_normal_pure_replay_no_runtime_construction_or_io(self):
        self.normal()
        with patch.object(root, "_Ledger", side_effect=AssertionError("no ledger")), \
             patch.object(pathlib.Path, "read_bytes", side_effect=AssertionError("no disk")):
            result = self.verify()
        self.assertEqual(result["status"], "NUMERIC_ACCOUNTING_REPLAYED")
        self.assertEqual(result["root"]["observed_sql_commands"], 3)
        self.assertEqual(result["root"]["reserved_consumed"], 5)
        for key in ("runtime_admitted", "hosted_admitted", "full_chain_admission",
                    "observed_execution_independently_proven", "source_semantics_independently_proven"):
            self.assertFalse(result[key])

    def test_local_cost_can_exceed_2349_without_changing_hosted_scope(self):
        ledger = self.start([row("local", 5000, hosted=0)])
        ledger.confirm(ledger.precharge("local"), observed_sql_commands=4900)
        ledger.close()
        self.capture()
        result = self.verify()["root"]
        self.assertEqual(result["reserved_consumed"], 5000)
        self.assertEqual(result["hosted_equivalent_reserved"], 0)

    def test_missing_complete_bound_never_promoted(self):
        self.normal()
        for field in ("bound_complete", "prefix_reserves_complete", "source_inventory_complete",
                      "hosted_scope_complete"):
            with self.subTest(field=field), self.assertRaisesRegex(root.RootBlocked, "trusted_bound"):
                self.verify(trusted_root=dict(self.register, **{field: False}))

    def test_source_drift_rejected(self):
        self.normal()
        with self.assertRaisesRegex(root.RootBlocked, "source_binding"):
            self.verify(expected_sources={"unit_source.py": "d"*64})

    def test_wrong_binding_rejected(self):
        self.normal()
        with self.assertRaisesRegex(root.RootBlocked, "original_trusted_binding"):
            self.verify(binding=dict(self.binding, run_id=str(uuid.uuid4())))

    def test_preparation_uuid_not_a_case(self):
        self.normal()
        with self.assertRaisesRegex(root.RootBlocked, "fresh_case_binding"):
            self.verify(binding=dict(self.binding, run_id="11a909f4-7113-424a-aa4b-ce9964720a3e"))

    def test_changed_raw_bytes_rejected(self):
        self.normal()
        self.originals["root-ledger-private.ledger.txt"] += b"\n"
        with self.assertRaisesRegex(root.RootBlocked, "original_bytes"):
            self.verify()

    def test_chunk_order_rejected(self):
        self.normal()
        self.refs["evidence_refs"].reverse()
        with self.assertRaisesRegex(root.RootBlocked, "chunk_order"):
            self.verify()

    def test_path_escape_rejected(self):
        self.normal()
        self.refs["journal_refs"][0]["path"] = "../root-ledger-private.ledger.txt"
        with self.assertRaisesRegex(root.RootBlocked, "member_name"):
            self.verify()

    def test_duplicate_reference_rejected(self):
        self.normal()
        self.refs["journal_refs"].append(self.refs["journal_refs"][0])
        with self.assertRaisesRegex(root.RootBlocked, "member_name_or_duplicate"):
            self.verify()

    def test_numeric_boolean_rejected_even_rehashed(self):
        self.normal()
        self.rewrite_journal(lambda values: values[1]["event"].update(observed_sql_commands=True))
        with self.assertRaisesRegex(root.RootBlocked, "numeric_count"):
            self.verify()

    def test_truthy_integer_cannot_replace_numeric_confirmed_boolean(self):
        self.normal()
        self.rewrite_journal(lambda values: values[1]["event"].update(numeric_confirmed=1))
        with self.assertRaisesRegex(root.RootBlocked, "event_changed"):
            self.verify()

    def test_boolean_cannot_replace_bound_instruction_unit(self):
        ledger = self.start([row("one", 1)])
        ledger.confirm(ledger.precharge("one"), observed_sql_commands=1)
        ledger.close()
        self.capture()
        self.rewrite_journal(lambda values: values[0]["event"].update(units=True))
        with self.assertRaisesRegex(root.RootBlocked, "precharge_instruction"):
            self.verify()

    def test_omitted_precharge_rejected_even_rehashed(self):
        self.normal()
        self.rewrite_journal(lambda values: values.pop(0))
        with self.assertRaisesRegex(root.RootBlocked, "precharge_instruction"):
            self.verify()

    def test_forged_totals_rejected_even_rehashed(self):
        self.normal()
        self.rewrite_journal(lambda values: values[1].update(observed_sql_commands=1))
        with self.assertRaisesRegex(root.RootBlocked, "totals_or_fault_changed"):
            self.verify()

    def test_command_order_rejected_even_rehashed(self):
        self.normal()
        self.rewrite_journal(lambda values: values[0]["event"].update(command_id="two"))
        with self.assertRaisesRegex(root.RootBlocked, "precharge_instruction"):
            self.verify()

    def test_closed_record_required(self):
        self.normal()
        self.rewrite_journal(lambda values: values.pop())
        with self.assertRaisesRegex(root.RootBlocked, "not_closed"):
            self.verify()

    def test_record_after_close_rejected(self):
        self.normal()
        self.rewrite_journal(lambda values: values.append(copy.deepcopy(values[-1])))
        with self.assertRaisesRegex(root.RootBlocked, "record_after_close"):
            self.verify()

    def test_duplicate_terminal_rejected(self):
        self.normal()
        self.rewrite_journal(lambda values: values.insert(2, copy.deepcopy(values[1])))
        with self.assertRaisesRegex(root.RootBlocked, "duplicate_terminal_update"):
            self.verify()

    def test_numeric_fault_preserved_not_success(self):
        program = dict(entry="main", events=[
            row("main", 5, 2, next_confirmed=None, next_unknown="cleanup", safety_only=False),
            row("cleanup", 2, next_confirmed=None, next_unknown=None, safety_only=True)])
        ledger = self.start(program)
        ledger.fault(ledger.precharge("main"), observed_sql_commands=3)
        ledger.confirm(ledger.precharge("cleanup"), observed_sql_commands=2)
        ledger.close()
        self.capture()
        self.assertTrue(self.verify()["root"]["fault_retained"])

    def test_unknown_never_becomes_numeric_by_close(self):
        ledger = self.start([row("main", 5)])
        ledger.unknown(ledger.precharge("main"), reason="lost_response")
        ledger.close()
        self.capture()
        with self.assertRaisesRegex(root.RootBlocked, "unknown_or_failed_consumption"):
            self.verify()

    def group(self, fault=False):
        program = dict(entry="managed", events=[
            row("managed", 10, 2, defer=True, observation_units=8, observation_group="group",
                next_confirmed="stop", next_unknown="stop", safety_only=False),
            row("stop", 2, defer=True, observation_group="group",
                next_confirmed=None, next_unknown=None, safety_only=True)])
        ledger = self.start(program)
        first = ledger.precharge("managed")
        method = ledger.defer_fault if fault else ledger.defer
        method(first, partial_observed_sql_commands=1)
        second = ledger.precharge("stop")
        ledger.defer(second)
        ledger.settle_union([first, second], observed_sql_commands=7)
        ledger.close()
        self.capture()

    def test_union_counts_once_and_native_partition_stays(self):
        self.group()
        result = self.verify()["root"]
        self.assertEqual(result["observed_sql_commands"], 8)
        self.assertEqual(len(result["numeric_unions"]), 1)

    def test_deferred_fault_preserved_after_numeric_union(self):
        self.group(fault=True)
        self.assertTrue(self.verify()["root"]["fault_retained"])

    def test_missing_union_member_rejected_even_rehashed(self):
        self.group()
        self.rewrite_journal(lambda values: values.pop(-2))
        with self.assertRaisesRegex(root.RootBlocked, "close_before_terminal|union_incomplete|unsettled"):
            self.verify()

    def test_union_repeated_charge_rejected_even_rehashed(self):
        self.group()
        self.rewrite_journal(lambda values: values[-2].update(observed_sql_commands=15))
        with self.assertRaisesRegex(root.RootBlocked, "totals_or_fault_changed"):
            self.verify()

    def test_partial_observation_retained_for_individual_settle(self):
        ledger = self.start([row("managed", 10, defer=True, observation_units=8)])
        ticket = ledger.precharge("managed")
        ledger.defer(ticket, partial_observed_sql_commands=2)
        ledger.settle_deferred(ticket, observed_sql_commands=6)
        ledger.close()
        self.capture()
        self.assertEqual(self.verify()["root"]["observed_sql_commands"], 8)

    def nested(self):
        ledger = self.start([row("outer", 8, children=[row("inner", 3)])])
        ticket, child = ledger.open_envelope("outer")
        child.confirm(child.precharge("inner"), observed_sql_commands=2)
        child.close()
        ledger.close_envelope(ticket, child, observed_sql_commands=4)
        ledger.close()
        self.capture()

    def test_children_are_covered_not_added(self):
        self.nested()
        result = self.verify()
        self.assertEqual(result["journal_count"], 2)
        self.assertEqual(result["root"]["observed_sql_commands"], 4)
        self.assertEqual(result["root"]["children"][0]["observed_sql_commands"], 2)

    def test_missing_child_rejected(self):
        self.nested()
        self.refs["journal_refs"].pop()
        with self.assertRaisesRegex(root.RootBlocked, "child_journal"):
            self.verify()

    def test_child_requires_original_close(self):
        self.nested()
        name = self.refs["journal_refs"][1]["path"]
        self.rewrite_journal(lambda values: values.pop(), name)
        with self.assertRaisesRegex(root.RootBlocked, "not_closed"):
            self.verify()

    def test_parent_cannot_undercount_child(self):
        self.nested()
        self.rewrite_journal(lambda values: values[1]["event"].update(observed_sql_commands=1))
        with self.assertRaisesRegex(root.RootBlocked, "child_numeric_coverage"):
            self.verify()

    def test_selection_uses_bound_actual_state_branch(self):
        state = {"unit_state": True}
        program = dict(entry="normal", events=[
            row("normal", 1, 2, next_confirmed="select", next_unknown="select", safety_only=False),
            row("auth.cleanup.select", 0, 2, node_id="select", next_confirmed=None,
                next_unknown=None, safety_only=True, selection_cases={root.digest(state): "cleanup"}),
            row("cleanup", 2, next_confirmed=None, next_unknown=None, safety_only=True)])
        ledger = self.start(program)
        ledger.confirm(ledger.precharge("normal"), observed_sql_commands=1)
        ledger._select_cleanup_state(root._KEY, state)
        ledger.confirm(ledger.precharge("cleanup"), observed_sql_commands=2)
        ledger.close()
        self.capture()
        self.assertEqual(self.verify()["root"]["observed_sql_commands"], 3)
        self.rewrite_journal(lambda values: values[3]["event"]["cleanup_state"].update(unit_state=False))
        with self.assertRaisesRegex(root.RootBlocked, "cleanup_selection"):
            self.verify()

    def test_duplicate_json_key_denied(self):
        with self.assertRaisesRegex(root.RootBlocked, "duplicate_json_key"):
            replay._json(b'{"value":1,"value":2}')

    def test_nonfinite_json_denied(self):
        with self.assertRaisesRegex(root.RootBlocked, "nonfinite_json"):
            replay._json(b'{"value":NaN}')

    def test_extra_detached_journal_denied(self):
        self.normal()
        ref = dict(self.refs["journal_refs"][0], path="root-ledger-" + "a"*24 + ".ledger.txt")
        self.originals[ref["path"]] = self.originals["root-ledger-private.ledger.txt"]
        self.refs["journal_refs"].append(ref)
        with self.assertRaisesRegex(root.RootBlocked, "unattached_journal"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
