import copy,importlib.util,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('request_m42_install',HERE/'install.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class InstallTests(unittest.TestCase):
    def test_exact_inventory(self):
        inv=[['public','t'+str(i),'1'] for i in range(153)]
        plan=m.plans(inv);self.assertEqual(len(plan),153)
        with self.assertRaises(Exception):m.plans(inv[:-1])
        with self.assertRaises(Exception):m.plans(inv+[inv[0]])
        names=[p['name'] for p in plan]
        self.assertEqual(m.plans(inv+[[m.NEW,'control','1'],[m.NEW,'receipts','1']],names),plan)
        with self.assertRaises(Exception):m.plans(inv+[['other','unexpected','1']],names)
    def test_precise_exclusions(self):
        names=['public.profiles','auth.users','cron.job_run_details','supabase_migrations.schema_migrations','fmz6e11_audit_private.relations']
        q=m.query([{'name':n} for n in names])
        self.assertIn("version <> '20260928120846'",q)
        self.assertNotIn("version <> '20260924155822'",q)
        self.assertIn('from "auth"."users" t where true',q)
        self.assertIn('from "public"."profiles" t where true',q)
        self.assertIn('from "cron"."job_run_details" t where false',q)
        self.assertNotIn('string_agg',q);self.assertNotIn('order by',q.lower())
    def test_ci_and_local_gate(self):
        value=m.admission()
        self.assertEqual(value['local_pairs'],45);self.assertEqual(value['negative_tests'],33)
        self.assertEqual(value['migration_sha256'],m.c.sha(m.ROOT/'supabase/migrations'/m.M42))
    def test_boundaries_in_source(self):
        text=(HERE/'install.py').read_text()
        self.assertIn("old.prior.cli_run",text);self.assertIn("c.revoke(token,folder)",text)
        self.assertIn("tx.start_readonly()",text);self.assertIn("tx.rollback()",text)
        self.assertNotIn('p.m.LOAD',text)
        self.assertIn("'automatic_retries':0",text)
    def test_registered_query_protocol(self):
        self.assertTrue(m.TAG.startswith('/* fmz6e11:qv1:'))
        for q in (m.REGISTRY,m.ACL,m.TAG+m.p.jit.META_SQL,m.TAG+m.p.m.INVENTORY,m.TAG+m.p.m.CATALOG):
            self.assertTrue(q.startswith('/* fmz6e11:qv1:'))
        self.assertNotIn('qv4:',(HERE/'install.py').read_text())
if __name__=='__main__':unittest.main()
