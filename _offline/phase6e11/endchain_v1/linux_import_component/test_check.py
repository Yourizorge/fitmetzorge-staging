import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('linux_import_check', Path(__file__).with_name('check.py'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CheckTests(unittest.TestCase):
    def test_large_log_is_bounded_but_original_digest_and_size_retained(self):
        value = check.bounded_log('x' * 100_000 + 'terminal')
        self.assertTrue(value['log_truncated'])
        self.assertLess(len(value['log']), 57_000)
        self.assertTrue(value['log'].endswith('terminal'))
        self.assertEqual(value['log_bytes'], 100_008)
        self.assertEqual(value['log_sha256'], hashlib.sha256(('x'*100_000+'terminal').encode()).hexdigest())
        self.assertEqual(check.bounded_log('short')['log'], 'short')

    def test_interfaces_are_read_from_active_namespace_not_sysfs_mount(self):
        with patch.object(check.socket, 'if_nameindex', return_value=[(1, 'lo')]):
            self.assertEqual(check.interfaces(), ['lo'])
        for actual in ([], [(1, 'lo'), (2, 'eth0')], [(2, 'eth0')]):
            with patch.object(check.socket, 'if_nameindex', return_value=actual):
                with self.assertRaisesRegex(ValueError, 'external_interface'):
                    check.interfaces()

    def test_skip_failure_or_missing_execution_cannot_pass(self):
        result = unittest.TestResult()
        result.testsRun = 29
        self.assertTrue(check.complete(result, 29))
        self.assertFalse(check.complete(result, 30))
        result.skipped.append(('case', 'skip'))
        self.assertFalse(check.complete(result, 29))
        result.skipped.clear()
        result.failures.append(('case', 'failure'))
        self.assertFalse(check.complete(result, 29))
        result.failures.clear()
        result.expectedFailures.append(('case', 'expected'))
        self.assertFalse(check.complete(result, 29))

    def test_changed_source_and_manifest_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {}
            for name in check.PATHS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'fixture\n')
                files[name] = hashlib.sha256(b'fixture\n').hexdigest()
            raw = json.dumps({'format':1, 'files':files}).encode()
            (root / check.MANIFEST).write_bytes(raw)
            pin = hashlib.sha256(raw).hexdigest()
            self.assertEqual(check.verify(root, pin)[0]['files'], files)
            with self.assertRaisesRegex(ValueError, 'manifest_hash'):
                check.verify(root, '0'*64)
            (root / check.PATHS[0]).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'source_hash'):
                check.verify(root, pin)


if __name__ == '__main__':
    unittest.main()
