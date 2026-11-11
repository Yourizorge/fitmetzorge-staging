"""F's preread/serialization failure regression; isolated unit ledgers only."""
import unittest
from unittest.mock import patch

import admission_budget_root_runtime as budget
import test_admission_budget_root_runtime as fixtures


class PrereadTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RootTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def grouped(self):
        ledger = self.fixture.ledger(program=self.fixture.grouped_program())
        tickets = []
        for ident in ("unit:managed", "unit:native"):
            ticket = ledger.precharge(ident)
            ledger.defer(ticket)
            tickets.append(ticket)
        return ledger, tickets

    def test_union_preread_failure_latches_before_retry(self):
        ledger, tickets = self.grouped()
        original = OSError("synthetic journal preread failure")
        with patch.object(budget, "_read_bytes", side_effect=original):
            with self.assertRaises(OSError) as caught:
                ledger.settle_union(tickets, observed_sql_commands=17)
        self.assertIs(caught.exception, original)
        with self.assertRaisesRegex(budget.RootBlocked, "journal_failed"):
            ledger.settle_union(tickets, observed_sql_commands=17)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 17)
        self.assertEqual(len(ledger.receipt()["numeric_unions"]), 1)
        with self.assertRaises(budget.RootBlocked):
            ledger.close()

    def test_union_serialization_failure_latches_before_retry(self):
        ledger, tickets = self.grouped()
        dumps = budget.json.dumps
        def fail_journal(value, *args, **kwargs):
            if isinstance(value, dict) and "previous_bytes_sha256" in value:
                raise TypeError("synthetic serialization failure")
            return dumps(value, *args, **kwargs)
        with patch.object(budget.json, "dumps", side_effect=fail_journal):
            with self.assertRaisesRegex(TypeError, "serialization"):
                ledger.settle_union(tickets, observed_sql_commands=17)
        with self.assertRaisesRegex(budget.RootBlocked, "journal_failed"):
            ledger.settle_union(tickets, observed_sql_commands=17)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 17)

    def test_confirm_preread_failure_cannot_reconfirm_mutated_total(self):
        ledger = self.fixture.ledger()
        ticket = ledger.precharge("unit:managed")
        with patch.object(budget, "_read_bytes", side_effect=OSError("synthetic preread")):
            with self.assertRaises(OSError):
                ledger.confirm(ticket, observed_sql_commands=3)
        with self.assertRaisesRegex(budget.RootBlocked, "journal_failed"):
            ledger.confirm(ticket, observed_sql_commands=3)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 3)

    def test_deferred_preread_failure_cannot_resettle(self):
        program = self.fixture.program
        program[0]["defer"] = True
        ledger = self.fixture.ledger(program=program)
        ticket = ledger.precharge("unit:managed")
        ledger.defer(ticket)
        ledger.confirm(ledger.precharge("unit:native"), observed_sql_commands=0)
        with patch.object(budget, "_read_bytes", side_effect=OSError("synthetic preread")):
            with self.assertRaises(OSError):
                ledger.settle_deferred(ticket, observed_sql_commands=3)
        with self.assertRaisesRegex(budget.RootBlocked, "journal_failed"):
            ledger.settle_deferred(ticket, observed_sql_commands=3)
        self.assertEqual(ledger.receipt()["observed_sql_commands"], 3)


if __name__ == "__main__":
    unittest.main()
