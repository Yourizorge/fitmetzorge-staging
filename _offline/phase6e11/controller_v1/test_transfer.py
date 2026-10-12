import hashlib,importlib.util,pathlib,tempfile,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('controller_install_transfer_test',HERE/'install.py')
i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=i.stream;t=m.t

def plan():
    return [{'name':n,'cohorts':{'protected':'true'}} for n in
      ['public.t'+str(x) for x in range(153)]+['fmz6e11_request_private.control','fmz6e11_request_private.receipts']]

class Transfer(unittest.TestCase):
    def test_exact_tables_not_open_ended(self):
        m.check_plan(plan());self.assertEqual(t.MAX_TABLES,153)
        for bad in [plan()[:-1],plan()+[plan()[0]],plan()[:-1]+[plan()[0]]]:
            with self.assertRaises(i.Stop):m.check_plan(bad)
    def test_no_extra_cohorts_or_exclusions(self):
        for cohorts in [{'protected':'false'},{'protected':'true','synthetic':'true'},{}]:
            p=plan();p[0]['cohorts']=cohorts
            with self.assertRaises(i.Stop):m.check_plan(p)
    def test_old_caps_stay_exact(self):
        self.assertEqual(t.MAX_ROWS,131072);self.assertEqual(t.MAX_PAGE_BYTES,1048576);self.assertEqual(t.MAX_MEMORY,134217728)
        with self.assertRaises(i.Stop):t.fetch_sql(32768)
    def test_saved_cause_precedes_any_hash_stream(self):
        a=i.corrected_admission();self.assertEqual(a['original_queries'],18);self.assertEqual(a['original_status'],'incomplete')
    def run_transfer(self,pages,inject=None):
        cursor=m.ControllerCursor.__new__(m.ControllerCursor)
        cursor.path=pathlib.Path(tempfile.mkdtemp(prefix='fmz-controller-transport-'));cursor.snapshot=['snapshot'];cursor.transaction={'id':'synthetic'}
        data=iter(pages);used=[]
        def utility(sql,qid,name,before=None,page_size=None):
            used.append(name)
            rows=next(data) if page_size else []
            frame=t.frame(rows,len(rows),page_size,len(cursor.plan)) if page_size else {'rows':0}
            return rows,None,frame
        cursor.utility=utility
        cursor.command=lambda sql,name:cursor.snapshot if sql==t.SNAPSHOT else []
        sql='select synthetic_hashes_only'
        bindings={name:{'queryid':'1','sql_sha256':hashlib.sha256(command.encode()).hexdigest()} for name,command in
          [('declare',t.declare_sql(sql)),('fetch',t.fetch_sql(8192)),('close',t.CLOSE)]}
        with patch.object(t.old.s,'identity',return_value=cursor.transaction),patch.object(t.old,'same_transaction',return_value=True):
            return cursor.transfer(sql,plan(),8192,bindings,inject),used
    def test_duplicates_last_table_empty_terminal(self):
        h=hashlib.sha256(b'synthetic-null-json').hexdigest()
        result,used=self.run_transfer([[['154',h,'1'],['154',h,'1']],[['0',h,'1']],[]])
        self.assertEqual(result['rows'],3);self.assertEqual(len(result['tables']),155)
        self.assertEqual(result['tables'][154]['cohorts']['protected']['rows'],2)
        self.assertEqual(result['tables'][154]['cohorts']['protected']['sha256'],hashlib.sha256((h+','+h).encode()).hexdigest())
        self.assertEqual(used,['cursor_declare','fetch_000','fetch_001','fetch_002','cursor_close'])
    def test_null_transport_is_not_a_row(self):
        with self.assertRaises(i.Stop):self.run_transfer([[['154',None,'1']]])
    def test_table_index_outside_exact_plan(self):
        with self.assertRaises(i.Stop):self.run_transfer([[['155','a'*64,'1']]])
    def test_interrupt_cannot_return_complete(self):
        with self.assertRaises(i.Stop):self.run_transfer([[['0','a'*64,'1']],[]],'after_chunk')
    def test_missing_terminal_is_incomplete(self):
        with self.assertRaises(StopIteration):self.run_transfer([[['0','a'*64,'1']]])

if __name__=='__main__':unittest.main()
