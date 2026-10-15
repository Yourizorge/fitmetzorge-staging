import copy,unittest
import registration_scope as s

ID=lambda n:'79000000-0000-4000-8000-'+str(n).zfill(12)
class Tests(unittest.TestCase):
    def setUp(self):
        self.ids=dict(zip(sorted(s.ROLES),map(ID,range(1,4))))
        self.kw=dict(issued_at='2026-10-15T10:00:00Z',expires_at='2026-10-15T10:10:00Z',
            now='2026-10-15T10:01:00Z',sources={'synthetic.py':'a'*64},
            register=[{'id':p,'phase':p,'commands':2,'retry':False,'mutation':False,
                       'template_sha256':'b'*64,'safety':dict.fromkeys(s.REQUIRED_CLOSURE,1)} for p in sorted(s.REQUIRED_PHASES)])
    def scope(self):return s.compile_scope(self.ids,{'A':ID(4),'B':ID(5)},**self.kw)
    def test_compile_never_activates(self):
        v=self.scope();self.assertFalse(v['hosted_authorized']);self.assertFalse(any(v['flags'].values()))
        self.assertEqual(v['required_maximum'],31);self.assertFalse(v['trainer_write_access'])
    def test_real_expiry_not_static_placeholder(self):
        for now in ('2026-10-15T10:10:00Z','2026-10-15T09:59:59Z'):
            self.kw['now']=now
            with self.assertRaisesRegex(ValueError,'release_expired'):self.scope()
    def test_missing_phase_or_safety_rejected(self):
        old=copy.deepcopy(self.kw);self.kw['register'].pop()
        with self.assertRaisesRegex(ValueError,'incomplete_register'):self.scope()
        self.kw=old;self.kw['register'][0]['safety'].pop('audit_delete')
        with self.assertRaisesRegex(ValueError,'missing_closure'):self.scope()
    def test_write_requires_complete_pair_and_writeset(self):
        self.kw['register'][0]['mutation']=True
        with self.assertRaisesRegex(ValueError,'write_evidence'):self.scope()
    def test_duplicate_identity_or_request_denied(self):
        self.ids['a_member']=self.ids['a_trainer']
        with self.assertRaisesRegex(ValueError,'identities'):self.scope()
    def test_no_local_pass_or_old_budget_as_admission(self):
        v=self.scope()
        with self.assertRaisesRegex(ValueError,'hosted11_complete'):
            s.admit(v,{'approved_sql_limit':4135},now=self.kw['now'],actual_sources=self.kw['sources'],registered_identities=self.ids)
    def test_each_gate_and_both_bindings_required(self):
        v=self.scope();proof=dict.fromkeys(('hosted11_complete','physical_owner_review','selected12_decision','transport_ci_complete',
            'migration_identity','rights_safe','data_preserved','full_register_ci_complete'),True)
        proof.update(approved_sql_limit=31,source_bundle_sha256=v['source_bundle_sha256'],register_sha256=v['register_sha256'])
        call=lambda p:s.admit(v,p,now=self.kw['now'],actual_sources=self.kw['sources'],registered_identities=self.ids)
        self.assertFalse(call(proof)['automatic_activation'])
        for name in proof:
            bad=copy.deepcopy(proof);bad[name]=False
            with self.assertRaises(ValueError):call(bad)
    def test_changed_source_denied(self):
        with self.assertRaisesRegex(ValueError,'source_changed'):
            s.admit(self.scope(),{},now=self.kw['now'],actual_sources={'synthetic.py':'c'*64},registered_identities=self.ids)

if __name__=='__main__':unittest.main()
