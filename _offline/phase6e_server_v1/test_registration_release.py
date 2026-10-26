import json,pathlib,tempfile,unittest
from registration_release import build
import ci_profile
from test_ci_profile import sources,history,receipt

class Tests(unittest.TestCase):
    def fixture(self):
        values={'result.json':{'status':'CLEAN_CI_PASS','commit':'a'*40,'candidate_sha256':'b'*64},
         'collection.json':{'verified':True,'run':1},'candidate.json':{'sources':{'synthetic':'c'*64}},
         'registration12-minimal-history.json':{'history':[{'version':str(i)} for i in range(44)]+[{'version':'20261014105919'}],'migration_sha256':'d'*64},
         'registration12-dry-run.json':{'pending':False,'local_only':True},
         'registration12-database.json':{'commands':313,'register':[]},
         'registration12-integration-native-admin-protocol.json':{'commands':30},
         'registration12-integration-managed-auth-protocol.json':{'commands':400,'statements':[{'temp_written':0}]},
         'registration12-browser.json':{'status':'PASS'}}
        values['registration12-integration-application-io.json']={'deltas':{'postgres':{'temp_written':0},'fmz6e_integration_server':{'temp_written':0}}}
        for i in (0,1):
            values[f'cli-protocol-{i}.json']={'complete':True,'protocol_commands':10,'observer_commands':[{}]*8}
            values[f'cli-numeric-coverage-{i}.json']={'all_protocol_visible':True,'temp_written':0}
            values[f'cli-isolation-{i}.json']={'commands':8,'restored':True,'protocol':[{'confirmed':True}]*8}
        return values
    def run_build(self,values):
        with tempfile.TemporaryDirectory(prefix='fmz-registration-release-unit-') as folder:
            p=pathlib.Path(folder)
            assert p.resolve().parent==pathlib.Path(tempfile.gettempdir()).resolve()
            for name,value in values.items():(p/name).write_text(json.dumps(value))
            return build(p)
    def test_no_implicit_hosted_budget(self):
        value=self.run_build(self.fixture());self.assertEqual(value['observed_sql_total'],795)
        self.assertFalse(value['budgets']['hosted_authorized']);self.assertFalse(value['owner_accepted'])
    def test_incomplete_or_temp_writing_evidence_denied(self):
        for file,key,value in [('result.json','status','NO_GO'),('registration12-browser.json','status','NO_GO'),
            ('registration12-dry-run.json','pending',True),('cli-numeric-coverage-0.json','temp_written',1)]:
            f=self.fixture();f[file][key]=value
            with self.assertRaises(ValueError):self.run_build(f)
    def current_fixture(self):
        value=self.fixture()
        value['result.json'].update(cli_profile=ci_profile.PROFILE,migrations_applied=47)
        value['candidate.json']['sources']={name:'c'*64 for name in sources()}
        value['registration12-minimal-history.json']['history']=history('minimal')
        value['candidate-47-history.json']={'history':history('complete')}
        for i in (0,1):value['cli-protocol-'+str(i)+'.json']=receipt(i)
        return value
    def test_canonical45_profile_has_46_minimal_and_47_complete(self):
        result=self.run_build(self.current_fixture())
        self.assertEqual(result['migration_history']['count'],46)
        self.assertEqual(result['migration_history']['sorted_last'],'20261018070231')
        self.assertEqual(result['complete_history_count'],47)
        self.assertFalse(result['budgets']['hosted_authorized'])
    def test_current_profile_cannot_reuse_old_counts_or_missing_quota(self):
        for stage in ('registration12-minimal-history.json','candidate-47-history.json'):
            value=self.current_fixture();value[stage]['history'].pop()
            with self.assertRaisesRegex(ValueError,'history_identity'):self.run_build(value)
        value=self.current_fixture();value['result.json']['migrations_applied']=46
        with self.assertRaisesRegex(ValueError,'complete_history'):self.run_build(value)
        value=self.current_fixture();value['cli-protocol-0.json']['profile']='endchain'
        with self.assertRaisesRegex(ValueError,'app_cli_evidence'):self.run_build(value)
if __name__=='__main__':unittest.main()
