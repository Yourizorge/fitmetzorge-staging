"""History validation tests use source bytes and generated unit samples, no DB."""
import argparse
import copy
import pathlib
import sys
import unittest
from unittest import mock
from quota_candidate_v1 import runtime_history as h
from quota_candidate_v1.compiler import CandidateStop,sha

ROOT=pathlib.Path(__file__).resolve().parents[4]


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names=list((ROOT/'supabase/migrations').glob('*.sql'))+list((ROOT/h.APP).glob('*.sql'))
        cls.sources={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in names}
        cls.names=names
        cls.local_sql='begin; select 1; commit;'

    def setUp(self):
        self.history=h.CaseHistory(ROOT,self.sources,local_version='20261103010203',local_sql=self.local_sql)
        old={r['version']:r for r in self.history.historical}
        self.rows=[]
        for name in self.names:
            version,label=name.stem.split('_',1)
            if version in old:self.rows.append({**old[version],'source_statements':None})
            else:
                text=name.read_text()
                self.rows.append(dict(version=version,name=label,sql_sha=sha(text.encode()),source_statements=[text]))
        self.rows.sort(key=lambda r:r['version'])

    def appended(self):
        return [*copy.deepcopy(self.rows),dict(version=self.history.local_version,name='disposable_case_quota_v1',
            sql_sha=sha(self.local_sql.encode()),source_statements=[self.local_sql])]

    def test_full47_preserves44pin_and_separately_verifies_three_appended_sources(self):
        receipt=self.history.attest(self.rows,appended=False)
        self.assertEqual(receipt['history_count'],47)
        self.assertEqual(len(receipt['source_ast_validated_versions']),3)
        self.assertNotIn('source_statements',str(receipt))
        self.assertFalse(receipt['canonical_migration_added'])

    def test_local48_append_then_immutable_complete_history(self):
        self.history.attest(self.rows,appended=False)
        result=self.history.attest(self.appended(),appended=True)
        self.history.check_observed(result['migrations'])
        changed=copy.deepcopy(result['migrations']);changed[-1]['sql_sha']='0'*64
        with self.assertRaises(CandidateStop):self.history.check_observed(changed)

    def test_historical_database_hash_change_is_not_recanonicalized(self):
        self.rows[0]['sql_sha']='0'*64
        with self.assertRaisesRegex(CandidateStop,'case_history_historical_drift'):self.history.attest(self.rows,appended=False)

    def test_existing_source_history_semantics_must_match_not_just_valid_hash(self):
        row=next(r for r in self.rows if r['source_statements'] is not None)
        row.update(source_statements=['select 1'],sql_sha=sha(b'select 1'))
        with self.assertRaisesRegex(CandidateStop,'case_history_statement_mismatch'):self.history.attest(self.rows,appended=False)

    def test_extra_or_missing_version_rejected(self):
        for rows in (self.rows[:-1],[*self.rows,self.rows[-1]]):
            with self.assertRaises(CandidateStop):self.history.attest(rows,appended=False)

    def test_local48_without_before47_never_establishes_baseline(self):
        with self.assertRaisesRegex(CandidateStop,'case_history_prefix_drift'):self.history.attest(self.appended(),appended=True)

    def test_raw_historical_statement_export_is_forbidden(self):
        self.rows[0]['source_statements']=['unit-only']
        with self.assertRaisesRegex(CandidateStop,'case_history_historical_raw_forbidden'):self.history.attest(self.rows,appended=False)

    def test_byte_identical_frozen_m45_required(self):
        with self.assertRaises(CandidateStop):h.CaseHistory(ROOT,{**self.sources,h.M45:'0'*64},
            local_version='20261103010203',local_sql=self.local_sql)

    def test_backward_prefix_and_changed_registered_digest_denied(self):
        self.history.attest(self.rows,appended=False)
        self.history.attest(self.appended(),appended=True)
        with self.assertRaisesRegex(CandidateStop,'case_history_backward'):self.history.attest(self.rows,appended=False)

    def test_query_is_one_statement_and_not_pgstat_raw_query(self):
        from sql_protocol import single
        self.assertEqual(single(h.MIGRATIONS)['kind'],'SelectStmt')
        self.assertNotIn('pg_stat_statements',h.MIGRATIONS)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--source-root',type=pathlib.Path)
    args,remaining=parser.parse_known_args()
    if args.source_root is not None:ROOT=args.source_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0],*remaining])
