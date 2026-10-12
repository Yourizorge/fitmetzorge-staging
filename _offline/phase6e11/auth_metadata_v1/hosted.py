"""One bounded metadata-audit canary; no token issuance or application workflow."""
import hashlib,importlib.util,json,os,pathlib,re,sys,time,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit,probe
sys.path.insert(0,str(HERE.parent/'controller_v1'))
import auth_preflight as pre
j=pre.j;m=pre.m
spec=importlib.util.spec_from_file_location('metadata_guard_lifecycle',HERE.parent/'controller_guard_v1/lifecycle.py')
life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p

def admit(folder):
    result=json.loads(disk(folder/'result.json').read_text())
    if result.get('status')!='CLEAN_CI_PASS' or result.get('auth_metadata_checks')!=34 or result.get('real_auth_ci_checks')!=18 or result.get('real_auth_exact_write_contracts')!=18 or result.get('full_controller_guard_node_tests')!=197:raise ValueError('new_metadata_ci_required')
    sources=json.loads(disk(folder/'candidate.json').read_text())['sources']
    for name,h in sources.items():
        if hashlib.sha256(disk(m.ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('tested_composition_changed')
    if '_offline/phase6e11/auth_metadata_v1/hosted.py' not in sources:raise ValueError('runner_not_bound')
    return {'ci_run':result['run_id'],'result_sha256':hashlib.sha256(disk(folder/'result.json').read_bytes()).hexdigest(),'sources':sources}

def same_catalog(before,after,schema,installed):
    a={(k,n):h for k,n,h in before};b={(k,n):h for k,n,h in after}
    if any(b.get(k)!=v for k,v in a.items()):raise ValueError('existing_catalog_changed')
    additions=set(b)-set(a)
    if installed:
        if not additions or any(not(n==schema or n.startswith(schema+'.') or n.startswith('auth.') and '.'+schema+'_' in n) for k,n in additions):raise ValueError('unexpected_catalog_object')
    elif additions:raise ValueError('audit_removal_incomplete')
    return {'existing_objects':len(a),'existing_equal':True,'own_additions':len(additions)}

def tagged_metadata(sql):return '/* fmz6e11:qv1:auth_metadata_admission */ '+sql

def corrected_admission():
    prior=m.ROOT/'supabase/.temp/phase6e11-auth-metadata-hosted-19239cccf8c244fe9c8845ca1a92c722'
    value=json.loads((prior/'result.json').read_text());rb=json.loads((prior/'io-admission/rollback.json').read_text());closed=json.loads((prior/'closed.json').read_text())
    if value.get('reason')!='unregistered_readonly_query' or value.get('commands')!=8 or value.get('auth_calls')!=0 or not value.get('jit_revoked') or not rb.get('confirmed') or closed.get('remaining_mappings')!=0:raise ValueError('wrong_corrected_attempt')
    if (prior/'before-catalog.json').exists() or (prior/'install-started.json').exists():raise ValueError('prior_mutation_not_excluded')
    return {'prior_run':prior.name,'prior_result_sha':hashlib.sha256((prior/'result.json').read_bytes()).hexdigest(),'prior_commands':8}

def main(folder_ci,corrected=False):
    admission=admit(folder_ci);ids=pre.identifiers();run=str(uuid.uuid4());action=str(uuid.uuid4());session=str(uuid.uuid4())
    prior=corrected_admission() if corrected else {'prior_commands':0}
    normal_limit=88-prior['prior_commands']
    folder=m.ROOT/'supabase/.temp'/('phase6e11-auth-metadata-hosted-'+run.replace('-',''));folder.mkdir()
    marker='phase6e11-auth-metadata-canary-'+('corrected-' if corrected else '')+'once.json'
    m.save(m.ROOT/'supabase/.temp'/marker,{'run':run,'folder':folder.name,**prior})
    m.save(folder/'contract.json',{**admission,'run':run,'action':action,'actor_sha':hashlib.sha256(ids['a_member'].encode()).hexdigest(),
        'fixture_sha':hashlib.sha256(session.encode()).hexdigest(),'expected':{'auth.sessions':{'INSERT':1,'UPDATE':1,'DELETE':1}},
        'max_commands':128-prior['prior_commands'],'combined_max_commands':128,'prior':prior,'safety_reserved':40,'max_seconds':240,'guard_seconds':180,'connections':1,'full_cycles':0,'automatic_retries':0,'auth_calls':0})
    db=journal=ledger=None;granted=False;cleanup=False;normal=0;safety=0;serial=0;started=time.monotonic()
    result={'status':'NO_GO','auth_calls':0,'application_writes':0,'folder':folder.name}
    def save(name,value):m.save(folder/(name+'.json'),value)
    try:
        token=m.p.jit.sb.credential();journal=j.Journal(token,folder);journal.inspect()
        ledger=m.Ledger(folder/'ledger')
        for _ in range(40):ledger.reserve_query()
        def charge():
            nonlocal normal,safety
            if cleanup:
                safety+=1
                if safety>40:raise m.Stop('safety_budget')
            else:
                if normal>=normal_limit or time.monotonic()-started>240:raise m.Stop('normal_budget')
                ledger.reserve_query();normal+=1
        granted=True;result['phase']='jit';journal.grant()
        result['phase']='tls';db=m.c.Connection(json.loads((m.c.CONNECT/'connect.json').read_text()),token,m.c.CA)
        def command(sql):charge();return db.query(sql,timeout=5)
        def read(sql,persist=True):
            nonlocal serial
            serial+=1;command('BEGIN TRANSACTION READ ONLY')
            try:
                if command("select current_setting('transaction_read_only')")!=[['on']]:raise ValueError('readonly_failed')
                value=command(sql)
                if persist:save('read-'+str(serial),{'sql_sha':hashlib.sha256(sql.encode()).hexdigest(),'rows':value})
                return value
            finally:command('ROLLBACK')
        def ddl(text,cost=None):
            nonlocal cleanup
            if text=='ROLLBACK':
                cleanup=True
                # A failed libpq command may still have results to drain.
                limit=time.monotonic()+3
                while db.conn:
                    while db.lib.PQisBusy(db.conn):
                        if time.monotonic()>limit:raise ValueError('drain_timeout')
                        if db.lib.PQconsumeInput(db.conn)!=1:raise ValueError('drain_failed')
                        time.sleep(.001)
                    item=db.lib.PQgetResult(db.conn)
                    if not item:break
                    db.lib.PQclear(item)
                command(text);return
            if text.startswith('/* fmz6e11:controller_guard_v1:'):
                parts=life.ddl_commands(text)
            else:
                # Only the fixed audit renderer, never arbitrary SQL splitting.
                tag=next((t for t in ('install','remove') if 'DO $'+t+'$' in text),None)
                if not tag:raise ValueError('unregistered_ddl')
                head,body=text.split('DO $'+tag+'$',1)
                if not body.endswith('END $'+tag+'$; COMMIT;'):raise ValueError('ddl_envelope')
                parts=[p.strip() for p in head.split(';') if p.strip()]+['DO $'+tag+'$'+body[:-len(' COMMIT;')],'COMMIT']
            for part in parts:command(part)
        # Reuse the exact text-free monitor for the read-only project admission.
        class Charged(m.Ledger):
            def reserve_query(self):charge();return super().reserve_query()
        result['phase']='read_only_project_admission'
        io_folder=folder/'io-admission';io_folder.mkdir();child=Charged(io_folder/'ledger',lock_scope=io_folder/'lock')
        tx=m.stream.t.old.s.Transaction(db,io_folder,child)
        try:
            tx.start_readonly();meta=json.loads(tx.measured(tagged_metadata(m.p.jit.META_SQL),'metadata_project')[0][0]);save('io-admission',tx.close_proof())
        finally:
            rb=tx.rollback();child.close()
            if not rb['confirmed']:raise ValueError('rollback_failed')
        expected=[p.stem.split('_',1) for p in sorted((m.ROOT/'supabase/migrations').glob('*.sql'))]
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['database']!='postgres' or meta['role']!='postgres' or [[r['version'],r['name']] for r in meta['migrations']]!=expected or len(expected)!=43:raise ValueError('project_migration_binding')
        save('project',{'project':'mokxyyullfhkfalopbzd','migrations':43,'verify_full':True,'official_ca_hostname':True,'jit':True})
        if read("select count(*) from pg_trigger where tgrelid='auth.sessions'::regclass and not tgisinternal")!=[['0']]:raise ValueError('unexpected_session_trigger')
        def action_body(guard_receipt):
            nonlocal cleanup
            schema=audit.scope(run,ids);receipt=None;attempted=False;before=None;out={'status':'NO_GO'};phase='before_saved'
            try:
                before=read(life.catalog_sql());save('metadata-before-catalog',before)
                save('metadata-install-started',{'sql_sha':hashlib.sha256(audit.install(run,ids,guard_receipt['expires_at']).encode()).hexdigest()})
                phase='audit_install';attempted=True;ddl(audit.install(run,ids,guard_receipt['expires_at']))
                receipt=audit.validate(json.loads(read(audit.inspect(run,ids))[0][0]),run,ids,guard_receipt['expires_at']);save('metadata-receipt',receipt)
                save('metadata-install-pair',same_catalog(before,read(life.catalog_sql()),schema,True))
                phase='action_before';baseline=json.loads(read(probe.snapshot(ids,session))[0][0]);save('action-before',baseline)
                if baseline['fixture_rows']!=0:raise ValueError('fixture_already_exists')
                # Fixed arm statement executed as one server-side transaction.
                text=audit.arm(run,ids,action,'a_member','verify')
                for part in ['BEGIN',"SET LOCAL lock_timeout='1s'",text[text.index('DO $arm$'):text.index(' COMMIT;')],'COMMIT']:command(part)
                phase='action_started';save('action-started',{'run':run,'action':action})
                command('BEGIN');command("SET LOCAL statement_timeout='2s'");command("SET LOCAL lock_timeout='1s'")
                plans=[]
                for index,sql in enumerate(probe.sql_sequence(session,ids['a_member'])):
                    plan=probe.plan_summary(command('explain(analyze,verbose,buffers,format json) '+sql)[0][0]);save('statement-'+str(index),plan);plans.append(plan)
                command('COMMIT');phase='action_confirmed';save('action-confirmed',{'statements':3})
                events=json.loads(read(audit.events(run,ids,action))[0][0]);save('action-events',events)
                after=json.loads(read(probe.snapshot(ids,session))[0][0]);save('action-after',after)
                phase='after_saved'
                if baseline!=after:raise ValueError('protected_synthetic_session_drift')
                proof=probe.validate(events,action,session,ids['a_member']);save('action-pair',{**proof,'data_equal':True,'plans':plans})
                command(audit.disarm(run,ids,action));out={'status':'AUDIT_CANARY_PASS',**proof,'data_equal':True}
            except Exception as error:
                out.update(phase=phase,error_class=type(error).__name__,reason=str(error) if isinstance(error,ValueError) and re.fullmatch('[a-z_]+',str(error)) else 'scoped_action_failed')
                raise
            finally:
                # Separately authorized safety removal, not fixture cleanup.
                ddl('ROLLBACK')
                if attempted:
                    state=json.loads(read(audit.inspect(run,ids),persist=False)[0][0])
                    if state['function_count']:
                        proven=audit.validate(state,run,ids,guard_receipt['expires_at'])
                        if receipt and proven!=receipt:raise ValueError('audit_receipt_changed')
                        try:save('safety-action-events',read(audit.events(run,ids,action),persist=False))
                        except Exception:out.update(status='NO_GO',safety_evidence_missing=True)
                        ddl(audit.remove(run,ids,proven))
                    pair=same_catalog(before,read(life.catalog_sql(),persist=False),schema,False)
                    save('metadata-removal-pair',pair)
                out['metadata_removed']=True;save('audit-result',out)
            return out
        result['phase']='lifecycle'
        value=life.execute(run=run,ids=ids,query=ddl,read=read,safety_read=lambda sql:read(sql,persist=False),save=save,seconds=180,action=action_body)
        result.update(value)
        if value['status']=='GUARD_LIFECYCLE_PASS' and value.get('action',{}).get('status')=='AUDIT_CANARY_PASS':result['status']='AUTH_METADATA_HOSTED_CANARY_PASS'
        else:result['status']='NO_GO'
    except j.Rejected as e:result.update(status='NO_GO',phase=e.phase,reason=e.code)
    except Exception as e:result.update(status='NO_GO',reason=str(e) if isinstance(e,(ValueError,m.Stop)) and re.fullmatch('[A-Za-z0-9_]+',str(e)) else type(e).__name__)
    finally:
        if db:db.close()
        if ledger:ledger.close()
        if granted:
            try:journal.close();result['jit_revoked']=True
            except Exception:result.update(status='NO_GO',jit_revoked=False)
        if journal:journal.token=None
        token=None;result.update(commands=normal+safety,combined_commands=normal+safety+prior['prior_commands'],normal_commands=normal,safety_commands=safety)
        save('result',result)
    print(json.dumps(result));return 0 if result['status']=='AUTH_METADATA_HOSTED_CANARY_PASS' else 2
if __name__=='__main__':
    if len(sys.argv) not in (2,3) or len(sys.argv)==3 and sys.argv[2]!='--corrected-preflight-once':raise ValueError('arguments')
    sys.exit(main(pathlib.Path(sys.argv[1]).resolve(),len(sys.argv)==3))
