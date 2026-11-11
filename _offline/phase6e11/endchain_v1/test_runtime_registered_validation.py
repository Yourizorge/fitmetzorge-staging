"""Startup control flow and ledger faults only; all external effects mocked."""
import types
import unittest
from unittest.mock import patch

from test_runtime_registered_context_join import StartupTests, FakeLedger, b, startup


class ValidationTests(unittest.TestCase):
    def fixture(self):
        return StartupTests().local_process()

    def attach(self, server):
        owner = server.owner
        owner.server = server
        owner.execution_ledger = FakeLedger(owner.binding)
        owner._extra_modules, owner._extra_binding = [], {}
        owner._validate = lambda: None
        owner._local_call = types.MethodType(b.Context._local_call, owner)
        return owner.execution_ledger

    def test_all_six_source_validation_nodes_have_zero_observed_sql(self):
        with self.fixture() as (server, _, _), patch.object(b.source_binding, "verify", return_value={}):
            ledger = self.attach(server)
            server.open()
            rows = [row for row in ledger.events if row[0] == "confirmed"
                    and row[1].startswith("auth.validate.")]
            self.assertEqual([row[1] for row in rows], ["auth.validate."+name for name in
                ("pg", "connection", "target", "image", "auth", "target_connection")])
            self.assertTrue(all(row[2]["observed_sql_commands"] == 0 for row in rows))
            server.close()

    def test_each_validation_failure_finishes_zero_ticket_before_cleanup(self):
        cases = (("pg", "stack_pg_changed"), ("connection", "original_stack_ca_changed"),
                 ("target", "target_boundary"), ("image", "image_id"),
                 ("auth", "auth_config_binding"), ("target_connection", "actual_auth_target_tls"))
        for node, code in cases:
            with self.subTest(node=node), self.fixture() as (server, _, commands), patch.object(
                    b.source_binding, "verify", return_value={}):
                ledger = self.attach(server)
                original = startup.require
                def reject(value, reason):
                    original(False if reason == code else value, reason)
                with patch.object(startup, "require", reject), self.assertRaisesRegex(ValueError, code):
                    server.open()
                rows = [r for r in ledger.events if r[0] == "fault"]
                self.assertEqual(rows, [("fault", "auth.validate."+node,
                    {"observed_sql_commands": 0, "reason": "validation_failed"})])
                self.assertIsNone(ledger.pending)
                if node in ("pg", "connection", "target", "image"):
                    self.assertFalse(any(args[1] == "run" for args in commands))
                server.close()


if __name__ == "__main__":
    unittest.main()
