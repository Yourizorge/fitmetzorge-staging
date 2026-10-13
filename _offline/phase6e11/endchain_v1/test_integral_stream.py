import unittest
from integral_stream import predicates,frame,statement,ALL_STATS,CONFIG,GUARD
from sql_protocol import statements

ID=lambda n:'78000000-0000-4000-8000-'+str(n).zfill(12)
class StreamTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
