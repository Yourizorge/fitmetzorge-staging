import copy,unittest
from cli_stat_reader import compare

def snap(calls=2):
    return dict(reset='fixed',dealloc=0,track_utility='on',track='top',
        statements=[dict(queryid='1',calls=calls,since='fixed',temp_written=0,wal='0')])

class Tests(unittest.TestCase):
    def test_complete_protocol_visible(self):
        self.assertTrue(compare(snap(),snap(17),14)['all_protocol_visible'])
    def test_missing_protocol_not_promoted_to_pass(self):
        self.assertFalse(compare(snap(),snap(10),14)['all_protocol_visible'])
    def test_reset_missing_and_replaced_fail(self):
        for field,value in [('reset','changed'),('dealloc',1),('track_utility','off'),('statements',[])]:
            after=snap(17);after[field]=value
            with self.assertRaises(ValueError):compare(snap(),after,14)
        after=snap(17);after['statements'][0]['since']='changed'
        with self.assertRaises(ValueError):compare(snap(),after,14)
    def test_temp_is_not_hidden(self):
        after=snap(17);after['statements'][0]['temp_written']=1
        self.assertEqual(compare(snap(),after,14)['temp_written'],1)

if __name__=='__main__':unittest.main()
