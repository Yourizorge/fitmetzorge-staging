import copy,json,unittest
from size_diagnosis import numeric,capacity,run,Probe,GUARD,INVENTORY,ALL_STATS,INSTANCE

class Tests(unittest.TestCase):
    def test_historical_input_uses_extended_path_before_any_access_grant(self):
        from unittest.mock import patch,Mock
        from size_diagnosis import historical_binding
        target=Mock();target.read_text.return_value='{"plan":[]}'
        with patch('size_diagnosis.disk',return_value=target) as path:
            self.assertEqual(historical_binding('long-historical-path'),{'plan':[]})
        path.assert_called_once_with('long-historical-path')
    def test_numeric_has_same_filters_without_hash_content_sort_or_limit(self):
        plans=[{'name':'auth.sessions','predicate':'user_id is null or user_id::text not in (\'00000000-0000-0000-0000-000000000000\')'}]
        sql=numeric(plans)
        for word in ('sha256','to_jsonb','order by','limit','select *'):self.assertNotIn(word,sql.lower())
        self.assertIn(plans[0]['predicate'],sql)
    def test_counts_duplicates_null_and_exact_json_size(self):
        plans=[{'name':'a.b','predicate':'true'}]
        v=capacity([{'i':'0','n':'100000'}],plans)
        self.assertEqual(v['protected_rows'],100000);self.assertEqual(v['hash_rows_transported'],0)
        self.assertEqual(v['pages_at_8192'],13);self.assertGreater(v['planned_json_frame_bytes'],6400000)
        for rows in ([],[{'i':'1','n':'1'}],[{'i':'0','n':'-1'}],[{'i':'0','n':'1','secret':'x'}]):
            with self.assertRaises(ValueError):capacity(rows,plans)
    def test_failure_always_rolls_back_and_never_retries(self):
        for phase in ('guard','inventory','exact_numeric_count','final_guard'):
            commands=[];saved={};samples=0
            identity={'ro':'on','isolation':'repeatable read','instance_sha':INSTANCE,'db':'postgres','role':'postgres','ssl':True,'backend':1}
            def query(sql):
                nonlocal samples
                commands.append(sql)
                if sql=='ROLLBACK':return []
                if sql==GUARD:
                    if phase=='guard' or phase=='final_guard' and commands.count(GUARD)==2:raise TimeoutError()
                    return [identity]
                if sql==INVENTORY:
                    if phase=='inventory':raise TimeoutError()
                    return [{'schema':'a','name':'b'}]
                if sql.startswith('EXPLAIN'):
                    qid=1 if ALL_STATS in sql else 2
                    return [{'QUERY PLAN':[{'Query Identifier':qid,'Plan':{'Actual Rows':1},'Execution Time':0}]}]
                if sql==ALL_STATS:
                    samples+=1
                    return [{'value':{'reset':'x','dealloc':0,'background':{'reset':'x','temp_bytes':0},'health':{'io_wait':0,'long_active':0},
                        'statements':[{'queryid':str(i),'calls':samples-1,'since':'x','temp_read':0,'temp_written':0,'wal':'0','exec_ms':samples-1} for i in (1,2)]}}]
                if 'numeric_size_v1' in sql:
                    if phase=='exact_numeric_count':raise TimeoutError()
                    return [{'i':'0','n':'2'}]
                return [{}]
            def save(name,value):self.assertNotIn(name,saved);saved[name]=copy.deepcopy(value)
            result=run(Probe(query,save),[{'name':'a.b','predicate':'true'}])
            self.assertEqual(result['status'],'NO_GO');self.assertTrue(result['rollback_confirmed'])
            self.assertEqual(commands[-1],'ROLLBACK');self.assertEqual(commands.count('ROLLBACK'),1)
            self.assertEqual(result['error']['phase'],phase)

if __name__=='__main__':unittest.main()
