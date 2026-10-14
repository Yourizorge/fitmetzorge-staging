import copy,unittest
from application_io import active_pair
class Tests(unittest.TestCase):
    def test_unchanged_migration_counters_are_not_new_work(self):
        a={'reset':'r','dealloc':0,'track_utility':'on','statements':[{'queryid':str(i),'calls':1} for i in range(2000)]};b=copy.deepcopy(a);b['statements'][3]['calls']=2
        x,y=active_pair(a,b);self.assertEqual(x['statements'],[{'queryid':'3','calls':1}]);self.assertEqual(y['statements'],[{'queryid':'3','calls':2}]);self.assertEqual(len(a['statements']),2000)
    def test_reset_and_replacement_remain_visible(self):
        a={'reset':'a','statements':[{'queryid':'1','calls':2,'since':'a'}]};b={'reset':'b','statements':[{'queryid':'1','calls':1,'since':'b'}]}
        x,y=active_pair(a,b);self.assertEqual(y,b);self.assertEqual(x,a)
    def test_missing_duplicate_or_excessive_counters_fail(self):
        for b in ({'statements':[]},{'statements':[{'queryid':'1'}]*2},{'statements':[{'queryid':str(i)} for i in range(5001)]}):
            with self.assertRaises(ValueError):active_pair({'statements':[{'queryid':'1'}]},b)
if __name__=='__main__':unittest.main()
