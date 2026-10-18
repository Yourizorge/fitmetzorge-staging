import unittest
from integral_stream import predicates,frame,statement,ALL_STATS,CONFIG,GUARD,run,INVENTORY,ROWS,PAGE,PAGES,PROTOCOL_CAPACITY
from sql_protocol import statements

ID=lambda n:'78000000-0000-4000-8000-'+str(n).zfill(12)
class StreamTests(unittest.TestCase):
    def test_only_new_quota_history_has_separate_pending_boundary(self):
        context={'window':ID(4),'a':ID(5),'b':ID(6),'runs':{'seed':ID(7)},'migration_boundary':True}
        row={'schema':'supabase_migrations','name':'schema_migrations','columns':['version']}
        self.assertEqual(predicates(row,{'a':ID(1)},context),"version<>'20261018070231'")
        context['migration_boundary']=False
        self.assertEqual(predicates(row,{'a':ID(1)},context),'true')
    def test_primary_failure_survives_failed_stop_storage_and_rollback(self):
        calls=[]
        def query(phase,sql,args=()):
            calls.append(phase)
            if sql==GUARD:raise ValueError('primary_guard_failure')
            if sql=='ROLLBACK':raise OSError('secondary_terminal_failure')
            return []
        def save(name,value):raise OSError('secondary_disk_failure')
        with self.assertRaisesRegex(ValueError,'primary_guard_failure') as result:
            run(query,save,{}, {},'fail')
        self.assertEqual(result.exception.__notes__,['stop_storage_failed:OSError','rollback_failed:OSError'])
        self.assertEqual(calls[-1],'stream_fail_rollback')
    def test_terminal_duplicate_and_null_hash_frames(self):
        rows=[{'i':'0','h':'a'*64,'keep':'1'}]*2
        frame(rows,2)
        with self.assertRaises(ValueError):frame(rows,1)
        with self.assertRaises(ValueError):frame([{'i':'0','h':None,'keep':'1'}],1)
    def test_only_exact_new_workspace_and_proof_are_excluded(self):
        ids={'a':ID(1),'b':ID(2),'c':ID(3)};c={'window':ID(4),'a':ID(5),'b':ID(6),'runs':{'seed':ID(7)}}
        p=predicates({'schema':'fmz6e11_private','name':'plans','columns':['workspace_id']},ids,c)
        self.assertIn(ID(5),p);self.assertIn(ID(6),p)
        self.assertNotEqual(p,'false')
        self.assertEqual(predicates({'schema':'public','name':'profiles','columns':['id']},ids,c),'true')
    def test_no_query_text_and_no_sql_sort_of_member_rows(self):
        self.assertIn('pg_stat_statements(false)',ALL_STATS)
        sql=statement([{'name':'public.synthetic','predicate':'true'}])
        self.assertNotIn('order by',sql.lower());self.assertNotIn('string_agg',sql.lower())
        for q in (sql,ALL_STATS,CONFIG,GUARD):self.assertEqual(len(statements(q)),1)
    def test_ambiguous_utility_preserves_both_numeric_samples_before_stop(self):
        from copy import deepcopy
        saved={};calls=[];samples=[]
        before={'statements':[{'queryid':'1','calls':1}]}
        after={'statements':[{'queryid':'1','calls':2},{'queryid':'2','calls':1},{'queryid':'3','calls':1}]}
        samples.extend([before,after])
        def query(phase,sql,args=()):
            calls.append(phase);query.terminal_count=-1
            if sql==GUARD:return [{'ro':'on','isolation':'repeatable read','db':'postgres','role':'postgres','ssl':True}]
            if sql==INVENTORY:return [{'schema':'public','name':'synthetic_'+str(i),'columns':['id']} for i in range(100)]
            if sql.startswith('EXPLAIN'):return [{'QUERY PLAN':[{'Query Identifier':1,'Execution Time':0,'Plan':{'Actual Rows':1,'Temp Written Blocks':0,'Temp Read Blocks':0,'WAL Bytes':0,'Actual Total Time':0}}]}]
            if sql==ALL_STATS:return [{'value':samples.pop(0)}]
            return []
        def save(name,value):
            self.assertNotIn(name,saved);saved[name]=deepcopy(value)
        context={'window':ID(4),'a':ID(5),'b':ID(6),'runs':{'seed':ID(7)}}
        with self.assertRaisesRegex(ValueError,'stream_utility_attribution'):
            run(query,save,{'member':ID(1)},context,'before')
        prefix='integral-stream-before-utility-000'
        self.assertEqual(saved[prefix+'-before.json']['sample'],before)
        self.assertEqual(saved[prefix+'-after.json']['sample'],after)
        self.assertEqual(saved[prefix+'-attribution.json']['changed_query_calls'],{'2':1,'3':1})
        self.assertFalse(saved[prefix+'-attribution.json']['background_attributed_to_collector'])
        self.assertEqual(saved['integral-stream-before-stop.json']['failed_phase'],'utility_attribution')
        self.assertEqual(saved['integral-stream-before-stop.json']['reason_code'],'stream_utility_attribution')
        self.assertEqual(calls[-1],'stream_before_rollback')
        self.assertFalse(any('FETCH' in phase for phase in calls))

    def test_exclusions_applied_before_transport_without_changing_predicates(self):
        for predicate in ('false','true','user_id is null or user_id::text not in (\'synthetic\')'):
            sql=statement([{'name':'public.synthetic','predicate':predicate}])
            self.assertIn('where ('+predicate+')',sql)
            self.assertIn("'1'::text keep",sql)
            self.assertNotIn('case when',sql.lower())

    def capacity_run(self,size,limit=9,page=4,short=False,interrupt=False,expected=None):
        from unittest.mock import patch
        import integral_stream
        saved={};calls=[];stats={'1':0,'2':0};received=[]
        def query(phase,sql,args=()):
            calls.append(sql);query.terminal_count=0
            if sql==GUARD:return [{'ro':'on','isolation':'repeatable read','db':'postgres','role':'postgres','ssl':True}]
            if sql==INVENTORY:return [{'schema':'public','name':'synthetic_'+str(i),'columns':['id']} for i in range(100)]
            if sql.startswith('EXPLAIN'):return [{'QUERY PLAN':[{'Query Identifier':1,'Execution Time':0,'Plan':{'Actual Rows':1,'Temp Written Blocks':0,'Temp Read Blocks':0,'WAL Bytes':0,'Actual Total Time':0}}]}]
            if sql==ALL_STATS:
                stats['1']+=1
                return [{'value':{'statements':[{'queryid':k,'calls':v} for k,v in stats.items()]}}]
            if sql.startswith(('DECLARE','FETCH','CLOSE','select count(*)')):stats['2']+=1
            if sql.startswith('select count(*)'):
                self.assertIn('integral-stream-capacity-binding.json',saved)
                query.terminal_count=1;return [{'protected_rows':str(min(size,limit+1))}]
            if sql.startswith('FETCH'):
                n=int(sql.split()[2]);received.append(n)
                if interrupt:raise OSError('synthetic_transport_break')
                if short:n-=1
                query.terminal_count=n
                return [{'i':'0','h':'a'*64,'keep':'1'} for _ in range(n)]
            return []
        context={'window':ID(4),'a':ID(5),'b':ID(6),'runs':{'seed':ID(7)}}
        error=None;result=None
        with patch.object(integral_stream,'ROWS',limit),patch.object(integral_stream,'PAGE',page),patch.object(integral_stream,'delta',return_value={'queries':[]}),patch.object(integral_stream,'other_load',return_value={'queries':[]}):
            try:result=run(query,lambda n,v:saved.update({n:v}),{'member':ID(1)},context,'capacity',expected)
            except Exception as e:error=e
        self.assertEqual(calls[-1],'ROLLBACK')
        return result,error,saved,calls,received

    def test_row_ceiling_checked_before_hash_cursor_or_transport(self):
        result,error,saved,calls,received=self.capacity_run(10)
        self.assertIsNone(result);self.assertEqual(str(error),'stream_row_ceiling')
        stop=saved['integral-stream-capacity-stop.json']
        self.assertEqual((stop['failed_phase'],stop['reason_code'],stop['received_rows'],stop['row_limit']),
                         ('row_capacity','stream_row_ceiling',0,9))
        self.assertFalse(any(q.startswith(('DECLARE','FETCH')) for q in calls))
        self.assertNotIn('integral-stream-capacity.json',saved)

    def test_protected_drift_retains_both_scoped_hashes_and_precise_stop(self):
        before=self.capacity_run(6)[0]
        result,error,saved,calls,received=self.capacity_run(7,expected=before)
        self.assertIsNone(result);self.assertEqual(str(error),'stream_protected_drift')
        pair=saved['integral-stream-capacity-comparison.json']
        self.assertFalse(pair['equal']);self.assertEqual(pair['before'],before['tables'])
        self.assertEqual(pair['after']['public.synthetic_0']['rows'],7)
        stop=saved['integral-stream-capacity-stop.json']
        self.assertEqual((stop['failed_phase'],stop['reason_code']),('protected_comparison','stream_protected_drift'))

    def test_zero_full_and_partial_last_pages_are_complete(self):
        for size,pages in [(0,[]),(4,[4]),(8,[4,4]),(9,[4,4,1]),(6,[4,2])]:
            result,error,saved,calls,received=self.capacity_run(size)
            self.assertIsNone(error);self.assertEqual(received,pages)
            self.assertEqual(result['rows'],size);self.assertTrue(result['complete_by_same_snapshot_capacity'])
            self.assertEqual(result['protocol_commands'],15+2*len(pages))
            self.assertEqual(result['tables']['public.synthetic_0']['rows'],size)

    def test_real_limit_no_overshoot_or_extra_hash_fetch(self):
        self.assertEqual((ROWS,PAGE,PAGES,PROTOCOL_CAPACITY),(106496,8192,13,41))
        for size in (65536,100843,ROWS-1,ROWS,ROWS+1):
            result,error,saved,calls,received=self.capacity_run(size,ROWS,PAGE)
            self.assertLessEqual(sum(received),ROWS)
            if size>ROWS:
                self.assertEqual(str(error),'stream_row_ceiling');self.assertEqual(received,[])
                self.assertFalse(any(q.startswith(('DECLARE','FETCH')) for q in calls))
                self.assertEqual(saved['integral-stream-capacity-stop.json']['failed_phase'],'row_capacity')
            else:
                self.assertIsNone(error);self.assertEqual(sum(received),size)
                self.assertLessEqual(result['protocol_commands'],PROTOCOL_CAPACITY)
                self.assertEqual(result['protocol_commands'],len(calls))
                self.assertLessEqual(len(received),PAGES)

    def test_truncation_and_interruption_do_not_produce_success(self):
        for kwargs in ({'short':True},{'interrupt':True}):
            result,error,saved,calls,received=self.capacity_run(6,**kwargs)
            self.assertIsNotNone(error);self.assertIsNone(result)
            self.assertNotIn('integral-stream-capacity.json',saved)

    def test_capacity_does_not_hash_sort_or_change_filters(self):
        from integral_stream import capacity_statement
        plans=[{'name':'public.synthetic','predicate':'allowed is true'}, {'name':'cron.job_run_details','predicate':'false'}]
        sql=capacity_statement(plans)
        self.assertIn('limit 106497',sql)
        for p in plans:self.assertIn('where ('+p['predicate']+')',sql)
        for forbidden in ('sha256','to_jsonb','order by','distinct'):
            self.assertNotIn(forbidden,sql.lower())
        self.assertEqual(len(statements(sql)),1)

if __name__=='__main__':unittest.main()
