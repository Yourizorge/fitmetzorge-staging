"""Exact frozen EXPLAIN adapter, simulated libpq frames, no socket or credential."""
import ast,pathlib,time,types,unittest
SOURCE=pathlib.Path(__file__).resolve().parent.parent/'textfree_v1/native.py'
tree=ast.parse(SOURCE.read_text())
node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Native')
ns={'time':time,'Stop':RuntimeError}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),ns)
Native=ns['Native']

class Lib:
    def __init__(self,frames):self.frames=iter(frames)
    def PQsendQuery(self,*a):return 1
    def PQsetSingleRowMode(self,*a):return 1
    def PQisBusy(self,*a):return 0
    def PQgetResult(self,*a):return next(self.frames,None)
    def PQresultStatus(self,r):return r['status']
    def PQntuples(self,r):return r.get('rows',1)
    def PQnfields(self,r):return 1
    def PQgetisnull(self,r,*a):return r.get('null',False)
    def PQgetvalue(self,r,*a):return b'[]'
    def PQcmdTuples(self,r):return r.get('tag',b'')
    def PQresultErrorField(self,r,*a):return b'42501'
    def PQclear(self,r):pass

class Transport(unittest.TestCase):
    def call(self,frames,sql='explain (analyze,format json) select 1'):
        def raw(*a,**kw):raise RuntimeError('terminal_row_count')
        db=types.SimpleNamespace(lib=Lib(frames),conn=True,queries=0,query=raw)
        return Native(db).query(sql)
    def test_complete_empty_command_tag(self):self.assertEqual(self.call([{'status':9},{'status':2}]),[['[]']])
    def test_original_missing_space_uses_wrong_path(self):
        with self.assertRaisesRegex(RuntimeError,'terminal_row_count'):self.call([],'explain(analyze,format json) select 1')
    def test_missing_terminal(self):
        with self.assertRaisesRegex(RuntimeError,'explain_incomplete'):self.call([{'status':9}])
    def test_duplicate_terminal(self):
        with self.assertRaisesRegex(RuntimeError,'explain_terminal'):self.call([{'status':9},{'status':2},{'status':2}])
    def test_row_after_terminal(self):
        with self.assertRaisesRegex(RuntimeError,'explain_row_shape'):self.call([{'status':2},{'status':9}])
    def test_sqlstate_no_error_text(self):
        with self.assertRaisesRegex(RuntimeError,'explain_sqlstate_42501'):self.call([{'status':7}])
    def test_null_frame(self):
        with self.assertRaisesRegex(RuntimeError,'explain_null'):self.call([{'status':9,'null':True}])
    def test_plan_budget(self):
        with self.assertRaisesRegex(RuntimeError,'explain_plan_budget'):self.call([{'status':9}]*501+[{'status':2}])

if __name__=='__main__':unittest.main()
