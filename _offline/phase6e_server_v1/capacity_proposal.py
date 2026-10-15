"""Offline arithmetic and synthetic transport benchmark; never grants a hosted run."""
import collections,copy,hashlib,json,os,pathlib,sys,time,tracemalloc
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase6e11/endchain_v1'))
from complete_register import reserve_prefixes
PAGE=8192

def build(register,counts):
    if register.get('normal_capacity')!=2196 or register.get('worst_including_safety')!=2207 or register.get('approved_limit')!=2226:
        raise ValueError('historical_register_binding')
    if counts.get('not_a_preservation_comparison') is not True or counts.get('hash_rows_transported')!=0:
        raise ValueError('numeric_scope')
    total=counts['protected_rows'];tables=counts['table_counts']
    if type(total) is not int or total<0 or sum(t['rows'] for t in tables)!=total or any(type(t['rows']) is not int or t['rows']<0 for t in tables):raise ValueError('numeric_counts')
    pages=max(8,(total+PAGE-1)//PAGE);rows=copy.deepcopy(register['rows'])
    if sum(r['sql'] for r in rows)!=2196:raise ValueError('register_rows')
    for label,phase in [('before','baseline'),('before_cleanup','measurements'),('after_cleanup','final')]:
        matches=[i for i,r in enumerate(rows) if r['action']=='stream_'+label+'_rollback']
        if len(matches)!=1:raise ValueError('cycle_anchor')
        at=matches[0]
        additions=[{'phase':phase,'action':'proposed_additional_fetch_and_io','sql':1,'writeset':[],
          'optional':True,'retry':False,'timeout_ms':5000,'proof':['same snapshot','complete frame','independent numeric IO pair']}
          for _ in range(2*(pages-8))]
        rows[at:at]=additions
    for i,row in enumerate(rows):row['id']='proposal_'+str(i+1).zfill(5)
    prefixes=reserve_prefixes(rows);worst=max(p['required_total'] for p in prefixes)
    return {'status':'OFFLINE_CAPACITY_PROPOSAL_NOT_ADMISSION','observed_protected_rows':total,
      'proposed_rows_per_cycle':pages*PAGE,'page_rounding_headroom':pages*PAGE-total,
      'pages_per_cycle':pages,'protocol_per_cycle':15+2*pages,'cycles':3,
      'normal_commands':sum(r['sql'] for r in rows),'worst_with_safety':worst,
      'smallest_sql_maximum':max(2226,worst),'previous_sql_maximum':2226,
      'phase_budgets':dict(collections.Counter(r['phase'] for r in rows)),
      'managed_auth_commands_unchanged':register['managed_auth_commands'],
      'new_run_authorized':False,'row_capacity_authorized':False,'fresh_integral_ci_required':True,
      'rows':rows,'prefixes':prefixes,
      'limits_unchanged':{'collector':1,'automatic_retries':0,'query_ms':5000,'query_load_ms':2500,
       'total_seconds':600,'ordinary_seconds':540,'worker_ms':120000,'guard_ms':180000,'own_temp_writes':0},
      'missing_before_admission':['new exact run binding and M44 candidate identity',
       'PG17 full-source hashing and cursor benchmark at proposed size, not only client hashes',
       'fresh integral source-bound CI and every prefix cleanup gate',
       'hosted transport/runtime evidence cannot be inferred from numeric counts']}

def benchmark(tables):
    total=sum(t['rows'] for t in tables)
    if total>1000000:raise ValueError('offline_benchmark_memory_bound')
    tracemalloc.start();started=time.perf_counter();frames=0;wire=0;buffer={t['table']:[] for t in tables};page=[]
    def receive(values):
        nonlocal frames,wire
        raw=json.dumps(values,separators=(',',':')).encode();parsed=json.loads(raw)
        if len(parsed)!=len(values):raise ValueError('client_frame')
        for r in parsed:buffer[tables[int(r['i'])]['table']].append(r['h'])
        frames+=1;wire+=len(raw)
    for i,t in enumerate(tables):
        for n in range(t['rows']):
            # Repeated deterministic synthetic hashes explicitly retain duplicates.
            page.append({'i':str(i),'h':hashlib.sha256(str(n%513).encode()).hexdigest(),'keep':'1'})
            if len(page)==PAGE:receive(page);page=[]
    if page:receive(page)
    hashes={name:hashlib.sha256(','.join(sorted(values)).encode()).hexdigest() for name,values in buffer.items()}
    elapsed=time.perf_counter()-started;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    if sum(len(v) for v in buffer.values())!=total:raise ValueError('client_completeness')
    return {'status':'SYNTHETIC_CLIENT_ONLY_PASS','rows':total,'frames':frames,'wire_bytes':wire,
      'elapsed_seconds':round(elapsed,3),'python_peak_bytes':peak,'duplicate_preserving':True,
      'hashes_sha256':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
      'hosted_requests':0,'pg_query_cost_proven':False,'process_rss_not_measured':True}

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def load_register(path):
    manifest=json.loads(disk(path.parent/'MANIFEST.json').read_text())['files'];bound={}
    def read(name):
        raw=disk(path.parent/name).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if manifest.get(name)!=digest:raise ValueError('historical_file_hash')
        bound[name]=digest;return json.loads(raw)
    register=read(path.name);rows=[]
    for phase in register['phase_budgets']:
        group=read('register-phase-'+phase+'.json')['rows']
        if len(group)!=register['phase_budgets'][phase] or any(r['phase']!=phase for r in group):raise ValueError('historical_phase')
        rows+=group
    rows.sort(key=lambda r:int(r['id'].split('_')[1]))
    if [r['id'] for r in rows]!=['cmd_'+str(i+1).zfill(5) for i in range(2196)]:raise ValueError('historical_order')
    register['rows']=rows
    if max(p['required_total'] for p in reserve_prefixes(rows))!=2207:raise ValueError('historical_safety_reserve')
    return register,bound
def main():
    folder=pathlib.Path(sys.argv[1]).resolve();root=HERE.parents[1]
    if folder.parent!=root/'supabase/.temp' or not folder.name.startswith('phase6e11-numeric-size-'):raise ValueError('numeric_folder')
    result=json.loads(disk(folder/'result.json').read_text())
    if result.get('status')!='NUMERIC_DIAGNOSIS_PASS_NOT_WORKFLOW_PASS' or result.get('jit_revoked') is not True:raise ValueError('numeric_not_closed')
    old=HERE.parent/'phase6e11/endchain_v1/receipts/reserved-ci-38722956194/complete-command-register.json'
    register,bound=load_register(old);proposal=build(register,result['capacity'])
    proposal.update(historical_register_files=bound,numeric_result_sha256=hashlib.sha256(disk(folder/'result.json').read_bytes()).hexdigest())
    proposal['client_benchmark']=benchmark(result['capacity']['table_counts'])
    target=disk(folder/'offline-capacity-proposal.json')
    with target.open('x',encoding='utf8') as f:json.dump(proposal,f,sort_keys=True,indent=2)
    print(json.dumps({k:v for k,v in proposal.items() if k not in ('rows','prefixes')}))
if __name__=='__main__':main()
