"""Source/AST and synthetic catalog regressions; never actual PostgreSQL proof."""
import argparse
import copy
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from quota_candidate_v1 import runtime_catalog as m
from quota_candidate_v1 import runtime_history as h
from quota_candidate_v1 import compiler as c
from quota_candidate_v1.test_quota_candidate import samples,START,END,NOW

ROOT=pathlib.Path(__file__).resolve().parents[4]


def old_target(root,module,function_oid,trigger_oid):
    text=module.source(root)
    body=text.split('as $f$',1)[1].split('$f$;',1)[0].replace('\r\n','\n')
    return dict(function_oid=function_oid,trigger_oid=trigger_oid,
        function=dict(body_sha=c.sha(body.encode()),owner='postgres',definer=False,
            path=['search_path=pg_catalog, pg_temp'],public_execute=False,forbidden_execute=False),
        trigger=dict(type=27,enabled='O',function_matches=True,no_filter=True,no_arguments=True,constraint='0'),
        migration_statements=[text])


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='case-catalog-offline-')
        cls.root=pathlib.Path(cls.temporary.name)
        files=list((ROOT/'supabase/migrations').glob('*.sql'))+list((ROOT/h.APP).glob('*.sql'))
        names={f.relative_to(ROOT).as_posix() for f in files}|set(c.PINS)|{
            c.PREFIX+n for n in (*c.SUPPORT,'lifecycle_gates.py','quota_boundary.py','migration_boundary.py')}
        for name in names:
            target=cls.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        for name in (*c.OWN,'runtime_history.py','runtime_catalog.py'):
            target=cls.root/c.PREFIX/'quota_candidate_v1'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(c.HERE/name,target)
            names.add(target.relative_to(cls.root).as_posix())
        cls.sources={name:c.sha((cls.root/name).read_bytes()) for name in names}
        cls.samples=samples(cls.root)
        manifest=c.prepare(cls.root,source_commit='a'*40,candidate_sha256='b'*64,
            github_run='41619169140',created_at=START,expires_at=END,
            cases=[dict(id='e66ba694-6c4a-4dab-b07d-0fad7a6d9abd',label='normal',cap=2349)],sources=cls.sources)
        cls.artifact=c.compile_candidate(cls.root,manifest,cls.samples,now=NOW)
        cls.history=h.CaseHistory(cls.root,cls.sources,local_version='20261103120000',local_sql=cls.artifact['sql'])
        old={r['version']:r for r in cls.history.historical}
        cls.raw=[]
        for path in files:
            version,label=path.stem.split('_',1)
            if version in old:cls.raw.append({**old[version],'source_statements':None})
            else:
                text=(cls.root/path.relative_to(ROOT)).read_text()
                cls.raw.append(dict(version=version,name=label,sql_sha=c.sha(text.encode()),source_statements=[text]))
        cls.raw.sort(key=lambda r:r['version'])
        cls.history.attest(cls.raw,appended=False)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def setUp(self):
        self.history=copy.deepcopy(self.__class__.history)
        self.owner=m.CaseCatalog(self.root,self.sources,self.artifact,self.history)
        old=old_target(self.root,m.quota_boundary,10,11)
        old.update(legacy_m44=old_target(self.root,m.migration_boundary,12,13),run_hashes=[],
            constraint_oid=20,constraint=dict(type='c',validated=True,expression=self.samples['constraint'][0]['expression']))
        self.before=dict(migrations=copy.deepcopy(self.history.before),catalog=dict(
            functions={'10':{'hash':'a'},'12':{'hash':'b'}},triggers={'11':'a','13':'b'},
            relations={'30':{'schema':c.SCHEMA,'name':'runs'}},policies={},
            constraints={'20':dict(name='runs_command_count_check',table=30,definition='bound-before',validated=True)},
            m44=old,baseline_quota=copy.deepcopy(self.samples),candidate={
                **{k:[] for k in ('table','columns','checks','indexes','function','triggers','leases')},
                'empty':copy.deepcopy(self.samples['empty'])}))

    def after(self):
        from pglast.stream import RawStream
        text=self.artifact['sql']
        raw=[*copy.deepcopy(self.raw),dict(version=self.history.local_version,name='disposable_case_quota_v1',
            sql_sha=c.sha(text.encode()),source_statements=[text])]
        self.history.attest(raw,appended=True)
        state=copy.deepcopy(self.before);state['migrations']=copy.deepcopy(self.history.after)
        catalog=state['catalog'];candidate=catalog['candidate'];contract=self.owner.contract
        catalog['baseline_quota']=None
        candidate['table']=[dict(oid='100',name=m.TABLE,kind='r',owner='postgres',rls=True,force=False,
            persistence='p',partition=False,inherited=False,rules=False,policies=False,forbidden_access=False,
            acl=[dict(grantee='postgres',grantor='postgres',privilege=p,grantable=False)
                 for p in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN')])]
        candidate['columns']=copy.deepcopy(contract['columns'])
        nodes=[n.stmt for n in m.quota.parser().parse_sql(text)]
        table=next(n for n in nodes if type(n).__name__=='CreateStmt')
        source_checks={m.TABLE+'_'+col.colname+'_check':RawStream()(k.raw_expr)
            for col in table.tableElts for k in col.constraints if k.contype.name=='CONSTR_CHECK'}
        candidate['checks']=[dict(oid=str(200+i),name=name,kind=kind,relation_oid='100',validated=True,
            local=True,inherited=0,noinherit=kind=='p',deferrable=False,deferred=False,
            expression=source_checks.get(name),columns=columns or [])
            for i,(name,(kind,expr,columns)) in enumerate(contract['checks'].items())]
        candidate['indexes']=[dict(oid='101',name=m.TABLE+'_pkey',method='btree',unique=True,primary=True,
            valid=True,ready=True,live=True,keys=1,attributes=1,nulls_not_distinct=False,no_predicate=True,
            no_expressions=True,key_numbers='1',options='0',opclasses=['pg_catalog.uuid_ops'])]
        candidate['function']=[dict(oid='110',schema=c.SCHEMA,name=m.FUNCTION,nargs=0,kind='f',returns_trigger=True,
            language=contract['language'],owner='postgres',definer=contract['definer'],leakproof=False,strict=False,
            volatility='v',parallel='u',config=contract['config'],body=contract['body'],
            effective_execute=dict.fromkeys(('anon','authenticated','service_role'),False),
            acl=[dict(grantee='postgres',grantor='postgres',privilege='EXECUTE',grantable=False)])]
        triggers=[n for n in nodes if type(n).__name__=='CreateTrigStmt']
        candidate['triggers']=[dict(oid=str(120+i),name=n.trigname,definition=RawStream()(n),enabled='O',
            internal=False,nonconstraint=True,deferrable=False,deferred=False,nargs=0,argument_bytes=0,
            columns='',unconditional=True,old_transition=None,new_transition=None,function_schema=c.SCHEMA,
            function_name=m.FUNCTION,function_nargs=0) for i,n in enumerate(triggers)]
        manifest=self.artifact['manifest']
        candidate['leases']=[dict(run_id=x['id'],purpose=manifest['purpose'],cap=x['cap'],parent_id=manifest['parent_run'],
            source_commit=manifest['source_commit'],candidate_sha=manifest['candidate_sha256'],ci_run=manifest['github_run'],
            starts_at=manifest['created_at'],expiry=manifest['expires_at'],binding_sha=c.sha(c.canonical(manifest)),
            whole_seconds=True) for x in manifest['cases']]
        catalog['relations'].update({'100':{'name':m.TABLE},'101':{'name':m.TABLE+'_pkey'}})
        catalog['functions']['110']={'hash':'new-function'}
        catalog['triggers'].update({r['oid']:r['definition'] for r in candidate['triggers']})
        catalog['constraints'].pop('20')
        catalog['constraints'].update({r['oid']:{'name':r['name']} for r in candidate['checks']})
        catalog['constraints']['299']={'name':'runs_command_count_check'}
        catalog['m44']['constraint_oid']=299
        check=next(k.def_ for n in nodes if type(n).__name__=='AlterTableStmt' for k in n.cmds
            if type(k.def_).__name__=='Constraint')
        catalog['m44']['constraint']['expression']=RawStream()(check.raw_expr)
        return state

    def ready(self):
        self.owner.initial(self.before)
        return self.after()

    def test_exact_source47_to_local48_and_post_catalog(self):
        after=self.ready()
        result=self.owner.transition(after)
        self.assertEqual(result['history_count'],48)
        self.assertFalse(result['canonical_migration_added'])
        self.assertEqual(result['sql_executed_by_validator'],0)
        self.assertEqual(self.owner.check_observed(after)['status'],'LOCAL48_CATALOG_UNCHANGED')
        self.assertNotIn('migration_statements',str(result))

    def test_single_select_same_parameter_and_before_absent_relation(self):
        for sql in (m.CATALOG_BEFORE,m.CATALOG_AFTER):
            self.assertEqual(m.single(sql)['kind'],'SelectStmt')
            self.assertIn('$1::text[]',sql)
            self.assertNotIn('$2',sql)
        self.assertNotIn(m.LEASE_QUERY,m.CATALOG_BEFORE)
        self.assertIn(m.LEASE_QUERY,m.CATALOG_AFTER)
        self.assertEqual(m.SQL_COMMANDS,{'before':1,'after':1})
        self.assertIn(m.gates.CATALOG,m.CATALOG_BEFORE)

    def test_history47_and_attested48_required(self):
        bad=copy.deepcopy(self.before);bad['migrations'].pop()
        with self.assertRaisesRegex(c.CandidateStop,'history_binding'):self.owner.initial(bad)
        self.owner.initial(self.before)
        with self.assertRaisesRegex(c.CandidateStop,'history_binding'):self.owner.transition(self.before)

    def test_preexisting_candidate_rejected_before_append(self):
        self.before['catalog']['candidate']['table']=[{'oid':'100'}]
        with self.assertRaisesRegex(c.CandidateStop,'preexists'):self.owner.initial(self.before)

    def test_nonempty_controller_before_and_after_denied(self):
        self.before['catalog']['candidate']['empty'][0]['runs_empty']=False
        with self.assertRaises(m.quota.QuotaStop):self.owner.initial(self.before)
        self.before['catalog']['candidate']['empty'][0]['runs_empty']=True
        after=self.ready();after['catalog']['candidate']['empty'][0]['evidence_empty']=False
        with self.assertRaises(m.quota.QuotaStop):self.owner.transition(after)

    def test_unrelated_objects_acl_and_rls_drift_rejected(self):
        after=self.ready()
        for group in ('functions','relations','triggers','policies','constraints'):
            with self.subTest(group=group):
                changed=copy.deepcopy(after);changed['catalog'][group]['999']={'unexpected':True}
                with self.assertRaisesRegex(c.CandidateStop,'unexpected_delta'):self.owner.transition(changed)

    def test_legacy_m44_m45_body_trigger_and_history_preserved(self):
        after=self.ready()
        for key in ('function','trigger','legacy_m44','migration_statements','run_hashes'):
            changed=copy.deepcopy(after);changed['catalog']['m44'][key]=None
            with self.subTest(key=key),self.assertRaisesRegex(c.CandidateStop,'legacy_or_rows'):self.owner.transition(changed)

    def test_exact_table_column_acl_index_invariants(self):
        after=self.ready()
        variants=[('table','rls',False),('table','owner','anon'),('table','acl',[]),
            ('columns','notnull',False),('columns','default_expression','gen_random_uuid()'),
            ('indexes','valid',False),('indexes','opclasses',['public.unsafe'])]
        for group,key,value in variants:
            changed=copy.deepcopy(after);changed['catalog']['candidate'][group][0][key]=value
            with self.subTest(group=group,key=key),self.assertRaises(c.CandidateStop):self.owner.transition(changed)

    def test_function_and_trigger_tampering_rejected(self):
        after=self.ready()
        for group,key,value in [('function','body','begin return null; end'),('function','definer',True),
                ('function','acl',[]),('triggers','enabled','D'),('triggers','definition','select 1')]:
            changed=copy.deepcopy(after);changed['catalog']['candidate'][group][0][key]=value
            with self.subTest(group=group,key=key),self.assertRaises((c.CandidateStop,m.quota.QuotaStop)):
                self.owner.transition(changed)

    def test_lease_exact_rows_caps_identity_expiry_no_duplicates(self):
        after=self.ready()
        for key,value in [('cap',2348),('parent_id',self.artifact['manifest']['cases'][0]['id']),
                ('ci_run','2'),('expiry',START),('binding_sha','0'*64),('whole_seconds',False)]:
            changed=copy.deepcopy(after);changed['catalog']['candidate']['leases'][0][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(c.CandidateStop,'lease_binding'):self.owner.transition(changed)
        after['catalog']['candidate']['leases']*=2
        with self.assertRaisesRegex(c.CandidateStop,'lease_binding'):self.owner.transition(after)

    def test_lease_limit16_sentinel_and_actual_manifest_max14(self):
        cases=[dict(id='e66ba694-6c4a-4dab-b07d-%012x'%i,label='case_'+str(i),cap=2349)
               for i in range(1,16)]
        args=dict(source_commit='a'*40,candidate_sha256='b'*64,github_run='41619169140',
            created_at=START,expires_at=END,sources=self.sources)
        with self.assertRaisesRegex(c.CandidateStop,'candidate_cases'):
            c.prepare(self.root,cases=cases,**args)
        manifest=c.prepare(self.root,cases=cases[:14],**args)
        self.artifact=c.compile_candidate(self.root,manifest,self.samples,now=NOW)
        self.history=h.CaseHistory(self.root,self.sources,local_version='20261103120000',
            local_sql=self.artifact['sql'])
        self.history.attest(self.raw,appended=False)
        self.owner=m.CaseCatalog(self.root,self.sources,self.artifact,self.history)
        after=self.ready()
        self.assertEqual(len(after['catalog']['candidate']['leases']),14)
        query=m.quota.parser().parse_sql(m.LEASE_QUERY)[0].stmt
        self.assertEqual(query.limitCount.val.ival,16)
        for number in (15,16):
            unknown=copy.deepcopy(after['catalog']['candidate']['leases'][0])
            unknown['run_id']='e66ba694-6c4a-4dab-b07d-%012x'%number
            after['catalog']['candidate']['leases'].append(unknown)
            with self.subTest(rows=number),self.assertRaisesRegex(c.CandidateStop,'lease_binding'):
                self.owner.transition(after)
        after['catalog']['candidate']['leases']=after['catalog']['candidate']['leases'][:14]
        self.owner.transition(after)

    def test_check_expression_validation_and_oid_replacement(self):
        after=self.ready()
        for field,value in [('expression','true'),('validated',False)]:
            changed=copy.deepcopy(after);changed['catalog']['m44']['constraint'][field]=value
            with self.subTest(field=field),self.assertRaises(c.CandidateStop):self.owner.transition(changed)
        changed=copy.deepcopy(after);changed['catalog']['m44']['constraint_oid']=20
        with self.assertRaisesRegex(c.CandidateStop,'replaced_constraint'):self.owner.transition(changed)
        changed=copy.deepcopy(after)
        row=next(r for r in changed['catalog']['candidate']['checks'] if r['kind']=='c');row['expression']='true'
        with self.assertRaisesRegex(c.CandidateStop,'constraint_expression'):self.owner.transition(changed)

    def test_post_current_run_receipt_can_change_but_catalog_cannot(self):
        after=self.ready();self.owner.transition(after)
        after['catalog']['m44']['run_hashes']=['0'*64]
        after['catalog']['candidate']['empty'][0]['runs_empty']=False
        self.owner.check_observed(after)
        after['catalog']['relations']['30']['acl']='changed'
        with self.assertRaisesRegex(c.CandidateStop,'post_drift'):self.owner.check_observed(after)

    def test_pg17_primary_key_noinherit_and_unordered_catalog_sets(self):
        after=self.ready()
        primary=next(r for r in after['catalog']['candidate']['checks'] if r['kind']=='p')
        self.assertTrue(primary['noinherit'])
        primary['noinherit']=False
        with self.assertRaisesRegex(c.CandidateStop,'constraint_flags'):self.owner.transition(after)
        primary['noinherit']=True
        self.owner.transition(after)
        for key in ('checks','triggers'):after['catalog']['candidate'][key].reverse()
        after['catalog']['candidate']['table'][0]['acl'].reverse()
        self.owner.check_observed(after)

    def test_deparse_text_interval_and_between_only_semantics(self):
        self.assertEqual(m.expression("purpose='x'"),m.expression("purpose='x'::text"))
        self.assertEqual(m.expression('cap between 1 and 2349'),m.expression('cap>=1 and cap<=2349'))
        self.assertEqual(m.expression("expiry<=starts_at+interval '10 minutes'"),
            m.expression("expiry<=starts_at+'00:10:00'::interval"))
        self.assertNotEqual(m.expression('cap between 1 and 2349'),m.expression('cap>=1 and cap<=2350'))
        self.assertNotEqual(m.expression("purpose='x'::uuid"),m.expression("purpose='x'::text"))

    def test_source_hash_and_loaded_module_binding_no_fallback(self):
        changed=dict(self.sources);changed[m.OWN]='0'*64
        artifact=copy.deepcopy(self.artifact);artifact['manifest']['sources']=changed
        with self.assertRaisesRegex(c.CandidateStop,'source_binding'):m.CaseCatalog(self.root,changed,artifact,self.history)
        with patch.object(m.gates,'__file__',str(self.root/'missing.py')):
            with self.assertRaises(OSError):self.owner.initial(self.before)

    def test_candidate_source_sql_tampering_and_retry_fail_closed(self):
        bad=copy.deepcopy(self.artifact);bad['sql']+='\nselect 1;'
        with self.assertRaisesRegex(c.CandidateStop,'append_binding'):m.CaseCatalog(self.root,self.sources,bad,self.history)
        self.owner.initial(self.before)
        with self.assertRaisesRegex(c.CandidateStop,'initial_once'):self.owner.initial(self.before)
        after=self.after();self.owner.transition(after)
        with self.assertRaisesRegex(c.CandidateStop,'transition_order'):self.owner.transition(after)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--source-root',type=pathlib.Path)
    args,remaining=parser.parse_known_args()
    if args.source_root is not None:ROOT=args.source_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0],*remaining])
