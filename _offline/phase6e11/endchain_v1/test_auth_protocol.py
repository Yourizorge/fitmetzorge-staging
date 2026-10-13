import copy,unittest
from auth_protocol import difference

def frame(n):return {'reset':'r','dealloc':0,'track_utility':'on','statements':[
    {'queryid':'1','calls':n,'since':'s','temp_written':0,'temp_read':0,'wal_bytes':str(n*4),'exec_ms':float(n)}]}

class AuthProtocolTests(unittest.TestCase):
    def test_all_top_level_commands_and_wal(self):
        d=difference(frame(1),frame(9));self.assertEqual(d['commands'],8);self.assertEqual(d['wal_bytes'],32)
        self.assertFalse(d['query_text_read'])
    def test_counter_resets_missing_and_utility_disabled(self):
        for k,v in [('reset','new'),('dealloc',1),('track_utility','off'),('statements',[])]:
            b=frame(2);b[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):difference(frame(1),b)
    def test_spill_and_counter_replacement(self):
        for k,v in [('since','other'),('temp_written',1),('calls',0)]:
            b=frame(2);b['statements'][0][k]=v
            with self.assertRaises(ValueError):difference(frame(1),b)

if __name__=='__main__':unittest.main()
