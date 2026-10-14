import copy,hashlib,pathlib,re,unittest
import migration_boundary as m

class Tests(unittest.TestCase):
    def make(self):
        root=pathlib.Path(__file__).resolve().parents[3];text=m.source(root)
        old={'function_oid':None,'function':None,'trigger_oid':None,'trigger':None,'constraint_oid':3,
            'constraint':{'expression':'command_count>=0 and command_count<=128','validated':True,'type':'c'},
            'run_hashes':['a'*64],'migration_statements':None}
        catalog={'functions':{'1':{'hash':'old'}},'triggers':{},'relations':{'9':{'acl':None}},'policies':{},
            'constraints':{'3':{'name':'runs_command_count_check'}},'m44':old}
        before={'migrations':[{'version':str(i)} for i in range(43)],'catalog':catalog}
        after=copy.deepcopy(before);after['migrations'].append({'version':m.VERSION})
        a=after['catalog'];v=a['m44'];v.update(function_oid=4,trigger_oid=5,constraint_oid=6,migration_statements=[text])
        v['constraint']['expression']=re.search(r'check\((command_count>=0.*?)\);',text,re.S)[1]
        v['function']={'body_sha':hashlib.sha256(text.split('as $f$',1)[1].split('$f$;',1)[0].encode()).hexdigest(),
            'owner':'postgres','definer':False,'path':['search_path=pg_catalog, pg_temp'],'public_execute':False,'forbidden_execute':False}
        v['trigger']={'type':27,'enabled':'O','function_matches':True,'no_filter':True,'no_arguments':True,'constraint':0}
        a['functions']['4']={'hash':'new'};a['triggers']['5']='new';del a['constraints']['3'];a['constraints']['6']={'new':True}
        return root,before,after
    def test_exact_delta_preserves_original_baseline(self):
        root,b,a=self.make();old=copy.deepcopy(b)
        self.assertEqual(m.validate(b,a,root),a);self.assertEqual(b,old)
    def test_acl_and_other_object_drift_denied(self):
        for part in ['relations','functions','policies']:
            root,b,a=self.make();a['catalog'][part]['forbidden']={}
            with self.assertRaises(ValueError):m.validate(b,a,root)
    def test_unsafe_function_or_trigger_denied(self):
        for key,value in [('definer',True),('public_execute',True),('path',['public'])]:
            root,b,a=self.make();a['catalog']['m44']['function'][key]=value
            with self.assertRaises(ValueError):m.validate(b,a,root)
    def test_data_and_history_drift_denied(self):
        root,b,a=self.make();a['catalog']['m44']['run_hashes'].append('b'*64)
        with self.assertRaisesRegex(ValueError,'rows_changed'):m.validate(b,a,root)
        root,b,a=self.make();a['migrations'][0]['version']='wrong'
        with self.assertRaisesRegex(ValueError,'history_delta'):m.validate(b,a,root)
    def test_wrong_limit_and_registered_sql_denied(self):
        root,b,a=self.make();a['catalog']['m44']['constraint']['expression']='command_count<=9999'
        with self.assertRaisesRegex(ValueError,'constraint_expression'):m.validate(b,a,root)
        root,b,a=self.make();a['catalog']['m44']['migration_statements']=['select 1']
        with self.assertRaisesRegex(ValueError,'registered_sql'):m.validate(b,a,root)
    def test_whitespace_not_a_fake_object_change(self):
        self.assertEqual(m.ast('select (1 + 2)'),m.ast('select 1+2;'))

if __name__=='__main__':unittest.main()
