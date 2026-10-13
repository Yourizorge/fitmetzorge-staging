"""Numeric PG17 query attribution for one sequential composed workflow.

No query text is requested from PostgreSQL. Source SQL is identified locally
and bound to EXPLAIN's lossless Query Identifier before it is executed.
"""
import hashlib,json

SNAPSHOT="""/* fmz6e11:endchain_v1:numeric_io */
select jsonb_build_object(
 'reset',(select stats_reset from extensions.pg_stat_statements_info),
 'dealloc',(select dealloc from extensions.pg_stat_statements_info),
 'statements',(select coalesce(jsonb_agg(jsonb_build_object(
   'queryid',queryid::text,'calls',calls,'since',stats_since,
   'temp_read',temp_blks_read,'temp_written',temp_blks_written,
   'wal',wal_bytes::text,'exec_ms',total_exec_time)),'[]')
   from extensions.pg_stat_statements(false)
   where dbid=(select oid from pg_database where datname=current_database())
     and userid=(select oid from pg_roles where rolname=current_user) and toplevel
     and queryid::text in(select jsonb_array_elements_text($1::jsonb))),
 'background',(select jsonb_build_object('temp_bytes',temp_bytes,'reset',stats_reset)
   from pg_stat_database where datname=current_database()),
 'health',(select jsonb_build_object('io_wait',count(*) filter(where wait_event_type='IO'),
   'long_active',count(*) filter(where state='active' and query_start<clock_timestamp()-interval '30 seconds'))
   from pg_stat_activity where datname=current_database() and pid<>pg_backend_pid())) value"""

def check_plan(value,analyzed=False):
    if not isinstance(value,list) or len(value)!=1 or type(value[0].get('Query Identifier')) is not int:
        raise ValueError('io_plan_identity_missing')
    root=value[0]
    def visit(node):
        if node.get('Temp Read Blocks',0) or node.get('Temp Written Blocks',0):raise ValueError('io_own_spill')
        for child in node.get('Plans',[]):visit(child)
    if analyzed:
        visit(root['Plan'])
        if root['Plan'].get('Actual Rows')!=1 or root.get('Execution Time',float('inf'))>1000:
            raise ValueError('io_closing_witness')
    return str(root['Query Identifier'])

def delta(before,after,expected):
    if before['reset']!=after['reset'] or before['dealloc']!=after['dealloc']:raise ValueError('io_statistics_reset')
    if before['background']['reset']!=after['background']['reset'] or after['background']['temp_bytes']<before['background']['temp_bytes']:
        raise ValueError('io_background_counter_reset')
    old={x['queryid']:x for x in before['statements']};new={x['queryid']:x for x in after['statements']}
    out=[]
    for qid,count in expected.items():
        a=old.get(qid);b=new.get(qid)
        if b is None or a and a['since']!=b['since']:raise ValueError('io_counter_missing_or_replaced')
        d={k:(float if k=='exec_ms' else int)(b[k])-(float if k=='exec_ms' else int)(a[k] if a else 0)
           for k in ('calls','temp_read','temp_written','wal','exec_ms')}
        if min(d.values())<0 or d['calls']!=count:raise ValueError('io_command_attribution')
        if d['temp_read'] or d['temp_written']:raise ValueError('io_own_spill')
        if d['exec_ms']>5000*count:raise ValueError('io_query_time')
        out.append({'queryid':qid,**d})
    if after['health']['io_wait'] or after['health']['long_active']:raise ValueError('io_project_health')
    return {'queries':out,'own_temp_written':sum(x['temp_written'] for x in out),
        'own_wal_bytes':sum(x['wal'] for x in out),
        'background_temp_bytes':after['background']['temp_bytes']-before['background']['temp_bytes'],
        'background_attributed_to_collector':False}

class QueryIO:
    def __init__(self,query):
        self.query=query;self.bindings={};self.expected={};self.baseline=None;self.samples=[];self.reader_id=None
    def start(self):
        rows=self.query('reader','io_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+SNAPSHOT,['[]'])
        self.reader_id=check_plan(rows[0]['QUERY PLAN'])
        self.bindings[hashlib.sha256(SNAPSHOT.encode()).hexdigest()]=self.reader_id
        self.baseline=self.sample()
    def sample(self):
        rows=self.query('reader','io_sample',SNAPSHOT,[json.dumps(sorted(set(self.bindings.values())))])
        if len(rows)!=1 or not isinstance(rows[0].get('value'),dict):raise ValueError('io_sample_shape')
        result=rows[0]['value'];self.samples.append(result)
        # The current stats query completes after its own observed counter.
        if self.reader_id:self.executed(self.reader_id)
        return result
    def bind(self,sql,args):
        key=hashlib.sha256(sql.encode()).hexdigest()
        if key in self.bindings:return self.bindings[key]
        rows=self.query('reader','io_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+sql,args)
        qid=check_plan(rows[0]['QUERY PLAN']);self.bindings[key]=qid
        # Preserve the actual previous value for a new family, never assume 0.
        sample=self.sample()
        if self.baseline is None:self.baseline=sample
        else:
            previous=next((x for x in sample['statements'] if x['queryid']==qid),None)
            if previous and not any(x['queryid']==qid for x in self.baseline['statements']):
                self.baseline['statements'].append(previous)
        return qid
    def executed(self,qid):self.expected[qid]=self.expected.get(qid,0)+1
    def checkpoint(self):
        expected=dict(self.expected)
        after=self.sample()
        result=delta(self.baseline,after,expected)
        self.baseline=after;self.expected={self.reader_id:1} if self.reader_id else {};return result
    def close(self):
        result=self.checkpoint()
        rows=self.query('reader','io_closing_witness',
            'EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+SNAPSHOT,
            [json.dumps(sorted(set(self.bindings.values())))])
        qid=check_plan(rows[0]['QUERY PLAN'],True)
        return {'last_pair':result,'closing_queryid':qid,'closing_temp_written':0,
            'bindings':self.bindings,'samples':len(self.samples),'query_text_read':False}
