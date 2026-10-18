import copy,unittest
from integral_io import delta
from utility_binding import UtilityBindings,other_load


def sample(reader=0,own=0,other=0):
    return {'reset':'r','dealloc':0,'track_utility':'on','track':'all','statements':[
        {'queryid':qid,'calls':calls,'since':'s','temp_read':0,'temp_written':0,
         'wal':'0','exec_ms':float(calls)} for qid,calls in [('1',reader),('2',own),('3',other)]],
        'background':{'temp_bytes':0,'reset':'b'},'health':{'io_wait':0,'long_active':0}}


class UtilityTests(unittest.TestCase):
    def bind(self):
        binding=UtilityBindings();first=binding.observe('source',sample(),sample(1,1),'1')
        delta(sample(),sample(1,1),{'1':1,'2':1});binding.confirm('source',first)
        return binding

    def test_isolated_first_observation_and_same_source_with_other_query(self):
        b=self.bind();before=sample(1,1);after=sample(2,2,1)
        result=b.observe('source',before,after,'1')
        self.assertTrue(result['previously_bound']);self.assertTrue(result['unambiguous'])
        self.assertEqual(result['queryid'],'2');self.assertEqual(result['other_query_calls'],{'3':1})
        self.assertEqual(delta(before,after,{'2':1,'1':1})['own_temp_written'],0)
        background=other_load(before,after,result)
        self.assertEqual(background['actor'],'UNKNOWN');self.assertFalse(background['attributed_to_collector'])

    def test_ambiguous_first_observation_remains_blocked(self):
        b=UtilityBindings();result=b.observe('source',sample(),sample(1,1,1),'1')
        self.assertFalse(result['unambiguous'])
        with self.assertRaises(ValueError):b.confirm('source',result)

    def test_binding_is_not_reused_for_another_source_or_stream(self):
        for b,source in [(self.bind(),'different'),(UtilityBindings(),'source')]:
            self.assertFalse(b.observe(source,sample(),sample(1,1,1),'1')['unambiguous'])

    def test_missing_and_duplicate_own_calls_block_even_with_other_query(self):
        b=self.bind()
        for count in (1,3):
            self.assertFalse(b.observe('source',sample(1,1),sample(2,count,1),'1')['unambiguous'])

    def test_duplicate_and_disappeared_query_entries_block(self):
        for mode in ('duplicate','missing'):
            after=sample(1,1)
            if mode=='duplicate':after['statements'].append(copy.deepcopy(after['statements'][0]))
            else:after['statements'].pop()
            with self.assertRaises(ValueError):self.bind().observe('source',sample(),after,'1')

    def test_negative_counter_blocks(self):
        with self.assertRaises(ValueError):self.bind().observe('source',sample(2,2),sample(3,1),'1')

    def test_own_spill_and_counter_replacement_remain_blocked(self):
        for key,value in [('temp_written',1),('since','new')]:
            before=sample(1,1);after=sample(2,2,1);after['statements'][1][key]=value
            observation=self.bind().observe('source',before,after,'1')
            self.assertTrue(observation['unambiguous'])
            with self.assertRaises(ValueError):delta(before,after,{'1':1,observation['queryid']:1})

    def test_unknown_spill_and_heavy_load_are_not_silently_accepted(self):
        for key,value in [('temp_written',1),('temp_read',1),('exec_ms',2501)]:
            before=sample(1,1);after=sample(2,2,1);after['statements'][2][key]=value
            observation=self.bind().observe('source',before,after,'1')
            with self.assertRaises(ValueError):other_load(before,after,observation)

    def test_resets_and_project_health_still_block(self):
        for field in ('reset','dealloc','health'):
            before=sample(1,1);after=sample(2,2,1)
            if field=='reset':after['reset']='new'
            elif field=='dealloc':after['dealloc']=1
            else:after['health']['io_wait']=1
            observation=self.bind().observe('source',before,after,'1')
            with self.assertRaises(ValueError):other_load(before,after,observation)

    def test_confirm_cannot_replace_an_existing_binding(self):
        b=self.bind()
        with self.assertRaises(ValueError):b.confirm('source',{'unambiguous':True,'queryid':'3'})

    def test_disabled_or_missing_utility_tracking_blocks_before_attribution(self):
        for field,value in [('track_utility','off'),('track_utility',None),('track','none'),('track',None)]:
            for where in ('before','after'):
                before=sample(1,1);after=sample(2,2,1)
                (before if where=='before' else after)[field]=value
                with self.assertRaisesRegex(ValueError,'stream_utility_tracking_disabled'):
                    self.bind().observe('source',before,after,'1')


if __name__=='__main__':unittest.main()
