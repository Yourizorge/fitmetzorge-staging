"""Local mock-protocol and real PG-parser tests, not GoTrue compatibility."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
import admission_auth_runtime_profile as m


def metadata(pid=10, restricted=False, readonly=False):
    role=dict(name='supabase_auth_admin',oid=42,superuser=False,inherit=True,
        createrole=not restricted,createdb=False,login=True,replication=False,
        bypassrls=False,connlimit=-1,validuntil=None,config=None)
    return dict(cluster_id='123',datid=5,pid=pid,postmaster_start='start',pg17=True,
        ssl=True,bounded=True,postgres=True,origin=True,readonly=readonly,
        no_prepared=True,tracked=True,external=False,roles=[role],memberships=[])


def privileges(before):
    return [{'role':role,**{flag:before and role=='supabase_auth_admin' and flag=='createrole'
             for flag in m.scope.PRIVILEGE_FLAGS}}
            for role in ('supabase_auth_admin','anon','authenticated','service_role')]


class Journal:
    def __init__(self):self.records={};self.fail=None
    def save(self,name,value):
        if name==self.fail:raise OSError('synthetic_storage')
        if name in self.records:raise AssertionError('overwrite')
        self.records[name]=copy.deepcopy(value)


class Cursor:
    description=True
    def __init__(self,rows):self.rows=rows
    def fetchall(self):return self.rows


class Connection:
    autocommit=True
    def __init__(self,owner):self.owner=owner;self.closed=False
    def close(self):self.closed=True
    def execute(self,text,args=None):
        o=self.owner;phase=o.phase.removeprefix('profile.')
        o.executed.append((phase,text))
        if phase==o.fail or (phase=='failure_rollback' and o.fail_rollback):raise TimeoutError(phase)
        if phase.endswith('_metadata'):
            v=metadata(pid=11 if phase=='witness_metadata' else 10,
                restricted=phase!='before_metadata',readonly=phase=='witness_metadata')
            if o.mutate:o.mutate(phase,v)
            return Cursor([{'value':v}])
        if phase.endswith('_privileges'):
            v=privileges(phase=='before_privileges')
            if o.bad_flag:v[0][o.bad_flag]=True
            return Cursor(v)
        return Cursor([])


class Owner:
    def __init__(self):
        self.isolation=dict(pg_system_identifier='123',database_oid=5)
        self.phase=None;self.calls=[];self.executed=[];self.connections=[]
        self.fail=self.reject=self.bad_flag=self.mutate=None;self.fail_rollback=False
        self.runtime=types.SimpleNamespace(connect=self.connect)
    def connect(self):
        c=Connection(self);self.connections.append(c);return c
    def _local_call(self,name,kind,action):
        self.calls.append((name,kind));self.phase=name
        if name==self.reject:raise RuntimeError('root_denied')
        return action()


class ProfileTests(unittest.TestCase):
    def test_exported_role_witnesses_replay_metadata_delta_and_privileges(self):
        owner=Owner();journal=Journal()
        def mutate(phase,value):value['roles'][0]['config']=['app.secret=DO_NOT_EXPORT']
        owner.mutate=mutate
        source={'test_only_source':'a'*64}
        result,error=m._execute(owner,journal,lambda:None,source_binding=source)
        self.assertIsNone(error)
        rows={r['phase']:r for name,r in journal.records.items() if name.startswith('query-')}
        self.assertEqual(len(rows),10)
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(rows))
        before=m.metadata(rows['before_metadata']['rows'],owner.isolation,readonly=False)
        after=m.metadata(rows['after_metadata']['rows'],owner.isolation,readonly=False)
        witness=m.metadata(rows['witness_metadata']['rows'],owner.isolation,readonly=True)
        m.delta(before,after,fresh=False);m.delta(before,witness,fresh=True)
        m.privileges(rows['before_privileges']['rows'],before=True)
        m.privileges(rows['witness_privileges']['rows'],before=False)
        for record in rows.values():
            self.assertEqual(record['source_binding'],source)
            self.assertEqual(record['rows_sha256'],m.engine.digest(record['rows']))
            self.assertFalse(record['query_io']['observed'])
        self.assertEqual(result['emitted_attempts'],10)
        self.assertTrue(witness['roles'][0]['config']['redacted'])
        self.assertEqual(witness['roles'][0]['config']['count'],1)
        witness['roles'][0]['config']['sha256']='b'*64
        with self.assertRaises(m.engine.Blocked):m.delta(before,witness,fresh=True)

    def test_profile_observation_storage_fault_does_not_repeat_commit(self):
        for name in ('query-02-before_metadata.json','query-06-commit.json'):
            with self.subTest(name=name):
                owner=Owner();journal=Journal();journal.fail=name
                result,error=m._execute(owner,journal,lambda:None)
                self.assertIsInstance(error,OSError)
                self.assertFalse(result['capability_reduced'])
                phases=[p for p,_ in owner.executed]
                if 'commit' in name:
                    self.assertTrue(result['commit_unknown'])
                    self.assertEqual(phases.count('commit'),1)
                    self.assertNotIn('failure_rollback',phases)
                    self.assertEqual(len(owner.connections),1)
                else:
                    self.assertNotIn('restrict',phases)
                    self.assertEqual(phases[-1],'failure_rollback')

    def test_unselected_profile_fields_and_nonboolean_flags_not_exported(self):
        rows=privileges(True);rows[0]['password']='DO_NOT_EXPORT'
        with self.assertRaises(m.engine.Blocked):m.observation_rows('before_privileges',rows)
        del rows[0]['password'];rows[0]['superuser']='DO_NOT_EXPORT'
        with self.assertRaises(m.engine.Blocked):m.observation_rows('before_privileges',rows)

    def test_actual_protocol_journal_positive_and_lost_commit_originals(self):
        for failure in (None,'commit'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp:
                root=pathlib.Path(temp).resolve()
                def publish(name,value):
                    with (root/name).open('xb') as stream:stream.write(m.durable.raw(value))
                journal=m.durable.Journal(root/'private',publish,'profile-journal')
                owner=Owner();owner.fail=failure
                def unchanged():
                    journal._inventory()
                    for name,ref in journal.entries.items():journal._read(name,ref)
                result,error=m._execute(owner,journal,unchanged)
                journal.save('result.json',result)
                index=journal.seal()
                refs=m.evidence_refs(journal,index,root)
                self.assertTrue(index['complete'])  # Complete evidence, not successful operation.
                charges=[json.loads((journal.folder/name).read_bytes())
                         for name in sorted(journal.entries) if name.startswith('charge-')]
                self.assertEqual([r['phase'] for r in charges],[p for p,_ in owner.executed])
                self.assertEqual(len(refs),len(journal.entries)+len(index['chunks'])+1)
                if failure is None:
                    self.assertIsNone(error)
                    self.assertTrue(result['capability_reduced'])
                    self.assertEqual(len(charges),10)
                    self.assertIn('witness.json',journal.entries)
                else:
                    self.assertIsInstance(error,TimeoutError)
                    self.assertTrue(result['commit_unknown'])
                    self.assertFalse(result['capability_reduced'])
                    self.assertEqual(len(charges),6)
                    self.assertNotIn('witness.json',journal.entries)
                    self.assertEqual(len(owner.connections),1)
                self.assertFalse(result['actual_auth_compatibility_proven'])

    def test_live_original_change_before_restrict_blocks_mutation(self):
        owner=Owner();journal=Journal()
        def unchanged():
            if owner.phase=='profile.restrict':raise m.engine.Blocked('original_changed')
        result,error=m._execute(owner,journal,unchanged)
        self.assertIn('original_changed',str(error))
        self.assertNotIn('restrict',[p for p,_ in owner.executed])
        self.assertEqual([p for p,_ in owner.executed][-1],'failure_rollback')
        self.assertFalse(result['capability_reduced'])

    def test_fresh_witness_external_writer_after_commit_is_no_go(self):
        owner=Owner()
        def mutate(phase,value):
            if phase=='witness_metadata':value['external']=True
        owner.mutate=mutate
        result,error=m._execute(owner,Journal(),lambda:None)
        self.assertIsNotNone(error)
        self.assertTrue(result['commit_confirmed'])
        self.assertFalse(result['commit_unknown'])
        self.assertFalse(result['capability_reduced'])
        self.assertEqual([p for p,_ in owner.executed].count('restrict'),1)
        self.assertNotIn('witness_privileges',[p for p,_ in owner.executed])

    def test_actual_durable_profile_journal_refs_include_all_packaged_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp).resolve()
            def publish(name,value):
                with (root/name).open('xb') as stream:stream.write(m.durable.raw(value))
            journal=m.durable.Journal(root/'private',publish,'profile-journal')
            journal.save('binding.json',{'target':'synthetic'})
            journal.save('result.json',{'status':'NO_GO'})
            index=journal.seal()
            refs=m.evidence_refs(journal,index,root)
            self.assertEqual({r['path'] for r in refs},{'private/binding.json','private/result.json',
                'profile-journal-001.json','profile-journal-index.json'})
            for ref in refs:
                raw=(root/ref['path']).read_bytes()
                self.assertEqual(ref['sha256'],m.durable.sha(raw))
                self.assertEqual(ref['bytes'],len(raw))
            (root/'private'/'result.json').write_bytes(b'changed')
            with self.assertRaises(m.engine.Blocked):m.evidence_refs(journal,index,root)

    def test_no_auth_backend_exemption_in_prestart_metadata(self):
        # Actual PG catalog query now rejects ALL other backends. This is not
        # a config-based claim that a live GoTrue worker cannot write.
        self.assertIn('and pid<>pg_backend_pid()),',m.META)
        self.assertNotIn('usename',m.META)
        v=metadata();v['external']=True
        with self.assertRaises(m.engine.Blocked):m.metadata([{'value':v}],Owner().isolation,readonly=False)

    def test_any_gotrue_start_or_lifetime_baseline_blocks_profile(self):
        clean=dict(start_attempted=False,container_id=None,auth=None,started_stats=None)
        m.before_start(types.SimpleNamespace(**clean))
        for name,value in (('start_attempted',True),('container_id','a'*64),('auth',{}),('started_stats',{})):
            with self.subTest(name=name),self.assertRaises(m.engine.Blocked):
                m.before_start(types.SimpleNamespace(**{**clean,name:value}))

    def test_prestart_server_runtime_not_uninitialized_context_runtime(self):
        o=Owner();runtime=o.runtime;target=o.isolation
        o.runtime=o.isolation=None
        result,error=m._execute(o,Journal(),lambda:None,runtime=runtime,isolation=target)
        self.assertIsNone(error)
        self.assertTrue(result['capability_reduced'])
        self.assertEqual(result['emitted_attempts'],10)

    def test_plan_and_sql_parser(self):
        from sql_protocol import statements
        self.assertEqual(len(m.PLAN),10)
        self.assertEqual(m.LIMIT,11)
        for phase,text in m.PLAN:self.assertEqual(len(statements(text)),1,phase)
        self.assertEqual(m.ALTER,'ALTER ROLE supabase_auth_admin NOCREATEROLE')
        self.assertIs(m.PLAN[2][1],m.scope.PRIVILEGES)
        self.assertIs(m.PLAN[8][1],m.scope.PRIVILEGES)

    def test_exact_reduction_and_no_other_mutation(self):
        o=Owner();j=Journal();result,error=m._execute(o,j,lambda:None)
        self.assertIsNone(error)
        self.assertTrue(result['capability_reduced'])
        self.assertEqual(result['emitted_attempts'],10)
        self.assertEqual([t for p,t in o.executed if p=='restrict'],[m.ALTER])
        self.assertTrue(all(c.closed for c in o.connections))
        for key in ('hosted_equivalence','security_freshness_claim','actual_auth_compatibility_proven',
                    'privilege_validator_exception','full_chain_admission'):
            self.assertFalse(result[key])

    def test_every_other_privilege_flag_blocks_before_alter(self):
        for flag in m.scope.PRIVILEGE_FLAGS:
            if flag=='createrole':continue
            o=Owner();o.bad_flag=flag
            result,error=m._execute(o,Journal(),lambda:None)
            self.assertIn('unexpected_privilege',str(error))
            self.assertNotIn('restrict',[p for p,_ in o.executed])

    def test_extra_role_capability_is_not_allowed(self):
        v=privileges(True);v[1]['createrole']=True
        with self.assertRaises(m.engine.Blocked):m.privileges(v,before=True)

    def test_postcondition_no_createrole_exception(self):
        with self.assertRaises(m.engine.Blocked):m.privileges(privileges(True),before=False)

    def test_other_role_attribute_and_membership_change_rejected(self):
        before=metadata()
        for field in ('createdb','oid','config','memberships'):
            after=metadata(restricted=True)
            if field=='memberships':after[field]=[{'changed':True}]
            else:after['roles'][0][field]=123
            with self.subTest(field=field),self.assertRaises(m.engine.Blocked):
                m.delta(before,after,fresh=False)

    def test_same_session_is_not_fresh_commit_witness(self):
        with self.assertRaisesRegex(m.engine.Blocked,'independent_backend'):
            m.delta(metadata(),metadata(restricted=True,readonly=True),fresh=True)

    def test_roles_and_memberships_overflow_refused(self):
        for key in ('roles','memberships'):
            v=metadata();v[key]=[v['roles'][0]]*257
            with self.assertRaisesRegex(m.engine.Blocked,'metadata_bound'):
                m.metadata([{'value':v}],Owner().isolation,readonly=False)

    def test_external_backend_wrong_cluster_and_tls_refused(self):
        for key,value in (('external',True),('cluster_id','different'),('ssl',False),('bounded',False)):
            v=metadata();v[key]=value
            with self.subTest(key=key),self.assertRaises(m.engine.Blocked):
                m.metadata([{'value':v}],Owner().isolation,readonly=False)

    def test_every_sql_failure_prefix_bounded(self):
        for phase,_ in m.PLAN:
            o=Owner();o.fail=phase
            with self.subTest(phase=phase):
                result,error=m._execute(o,Journal(),lambda:None)
                self.assertIsNotNone(error)
                self.assertFalse(result['capability_reduced'])
                self.assertLessEqual(result['emitted_attempts'],11)
                self.assertEqual([p for p,_ in o.executed].count(phase),1)
                self.assertTrue(all(c.closed for c in o.connections))

    def test_lost_begin_rollback_reserved(self):
        o=Owner();o.fail='begin'
        result,error=m._execute(o,Journal(),lambda:None)
        self.assertEqual([p for p,_ in o.executed],['begin','failure_rollback'])

    def test_lost_commit_no_retry_no_witness(self):
        o=Owner();o.fail='commit'
        result,error=m._execute(o,Journal(),lambda:None)
        self.assertTrue(result['commit_unknown'])
        self.assertNotIn('failure_rollback',[p for p,_ in o.executed])
        self.assertEqual(len(o.connections),1)

    def test_rollback_error_preserves_primary(self):
        o=Owner();o.fail='restrict';o.fail_rollback=True
        result,error=m._execute(o,Journal(),lambda:None)
        self.assertEqual(str(error),'restrict')
        self.assertTrue(any('rollback_secondary' in n for n in error.__notes__))

    def test_root_denial_before_alter(self):
        o=Owner();o.reject='profile.restrict'
        result,error=m._execute(o,Journal(),lambda:None)
        self.assertNotIn('restrict',[p for p,_ in o.executed])

    def test_durable_intent_failure_before_alter(self):
        o=Owner();j=Journal();j.fail='intent.json'
        result,error=m._execute(o,j,lambda:None)
        self.assertIsInstance(error,OSError)
        self.assertNotIn('restrict',[p for p,_ in o.executed])

    def test_predispatch_storage_failure_before_alter(self):
        o=Owner();j=Journal();j.fail='charge-04.json'
        result,error=m._execute(o,j,lambda:None)
        self.assertIsInstance(error,OSError)
        self.assertNotIn('restrict',[p for p,_ in o.executed])

    def test_before_already_restricted_is_not_mutated(self):
        o=Owner()
        def mutate(phase,v):
            if phase=='before_metadata':v['roles'][0]['createrole']=False
        o.mutate=mutate
        result,error=m._execute(o,Journal(),lambda:None)
        self.assertNotIn('restrict',[p for p,_ in o.executed])
        self.assertFalse(result['capability_reduced'])


if __name__=='__main__':unittest.main()
