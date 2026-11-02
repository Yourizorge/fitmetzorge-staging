import copy
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import admission_journal as j


class Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.folder = pathlib.Path(temp.name)/'journal'; self.published = {}
        def publish(name, value):
            self.assertNotIn(name, self.published)
            self.published[name] = copy.deepcopy(value)
        self.journal = j.Journal(self.folder, publish, 'admission-fixture')

    def test_every_record_is_durable_and_losslessly_packaged(self):
        for i in range(140): self.journal.save('record-%03d.json'%i, {'i':i, 'confirmed':False})
        self.assertEqual(len(list(self.folder.iterdir())), 140)
        index = self.journal.seal()
        self.assertEqual(len(index['chunks']), 3)
        self.assertEqual(j.verify(index, self.published.__getitem__)['records'], 140)
        self.assertEqual(len(self.published), 4)

    def test_truly_empty_unpoisoned_journal_can_be_sealed(self):
        index = self.journal.seal()
        self.assertEqual(index['record_count'], 0)
        self.assertEqual(j.verify(index, self.published.__getitem__),
                         {'records': 0, 'raw_bytes': 0, 'complete': True})
        self.assertFalse(self.journal.poisoned)
        self.assertIsNone(self.journal.failure)

    def test_duplicate_alias_path_and_reseal_rejected(self):
        self.journal.save('first.json', {})
        for name in ('first.json', 'FIRST.json', '../outside.json', 'a/b.json'):
            with self.subTest(name=name), self.assertRaises(ValueError): self.journal.save(name, {})
        self.journal.seal()
        with self.assertRaises(ValueError): self.journal.seal()
        with self.assertRaises(ValueError): self.journal.save('late.json', {})

    def test_modified_record_blocks_packaging(self):
        self.journal.save('first.json', {'i':1})
        (self.folder/'first.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed_before_packaging'): self.journal.seal()

    def test_modified_chunk_and_missing_record_never_verify(self):
        self.journal.save('first.json', {'i':1}); index = self.journal.seal()
        name = next(iter(index['chunks']))
        self.published[name]['entries']['first.json']['base64'] = 'e30='
        with self.assertRaises(ValueError): j.verify(index, self.published.__getitem__)

    def test_removed_chunk_is_not_complete_even_with_rehashed_index(self):
        self.journal.save('first.json', {}); index = self.journal.seal()
        index['chunks'] = {}
        with self.assertRaisesRegex(ValueError, 'incomplete'): j.verify(index, self.published.__getitem__)

    def test_existing_private_directory_never_reused(self):
        with self.assertRaises(FileExistsError): j.Journal(self.folder, lambda *a:None, 'admission-other')

    def test_near_limit_records_remain_below_artifact_member_limit(self):
        for i in range(2): self.journal.save('large-%d.json'%i, {'data':'a'*990000})
        index = self.journal.seal()
        self.assertEqual(len(index['chunks']), 2)
        self.assertTrue(all(len(j.raw(v)) < 2000000 for v in self.published.values()))
        self.assertEqual(j.verify(index, self.published.__getitem__)['records'], 2)

    def test_oversized_record_is_not_written(self):
        with self.assertRaisesRegex(ValueError, 'record_size'):
            self.journal.save('large.json', {'data':'a'*j.MAX_RECORD})
        self.assertEqual(list(self.folder.iterdir()), [])

    def assert_poison_blocks_continuation(self):
        self.assertTrue(self.journal.poisoned)
        failure = copy.deepcopy(self.journal.failure)
        with self.assertRaisesRegex(ValueError, 'journal_poisoned'):
            self.journal.save('later.json', {'must_not_write': True})
        with self.assertRaisesRegex(ValueError, 'journal_poisoned'):
            self.journal.seal()
        self.assertFalse((self.folder/'later.json').exists())
        self.assertEqual(self.journal.failure, failure)
        self.assertNotIn('admission-fixture-index.json', self.published)

    def test_real_fsync_failure_preserves_unregistered_file_and_cannot_seal_empty(self):
        value = {'dispatch': 'not_authorized_until_save_returns'}
        with patch.object(j.os, 'fsync', side_effect=OSError('sensitive filesystem details')) as fsync:
            with self.assertRaises(OSError): self.journal.save('uncertain.json', value)
        fsync.assert_called_once()
        self.assertEqual((self.folder/'uncertain.json').read_bytes(), j.raw(value))
        self.assertEqual(self.journal.entries, {})
        self.assertEqual(self.journal.failure,
                         {'stage': 'fsync', 'record': 'uncertain.json', 'error_class': 'OSError'})
        self.assertNotIn('sensitive', str(self.journal.failure))
        self.assert_poison_blocks_continuation()
        self.assertEqual(self.published, {})

    def test_fsync_failure_after_durable_record_never_exports_only_the_old_subset(self):
        self.journal.save('durable.json', {'ordinal': 1})
        original = (self.folder/'durable.json').read_bytes()
        with patch.object(j.os, 'fsync', side_effect=OSError('lost fsync confirmation')):
            with self.assertRaises(OSError): self.journal.save('uncertain.json', {'ordinal': 2})
        self.assertEqual(set(self.journal.entries), {'durable.json'})
        self.assertEqual({p.name for p in self.folder.iterdir()}, {'durable.json', 'uncertain.json'})
        self.assert_poison_blocks_continuation()
        self.assertEqual((self.folder/'durable.json').read_bytes(), original)
        self.assertEqual(self.published, {})

    def test_write_flush_close_and_short_write_failures_retain_real_files(self):
        actual_open = pathlib.Path.open
        for mode in ('write', 'short_write', 'flush', 'close'):
            with self.subTest(mode=mode):
                journal = j.Journal(self.folder/mode, lambda *args: self.fail('must not publish'), 'failure-case')
                target = journal.folder/'partial.json'
                def opened(path, *args, **kwargs):
                    stream = actual_open(path, *args, **kwargs)
                    if path != target: return stream
                    class Wrapped:
                        def __enter__(self): stream.__enter__(); return self
                        def __exit__(self, *exc):
                            result = stream.__exit__(*exc)
                            if mode == 'close': raise OSError('close failed')
                            return result
                        def write(self, data):
                            if mode in ('write', 'short_write'):
                                count = stream.write(data[:3])
                                if mode == 'write': raise OSError('write failed')
                                return count
                            return stream.write(data)
                        def flush(self):
                            stream.flush()
                            if mode == 'flush': raise OSError('flush failed')
                        def fileno(self): return stream.fileno()
                    return Wrapped()
                with patch.object(pathlib.Path, 'open', opened):
                    with self.assertRaises(OSError): journal.save('partial.json', {'value': 'retained'})
                self.assertTrue(target.exists()); self.assertGreater(target.stat().st_size, 0)
                self.assertTrue(journal.poisoned); self.assertEqual(journal.entries, {})
                self.assertEqual(journal.failure['stage'], 'write' if mode == 'short_write' else mode)
                with self.assertRaisesRegex(ValueError, 'poisoned'): journal.seal()

    def test_exclusive_open_collision_preserves_file_and_poisons(self):
        path = self.folder/'orphan.json'; path.write_bytes(b'prior uncertain evidence')
        with self.assertRaises(FileExistsError): self.journal.save('orphan.json', {'overwrite': False})
        self.assertEqual(path.read_bytes(), b'prior uncertain evidence')
        self.assertEqual(self.journal.failure['error_class'], 'FileExistsError')
        self.assert_poison_blocks_continuation()

    def test_unregistered_file_prevents_false_zero_record_completion(self):
        (self.folder/'orphan.json').write_bytes(b'unregistered')
        with self.assertRaisesRegex(ValueError, 'unregistered_or_missing'): self.journal.seal()
        self.assert_poison_blocks_continuation()
        self.assertEqual(self.published, {})
        self.assertEqual((self.folder/'orphan.json').read_bytes(), b'unregistered')

    def test_missing_record_is_detected_before_any_chunk_publication(self):
        for i in range(65): self.journal.save('record-%03d.json' % i, {'ordinal': i})
        (self.folder/'record-064.json').unlink()
        with self.assertRaisesRegex(ValueError, 'unregistered_or_missing'): self.journal.seal()
        self.assert_poison_blocks_continuation()
        self.assertEqual(self.published, {})

    def test_extra_directory_is_not_silently_omitted(self):
        (self.folder/'unexpected').mkdir()
        with self.assertRaisesRegex(ValueError, 'nonregular_record'): self.journal.seal()
        self.assert_poison_blocks_continuation()

    def test_inventory_drift_during_publication_never_gets_complete_index(self):
        self.journal.save('first.json', {})
        publish = self.journal.publish
        def drifting(name, value):
            publish(name, value)
            (self.folder/'late.json').write_bytes(b'late evidence')
        self.journal.publish = drifting
        with self.assertRaisesRegex(ValueError, 'unregistered_or_missing'): self.journal.seal()
        self.assertEqual(len(self.published), 1)
        self.assert_poison_blocks_continuation()

    def test_content_drift_during_publication_never_gets_complete_index(self):
        self.journal.save('first.json', {})
        publish = self.journal.publish
        def drifting(name, value):
            publish(name, value)
            (self.folder/'first.json').write_bytes(b'changed')
        self.journal.publish = drifting
        with self.assertRaisesRegex(ValueError, 'changed_before_packaging'): self.journal.seal()
        self.assert_poison_blocks_continuation()

    def test_publish_failure_poisons_and_is_never_retried(self):
        self.journal.save('first.json', {})
        calls = []
        def failing(name, value):
            calls.append(name)
            raise OSError('publisher fsync failed')
        self.journal.publish = failing
        with self.assertRaises(OSError): self.journal.seal()
        self.assertEqual(self.journal.failure, {'stage': 'seal', 'record': None, 'error_class': 'OSError'})
        self.assert_poison_blocks_continuation()
        self.assertEqual(len(calls), 1)


if __name__ == '__main__': unittest.main()
