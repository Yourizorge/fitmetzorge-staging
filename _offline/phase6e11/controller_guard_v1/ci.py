"""Fresh source-bound clean Supabase CI. No hosted access or staging secrets."""
import contextlib,hashlib,importlib.util,json,pathlib,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard_previous_controller_ci',HERE.parent/'controller_v1/ci.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
CONTROLLER_NAMES=['core.mjs','core.test.mjs','oidc.mjs','oidc.test.mjs','store.mjs','auth.mjs','auth.test.mjs',
 'auth_guard.mjs','auth_guard.test.mjs','manifest.mjs','manifest.test.mjs','workflow_evidence.mjs',
 'workflow_evidence.test.mjs','forensic.test.mjs']
GUARD_NAMES=['guard.py','checks.py','issuance.mjs','issuance.test.mjs','ci.py','local.py','lifecycle.py','hosted_lifecycle.py','ops.py','test_artifact.py','artifact.py','auth_service.py','auth_service.mjs']
EXTRA={'_offline/phase6e11/controller_v1/'+n for n in CONTROLLER_NAMES}
EXTRA|={'_offline/phase6e11/controller_guard_v1/'+n for n in GUARD_NAMES}
EXTRA|={'_offline/phase6e11/edge_bridge_v2/handler.mjs',*('_offline/phase6e11/edge/'+n for n in ['handler.mjs','core.mjs','frozen.mjs'])}
EXTRA|={'_offline/phase6e11/auth_metadata_v1/'+n for n in ['audit.py','checks.py','local.py','probe.py','hosted.py','test_probe.py']}
EXTRA|={'_offline/phase6e11/auth_metadata_v1/'+n for n in ['auth_contract.py','test_auth_contract.py','test_hosted.py']}
EXTRA|={'_offline/phase6e11/auth_metadata_v1/'+n for n in ['hashes.mjs','hashes.test.mjs']}
old.EXTRA|=EXTRA

class Gate(old.Gate):
    def fetch(self):
        migrations=super().fetch()
        files=json.loads((self.out/'candidate.json').read_text())['sources']
        if not EXTRA<=set(files):raise RuntimeError('full_guard_composition_missing')
        self.save('guard-composition.json',{'sources':{n:files[n] for n in sorted(EXTRA)},
            'controller_full_source_bound':True,'hosted_auth_proven':False})
        return migrations
    def regressions(self):
        super().regressions()
        tests=sorted((self.sources/'_offline/phase6e11/controller_v1').glob('*.test.mjs'))
        tests+=sorted((self.sources/'_offline/phase6e11/controller_guard_v1').glob('*.test.mjs'))
        output=self.command('full-controller-guard-tests',['node','--test','--test-reporter=tap',*map(str,tests)])
        import re
        count=re.search(r'# tests (\d+)',output.stdout)
        if not count or int(count[1])!=197:raise RuntimeError('full_node_count')
        self.result['full_controller_guard_node_tests']=197
        self.command('artifact-receipt-tests',['python3',str(self.sources/'_offline/phase6e11/controller_guard_v1/test_artifact.py')])
        self.result['artifact_receipt_tests']=8
        folder=self.sources/'_offline/phase6e11/controller_guard_v1'
        spec=importlib.util.spec_from_file_location('guard',folder/'guard.py')
        g=importlib.util.module_from_spec(spec);sys.modules['guard']=g;spec.loader.exec_module(g)
        spec=importlib.util.spec_from_file_location('guard_database_checks',folder/'checks.py')
        checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
        def args(actor):
            if actor=='supabase_auth_admin':
                # This is the disposable container's own local credential, not
                # a staging secret. Peer/socket auth is intentionally denied.
                return ['docker','exec','-i',self.container,'sh','-c',
                    'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X -h 127.0.0.1 -U supabase_auth_admin -d postgres -qAt -v ON_ERROR_STOP=1']
            return ['docker','exec','-i',self.container,'psql','-X','-U',actor,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
        def sql(q,actor='postgres'):
            if actor in ('anon','authenticated','service_role'):
                q='set role '+actor+';'+q;actor='postgres'
            return self.command('guard-check',args(actor),sql="set lock_timeout='200ms';set statement_timeout='5s';"+q,timeout=15,check=False)
        @contextlib.contextmanager
        def hold(q):
            p=subprocess.Popen(args('postgres'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                p.stdin.write(q+"\nselect 'fmz_guard_held';\n");p.stdin.flush()
                while p.stdout.readline().strip()!='fmz_guard_held':
                    if p.poll() is not None:raise RuntimeError('hold_failed')
                yield
            finally:
                try:p.communicate('rollback;\n',timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.communicate()
        result=checks.run(sql,hold)
        self.save('temporary-guard-database.json',result)
        if result['checks']!=34 or result['guard_objects_remaining']!=0:raise RuntimeError('guard_database_incomplete')
        self.result['temporary_guard_database']=result['status'];self.result['temporary_guard_checks']=result['checks']
        metadata_folder=self.sources/'_offline/phase6e11/auth_metadata_v1'
        sys.path.insert(0,str(metadata_folder))
        spec=importlib.util.spec_from_file_location('metadata_database_checks',metadata_folder/'checks.py')
        meta=importlib.util.module_from_spec(spec);spec.loader.exec_module(meta)
        result=meta.run(sql,hold,checks.IDS);self.save('auth-metadata-database.json',result)
        if result['checks']!=34:raise RuntimeError('metadata_database_incomplete')
        self.result['auth_metadata_database']=result['status'];self.result['auth_metadata_checks']=result['checks']
        self.command('metadata-probe-unit-tests',['python3',str(metadata_folder/'test_probe.py')])
        self.result['metadata_probe_unit_tests']=7
        self.command('audit-session-hash-tests',['node','--test',str(metadata_folder/'hashes.test.mjs')])
        self.result['audit_session_hash_tests']=4
        spec=importlib.util.spec_from_file_location('guard_real_auth_ci',folder/'auth_service.py')
        real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
        result=real.run(self);self.save('real-auth-ci.json',result)
        self.result['real_auth_ci']=result['status'];self.result['real_auth_ci_checks']=result['checks']
        from auth_contract import Contract
        contracts={}
        for row in result['proof']:
            role=row['role']
            if role not in contracts:contracts[role]=Contract(row['after']['events'][0]['actor_sha'])
            contracts[role].validate(row['operation'],row['after']['events'],row['result'].get('key_sha'))
        if len(contracts)!=3 or any(c.step!=6 for c in contracts.values()):raise RuntimeError('auth_exact_contract_incomplete')
        self.result['real_auth_exact_write_contracts']=18
        self.command('auth-exact-negative-tests',['python3',str(metadata_folder/'test_auth_contract.py'),str(self.out/'real-auth-ci-observed.json')])
        self.result['auth_exact_negative_tests']=4
if __name__=='__main__':sys.exit(Gate().run())
