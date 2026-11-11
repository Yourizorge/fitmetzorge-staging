"""Local driver source/identity checks; never opens PostgreSQL."""
import os
import unittest
from unittest.mock import patch
import test_runtime_registered_bootstrap as base
from quota_candidate_v1 import runtime_registered_costs as costs


class CostTests(unittest.TestCase):
    parameters = {'host': '127.0.0.1', 'hostaddr': '127.0.0.1'}
    def test_installed_reviewed_driver_proof_no_connection(self):
        import psycopg
        with patch.object(psycopg, 'connect', side_effect=AssertionError('no connection')):
            proof = costs.native_proof(self.parameters)
        self.assertEqual(proof['connection_open_sql'], 0)
        self.assertEqual(proof['connection_close_sql'], 0)
        self.assertEqual(len(proof['binary_hashes']), 2)
        self.assertFalse(proof['server_connection_executed'])

    def test_target_probe_or_service_is_rejected(self):
        for env in ({'PGTARGETSESSIONATTRS': 'read-write'}, {'PGSERVICE': 'external'},
                    {'PGSERVICEFILE': 'external'}):
            with self.subTest(env=list(env)), patch.dict(os.environ, env):
                with self.assertRaisesRegex(ValueError, 'implicit_target_probe_or_service'):
                    costs.native_proof(self.parameters)

    def test_unreviewed_libpq_is_not_silently_zero(self):
        import psycopg.pq
        with patch.object(psycopg.pq, 'version', return_value=180000):
            with self.assertRaisesRegex(ValueError, 'libpq_unreviewed'):
                costs.native_proof(self.parameters)

    def test_explicit_parameters_cannot_override_zero_contract(self):
        for update in ({'target_session_attrs': 'primary'}, {'target_session_attrs': 'prefer-standby'},
                       {'service': 'other'}, {'host': '127.0.0.1,127.0.0.1'},
                       {'hostaddr': '127.0.0.1,127.0.0.1'}):
            with self.subTest(update=update):
                with self.assertRaisesRegex(ValueError, 'actual_connection_parameters'):
                    costs.native_proof({**self.parameters, **update})

    def test_three_is_explicit_config_transaction_not_lifetime_http_bound(self):
        value = costs.source_bound_contract()
        self.assertEqual(value['normal_max'], len(value['normal_commands']))
        self.assertTrue(all(len(p) <= 3 for p in value['fault_prefixes']))
        self.assertFalse(value['full_chain_admission'])
        self.assertEqual(value['covered_managed_group'], 'auth.managed_lifetime')
        self.assertTrue(any('provenance' in x for x in value['limitations']))


if __name__ == '__main__':
    unittest.main()
