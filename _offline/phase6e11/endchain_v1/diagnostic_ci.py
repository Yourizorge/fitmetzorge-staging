"""Separate opt-in disposable WAL observation. Never a proof-chain entry."""
import hashlib,json,os,pathlib,re,sys
import ci

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ci.prior.old.old.Gate
EXTRA={'_offline/phase6e11/endchain_v1/'+name for name in (
    'diagnostic_ci.py','diagnostic_ops.py','test_diagnostic_ci.py',
    'ci_wal_diagnostic.py','test_ci_wal_diagnostic.py')}
EXTRA.add('.github/workflows/phase6e11-wal-diagnostic.yml')
IMAGE='supabase/postgres:17.6.1.167'
DIGEST='supabase/postgres@sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb'
IDS={r:'69000000-0000-4000-8000-%012d'%(i+1)
     for i,r in enumerate(('a_member','a_trainer','b_member'))}
CONTEXT={'window':'69000000-0000-4000-8000-000000000004',
    'temporary_schemas':['fmz6e11_guard_'+'a'*32,'fmz6e11_am_'+'a'*32]}

def enabled(env):
    if (env.get('FMZ6E11_LOCAL_WAL_DIAGNOSTIC')!='1'
        or env.get('GITHUB_ACTIONS')!='true'
        or env.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging'
        or env.get('GITHUB_REF')!='refs/heads/main'
        or env.get('GITHUB_RUN_ATTEMPT')!='1'):
        raise ValueError('diagnostic_opt_in_ci_only')
    commit=env.get('GITHUB_SHA','')
    if not re.fullmatch('[0-9a-f]{40}',commit) or env.get('EXPECTED_SOURCE_COMMIT')!=commit:
        raise ValueError('diagnostic_source_commit')
    return commit

def activate_sources():
    # Only this dedicated process expands candidate preparation/path admission.
    ci.prior.old.EXTRA.update(EXTRA)

class DiagnosticGate(ci.Gate):
    def __init__(self):
        enabled(os.environ)
        super().__init__()
        self.bootstrap=[];self.stack_attempted=False
        self.result.update(status='DIAGNOSTIC_ONLY',full_chain_admission=False,
            hosted_admitted=False,wal_zero_pass=False,causal_attribution=False,
            diagnostic_completed=False,diagnostic_sql_cap=16,
            fixture='EMPTY_METADATA_DIFFERENT_FROM_HISTORICAL',
            synthetic_ids=IDS,auth_accounts_created=0,
            fixture_limitations=['No Auth users, registry identities, guard or audit fixtures are created.',
                'Empty metadata results do not reproduce or explain historical WAL.',
                'pg_walinspect permission failure remains a limitation; no privilege escalation.'])

    def save(self,name,value):
        # Bootstrap subprocess output can contain local credentials. Export only hashes.
        if isinstance(value,dict) and 'stdout' in value and 'stderr' in value:
            value=dict(value)
            for field in ('stdout','stderr'):
                raw=value.pop(field).encode()
                value[field+'_sha256']=hashlib.sha256(raw).hexdigest()
                value[field+'_bytes']=len(raw)
        return super().save(name,value)

    def command(self,label,args,sql=None,timeout=90,check=True):
        if sql is not None:
            from sql_protocol import statements
            self.bootstrap.append({'kind':'direct_sql','label':label,
                'attempted_commands':len(statements(sql)),
                'sql_sha256':hashlib.sha256(sql.encode()).hexdigest()})
        return super().command(label,args,sql=sql,timeout=timeout,check=check)

    def cli(self,*args,timeout=120):
        allowed={('--version',),('init','--yes'),('db','start'),
                 ('migration','up','--local'),('stop','--no-backup')}
        if args not in allowed:raise ValueError('diagnostic_cli_bootstrap_scope')
        if args==('db','start'):self.stack_attempted=True
        self.bootstrap.append({'kind':'cli','arguments':list(args),
            'internal_sql_commands':None,'scope':'CI_BOOTSTRAP_NOT_HOSTED_BUDGET'})
        # Deliberately bypass registered-chain CLI slots and their hosted envelopes.
        return BASE.cli(self,*args,timeout=timeout)

    def fetch(self):
        activate_sources()
        migrations=super().fetch()
        sources=json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA<=set(sources):raise ValueError('diagnostic_candidate_missing')
        for name in EXTRA:
            candidate=(self.sources/name).read_bytes();checkout=(ROOT/name).read_bytes()
            if hashlib.sha256(candidate).hexdigest()!=sources[name] or candidate.replace(b'\r\n',b'\n')!=checkout.replace(b'\r\n',b'\n'):
                raise ValueError('diagnostic_source_binding')
        from cli_meter import source_commit
        if source_commit(self.result)!=enabled(os.environ):raise ValueError('diagnostic_commit_mismatch')
        return migrations

    def probe(self):
        from ci_wal_diagnostic import run
        from native_runtime import NativeRuntime
        runtime=NativeRuntime.disposable(self);connection=None
        try:
            connection=runtime.connect()
            receipt=run(connection,environment='disposable_ci',ids=IDS,context=CONTEXT,
                ci_ca_path=self.work/'fmz-ci-ca.crt')
            if (receipt.get('status')!='DIAGNOSTIC_ONLY'
                or receipt.get('full_chain_admission') is not False
                or receipt.get('wal_zero_pass') is not False
                or type(receipt.get('commands')) is not int or not 0<=receipt['commands']<=16):
                raise ValueError('diagnostic_receipt_contract')
            self.save('ci-wal-diagnostic.json',receipt)
            return receipt
        finally:
            try:
                if connection is not None:connection.close()
            finally:runtime.clear()

    def postcheck(self):
        from ci_source_binding import verify_all
        sources=json.loads((self.out/'candidate.json').read_text())['sources']
        self.save('loaded-source-postchecks.json',verify_all(ROOT,self.sources,sources))

    def cleanup(self):
        if not self.stack_attempted:return {'attempted':False,'confirmed':True}
        self.cli('stop','--no-backup',timeout=120)
        return {'attempted':True,'confirmed':True,'scope':'fresh_disposable_stack_only'}

    def run(self):
        code=1
        try:
            enabled(os.environ)
            self.result['phase']='candidate';migrations=self.fetch()
            self.result['phase']='ci_bootstrap';self.install()
            platform=self.result['platform']
            if platform['image']!=IMAGE or DIGEST not in platform['repository_digests']:
                raise ValueError('diagnostic_image_binding')
            self.rebuild(migrations)
            if self.result['migrations_applied']!=45:raise ValueError('diagnostic_schema_45')
            self.result['phase']='diagnostic'
            receipt=self.probe();self.postcheck()
            self.result['diagnostic_commands']=receipt['commands']
            self.result['diagnostic_completed']=(receipt.get('rollback_confirmed') is True
                and not receipt.get('limitations') and len(receipt.get('queries',[]))==4
                and all(q.get('complete') is True for q in receipt['queries']))
            code=0 if self.result['diagnostic_completed'] else 1
        except Exception as error:
            self.result['error_type']=type(error).__name__  # Never exception text.
        finally:
            try:self.result['disposable_cleanup']=self.cleanup()
            except Exception as error:
                self.result['disposable_cleanup']={'attempted':True,'confirmed':False,
                    'error_type':type(error).__name__};code=1
            self.save('diagnostic-bootstrap.json',{'scope':'CI_ONLY_NOT_HOSTED_METER',
                'entries':self.bootstrap,'direct_sql_attempted':sum(
                    x['attempted_commands'] for x in self.bootstrap if x['kind']=='direct_sql'),
                'cli_invocations':sum(x['kind']=='cli' for x in self.bootstrap),
                'cli_internal_sql_total':None,'exact_total_sql_claim':False,
                'diagnostic_sql_separately_capped':16})
            self.result.update(status='DIAGNOSTIC_ONLY',full_chain_admission=False,
                hosted_admitted=False,wal_zero_pass=False,causal_attribution=False)
            self.save('result.json',self.result)
            print(json.dumps({'status':'DIAGNOSTIC_ONLY',
                'diagnostic_completed':self.result.get('diagnostic_completed',False),
                'full_chain_admission':False,'exitcode':code}),flush=True)
        return code

if __name__=='__main__':
    # Reject default-off invocations before creating work directories or a Gate.
    enabled(os.environ)
    sys.exit(DiagnosticGate().run())
