"""Pin/TLS admission negatives; Docker, PG and TLS handshake remain mocked."""
import unittest
from test_runtime_registered_context_join import StartupTests, startup


class PinTlsTests(unittest.TestCase):
    def test_exact_digest_is_used_for_pull_inspect_and_run(self):
        with StartupTests().local_process() as (server, _, commands):
            witness = server.open()
            server.close()
        self.assertIn(["docker", "pull", startup.IMAGE], commands)
        self.assertIn(["docker", "image", "inspect", startup.IMAGE], commands)
        self.assertEqual(next(c for c in commands if c[1] == "run")[-3], startup.IMAGE)
        self.assertTrue(witness["native_ssl"])
        self.assertTrue(witness["auth_ssl"])
        self.assertEqual(witness["auth_sslmode"], "verify-full")

    def test_nonempty_wrong_digest_blocks_before_auth_start(self):
        with StartupTests().local_process(wrong_digest=True) as (server, _, commands):
            with self.assertRaisesRegex(ValueError, "image_digest"):
                server.open()
            server.close()
        self.assertFalse(any(c[1] == "run" for c in commands))

    def test_plaintext_auth_backend_is_not_observer_tls_proof(self):
        with StartupTests().local_process(auth_tls=False) as (server, _, commands):
            with self.assertRaisesRegex(ValueError, "actual_auth_target_tls"):
                server.open()
            server.close()
        self.assertIn("pg_stat_ssl", startup.BOUND)
        self.assertTrue(any(c[1] == "stop" for c in commands))

    def test_ca_mount_must_be_original_and_readonly(self):
        with StartupTests().local_process(writable_ca=True) as (server, calls, commands):
            with self.assertRaisesRegex(ValueError, "auth_ca_mount"):
                server.open()
            server.close()
        self.assertNotIn(("health", "http_health"), calls)
        self.assertTrue(any(c[1] == "stop" for c in commands))


if __name__ == "__main__":
    unittest.main()
