"""Real PG17 parser and mocked native wire; not an actual PostgreSQL result."""
import copy
import hashlib
import json
import os
import pathlib
import sqlite3
import tempfile
import types
import unittest
from unittest.mock import patch

import fixture_producer_scope as m
from fixture_cleanup_runtime import Blocked
from fixture_cleanup_runtime_test import Cursor
from test_fixture_parent_closure import ENV

ROOT = pathlib.Path(__file__).resolve().parents[3]


def contract():
    with tempfile.TemporaryDirectory() as temporary:
        out = pathlib.Path(temporary)
        files = sorted((ROOT/'supabase/migrations').glob('*.sql'))
        sources = {f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
        (out/'candidate.json').write_text(json.dumps({'sources':sources}), encoding='utf-8')
        return m.source_contract(types.SimpleNamespace(sources=ROOT,out=out))


def samples(c):
    value = {'session':[dict.fromkeys(('pg17','statement_bounded','lock_bounded','no_prepared',
                 'tracked','fresh','origin','privileged'),True) | {'pid':123,'cluster_id':'cluster',
                 'postmaster_start':'start','datid':'5'}],
        'relations':[{'name':t,'kind':'r','rls':True,'partition':False,'owner':'postgres',
                      'inherited':False,'rules':False} for t in m.TABLES],
        'privileges':[{'role':r,**dict.fromkeys(('superuser','createrole','elevated_membership',
                       'schema_create','direct_write','private_execute','set_role_write','set_role_indirect_write'),False)}
                      for r in ('supabase_auth_admin','anon','authenticated','service_role')],
        'fks':copy.deepcopy(c['fks']), 'functions':[], 'triggers':[],
        'gates':[dict.fromkeys(('rpc_closed','bridge_closed','windows_closed','identities_empty','operators_empty'),True)],
        'activity':[]}
    triggers = {k:v for k,v in c['triggers'].items() if k[0] in ('auth',m.SCHEMA)}
    for t in m.TABLES:
        triggers[(m.SCHEMA,t,'fmz6e11_tx_observer')] = {'type':29,
                 'function_schema':'fmz6e11_audit_private','function_name':'observe'}
    for (schema,relation,name),fields in triggers.items():
        value['triggers'].append({'schema':schema,'relation':relation,'name':name,**fields,
            'enabled':'O','nargs':0,'argument_bytes':0,'columns':'','unconditional':True,
            'nonconstraint':True,'old_transition':None,'new_transition':None})
    for (schema,name,nargs),fields in c['functions'].items():
        if schema in m.SCHEMAS or (schema=='public' and name in ('fmz6e11_call','fmz_handle_new_auth_user')):
            value['functions'].append({'schema':schema,'name':name,'nargs':nargs,**fields,'auth_execute':False})
    return copy.deepcopy(value)


class Wire:
    autocommit = True
    environment = 'disposable_ci'
    def __init__(self, data):
        self.data, self.calls, self.failure, self.closed = data, [], None, False
    def connect(self): return self
    def clear(self): pass
    def close(self): self.closed = True
    def execute(self,text,args=None):
        phase = next((name for name,sql in m.QUERIES if text == sql.replace('$1','%s')), text)
        self.calls.append(phase)
        if phase == self.failure: raise TimeoutError('do not persist transport secrets')
        return Cursor(copy.deepcopy(self.data.get(phase,[])))


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.contract = contract()
    def setUp(self): self.data = samples(self.contract)
    def validate(self): return m.validate(self.data,self.contract,before=True)
    def test_real_bound_migration_ast_contains_exact_nine_auth_noaction_fks(self):
        result = self.validate()
        self.assertEqual(result['auth_fk_noaction_count'],9)
        self.assertEqual(len(result['tables']),13)
    def test_sql_is_single_parsed_statement_no_query_text_collection(self):
        for name,text in m.QUERIES:
            with self.subTest(name=name):
                self.assertEqual(len(m.parser().parse_sql(text)),1)
        self.assertNotIn('.query',m.ACTIVITY)
        self.assertNotIn('query_start',m.ACTIVITY)
        self.assertIn('limit 257',m.ACTIVITY)
    def test_auth_grant_or_inherited_setrole_is_rejected(self):
        for flag in ('direct_write','private_execute','schema_create','superuser','createrole',
                     'elevated_membership','set_role_write','set_role_indirect_write'):
            with self.subTest(flag=flag):
                self.data = samples(self.contract)
                self.data['privileges'][0][flag] = True
                with self.assertRaisesRegex(Blocked,'unexpected_privilege'): self.validate()
    def test_missing_or_extra_table_cannot_be_thirteen_scope(self):
        self.data['relations'][0]['name'] = 'foreign'
        with self.assertRaisesRegex(Blocked,'exact_thirteen'): self.validate()
    def test_partition_rule_or_inheritance_is_not_covered(self):
        for flag in ('partition','inherited','rules'):
            self.data = samples(self.contract); self.data['relations'][0][flag] = True
            with self.assertRaisesRegex(Blocked,'relation_shape'): self.validate()
    def test_changed_fk_delete_update_validation_and_extra_fk(self):
        for field,value in (('on_delete','c'),('on_update','c'),('validated',False),('target','sessions')):
            self.data = samples(self.contract); self.data['fks'][0][field] = value
            with self.assertRaisesRegex(Blocked,'fk_contract'): self.validate()
        self.data = samples(self.contract); self.data['fks'].append(copy.deepcopy(self.data['fks'][0]))
        with self.assertRaisesRegex(Blocked,'fk_contract'): self.validate()
    def test_changed_trigger_source_identity_mode_and_addition(self):
        for field,value in (('enabled','D'),('type',31),('function_name','evil'),('unconditional',False)):
            self.data = samples(self.contract); self.data['triggers'][0][field] = value
            with self.assertRaisesRegex(Blocked,'changed_trigger'): self.validate()
        self.data = samples(self.contract); self.data['triggers'][0]['name'] = 'unknown'
        with self.assertRaisesRegex(Blocked,'unregistered_trigger'): self.validate()
    def test_removed_observer_is_not_clean(self):
        self.data['triggers'].pop()
        with self.assertRaisesRegex(Blocked,'trigger_missing'): self.validate()
    def test_changed_function_body_definer_path_and_owner(self):
        for field,value in (('body_sha256','0'*64),('definer',not self.data['functions'][0]['definer']),
                             ('config',['search_path=public']),('owner','supabase_auth_admin')):
            self.data = samples(self.contract); self.data['functions'][0][field] = value
            with self.assertRaisesRegex(Blocked,'changed_function'): self.validate()
    def test_changed_function_argument_identity_is_rejected(self):
        f=next(f for f in self.data['functions'] if f['nargs'])
        f['argument_types'][0]['name']='text_not_jsonb'
        with self.assertRaisesRegex(Blocked,'changed_function'): self.validate()
    def catalog_argument(self, oid):
        # Execute the actual parsed projection predicates against PG17 type rows.
        # SQLite is only an in-memory expression harness, not PostgreSQL evidence.
        query = m.parser().parse_sql(m.FUNCTIONS)[0].stmt
        from pglast.stream import RawStream
        arguments = next(t.val.subselect for t in query.targetList if t.name == 'argument_types')
        array_flag = RawStream()(arguments.targetList[0].val.args[-1])
        element_join = RawStream()(arguments.fromClause[0].larg.quals)
        connection = sqlite3.connect(':memory:')
        try:
            connection.execute('create table pg_type(oid integer primary key,typname text,typelem integer,typarray integer)')
            # Scalar name has typelem=char, but char.typarray is NOT name's OID.
            connection.executemany('insert into pg_type values(?,?,?,?)',
                [(18,'char',0,1002),(19,'name',18,1003),(1003,'_name',19,0)])
            rows = connection.execute('select at.typname, '+array_flag+
                ' from pg_type t join pg_type at on '+element_join+' where t.oid=?', (oid,)).fetchall()
            self.assertEqual(len(rows),1)
            self.assertIn(rows[0][1],(0,1))
            return {'schema':'pg_catalog','name':rows[0][0],'array':bool(rows[0][1])}
        finally:
            connection.close()
    def test_catalog_scalar_name_matches_bound_attach_contract(self):
        argument = self.catalog_argument(19)
        self.assertEqual(argument,{'schema':'pg_catalog','name':'name','array':False})
        function = next(f for f in self.data['functions']
                        if f['schema']=='fmz6e11_audit_private' and f['name']=='attach')
        self.assertEqual(function['argument_types'][1:],[argument,argument])
        function['argument_types'][1:] = [argument,argument]
        self.validate()
    def test_catalog_name_array_matches_bound_project_key_contract(self):
        argument = self.catalog_argument(1003)
        self.assertEqual(argument,{'schema':'pg_catalog','name':'name','array':True})
        function = next(f for f in self.data['functions']
                        if f['schema']=='fmz6e11_audit_private' and f['name']=='project_key')
        self.assertEqual(function['argument_types'][1],argument)
        function['argument_types'][1] = argument
        self.validate()
    def test_auth_callable_definer_not_whitelisted_by_source_hash_alone(self):
        next(f for f in self.data['functions'] if f['schema']==m.SCHEMA)['auth_execute'] = True
        with self.assertRaisesRegex(Blocked,'auth_callable'): self.validate()
    def test_rpc_activation_or_nonempty_bootstrap_is_blocked(self):
        for field in self.data['gates'][0]:
            self.data = samples(self.contract); self.data['gates'][0][field] = False
            with self.assertRaisesRegex(Blocked,'rpc_or_bootstrap_open'): self.validate()
    def test_running_and_idle_external_postgres_are_both_blocked(self):
        for state in ('active','idle','idle in transaction'):
            self.data['activity'] = [{'pid':11,'state':state,'usename':'postgres'}]
            with self.assertRaisesRegex(Blocked,'external_backend'): self.validate()
    def test_metadata_overflow_does_not_turn_into_empty_inventory(self):
        self.data['activity'] = [{}]*257
        with self.assertRaisesRegex(Blocked,'metadata_bound'): self.validate()


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.contract = contract()
    def setUp(self):
        self.saved = {}
        self.wire = Wire(samples(self.contract))
        self.gate = types.SimpleNamespace(out=pathlib.Path.cwd(),container='supabase_db_fmz-db41-ci',save=self.save)
        for context in (patch.dict(os.environ,ENV),patch.object(m.binding,'verify',return_value={'bound':True}),
                        patch.object(m,'source_contract',return_value=self.contract),
                        patch.object(m.NativeRuntime,'disposable',return_value=self.wire)):
            context.start(); self.addCleanup(context.stop)
        self.scope = m.Scope(self.gate)
    def save(self,name,value):
        if name in self.saved: raise FileExistsError(name)
        self.saved[name] = copy.deepcopy(value)
    def test_ten_commands_charged_before_each_dispatch_no_barrier_claim(self):
        execute = self.wire.execute
        def check(text,args=None):
            charges = [k for k in self.saved if '-charge-' in k]
            self.assertEqual(len(charges),len(self.wire.calls)+1)
            return execute(text,args)
        self.wire.execute = check
        result = self.scope.before_bootstrap()
        self.assertEqual((result['admitted_attempts'],result['emitted_attempts']),(10,10))
        self.assertFalse(result['mutation_admitted']); self.assertFalse(result['physical_exclusion_held'])
        self.assertEqual(self.wire.calls[-1],'ROLLBACK')
    def test_every_query_failure_rolls_back_no_retry_preserves_primary(self):
        for phase,_ in m.QUERIES:
            with self.subTest(phase=phase):
                self.saved.clear(); self.wire.calls.clear(); self.wire.failure=phase
                scope=m.Scope(self.gate)
                with self.assertRaises(TimeoutError): scope.before_bootstrap()
                self.assertEqual(self.wire.calls[-1],'ROLLBACK')
                self.assertEqual(self.wire.calls.count(phase),1)
                self.assertLessEqual(len(self.wire.calls),10)
                self.assertNotIn('transport secrets',json.dumps(self.saved))
    def test_lost_begin_also_rollback(self):
        self.wire.failure='BEGIN TRANSACTION READ ONLY'
        with self.assertRaises(TimeoutError): self.scope.before_bootstrap()
        self.assertEqual(self.wire.calls,['BEGIN TRANSACTION READ ONLY','ROLLBACK'])
    def test_rollback_failure_has_no_success_receipt(self):
        self.wire.failure='ROLLBACK'
        with self.assertRaises(TimeoutError): self.scope.before_bootstrap()
        self.assertEqual(self.saved['fixture-producer-scope-before-result.json']['status'],'NO_GO')
    def test_storage_failure_poison_prevents_unrecorded_continuation(self):
        save=self.gate.save
        def fail(name,value):
            if name.endswith('charge-003.json'): raise OSError('fsync')
            save(name,value)
        self.gate.save=fail
        with self.assertRaises(OSError): self.scope.before_bootstrap()
        self.assertEqual(len(self.wire.calls),2)
        self.assertTrue(self.wire.closed)
    def test_duplicate_and_missing_baseline_do_not_dispatch(self):
        with self.assertRaisesRegex(Blocked,'before_bootstrap'): self.scope.after_mint_closure({})
        self.scope.before_bootstrap()
        with self.assertRaisesRegex(Blocked,'duplicate'): self.scope.before_bootstrap()
        self.assertEqual(len(self.wire.calls),10)
    def test_after_requires_terminal_and_same_cluster(self):
        self.scope.before_bootstrap()
        self.wire.data['session'][0]['cluster_id']='other'
        terminal={'preparation_run':m.NEW_RUN,'db_terminality_proven':True,
                  'classification':'TRACKED_DB_BACKENDS_TERMINAL'}
        with patch.object(m,'reference',return_value=terminal):
            with self.assertRaisesRegex(Blocked,'baseline_changed'): self.scope.after_mint_closure({'path':'terminal'})
        self.assertEqual(len(self.wire.calls),20)
    def test_protocol_reserves_rollback_slot(self):
        meter=m.Meter(self.save,'partial',2)
        meter.query(self.wire,'begin','BEGIN')
        with self.assertRaisesRegex(Blocked,'protocol_limit'): meter.query(self.wire,'read','SELECT 1')
        meter.query(self.wire,'rollback','ROLLBACK',reserve=0)
        self.assertEqual(meter.used,2)


if __name__ == '__main__': unittest.main()
