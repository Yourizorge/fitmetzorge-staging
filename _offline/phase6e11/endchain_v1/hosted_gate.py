"""Private staging orchestration adapter. No listener, browser API or retries.

The entry point requires an exact verified CI artifact and current source bytes.
It uses only the already approved owner JIT and registered synthetic identities.
"""
import hashlib,importlib.util,json,os,pathlib,re,subprocess,sys,time,uuid
from native_runtime import NativeRuntime,PROJECT
from metered_composition import MeteredComposition,capacity
from quota_boundary import FILE,SOURCE_SHA
from closure import AUTHORIZATION,RUN_ID,PURPOSE,allowance
from cli_stat_reader import snapshot
from cli_envelope import attribution,charged,CAP,CHARGE

HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p

def assert_unused(root=ROOT,run_id=RUN_ID):
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',run_id):
        raise ValueError('hosted_run_identity')
    paths=[root/'supabase/.temp'/('phase6e11-reserved-hosted-'+run_id),
           root/'_offline/phase6e11/endchain_v1/receipts'/('reserved-'+run_id)]
    # The committed receipt also prevents a fresh checkout from reopening a
    # consumed run whose local temporary folder is absent.
    if any(disk(p).exists() for p in paths):raise ValueError('hosted_attempt_consumed')

def save(folder,name,value):
    if not re.fullmatch(r'[a-zA-Z0-9_.-]+\.json',name):raise ValueError('hosted_evidence_path')
    raw=(json.dumps(value,sort_keys=True,indent=2,default=str)+'\n').encode()
    if len(raw)>2000000 or re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',raw):
        raise ValueError('hosted_evidence_size_or_secret')
    with disk(folder/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def admission(folder,root=ROOT):
    read=lambda n:json.loads(disk(folder/n).read_bytes())
    result=read('result.json');collection=read('collection.json');sources=read('candidate.json')['sources']
    if result.get('status')!='CLEAN_CI_PASS' or result.get('full_chain_admission') is not True or result.get('migrations_applied')!=45 or result.get('quota_present_chain_pass') is not True:
        raise ValueError('hosted_full_ci_missing')
    if collection.get('all_file_hashes_valid') is not True or collection.get('head')!=result['commit'] or str(collection['run'])!=str(result['run_id']):
        raise ValueError('hosted_archive_binding')
    raw=disk(folder/'evidence.zip').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=collection['archive_sha256']:raise ValueError('hosted_archive_changed')
    manifest=read('artifact-manifest.json')
    for name,h in manifest.items():
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+\.(json|txt)',name) or hashlib.sha256(disk(folder/name).read_bytes()).hexdigest()!=h:
            raise ValueError('hosted_receipt_changed')
    for name,h in sources.items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or hashlib.sha256(disk(path).read_bytes()).hexdigest()!=h:
            raise ValueError('hosted_composition_changed')
    required={'_offline/phase6e11/endchain_v1/'+n for n in
              ('hosted_gate.py','authorization.json','budget.mjs','closure.py','metered_composition.py',
               'complete_register.py','runtime_budget.py','integral_stream.py','migration_boundary.py','quota_boundary.py','cli_envelope.py')}
    numeric=AUTHORIZATION['numeric_evidence']['result']
    required|={'supabase/migrations/'+FILE,numeric,str(pathlib.PurePosixPath(numeric).with_name('MANIFEST.json'))}
    if not required<=sources.keys():raise ValueError('hosted_entry_not_source_bound')
    pair=read('integral-migration-pair.json');meter=read('runtime-command-meter.json');register=read('complete-command-register.json')
    if not pair.get('complete') or pair.get('migration_sha256')!=SOURCE_SHA or not meter.get('complete') or meter.get('stopped'):
        raise ValueError('hosted_migration_or_meter_incomplete')
    if any(register.get(k)!=v for k,v in capacity().items()) or meter.get('limit')!=allowance(RUN_ID,PURPOSE):
        raise ValueError('hosted_budget_not_admitted')
    expected_limits={'rows_per_stream':AUTHORIZATION['maximum_rows_per_cycle'],
        'numeric_capacity_sentinel':AUTHORIZATION['maximum_rows_per_cycle']+1,'capacity_counted_in_protocol':True,
        'page_rows':8192,'cycles':3,'collectors':1,'query_ms':5000,
        'worker_ms':120000,'guard_ms':180000,'full_retry':0,'own_temp_writes':0}
    if any(register.get('data_limits',{}).get(k)!=v for k,v in expected_limits.items()):
        raise ValueError('hosted_stream_budget_not_admitted')
    return {'head':result['commit'],'ci_run':str(result['run_id']),'archive_sha256':collection['archive_sha256'],
        'candidate_sha256':result['candidate_sha256'],'sources':sources,'register':register}

class ScalarSession:
    def __init__(self,runtime,composition):self.runtime=runtime;self.composition=composition;self.sql_connection=None
    def query(self,text):
        c=self.composition;phase=c.current_phase
        if self.sql_connection is None:self.sql_connection=self.runtime.connect()
        c.before_sql(phase,text)
        cursor=self.sql_connection.execute(text,prepare=False);lines=[]
        while True:
            if cursor.description:
                for row in cursor.fetchall():
                    values=list(row.values())
                    if len(values)!=1:raise ValueError('hosted_scalar_metadata_required')
                    value=values[0];lines.append(value if isinstance(value,str) else json.dumps(value,default=str))
            if not cursor.nextset():break
        c.after_sql(phase,text);return '\n'.join(lines)
    def close(self):
        if self.sql_connection is None:return
        c=self.composition
        try:
            if self.sql_connection.info.transaction_status!=0:
                c.safety_label='rollback_writer';c.before_sql('safety_rollback','ROLLBACK')
                self.sql_connection.execute('ROLLBACK');c.after_sql('safety_rollback','ROLLBACK')
        finally:self.sql_connection.close();self.sql_connection=None;c.safety_label=None

class Gate:
    def __init__(self,out,runtime,composition,admitted,cli_executor,ci_folder):
        self.out=out;self.sources=ROOT;self.runtime=runtime;self.composition=composition
        self.result={'head':admitted['head']};self.cli_executor=cli_executor;self.cli_protocol=[]
        self.ci_folder=ci_folder;self.scalar=ScalarSession(runtime,composition);self.final_dry_run=None
        composition.fixture_context['instance_sha']='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15'
    def save(self,name,value):save(self.out,name,value)
    def sql(self,text):
        return self.scalar.query(text)
    def metered_cli(self,dry):
        index=len(self.cli_protocol)
        if index>1 or (index==1 and not dry):raise ValueError('hosted_cli_sequence')
        before,first=snapshot(self.runtime)
        self.save('hosted-cli-before-'+str(index)+'.json',{'stats':before,'commands':first})
        outcome=None;failure=None
        try:outcome=self.cli_executor(dry)
        except Exception as error:failure=type(error).__name__
        finally:
            # The direct after-observation is mandatory even after CLI failure.
            after,last=snapshot(self.runtime)
            self.save('hosted-cli-after-'+str(index)+'.json',{'stats':after,'commands':last,'outcome':outcome,'error_class':failure})
        if failure:raise ValueError('hosted_cli_execution_failed')
        numeric=attribution(before,after,between=3)
        self.save('cli-numeric-coverage-'+str(index)+'.json',numeric)
        if outcome['exit_code']:
            raise ValueError('hosted_cli_or_numeric_evidence_failed')
        if dry and (not outcome['up_to_date'] or outcome['migration_files']):raise ValueError('hosted_dry_run_not_empty')
        if not dry and outcome['migration_files']!=[FILE]:raise ValueError('hosted_migration_not_exact_quota')
        receipt={'complete':True,'environment':'staging','protocol_commands':None,'commands':[],
            'observer_commands':first+last,'outcome':outcome,'attribution':numeric,
            'capacity_reserved':CAP,'charged_commands':CHARGE,
            'command_identity':'64 reserved CLI/unknown commands; database-wide numeric deltas are not session attribution'}
        charged(receipt)
        self.save('cli-protocol-'+str(index)+'.json',receipt);self.cli_protocol.append(receipt)
        return receipt
    def apply_endchain_migration(self):return self.metered_cli(not self.composition.fixture_context['migration_boundary'])
    def cli(self,*args,timeout=90):
        if args!=('db','push','--local','--dry-run','--skip-vault'):raise ValueError('hosted_cli_action_denied')
        return self.metered_cli(True)
    def close(self):
        self.scalar.close()

def main(ci_folder):
    assert_unused()
    admitted=admission(ci_folder)
    def git(*args):
        p=subprocess.run([os.environ.get('FMZ_GIT','git'),*args],cwd=ROOT,capture_output=True,text=True,timeout=15)
        if p.returncode:raise ValueError('hosted_git_check')
        return p.stdout.strip()
    if git('branch','--show-current')!='main' or git('remote','get-url','origin') not in (
        'https://github.com/Yourizorge/fitmetzorge-staging.git','https://github.com/Yourizorge/fitmetzorge-staging'):
        raise ValueError('hosted_repository_binding')
    if git('rev-parse','HEAD')!=admitted['head'] or git('ls-remote','origin','refs/heads/main').split()[0]!=admitted['head']:
        raise ValueError('hosted_source_head_changed')
    sys.path.insert(0,str(HERE.parent/'controller_v1'))
    import jit_diagnose as j,auth_preflight
    sys.path.insert(0,str(HERE.parent/'controller_guard_v1'))
    spec=importlib.util.spec_from_file_location('hosted_exact_identity_guard',HERE.parent/'controller_guard_v1/guard.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    sys.path.insert(0,str(HERE.parent/'auth_metadata_v1'))
    import audit,auth_contract,auth_arm
    ids=auth_preflight.identifiers();guard_run=str(uuid.uuid4());guard.scope(guard_run,ids)
    out=ROOT/'supabase/.temp'/('phase6e11-reserved-hosted-'+RUN_ID)
    out.mkdir(exist_ok=False)
    save(out,'preregistration.json',{**admitted,'run_id':RUN_ID,'purpose':PURPOSE,'guard_run':guard_run,
        'maximum_sql':allowance(RUN_ID,PURPOSE),'maximum_rows_per_cycle':AUTHORIZATION['maximum_rows_per_cycle'],
        'maximum_cycles':3,'collectors':1,'authorization_sha256':admitted['sources']['_offline/phase6e11/endchain_v1/authorization.json'],
        'numeric_evidence':AUTHORIZATION['numeric_evidence'],'migration_sha256':SOURCE_SHA,
        'maximum_seconds':600,'jit_seconds':300,'guard_seconds':180,'automatic_retries':0})
    token=journal=runtime=gate=lifecycle=identity=c=None;granted=False;result={'status':'NO_GO','phase':'management'}
    try:
        token=j.jit.sb.credential();journal=j.Journal(token,out);journal.inspect()
        policy=auth_preflight.settings(journal.request('auth_policy',j.BASE+'/config/auth'))
        if policy.get('sessions_single_per_user') is not False or any(v is not False for k,v in policy.items() if k.startswith('hook_')):
            raise ValueError('hosted_auth_policy_changed')
        save(out,'auth-policy.json',policy)
        import urllib.request
        req=urllib.request.Request(j.jit.API+j.BASE+'/api-keys?reveal=true',headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
        with urllib.request.build_opener(j.jit.NoRedirect()).open(req,timeout=5) as response:
            raw=response.read(100001)
        if len(raw)>100000:raise ValueError('private_keys_response_budget')
        keys=json.loads(raw);raw=None
        admin=next(x['api_key'] for x in keys if x['name']=='service_role')
        anon=next(x['api_key'] for x in keys if x['name']=='anon');keys=None
        req=urllib.request.Request('https://'+PROJECT+'.supabase.co/auth/v1/health',headers={'apikey':anon})
        with urllib.request.build_opener(j.jit.NoRedirect()).open(req,timeout=5) as response:
            health=json.loads(response.read(4097))
        if health.get('version')!='v2.197.0':raise ValueError('hosted_auth_version_changed')
        save(out,'auth-version.json',{'version':health['version']})
        result['phase']='jit';granted=True;journal.grant()
        connect=json.loads((j.m.c.CONNECT/'connect.json').read_text())
        runtime=NativeRuntime.staging(connect,token,j.m.c.CA,j.m.c.parameters)
        c=MeteredComposition(runtime=runtime)
        cli=pathlib.Path(os.environ['FMZ_SUPABASE_CLI'])
        p=subprocess.run([str(cli),'--version'],capture_output=True,text=True,timeout=5)
        if p.returncode or p.stdout.strip()!='2.117.0':raise ValueError('hosted_cli_pin')
        import migration_run
        gate=Gate(out,runtime,c,admitted,lambda dry:migration_run.cli_run(cli,connect,j.m.c.CA,token,dry),ci_folder)
        save(out,'source-admission.json',{'ci_run':admitted['ci_run'],'head':admitted['head'],'exact_sources':True})
        from registered_lifecycle import RegisteredLifecycle
        from registered_runner import IdentitySession,execute
        audit.arm=auth_arm.render
        identity=IdentitySession(runtime,c,guard_run,ids)
        lifecycle=RegisteredLifecycle(gate=gate,composition=c,run_id=guard_run,ids=ids,guard=guard,audit=audit,
            contract_type=auth_contract.Contract,sql=gate.sql,lock_query=identity.query)
        config={**runtime.context(ids),'ids':ids,'admin':admin,'anon':anon,'sourceSha':admitted['head'],'ciRun':admitted['ci_run'],
            'authContracts':{op:[{'table':'auth.'+t,'operation':o,'count':n} for (t,o),n in values.items()] for op,values in auth_contract.COUNTS.items()}}
        admin=anon=None;result['phase']='registered_chain'
        outcome=execute(gate,c,lifecycle,config)
        result.update(status='HOSTED_CHAIN_PASS_PENDING_ACCESS_CLOSURE',outcome=outcome['status'],commands=c.meter.used,
            auth_pairs=18,workflow_pairs=71,deletes=123,migrations=45,dry_run_empty=True)
    except Exception as error:
        import traceback
        result.update(status='NO_GO',error_class=type(error).__name__,sqlstate=getattr(error,'sqlstate',None),
            reason=str(error) if re.fullmatch(r'[a-zA-Z0-9_]+',str(error)) else 'sanitized',
            frames=[{'file':pathlib.Path(x.filename).name,'line':x.lineno,'function':x.name} for x in traceback.extract_tb(error.__traceback__)])
    finally:
        for name,close in [('identity',lambda:identity.close() if identity else None),('guard_audit',lambda:lifecycle.close_temporary() if lifecycle and not lifecycle.removed else None),('native',lambda:gate.close() if gate else None)]:
            try:close()
            except Exception as error:result.update(status='NO_GO',**{name+'_closure_error':type(error).__name__})
        if granted:
            try:journal.close();result['jit_revoked']=True
            except Exception:result.update(status='NO_GO',jit_revoked=False)
        if runtime:runtime.clear()
        if c is not None:
            result['commands']=c.meter.used
            save(out,'final-command-meter.json',c.meter.receipt())
        if journal:journal.token=None
        token=None
        if result['status']=='HOSTED_CHAIN_PASS_PENDING_ACCESS_CLOSURE' and result.get('jit_revoked'):
            result['status']='HOSTED_CHAIN_TECHNICAL_PASS'
        result.update(owner_acceptance=False,production_touched=False,external_ai_calls=0,real_member_ai=False)
        save(out,'result.json',result)
    print(json.dumps({'status':result['status'],'phase':result['phase'],'evidence':str(out),
        'commands':result.get('commands'),'jit_revoked':result.get('jit_revoked')}))
    return 0 if result['status']=='HOSTED_CHAIN_TECHNICAL_PASS' else 2

if __name__=='__main__':sys.exit(main(pathlib.Path(sys.argv[1]).resolve()))
