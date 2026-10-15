import unittest
from integral_stream import predicates,frame,statement,ALL_STATS,CONFIG,GUARD,run,INVENTORY
from sql_protocol import statements

ID=lambda n:'78000000-0000-4000-8000-'+str(n).zfill(12)
class StreamTests(unittest.TestCase):
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
            if sql.startswith('EXPLAIN'):return [{'QUERY PLAN':[{'Query Identifier':1}]}]
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

    def test_row_ceiling_preserves_precise_reason_and_rolls_back(self):
        from unittest.mock import patch
        import integral_stream
        saved={};calls=[];stats={'1':0,'2':0,'3':0};pages=[4,1]
        def query(phase,sql,args=()):
            calls.append(sql);query.terminal_count=0
            if sql==GUARD:return [{'ro':'on','isolation':'repeatable read','db':'postgres','role':'postgres','ssl':True}]
            if sql==INVENTORY:return [{'schema':'public','name':'synthetic_'+str(i),'columns':['id']} for i in range(100)]
            if sql.startswith('EXPLAIN'):return [{'QUERY PLAN':[{'Query Identifier':1}]}]
            if sql==ALL_STATS:
                stats['1']+=1
                return [{'value':{'statements':[{'queryid':k,'calls':v} for k,v in stats.items()]}}]
            if sql.startswith('DECLARE'):stats['2']+=1
            if sql.startswith('FETCH'):
                stats['3']+=1;n=pages.pop(0);query.terminal_count=n
                return [{'i':'0','h':'a'*64,'keep':'1'} for _ in range(n)]
            return []
        context={'window':ID(4),'a':ID(5),'b':ID(6),'runs':{'seed':ID(7)}}
        with patch.object(integral_stream,'ROWS',4),patch.object(integral_stream,'PAGE',4),patch.object(integral_stream,'delta',return_value={'queries':[]}):
            with self.assertRaisesRegex(ValueError,'stream_row_ceiling'):
                run(query,lambda n,v:saved.update({n:v}),{'member':ID(1)},context,'capacity')
        stop=saved['integral-stream-capacity-stop.json']
        self.assertEqual((stop['failed_phase'],stop['reason_code'],stop['received_rows'],stop['row_limit']),
                         ('row_capacity','stream_row_ceiling',5,4))
        self.assertEqual(calls[-1],'ROLLBACK')
        self.assertNotIn('integral-stream-capacity.json',saved)

if __name__=='__main__':unittest.main()
