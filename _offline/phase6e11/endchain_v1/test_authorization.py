import json,pathlib,unittest
from closure import AUTHORIZATION as A,RUN_ID,PURPOSE,allowance
from integral_stream import predicates

class Tests(unittest.TestCase):
    def test_one_new_separately_authorized_attempt_not_historical_retry(self):
        self.assertNotEqual(RUN_ID,A['previous_used_run'])
        self.assertTrue(A['additional_attempt_granted'])
        self.assertEqual(A['owner_instruction'],'cead148d-244b-4676-b6a3-907098ac55df')
        for old in A['earlier_used_runs']:
            self.assertEqual(allowance(old,PURPOSE),128)
        self.assertTrue(A['historical_no_go_unchanged'])
        self.assertEqual(A['reserved_attempt_count'],1)
        self.assertEqual(allowance(A['previous_used_run'],PURPOSE),128)
        self.assertEqual(allowance(RUN_ID,PURPOSE),2226)
    def test_js_and_python_exact_binding(self):
        p=pathlib.Path(__file__).parent
        text=(p/'budget.mjs').read_text()
        self.assertIn("ENDCHAIN_RUN_ID='"+RUN_ID+"'",text)
        self.assertIn("PURPOSE='"+PURPOSE+"'",text)
        self.assertNotIn(A['previous_used_run'],text)
    def test_old_controller_rows_remain_protected(self):
        c={'window':RUN_ID,'a':RUN_ID,'b':RUN_ID,'runs':{'seed':RUN_ID}}
        q=predicates({'schema':'fmz6e11_controller_private','name':'runs','columns':['id']},{},c)
        self.assertEqual(q,"id<>'"+RUN_ID+"'")
        self.assertNotIn(A['previous_used_run'],q)
    def test_current_safety_limits_not_waived(self):
        self.assertTrue(A['current_evidence_requirements_unchanged'])
        self.assertEqual([A[x] for x in ('maximum_sql','maximum_seconds','ordinary_stop_seconds','query_connect_seconds','lock_seconds','collectors','automatic_retries')],[2226,600,540,5,1,1,0])

if __name__=='__main__':unittest.main()
