import types
import unittest
from admission_failure import save_final, package_journal


def fail(*args):raise OSError('synthetic-write-error')


class Tests(unittest.TestCase):
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
