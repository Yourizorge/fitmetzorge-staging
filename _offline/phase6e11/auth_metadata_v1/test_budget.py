import copy,unittest
import budget

class OwnerBudget(unittest.TestCase):
    def setUp(self):
        self.records=[{'status':'NO_GO','commands':95,'combined_commands':103,'auth_calls':0,'application_writes':0,'jit_revoked':True},
                      {'status':'NO_GO','error_class':'Stop','metadata_removed':True},
                      {'remaining_mappings':0,'disabled':True},
                      {'existing_equal':True,'own_additions':0},
                      {'existing_objects_equal':True,'own_additions':0}]
    def test_separate_budget(self):
        result=budget.validate(*self.records)
        self.assertEqual((result['max_seconds'],result['max_commands'],result['prior_commands'],result['historical_commands']),(180,128,0,103))
    def test_no_automatic_retry(self):self.assertEqual(budget.validate(*self.records)['automatic_retries'],0)
    def test_no_auth_or_workflow(self):
        result=budget.validate(*self.records);self.assertEqual((result['auth_calls'],result['workflow_writes']),(0,0))
    def test_changed_prior(self):
        for index,key,value in [(0,'commands',94),(0,'auth_calls',1),(0,'status','PASS'),(0,'jit_revoked',False),(1,'metadata_removed',False),(2,'remaining_mappings',1),(2,'disabled',False),(3,'existing_equal',False),(3,'own_additions',1),(4,'own_additions',1)]:
            with self.subTest(key=key):
                records=copy.deepcopy(self.records);records[index][key]=value
                with self.assertRaises(ValueError):budget.validate(*records)

if __name__=='__main__':unittest.main()
