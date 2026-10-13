import unittest
import lifecycle_gates as g
from sql_protocol import statements

class LifecycleTests(unittest.TestCase):
    def test_fixed_read_only_single_commands(self):
        for sql in (g.CATALOG,g.MIGRATIONS,g.ACCESS,g.ABSENCE):
            self.assertEqual(len(statements(sql)),1)
            self.assertEqual(statements(sql)[0]['kind'],'SelectStmt')
    def test_absence_requires_every_field(self):
        value=dict.fromkeys(('temporary_schemas','sessions','refresh_tokens','windows','workspaces','participants'),0)
        g.check_absence(value)
        for key in value:
            with self.assertRaises(ValueError):g.check_absence({**value,key:1})
            with self.assertRaises(ValueError):g.check_absence({k:v for k,v in value.items() if k!=key})
    def test_acl_and_tls_are_not_truthy(self):
        value=dict.fromkeys(('database_ok','role_ok','pg17','ssl','registered','private_functions_safe'),True)
        g.check_access(value)
        for key in value:
            with self.assertRaises(ValueError):g.check_access({**value,key:1})
    def test_migration_change_is_not_accepted(self):
        rows=[{'version':str(i),'name':'synthetic','sql_sha':'a'*64} for i in range(43)]+[{'version':'20261012185121','name':'synthetic','sql_sha':'b'*64}]
        g.check_migrations(rows,rows)
        with self.assertRaises(ValueError):g.check_migrations(rows,rows[:-1])

if __name__=='__main__':unittest.main()
