import copy,hashlib,pathlib,unittest
import quota_boundary as q
import migration_boundary as old

class Tests(unittest.TestCase):
    def objects(self,text,base):
        body=text.split('as $f$',1)[1].split('$f$;',1)[0].replace('\r\n','\n')
        return dict(function_oid=base,trigger_oid=base+1,migration_statements=[text],
            function=dict(body_sha=hashlib.sha256(body.encode()).hexdigest(),owner='postgres',definer=False,
                path=['search_path=pg_catalog, pg_temp'],public_execute=False,forbidden_execute=False),
            trigger=dict(type=27,enabled='O',function_matches=True,no_filter=True,no_arguments=True,constraint='0'))
    def states(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        names=[dict(zip(('version','name'),p.stem.split('_',1))) for p in sorted((root/'supabase/migrations').glob('*.sql'))]
        b=dict(migrations=names[:-1],catalog=dict(functions={'1':True},triggers={'2':True},relations={},policies={},
            constraints={'3':True},m44=dict(function_oid=None,trigger_oid=None,migration_statements=None,
                function=None,trigger=None,constraint_oid=3,run_hashes=['a'*64],
                constraint=dict(type='c',validated=True,expression=q.expression(old.source(root))),
                legacy_m44=self.objects(old.source(root),1))))
        a=copy.deepcopy(b);a['migrations']=names;a['catalog']['m44'].update(self.objects(q.source(root),4),constraint_oid=6)
        a['catalog']['m44']['constraint']['expression']=q.expression(q.source(root))
        a['catalog']['functions']['4']=True;a['catalog']['triggers']['5']=True;a['catalog']['constraints']={'6':True}
        return root,b,a
    def test_pending_and_present_states_with_exact_additive_delta(self):
        root,b,a=self.states();saved=copy.deepcopy(b)
        self.assertTrue(q.initial(b,root));self.assertFalse(q.initial(a,root))
        self.assertEqual(q.validate(b,a,root),a);self.assertEqual(b,saved)
        self.assertEqual(q.validate(a,copy.deepcopy(a),root),a)
    def test_legacy_change_or_row_drift_denied(self):
        for path,value in [('legacy_m44',{}),('run_hashes',[])]:
            root,b,a=self.states();a['catalog']['m44'][path]=value
            with self.assertRaises((ValueError,KeyError)):q.validate(b,a,root)
    def test_extra_object_or_acl_denied(self):
        for group in ('relations','functions','triggers','policies'):
            root,b,a=self.states();a['catalog'][group]['unexpected']={}
            with self.assertRaisesRegex(ValueError,'unexpected_object'):q.validate(b,a,root)
    def test_public_execute_definer_and_wrong_path_denied(self):
        for key,value in [('public_execute',True),('definer',True),('path',['public'])]:
            root,b,a=self.states();a['catalog']['m44']['function'][key]=value
            with self.assertRaisesRegex(ValueError,'function_boundary'):q.validate(b,a,root)
    def test_missing_history_wrong_sql_and_wrong_quota_denied(self):
        root,b,a=self.states();a['migrations'][-1]['name']='wrong'
        with self.assertRaisesRegex(ValueError,'history_identity'):q.initial(a,root)
        root,b,a=self.states();a['catalog']['m44']['migration_statements']=['select 1']
        with self.assertRaisesRegex(ValueError,'registered_sql'):q.validate(b,a,root)
        root,b,a=self.states();a['catalog']['m44']['constraint']['expression']='command_count<=9999'
        with self.assertRaisesRegex(ValueError,'constraint_expression'):q.validate(b,a,root)
    def test_already_present_cannot_hide_changes(self):
        root,b,a=self.states();changed=copy.deepcopy(a);changed['catalog']['relations']['new']={}
        with self.assertRaisesRegex(ValueError,'already_present_drift'):q.validate(a,changed,root)
    def test_cli_split_and_crlf_are_equivalent(self):
        from pglast.parser import split
        root,b,a=self.states();a['catalog']['m44']['migration_statements']=list(split(q.source(root).replace('\n','\r\n')))
        self.assertEqual(q.validate(b,a,root),a)

if __name__=='__main__':unittest.main()
