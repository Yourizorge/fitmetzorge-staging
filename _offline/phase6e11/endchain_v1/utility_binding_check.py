"""Small interleaved PG17 check, disposable CI only; never opens staging."""
import hashlib,os
from integral_io import check_plan,delta
from integral_stream import ALL_STATS,CONFIG
from native_runtime import NativeRuntime
from utility_binding import UtilityBindings,other_load


def run(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':
        raise ValueError('disposable_ci_only')
    runtime=NativeRuntime.disposable(gate);connections=[]
    try:
        first=runtime.connect();connections.append(first)
        second=runtime.connect();connections.append(second)
        for c in connections:
            c.execute('BEGIN TRANSACTION READ ONLY')
            if c.execute("select current_setting('transaction_read_only') ro").fetchone()['ro']!='on':
                raise ValueError('utility_ci_read_only')
            c.execute(CONFIG)
        reader=check_plan(first.execute('EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS).fetchone()['QUERY PLAN'])
        background_sql='select 137::bigint as synthetic_count,29::bigint as synthetic_marker'
        background_id=check_plan(second.execute('EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+background_sql).fetchone()['QUERY PLAN'])
        first.execute('DECLARE fmz_binding_probe NO SCROLL CURSOR WITHOUT HOLD FOR select g from generate_series(1,4) g')
        fetch='FETCH FORWARD 1 FROM fmz_binding_probe';source=hashlib.sha256(fetch.encode()).hexdigest()
        bindings=UtilityBindings()
        def sample():return first.execute(ALL_STATS).fetchone()['value']
        before=sample();first.execute(fetch).fetchall();after=sample()
        initial=bindings.observe(source,before,after,reader)
        if not initial['unambiguous']:raise ValueError('utility_ci_initial_binding')
        own=initial['queryid'];delta(before,after,{own:1,reader:1});bindings.confirm(source,initial)
        before=after
        second.execute(background_sql).fetchall()
        first.execute(fetch).fetchall();after=sample()
        observed=bindings.observe(source,before,after,reader)
        if not observed['unambiguous'] or observed['other_query_calls']!={background_id:1}:
            raise ValueError('utility_ci_interleaved_binding')
        own_profile=delta(before,after,{own:1,reader:1})
        other_profile=other_load(before,after,observed)
        if UtilityBindings().observe(source,before,after,reader)['unambiguous']:
            raise ValueError('utility_ci_first_ambiguity_accepted')
        before=after;first.execute(fetch).fetchall();first.execute(fetch).fetchall();after=sample()
        if bindings.observe(source,before,after,reader)['unambiguous']:
            raise ValueError('utility_ci_double_fetch_accepted')
        first.execute('CLOSE fmz_binding_probe')
        if check_plan(first.execute('EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS).fetchone()['QUERY PLAN'],True)!=reader:
            raise ValueError('utility_ci_reader_closure')
        gate.save('utility-binding-pg17.json',{'status':'PASS','checks':6,
            'disposable_only':True,'hosted_calls':0,'source_sha256':source,
            'binding':observed,'own_profile':own_profile,'other_profile':other_profile,
            'ambiguous_first_denied':True,'double_fetch_denied':True,'read_only':True})
        return 6
    finally:
        for c in connections:
            try:c.execute('ROLLBACK')
            finally:c.close()
        runtime.clear()
