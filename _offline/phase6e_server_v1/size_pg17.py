"""Exact-count equivalence without a hash stream; disposable PostgreSQL only."""
from size_diagnosis import numeric,capacity
from native_runtime import NativeRuntime

def run(gate):
    runtime=NativeRuntime.disposable(gate);db=runtime.connect();receipts=[]
    try:
        db.execute('BEGIN')
        db.execute('create temporary table numeric_size_rows on commit drop as select case when i%2=0 then null else 0 end v, i%3=0 allowed from generate_series(1,150000) i')
        for predicate,expected in [('true',150000),('allowed',50000),('false',0),('v is null',75000)]:
            plans=[{'name':'pg_temp.numeric_size_rows','predicate':predicate}];sql=numeric(plans)
            rows=db.execute(sql).fetchall();report=capacity(rows,plans)
            if report['protected_rows']!=expected:raise ValueError('numeric_exact_count')
            explained=db.execute('EXPLAIN (ANALYZE,BUFFERS,COSTS FALSE,FORMAT JSON) '+sql).fetchone()['QUERY PLAN'][0]
            def visit(node):
                if node.get('Temp Written Blocks',0) or node.get('Node Type') in ('Sort','Incremental Sort'):raise ValueError('numeric_spill_or_sort')
                for child in node.get('Plans',[]):visit(child)
            visit(explained['Plan']);receipts.append({'rows':expected,'execution_ms':explained['Execution Time'],'temp_written':0,'hash_rows':0})
    finally:db.execute('ROLLBACK');db.close();runtime.clear()
    gate.save('numeric-size-pg17.json',{'status':'PASS','checks':4,'cases':receipts,'hosted':False})
    return 4
