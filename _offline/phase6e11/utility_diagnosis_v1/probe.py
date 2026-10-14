"""One authorized metadata diagnosis. Only literal synthetic rows are fetched."""
import hashlib,json,os,pathlib,re,subprocess,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
END=HERE.parent/'endchain_v1';ROOT=HERE.parents[2]
sys.path.insert(0,str(END))
from integral_stream import ALL_STATS,CONFIG,GUARD,INVENTORY,plan,statement
from integral_io import check_plan
from sql_protocol import single
from native_runtime import NativeRuntime
RUN_ID='e91ae17a-357c-4af3-a10a-dc2de7c471f7'
BEGIN='BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'
SETTINGS="""select current_setting('server_version_num') pg_version,
 current_setting('compute_query_id') compute_query_id,
 current_setting('pg_stat_statements.track',true) track,
 current_setting('pg_stat_statements.track_utility',true) track_utility,
 current_setting('pg_stat_statements.track_planning',true) track_planning,
 current_setting('stats_fetch_consistency') consistency,
 (select count(*) from supabase_migrations.schema_migrations) migrations,
 (select max(version) from supabase_migrations.schema_migrations) latest_migration"""
SYNTHETIC='select x::text value from (values (null::integer),(1),(1)) s(x)'
INSTANCE='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15'
def digest(value):return hashlib.sha256(value).hexdigest()
def disk(p):return pathlib.Path('\\\\?\\'+str(pathlib.Path(p).resolve())) if os.name=='nt' and not str(p).startswith('\\\\?\\') else pathlib.Path(p)

class Evidence:
    def __init__(self,folder):self.folder=disk(folder)
    def save(self,name,value):
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+\.json',name):raise ValueError('evidence_path')
        raw=(json.dumps(value,sort_keys=True,indent=2,default=str)+'\n').encode()
        if len(raw)>2000000 or re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]+\.eyJ',raw):raise ValueError('evidence_content_budget')
        target=self.folder/name;temp=self.folder/(name+'.pending-'+uuid.uuid4().hex)
        with temp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        # Atomic publication, without replacing an existing historical receipt.
        os.link(temp,target);temp.unlink()

def changes(before,after):
    if before['reset']!=after['reset'] or before['dealloc']!=after['dealloc']:raise ValueError('statistics_reset_or_deallocation')
    old={x['queryid']:x for x in before['statements']};out=[]
    for x in after['statements']:
        a=old.get(x['queryid'])
        if a and a['since']!=x['since']:raise ValueError('statistics_entry_replaced')
        d={k:(float if k=='exec_ms' else int)(x[k])-(float if k=='exec_ms' else int)(a[k] if a else 0) for k in ('calls','temp_read','temp_written','wal','exec_ms')}
        if min(d.values())<0:raise ValueError('statistics_counter_decreased')
        if any(d.values()):out.append({'queryid':x['queryid'],**d})
    return out

class Probe:
    def __init__(self,query,save,clock=time.monotonic,started=None):
        self.query=query;self.save=save;self.clock=clock;self.started=clock()
        if started is not None:self.started=started
        self.commands=[];self.active_phase='not_started';self.opened=False
        self.identity=None;self.reader=None;self.previous=None;self.pairs=[]
    def command(self,phase,sql):
        safety=phase=='rollback';elapsed=self.clock()-self.started
        if len(self.commands)>=(128 if safety else 127) or elapsed>=(600 if safety else 540):raise ValueError('diagnosis_budget')
        info=single(sql);self.active_phase=phase
        item={'number':len(self.commands)+1,'phase':phase,'sql_sha256':info['sha256'],'kind':info['kind'],
              'transaction':None if self.identity is None else self.identity['backend'],
              'elapsed_ms':round(elapsed*1000),'sent':False,'confirmed':False}
        self.commands.append(item);storage_error=None
        try:self.save('command-%03d-started.json'%item['number'],dict(item))
        except Exception as exc:
            if not safety:raise
            storage_error=exc
        if phase=='begin':self.opened=True
        item['sent']=True
        result=self.query(sql)
        item['confirmed']=True;item['duration_ms']=round((self.clock()-self.started-elapsed)*1000)
        self.save('command-%03d-confirmed.json'%item['number'],dict(item))
        if storage_error:raise storage_error
        return result
    def sample(self,label):
        value=self.command('sample_'+label,ALL_STATS)[0]['value']
        if not isinstance(value,dict) or len(value['statements'])>5000:raise ValueError('numeric_sample_budget')
        self.save('sample-'+label+'.json',value)
        if value['health']['io_wait'] or value['health']['long_active']:raise ValueError('project_health')
        return value
    def utility(self,label,sql,synthetic_fetch=False):
        before=self.previous;self.save(label+'-before.json',{'sample':before,'sql_sha256':digest(sql.encode())})
        rows=self.command(label,sql)
        after=self.sample(label);self.save(label+'-after.json',{'sample':after})
        observed=changes(before,after);other=[x for x in observed if x['queryid']!=self.reader and x['calls']]
        result={'phase':label,'changed':observed,'reader_queryid':self.reader,
                'old_rule_passes':len(other)==1 and other[0]['calls']==1,
                'background_attribution':'UNRESOLVED','row_count':len(rows)}
        if synthetic_fetch:
            result['synthetic_null_duplicates_preserved']=rows==[{'value':None},{'value':'1'},{'value':'1'}]
            if not result['synthetic_null_duplicates_preserved']:raise ValueError('synthetic_transport')
        self.save(label+'-comparison.json',result);self.pairs.append(result);self.previous=after
        if any(x['temp_written'] or x['temp_read'] for x in observed):raise ValueError('unresolved_temporary_load')
        return rows
    def run(self,ids,context):
        result={'status':'NO_GO','run_id':RUN_ID,'application_writes':0,'auth_calls':0,'real_hash_rows_fetched':0,'automatic_retries':0}
        error=None;cleanup=[]
        try:
            self.command('begin',BEGIN);self.identity=self.command('guard',GUARD)[0]
            if self.identity.get('ro')!='on' or self.identity.get('isolation')!='repeatable read' or self.identity.get('db')!='postgres' or self.identity.get('role')!='postgres' or self.identity.get('ssl') is not True or self.identity.get('instance_sha')!=INSTANCE:raise ValueError('read_only_project_binding')
            self.save('transaction.json',self.identity);self.command('canonical',CONFIG)
            self.save('settings.json',self.command('settings',SETTINGS)[0])
            self.reader=check_plan(self.command('reader_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)[0]['QUERY PLAN'])
            a=self.sample('observer_before');b=self.sample('observer_after')
            self.save('observer-binding.json',{'explain_queryid':self.reader,'changed':changes(a,b)})
            self.previous=b
            self.utility('synthetic_declare','DECLARE fmz_utility_diagnosis NO SCROLL CURSOR WITHOUT HOLD FOR '+SYNTHETIC)
            self.utility('synthetic_fetch','FETCH FORWARD 4 FROM fmz_utility_diagnosis',True)
            self.utility('synthetic_close','CLOSE fmz_utility_diagnosis')
            plans=plan(self.command('inventory',INVENTORY),ids,context);source=statement(plans)
            self.save('stream-binding.json',{'plans':plans,'query_sha256':digest(source.encode()),'source_sha256':digest((END/'integral_stream.py').read_bytes()),'fetch_permitted':False,'canonicalization':'PG17 JSONB text UTF8 SHA256 / sorted duplicate-preserving multiset'})
            self.previous=self.sample('stream_before')
            self.utility('original_declare','DECLARE fmz_integral_hashes NO SCROLL CURSOR WITHOUT HOLD FOR '+source)
            self.utility('original_close','CLOSE fmz_integral_hashes')
            terminal=self.command('reader_witness','EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)
            if check_plan(terminal[0]['QUERY PLAN'],True)!=self.reader:raise ValueError('reader_binding_changed')
            self.save('reader-witness.json',{'queryid':self.reader,'temp_written':0,'source_sha':digest(ALL_STATS.encode())})
            if self.command('final_guard',GUARD)[0]!=self.identity:raise ValueError('transaction_changed')
            result['status']='READ_ONLY_DIAGNOSIS_COLLECTED_NOT_WORKFLOW_PASS'
        except Exception as exc:
            error={'phase':self.active_phase,'command':len(self.commands),'class':type(exc).__name__,'sqlstate':getattr(exc,'sqlstate',None),'reason':str(exc) if type(exc) is ValueError and re.fullmatch('[a-z_]+',str(exc)) else 'sanitized'}
            try:self.save('original-error.json',error)
            except Exception as exc:cleanup.append({'phase':'error_storage','class':type(exc).__name__})
        finally:
            try:self.save('ledger-before-close.json',{'commands':self.commands,'original_error':error})
            except Exception as exc:cleanup.append({'phase':'ledger_storage','class':type(exc).__name__})
            if self.opened:
                try:self.command('rollback','ROLLBACK');result['rollback_confirmed']=True
                except Exception as exc:cleanup.append({'phase':'rollback','class':type(exc).__name__});result['rollback_confirmed']=False
            result.update(original_error=error,closure_errors=cleanup,commands=len(self.commands),pairs=len(self.pairs),elapsed_ms=round((self.clock()-self.started)*1000))
            if error or cleanup:result['status']='NO_GO'
            self.save('ledger-final.json',{'commands':self.commands,'result':result})
        return result

def main():
    started=time.monotonic()
    def git(*args):
        return subprocess.check_output([os.environ.get('FMZ_GIT','git'),*args],cwd=ROOT,text=True,timeout=15).strip()
    if git('branch','--show-current')!='main' or git('remote','get-url','origin')!='https://github.com/Yourizorge/fitmetzorge-staging.git':raise ValueError('repository_scope')
    head=git('rev-parse','HEAD')
    if head!=git('ls-remote','origin','refs/heads/main').split()[0]:raise ValueError('remote_head_changed')
    sys.path.insert(0,str(HERE.parent/'controller_v1'))
    import jit_diagnose as j,auth_preflight
    folder=ROOT/'supabase/.temp'/('phase6e11-utility-diagnosis-'+RUN_ID)
    disk(folder).mkdir(exist_ok=False);e=Evidence(folder)
    sources=[pathlib.Path(__file__),END/'integral_stream.py',END/'integral_io.py',END/'native_runtime.py',END/'sql_protocol.py']
    e.save('authorization.json',{'run_id':RUN_ID,'head':head,'source_request':'1f3971da-1021-4208-835c-de31c29ac281','maximum_sql':128,'maximum_seconds':600,'ordinary_stop_seconds':540,'maximum_collectors':1,'retries':0,'no_migration_auth_fixture_or_application_writes':True,'real_table_fetches':0,'sources':{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sources}})
    journal=runtime=db=None;granted=False;result={'status':'NO_GO','phase':'management'}
    try:
        journal=j.Journal(j.jit.sb.credential(),folder);journal.deadline=started+600
        journal.inspect();granted=True;journal.grant()
        connect=json.loads((j.m.c.CONNECT/'connect.json').read_text())
        runtime=NativeRuntime.staging(connect,journal.token,j.m.c.CA,j.m.c.parameters);db=runtime.connect()
        def query(sql):
            c=db.execute(sql,prepare=False);rows=c.fetchall() if c.description else []
            if len(rows)>1000:raise ValueError('metadata_rows')
            return rows
        ids=auth_preflight.identifiers();context={k:str(uuid.uuid4()) for k in ('window','a','b')}
        context['runs']={k:str(uuid.uuid4()) for k in ('seed','activate','delete_window')}
        result=Probe(query,e.save,started=started).run(ids,context)
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
    return 0 if result['status']=='READ_ONLY_DIAGNOSIS_COLLECTED_NOT_WORKFLOW_PASS' and result.get('jit_revoked') else 2

if __name__=='__main__':sys.exit(main())
