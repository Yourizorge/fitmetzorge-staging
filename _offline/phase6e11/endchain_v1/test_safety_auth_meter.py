import collections,copy,itertools,json,pathlib,types,unittest
from complete_register import AUTH_CALLS,PHASES,bind_auth_states,reserve_prefixes,safety_path
from integral_failures import auth_zero_projection,check_auth_zero
from metered_composition import MeteredComposition,capacity
from runtime_budget import BudgetStop,RuntimeBudget
from closure import RUN_ID,PURPOSE
from safety_auth_budget import ROLES,labels

IDS={role:'69000000-0000-4000-8000-%012d'%(i+1) for i,role in enumerate(ROLES)}


class SafetyMeterTests(unittest.TestCase):
    def meter(self):return RuntimeBudget(capacity(),run_id=RUN_ID,purpose=PURPOSE)

    def composition(self,terminal=True):
        c=MeteredComposition();c.bind_auth_scope(RUN_ID,IDS)
        for role in ROLES:
            for op in ('issue','verify','getUser','refresh') if terminal else ('issue',):
                c.auth_before(role,op);c.auth_after(op)
        return c

    def proof(self):
        return dict(run_id=RUN_ID,status='NO_GO',reason='exact_three_account_session_zero',
            revocation_confirmed=True,mint_terminal=True,commit_confirmed=True,
            native_commands=9,global_zero_claim=False)

    def test_first_issue_arms_reserve_before_unconfirmed_http(self):
        c=MeteredComposition();c.bind_auth_scope(RUN_ID,IDS)
        c.auth_before(ROLES[0],'issue')
        self.assertTrue(c.meter.state['auth_maybe_live'])
        self.assertEqual(c.meter.used,11)
        c.abort('lost_issue_response');c.authorize_safety_auth(60)
        self.assertEqual(c.meter.used,11)
        self.assertEqual(sum(x['sql'] for x in safety_path(**c.meter.state)),69)
        with self.assertRaisesRegex(ValueError,'zero_unconfirmed'):c.confirm_auth_zero(safety_receipt=self.proof())
        self.assertTrue(c.meter.state['auth_maybe_live'])

    def test_exact_sixty_labels_cap_and_kind_with_no_double_charge(self):
        c=self.composition();c.abort('original_fault');used=c.meter.used
        c.authorize_safety_auth(60);self.assertEqual(c.meter.used,used)
        with self.assertRaisesRegex(ValueError,'state'):c.authorize_safety_auth(60)
        for row in labels():
            with self.assertRaises(BudgetStop):c.meter.safety(row['action'],row['sql'],kind='invalid')
            n=c.meter.safety(row['action'],row['sql'],kind=row['kind']);c.meter.confirm_safety(n)
            with self.assertRaises(BudgetStop):c.meter.safety(row['action'],1,kind=row['kind'])
        self.assertEqual(c.meter.used-used,60)
        self.assertEqual(c.meter.stop_reason,'original_fault')

    def test_own_managed_ticket_survives_intervening_native_and_not_original(self):
        c=self.composition();old=c.meter.charge('route_a',5,action='original',kind='managed_auth')
        c.abort('lost_original');c.authorize_safety_auth(60)
        managed=c.charge_safety_auth(ROLES[0],10)
        native=c.meter.safety('auth_logout_'+ROLES[0],6);c.meter.confirm_safety(native)
        c.confirm_safety_auth(managed)
        self.assertIn(old,c.meter.managed_pending)
        self.assertNotIn(managed,c.meter.safety_pending)
        with self.assertRaises(BudgetStop):c.confirm_safety_auth(managed)
        with self.assertRaises(ValueError):c.confirm_safety_auth(old)
        self.assertFalse(c.meter.receipt()['complete'])

    def test_safety_count_drift_is_charged_no_refund_or_reason_overwrite(self):
        c=self.composition();c.abort('original');c.authorize_safety_auth(60)
        n=c.charge_safety_auth(ROLES[0],10);used=c.meter.used
        with self.assertRaises(BudgetStop):c.meter.confirm_safety(n,actual=11)
        self.assertEqual(c.meter.used,used+1);self.assertEqual(c.meter.stop_reason,'original')
        self.assertIn(n,c.meter.safety_pending)

    def test_precharge_cannot_release_auth_even_for_absence(self):
        m=self.meter();n=m.charge('auth',11,action='issue',kind='managed_auth',state_after={'auth_maybe_live':True})
        m.confirm(n)
        n=m.charge('final',1,action='gates_after_cleanup_absence')
        m.confirm(n);self.assertTrue(m.state['auth_maybe_live'])
        with self.assertRaisesRegex(BudgetStop,'requires_known_zero'):
            m.charge('final',1,action='forged_release',state_after={'auth_maybe_live':False})
        self.assertTrue(m.state['auth_maybe_live'])

    def test_normal_terminal_operations_do_not_release_without_validated_absence_hook(self):
        c=self.composition()
        for role in ROLES:
            for op in ('logout','revoked_denial'):c.auth_before(role,op);c.auth_after(op)
        self.assertTrue(c.meter.state['auth_maybe_live'])
        with self.assertRaisesRegex(ValueError,'metadata_required'):c.confirm_auth_zero()
        from auth_zero import validate
        measured=dict(manifest_sha256=c.auth_zero_scope['sha256'],manifest_count=3,registered_count=3,
            scope_count=3,extra_registered_count=0,sessions=0,refresh_tokens=0)
        c.action={'kind':'auth','role':ROLES[-1],'operation':'revoked_denial'}
        c.before_sql('after','SELECT 1');c.after_sql('after','SELECT 1')
        used=c.meter.used;c.confirm_auth_zero(metadata=validate(measured,c.auth_zero_scope))
        self.assertEqual(c.meter.used,used);self.assertFalse(c.meter.state['auth_maybe_live'])
        self.assertEqual(c.meter.state_confirmations[-1]['sql'],0)

    def test_incomplete_or_lost_commit_proof_never_releases(self):
        c=self.composition();c.abort('lost_logout');c.authorize_safety_auth(60)
        for key,value in [('commit_confirmed',False),('revocation_confirmed',False),('mint_terminal',False),
                ('run_id',IDS[ROLES[0]]),('status','PASS'),('global_zero_claim',True),('native_commands',13)]:
            with self.subTest(key=key):
                proof=self.proof();proof[key]=value
                with self.assertRaisesRegex(ValueError,'zero_unconfirmed'):c.confirm_auth_zero(safety_receipt=proof)
                self.assertTrue(c.meter.state['auth_maybe_live'])
        c.confirm_auth_zero(safety_receipt=self.proof())
        self.assertFalse(c.meter.state['auth_maybe_live']);self.assertTrue(c.meter.stopped)

    def test_deadline_or_capacity_does_not_start_safety_protocol(self):
        for late in (False,True):
            c=self.composition();c.abort('fault')
            if late:c.meter.clock=lambda:c.meter.started+600
            else:c.meter.used=c.meter.limit-68
            with self.assertRaisesRegex(ValueError,'deadline|capacity'):c.authorize_safety_auth(60)
            self.assertFalse(c.safety_auth_started)

    def test_prefix_keeps_sixty_for_lost_absence_response_without_mutating_rows(self):
        rows=[dict(phase='auth',sql=11,action='gotrue_a_member_issue'),
              dict(phase='cleanup',sql=1,action='after',auth_zero_validated=True),
              dict(phase='closure',sql=1,action='closure')]
        original=copy.deepcopy(rows);bound=bind_auth_states(rows);prefix=reserve_prefixes(bound)
        self.assertEqual(rows,original)
        self.assertTrue(prefix[1]['auth_maybe_live'])
        self.assertFalse(prefix[2]['auth_maybe_live']);self.assertTrue(prefix[2]['unconfirmed_auth_maybe_live'])
        self.assertEqual(prefix[2]['reserve'],69);self.assertEqual(prefix[3]['reserve'],9)
        rows[0]['state_after']={'auth_maybe_live':False}
        with self.assertRaisesRegex(ValueError,'before_confirmation'):reserve_prefixes(rows)

    def current_counterfactual(self):
        """Model current ordering in memory; historical receipts prove none of it."""
        folder=pathlib.Path(__file__).parent/'receipts/reserved-ci-39109482869'
        historical=[]
        for phase in PHASES:
            value=json.loads((folder/('register-phase-'+phase+'.json')).read_text())
            historical.extend(value['rows'])
        historical=sorted(historical,key=lambda r:r['id']);original=copy.deepcopy(historical)
        old_limits={**capacity()['phase_budgets'],'migration':92,'final':133}
        self.assertEqual(dict(collections.Counter(r['phase'] for r in historical)),old_limits)
        self.assertTrue(all(r['sql']==1 for r in historical))
        old_cli=[r for r in historical if r['action']=='empty_cli_dry_run']
        self.assertEqual(len(old_cli),72)
        self.assertEqual(sum(bool(r.get('reservation_only')) for r in old_cli),64)
        stream=[copy.deepcopy(r) for r in historical if r['phase']=='final' and
            (r['action'].startswith('stream_after_cleanup_') or r['action']=='bounded_additional_fetch_and_io')]
        self.assertEqual(len(stream),41)
        self.assertEqual(sum(r['action'].startswith('gates_after_cleanup_') for r in historical),20)
        removed=[copy.deepcopy(r) for r in historical if r['action']=='remove']
        self.assertEqual(len(removed),10)
        for offset,name in ((0,'observer'),(5,'guard')):
            removed[offset]['removal_precharged']={'object':name,'commands':5}
        closing=[copy.deepcopy(r) for r in historical if r['phase']=='closure']
        self.assertEqual(len(closing),1)
        rows=[copy.deepcopy(r) for r in historical if r['phase'] not in ('final','closure') and r['action']!='remove']

        from cli_envelope import CHARGE,DRY_CAP,OBSERVERS
        self.assertEqual((CHARGE,DRY_CAP,OBSERVERS),(72,28,8))
        def dry(slot,phase,action):
            return [dict(phase=phase,action=action,sql=1,slot=slot,
                ordinal_in_action=i,reservation_only=4<=i<4+DRY_CAP) for i in range(DRY_CAP+OBSERVERS)]
        quota=[r for r in rows if r['action']=='candidate_quota_migration_aware_cli']
        self.assertEqual(len(quota),CHARGE)
        for row in quota:row['slot']='quota'
        early=dry('pre_auth','migration','pre_auth_empty_cli_dry_run')
        at=next(i for i,r in enumerate(rows) if r['action']=='guard_install')
        self.assertEqual(rows[at-1]['action'],'gates_after_migration_rollback')
        rows[at:at]=early

        # Use the current production final-metadata sequence with the existing
        # in-memory IO fixture. No database, CLI or historical zero proof runs.
        from test_final_gates import FinalGatesTests
        fixture=FinalGatesTests();fixture.setUp()
        pre=fixture.exercise('pre');post=fixture.exercise('post')
        self.assertEqual((len(pre),len(post)),(11,9))
        def metadata(phases):
            return [dict(phase='final',action=p,sql=1) for p in phases]
        final_pre=metadata(pre);final_post=metadata(post)
        for row in final_post:
            if row['action']=='gates_final_post_metadata':row['temporary_absence_validated']=True
        final_post[-1]['final_cleanup_validated']=True
        final_cli=dry('final','final','empty_cli_dry_run')
        rows+=stream+final_pre+final_cli+removed+final_post+closing

        # This is the assumed successful *new* terminal metadata response, not
        # an assertion that the immutable old CI performed the new zero query.
        final_after=[r for r in rows if r['action']=='after' and r.get('action_binding')==
            {'kind':'auth','role':'b_member','operation':'revoked_denial'}][-1]
        final_after['auth_zero_validated']=True
        restored=next(row for row in rows if row['action']=='control_restored')
        self.assertEqual(restored.pop('state_after'),{'controls':False})
        restored['controls_restored_validated']=True
        for i,row in enumerate(rows):
            row['historical_id']=row.pop('id',None);row['id']='counterfactual_%05d'%(i+1)
            row['counterfactual_only']=True
        self.assertEqual(historical,original)
        self.assertEqual(dict(collections.Counter(r['phase'] for r in rows)),capacity()['phase_budgets'])
        self.assertEqual(sum(r['sql'] for r in rows),2338)
        self.assertEqual(collections.Counter(r.get('slot') for r in rows if 'slot' in r),
            {'quota':72,'pre_auth':36,'final':36})
        self.assertEqual(sum(r['sql'] for r in rows if r.get('managed')),594)
        return rows

    def replay_counterfactual(self,rows):
        rows=bind_auth_states(rows);m=self.meter();prepaid=set();tickets=[];peak=0;anchors={}
        workflow=[r for r in rows if r['action']=='gotrue_fixture_identity' or r['action'].startswith('gotrue_workflow_identity_')]
        def observe(action):
            nonlocal peak
            required=m.used+m._reserve(m.phases,m.state);peak=max(peak,required)
            self.assertLessEqual(required,2349,action)
            if action in ('after','gates_final_pre_rollback','empty_cli_dry_run','remove',
                    'gates_final_post_metadata','final_closure'):
                anchors[action]={'used':m.used,'required':required,'auth_maybe_live':m.state['auth_maybe_live']}
        index=0
        while index<len(rows):
            row=rows[index]
            if row['action']=='gotrue_fixture_identity' and not prepaid:
                for action,items in itertools.groupby(workflow,key=lambda r:r['action']):
                    group=list(items);self.assertEqual(len(group),5)
                    tickets.append(m.charge(group[0]['phase'],5,action=action,kind='managed_auth'))
                    prepaid.update(r['id'] for r in group);observe(action)
                self.assertEqual(len(m.managed_pending),72)
            if row['id'] in prepaid:index+=1;continue
            if row['action'].startswith('gotrue_') and row['action'].endswith('_logout') and tickets:
                for ticket in tickets:m.confirm(ticket,actual=5)
                tickets=[]
            count=1
            if row.get('managed') or 'slot' in row:
                while index+count<len(rows) and rows[index+count]['action']==row['action']:count+=1
            if row.get('removal_precharged'):count=5
            self.assertFalse(any(r.get('confirmed_state_after') for r in rows[index:index+count-1]))
            n=m.charge(row['phase'],count,action=row['action'],
                kind='managed_auth' if row.get('managed') else 'cli_reserved' if 'slot' in row else 'native',
                mutation=True,state_after=row.get('state_after'))
            observe(row['action']);m.confirm(n)
            released=rows[index+count-1].get('confirmed_state_after',{})
            if released.get('auth_maybe_live') is False:m.confirm_auth_zero()
            if released.get('guard') is False:m.confirm_temporary_absence()
            if released.get('controls') is False:m.confirm_controls_restored()
            index+=count
        self.assertEqual(len(prepaid),360);self.assertEqual(m.used,2338)
        self.assertFalse(tickets);self.assertEqual(dict(m.phases),capacity()['phase_budgets'])
        self.assertEqual(peak,2349);self.assertTrue(m.close()['complete'])
        return {'normal':m.used,'worst':peak,'workflow_prepaid':len(prepaid),'anchors':anchors}

    def test_current_counterfactual_includes_upfront_workflow_escrow(self):
        rows=self.current_counterfactual();prefixes=reserve_prefixes(bind_auth_states(rows))
        self.assertEqual(len(prefixes),2339)
        self.assertEqual(max(p['required_total'] for p in prefixes),2349)
        self.assertTrue(all(p['within_approved_limit'] for p in prefixes))
        result=self.replay_counterfactual(rows)
        self.assertEqual(result['anchors']['after'],{'used':2228,'required':2338,'auth_maybe_live':True})
        self.assertEqual(result['anchors']['gates_final_pre_rollback']['used'],2282)
        self.assertEqual(result['anchors']['empty_cli_dry_run']['used'],2318)
        self.assertEqual(result['anchors']['gates_final_post_metadata']['required'],2349)

    def test_counterfactual_cannot_release_auth_late_or_omit_the_zero_proof(self):
        for late in (False,True):
            rows=self.current_counterfactual()
            for row in rows:row.pop('auth_zero_validated',None)
            if late:
                next(r for r in rows if r['action']=='gates_final_pre_rollback')['auth_zero_validated']=True
            prefixes=reserve_prefixes(bind_auth_states(rows))
            self.assertGreater(max(p['required_total'] for p in prefixes),2349)
            if late:
                at=next(i+1 for i,r in enumerate(rows) if r['action']=='gates_final_pre_rollback')
                self.assertEqual(prefixes[at]['required_total'],2367)
            with self.assertRaises(BudgetStop):self.replay_counterfactual(rows)

    def test_five_command_remove_is_prepaid_once_and_not_replayed_after_stop(self):
        sql='BEGIN; SELECT 1; SELECT 2; SELECT 3; COMMIT'
        for name in ('guard','observer'):
            for stopped in (False,True):
                c=MeteredComposition();c.meter.state[name]=True
                if stopped:c.abort('original')
                c.safety_label=name+'_exact_remove';used=c.meter.used
                c.before_sql('remove',sql)
                self.assertEqual(c.meter.used-used,5)
                self.assertTrue(c.meter.state[name+'_remove_attempted']);self.assertTrue(c.meter.state[name])
                c.abort('lost_remove')
                self.assertNotIn(name+'_exact_remove',[r['action'] for r in safety_path(**c.meter.state)])
                with self.assertRaises(ValueError):c.before_sql('remove',sql)
                self.assertEqual(c.meter.used-used,5)

    def test_post_failure_before_and_after_each_command_releases_only_validated_metadata(self):
        for boundary in range(19):
            c=MeteredComposition();c.meter.state.update(guard=True,observer=True,
                guard_remove_attempted=True,observer_remove_attempted=True)
            released=False;tick=0
            for index in range(9):
                if tick==boundary:break
                phase='gates_final_post_metadata' if index==5 else 'gates_final_post_command'
                c.before_sql(phase,'SELECT 1');tick+=1
                if tick==boundary:break
                c.after_sql(phase,'SELECT 1');tick+=1
                if index==5:c.temporary_absence_confirmed();released=True
            self.assertEqual(c.meter.state['guard'],not released)
            self.assertEqual(c.meter.state['observer'],not released)
            self.assertFalse(c.meter.state['auth_maybe_live'])
            self.assertFalse(getattr(c,'final_post_complete',False))
            c.abort('post_failure')
            self.assertEqual(sum(r['sql'] for r in safety_path(**c.meter.state)),9 if released else 13)

    def test_removal_prefix_preserves_prepaid_tail_and_lost_post_reserve(self):
        rows=[dict(phase='guard',sql=1,action='install',state_after={'guard':True,'observer':True}),
            dict(phase='cleanup',sql=1,action='remove',removal_precharged={'object':'guard','commands':5})]
        rows += [dict(phase='cleanup',sql=1,action='remove') for _ in range(4)]
        rows += [dict(phase='final',sql=1,action='gates_final_post_metadata',temporary_absence_validated=True)]
        p=reserve_prefixes(bind_auth_states(rows))
        self.assertEqual(p[2]['prepaid_safety_tail'],4)
        self.assertFalse(any(r['action']=='guard_exact_remove' for r in p[2]['path']))
        self.assertEqual(p[-1]['emergency_sql'],9)
        self.assertEqual(p[-1]['unconfirmed_emergency_sql'],18)


class FailureZeroTests(unittest.TestCase):
    def test_three_retained_accounts_and_zero_sessions_refresh_required_for_each_fault(self):
        for fault in ('before_call','after_commit','after_snapshot'):
            with self.subTest(fault=fault):
                c=types.SimpleNamespace(safety_auth_result={'status':'NO_GO','revocation_confirmed':True},
                    auth_zero_proof={'source':'validated_safety_native'},meter=types.SimpleNamespace(state={'auth_maybe_live':False}))
                row={'auth_accounts':3,'auth_sessions':0,'auth_refresh_tokens':0};check_auth_zero(row,c)
                for key in row:
                    bad=dict(row);bad[key]+=1
                    with self.assertRaisesRegex(RuntimeError,'three_auth_not_zero'):check_auth_zero(bad,c)
                c.meter.state['auth_maybe_live']=True
                with self.assertRaisesRegex(RuntimeError,'zero_unconfirmed'):check_auth_zero(row,c)

    def test_projection_extends_existing_query_without_command_or_account_deletion(self):
        from sql_protocol import statements
        sql='select 1 existing_diagnostic'+auth_zero_projection(IDS)
        self.assertEqual(len(statements(sql)),1)
        self.assertNotIn('DELETE',sql)
        self.assertEqual(sql.count('count(*)'),3)
        for actor in IDS.values():self.assertEqual(sql.count(actor),3)
        with self.assertRaises(ValueError):auth_zero_projection({**IDS,ROLES[0]:"' untrusted"})


if __name__=='__main__':unittest.main()
