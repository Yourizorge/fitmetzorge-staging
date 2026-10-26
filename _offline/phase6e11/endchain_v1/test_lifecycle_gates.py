import unittest
import lifecycle_gates as g
from sql_protocol import statements

class LifecycleTests(unittest.TestCase):
    def test_percent_and_repeated_parameters(self):
        from integral_ci import bind_parameters
        self.assertEqual(bind_parameters("select x like 'pg_%'",[]),("select x like 'pg_%'",None))
        self.assertEqual(bind_parameters("select $1,$1 where x like 'fmz%'",['synthetic']),
            ("select %s,%s where x like 'fmz%%'",['synthetic','synthetic']))
    def test_fixed_read_only_single_commands(self):
        for sql in (g.CATALOG,g.MIGRATIONS,g.ACCESS,g.ABSENCE):
            self.assertEqual(len(statements(sql)),1)
            self.assertEqual(statements(sql)[0]['kind'],'SelectStmt')
    def test_existing_private_observer_is_only_definer_exception(self):
        self.assertIn("p.oid<>to_regprocedure('fmz6e11_audit_private.observe()')",g.ACCESS)
        self.assertIn("pg_get_userbyid(p.proowner)<>'postgres'",g.ACCESS)
        self.assertIn("has_function_privilege(roles.name,p.oid,'EXECUTE')",g.ACCESS)
    def test_absence_requires_every_field(self):
        value=dict.fromkeys(('temporary_schemas','sessions','refresh_tokens','windows','workspaces','participants','all_test_windows','all_test_workspaces','all_test_participants','all_registered_sessions','all_registered_refresh_tokens'),0)
        g.check_absence(value)
        for key in value:
            with self.assertRaises(ValueError):g.check_absence({**value,key:1})
            with self.assertRaises(ValueError):g.check_absence({k:v for k,v in value.items() if k!=key})
    def test_acl_and_tls_are_not_truthy(self):
        value=dict.fromkeys(('database_ok','role_ok','pg17','ssl','registered','private_functions_safe'),True)
        g.check_access(value)
        for key in value:
            with self.assertRaises(ValueError):g.check_access({**value,key:1})
    def test_catalog_covers_non_system_schemas_and_global_fixture_absence(self):
        self.assertNotIn("n.nspname in('public','auth')",g.CATALOG)
        self.assertGreaterEqual(g.CATALOG.count("n.nspname not like 'pg_%'"),5)
        for table in ('windows','workspaces','participants'):
            self.assertIn('count(*) from fmz6e11_private.'+table+')',g.ABSENCE)
        self.assertIn('select user_id from fmz6e11_private.identities',g.ABSENCE)
    def test_migration_change_is_not_accepted(self):
        rows=[{'version':str(i),'name':'synthetic','sql_sha':'a'*64} for i in range(44)]+[{'version':'20261018070231','name':'synthetic','sql_sha':'b'*64}]
        g.check_migrations(rows,rows)
        with self.assertRaises(ValueError):g.check_migrations(rows,rows[:-1])

if __name__=='__main__':unittest.main()
