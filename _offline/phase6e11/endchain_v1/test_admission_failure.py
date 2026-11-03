import types
import unittest
import json
from unittest.mock import patch
from admission_failure import save_final, package_journal, secondary


def fail(*args):raise OSError('synthetic-write-error')


class Tests(unittest.TestCase):
    def test_budget_failure_preserves_stage_and_original_without_secret(self):
        import admission_budget_receipts as receipts
        secret = 'DO_NOT_PUBLISH_password_connection_string'
        original = RuntimeError('original-' + secret)
        failure = FileNotFoundError(secret)
        gate = types.SimpleNamespace(result={})
        with patch.object(receipts, 'assemble', side_effect=failure):
            try:
                receipts.run(gate)
            except FileNotFoundError as raised:
                self.assertIs(raised, failure)
                secondary(gate, 'budget_packaging', raised, original)
            else:
                self.fail('the original exception was suppressed')
        result = gate.result['admission_secondary_failures'][0]
        self.assertEqual(result['diagnostic']['stage'], 'assemble')
        self.assertTrue(result['diagnostic']['source_frames'])
        self.assertNotIn(secret, json.dumps(result))
        self.assertNotIn('filename', json.dumps(result))
        self.assertIs(original.admission_secondary_failures[0], result)

    def test_budget_diagnostic_rejects_unregistered_stage(self):
        error = ValueError('secret')
        error.admission_budget_stage = 'secret'
        gate = types.SimpleNamespace(result={})
        secondary(gate, 'budget_packaging', error, None)
        self.assertEqual(gate.result['admission_secondary_failures'][0]['diagnostic'],
                         {'stage': 'unclassified', 'source_frames': []})

    def test_storage_error_does_not_replace_original(self):
        gate=types.SimpleNamespace(save=fail,result={});original=ConnectionError('synthetic')
        save_final(gate,'final.json',{},original)
        self.assertEqual(gate.result['admission_secondary_failures'][0]['primary_class'],'ConnectionError')
        self.assertEqual(original.admission_secondary_failures[0]['secondary_class'],'OSError')

    def test_storage_error_without_original_is_fatal(self):
        gate=types.SimpleNamespace(save=fail,result={})
        with self.assertRaises(OSError):save_final(gate,'final.json',{})
        self.assertEqual(gate.result['admission_secondary_failures'][0]['phase'],'receipt_storage')

    def test_packaging_error_keeps_primary_and_secondary(self):
        gate=types.SimpleNamespace(result={});journal=types.SimpleNamespace(seal=fail)
        original=TimeoutError('synthetic')
        package_journal(gate,journal,lambda *a:None,original)
        self.assertEqual(gate.result['admission_secondary_failures'][0]['primary_class'],'TimeoutError')

    def test_packaging_error_cannot_be_a_pass(self):
        gate=types.SimpleNamespace(result={});journal=types.SimpleNamespace(seal=fail)
        with self.assertRaises(OSError):package_journal(gate,journal,lambda *a:None)


if __name__=='__main__':unittest.main()
