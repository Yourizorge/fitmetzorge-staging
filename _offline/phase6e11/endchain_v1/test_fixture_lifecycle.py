import copy,unittest
from fixture_lifecycle import seed_writes,validate,SEED,REGISTER,SNAPSHOT
from sql_protocol import statements

class FixtureTests(unittest.TestCase):
    def test_each_template_one_protocol_statement(self):
        for sql in (SEED,REGISTER,SNAPSHOT):self.assertEqual(len(statements(sql)),1)
    def test_seed_contract_has_only_ten_exact_synthetic_inserts(self):
        c={k:str(i) for i,k in enumerate(('window','a','b','trainer','member','b_member','key'))}
        e=seed_writes(c);self.assertEqual(len(e),10)
        self.assertTrue(all(x[1]=='INSERT' and len(x[2])>=1 for x in e))
        self.assertEqual(len([x for x in e if x[0]=='participants']),3)
    def pair(self):
        before={'coverage':True,'profiles':'p','accounts':'u'}
        expected=[{'table':'fmz6e11_private.windows','op':'DELETE','old':'h','new':None}]
        after={**before,'action':{'state':'action_confirmed','expected':expected,'xid':'4','backend':8,'actor':'a','workspace':'w'},
            'writes':[{'table_name':'fmz6e11_private.windows','operation':'DELETE','old_key_sha':'h','new_key_sha':None,
                'xid':'4','backend':8,'actor':'a','workspace':'w'}]}
        return before,after,expected
    def test_delete_evidence_is_not_lost_after_row_removal(self):
        b,a,e=self.pair();self.assertEqual(validate(b,a,e)['deletes'],1)
    def test_extra_missing_wrong_transaction_or_protected_row_rejected(self):
        for change in ('missing','extra','transaction','actor','profile','observer'):
            b,a,e=self.pair()
            if change=='missing':a['writes']=[]
            elif change=='extra':a['writes']*=2
            elif change=='transaction':a['writes'][0]['xid']='5'
            elif change=='actor':a['writes'][0]['actor']='other'
            elif change=='profile':a['profiles']='changed'
            else:a['coverage']=False
            with self.subTest(change=change),self.assertRaises(ValueError):validate(b,a,e)

if __name__=='__main__':unittest.main()
