import copy
import unittest
from closure import counted_close, allowance, RUN_ID, PURPOSE
from cli_envelope import local


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.trace=[{'command':i+1,'phase':'evidence_query','confirmed':True} for i in range(1518)]
        self.pre={'commands':[{'confirmed':True} for _ in range(4)]}
        self.cli=[local({'protocol_commands':n,'complete':True,'numeric_protocol_coverage':True,'observer_commands':[{'confirmed':True}]*8,'total_commands':n+8}) for n in (14,2)]
        self.auth=[{'role':r,'operation':op,'commands':n,'statements':[{'temp_written':0}]}
                   for r in ('a_member','a_trainer','b_member')
                   for op,n in {'issue':11,'verify':21,'getUser':5,'refresh':27,'logout':10,'revoked_denial':4}.items()]
        self.workflow={'commands':360,'verified_calls':72,'statements':[{'temp_written':0}]}
    def close(self,run=RUN_ID,purpose=PURPOSE):
        return counted_close(self.trace,self.pre,self.cli,self.auth,self.workflow,run,purpose)
    def test_counts_auth_cli_protocol_and_own_close(self):
        self.assertEqual(self.close()['global_commands'],2261)
    def test_ordinary_limits_unchanged(self):
        for run,purpose in [('other',PURPOSE),(RUN_ID,'other')]:
            self.assertEqual(allowance(run,purpose),128)
            with self.assertRaises(ValueError):self.close(run,purpose)
    def test_incomplete_or_repeated_closure_denied(self):
        self.trace[-1]['confirmed']=False
        with self.assertRaises(ValueError):self.close()
        self.trace[-1].update(confirmed=True,phase='final_closure')
        with self.assertRaises(ValueError):self.close()
    def test_duplicate_auth_role_does_not_complete_matrix(self):
        self.auth[-1]=copy.deepcopy(self.auth[0])
        with self.assertRaises(ValueError):self.close()
    def test_no_hiding_extra_managed_sql_or_temp_write(self):
        self.workflow['commands']+=1
        with self.assertRaises(ValueError):self.close()
        self.workflow['commands']-=1;self.auth[0]['statements'][0]['temp_written']=1
        with self.assertRaises(ValueError):self.close()
    def test_empty_cli_receipt_not_zero_cost(self):
        self.cli=[]
        with self.assertRaises(ValueError):self.close()
    def test_numeric_observers_cannot_be_outside_counter(self):
        self.cli[0]['observer_commands']=[]
        with self.assertRaisesRegex(ValueError,'observer_count'):self.close()
    def test_over_budget_cannot_close(self):
        self.trace += [{'command':i+1,'phase':'evidence_query','confirmed':True} for i in range(1518,1606)]
        self.assertEqual(self.close()['global_commands'],2349)
        self.trace.append({'command':1607,'phase':'evidence_query','confirmed':True})
        with self.assertRaisesRegex(ValueError,'closure_budget'):self.close()


if __name__=='__main__':unittest.main()
