"""Passive readiness orchestration; Docker/procfs are models, not actual CI."""
import unittest
from unittest.mock import patch
from test_runtime_registered_context_join import StartupTests, startup


class ReadinessTests(unittest.TestCase):
    def test_delayed_listen_precedes_single_health_and_no_extra_sql(self):
        with StartupTests().local_process(readiness_polls=7) as (server, calls, commands):
            with patch.object(startup, "health", return_value={}) as health:
                server.open()
                server.close()
        health.assert_called_once_with()
        self.assertLess(calls.index(("auth_listen_ready", "docker")),
                        calls.index(("health", "http_health")))
        self.assertEqual(sum(kind == "native_sql" for _, kind in calls), 6)
        self.assertEqual(sum(c[1:3] == ["exec", "4"*64] for c in commands), 1)

    def test_expired_readiness_never_dispatches_health_and_stops_owned_process(self):
        with StartupTests().local_process(readiness_status="expired", readiness_polls=40) as (server, calls, commands):
            with patch.object(startup, "health") as health:
                with self.assertRaisesRegex(ValueError, "readiness_expired"):
                    server.open()
                server.close()
        health.assert_not_called()
        self.assertTrue(any(c[1] == "stop" for c in commands))

    def test_bad_poll_count_cannot_be_readiness_proof(self):
        for count in (True, 0, 41):
            with self.subTest(count=count), StartupTests().local_process(readiness_polls=count) as (server, calls, _):
                with self.assertRaisesRegex(ValueError, "readiness_receipt"):
                    server.open()
                server.close()
                self.assertNotIn(("health", "http_health"), calls)

    def test_fixed_readiness_budget_is_not_auth_retry_or_barrier(self):
        plan = startup.source_program()
        self.assertEqual(plan["health_attempts"], 1)
        self.assertEqual(plan["readiness"]["passive_poll_ceiling"], 40)
        self.assertEqual(plan["readiness"]["sql_commands"], 0)
        self.assertEqual(plan["readiness"]["http_attempts"], 0)
        self.assertFalse(plan["readiness"]["mint_barrier"])
        self.assertIn('"$i" -lt 40', startup.READINESS_SCRIPT)
        self.assertIn("sleep 0.25", startup.READINESS_SCRIPT)


if __name__ == "__main__":
    unittest.main()
