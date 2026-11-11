"""Pinned-byte compatibility only: no PG connection, workflow or admission proof."""
import ast
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import admission_budget_bootstrap_prefix as prefix
import admission_budget_prefix_originals as audit
from assembly_checks import run as portable
from assembly_checks import test_runner as runner_tests

ROOT = pathlib.Path(__file__).resolve().parents[3]


class ReviewedByteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = portable.approved_byte_pairs(ROOT)
        cls.original_pins = portable.decode(portable.read(ROOT, portable.CHECKS+'fixture_pins.json'))
        names = set(cls.pairs) | set(prefix.PINS) | set(audit.CURRENT_PINS)
        names |= set(cls.original_pins['policy']) | {
            portable.CHECKS+'historical/'+p for p in cls.original_pins['historical']}
        names |= {prefix.REVIEWED_BYTE_PAIRS, portable.CHECKS+'fixture_pins.json'}
        cls.originals = {p: portable.read(ROOT, p) for p in names}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='d12-')
        self.addCleanup(self.temp.cleanup)
        self.root = portable.io_path(pathlib.Path(self.temp.name))
        for name, raw in self.originals.items():
            self.write(name, raw)

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def variant(self, name, encoding):
        lf = self.originals[name].replace(b'\r\n', b'\n')
        raw = lf if encoding == 'lf' else lf.replace(b'\n', b'\r\n')
        row = next(v for v in self.pairs[name]['variants'] if v['encoding'] == encoding)
        self.assertEqual((prefix.sha(raw), len(raw)), (row['sha256'], row['bytes']))
        return raw

    def install_variants(self, encoding):
        for name in self.pairs:
            self.write(name, self.variant(name, encoding))

    def candidate(self):
        return dict(sources={p: prefix.sha(prefix._raw(self.root, p))
                             for p in (*audit.CURRENT_PINS, prefix.REVIEWED_BYTE_PAIRS)})

    def test_all_exact_sixteen_pairs_both_directions(self):
        self.assertEqual(len(self.pairs), 16)
        for name, row in self.pairs.items():
            for actual in ('lf', 'crlf'):
                for expected in row['variants']:
                    with self.subTest(name=name, actual=actual, expected=expected['encoding']):
                        self.assertTrue(prefix.reviewed_raw_matches(self.root, name,
                            self.variant(name, actual), expected['sha256'], expected['bytes']))

    def test_current_source_contract_and_program_emit_actual_raw_hashes(self):
        for encoding in ('lf', 'crlf'):
            with self.subTest(encoding=encoding):
                self.install_variants(encoding)
                candidate = self.candidate()
                raw, hashes, _, _ = audit._source_contract(self.root, candidate)
                self.assertEqual(hashes, {p:h for p,h in candidate['sources'].items()
                                         if p != prefix.REVIEWED_BYTE_PAIRS})
                self.assertEqual(prefix.sha(raw[prefix.REVIEWED_BYTE_PAIRS]),
                                 candidate['sources'][prefix.REVIEWED_BYTE_PAIRS])
                program = prefix.source_program(self.root)
                self.assertTrue(program['canonical_originals_producer'])
                self.assertEqual(program['source_hashes'][prefix.REVIEWED_BYTE_PAIRS],
                                 prefix.REVIEWED_BYTE_PAIRS_SHA)
                for name, actual in program['source_hashes'].items():
                    self.assertEqual(actual, prefix.sha(prefix._raw(self.root, name)))
                self.assertIsNone(program['cases']['pre_migration']['complete_upper_bound'])
                self.assertEqual(hashes[prefix.BOOTSTRAP],
                                 prefix.sha(self.variant(prefix.BOOTSTRAP, encoding)))

    def test_frozen_policy_lf_crlf_count_and_actual_hashes(self):
        for encoding in ('lf', 'crlf'):
            with self.subTest(encoding=encoding):
                self.install_variants(encoding)
                report = prefix.inspect_canonical_policy_inventory(self.root)
                self.assertEqual(report['body_statement_count'], 1552)
                self.assertEqual(report['declared_cli_policy_cap_sum'], 2256)
                self.assertFalse(report['actual_execution_evidence'])
                self.assertFalse(report['bound_complete'])
                self.assertEqual(report['source_hashes'][prefix.REVIEWED_BYTE_PAIRS],
                                 prefix.REVIEWED_BYTE_PAIRS_SHA)
                for row in report['migrations']:
                    raw = prefix._raw(self.root, row['path'])
                    self.assertEqual((row['sha256'], row['bytes']), (prefix.sha(raw), len(raw)))
                    self.assertEqual(report['source_hashes'][row['path']], prefix.sha(raw))

    def test_mixed_endings_rejected_at_all_three_callers(self):
        name = prefix.BOOTSTRAP
        raw = self.variant(name, 'lf').replace(b'\n', b'\r\n', 1)
        self.write(name, raw)
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'producer_revision'):
            audit._source_contract(self.root, self.candidate())
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'bootstrap_prefix_source_changed'):
            prefix.source_program(self.root)
        name = next(p for p in self.pairs if p.startswith('supabase/migrations/'))
        self.write(name, self.variant(name, 'lf').replace(b'\n', b'\r\n', 1))
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'bootstrap_frozen_bytes:2'):
            prefix.inspect_canonical_policy_inventory(self.root)

    def test_changed_body_rejected_even_with_candidate_repinned(self):
        self.write(prefix.BOOTSTRAP, self.variant(prefix.BOOTSTRAP, 'lf')+b'\n# changed\n')
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'producer_revision'):
            audit._source_contract(self.root, self.candidate())
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'bootstrap_prefix_source_changed'):
            prefix.source_program(self.root)

    def test_changed_migration_body_rejected(self):
        name = next(p for p in self.pairs if p.startswith('supabase/migrations/'))
        self.write(name, self.variant(name, 'lf')+b'\n-- changed\n')
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'bootstrap_frozen_bytes:2'):
            prefix.inspect_canonical_policy_inventory(self.root)

    def test_candidate_cannot_report_other_valid_variant_as_actual(self):
        self.install_variants('lf')
        candidate = self.candidate()
        candidate['sources'][prefix.BOOTSTRAP] = audit.CURRENT_PINS[prefix.BOOTSTRAP]
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'candidate_producer_binding'):
            audit._source_contract(self.root, candidate)

    def test_candidate_missing_or_wrong_table_binding_rejected(self):
        for value in (None, '0'*64):
            with self.subTest(value=value):
                candidate = self.candidate()
                if value is None:
                    candidate['sources'].pop(prefix.REVIEWED_BYTE_PAIRS)
                else:
                    candidate['sources'][prefix.REVIEWED_BYTE_PAIRS] = value
                with self.assertRaisesRegex(prefix.PrefixBlocked, 'candidate_byte_pairs_binding'):
                    audit._source_contract(self.root, candidate)

    def test_unlisted_path_cannot_use_pair(self):
        name = prefix.BOOTSTRAP
        self.assertFalse(prefix.reviewed_raw_matches(self.root, 'unknown/bootstrap.py',
            self.variant(name, 'lf'), audit.CURRENT_PINS[name]))

    def test_wrong_original_hash_or_size_denied(self):
        name = prefix.BOOTSTRAP
        raw = self.variant(name, 'lf')
        row = self.pairs[name]['variants'][1]
        self.assertFalse(prefix.reviewed_raw_matches(self.root, name, raw, '0'*64))
        self.assertFalse(prefix.reviewed_raw_matches(self.root, name, raw, row['sha256'], row['bytes']+1))
        self.assertFalse(prefix.reviewed_raw_matches(self.root, name, raw, row['sha256'], True))

    def test_missing_or_changed_table_cannot_authorize_variant(self):
        name = prefix.BOOTSTRAP
        raw = self.variant(name, 'lf')
        path = self.root / prefix.REVIEWED_BYTE_PAIRS
        path.unlink()
        self.assertFalse(prefix.reviewed_raw_matches(self.root, name, raw, audit.CURRENT_PINS[name]))
        self.write(prefix.REVIEWED_BYTE_PAIRS, self.originals[prefix.REVIEWED_BYTE_PAIRS]+b'\n')
        with self.assertRaisesRegex(prefix.PrefixBlocked, 'bootstrap_byte_pairs_changed'):
            prefix.reviewed_raw_matches(self.root, name, raw, audit.CURRENT_PINS[name])

    def test_frozen_pins_and_historical_four_stay_exact(self):
        self.assertEqual(prefix.PINS, self.original_pins['historical'])
        for path, expected in prefix.PINS.items():
            raw = self.originals[portable.CHECKS+'historical/'+path]
            self.assertEqual(prefix.sha(raw), expected)
            self.assertTrue(prefix.reviewed_raw_matches(self.root, path, raw, expected))
        (self.root / prefix.REVIEWED_BYTE_PAIRS).unlink()
        raw = self.originals[portable.CHECKS+'historical/'+prefix.BOOTSTRAP]
        self.assertTrue(prefix.reviewed_raw_matches(self.root, prefix.BOOTSTRAP, raw, prefix.PINS[prefix.BOOTSTRAP]))
        self.assertEqual(audit.CURRENT_PINS[prefix.BOOTSTRAP], self.pairs[prefix.BOOTSTRAP]['variants'][1]['sha256'])

    def test_portable_fixture_test_uses_exact_v2_context_both_variants(self):
        for encoding in ('lf', 'crlf'):
            with self.subTest(encoding=encoding):
                self.install_variants(encoding)
                with patch.object(portable, 'SOURCE_ROOT', self.root):
                    runner_tests.RunnerTests('test_actual_fixture_inventory_is_four_plus_48_no_policy_copy').test_actual_fixture_inventory_is_four_plus_48_no_policy_copy()


class SourceInventoryTests(unittest.TestCase):
    def test_case_and_local_inventories_bind_helper_table_and_test(self):
        needed = {prefix.PREFIX+p for p in ('admission_budget_bootstrap_prefix.py',
                  'admission_budget_prefix_originals.py', 'test_admission_source_bytes.py',
                  'assembly_checks/byte_pairs_20261111.json')}
        case_tree = ast.parse(portable.read(ROOT, prefix.PREFIX+'quota_candidate_v1/case_ci.py'))
        statement = next(n for n in case_tree.body if isinstance(n, ast.Assign)
                         and any(isinstance(t, ast.Name) and t.id == 'SOURCES' for t in n.targets))
        # SOURCES is tuple(generator) + a literal tuple; no module execution needed.
        self.assertIsInstance(statement.value, ast.BinOp)
        case_names = set(ast.literal_eval(statement.value.right))
        local_tree = ast.parse(portable.read(ROOT, prefix.PREFIX+'admission_ci.py'))
        local = next(n for n in local_tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'LOCAL_SOURCES' for t in n.targets))
        local_names = {prefix.PREFIX+n for n in ast.literal_eval(local.value)}
        self.assertTrue(needed <= case_names)
        self.assertTrue(needed <= local_names)
        ready = next(n for n in case_tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'READY' for t in n.targets))
        self.assertIs(ast.literal_eval(ready.value), False)
        self.assertEqual(portable.sha(portable.read(ROOT, prefix.REVIEWED_BYTE_PAIRS)),
                         prefix.REVIEWED_BYTE_PAIRS_SHA)


if __name__ == '__main__':
    unittest.main()
