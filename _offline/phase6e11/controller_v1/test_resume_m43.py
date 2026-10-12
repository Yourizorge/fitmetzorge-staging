import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import resume_m43 as r

class Ledger:
    def __init__(self):self.events=[]
    def event(self,name,**kw):self.events.append(name)

class Resume(unittest.TestCase):
    def run_case(self,bad=None):
        calls=[];ledger=Ledger()
        before={'status':'complete','history_count':42,'tables':[{'name':'public.synthetic'}],'bindings':{},'cli_numeric':{}}
        after={**before,'history_count':43}
        if bad=='before':before.update(status='incomplete',reason='pair_missing')
        if bad=='after':after.update(status='incomplete',reason='pair_missing')
        def capture(*args):calls.append('capture');return before if len([x for x in calls if x=='capture'])==1 else after
        def cli(dry):
            calls.append('dry' if dry else 'apply')
            return {'exit_code':1 if bad=='apply' and not dry else 0,
                'migration_files':[] if bad=='dry' or len(calls)==5 else [r.m.M43], 'up_to_date':len(calls)==5}
        saved={}
        with patch.object(r.m,'save',side_effect=lambda p,v:saved.update({p.name:v})),patch.object(r.m,'compare',side_effect=r.m.Stop('protected_data_drift') if bad=='drift' else None,return_value={'protected_data_unchanged':True}),patch.object(r.m.prior.old,'cli_load',return_value={'pass':True}):
            value=r.perform('unused',{},Path('synthetic'),ledger,capture,cli)
        return value,calls,ledger.events,saved
    def test_complete_sequence(self):
        value,calls,events,saved=self.run_case()
        self.assertEqual(calls,['capture','dry','apply','capture','dry'])
        self.assertEqual(value['status'],'M43_PAIRED_PASS_CONTROLLER_PENDING')
        self.assertEqual(events,['before_saved','action_started','action_confirmed','after_saved','pair_validated','next_step_allowed'])
    def test_incomplete_before_never_runs_cli(self):
        value,calls,_,_=self.run_case('before');self.assertEqual(calls,['capture']);self.assertFalse(value['migration_applied'])
    def test_wrong_dryrun_never_applies(self):
        value,calls,_,_=self.run_case('dry');self.assertEqual(calls,['capture','dry']);self.assertEqual(value['status'],'NO_GO')
    def test_failed_apply_still_measures_after(self):
        value,calls,_,_=self.run_case('apply');self.assertEqual(calls,['capture','dry','apply','capture']);self.assertEqual(value['reason'],'migration_identity')
    def test_missing_after_blocks_every_followup(self):
        value,calls,events,_=self.run_case('after');self.assertEqual(value['status'],'NO_GO');self.assertNotIn('next_step_allowed',events);self.assertEqual(len(calls),4)
    def test_preservation_failure_blocks_followup(self):
        value,calls,events,_=self.run_case('drift')
        self.assertEqual(value['status'],'NO_GO');self.assertEqual(value['reason'],'protected_data_drift')
        self.assertEqual(calls,['capture','dry','apply','capture'])
        self.assertNotIn('pair_validated',events);self.assertNotIn('next_step_allowed',events)
    def test_applied_migration_remains_byte_identical_to_ci(self):
        source='supabase/migrations/'+r.m.M43
        manifest=json.loads((r.m.CI/'candidate.json').read_text())['sources']
        self.assertEqual(r.m.c.sha(r.m.ROOT/source),manifest[source])
        self.assertEqual(manifest[source],'bab79b7ca5876c2dcef055d0e95997595772aebc051283e69bbeb2ca1dc4bd57')
    def test_changed_controller_cannot_reuse_old_ci_admission(self):
        with self.assertRaisesRegex(r.m.Stop,'tested_candidate_changed'):r.admission()

if __name__=='__main__':unittest.main()
