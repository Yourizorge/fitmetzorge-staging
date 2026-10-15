"""One numeric-only size diagnosis, not a new hosted mutation attempt."""
import hashlib,importlib.util,json,os,pathlib,re,subprocess,sys,time
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1];END=HERE.parent/'phase6e11/endchain_v1'
sys.path.insert(0,str(END));sys.path.insert(0,str(HERE.parent/'phase6e11/utility_diagnosis_v1'))
from integral_stream import ALL_STATS,CONFIG,GUARD,INVENTORY,ident,statement
from integral_io import check_plan,delta
spec=importlib.util.spec_from_file_location('numeric_utility_probe',HERE.parent/'phase6e11/utility_diagnosis_v1/probe.py')
utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
Probe,Evidence,disk,SETTINGS,INSTANCE=utility.Probe,utility.Evidence,utility.disk,utility.SETTINGS,utility.INSTANCE
from native_runtime import NativeRuntime
RUN='91ba398d-8888-4026-9f0b-3aafd988e5b3'
FILTER='b94f4eea413204787b134198bcaae488bf6c98082687e44bf466f735920ef85a'
PREVIOUS=END/'receipts/reserved-debe3298-9772-40b1-a9f4-8e3d99c8fd20/integral-stream-before-binding.json'

def historical_binding(path=PREVIOUS):
    return json.loads(disk(path).read_text())

def numeric(plans):
    return '/* fmz6e11:numeric_size_v1 */ '+ ' union all '.join(
        'select '+str(i)+'::text i,count(*)::text n from '+'.'.join(ident(n) for n in p['name'].split('.'))+
        ' t where ('+p['predicate']+')' for i,p in enumerate(plans))

def capacity(rows,plans):
    if len(rows)!=len(plans):raise ValueError('numeric_incomplete')
    seen={};wire=0
    for row in rows:
        if set(row)!={'i','n'} or not re.fullmatch('[0-9]+',str(row['i'])) or not re.fullmatch('[0-9]+',str(row['n'])):raise ValueError('numeric_frame')
        i=int(row['i']);n=int(row['n'])
        if i in seen or not 0<=i<len(plans):raise ValueError('numeric_duplicate_or_foreign')
        seen[i]=n
        wire+=n*(len(json.dumps({'i':str(i),'h':'0'*64,'keep':'1'},separators=(',',':')))+1)
    total=sum(seen.values());pages=(total+8191)//8192
    return {'protected_rows':total,'numeric_tables':len(plans),'hash_rows_transported':0,
        'planned_json_frame_bytes':wire+pages*2,'planned_hash_payload_bytes':total*64,
        'pages_at_8192':pages,'full_cycle_fetch_and_sample_commands':pages*2,
        'table_counts':[{'table':plans[i]['name'],'rows':seen[i]} for i in range(len(plans))],
        'not_a_preservation_comparison':True,'new_mutation_capacity_admitted':False}

def run(probe,plans):
    result={'run_id':RUN,'status':'NO_GO','application_writes':0,'auth_calls':0,'hash_rows_transported':0};error=None
    try:
        probe.command('begin','BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        identity=probe.command('guard',GUARD)[0];probe.identity=identity
        if identity.get('ro')!='on' or identity.get('isolation')!='repeatable read' or identity.get('instance_sha')!=INSTANCE or identity.get('db')!='postgres' or identity.get('role')!='postgres' or identity.get('ssl') is not True:raise ValueError('read_only_project_binding')
        probe.save('transaction.json',identity);probe.command('canonical',CONFIG)
        probe.save('settings.json',probe.command('settings',SETTINGS)[0])
        inventory=probe.command('inventory',INVENTORY)
        if sorted(x['schema']+'.'+x['name'] for x in inventory)!=sorted(x['name'] for x in plans):raise ValueError('inventory_changed')
        sql=numeric(plans)
        reader=check_plan(probe.command('reader_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)[0]['QUERY PLAN'])
        own=check_plan(probe.command('size_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+sql)[0]['QUERY PLAN'])
        if own==reader:raise ValueError('query_identity_collision')
        before=probe.sample('before');probe.save('numeric-before.json',{'sample':before,'queryid':own,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest()})
        rows=probe.command('exact_numeric_count',sql)
        after=probe.sample('after');probe.save('numeric-after.json',{'sample':after,'counts':rows})
        profile=delta(before,after,{reader:1,own:1})
        probe.save('numeric-io.json',profile)
        if any(q['exec_ms']>2500 for q in profile['queries']):raise ValueError('numeric_load_limit')
        report=capacity(rows,plans);probe.save('numeric-capacity.json',report)
        if check_plan(probe.command('reader_witness','EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)[0]['QUERY PLAN'],True)!=reader:raise ValueError('reader_changed')
        if probe.command('final_guard',GUARD)[0]!=identity:raise ValueError('transaction_changed')
        result.update(status='NUMERIC_DIAGNOSIS_PASS_NOT_WORKFLOW_PASS',capacity=report,io=profile)
    except Exception as exc:
        error={'phase':probe.active_phase,'command':len(probe.commands),'class':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None),
               'reason':str(exc) if type(exc) is ValueError and re.fullmatch('[a-z_]+',str(exc)) else 'sanitized'}
        probe.save('original-error.json',error)
    finally:
        try:
            if probe.opened:probe.command('rollback','ROLLBACK');result['rollback_confirmed']=True
        except Exception as exc:result.update(status='NO_GO',rollback_confirmed=False,closure_error=type(exc).__name__)
        result.update(error=error,commands=len(probe.commands),elapsed_ms=round((probe.clock()-probe.started)*1000))
        probe.save('ledger-final.json',{'commands':probe.commands,'result':result})
    return result

def main():
    started=time.monotonic()
    def git(*args):return subprocess.check_output([os.environ.get('FMZ_GIT','git'),*args],cwd=ROOT,text=True,timeout=15).strip()
    if git('branch','--show-current')!='main' or git('remote','get-url','origin')!='https://github.com/Yourizorge/fitmetzorge-staging.git':raise ValueError('repository_scope')
    head=git('rev-parse','HEAD')
    if head!=git('ls-remote','origin','refs/heads/main').split()[0]:raise ValueError('remote_head_changed')
    # The operator must supply an immutable verified CI result for this exact source.
    evidence=disk(sys.argv[1]);candidate=json.loads((evidence/'candidate.json').read_text())
    ci=json.loads((evidence/'result.json').read_text());collection=json.loads((evidence/'collection.json').read_text())
    source=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    if collection.get('verified') is not True or ci.get('status')!='CLEAN_CI_PASS' or candidate['sources'].get('_offline/phase6e_server_v1/size_diagnosis.py')!=source or ci.get('numeric_size_pg17_checks',0)<4:raise ValueError('source_bound_ci_missing')
    binding=historical_binding();plans=binding['plan']
    if hashlib.sha256(json.dumps(plans,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=FILTER:raise ValueError('historical_filter_changed')
    if hashlib.sha256(statement(plans).encode()).hexdigest()!=binding['query_sha256']:raise ValueError('historical_query_changed')
    folder=ROOT/'supabase/.temp'/('phase6e11-numeric-size-'+RUN);disk(folder).mkdir(exist_ok=False);e=Evidence(folder)
    e.save('authorization.json',{'run_id':RUN,'head':head,'source_sha256':source,'ci_run':collection['run'],
        'filter_sha256':FILTER,'maximum_sql':128,'maximum_seconds':600,'ordinary_stop_seconds':540,'query_timeout_ms':5000,
        'own_query_load_limit_ms':2500,'collectors':1,'automatic_retries':0,'hash_transport':False,'writes':False})
    sys.path.insert(0,str(HERE.parent/'phase6e11/controller_v1'));import jit_diagnose as j
    journal=runtime=db=None;granted=False;result={'status':'NO_GO','phase':'management'}
    try:
        journal=j.Journal(j.jit.sb.credential(),folder);journal.deadline=started+600;journal.inspect();granted=True;journal.grant()
        connect=json.loads((j.m.c.CONNECT/'connect.json').read_text())
        runtime=NativeRuntime.staging(connect,journal.token,j.m.c.CA,j.m.c.parameters);db=runtime.connect()
        def query(sql):
            cursor=db.execute(sql,prepare=False);rows=cursor.fetchall() if cursor.description else []
            if len(rows)>200:raise ValueError('numeric_output_limit')
            return rows
        result=run(Probe(query,e.save,started=started),plans)
    except Exception as exc:result.update(status='NO_GO',error_class=type(exc).__name__,sqlstate=getattr(exc,'sqlstate',None))
    finally:
        if db:db.close()
        if runtime:runtime.clear()
        if granted:
            try:journal.close();result['jit_revoked']=True
            except Exception as exc:result.update(status='NO_GO',jit_revoked=False,closure_error=type(exc).__name__)
        if journal:journal.token=None
        e.save('result.json',result)
    print(json.dumps({'status':result['status'],'commands':result.get('commands'),'jit_revoked':result.get('jit_revoked'),'folder':str(folder)}))
    return 0 if result['status']=='NUMERIC_DIAGNOSIS_PASS_NOT_WORKFLOW_PASS' and result.get('jit_revoked') else 2

if __name__=='__main__':sys.exit(main())
