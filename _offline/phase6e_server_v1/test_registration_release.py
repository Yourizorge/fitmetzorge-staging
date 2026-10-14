import json,pathlib,tempfile,unittest
from registration_release import build

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
        return values
    def run_build(self,values):
        with tempfile.TemporaryDirectory(prefix='fmz-registration-release-unit-') as folder:
            p=pathlib.Path(folder)
            assert p.resolve().parent==pathlib.Path(tempfile.gettempdir()).resolve()
            for name,value in values.items():(p/name).write_text(json.dumps(value))
            return build(p)
    def test_no_implicit_hosted_budget(self):
        value=self.run_build(self.fixture());self.assertEqual(value['observed_sql_total'],779)
        self.assertFalse(value['budgets']['hosted_authorized']);self.assertFalse(value['owner_accepted'])
    def test_incomplete_or_temp_writing_evidence_denied(self):
        for file,key,value in [('result.json','status','NO_GO'),('registration12-browser.json','status','NO_GO'),
            ('registration12-dry-run.json','pending',True),('cli-numeric-coverage-0.json','temp_written',1)]:
            f=self.fixture();f[file][key]=value
            with self.assertRaises(ValueError):self.run_build(f)
if __name__=='__main__':unittest.main()
