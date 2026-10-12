"""One scoped installation/removal canary. Never issues tokens or runs workflows."""
import hashlib,importlib.util,json,os,pathlib,re,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'controller_v1'))
import auth_preflight as pre
j=pre.j;m=pre.m
spec=importlib.util.spec_from_file_location('guard_lifecycle_hosted',HERE/'lifecycle.py')
life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def admit(folder):
    p=disk(folder);r=json.loads((p/'result.json').read_text())
    if r.get('status')!='CLEAN_CI_PASS' or r.get('temporary_guard_checks')!=32 or r.get('full_controller_guard_node_tests')!=186:raise m.Stop('new_guard_ci_required')
    sources=json.loads((p/'candidate.json').read_text())['sources']
    for name,sha in sources.items():
        if hashlib.sha256(disk(m.ROOT/name).read_bytes()).hexdigest()!=sha:raise m.Stop('tested_composition_changed')
    if '_offline/phase6e11/controller_guard_v1/hosted_lifecycle.py' not in sources:raise m.Stop('runner_not_bound')
    return {'ci_result_sha256':hashlib.sha256((p/'result.json').read_bytes()).hexdigest(),'ci_run':r['run_id'],'sources':sources}

def main(ci):
    admitted=admit(ci);ids=pre.identifiers();run=str(uuid.uuid4())
    folder=m.ROOT/'supabase/.temp'/('phase6e11-guard-hosted-'+run.replace('-',''));folder.mkdir()
    m.save(m.ROOT/'supabase/.temp/phase6e11-guard-lifecycle-once.json',{'run':run,'folder':folder.name})
    m.save(folder/'contract.json',{**admitted,'run':run,'auth_calls':0,'row_writes':0,'guard_seconds':180,
        'max_commands':128,'safety_reserved_commands':40,'max_seconds':240,'connections':1,'full_fingerprint_cycles':0,'retries':0,
        'scope':'exact temporary guard installation and unconditional removal only; NOT Auth/workflow PASS'})
    journal=db=ledger=None;granted=False;cleanup=False;serial=0;normal=0;safety=0;deadline=time.monotonic()+240
    result={'status':'NO_GO','auth_calls':0,'application_writes':0,'folder':folder.name,'phase':'admission'}
    try:
        token=m.p.jit.sb.credential();journal=j.Journal(token,folder);journal.inspect()
        ledger=m.Ledger(folder/'ledger')
        # Reserve cleanup before any network mutation. A stopped action cannot
        # consume these commands or block the independently authorized removal.
        for _ in range(40):ledger.reserve_query()
        def charge():
            nonlocal normal,safety
            if cleanup:
                safety+=1
                if safety>40:raise m.Stop('safety_budget')
            else:
                if time.monotonic()>deadline:raise m.Stop('probe_deadline')
                ledger.reserve_query();normal+=1
        class ScopedLedger(m.Ledger):
            def reserve_query(self):charge();return super().reserve_query()
        granted=True;result['phase']='jit';journal.grant()
        result['phase']='tls';db=m.c.Connection(json.loads((m.c.CONNECT/'connect.json').read_text()),token,m.c.CA)
        def read(sql):
            nonlocal serial
            serial+=1;target=folder/('read-'+str(serial).zfill(2));target.mkdir()
            child=ScopedLedger(target/'ledger',lock_scope=target/'lock')
            tx=m.stream.t.old.s.Transaction(db,target,child)
            try:
                tx.start_readonly()
                rows=tx.measured('/* fmz6e11:qv1:guard_lifecycle */ '+sql,'scoped_metadata')
                proof=tx.close_proof();m.save(target/'io-proof.json',proof)
                return rows
            finally:
                rb=tx.rollback();child.close()
                if not rb['confirmed']:raise m.Stop('rollback_not_confirmed')
        def query(sql,reserved):
            nonlocal cleanup
            if sql=='ROLLBACK':
                cleanup=True
                # Drain failed libpq results; never replay the failed command.
                started=time.monotonic()
                while db.conn:
                    while db.lib.PQisBusy(db.conn):
                        if time.monotonic()-started>3:raise m.Stop('safety_drain_timeout')
                        if db.lib.PQconsumeInput(db.conn)!=1:raise m.Stop('safety_drain_transport')
                        time.sleep(.001)
                    value=db.lib.PQgetResult(db.conn)
                    if not value:break
                    db.lib.PQclear(value)
            for command in life.ddl_commands(sql):
                charge();ledger.event('ddl_command_started',sql_sha256=hashlib.sha256(command.encode()).hexdigest(),safety=cleanup)
                db.query(command,timeout=8)
                ledger.event('ddl_command_confirmed',safety=cleanup)
        def save(name,value):m.save(folder/(name+'.json'),value)
        result['phase']='project_binding'
        meta=json.loads(read(m.p.jit.META_SQL)[0][0])
        expected=[p.stem.split('_',1) for p in sorted((m.ROOT/'supabase/migrations').glob('*.sql'))]
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['database']!='postgres' or meta['role']!='postgres' or meta['read_only']!='on' or [[r['version'],r['name']] for r in meta['migrations']]!=expected or len(expected)!=43:
            raise m.Stop('project_or_migration_binding')
        save('project-binding',{'project':j.jit.PROJECT,'migrations':43,'verify_full':True,'ca_hostname':True,'jit':True})
        result['phase']='lifecycle'
        result.update(life.execute(run=run,ids=ids,query=query,read=read,save=save,seconds=180))
    except j.Rejected as error:result.update(status='NO_GO',phase=error.phase,reason=error.code)
    except Exception as error:
        result['reason']=str(error) if isinstance(error,(m.Stop,ValueError)) and re.fullmatch('[a-zA-Z0-9_]+',str(error)) else type(error).__name__
        result['status']='NO_GO'
    finally:
        if db:db.close()
        if ledger:ledger.close()
        if granted:
            try:journal.close();result['jit_revoked']=True
            except Exception:result.update(status='NO_GO',jit_revoked=False)
        if journal:journal.token=None
        token=None;result.update(commands=normal+safety,normal_commands=normal,safety_commands=safety)
        m.save(folder/'result.json',result)
    print(json.dumps(result));return 0 if result['status']=='GUARD_LIFECYCLE_PASS' and result.get('jit_revoked') else 2
if __name__=='__main__':sys.exit(main(pathlib.Path(sys.argv[1]).resolve()))
