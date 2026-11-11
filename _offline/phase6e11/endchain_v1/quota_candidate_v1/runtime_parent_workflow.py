"""Versioned worker-path adapter; inherited native workflow and IO gates unchanged."""
import hashlib,json,os,pathlib,re,subprocess,sys,threading,time,uuid
from integral_ci import bind_parameters,capture

def dispatch_reply(process, reply, primary=None):
    """A rejected dispatch is terminal, including when its error reply is lost."""
    try:
        process.stdin.write(json.dumps(reply,default=str)+'\n')
        process.stdin.flush()
    except BaseException as secondary:
        if primary is None:
            raise
        primary.add_note('workflow_error_reply_secondary:'+type(secondary).__name__)
    if primary is not None:
        raise primary

class WorkflowBridge:
    def workflow(self,gate,request,outer_sql,ids,run_id):
        import auth_failure_transport
        from .compiler import read_source, require, sha
        from .runtime_worker_evidence import bind,save,validate_result,WaitEvidence
        binding,worker_sources,case=bind(self)
        worker_evidence=WaitEvidence(binding,case,'workflow')
        transport_source = '_offline/phase6e11/endchain_v1/auth_failure_transport.py'
        require(sha(pathlib.Path(auth_failure_transport.__file__).read_bytes())
                == self.quota['manifest']['sources'].get(transport_source)
                == sha(read_source(self.quota['root'], transport_source)),
                'workflow_http_transport_source')
        import psycopg
        from psycopg.types.json import Jsonb
        from psycopg import sql as pgsql
        runtime=self.native_runtime(gate);connections={}
        try:
            for channel in ('setup','writer','reader','workflow'):
                connections[channel]=runtime.connect()
                if channel=='setup':self.meter.setup_connection_owned=True
        except Exception as error:
            self.abort('workflow_connection_failed')
            for channel,connection in connections.items():
                try:
                    connection.close()
                    if channel=='setup':self.meter.setup_connection_owned=False
                except Exception as secondary:
                    error.add_note('workflow_connection_close_secondary:'+type(secondary).__name__)
            raise
        monitor=None;io_receipts=[]
        def raw_query(channel,phase,text,values=()):
            # SQL templates are fixed candidate sources, values are bound by the
            # driver. Repeated numbered parameters retain their original value.
            faults=getattr(self,'phase_faults',None)
            if faults is not None:
                text,values=faults.prepare_native(channel,phase,text,values,self.action)
            q,params=bind_parameters(text,values,lambda value:Jsonb(value) if isinstance(value,(dict,list)) else value)
            first=self.action=={'kind':'workflow','step':0}
            if first and channel=='reader' and phase=='measurement' and 'scoped_workflow_pair' in text:
                self.step_zero_reads+=1
            if not self.injected and first and ((self.fault=='before_call' and channel=='workflow' and phase=='call')
                    or (self.fault=='after_snapshot' and self.step_zero_reads==2 and channel=='reader' and phase=='measurement')):
                self.injected=True;raise RuntimeError('ci_injected_'+self.fault)
            self.before_sql(phase,text)
            try:
                cur=connections[channel].execute(q,params)
                rows=cur.fetchall() if cur.description else []
                self.after_sql(phase,text)
                if faults is not None:faults.native_after(channel,phase,text,self.action)
                if not self.injected and first and self.fault=='after_commit' and channel=='workflow' and phase=='commit':
                    self.injected=True;raise RuntimeError('ci_injected_after_commit')
                return rows
            except psycopg.Error as e:
                if faults is not None:faults.native_error(channel,phase,text,self.action,e.sqlstate)
                if hasattr(self,'abort'):self.abort('workflow_database_command_failed')
                raise RuntimeError('ci_sql_'+(e.sqlstate or 'unknown')) from None
        def query(channel,phase,text,values=()):
            track=monitor is not None and re.match(r'\s*(?:/\*.*?\*/\s*)?(select|with|insert|update|delete)\b',text,re.I|re.S)
            pure_read=channel=='reader' or (channel,phase) in {
                ('workflow','identity'),('workflow','binding'),('workflow','read_binding'),('setup','lifecycle_bind')}
            qid=monitor.bind(text,values,read_only=pure_read) if track else None
            result=raw_query(channel,phase,text,values)
            if qid is not None:monitor.executed(qid)
            return result
        process=None;timer=None;result=None;enabled=None;controls=None;restored=None;enable_attempted=False
        try:
            def start_reader():
                nonlocal monitor
                query('reader','lifecycle_reader_begin','BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY')
                if query('reader','lifecycle_reader_check',"select current_setting('transaction_read_only')='on' readonly")[0]['readonly'] is not True:
                    raise RuntimeError('ci_lifecycle_readonly')
                from integral_io import QueryIO
                monitor=QueryIO(raw_query,on_failure=lambda evidence:gate.save('integral-workflow-io-failure.json',evidence));monitor.start()
            def end_reader(label):
                nonlocal monitor
                if monitor is not None:
                    gate.save('integral-'+label+'-io.json',monitor.close());monitor=None
                query('reader','lifecycle_reader_end','ROLLBACK')
            start_reader()
            roles={'member':ids['a_member'],'trainer':ids['a_trainer'],'b':ids['b_member']}
            from auth_protocol import STATS,difference
            auth_before=query('reader','workflow_auth_before','select '+STATS+' value')[0]['value']
            # Verify the actual token with GoTrue again before it supplies claims.
            import urllib.request,base64
            from auth_failure_transport import complete_body, StrictHTTPHandler, NoRedirect
            token=request['tokens']['a_trainer']
            req=urllib.request.Request(runtime.auth_base+'/user',headers={'Authorization':'Bearer '+token,'apikey':request['anon']})
            self.workflow_dispatch.before(0)
            try:
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),StrictHTTPHandler())
                with opener.open(req,timeout=5) as response:
                    body=complete_body(response)
                    if len(body)>20000:raise RuntimeError('ci_auth_body_bound')
                    user=json.loads(body);status=response.status
            except Exception:
                self.workflow_dispatch.after(0,'lost_response')
                raise
            self.workflow_dispatch.after(0,'response_received',status)
            claims=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
            if user['id']!=ids['a_trainer'] or claims['sub']!=user['id']:raise RuntimeError('ci_auth_identity')
            from control_recovery import CONTROL_SQL,BEFORE_SQL,intent
            control_sql=CONTROL_SQL
            control_before=query('reader','control_before',BEFORE_SQL)[0]
            controls=control_before['value']
            # Persist ownership before either mutation, including a lost response.
            proof,enabled=intent(controls,run_id,control_before['expires_at'])
            gate.save('integral-control-intent.json',{'run_id':run_id,'expected':enabled,
                'before_sha':hashlib.sha256(json.dumps(controls,sort_keys=True).encode()).hexdigest()})
            headers={'x-fmz6e11-proof':proof}
            enable_attempted=True
            if query('setup','control_enable',"update fmz6e11_private.config set enabled=true,proof_hash=encode(sha256(convert_to($1,'UTF8')),'hex') where id and not enabled and proof_hash is null returning id",[proof])!=[{'id':True}]:raise RuntimeError('ci_control_enable_count')
            if query('setup','control_enable',"update fmz6e11_request_private.control set enabled=true,expires_at=$1::timestamptz where id and not enabled and expires_at is null returning id",[enabled['request']['expires_at']])!=[{'id':True}]:raise RuntimeError('ci_bridge_enable_count')
            observed=query('reader','control_after',control_sql)[0]['value']
            if observed!=enabled:raise RuntimeError('ci_controls_not_enabled')
            gate.save('integral-control-enable-pair.json',{'before_sha':hashlib.sha256(json.dumps(controls,sort_keys=True).encode()).hexdigest(),
                'after_sha':hashlib.sha256(json.dumps(enabled,sort_keys=True).encode()).hexdigest(),'expected_updates':2,'actual_updates':2})
            times=query('reader','fixture_times',"select clock_timestamp()-interval '10 seconds' starts_at,clock_timestamp()+interval '3 minutes' ends_at")[0]
            import fixture_lifecycle as fixture
            ctx=self.fixture_context
            ctx.update(trainer=ids['a_trainer'],member=ids['a_member'],b_member=ids['b_member'])
            window=ctx['window'];by_route={'A':ctx['a'],'B':ctx['b']}
            prepare={'op':'command','action':'prepare','window':None,'workspace':None,'expected':0,'key':ctx['key'],
                'data':{'scenario':'kg',**{k:v.isoformat() for k,v in times.items()}}}
            seed=fixture.perform(query,gate.save,ctx,'seed',fixture.seed_writes(ctx),fixture.SEED,
                [window,ctx['a'],ctx['b'],ctx['trainer'],ctx['member'],ctx['b_member'],ctx['key'],
                 times['starts_at'].isoformat(),times['ends_at'].isoformat(),prepare],claims,headers)
            if len(seed)!=1 or seed[0]['value'].get('revision')!=1:raise RuntimeError('ci_seed_incomplete')
            gate.save('integral-seed-io-pair.json',monitor.checkpoint())
            activation={'op':'command','action':'activate','window':window,'workspace':None,'expected':1,
                'key':str(uuid.uuid4()),'data':{}}
            active=fixture.perform(query,gate.save,ctx,'activate',[
                ['windows','UPDATE',[window]],['windows','UPDATE',[window]],
                ['audit','INSERT',[window,ctx['trainer'],'activate']],['requests','INSERT',[ctx['trainer'],activation['key']]]],
                'select public.fmz6e11_call($1::jsonb) value',[activation],claims,headers)[0]['value']
            if active.get('revision')!=2 or active.get('http_status',200)!=200:raise RuntimeError('ci_activation_denied')
            end_reader('fixture_setup')
            payload={**runtime.context(ids),'tokens':request['tokens'],
                'key':request['anon'],'proof':proof,'ids':roles,'window':window,
                'a':by_route['A'],'b':by_route['B'],'initialRevision':active['revision'],
                'scenario':capture()['workflow_actions'],'sourceSha':gate.result['head'] if 'head' in gate.result else os.environ['GITHUB_SHA'],
                'commandCount':0}
            payload['controllerContext']=request.get('controllerContext')
            # Keep the complete outer count in this adapter. The unchanged
            # controller's own receipt counts its 71-action subchain only.
            offset=len(self.commands)
            process=subprocess.Popen(['node',str(self.worker_path('runtime_integral_workflow.mjs'))],stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            worker_evidence.attach(process)
            timer=threading.Timer(125,lambda:worker_evidence.kill(watchdog=True))
            worker_evidence.start_timer(timer,deadline=time.monotonic()+125)
            process.stdin.write(json.dumps(payload)+'\n');process.stdin.flush();payload=None
            for line in process.stdout:
                message=json.loads(line)
                if not isinstance(message,dict) or message.get('op') not in ('complete','sql','workflow_auth','persist'):
                    raise RuntimeError('ci_operation')
                if message['op']=='complete':
                    result=validate_result(message['result'],'workflow')
                    save(gate,'case-workflow-worker-result.json',result)
                    break
                reply={};dispatch_failure=None
                try:
                    if message['op']=='sql':
                        self.action={'kind':'workflow','step':message['scenario_step']}
                        if message['channel'] not in ('writer','reader','workflow'):raise RuntimeError('ci_channel')
                        if message['channel']=='reader' and message['q']=='ROLLBACK' and monitor is not None:
                            terminal=monitor.close()
                            gate.save('integral-workflow-io.json',{'pairs':io_receipts,'terminal':terminal,
                                'scope':'71 workflow actions including scoped reads and evidence writes; no setup/Auth attribution'})
                            monitor=None
                        reply={'rows':query(message['channel'],message['phase'],message['q'],message['args']),
                            'commandCount':len(self.commands)-offset}
                        if message['channel']=='reader' and message['q'].startswith('select current_setting') and monitor is None:
                            from integral_io import QueryIO
                            monitor=QueryIO(raw_query,on_failure=lambda evidence:gate.save('integral-workflow-io-failure.json',evidence));monitor.start()
                            reply['commandCount']=len(self.commands)-offset
                    elif message['op']=='workflow_auth':
                        self.workflow_dispatch.worker_message(message)
                    elif message['op']=='persist':
                        self.events.append({**message['event'],'protocol_count':len(self.commands)})
                        gate.save('integral-pair-%03d-%s.json'%(message['event']['step'],message['event']['phase']),message['event'])
                        if message['event']['step']==45 and message['event']['phase']=='contract':
                            raw_query('reader','preservation_suspend','ROLLBACK')
                            self.preservation(gate,ids,'before_cleanup')
                            raw_query('reader','preservation_resume','BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY')
                            if raw_query('reader','preservation_attest',"select current_setting('transaction_read_only')='on' readonly")[0]['readonly'] is not True:
                                raise RuntimeError('ci_collector_resume')
                        if message['event']['phase']=='pair_validated':
                            evidence=monitor.checkpoint();io_receipts.append(evidence)
                            gate.save('integral-io-pair-%03d.json'%message['event']['step'],evidence)
                            faults=getattr(self,'phase_faults',None)
                            if faults is not None:faults.pair_confirmed(message['event'])
                    else:raise RuntimeError('ci_operation')
                except Exception as error:
                    dispatch_failure=error
                    try:self.abort('workflow_dispatch_failed')
                    except BaseException as secondary:
                        error.add_note('workflow_abort_secondary:'+type(secondary).__name__)
                    reply={'error':'ci_query_failed',
                        'commandCount':len(self.commands)-offset}
                dispatch_reply(process,reply,dispatch_failure)
            worker_evidence.wait()
            worker_evidence.stop_timer(timer)
            if (not worker_evidence.known or worker_evidence.returncode or not result
                    or result.get('status')!='LOCAL_COMPOSED_71_PASS' or result.get('pairs')!=71):
                gate.save('integral-workflow-stop.json',result or {'status':'NO_GO','phase':'child_process'})
                raise RuntimeError('ci_integral_workflow_incomplete')
            if result['deletes']!=123:raise RuntimeError('ci_integral_delete_count')
            start_reader()
            auth_after=query('reader','workflow_auth_after','select '+STATS+' value')[0]['value']
            auth_load=difference(auth_before,auth_after)
            if auth_load['commands']!=360:raise RuntimeError('ci_workflow_auth_protocol')
            gate.save('workflow-auth-protocol.json',{'verified_calls':72,**auth_load})
            gate.save('case-workflow-auth-dispatch.json',self.workflow_dispatch.validated({'verified_calls':72,**auth_load}))
            deleted=fixture.perform(query,gate.save,ctx,'delete_window',[['windows','DELETE',[window]]],
                "delete from fmz6e11_private.windows where id=$1::uuid and status='revoked' and not feature_enabled returning id::text",[window],claims,headers)
            if deleted!=[{'id':window}]:raise RuntimeError('ci_window_delete_unconfirmed')
            restore_before=query('reader','control_restore_before',control_sql)[0]['value']
            if restore_before!=enabled:raise RuntimeError('ci_control_unexpected_drift')
            if query('setup','control_restore',"update fmz6e11_request_private.control set enabled=false,expires_at=null where id and enabled and expires_at=$1::timestamptz returning id",[enabled['request']['expires_at']])!=[{'id':True}]:raise RuntimeError('ci_bridge_restore_count')
            if query('setup','control_restore',"update fmz6e11_private.config set enabled=false,proof_hash=null where id and enabled and proof_hash=$1 returning id",[enabled['config']['proof_hash']])!=[{'id':True}]:raise RuntimeError('ci_control_restore_count')
            restored=query('reader','control_restored',control_sql)[0]['value']
            self.confirm_controls_restored(restored,controls)
            gate.save('integral-control-restore-pair.json',{'before_sha':hashlib.sha256(json.dumps(restore_before,sort_keys=True).encode()).hexdigest(),
                'after_sha':hashlib.sha256(json.dumps(restored,sort_keys=True).encode()).hexdigest(),'expected_updates':2,'actual_updates':2,'original_state_restored':True})
            end_reader('fixture_closeout')
            gate.save('integral-workflow.json',result)
            return {'status':'REAL_AUTH_THROUGH_71_WORKFLOW_PAIRS','pairs':71,'deletes':123,
                'outer_sql_commands_so_far':len(self.commands),'next_step':result['next_step'],'hosted_admitted':False}
        finally:
            from .runtime_recovery import finish
            finish(self,gate,runtime,connections,query,raw_query,process=process,timer=timer,
                enable_attempted=enable_attempted,original=controls,enabled=enabled,
                restored=restored,primary=sys.exc_info()[1],worker_evidence=worker_evidence)
