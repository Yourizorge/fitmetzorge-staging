import copy
import json
import pathlib
import tempfile
import unittest
from registry import build, contracts, validate, ROOT
from proof_gate import EvidenceGate, Stop, canary_decision, query_plan, REQUIRED_GATES

class Coverage(unittest.TestCase):
    def setUp(self):
        self.folder = pathlib.Path(tempfile.mkdtemp(prefix='fmz-coverage-offline-'))
        self.g = EvidenceGate(self.folder / 'proof')
        self.route = contracts()[0]
        self.before = dict(actor_sha256='a'*64, request_sha256='b'*64, scope_sha256='c'*64,
            snapshot_sha256='d'*64, table_names=sorted({x['table'] for x in self.route['effects']}))
        self.receipt = dict(actor_sha256='a'*64,request_sha256='b'*64,scope_sha256='c'*64,
                            transaction_sha256='e'*64,outcome='committed')

    def start(self):
        self.g.before(self.route['route_id'], self.before)
        self.g.advance('action_started')
        self.g.advance('action_confirmed', self.receipt)

    def test_registry_matches_sources(self):
        r=json.loads((pathlib.Path(__file__).parent/'register.json').read_text())
        self.assertTrue(validate(r)['static_contract_pass'])
        self.assertFalse(validate(r)['hosted_coverage_pass'])

    def test_observed_dependencies_never_claim_complete_closure(self):
        r=build()
        self.assertTrue(r['dependency_evidence']['foreign_keys'])
        self.assertIn('public.touch_updated_at',r['dependency_evidence']['unresolved_body_binding'])
        self.assertTrue(all(not x['complete_transitive_write_closure_proven'] for x in r['routes']))

    def test_dependency_evidence_is_bound(self):
        r=build();r['dependency_evidence']['foreign_keys'].pop()
        with self.assertRaisesRegex(ValueError,'dependency_evidence'):validate(r)

    def test_removed_route(self):
        r=build();r['routes'].pop()
        with self.assertRaisesRegex(ValueError,'unregistered'):validate(r)

    def test_route_without_pair(self):
        r=build();r['routes'][0]['measurement_required']=False
        with self.assertRaisesRegex(ValueError,'measurement'):validate(r)

    def test_new_mutating_source(self):
        r=build();r['sources']['_offline/phase6e11/new_writer.py']='a'*64
        with self.assertRaisesRegex(ValueError,'source_manifest'):validate(r)

    def test_changed_source_route(self):
        r=build();r['sources'][next(iter(r['sources']))]='0'*64
        with self.assertRaisesRegex(ValueError,'source_manifest'):validate(r)

    def test_unknown_route(self):
        with self.assertRaisesRegex(Stop,'unregistered'):self.g.before('A.silent_write',self.before)

    def test_missing_after(self):
        self.start()
        with self.assertRaisesRegex(Stop,'after_saved'):self.g.validate_pair(True,True)

    def test_cleanup_before_pair(self):
        self.start()
        with self.assertRaisesRegex(Stop,'cleanup_before'):self.g.cleanup(True)

    def test_missing_after_blocks_next(self):
        self.start()
        with self.assertRaisesRegex(Stop,'previous_pair'):self.g.before(self.route['route_id'],self.before)

    def test_missing_transaction(self):
        self.g.before(self.route['route_id'],self.before);self.g.advance('action_started')
        with self.assertRaisesRegex(Stop,'receipt_missing'):self.g.advance('action_confirmed',{})

    def test_wrong_actor(self):
        self.receipt['actor_sha256']='f'*64
        with self.assertRaisesRegex(Stop,'binding_mismatch'):self.start()

    def test_missing_table(self):
        self.before['table_names'].pop()
        with self.assertRaisesRegex(Stop,'table_coverage'):self.g.before(self.route['route_id'],self.before)

    def test_all_outcomes_need_after(self):
        for outcome in ('committed','denied','replayed'):
            self.g=EvidenceGate(self.folder/outcome);self.receipt['outcome']=outcome;self.start()
            with self.assertRaisesRegex(Stop,'after_saved'):self.g.after(None)

    def test_valid_chain(self):
        self.start();self.g.after(self.before);self.g.validate_pair(True,True);self.g.cleanup(True)
        self.assertTrue((self.g.path/'after-1.json').exists())
        self.assertTrue(all(x['timestamp_ns']>0 for x in self.g.history))
        self.assertTrue(all(x['previous_sha256'] for x in self.g.history[1:]))

    def test_protected_drift(self):
        self.start();self.g.after(self.before)
        with self.assertRaisesRegex(Stop,'drift'):self.g.validate_pair(False,True)

    def test_unexplained_write(self):
        self.start();self.g.after(self.before)
        with self.assertRaisesRegex(Stop,'unexplained'):self.g.validate_pair(True,False)

    def test_query_budget(self):
        for _ in range(128):self.g.query()
        with self.assertRaisesRegex(Stop,'budget'):self.g.query()

    def test_no_retry(self):
        with self.assertRaisesRegex(Stop,'retry'):self.g.query(retry=True)

    def test_interruption(self):
        self.start()
        with self.assertRaisesRegex(Stop,'missing_pair'):self.g.close()
        self.assertTrue(self.g.halted)
        self.assertEqual(self.g.history[-1]['status'],'NO_GO')

    def test_canary_requires_every_gate(self):
        all_pass={x:True for x in REQUIRED_GATES}
        for key in REQUIRED_GATES:
            r=dict(all_pass);r[key]=False
            self.assertFalse(canary_decision(r)['allowed'])
        self.assertFalse(canary_decision(all_pass)['workflow_proofrun_allowed'])

    def test_full_workflow_not_squeezed_into_128(self):
        p=query_plan(len(contracts()))
        self.assertFalse(p['admitted_under_current_limit'])
        self.assertEqual(p['parts']['full_collectors'],18)

    def test_cleanup_deletes_cascades_but_keeps_receipt(self):
        r=next(x for x in contracts() if x['route_id']=='window.cleanup')
        self.assertTrue(any(x['table'].endswith('.b_versions') and x['origin']=='workspace_fk_cascade' for x in r['effects']))
        self.assertTrue(any(x['table'].endswith('.audit') and x['operations']==['insert'] for x in r['effects']))

if __name__=='__main__':unittest.main()
