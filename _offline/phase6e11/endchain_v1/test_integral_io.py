import copy,unittest
from integral_io import delta,check_plan,QueryIO

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
    def test_read_wal_rejected_but_expected_mutation_wal_recorded(self):
        self.assertEqual(delta(sample(),sample(2),{'1':2})['own_wal_bytes'],6)
        with self.assertRaisesRegex(ValueError,'io_read_wal'):delta(sample(),sample(2),{'1':2},{'1'})
        after=sample(2);after['statements'][0]['wal']='0'
        self.assertEqual(delta(sample(),after,{'1':2},{'1'})['own_wal_bytes'],0)
    def test_terminal_reader_rejects_nested_wal(self):
        for field in ('WAL Bytes','WAL Records','WAL FPI'):
            p=[{'Query Identifier':2,'Execution Time':1,'Plan':{'Actual Rows':1,'Plans':[{field:1}]}}]
            with self.assertRaisesRegex(ValueError,'io_read_wal'):check_plan(p,True)
    def test_read_write_family_collision_and_missing_class_fail_closed(self):
        q=QueryIO(lambda *a:self.fail('no SQL expected'))
        q.register('source1','1',True)
        q.register('source2','1',True)
        with self.assertRaisesRegex(ValueError,'family_collision'):q.register('source3','1',False)
        with self.assertRaisesRegex(ValueError,'class_missing'):q.register('source4','2',None)
        q.register('write-source','3',False)
        self.assertEqual(q.readonly,{'1'})
    def test_closing_plan_must_match_the_bound_reader(self):
        plan=[{'Query Identifier':999,'Execution Time':1,'Plan':{'Actual Rows':1}}]
        q=QueryIO(lambda *a:[{'QUERY PLAN':plan}])
        q.reader_id='1';q.checkpoint=lambda:{'own_wal_bytes':0}
        with self.assertRaisesRegex(ValueError,'io_closing_reader_identity'):q.close()
        plan[0]['Query Identifier']=1
        self.assertEqual(q.close()['closing_queryid'],'1')

if __name__=='__main__':unittest.main()
