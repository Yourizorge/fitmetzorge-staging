"""Derive reports from retained metadata. Absolutely no network or database calls."""
import hashlib
import json
import pathlib
import re
from registry import ROOT, build, validate
from proof_gate import canary_decision, query_plan

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

def metrics(p):
    r=read(p)
    return r['at'], next(x['metrics'] for x in r['requests'] if x['endpoint'].endswith('/metrics'))

def metric(rows,name,**labels):
    return sum(x['value'] for x in rows if x['name']==name and all(x['labels'].get(k)==v for k,v in labels.items()))

def function_bodies():
    # Restricted extractor for the pinned migration's dollar-quoted CREATE FUNCTION
    # statements. Not a general SQL parser; any missing/mismatched body is NO-GO.
    bodies={}
    for p in sorted((ROOT/'supabase/migrations').glob('*.sql')):
        sql=p.read_text(encoding='utf-8-sig').replace('\r\n','\n')
        for m in re.finditer(r'create\s+(?:or\s+replace\s+)?function\s+([\w]+)\.([\w]+)\s*\(.*?\bas\s+(\$\w*\$)(.*?)\3',sql,re.I|re.S):
            bodies[(m[1],m[2])]=hashlib.sha256(m[4].encode()).hexdigest()
    return bodies

def analyse():
    r=read('docs/PHASE6E11_PG17_READONLY_METADATA.json')
    start,a=metrics('supabase/.temp/phase6e11-io-metrics-d0afdca3172a4df0ae5395008693960d.json')
    end,b=metrics('supabase/.temp/phase6e11-io-metrics-76f4108affc843ac8e96b165a5ad5f2f.json')
    duration=metric(b,'node_time_seconds')-metric(a,'node_time_seconds')
    modes={m:metric(b,'node_cpu_seconds_total',mode=m)-metric(a,'node_cpu_seconds_total',mode=m)
           for m in ('idle','iowait','user','system','nice','irq','softirq','steal')}
    total=sum(modes.values())
    base=read('docs/PHASE6E11_DISK_IO_OBSERVATIONS.json')['pg_metadata']
    byid={str(x['queryid']):x for x in r['after']['fingerprints']}
    comparisons=[]
    for x in base['statements']:
        if str(x['queryid']) in byid:
            n=byid[str(x['queryid'])]
            comparisons.append({'queryid':str(x['queryid']),'calls_before':x['calls'],'calls_after':n['calls'],
                'temp_blocks_before':x['temp_blks_written'],'temp_blocks_after':n['temp_blks_written']})
    local=function_bodies()
    bindings=[{**x,'local_sha256':local.get((x['schema'],x['function'])),
               'match':local.get((x['schema'],x['function']))==x['body_sha256']} for x in r['after']['function_hashes']]
    triggers=[]
    for trigger in r['after']['triggers']:
        name=trigger['function'].split('(')[0]
        if '.' not in name:
            name='public.'+name
        expected=local.get(tuple(name.split('.')))
        triggers.append({**trigger,'local_sha256':expected,'match':expected==trigger['body_sha256']})
    gates={'pg17_equivalent':True,'complete_write_coverage':False,'io_recovered':False,
        'stable_latency':False,'no_worker':True,'historical_expectation_bound':False,'stream_transport_verified':False}
    return {'scope':'metadata derivation only; no hosted cycle', 'observations_utc':[start,end],
        'metrics_seconds':duration,'io_wait_percent':100*modes['iowait']/total,
        'cpu_busy_percent':100*(total-modes['idle']-modes['iowait'])/total,
        'swap_used_bytes':metric(b,'node_memory_SwapTotal_bytes')-metric(b,'node_memory_SwapFree_bytes'),
        'swap_in_pages_delta':metric(b,'node_vmstat_pswpin')-metric(a,'node_vmstat_pswpin'),
        'swap_out_pages_delta':metric(b,'node_vmstat_pswpout')-metric(a,'node_vmstat_pswpout'),
        'temp_bytes_delta':r['after']['counters']['temp_bytes']-r['before']['counters']['temp_bytes'],
        'temp_files_delta':r['after']['counters']['temp_files']-r['before']['counters']['temp_files'],
        'stats_reset_unchanged':r['before']['counters']['stats_reset']==r['after']['counters']['stats_reset'],
        'fingerprint_counter_comparisons':comparisons,'function_bindings':bindings,'trigger_bindings':triggers,
        'metadata_roundtrip_ms':[r[k]['request_ms'] for k in ('before','middle','after')],
        'db_execution_latency_proven':False,
        'dashboard':{'observed_date':'2026-09-22','disk_io_percent_consumed':57,
                     'per_second_budget_trend_available':False,'after_reload_active_warning_visible':False},
        'local_synthetic_workers_remaining':0,
        'gates':gates,'canary':canary_decision(gates),
        'catalogue_budget_not_executable_workflow':query_plan(len(build()['routes'])),
        'source_registry':validate(read('_offline/phase6e11/readiness_v1/register.json')),
        'hosted_cycles_executed':0,'hosted_cleanup':False}

if __name__=='__main__':
    print(json.dumps(analyse(),indent=2,sort_keys=True))
