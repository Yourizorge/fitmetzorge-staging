import importlib.util, pathlib, sys, unittest
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sql_protocol import statements, single, receipt

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

class Protocol(unittest.TestCase):
    def test_all_transaction_commands_count(self):
        self.assertEqual(len(statements('BEGIN; SELECT 1; COMMIT; ROLLBACK;')), 4)

    def test_semicolons_in_literals_are_not_commands(self):
        self.assertEqual(len(statements("select ';', $$;$$ /* ; */; -- ;\n")), 1)

    def test_do_is_one_protocol_command_not_write_exemption(self):
        r = receipt("DO $$ BEGIN PERFORM 1; PERFORM 2; END $$;")
        self.assertEqual(r['protocol_commands'], 1)
        self.assertFalse(r['internal_writes_exempt'])

    def test_cursor_commands_count(self):
        self.assertEqual(len(statements('BEGIN READ ONLY; DECLARE c CURSOR FOR SELECT 1; FETCH 8 FROM c; CLOSE c; ROLLBACK;')), 5)

    def test_extra_statement_denied(self):
        with self.assertRaisesRegex(ValueError, 'multiple_protocol_statements'):
            single('SELECT 1; SELECT 2')

    def test_changed_statement_denied(self):
        with self.assertRaisesRegex(ValueError, 'protocol_source_changed'):
            single('SELECT 2', single('SELECT 1')['sha256'])

    def test_invalid_sql_not_estimated(self):
        with self.assertRaises(Exception):
            statements('SELECT (')

    def test_empty_not_zero_cost(self):
        with self.assertRaises(ValueError):
            statements('')

    def test_real_guard_and_observer_install_counts(self):
        g = module('protocol_guard', HERE.parent/'controller_guard_v1/guard.py')
        a = module('protocol_audit', HERE.parent/'auth_metadata_v1/audit.py')
        ids = {role: f'68000000-0000-4000-8000-{i:012}' for i, role in enumerate(g.ROLES, 1)}
        run = '68000000-0000-4000-8000-000000000020'
        self.assertEqual(len(statements(g.install(run, ids))), 6)
        self.assertEqual(len(statements(a.install(run, ids, '2026-10-12T12:00:00+00:00'))), 5)
        self.assertEqual(len(statements(g.inspect(run, ids))), 1)
        self.assertEqual(len(statements(a.inspect(run, ids))), 1)

    def test_compact_arm_is_single_real_statement(self):
        import auth_arm
        ids = {role: f'68000000-0000-4000-8000-{i:012}' for i, role in enumerate(('a_member','a_trainer','b_member'), 1)}
        self.assertEqual(len(statements(auth_arm.render('68000000-0000-4000-8000-000000000020', ids,
            '68000000-0000-4000-8000-000000000021', 'a_member', 'issue'))), 1)

if __name__ == '__main__':
    unittest.main()
