import copy,hashlib,json,pathlib,types,unittest,uuid
from unittest.mock import patch
from complete_register import auth_source
from registered_lifecycle import RegisteredLifecycle
from safety_auth import RESERVE,ROLES,reserve_required,auth_state_before,auth_state_after
from safety_auth_native import allowed_rows,native_suffix,read_sql,revoke_sql,validate_deletes,validate_snapshot

RUN='69000000-0000-4000-8000-000000000099'
IDS={r:'69000000-0000-4000-8000-%012d'%(i+1) for i,r in enumerate(ROLES)}
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
KEYS={r:{k:digest(r+':'+k) for k in ('session','refresh','fresh','amr')} for r in ROLES}


class SafetyProtocolTests(unittest.TestCase):
    def make(self,step=4):
        self.calls=[];self.saved={};self.queue=[];self.charges=[];self.confirmed=[]
        def save(name,value):
            self.assertNotIn(name,self.saved);self.saved[name]=copy.deepcopy(value)
        def sql(text):self.calls.append(text);return self.queue.pop(0)
        audit=types.SimpleNamespace(scope=lambda *a:'audit',arm=lambda *a:'ARM',
            events=lambda *a:'EVENTS',disarm=lambda *a:'DISARM')
        def charge(role,n):self.charges.append((role,n));return len(self.charges)
        c=types.SimpleNamespace(abort=lambda reason:None,safety_label=None,
            authorize_safety_auth=lambda n:self.assertEqual(n,60),
            charge_safety_auth=charge,confirm_safety_auth=self.confirmed.append,
            confirm_auth_zero=lambda **kwargs:None)
        r=RegisteredLifecycle(gate=types.SimpleNamespace(save=save),composition=c,run_id=RUN,ids=IDS,
            guard=types.SimpleNamespace(scope=lambda *a:None),audit=audit,contract_type=auth_source.Contract,
            sql=sql,lock_query=lambda *a:None)
        r.failed=True;r.installed=True;r.receipt={'binding':'guard'};r.metadata_receipt={'binding':'audit'}
        for role,contract in r.evidence.contracts.items():contract.step=step;contract.keys=copy.deepcopy(KEYS[role])
        self.original=copy.deepcopy({k:vars(v) for k,v in r.evidence.contracts.items()})
        return r

    def logout(self,r,role):
        k=KEYS[role];actor=digest(IDS[role])
        keys=[('audit_log_entries','INSERT',digest(role+'audit')),('sessions','DELETE',k['session']),
            ('refresh_tokens','DELETE',k['refresh']),('refresh_tokens','DELETE',k['fresh']),('mfa_amr_claims','DELETE',k['amr'])]
        events=[dict(table_name='auth.'+t,operation=op,key_sha=key,actor_sha=actor,xid='9') for t,op,key in keys]
        before={'reset':'fixed','dealloc':0,'track_utility':'on','statements':[]}
        after={**before,'statements':[dict(queryid='8',calls=10,since='fixed',temp_written=0,temp_read=0,wal_bytes='10',exec_ms=1)]}
        self.queue.extend(['',json.dumps([]),json.dumps({'seq':0,'auth_stats':before}),
            json.dumps({'auth_stats':after}),json.dumps(events),''])
        r.dispatch({'op':'safetyAuthlogout','stage':'before','role':role})
        return r.dispatch({'op':'safetyAuthlogout','stage':'after','role':role,'result':{'key_sha':k['session'],'http_status':204}})

    def test_three_workflow_faults_use_real_logout_contract_without_original_changes(self):
        for fault in ('before_call','after_commit','after_snapshot'):
            with self.subTest(fault=fault):
                r=self.make();start=r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
                self.assertEqual(start['roles'],list(ROLES))
                for role in ROLES:self.assertTrue(self.logout(r,role)['exact_contract'])
                self.assertEqual(len(self.calls),18);self.assertEqual(sum(n for _,n in self.charges),30)
                self.assertEqual(self.confirmed,[1,2,3])
                self.assertEqual(self.original,{k:vars(v) for k,v in r.evidence.contracts.items()})
                self.assertEqual(r.evidence.receipts,[])
                self.assertEqual([c.step for c in r.safety_auth.clone.contracts.values()],[5,5,5])
                self.assertTrue(all(n.startswith('safety-auth-') for n in self.saved))
                with patch('safety_auth.native_suffix',return_value={'status':'NO_GO','revocation_confirmed':True}):
                    self.assertEqual(r.dispatch({'op':'safetyAuthlogout','stage':'finish'})['status'],'NO_GO')
                with self.assertRaises(ValueError):r.dispatch({'op':'safetyAuthlogout','stage':'finish'})

    def test_partial_verify_or_stopped_evidence_never_issues_logout(self):
        for step,stopped,active in ((1,False,{'operation':'verify'}),(2,False,None),(4,True,None)):
            r=self.make(step);r.evidence.stopped=stopped;r.evidence.active=active
            start=r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
            self.assertEqual(start['roles'],[]);self.assertEqual(self.charges,[]);self.assertEqual(self.calls,[])
            with patch('safety_auth.native_suffix',return_value={'status':'NO_GO'}) as fallback:
                r.dispatch({'op':'safetyAuthlogout','stage':'finish'})
                self.assertFalse(fallback.call_args.args[-1])
            self.assertEqual(r.evidence.active,active)

    def test_client_http_failure_can_start_stopped_suffix(self):
        r=self.make(step=1);r.failed=False
        self.assertEqual(r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})['roles'],[])
        self.assertTrue(r.failed)
        with self.assertRaisesRegex(ValueError,'registered_stopped'):r.dispatch({'op':'workflow'})

    def test_meter_missing_fails_closed_before_http(self):
        r=self.make();del r.composition.authorize_safety_auth
        with self.assertRaisesRegex(ValueError,'meter_not_wired'):
            r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
        self.assertEqual(self.calls,[]);self.assertEqual(self.charges,[])

    def test_rejected_start_cannot_reach_any_native_suffix(self):
        r=self.make()
        def deny(count):raise ValueError('reservation_denied')
        r.composition.authorize_safety_auth=deny
        with self.assertRaisesRegex(ValueError,'reservation_denied'):
            r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
        self.assertFalse(r.safety_auth.admitted)
        with patch('safety_auth.native_suffix') as fallback:
            for stage in ('before','after','finish','start'):
                with self.assertRaises(ValueError):
                    r.dispatch({'op':'safetyAuthlogout','stage':stage,'role':ROLES[0],'receipt':r.receipt})
            fallback.assert_not_called()
        self.assertEqual(self.calls,[]);self.assertEqual(self.charges,[])

    def test_wrong_role_replay_and_forged_receipt_rejected(self):
        r=self.make()
        with self.assertRaises(ValueError):r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':{}})
        self.assertEqual(self.calls,[])
        r=self.make();r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
        with self.assertRaises(ValueError):r.dispatch({'op':'safetyAuthlogout','stage':'before','role':'b_member'})
        self.assertEqual(self.charges,[])
        self.logout(r,'a_member')
        with self.assertRaises(ValueError):r.dispatch({'op':'safetyAuthlogout','stage':'before','role':'a_member'})
        with self.assertRaises(ValueError):r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})

    def test_fixed_prefix_reserve_fits_but_not_after_auth_state_should_clear(self):
        self.assertEqual(RESERVE,60)
        folder=pathlib.Path(__file__).parent/'receipts/reserved-ci-39109482869'
        rows=json.loads((folder/'register-prefix-reserves.json').read_text())['prefixes']
        values=[reserve_required(p['used'],p['remaining_normal_cleanup'],p['emergency_sql'],172<=p['after']<2262) for p in rows]
        self.assertEqual(max(values),2349)
        live=[values[i] for i,p in enumerate(rows) if 172<=p['after']<2262]
        self.assertEqual(max(live),2346)
        self.assertGreater(reserve_required(2338,0,11,True),2349)

    def test_auth_escrow_arms_before_issue_and_survives_unconfirmed_zero(self):
        self.assertTrue(auth_state_before(False,'issue'))
        self.assertTrue(auth_state_before(True,'logout'))
        self.assertFalse(auth_state_before(False,'getUser'))
        for confirmed,zero,terminal in ((False,True,True),(True,False,True),(True,True,False)):
            self.assertTrue(auth_state_after(True,confirmed=confirmed,exact_three_zero=zero,mint_terminal=terminal))
        self.assertFalse(auth_state_after(True,confirmed=True,exact_three_zero=True,mint_terminal=True))
        # Do not couple escrow to guard remove-attempt flags or ordinary phase caps.
        self.assertEqual(reserve_required(2261,0,25,True),2346)
        self.assertEqual(reserve_required(2262,0,25,True),2347)

    def test_known_fault_protocol_uses_real_meter_hooks_without_refunding_original(self):
        from metered_composition import MeteredComposition
        for fault in ('before_call','after_commit','after_snapshot'):
            with self.subTest(fault=fault):
                r=self.make();c=MeteredComposition(fault);r.composition=c;c.bind_auth_scope(RUN,IDS)
                for role in ROLES:
                    for operation in ('issue','verify','getUser','refresh'):
                        c.auth_before(role,operation);c.auth_after(operation)
                original=c.meter.charge('route_a',5,action='original_unconfirmed_workflow',kind='managed_auth')
                c.abort('ci_injected_'+fault);used=c.meter.used
                old_sql=r.sql
                def metered_sql(text):
                    rendered='DO $$BEGIN NULL; END$$;' if text in ('ARM','DISARM') else 'SELECT 1'
                    c.before_sql(c.current_phase,rendered)
                    result=old_sql(text);c.after_sql(c.current_phase,rendered);return result
                r.sql=metered_sql
                r.dispatch({'op':'safetyAuthlogout','stage':'start','receipt':r.receipt})
                for role in ROLES:self.logout(r,role)
                def native(*args):
                    n=c.meter.safety('auth_native_fallback',9);c.meter.confirm_safety(n)
                    return dict(run_id=RUN,status='NO_GO',reason='exact_three_account_session_zero',
                        revocation_confirmed=True,mint_terminal=True,commit_confirmed=True,
                        native_commands=9,global_zero_claim=False)
                with patch('safety_auth.native_suffix',side_effect=native):
                    r.dispatch({'op':'safetyAuthlogout','stage':'finish'})
                self.assertEqual(c.meter.used-used,57)
                self.assertIn(original,c.meter.managed_pending)
                self.assertFalse(c.meter.state['auth_maybe_live'])
                self.assertEqual(c.meter.stop_reason,'ci_injected_'+fault)
                self.assertEqual(self.original,{k:vars(v) for k,v in r.evidence.contracts.items()})


class NativeSuffixTests(unittest.TestCase):
    def make(self,fail=None):
        self.calls=[];self.saved={};self.snapshots=[]
        audit=types.SimpleNamespace(scope=lambda *a:'fmz6e11_am_'+RUN.replace('-',''),
            inspect=lambda *a:"select '{}'::text",validate=lambda *a:None)
        self.r=types.SimpleNamespace(run_id=RUN,ids=IDS,expiry='2099-01-01T00:00:00+00:00',audit=audit)
        rows=[dict(zip(('t','k','a','s'),x)) for x in sorted(allowed_rows(IDS,KEYS))]
        def sample(reader,begin=0,mutation=0,commit=0):
            statements=[dict(queryid=q,calls=n,since='fixed',temp_read=0,temp_written=0,wal='0',exec_ms=n)
                for q,n in (('9',reader),('10',begin),('11',mutation),('12',commit)) if n]
            return dict(track='top',track_utility='on',reset='fixed',dealloc=0,statements=statements,
                background={'reset':'fixed','temp_bytes':0},health={'io_wait':0,'long_active':0})
        initial=dict(lock=True,live=True,statement_timeout='5s',lock_timeout='1s',audit={},rows=rows,events=[],io=sample(0))
        before={**copy.deepcopy(initial),'io':sample(1,1)}
        actions={digest(IDS[r]):str(uuid.uuid5(uuid.UUID(RUN),'safety-auth-native:'+r)) for r in ROLES}
        events=[dict(seq=i+1,action_id=actions[x['a']],table_name=x['t'],operation='DELETE',
            key_sha=x['k'],actor_sha=x['a'],session_sha=x['s'],xid='5',backend=9) for i,x in enumerate(rows)]
        after={**copy.deepcopy(initial),'rows':[],'events':events,'io':sample(2,1,1)}
        witness={**copy.deepcopy(after),'io':sample(3,1,1,1)}
        self.snapshots=[initial,before,after,witness]
        self.initial=initial;self.after=after;self.actions=set(actions.values())
        def sql(text):
            self.calls.append(text)
            if fail and text.startswith(fail):raise RuntimeError('lost_sql_response')
            if text.startswith('EXPLAIN'):return json.dumps([{'Query Identifier':9,'Plan':{'Actual Rows':1},'Execution Time':0.1}])
            if text.startswith('select jsonb_build_object'):return json.dumps(self.snapshots.pop(0))
            return ''
        self.r.sql=sql
        def save(name,value):
            self.assertNotIn(name,self.saved);self.saved[name]=copy.deepcopy(value)
        return save

    def test_exact_native_delete_and_independent_commit_witness_cost_nine(self):
        save=self.make();out=native_suffix(self.r,save,KEYS,True)
        self.assertEqual(out['status'],'NO_GO');self.assertTrue(out['revocation_confirmed'])
        self.assertEqual(out['native_commands'],9);self.assertFalse(out['global_zero_claim'])
        mutation=next(x for x in self.calls if x.startswith('DO '))
        self.assertEqual(mutation.count('DELETE FROM auth.sessions'),3)
        for forbidden in ('DELETE FROM auth.users','DELETE FROM auth.refresh_tokens','DROP ','workspaces','windows'):
            self.assertNotIn(forbidden,mutation)

    def test_unknown_verify_observes_without_delete_even_if_current_zero(self):
        save=self.make();self.snapshots[0]['rows']=[]
        out=native_suffix(self.r,save,{},False)
        self.assertEqual(out['reason'],'incomplete_auth_mint_outcome_unknown')
        self.assertFalse(out['revocation_confirmed']);self.assertEqual(len(self.calls),2)
        self.assertFalse(any(x.startswith(('BEGIN','DO ')) for x in self.calls))

    def test_lost_native_commit_is_never_confirmed_or_retried(self):
        save=self.make(fail='COMMIT');out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertEqual(self.calls.count('COMMIT'),1)
        self.assertTrue(out['commit_attempted']);self.assertFalse(out['commit_confirmed'])
        self.assertEqual(self.calls.count('ROLLBACK'),1);self.assertLessEqual(out['native_commands'],12)

    def test_lost_begin_rolls_back_once(self):
        save=self.make(fail='BEGIN');out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertEqual(self.calls.count('ROLLBACK'),1)

    def test_foreign_or_duplicate_rows_block_before_delete(self):
        for duplicate in (False,True):
            save=self.make()
            if duplicate:self.snapshots[0]['rows'][0]=copy.deepcopy(self.snapshots[0]['rows'][1])
            else:self.snapshots[0]['rows'][0]['k']='f'*64
            out=native_suffix(self.r,save,KEYS,True)
            self.assertFalse(out['revocation_confirmed']);self.assertFalse(any(x.startswith('DO ') for x in self.calls))

    def test_observer_lock_not_terminal_http_proof(self):
        save=self.make();self.snapshots[0]['lock']=False
        out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertEqual(len(self.calls),2)

    def test_original_event_rewrite_or_wrong_delete_multiset_rejected(self):
        self.make();before=copy.deepcopy(self.initial);after=copy.deepcopy(self.after)
        before['events']=[{'action_id':'old','seq':0}]
        with self.assertRaisesRegex(ValueError,'original_events_changed'):validate_deletes(before,after,self.actions)
        after=copy.deepcopy(self.after);after['events'][0]['operation']='INSERT'
        with self.assertRaisesRegex(ValueError,'delete_multiset'):validate_deletes(self.initial,after,self.actions)

    def test_first_utility_ambiguity_rolls_back_and_never_deletes(self):
        save=self.make();extra=dict(queryid='99',calls=1,since='fixed',temp_read=0,temp_written=0,wal='0',exec_ms=1)
        self.snapshots[1]['io']['statements'].append(extra)
        out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertEqual(self.calls.count('ROLLBACK'),1)
        self.assertFalse(any(x.startswith('DO ') for x in self.calls))

    def test_renderers_are_single_pg17_statements(self):
        self.make()
        from sql_protocol import statements
        sql,_=revoke_sql(self.r,KEYS,self.initial)
        self.assertEqual(len(statements(sql)),1);self.assertEqual(len(statements(read_sql(self.r))),1)

    def test_metadata_reader_wal_blocks_but_exact_do_wal_is_attributed(self):
        save=self.make();self.snapshots[1]['io']['statements'][0]['wal']='1'
        out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertFalse(any(q.startswith('DO ') for q in self.calls))
        save=self.make()
        for sample in self.snapshots[2:]:
            next(x for x in sample['io']['statements'] if x['queryid']=='11')['wal']='512'
        out=native_suffix(self.r,save,KEYS,True)
        self.assertTrue(out['revocation_confirmed'])
        self.assertEqual(self.saved['native-committed.json']['profiles'][1]['profile']['own_wal_bytes'],512)

    def test_begin_and_commit_are_not_authorized_writers(self):
        for index,qid in ((1,'10'),(3,'12')):
            save=self.make();next(x for x in self.snapshots[index]['io']['statements'] if x['queryid']==qid)['wal']='1'
            self.assertFalse(native_suffix(self.r,save,KEYS,True)['revocation_confirmed'])

    def test_raw_verbose_plan_expressions_never_enter_receipts(self):
        save=self.make();sql=self.r.sql
        def with_plan_text(text):
            answer=sql(text)
            if text.startswith('EXPLAIN'):
                plan=json.loads(answer);plan[0]['Plan']['Output']=['RAW_SQL_SENTINEL secret_token_literal']
                return json.dumps(plan)
            return answer
        self.r.sql=with_plan_text
        self.assertTrue(native_suffix(self.r,save,KEYS,True)['revocation_confirmed'])
        exported=json.dumps(self.saved)
        for text in ('RAW_SQL_SENTINEL','secret_token_literal','Output','SELECT ','select jsonb_build_object'):
            self.assertNotIn(text,exported)

    def test_closing_read_wal_never_confirms_revocation(self):
        save=self.make();sql=self.r.sql
        def with_wal(text):
            answer=sql(text)
            if text.startswith('EXPLAIN (ANALYZE'):
                plan=json.loads(answer);plan[0]['Plan']['WAL Bytes']=1
                return json.dumps(plan)
            return answer
        self.r.sql=with_wal
        out=native_suffix(self.r,save,KEYS,True)
        self.assertFalse(out['revocation_confirmed']);self.assertTrue(out['commit_confirmed'])
        self.assertNotIn('native-committed.json',self.saved)

    def test_every_native_attempt_uses_stopped_runtime_meter_even_lost_response(self):
        from metered_composition import MeteredComposition
        for failure,expected in ((None,9),('BEGIN',4),('COMMIT',8)):
            with self.subTest(failure=failure):
                save=self.make(fail=failure);c=MeteredComposition();c.bind_auth_scope(RUN,IDS)
                for role in ROLES:
                    for operation in ('issue','verify','getUser','refresh'):
                        c.auth_before(role,operation);c.auth_after(operation)
                c.abort('original_fault');c.authorize_safety_auth(60)
                c.safety_label='auth_native_fallback';c.current_phase='safety_auth_finish'
                sql=self.r.sql;used=c.meter.used
                def metered(text):
                    c.before_sql(c.current_phase,text)
                    result=sql(text);c.after_sql(c.current_phase,text);return result
                self.r.sql=metered
                out=native_suffix(self.r,save,KEYS,True)
                self.assertEqual(out['native_commands'],expected)
                self.assertEqual(c.meter.used-used,expected)
                self.assertEqual(c.meter.safety_spent['auth_native_fallback'],expected)
                self.assertEqual(c.meter.stop_reason,'original_fault')
                if failure:
                    self.assertTrue(c.meter.safety_pending)
                    with self.assertRaises(ValueError):c.confirm_auth_zero(safety_receipt=out)
                    self.assertTrue(c.meter.state['auth_maybe_live'])
                else:
                    c.confirm_auth_zero(safety_receipt=out)
                    self.assertFalse(c.meter.state['auth_maybe_live'])


if __name__=='__main__':unittest.main()
