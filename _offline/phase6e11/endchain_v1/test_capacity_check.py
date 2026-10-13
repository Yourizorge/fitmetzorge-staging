import copy, unittest
from capacity_check import build,cursor_budget,lifecycle_count,verify_receipt

def fixture():
    counts={'begin':71,'binding':71,'call':71,'commit':71,'seal':71,'identity':1,
        'controller_evidence':356,'measurement':144,'read_begin':20,'read_binding':20,'read_call':20,'rollback':20}
    phases=[p for p,n in counts.items() for _ in range(n)]+['measurement','controller_evidence']
    return {'exitcode':0,'hosted_calls':0,'sources_unchanged':True,'sources':{},'result':{
        'status':'LOCAL_COMPOSED_71_PASS','pairs':71,'deletes':123,'seconds':1,
        'commands':[{'command':i+1,'phase':p} for i,p in enumerate(phases)]}}

class Capacity(unittest.TestCase):
    def test_receipt_counts_every_sql(self):self.assertEqual(sum(verify_receipt(fixture(),False).values()),938)
    def test_unknown_cost_is_not_zero(self):
        r=build(fixture(),False)
        self.assertFalse(r['complete_budget']);self.assertFalse(r['hosted_admitted'])
        self.assertIsNone(r['recommended_new_maximum']);self.assertEqual(len(r['not_yet_costed']),7)
    def test_current_capacity_is_not_admitted(self):
        r=build(fixture(),False)
        self.assertEqual(r['source_bound_known_capacity'],1297)
        self.assertEqual(r['known_capacity_above_limit'],17)
    def test_guard_observer_envelopes_use_pg17_parser(self):
        self.assertEqual(lifecycle_count(),{'guard_install':6,'guard_inspect':1,'guard_remove':5,
            'guard_removed_inspect':1,'observer_install':5,'observer_inspect':1,'observer_remove':5,'observer_removed_inspect':1})
    def test_stream_bound_is_original_no_silent_row_limit_reduction(self):
        c=cursor_budget();self.assertEqual(c['row_ceiling'],131072);self.assertEqual(c['cycles'],2)
        self.assertEqual(c['fetches_per_cycle'],17);self.assertEqual(c['commands'],118)
    def test_gap_duplicate_or_missing_commands_rejected(self):
        for change in ('gap','duplicate','remove'):
            v=fixture()
            if change=='gap':v['result']['commands'][5]['command']=9
            elif change=='duplicate':v['result']['commands'].append(v['result']['commands'][-1])
            else:v['result']['commands'].pop()
            with self.assertRaises(ValueError):verify_receipt(v,False)
    def test_missing_deletes_or_incomplete_pair_rejected(self):
        for k,v in [('pairs',70),('deletes',122),('status','NO_GO')]:
            f=fixture();f['result'][k]=v
            with self.assertRaises(ValueError):verify_receipt(f,False)
    def test_source_change_or_hosted_receipt_rejected(self):
        for k,v in [('sources_unchanged',False),('hosted_calls',1),('exitcode',2)]:
            f=fixture();f[k]=v
            with self.assertRaises(ValueError):verify_receipt(f,False)
    def test_rollback_must_precede_final_counter(self):
        f=fixture();f['result']['commands'][-1]['phase']='measurement';f['result']['commands'][-2]['phase']='controller_evidence'
        with self.assertRaisesRegex(ValueError,'closure_not_counted'):verify_receipt(f,False)

if __name__=='__main__':unittest.main()
