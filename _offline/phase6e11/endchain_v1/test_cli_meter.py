import unittest
from cli_meter import parse

class MeterTests(unittest.TestCase):
    def test_protocol_and_multiline(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: statement: BEGIN;\nselect 1;\nCOMMIT;\n')
        self.assertEqual(len(rows),3)
        self.assertNotIn('sql',rows[0])
    def test_extended_and_other_connection(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: execute <unnamed>: select 1\nFMZSQL|other|2|1|LOG: statement: select 2\n')
        self.assertEqual(len(rows),1)
    def test_missing_or_malformed_not_zero(self):
        for raw in ('','FMZSQL|bad','FMZSQL|other|2|1|LOG: statement: select 2'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):parse(raw)
    def test_function_body_not_semicolon_split(self):
        rows=parse('FMZSQL|fmz_ci_endchain_meter|1|1|LOG: statement: do $$begin perform 1; perform 2;end$$;\n')
        self.assertEqual(len(rows),1)
    def test_pinned_cli_and_unique_window(self):
        raw='FMZSQLold|@effect/sql-pg|1|1|LOG: statement: select 1\nFMZSQLnew|@effect/sql-pg|2|1|LOG: statement: BEGIN; COMMIT;\n'
        self.assertEqual(len(parse(raw,'FMZSQLnew|',('@effect/sql-pg',))),2)
        with self.assertRaises(ValueError):parse(raw,'FMZSQLabsent|',('@effect/sql-pg',))

if __name__=='__main__':unittest.main()
