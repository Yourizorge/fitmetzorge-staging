"""Pure manifest regressions using pinned local bytes, never execution evidence."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from assembly_checks import run as r


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2).encode('ascii')


def exact(path, raw):
    return dict(path=path, sha256=r.sha(raw), bytes=len(raw))


class ManifestV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = r.SOURCE_ROOT
        cls.pairs = r.approved_byte_pairs(cls.source)
        original_raw = r.read(cls.source, r.CHECKS+'fixture_pins.json')
        if r.sha(original_raw) != r.ORIGINAL_FIXTURES_SHA:
            raise ValueError('test_original_fixture_pin')
        cls.original = r.decode(original_raw)
        names = set(cls.pairs) | set(cls.original['policy']) | {
            r.CHECKS+'historical/'+p for p in cls.original['historical']}
        names |= {r.BYTE_PAIRS, r.CHECKS+'fixture_pins.json'}
        cls.original_bytes = {p: r.read(cls.source, p) for p in names}
        for p, row in cls.pairs.items():
            r.verify_record(cls.original_bytes[p], row, cls.pairs)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='manifest-v2-')
        self.addCleanup(self.temp.cleanup)
        self.root = r.io_path(Path(self.temp.name))
        self.data = dict(self.original_bytes)
        self.name = r.CHECKS+'sources-current.json'
        self.fixture_name = r.CHECKS+'fixture-pins-current.json'
        self.rows = {p: copy.deepcopy(self.pairs[p]) if p in self.pairs else exact(p, raw)
                     for p, raw in self.data.items()}
        self.pins = dict(format='portable-assembly-fixtures-v2',
                         historical=copy.deepcopy(self.original['historical']),
                         policy={p: copy.deepcopy(self.rows[p]) for p in self.original['policy']})
        for p, raw in self.data.items():
            self.write(p, raw)
        self.write_fixtures()
        self.value = dict(format='portable-assembly-source-v2',
                          files=list(self.rows.values()), fixtures=self.fixture_name,
                          byte_pairs_sha256=r.BYTE_PAIRS_SHA, READY=False,
                          historical_authority=False, full_selection_tests=452)

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def write_fixtures(self):
        raw = encoded(self.pins)
        self.write(self.fixture_name, raw)
        row = exact(self.fixture_name, raw)
        self.rows[self.fixture_name] = row
        if hasattr(self, 'value'):
            self.value['files'] = [row if x['path'] == self.fixture_name else x
                                   for x in self.value['files']]

    def verify(self, fixtures=True):
        raw = encoded(self.value)
        self.write(self.name, raw)
        manifest, actual = r.verify_manifest(self.root, self.name, r.sha(raw))
        if fixtures:
            r.verify_fixtures(self.root, self.pins, manifest)
        return actual

    def row(self, path=None):
        path = path or sorted(self.pairs)[0]
        return next(x for x in self.value['files'] if x['path'] == path)

    def test_preserved_raw_hashes_returned(self):
        actual = self.verify()
        self.assertEqual(set(self.pairs), r.VARIANT_PATHS)
        for path in self.pairs:
            self.assertEqual(actual[path], r.sha(self.data[path]))

    def test_all_lf_and_all_crlf_independently_pinned(self):
        for encoding in ('lf', 'crlf'):
            with self.subTest(encoding=encoding):
                for p, raw in self.data.items():
                    if p in self.pairs:
                        lf = raw.replace(b'\r\n', b'\n')
                        self.write(p, lf if encoding == 'lf' else lf.replace(b'\n', b'\r\n'))
                actual = self.verify()
                for p, row in self.pairs.items():
                    variant = next(x for x in row['variants'] if x['encoding'] == encoding)
                    self.assertEqual(actual[p], variant['sha256'])

    def test_wrong_body_not_normalized_away(self):
        path = sorted(self.pairs)[0]
        self.write(path, self.data[path]+b'# changed\n')
        with self.assertRaisesRegex(ValueError, 'variant_raw_bytes'):
            self.verify()

    def test_mixed_endings_even_same_canonical_are_denied(self):
        path = sorted(self.pairs)[0]
        raw = self.data[path].replace(b'\r\n', b'\n')
        self.assertGreater(raw.count(b'\n'), 1)
        self.write(path, raw.replace(b'\n', b'\r\n', 1))
        with self.assertRaisesRegex(ValueError, 'variant_raw_bytes'):
            self.verify()

    def test_wrong_variant_size(self):
        self.row()['variants'][0]['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'variant_not_independently_pinned'):
            self.verify()

    def test_bool_size_not_integer(self):
        self.row()['variants'][0]['bytes'] = True
        with self.assertRaisesRegex(ValueError, 'variant_record'):
            self.verify()

    def test_wrong_variant_hash(self):
        self.row()['variants'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'variant_not_independently_pinned'):
            self.verify()

    def test_wrong_canonical_hash(self):
        self.row()['canonical_lf_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'variant_not_independently_pinned'):
            self.verify()

    def test_third_variant_denied(self):
        self.row()['variants'].append(copy.deepcopy(self.row()['variants'][0]))
        with self.assertRaisesRegex(ValueError, 'variant_record'):
            self.verify()

    def test_missing_variant_denied(self):
        self.row()['variants'].pop()
        with self.assertRaisesRegex(ValueError, 'variant_record'):
            self.verify()

    def test_variant_cannot_move_to_another_path(self):
        row = copy.deepcopy(self.row())
        row['path'] = 'not-allowlisted.py'
        self.write(row['path'], self.data[self.row()['path']])
        self.value['files'].append(row)
        with self.assertRaisesRegex(ValueError, 'variant_record'):
            self.verify()

    def test_one_of_sixteen_cannot_be_exact_only(self):
        row = self.row()
        path = row['path']
        row.clear()
        row.update(exact(path, self.data[path]))
        with self.assertRaisesRegex(ValueError, 'manifest_v2_inventory'):
            self.verify()

    def test_missing_one_of_sixteen(self):
        self.value['files'].remove(self.row())
        with self.assertRaisesRegex(ValueError, 'manifest_v2_inventory'):
            self.verify()

    def test_pair_file_changed_even_with_matching_source_row(self):
        raw = self.data[r.BYTE_PAIRS]+b'\n'
        self.write(r.BYTE_PAIRS, raw)
        self.row(r.BYTE_PAIRS).update(exact(r.BYTE_PAIRS, raw))
        with self.assertRaisesRegex(ValueError, 'byte_pairs_pin'):
            self.verify()

    def test_unbound_pair_file_denied(self):
        self.value['files'].remove(self.row(r.BYTE_PAIRS))
        with self.assertRaisesRegex(ValueError, 'manifest_v2_inventory'):
            self.verify()

    def test_wrong_pair_manifest_pin(self):
        self.value['byte_pairs_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'manifest_v2_binding'):
            self.verify()

    def test_policy_source_records_must_be_identical(self):
        p = next(p for p in self.pins['policy'] if p in self.pairs)
        self.pins['policy'][p] = exact(p, self.data[p])
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, 'policy_source_mismatch'):
            self.verify()

    def test_policy_size_mismatch(self):
        p = next(p for p in self.pins['policy'] if p in self.pairs)
        self.pins['policy'][p]['variants'][0]['bytes'] += 1
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, 'variant_not_independently_pinned'):
            self.verify()

    def test_unapproved_policy_content_cannot_be_repinned(self):
        p = next(p for p in self.pins['policy'] if p not in self.pairs)
        raw = self.data[p]+b'\n'
        self.write(p, raw)
        self.row(p).update(exact(p, raw))
        self.pins['policy'][p] = exact(p, raw)
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, 'policy_original_pin'):
            self.verify()

    def test_missing_policy_denied(self):
        self.pins['policy'].pop(next(iter(self.pins['policy'])))
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, 'fixture_v2_inventory'):
            self.verify()

    def test_historical_content_cannot_be_repinned(self):
        p = next(iter(self.pins['historical']))
        name = r.CHECKS+'historical/'+p
        raw = self.data[name]+b'\n'
        self.write(name, raw)
        self.row(name).update(exact(name, raw))
        self.pins['historical'][p] = r.sha(raw)
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, 'fixture_v2_inventory'):
            self.verify()

    def test_historical_variant_denied(self):
        name = r.CHECKS+'historical/'+next(iter(self.pins['historical']))
        row = copy.deepcopy(self.row())
        row['path'] = name
        self.value['files'] = [row if x['path'] == name else x for x in self.value['files']]
        with self.assertRaisesRegex(ValueError, 'variant_record'):
            self.verify()

    def test_original_fixture_pin_file_cannot_change(self):
        name = r.CHECKS+'fixture_pins.json'
        raw = self.data[name]+b'\n'
        self.write(name, raw)
        self.row(name).update(exact(name, raw))
        with self.assertRaisesRegex(ValueError, 'original_fixture_pins_changed'):
            self.verify()

    def test_missing_fixture_source_binding(self):
        self.value['files'].remove(self.row(self.fixture_name))
        with self.assertRaisesRegex(ValueError, 'manifest_v2_inventory'):
            self.verify()

    def test_casefold_alias_denied(self):
        row = copy.deepcopy(self.row())
        row['path'] = row['path'].upper()
        self.value['files'].append(row)
        with self.assertRaisesRegex(ValueError, 'manifest_duplicate_or_self'):
            self.verify()

    def test_extra_envelope_key_denied(self):
        self.value['allow_normalization'] = True
        with self.assertRaisesRegex(ValueError, 'manifest_shape'):
            self.verify()

    def test_ready_cannot_be_enabled(self):
        self.value['READY'] = True
        with self.assertRaisesRegex(ValueError, 'manifest_authority'):
            self.verify()

    def test_explicit_new_manifest_does_not_rewrite_old(self):
        old = b'original manifest sentinel\n'
        self.write(r.CHECKS+'sources.json', old)
        self.verify()
        self.assertEqual(r.read(self.root, r.CHECKS+'sources.json'), old)

    def test_v1_exact_shape_still_works(self):
        p = sorted(self.pairs)[0]
        self.value = dict(format='portable-assembly-source-v1', files=[exact(p, self.data[p])])
        self.assertEqual(self.verify(fixtures=False), {p: r.sha(self.data[p])})

    def test_v1_cannot_gain_variants(self):
        self.value = dict(format='portable-assembly-source-v1', files=[self.row()])
        with self.assertRaisesRegex(ValueError, 'manifest_row'):
            self.verify(fixtures=False)

    def test_v1_bool_size_denied(self):
        p = sorted(self.pairs)[0]
        row = exact(p, self.data[p])
        row['bytes'] = True
        self.value = dict(format='portable-assembly-source-v1', files=[row])
        with self.assertRaisesRegex(ValueError, 'manifest_row'):
            self.verify(fixtures=False)


class CompleteResultTests(unittest.TestCase):
    def result(self, case):
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
        count = suite.countTestCases()
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        return result, count

    def test_real_class_skip_zero_executed_is_not_pass(self):
        class ClassSkip(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise unittest.SkipTest('synthetic class skip')
            def test_one(self): pass
            def test_two(self): pass
        result, count = self.result(ClassSkip)
        self.assertEqual((count, result.testsRun, len(result.skipped)), (2, 0, 1))
        self.assertTrue(result.wasSuccessful())
        self.assertFalse(r.complete_result(result, count))

    def test_real_individual_skip_is_not_pass(self):
        class TestSkip(unittest.TestCase):
            @unittest.skip('synthetic test skip')
            def test_one(self): pass
        result, count = self.result(TestSkip)
        self.assertEqual(result.testsRun, count)
        self.assertTrue(result.wasSuccessful())
        self.assertFalse(r.complete_result(result, count))

    def test_incomplete_count_without_skips_is_not_pass(self):
        class One(unittest.TestCase):
            def test_one(self): pass
        result, count = self.result(One)
        self.assertTrue(r.complete_result(result, count))
        self.assertFalse(r.complete_result(result, count+1))

    def test_setupclass_error_cannot_pass(self):
        class Error(unittest.TestCase):
            @classmethod
            def setUpClass(cls): raise RuntimeError('synthetic setup error')
            def test_one(self): pass
        result, count = self.result(Error)
        self.assertFalse(r.complete_result(result, count))

    def test_complete_zero_skip_run_passes(self):
        class Two(unittest.TestCase):
            def test_one(self): pass
            def test_two(self): pass
        result, count = self.result(Two)
        self.assertEqual((count, result.testsRun, len(result.skipped)), (2, 2, 0))
        self.assertTrue(r.complete_result(result, count))


if __name__ == '__main__':
    unittest.main()
