"""PG17-only synthetic filter equivalence, run in disposable CI, never hosted."""
import hashlib,json,os
from integral_stream import statement,capacity_statement,frame,ROWS,PAGE

def boundaries(gate):
    from native_runtime import NativeRuntime
    runtime=NativeRuntime.disposable(gate);receipts=[]
    connection=runtime.connect()
    try:
        for size in (0,8192,8193,65535,65536,65537):
            connection.execute('BEGIN')
            try:
                connection.execute('create temporary table stream_boundary on commit drop as '
                    'select case when mod(g,2)=0 then null else 0 end quantity, '
                    'case when g<=%s then true when g=%s then null else false end allowed '
                    'from generate_series(1,73728) g',(size,size+1))
                plans=[{'name':'pg_temp.stream_boundary','predicate':'allowed'}]
                count_sql=capacity_statement(plans)
                analyzed=connection.execute('EXPLAIN (ANALYZE,BUFFERS,COSTS FALSE,FORMAT JSON) '+count_sql).fetchone()['QUERY PLAN'][0]
                def check(node):
                    if node.get('Node Type') in ('Sort','Incremental Sort') or node.get('Temp Written Blocks',0):
                        raise ValueError('capacity_pg17_sort_or_spill')
                    for child in node.get('Plans',[]):check(child)
                check(analyzed['Plan'])
                bounded=int(connection.execute(count_sql).fetchone()['protected_rows'])
                if bounded!=min(size,ROWS+1):raise ValueError('capacity_pg17_count')
                received=[];pages=[]
                if bounded<=ROWS:
                    connection.execute('DECLARE boundary_hashes NO SCROLL CURSOR WITHOUT HOLD FOR '+statement(plans))
                    while len(received)<bounded:
                        requested=min(PAGE,bounded-len(received),ROWS-len(received))
                        cursor=connection.execute('FETCH FORWARD '+str(requested)+' FROM boundary_hashes')
                        rows=cursor.fetchall();frame(rows,cursor.rowcount)
                        if len(rows)!=requested:raise ValueError('capacity_pg17_page')
                        received.extend(row['h'] for row in rows);pages.append(requested)
                    connection.execute('CLOSE boundary_hashes')
                    legacy=connection.execute("select encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h, "
                        "case when allowed then '1' else '0' end keep from pg_temp.stream_boundary t").fetchall()
                    expected=sorted(row['h'] for row in legacy if row['keep']=='1')
                    if sorted(received)!=expected:raise ValueError('capacity_pg17_duplicate_or_null_loss')
                    digest=hashlib.sha256(','.join(sorted(received)).encode()).hexdigest()
                else:digest=None
                receipts.append({'protected_rows':size,'bounded_numeric_result':bounded,'hash_rows':len(received),
                    'pages':pages,'hash_sha256':digest,'independent_legacy_multiset_equal':bounded<=ROWS,
                    'denied_before_hash_cursor':bounded>ROWS,'numeric_temp_blocks':0,'numeric_execution_ms':analyzed['Execution Time'],
                    'query_sha256':hashlib.sha256(count_sql.encode()).hexdigest()})
            finally:connection.execute('ROLLBACK')
    finally:connection.close();runtime.clear()
    gate.save('stream-capacity-pg17.json',{'status':'PASS','cases':receipts,'disposable_only':True,
        'hosted_size_proven':False,'capacity':ROWS,'checks':30})
    return 30

def run(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':
        raise ValueError('disposable_ci_only')
    candidate=statement([{'name':'synthetic.stream_probe','predicate':'allowed'}])
    candidate=candidate.replace('"synthetic"."stream_probe"','fixture')
    sql="""with fixture as materialized (
      select case when g%2=0 then null else 0 end quantity,
             case when g<=4 then true when g=5 then null else false end allowed
      from generate_series(1,73728) g
    ), legacy as (
      select '0'::text i,encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h,
             case when allowed then '1' else '0' end keep from fixture t
    ), candidate as ("""+candidate+""")
    select (select count(*) from fixture) source_rows,
           (select count(*) from legacy) legacy_transport_rows,
           (select count(*) from candidate) filtered_transport_rows,
           (select count(distinct h) from candidate) distinct_hashes,
           (select count(*) from fixture where allowed and quantity is null) null_rows,
           not exists ((select i,h,keep from legacy where keep='1' except all select i,h,keep from candidate)
             union all (select i,h,keep from candidate except all select i,h,keep from legacy where keep='1')) multiset_equal"""
    rows=gate.rows(sql)
    expected={'source_rows':73728,'legacy_transport_rows':73728,'filtered_transport_rows':4,
              'distinct_hashes':2,'null_rows':2,'multiset_equal':True}
    if rows!=[expected]:raise ValueError('stream_filter_pg17_equivalence')
    gate.save('stream-filter-pg17.json',{'status':'PASS','checks':expected,'disposable_only':True,
        'hosted_rows_attribution':'UNKNOWN; no table counts reconstructed from incomplete receipt',
        'row_limit_unchanged':65536,'page_limit_unchanged':8192,'hosted_admitted':False})
    return 6+boundaries(gate)
