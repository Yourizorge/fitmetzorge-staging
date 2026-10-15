import unittest
from capacity_proposal import build,benchmark
class Tests(unittest.TestCase):
    def test_every_extra_page_is_counted_in_three_cycles_and_safety(self):
        rows=[{'phase':'setup','action':'fixed','sql':1} for _ in range(2193)]
        rows += [{'phase':phase,'action':'stream_'+label+'_rollback','sql':1} for label,phase in [('before','baseline'),('before_cleanup','measurements'),('after_cleanup','final')]]
        old={'normal_capacity':2196,'worst_including_safety':2207,'approved_limit':2226,'rows':rows,'managed_auth_commands':594}
        count={'protected_rows':100000,'table_counts':[{'table':'synthetic.rows','rows':100000}],'not_a_preservation_comparison':True,'hash_rows_transported':0}
        value=build(old,count)
        self.assertEqual(value['pages_per_cycle'],13);self.assertEqual(value['normal_commands'],2226)
        self.assertEqual(sum(value['phase_budgets'].values()),2226)
        self.assertFalse(value['new_run_authorized']);self.assertFalse(value['row_capacity_authorized'])
        self.assertGreaterEqual(value['smallest_sql_maximum'],value['worst_with_safety'])
        with self.assertRaises(ValueError):build(old,{**count,'hash_rows_transported':1})
    def test_small_duplicate_preserving_transport_and_memory_bound(self):
        value=benchmark([{'table':'synthetic.a','rows':8200},{'table':'synthetic.b','rows':1}])
        self.assertEqual(value['frames'],2);self.assertEqual(value['rows'],8201)
        self.assertFalse(value['pg_query_cost_proven']);self.assertEqual(value['hosted_requests'],0)
        with self.assertRaises(ValueError):benchmark([{'table':'synthetic.a','rows':1000001}])
if __name__=='__main__':unittest.main()
