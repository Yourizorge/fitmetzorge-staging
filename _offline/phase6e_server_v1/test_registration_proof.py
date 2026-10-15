import copy,types,unittest
from registration_proof import MeasuredRegistration,SCHEMA,digest
from store import Denied

ID=lambda n:'79000000-0000-4000-8000-'+str(n).zfill(12)
class Tests(unittest.TestCase):
    def scenario(self,mode):
        saved={};actor=digest(ID(2));key='a'*64
        writes=[{'id':i,'table':SCHEMA+'.'+table,'operation':op,'key_sha':key,'xid':'42','actor_sha':actor}
                for i,(table,op) in enumerate([('workspaces','UPDATE'),('revisions','INSERT'),('requests','INSERT')])]
        before={'state_sha':'a'*64,'version':0,'writes':[]};after={'state_sha':'b'*64,'version':1,'writes':copy.deepcopy(writes)}
        def execute(*args):
            if mode=='failed':raise Denied('synthetic_rollback')
            return {'idempotent':mode=='replay','writes':writes}
        store=types.SimpleNamespace(bindings={ID(1):ID(2)},execute=execute)
        if mode in ('failed','replay'):after=copy.deepcopy(before)
        if mode=='extra':after['writes'].append({**writes[0],'id':4})
        if mode=='missing':after['writes'].pop()
        if mode=='actor':after['writes'][0]['actor_sha']='c'*64
        if mode=='transaction':after['writes'][0]['xid']='43'
        if mode=='key':after['writes'][0]['key_sha']='d'*64
        if mode=='history':before['writes']=copy.deepcopy(writes);after['writes']=[]
        pair=MeasuredRegistration(store,lambda n,v:saved.update({n:copy.deepcopy(v)}))
        values=iter([before,after])
        pair.sample=lambda *args:next(values)
        return pair,saved
    def test_exact_request_actor_transaction_and_three_writes(self):
        pair,saved=self.scenario('pass');pair.execute(ID(1),'synthetic',ID(3),0,{'action':'register12'})
        self.assertEqual(len(saved),3);self.assertEqual(pair.pairs[0]['expected_count'],3)
    def test_zero_writes_for_replay_and_rollback(self):
        for mode in ('replay','failed'):
            pair,saved=self.scenario(mode)
            if mode=='failed':
                with self.assertRaises(Denied):pair.execute(ID(1),'synthetic',ID(3),0,{})
            else:pair.execute(ID(1),'synthetic',ID(3),0,{})
            self.assertEqual(pair.pairs[0]['writes'],[]);self.assertEqual(len(saved),3)
    def test_extra_missing_history_actor_xid_key_fail_closed(self):
        for mode in ('extra','missing','history','actor','transaction','key'):
            pair,saved=self.scenario(mode)
            with self.assertRaises(Denied):pair.execute(ID(1),'synthetic',ID(3),0,{})
            self.assertEqual(pair.pairs,[]);self.assertEqual(len(saved),2)
    def test_missing_after_is_not_a_complete_pair(self):
        pair,saved=self.scenario('pass');sample=pair.sample;calls=[]
        def broken(*args):
            calls.append(1)
            if len(calls)==2:raise OSError('synthetic_transport')
            return sample(*args)
        pair.sample=broken
        with self.assertRaises(OSError):pair.execute(ID(1),'synthetic',ID(3),0,{})
        self.assertEqual(len(saved),1);self.assertEqual(pair.pairs,[])
    def test_unknown_workspace_never_measured(self):
        pair,saved=self.scenario('pass')
        with self.assertRaises(Denied):pair.execute(ID(5),'synthetic',ID(3),0,{})
        self.assertEqual(saved,{})

if __name__=='__main__':unittest.main()
