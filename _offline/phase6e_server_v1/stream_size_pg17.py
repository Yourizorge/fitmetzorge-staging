"""Proposed capacity only, on disposable PG17 with entirely synthetic contents."""
import hashlib,json,pathlib,time,tracemalloc
from native_runtime import NativeRuntime
from integral_stream import statement,frame,CONFIG,PAGE
from integral_io import check_plan
HERE=pathlib.Path(__file__).resolve().parent

def run(gate):
    fixture=json.loads((HERE/'stream_size_fixture.json').read_text());counts=fixture['row_counts'][:]
    if fixture.get('synthetic_only') is not True or len(counts)!=158 or sum(counts)!=100843 or fixture['row_ceiling_proposal']!=106496:raise ValueError('synthetic_distribution')
    counts[counts.index(max(counts))]+=106496-sum(counts)
    runtime=NativeRuntime.disposable(gate);db=runtime.connect();plans=[];command=0;records=[];result=None
    def q(label,sql,args=None):
        nonlocal command
        command+=1;started=time.perf_counter();cursor=db.execute(sql,args,prepare=False)
        rows=cursor.fetchall() if cursor.description else []
        records.append({'command':command,'phase':label,'ms':round((time.perf_counter()-started)*1000,3)})
        return rows
    try:
        q('setup_begin','BEGIN')
        for i,n in enumerate(counts):
            name='fmz_capacity_'+str(i)
            q('synthetic_table','create temporary table '+name+' (n integer,label text,optional text,values_json jsonb)')
            if n:
                q('synthetic_rows','insert into '+name+" select mod(g,257),repeat('synthetic',16),case when mod(g,2)=0 then null else 'explicit' end,jsonb_build_object('v',mod(g,3),'a',jsonb_build_array(null,0,1),'u',chr(233)) from generate_series(1,%s) g",[n])
            plans.append({'name':'pg_temp.'+name,'predicate':'true'})
        q('setup_commit','COMMIT')
        q('begin','BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        if q('guard',"select current_setting('transaction_read_only') ro,current_setting('transaction_isolation') isolation")[0]!={'ro':'on','isolation':'repeatable read'}:raise ValueError('benchmark_transaction')
        q('canonical',CONFIG)
        sql=statement(plans)
        plan=q('bound_plan','EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+sql)[0]['QUERY PLAN']
        queryid=check_plan(plan,True)
        def check(node):
            if node.get('Node Type') in ('Sort','Incremental Sort') or node.get('Temp Written Blocks',0):raise ValueError('benchmark_sort_or_temp')
            for child in node.get('Plans',[]):check(child)
        check(plan[0]['Plan'])
        if plan[0]['Execution Time']>=2500:raise ValueError('benchmark_own_load')
        q('declare','DECLARE fmz_capacity_hashes NO SCROLL CURSOR WITHOUT HOLD FOR '+sql)
        tracemalloc.start();started=time.perf_counter();buffer={i:[] for i in range(158)};wire=0
        for page in range(13):
            rows=q('fetch','FETCH FORWARD '+str(PAGE)+' FROM fmz_capacity_hashes')
            frame(rows,PAGE);wire+=len(json.dumps(rows,separators=(',',':')).encode())
            for row in rows:buffer[int(row['i'])].append(row['h'])
        if q('terminal','FETCH FORWARD 1 FROM fmz_capacity_hashes'):raise ValueError('benchmark_extra_rows')
        if [len(buffer[i]) for i in range(158)]!=counts:raise ValueError('benchmark_completeness')
        hashes={str(i):hashlib.sha256(','.join(sorted(values)).encode()).hexdigest() for i,values in buffer.items()}
        elapsed=time.perf_counter()-started;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        q('close','CLOSE fmz_capacity_hashes')
        result={'status':'DISPOSABLE_PG17_CAPACITY_PASS_NOT_HOSTED_ADMISSION','rows':sum(counts),'tables':158,'pages':13,
          'json_frame_bytes':wire,'python_peak_bytes':peak,'client_fetch_reduce_seconds':round(elapsed,3),
          'pg_hash_ms':plan[0]['Execution Time'],'temp_written_blocks':0,'queryid':queryid,
          'query_sha256':hashlib.sha256(sql.encode()).hexdigest(),'statement_source_sha256':hashlib.sha256((HERE.parent/'phase6e11/endchain_v1/integral_stream.py').read_bytes()).hexdigest(),
          'hashes_sha256':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
          'source_shape':'synthetic integer,128-character text,NULL and structured JSON; not a bound on real row width',
          'hosted_requests':0,'server_memory_or_network_latency_proven':False,'legacy_equivalence':'separate frozen 36-case PG17 test remains mandatory'}
    finally:
        if tracemalloc.is_tracing():tracemalloc.stop()
        try:q('rollback','ROLLBACK')
        finally:db.close();runtime.clear()
        if result:
            result.update(protocol_commands=command,protocol=records,connection_closed=True)
            gate.save('proposed-size-pg17.json',result)
    return result
