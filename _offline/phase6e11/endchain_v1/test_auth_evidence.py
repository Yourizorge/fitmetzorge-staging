import copy,hashlib,json,types,unittest
from auth_evidence import AuthEvidence
from complete_register import auth_source

class AuthEvidenceTests(unittest.TestCase):
    def setup(self,extra=False,background=0,ci=False):
        actor='69000000-0000-4000-8000-000000000001';h=hashlib.sha256(actor.encode()).hexdigest()
        events=[dict(table_name='auth.'+table,operation=op,xid='9',key_sha=h if table=='users' else str(i)*64,actor_sha=h)
            for i,(table,op) in enumerate([('users','UPDATE'),('audit_log_entries','INSERT'),('one_time_tokens','INSERT')],1)]
        if extra:events.append({**events[0],'table_name':'auth.identities'})
        before={'reset':'fixed','dealloc':0,'track_utility':'on','statements':[]}
        after={**before,'statements':[{'queryid':'7','calls':11+background,'since':'fixed','temp_written':0,'temp_read':0,'wal_bytes':'18','exec_ms':2}]}
        queue=['',json.dumps([]),json.dumps({'seq':0,'auth_stats':before}),json.dumps({'events':events,'auth_stats':after}),json.dumps(events),'']
        calls=[];saved={}
        def sql(query):calls.append(query);return queue.pop(0)
        def save(name,value):self.assertNotIn(name,saved);saved[name]=copy.deepcopy(value)
        audit=types.SimpleNamespace(arm=lambda *a:'ARM',events=lambda *a:'EVENTS',disarm=lambda *a:'DISARM')
        e=AuthEvidence(run_id=actor,ids={'a_member':actor},audit=audit,contract_type=auth_source.Contract,
            sql=sql,save=save,independent_ci=ci)
        return e,calls,saved,actor
    def test_scoped_write_events_remain_separate_from_final_state(self):
        e,calls,saved,action=self.setup()
        before=e.before('a_member','issue',action)
        value=e.after('a_member','issue',before,{})
        self.assertTrue(value['pair_complete']);self.assertEqual(len(value['events']),3)
        self.assertEqual(calls[-1],'DISARM')
        self.assertEqual(len(saved),4);self.assertTrue(saved['auth-pair-00.json']['contract']['exact_multiset'])
        self.assertFalse(saved['auth-pair-00.json']['independent_ci'])
    def test_extra_write_preserves_after_evidence_and_blocks_followup(self):
        e,calls,saved,action=self.setup(extra=True)
        before=e.before('a_member','issue',action)
        with self.assertRaisesRegex(ValueError,'write_multiset'):e.after('a_member','issue',before,{})
        self.assertIn('auth-after-00.json',saved);self.assertNotIn('DISARM',calls)
        with self.assertRaises(ValueError):e.before('a_member','verify',action)
    def test_changed_before_payload_cannot_replace_server_measurement(self):
        e,calls,saved,action=self.setup();before=e.before('a_member','issue',action)
        before['auth_stats']['reset']='changed'
        with self.assertRaisesRegex(ValueError,'pair_binding'):e.after('a_member','issue',before,{})
        self.assertEqual(len(calls),3)
    def test_background_auth_is_not_silently_subtracted_or_called_collector_load(self):
        e,calls,saved,action=self.setup(background=5);before=e.before('a_member','issue',action)
        with self.assertRaisesRegex(ValueError,'command_bound_mismatch'):e.after('a_member','issue',before,{})
        self.assertEqual(saved['auth-protocol-00.json']['commands'],16)
        self.assertIn('background not separately attributed',saved['auth-protocol-00.json']['scope'])
    def test_independent_observer_is_ci_only_option(self):
        e,calls,saved,action=self.setup(ci=True);before=e.before('a_member','issue',action)
        self.assertTrue(e.after('a_member','issue',before,{})['pair_complete'])
        self.assertTrue(any('fmz_ci_auth_observer' in q for q in calls))

if __name__=='__main__':unittest.main()
