"""Actual A ledger union mechanics; no DB, HTTP, Docker or runtime admission."""
import pathlib
import tempfile
import types
import unittest
import uuid

import test_runtime_registered_bootstrap as base
import admission_budget_root_runtime as root
from quota_candidate_v1 import runtime_registered_bootstrap as b


def program(items):
    suffix = 0
    rows = []
    for name, units, observation in reversed(items):
        row = {"command_id": name, "units": units, "reserve_after": suffix,
               "domain": "local_ci_test", "hosted_units": 0, "hosted_reserve_after": 0}
        if observation is not None:
            row.update(defer=True, observation_units=observation,
                       observation_group=root.MANAGED_OBSERVATION_GROUP)
        elif name == "driver":
            row.update(defer=True)
        rows.append(row)
        suffix += units
    return list(reversed(rows)), suffix


class UnionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gate = types.SimpleNamespace(out=pathlib.Path(self.temp.name))
        self.binding = {"run_id": str(uuid.uuid4())}

    def make(self, driver=False, unknown_core=False):
        items = [("native", 1, None), ("auth.auth_start", 6, 6), ("case.core", 12, 10)]
        if driver: items.append(("driver", 2, None))
        children, units = program(items)
        parent, _ = program([("case.auth.context", units, None)])
        parent[0]["children"] = children
        ledger = root._Ledger(root._KEY, self.gate, program=parent, binding=self.binding,
                              register_sha256="a"*64)
        envelope, child = ledger.open_envelope("case.auth.context")
        ticket = child.precharge("native")
        child.confirm(ticket, observed_sql_commands=1)
        startup = child.precharge("auth.auth_start")
        child.defer(startup)
        core = child.precharge("case.core")
        if unknown_core:
            child.unknown(core, reason="not_terminal")
        else:
            child.defer(core, partial_observed_sql_commands=2)
        deferred = [startup]
        if driver:
            connection = child.precharge("driver")
            child.defer(connection)
            deferred.append(connection)
        ctx = b.Context(self.gate, binding=self.binding, stack={}, ledger=ledger)
        ctx.execution_ledger, ctx._envelope = child, envelope
        ctx._managed_group = root.MANAGED_OBSERVATION_GROUP
        ctx._deferred, ctx.closeout = deferred, {}
        ctx._validate = lambda: None  # Scope here is actual ledger arithmetic, not source admission.
        return ctx, ledger, child

    def test_actual_ledger_counts_native_and_whole_managed_union_once(self):
        ctx, ledger, child = self.make()
        ctx._settle_root({"process_stopped": True, "managed_sql": {"commands": 8}})
        value = ledger.receipt()
        self.assertEqual(value["observed_sql_commands"], 11)
        self.assertFalse(value["pending"])
        self.assertFalse(value["runtime_admitted"])
        self.assertTrue(ctx.closeout["numeric_lifetime_complete"])
        self.assertEqual(child.receipt()["numeric_unions"][0]["command_ids"],
                         ["auth.auth_start", "case.core"])
        self.assertFalse(child.receipt()["numeric_unions"][0]["per_request_attribution"])

    def test_unknown_driver_is_not_zero_and_parent_reservation_remains(self):
        ctx, ledger, child = self.make(driver=True)
        ctx._settle_root({"process_stopped": True, "managed_sql": {"commands": 8}})
        self.assertFalse(ctx.closeout["numeric_lifetime_complete"])
        value = ledger.receipt()
        self.assertTrue(value["stopped"])
        self.assertEqual(value["refundable_units"], 0)
        self.assertEqual(value["events"][0]["state"], "unknown_consumed")
        self.assertEqual(value["observed_sql_commands"], 0)  # No invented whole-parent count.
        self.assertEqual(child.receipt()["observed_sql_commands"], 11)

    def test_unknown_core_cannot_be_promoted_by_union(self):
        ctx, ledger, child = self.make(unknown_core=True)
        with self.assertRaisesRegex(root.RootBlocked, "unknown_or_already_counted_partition"):
            ctx._settle_root({"process_stopped": True, "managed_sql": {"commands": 8}})
        self.assertTrue(ledger.receipt()["pending"])
        self.assertEqual(child.receipt()["numeric_unions"], [])

    def test_stopped_flag_false_cannot_settle_managed_interval(self):
        ctx, ledger, child = self.make()
        with self.assertRaisesRegex(b.tracked.Blocked, "managed_process_not_terminal"):
            ctx._settle_root({"process_stopped": False, "managed_sql": {"commands": 8}})
        self.assertEqual(child.receipt()["numeric_unions"], [])


if __name__ == "__main__":
    unittest.main()

