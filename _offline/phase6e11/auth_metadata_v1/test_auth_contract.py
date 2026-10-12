"""Replay sanitized real CI observations; add missing/extra/wrong-row faults."""
import copy,hashlib,json,pathlib,sys,unittest
from auth_contract import Contract

SOURCE=None
class Exact(unittest.TestCase):
    def proof(self,fault=None):
        rows=copy.deepcopy(SOURCE)
        first=rows[0]['events'][0]['actor_sha'];contract=Contract(first)
        session=next(e['key_sha'] for e in rows[1]['events'] if e['table_name']=='auth.sessions')
        for index,row in enumerate(rows):
            events=row['events'];op=row['operation']
            if fault=='missing' and op=='verify':events.pop()
            if fault=='extra' and op=='issue':events.append(copy.deepcopy(events[0]))
            if fault=='actor' and op=='issue':events[0]['actor_sha']='0'*64
            if fault=='transaction' and op=='verify':events[-1]['xid']='0'
            if fault=='link' and op=='verify':next(e for e in events if e['operation']=='DELETE')['key_sha']='0'*64
            if fault=='session' and op=='refresh':next(e for e in events if e['table_name']=='auth.sessions')['key_sha']='0'*64
            if fault=='delete' and op=='logout':next(e for e in events if e['table_name']=='auth.refresh_tokens')['key_sha']='0'*64
            contract.validate(op,events,session if op in ('verify','refresh','logout') else None)
        return contract
    def test_real_six(self):self.assertEqual(self.proof().step,6)
    def test_faults(self):
        for fault in ('missing','extra','actor','transaction','link','session','delete'):
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.proof(fault)
    def test_duplicate_action(self):
        contract=self.proof()
        with self.assertRaises(ValueError):contract.validate('issue',SOURCE[0]['events'])
    def test_sticky_stop(self):
        c=Contract(SOURCE[0]['events'][0]['actor_sha'])
        with self.assertRaises(ValueError):c.validate('issue',[])
        with self.assertRaisesRegex(ValueError,'stopped'):c.validate('issue',SOURCE[0]['events'])

if __name__=='__main__':
    path=pathlib.Path(sys.argv.pop(1));value=json.loads(path.read_text())
    SOURCE=[x for x in value['completed_pairs'] if x['role']=='a_member']
    if len(SOURCE)!=6 or not all(x['pair_complete'] for x in SOURCE):raise RuntimeError('reference_incomplete')
    unittest.main()
