import hashlib,json,pathlib,re,unittest
from closure import AUTHORIZATION as A,RUN_ID,PURPOSE,allowance
from integral_stream import predicates

class Tests(unittest.TestCase):
    def test_one_new_separately_authorized_attempt_not_historical_retry(self):
        self.assertNotEqual(RUN_ID,A['previous_used_run'])
        self.assertTrue(A['additional_attempt_granted'])
        self.assertEqual(RUN_ID,'1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d')
        self.assertEqual(A['previous_used_run'],'debe3298-9772-40b1-a9f4-8e3d99c8fd20')
        self.assertEqual(A['owner_instruction'],'f39c835e-3db0-4149-9011-998f00aff831')
        self.assertEqual(A['owner_instruction_sha256'],'c2fd22c7b8e0a95009eb29c6d62333deca1e778e528da9f9b02c1c8f759c79cf')
        for old in A['earlier_used_runs']:
            self.assertEqual(allowance(old,PURPOSE),128)
        self.assertTrue(A['historical_no_go_unchanged'])
        self.assertEqual(A['reserved_attempt_count'],1)
        self.assertEqual(allowance(A['previous_used_run'],PURPOSE),128)
        self.assertEqual(allowance(RUN_ID,PURPOSE),2237)
    def test_js_and_python_exact_binding(self):
        p=pathlib.Path(__file__).parent
        text=(p/'budget.mjs').read_text()
        self.assertIn("ENDCHAIN_RUN_ID='"+RUN_ID+"'",text)
        self.assertIn("PURPOSE='"+PURPOSE+"'",text)
        self.assertNotIn(A['previous_used_run'],text)
        from metered_composition import capacity
        limits=re.search(r'Object.freeze\(\{(.*?)\}\)',text,re.S)[1]
        self.assertEqual({k:int(v) for k,v in re.findall(r'(\w+):(\d+)',limits)},capacity()['phase_budgets'])
        self.assertIn('?2237:128',text)
    def test_old_controller_rows_remain_protected(self):
        c={'window':RUN_ID,'a':RUN_ID,'b':RUN_ID,'runs':{'seed':RUN_ID}}
        q=predicates({'schema':'fmz6e11_controller_private','name':'runs','columns':['id']},{},c)
        self.assertEqual(q,"id<>'"+RUN_ID+"'")
        self.assertNotIn(A['previous_used_run'],q)
    def test_current_safety_limits_not_waived(self):
        self.assertTrue(A['current_evidence_requirements_unchanged'])
        self.assertEqual([A[x] for x in ('maximum_sql','maximum_rows_per_cycle','maximum_cycles','maximum_seconds','ordinary_stop_seconds','query_connect_seconds','lock_seconds','collectors','automatic_retries')],[2237,106496,3,600,540,5,1,1,0])
    def test_numeric_reference_is_immutable_scope_evidence_only(self):
        root=pathlib.Path(__file__).resolve().parents[3];ref=A['numeric_evidence']
        path=root/ref['result'];raw=path.read_bytes();manifest=path.with_name('MANIFEST.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['result_sha256'])
        self.assertEqual(hashlib.sha256(manifest).hexdigest(),ref['manifest_sha256'])
        self.assertEqual(json.loads(manifest)['files']['result.json'],ref['result_sha256'])
        receipt=json.loads(raw)
        self.assertEqual(receipt['run_id'],ref['run_id'])
        self.assertEqual(receipt['capacity']['protected_rows'],ref['protected_rows'])
        self.assertEqual(receipt['status'],'NUMERIC_DIAGNOSIS_PASS_NOT_WORKFLOW_PASS')
        self.assertTrue(ref['not_a_preservation_comparison'])
        self.assertEqual(receipt['hash_rows_transported'],0)
    def test_only_current_m44_identity_has_exception_old_receipts_retained(self):
        from migration_boundary import source
        text=source(pathlib.Path(__file__).resolve().parents[3])
        self.assertEqual(re.findall(r"when id='([^']+)'::uuid then (\d+)",text),[(RUN_ID,'2237')])
        for old in [A['previous_used_run'],*A['earlier_used_runs']]:
            self.assertEqual(text.count("'"+old+"'::uuid"),3)
        self.assertEqual(text.count("'"+RUN_ID+"'::uuid"),4)

if __name__=='__main__':unittest.main()
