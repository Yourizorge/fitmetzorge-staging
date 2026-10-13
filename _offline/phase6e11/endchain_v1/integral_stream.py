"""Disposable-CI preservation stream, exercising the pinned PG17 row hash.

One cursor, bounded hash-only pages, local multiset reduction. This does not
replace or authorize the separately proven hosted native streaming adapter.
"""
import hashlib,json,pathlib,re
from integral_io import SNAPSHOT,check_plan,delta

ROWS=131072
PAGE=8192
ALL_STATS=SNAPSHOT.replace("and queryid::text in(select jsonb_array_elements_text($1::jsonb))",'')
INVENTORY="""select n.nspname schema,c.relname name,array_agg(a.attname order by a.attnum) columns
 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
 where c.relkind in('r','p') and n.nspname not like 'pg_%' and n.nspname<>'information_schema'
 group by n.nspname,c.relname order by n.nspname,c.relname"""
CONFIG="""select set_config('TimeZone','UTC',true),set_config('DateStyle','ISO, YMD',true),
 set_config('IntervalStyle','postgres',true),set_config('extra_float_digits','3',true),
 set_config('bytea_output','hex',true),set_config('lc_numeric','C',true),
 set_config('stats_fetch_consistency','none',true),set_config('max_parallel_workers_per_gather','0',true),
 set_config('work_mem','2184kB',true),set_config('statement_timeout','5000',true)"""
GUARD="""select current_setting('transaction_read_only') ro,current_setting('transaction_isolation') isolation,
 pg_backend_pid() backend,pg_current_snapshot()::text snapshot,
 current_database() db,current_user role,(select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl"""

def ident(x):
    if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',x):raise ValueError('stream_identifier')
    return '"'+x+'"'

def literal(x):
    if not re.fullmatch('[0-9a-f-]{36}',x):raise ValueError('stream_scope_identity')
    return "'"+x+"'"

def predicates(row,ids,c):
    s,t,columns=row['schema'],row['name'],row['columns'];w=literal(c['window']);a=literal(c['a']);b=literal(c['b'])
    users=','.join(literal(x) for x in ids.values());run=literal('32321f17-07f1-4f3d-aa4b-3218bc7368a4')
    life=','.join(literal(x) for x in c['runs'].values())
    owned_runs=f"select run_id from fmz6e11_request_private.receipts where window_id={w}"
    new_runs=f"({owned_runs} union select unnest(array[{life}]::uuid[]))"
    if s=='cron' and t=='job_run_details':return 'false'
    if s=='fmz_ci_auth_observer':return 'false'
    if s=='auth':
        if t=='users':return 'id not in('+users+')'
        if 'user_id' in columns:return 'user_id is null or user_id::text not in('+users+')'
        if t=='mfa_amr_claims':return 'session_id not in(select id from auth.sessions where user_id in('+users+'))'
        if t=='audit_log_entries':return "coalesce(payload->>'actor_id','') not in("+users+')'
    if s=='fmz6e11_private':
        if t=='config':return 'false' # exact singleton has its own before/after contract
        if t=='windows':return 'id<>'+w
        if t=='workspaces':return 'window_id<>'+w
        if 'window_id' in columns:return 'window_id<>'+w
        if 'workspace_id' in columns:return 'workspace_id not in('+a+','+b+')'
    if s=='fmz6e11_request_private':
        if t=='control':return 'false'
        if t=='receipts':return 'window_id<>'+w
    if s=='fmz6e11_controller_private':return ('id' if t=='runs' else 'run_id')+'<>'+run
    if s=='fmz6e11_audit_private':
        if t=='actors':return 'id not in('+users+')'
        if t=='runs':return 'id not in '+new_runs
        if t in ('actions','writes'):return 'run_id not in '+new_runs
        if t=='bindings':return 'action_id not in(select id from fmz6e11_audit_private.actions where run_id in '+new_runs+')'
    return 'true'

def plan(inventory,ids,c):
    out=[]
    for row in inventory:
        if row['schema'] in c.get('temporary_schemas',[]):continue
        out.append({'name':row['schema']+'.'+row['name'],'predicate':predicates(row,ids,c)})
    if not 100<=len(out)<=200 or len({r['name'] for r in out})!=len(out):raise ValueError('ci_stream_inventory_budget')
    return out

def statement(plans):
    return ' union all '.join("select "+str(i)+"::text i,encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h,"
        "case when ("+p['predicate']+") then '1' else '0' end keep from "+'.'.join(ident(n) for n in p['name'].split('.'))+' t'
        for i,p in enumerate(plans))

def frame(rows,terminal):
    if terminal!=len(rows) or len(rows)>PAGE:raise ValueError('stream_terminal_count')
    for row in rows:
        if set(row)!=set(('i','h','keep')) or any(not isinstance(row[k],str) for k in ('i','h','keep')) or not row['i'].isdigit() or not re.fullmatch('[0-9a-f]{64}',row['h']) or row['keep'] not in ('0','1'):
            raise ValueError('stream_frame_content')
    if sum(len(r['i'])+len(r['h'])+len(r['keep'])+19 for r in rows)>1024*1024:raise ValueError('stream_frame_bytes')

def run(query,save,ids,context,label,expected=None):
    count=0;frames=[];profiles=[];buffer={};opened=False
    def q(phase,sql,args=()):
        nonlocal count
        count+=1
        if count>(96 if phase=='rollback' else 95):raise ValueError('ci_stream_command_ceiling')
        return query('stream_'+label+'_'+phase,sql,args)
    try:
        q('begin','BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');opened=True
        identity=q('guard',GUARD)[0]
        if identity['ro']!='on' or identity['isolation']!='repeatable read' or identity['db']!='postgres' or identity['role']!='postgres' or identity['ssl'] is not True:
            raise ValueError('stream_identity')
        q('canonical',CONFIG)
        plans=plan(q('inventory',INVENTORY),ids,context)
        if expected is not None and plans!=expected['plan']:raise ValueError('stream_inventory_changed')
        stream=statement(plans);reader=check_plan(q('reader_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)[0]['QUERY PLAN'])
        def sample():
            value=q('io',ALL_STATS)[0]['value']
            if len(value['statements'])>5000:raise ValueError('stream_numeric_metadata_budget')
            return value
        previous=sample();buffer={r['name']:[] for r in plans};total=0
        def utility(sql):
            nonlocal previous
            before=previous;rows=q('utility',sql);terminal=query.terminal_count;after=sample()
            old={v['queryid']:v for v in before['statements']}
            changed={v['queryid']:v['calls']-old.get(v['queryid'],{}).get('calls',0) for v in after['statements']
                if v['queryid']!=reader and v['calls']!=old.get(v['queryid'],{}).get('calls',0)}
            if len(changed)!=1 or list(changed.values())!=[1]:raise ValueError('stream_utility_attribution')
            profile=delta(before,after,{**changed,reader:1})
            save('integral-stream-'+label+'-io-%03d.json'%len(profiles),profile)
            # A read-only cursor may generate WAL for PostgreSQL hint bits.
            # Keep that load visible; temporary writes remain a hard failure.
            if any(x['exec_ms']>2500 for x in profile['queries']):raise ValueError('stream_own_load')
            profiles.append(profile);previous=after
            return rows,terminal
        utility('DECLARE fmz_integral_hashes NO SCROLL CURSOR WITHOUT HOLD FOR '+stream)
        for page in range(ROWS//PAGE+1):
            rows,terminal=utility('FETCH FORWARD '+str(PAGE)+' FROM fmz_integral_hashes')
            frame(rows,terminal);total+=len(rows)
            if total>ROWS:raise ValueError('stream_row_ceiling')
            frames.append({'page':page,'rows':len(rows),'terminal_count':len(rows),
                'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()})
            if not rows:break
            for r in rows:
                if int(r['i'])>=len(plans):raise ValueError('stream_table_index')
                if r['keep']=='1':buffer[plans[int(r['i'])]['name']].append(r['h'])
        else:raise ValueError('stream_empty_terminal_missing')
        utility('CLOSE fmz_integral_hashes')
        terminal=q('io_terminal','EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)
        if check_plan(terminal[0]['QUERY PLAN'],True)!=reader:raise ValueError('stream_closing_binding')
        if q('final_guard',GUARD)[0]!=identity:raise ValueError('stream_snapshot_changed')
        tables={name:{'rows':len(h),'sha256':hashlib.sha256(','.join(sorted(h)).encode()).hexdigest()} for name,h in buffer.items()}
        if expected is not None and expected['tables']!=tables:raise ValueError('stream_protected_drift')
        value={'label':label,'tables':tables,'rows':total,'plan':plans,'frames':frames,'profiles':profiles,
            'query_sha256':hashlib.sha256(stream.encode()).hexdigest(),'snapshot_sha256':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),
            'canonicalization':'PG17 JSONB text UTF8 SHA256 / sorted duplicate-preserving multiset',
            'algorithm':'fmz-legacy-sha256-multiset-pinned-v1','query_text_read':False,'protected_equal':expected is None or tables==expected['tables'],
            'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
            'protocol_commands':count+1,'hosted_admitted':False}
        save('integral-stream-'+label+'.json',value);return value
    finally:
        if opened:q('rollback','ROLLBACK')
