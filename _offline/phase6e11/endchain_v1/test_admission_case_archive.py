"""Filesystem/ZIP transport proof only; no PG, Auth or case-admission claim."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import admission_case_archive as archive


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.gate = types.SimpleNamespace(out=self.root)
        self.originals = {'registered-context-private/001-closeout.json': b'{"synthetic":true}\n',
                          'registered-fixture-closeout-private/result.json': b'{"zero":true}\n',
                          'case-root.ledger.txt': b'{"sequence":1}\n{"sequence":2}\n'}
        self.refs = []
        for name, raw in self.originals.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.refs.append({'path': name, 'sha256': archive.sha(raw), 'bytes': len(raw)})

    def build(self):
        reference = archive.pack(self.gate, self.refs)
        payloads = {p.name: p.read_bytes() for p in self.root.glob('case-original-*')}
        return reference, payloads

    def reseal(self, reference, payloads, *, index=None, chunk=None):
        value = archive.object_json(payloads[archive.INDEX])
        if chunk:
            name = 'case-original-001.json'
            content = archive.object_json(payloads[name])
            chunk(content)
            payloads[name] = archive.encoded(content)
            value['chunks'][name].update(sha256=archive.sha(payloads[name]), bytes=len(payloads[name]))
        if index:
            index(value)
        payloads[archive.INDEX] = archive.encoded(value)
        reference.update(sha256=archive.sha(payloads[archive.INDEX]), bytes=len(payloads[archive.INDEX]))

    def test_all_explicit_records_survive_flat_artifact(self):
        (self.root / 'unregistered-private.txt').write_bytes(b'not exported')
        reference, payloads = self.build()
        self.assertEqual(archive.verify(payloads, reference, self.refs), self.originals)
        self.assertTrue(all('/' not in name for name in payloads))
        self.assertNotIn(b'not exported', b''.join(payloads.values()))

    def test_duplicate_basenames_keep_their_own_full_paths(self):
        name = 'registered-other-private/result.json'
        raw = b'{"different":1}'
        (self.root / name).parent.mkdir()
        (self.root / name).write_bytes(raw)
        self.refs.append({'path': name, 'sha256': archive.sha(raw)})
        reference, payloads = self.build()
        self.assertEqual(archive.verify(payloads, reference, self.refs)[name], raw)

    def test_chunk_boundary_and_record_order_are_lossless(self):
        with patch.object(archive, 'CHUNK_RAW', 20):
            reference, payloads = self.build()
        index = archive.object_json(payloads[archive.INDEX])
        self.assertGreaterEqual(len(index['chunks']), 3)
        self.assertEqual(archive.verify(payloads, reference, list(reversed(self.refs))), self.originals)

    def test_repeated_pack_cannot_overwrite_original_or_partial_publication(self):
        reference, payloads = self.build()
        with self.assertRaisesRegex(ValueError, 'already_attempted'):
            archive.pack(self.gate, self.refs)
        self.assertEqual(payloads, {p.name: p.read_bytes() for p in self.root.glob('case-original-*')})

    def test_partial_publication_stays_incomplete_and_is_not_retried(self):
        publish = archive.publish
        def fail(root, name, value):
            if name == archive.INDEX:
                raise OSError('synthetic storage failure')
            return publish(root, name, value)
        with patch.object(archive, 'publish', fail), self.assertRaises(OSError):
            archive.pack(self.gate, self.refs)
        self.assertFalse((self.root / archive.INDEX).exists())
        self.assertTrue((self.root / 'case-original-001.json').exists())
        with self.assertRaisesRegex(ValueError, 'already_attempted'):
            archive.pack(self.gate, self.refs)

    def test_changed_source_during_pack_prevents_complete_index(self):
        read = archive.read_original
        counts = {}
        def change(root, ref):
            counts[ref['path']] = counts.get(ref['path'], 0) + 1
            if counts[ref['path']] == 2:
                (root / ref['path']).write_bytes(b'changed')
            return read(root, ref)
        with patch.object(archive, 'read_original', change), self.assertRaisesRegex(ValueError, 'record_digest'):
            archive.pack(self.gate, self.refs)
        self.assertFalse((self.root / archive.INDEX).exists())

    def test_wrong_original_hash_and_size_fail_before_export(self):
        for key, value in (('sha256', '0' * 64), ('bytes', 1)):
            refs = copy.deepcopy(self.refs)
            refs[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                archive.pack(self.gate, refs)
            self.assertFalse(list(self.root.glob('case-original-*')))

    def test_alias_traversal_hidden_and_archive_paths_denied(self):
        for name in ('../outside.json', 'a//b.json', '/root.json', 'C:/bad.json',
                     '.env', 'a\\b.json', 'case-original-001.json', 'a/./b.json'):
            refs = [{'path': name, 'sha256': 'a' * 64}]
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive.references(refs)
        duplicate = copy.deepcopy(self.refs)
        duplicate.append({**self.refs[0], 'path': self.refs[0]['path'].upper()})
        with self.assertRaises(ValueError):
            archive.references(duplicate)

    def test_symlink_source_is_not_exported(self):
        path = self.root / 'link.json'
        try:
            path.symlink_to(self.root / self.refs[0]['path'])
        except (OSError, NotImplementedError):
            self.skipTest('symlink privilege unavailable')
        with self.assertRaisesRegex(ValueError, 'source_link'):
            archive.pack(self.gate, [{**self.refs[0], 'path': 'link.json'}])

    def test_windows_directory_aliases_and_devices_are_rejected(self):
        for name in ('a./record.json', 'a../record.json', 'a/b./record.json',
                     'CON/record.json', 'nul.json', 'a/Aux.txt', 'COM1/record.json',
                     'LPT9.json', 'a/PRN.old/record.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'reference_path'):
                archive.references([{'path': name, 'sha256': 'a' * 64}])
        valid = [{'path': 'ordinary.name/record.json', 'sha256': 'a' * 64}]
        self.assertIn(valid[0]['path'], archive.references(valid))

    def test_record_and_total_caps_apply_before_complete_index(self):
        with patch.object(archive, 'MAX_RAW', 1), self.assertRaisesRegex(ValueError, 'total_raw_size'):
            archive.pack(self.gate, self.refs)
        self.assertFalse((self.root / archive.INDEX).exists())
        with patch.object(archive, 'MAX_RECORD', 1), self.assertRaises(ValueError):
            archive.pack(self.gate, self.refs)

    def test_missing_chunk_and_extra_chunk_rejected(self):
        reference, payloads = self.build()
        for remove in (True, False):
            candidate = dict(payloads)
            if remove:
                candidate.pop('case-original-001.json')
            else:
                candidate['case-original-099.json'] = b'{}'
            with self.subTest(remove=remove), self.assertRaises(ValueError):
                archive.verify(candidate, reference, self.refs)

    def test_changed_index_or_chunk_digest_rejected(self):
        reference, payloads = self.build()
        for name in payloads:
            candidate = dict(payloads)
            candidate[name] += b' '
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive.verify(candidate, reference, self.refs)

    def test_resealed_missing_or_extra_reference_rejected(self):
        reference, payloads = self.build()
        self.reseal(reference, payloads, chunk=lambda c: c['entries'].pop(self.refs[0]['path']))
        with self.assertRaises(ValueError):
            archive.verify(payloads, reference, self.refs)

    def test_resealed_changed_original_bytes_still_fail_original_hash(self):
        reference, payloads = self.build()
        self.reseal(reference, payloads, chunk=lambda c: c['entries'][self.refs[0]['path']].update(base64='e30='))
        with self.assertRaises(ValueError):
            archive.verify(payloads, reference, self.refs)

    def test_two_megabyte_original_survives_bounded_fragments(self):
        raw = b'X' * archive.MAX_RECORD
        name = 'case-large.ledger.txt'
        (self.root / name).write_bytes(raw)
        self.refs.append({'path': name, 'sha256': archive.sha(raw), 'bytes': len(raw)})
        reference, payloads = self.build()
        self.assertTrue(all(len(v) <= archive.MAX_MEMBER for v in payloads.values()))
        self.assertEqual(archive.verify(payloads, reference, self.refs)[name], raw)

    def test_resealed_fragment_gap_or_replay_is_rejected(self):
        reference, payloads = self.build()
        self.reseal(reference, payloads, chunk=lambda c: c['entries'][self.refs[0]['path']].update(offset=1))
        with self.assertRaisesRegex(ValueError, 'fragment_order'):
            archive.verify(payloads, reference, self.refs)

    def test_flat_original_and_archive_cannot_disagree(self):
        reference, payloads = self.build()
        payloads['case-root.ledger.txt'] = b'conflicting original'
        with self.assertRaisesRegex(ValueError, 'flat_original_conflict'):
            archive.verify(payloads, reference, self.refs)

    def test_resealed_count_total_and_flags_are_not_trusted(self):
        reference, payloads = self.build()
        for field, value in (('record_count', True), ('raw_bytes', 0), ('complete', False),
                             ('hosted_calls', False), ('explicit_references_only', False)):
            ref, data = dict(reference), dict(payloads)
            self.reseal(ref, data, index=lambda v: v.update({field: value}))
            with self.subTest(field=field), self.assertRaises(ValueError):
                archive.verify(data, ref, self.refs)

    def test_duplicate_json_keys_are_never_accepted(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_json_key'):
            archive.object_json(b'{"complete":false,"complete":true}')


if __name__ == '__main__':
    unittest.main()
