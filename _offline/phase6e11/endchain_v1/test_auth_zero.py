import copy,hashlib,json,types,unittest,uuid
from unittest.mock import patch
import auth_zero
from auth_evidence import AuthEvidence
from complete_register import auth_source
from safety_auth_budget import ROLES

IDS={r:'69000000-0000-4000-8000-%012d'%(i+1) for i,r in enumerate(ROLES)}


class AuthZeroTests(unittest.TestCase):
    def metadata(self,bound):
        n=len(bound['ids'])
        return dict(manifest_sha256=bound['sha256'],manifest_count=n,registered_count=3,
            scope_count=n,extra_registered_count=0,sessions=0,refresh_tokens=0)

    def test_staging_twelve_is_bound_and_all_registered_ids_are_measured_without_enabled_filter(self):
        actors=['69000000-0000-4000-8000-%012d'%i for i in range(1,13)]
        values=[{'accounts':[{'id':x} for x in actors[:3]]},
            {'foreign':{'id':actors[3]},'plain':{'id':actors[4]}},
            [{'id':x} for x in actors[5:10]],{'controls':[{'id':x} for x in actors[6:12]]}]
        raw=[json.dumps(v).encode() for v in values]
        pins={k:hashlib.sha256(v).hexdigest() for k,v in zip(auth_zero.SOURCES,raw)}
        with patch.object(auth_zero,'SOURCES',pins),patch('pathlib.Path.read_bytes',side_effect=raw):
            bound=auth_zero.scope(IDS,'staging','unused')
        self.assertEqual(len(bound['ids']),12)
        sql=auth_zero.expression(bound)
        for table in ('fmz6e10_private.identities','fmz6e11_private.identities','auth.sessions','auth.refresh_tokens'):
            self.assertIn(table,sql)
        self.assertNotIn('enabled',sql);self.assertNotIn('DELETE',sql)
        from sql_protocol import statements
        self.assertEqual(len(statements('select ('+sql+')')),1)
        for actor in actors:self.assertIn(actor,sql)
        with patch('pathlib.Path.read_bytes',return_value=b'{}'):
            with self.assertRaisesRegex(ValueError,'inventory_changed'):auth_zero.scope(IDS,'staging','unused')

    def test_scope_or_residual_on_any_old_control_blocks_zero(self):
        bound=auth_zero.scope(IDS,'disposable_ci');good=self.metadata(bound)
        auth_zero.validate(good,bound)
        for key,value in [('sessions',1),('refresh_tokens',1),('manifest_sha256','0'*64),
                ('scope_count',2),('manifest_count',12),('registered_count',True)]:
            with self.subTest(key=key):
                bad={**good,key:value}
                with self.assertRaises(ValueError):auth_zero.validate(bad,bound)
        more={**good,'scope_count':4,'registered_count':4,'extra_registered_count':1}
        self.assertEqual(auth_zero.validate(more,bound)['scope_count'],4)

    def evidence(self,ci=False,bad=False,lost=False):
        bound=auth_zero.scope(IDS,'disposable_ci');calls=[];saved={}
        before=dict(reset='fixed',dealloc=0,track_utility='on',statements=[])
        after={**before,'statements':[dict(queryid='7',calls=4,since='fixed',temp_read=0,temp_written=0,wal_bytes='0',exec_ms=1)]}
        zero=self.metadata(bound)
        if bad:zero['sessions']=1
        combined=dict(auth_stats=after,registered_auth_zero=zero,events=[])
        queue=['','[]',json.dumps(dict(seq=0,auth_stats=before)),json.dumps(combined),'[]','']
        def sql(text):
            calls.append(text)
            if lost and len(calls)==4:raise RuntimeError('lost_after')
            return queue.pop(0)
        audit=types.SimpleNamespace(arm=lambda *a:'ARM',events=lambda *a:'EVENTS',disarm=lambda *a:'DISARM')
        e=AuthEvidence(run_id=IDS[ROLES[0]],ids=IDS,audit=audit,contract_type=auth_source.Contract,
            sql=sql,save=lambda n,v:saved.update({n:copy.deepcopy(v)}),independent_ci=ci,zero_scope=bound)
        for role in ROLES:e.contracts[role].step=5 if role==ROLES[-1] else 6
        return e,calls,saved

    def test_final_auth_after_contains_independent_zero_without_an_extra_command(self):
        for ci in (False,True):
            e,calls,saved=self.evidence(ci)
            before=e.before(ROLES[-1],'revoked_denial',str(uuid.uuid4()))
            result=e.after(ROLES[-1],'revoked_denial',before,{})
            self.assertEqual(len(calls),6)
            self.assertEqual(result['registered_auth_zero']['sessions'],0)
            self.assertEqual(sum('registered_auth_zero' in sql for sql in calls),1)
            self.assertIn('registered_auth_zero',saved['auth-pair-00.json'])

    def test_lost_or_nonzero_final_after_returns_no_proof(self):
        for bad,lost in ((True,False),(False,True)):
            e,calls,saved=self.evidence(bad=bad,lost=lost)
            before=e.before(ROLES[-1],'revoked_denial',str(uuid.uuid4()))
            with self.assertRaises((ValueError,RuntimeError)):e.after(ROLES[-1],'revoked_denial',before,{})
            self.assertTrue(e.stopped);self.assertNotIn('auth-pair-00.json',saved)
            self.assertNotIn('DISARM',calls)


if __name__=='__main__':unittest.main()
