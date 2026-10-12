import copy,importlib.util,pathlib,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controller_install_test',HERE/'install.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InstallTests(unittest.TestCase):
    def test_tested_candidate(self):
        result=m.admitted()
        self.assertEqual(result['migration_sha256'],m.c.sha(m.ROOT/'supabase/migrations'/m.M43))
    def test_untested_source_cannot_reuse_ci(self):
        real=m.c.sha
        with patch.object(m.c,'sha',side_effect=lambda p:'0'*64 if pathlib.Path(p).name=='store.mjs' else real(p)):
            with self.assertRaisesRegex(m.Stop,'tested_candidate_changed'):m.admitted()

    def test_exact_inventory(self):
        inventory=[['public','synthetic','1024'],['auth','users','1024']]
        plan=m.plan(inventory)
        self.assertEqual(m.plan(inventory+[[m.NEW,t,'1'] for t in ['runs','steps','evidence']],['public.synthetic','auth.users']),plan)
        for bad in [inventory+inventory,inventory+[[m.NEW,'runs','1']],[['public','large',str(128*1024*1024+1)]]]:
            with self.assertRaises(m.Stop):m.plan(bad)
        with self.assertRaises(m.Stop):m.plan(inventory+[['public','unexpected','1']],['public.synthetic','auth.users'])

    def test_exclusions_precise_and_no_sort(self):
        names=['public.profiles','auth.users','cron.job_run_details','supabase_migrations.schema_migrations','fmz6e11_audit_private.relations']
        q=m.stream_query([{'name':name} for name in names])
        self.assertIn("version <> '20261012104331'",q)
        for name in ['public.profiles','auth.users','fmz6e11_audit_private.relations']:
            self.assertIn('from '+'.'.join('"'+x+'"' for x in name.split('.'))+' t where true',q)
        self.assertIn('from "cron"."job_run_details" t where false',q)
        self.assertNotIn('string_agg',q.lower());self.assertNotIn('order by',q.lower())

    def test_compare_rejects_every_unexpected_change(self):
        before={'tables':[{'name':'public.synthetic','count':0,'sha256':'a'}], 'query_sha256':'x',
          'catalog':[['table','public.synthetic','hash']], 'registry':{'relations':['stable']}}
        after=copy.deepcopy(before);after['catalog']+=[['schema',m.NEW,'s'],['table',m.NEW+'.runs','r']]
        self.assertTrue(m.compare(before,after)['protected_data_unchanged'])
        for change in ['data','query','catalog','registry','extra']:
            bad=copy.deepcopy(after)
            if change=='data':bad['tables'][0]['count']=1
            elif change=='query':bad['query_sha256']='other'
            elif change=='catalog':bad['catalog'][0][2]='other'
            elif change=='registry':bad['registry']={}
            else:bad['catalog'].append(['table','public.unexpected','x'])
            with self.assertRaises(m.Stop):m.compare(before,bad)

    def test_query_protocol_and_closed_authority(self):
        for q in [m.ACL,m.TAG+m.p.jit.META_SQL,m.TAG+m.p.m.INVENTORY,m.TAG+m.p.m.CATALOG]:
            self.assertTrue(q.startswith('/* fmz6e11:qv1:'))
        source=(HERE/'install.py').read_text()
        for phrase in ['tx.start_readonly()','tx.rollback()','c.revoke(token,folder)','parent.reserve_query()',"'query_cap_per_measurement':128","'query_cap_total':296"]:
            self.assertIn(phrase,source)
        sql=(m.ROOT/'supabase/migrations'/m.M43).read_text()
        self.assertNotIn('create function',sql.lower());self.assertNotIn('security definer',sql.lower())

    def test_cli_interval_excludes_fetches(self):
        source=(HERE/'install.py').read_text()
        self.assertLess(source.index('if names is not None:'),source.index('transfer=tx.transfer'))
        self.assertGreater(source.index('if names is None:\n            numeric='),source.index('transfer=tx.transfer'))

if __name__=='__main__':unittest.main()
