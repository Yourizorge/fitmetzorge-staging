import copy,unittest
from integral_io import delta,check_plan

def sample(calls=0,temp=0):
    return {'reset':'r','dealloc':0,'statements':[{'queryid':'1','calls':calls,'since':'s',
        'temp_read':0,'temp_written':temp,'wal':str(calls*3),'exec_ms':calls}],
        'background':{'temp_bytes':0,'reset':'b'},'health':{'io_wait':0,'long_active':0}}

class IOTests(unittest.TestCase):
    def test_own_and_background_are_separate(self):
        b=sample(2);b['background']['temp_bytes']=50000000
        r=delta(sample(),b,{'1':2});self.assertEqual(r['own_temp_written'],0)
        self.assertEqual(r['background_temp_bytes'],50000000)
    def test_missing_extra_spill_reset_health(self):
        for field,value in [('calls',3),('temp_written',1),('since','other')]:
            b=sample(2);b['statements'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):delta(sample(),b,{'1':2})
        for field,value in [('reset','other'),('dealloc',1)]:
            b=sample(2);b[field]=value
            with self.assertRaises(ValueError):delta(sample(),b,{'1':2})
        b=sample(2);b['health']['io_wait']=1
        with self.assertRaises(ValueError):delta(sample(),b,{'1':2})
    def test_terminal_plan_checks_nested_spill(self):
        p=[{'Query Identifier':2,'Execution Time':1,'Plan':{'Actual Rows':1,'Plans':[{'Temp Written Blocks':1}]}}]
        with self.assertRaises(ValueError):check_plan(p,True)
        p[0]['Plan']['Plans']=[];self.assertEqual(check_plan(p,True),'2')
    def test_plan_identity_must_be_lossless_integer(self):
        with self.assertRaises(ValueError):check_plan([{'Query Identifier':'2'}])

if __name__=='__main__':unittest.main()
