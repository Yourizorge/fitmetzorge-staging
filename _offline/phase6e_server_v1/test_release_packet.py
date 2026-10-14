import copy,json,pathlib,tempfile,unittest
import release_packet as p


class Tests(unittest.TestCase):
    def receipt(self):
        observer=[{'confirmed':True,'protocol_commands':1} for _ in range(8)]
        values={
            'result.json':{'status':'CLEAN_CI_PASS','migrations_applied':45,'commit':'a'*40,'candidate_sha256':'b'*64},
            'collection.json':{'verified':True,'run':123,'archive_sha256':'c'*64},
            'candidate.json':{'sources':{'synthetic-only':'d'*64}},
            'integration-database.json':{'protocol':{'commands':1841}},
            'integration-native-admin-protocol.json':{'commands':81},
            'integration-managed-auth-protocol.json':{'commands':1433,'statements':[{'temp_written':0}]}}
        for i,n in enumerate([47,2]):
            values['cli-protocol-'+str(i)+'.json']={'complete':True,'protocol_commands':n,'observer_commands':copy.deepcopy(observer)}
            values['cli-numeric-coverage-'+str(i)+'.json']={'all_protocol_visible':True,'temp_written':0}
        return values
    def build(self,values):
        with tempfile.TemporaryDirectory(prefix='fmz-release-unit-') as name:
            folder=pathlib.Path(name)
            for file,value in values.items():(folder/file).write_text(json.dumps(value))
            return p.build(folder)
    def test_all_protocol_and_safety_costs_are_counted(self):
        result=self.build(self.receipt())
        self.assertEqual(result['observed_local_total'],3420)
        self.assertEqual(result['normal_capacity'],4015)
        self.assertEqual(result['safety_reserve'],120)
        self.assertEqual(result['proposed_maximum'],4135)
        self.assertFalse(result['owner_budget_approval'])
        self.assertFalse(result['migration']['hosted_applied'])
    def test_old_unmetered_observer_receipt_is_not_admission(self):
        values=self.receipt();del values['cli-protocol-0.json']['observer_commands']
        with self.assertRaisesRegex(ValueError,'observers_incomplete'):self.build(values)
    def test_partial_or_temp_writing_evidence_is_denied(self):
        for file,key,value in [('result.json','status','NO_GO'),('cli-numeric-coverage-0.json','temp_written',1),
                               ('integration-managed-auth-protocol.json','commands',1701)]:
            values=self.receipt();values[file][key]=value
            with self.assertRaises(ValueError):self.build(values)
    def test_incomplete_observer_is_denied(self):
        values=self.receipt();values['cli-protocol-1.json']['observer_commands'][3]['confirmed']=False
        with self.assertRaisesRegex(ValueError,'observers_incomplete'):self.build(values)


if __name__=='__main__':unittest.main()
