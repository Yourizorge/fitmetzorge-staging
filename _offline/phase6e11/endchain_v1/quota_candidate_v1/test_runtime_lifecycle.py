"""Offline lifecycle transport models; no DB/Docker/Auth or admission proof."""
import argparse
import copy
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p/'supabase/migrations').is_dir()), None)
RUNTIME_ROOT = HERE
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root', type=pathlib.Path, default=ROOT)
    parser.add_argument('--runtime-root', type=pathlib.Path, default=HERE)
    options, remaining = parser.parse_known_args()
    ROOT, RUNTIME_ROOT = options.source_root, options.runtime_root
    sys.argv = [sys.argv[0], *remaining]
if ROOT is None:
    raise RuntimeError('isolated tests require --source-root and --runtime-root')
sys.path.insert(0, str(ROOT/'_offline/phase6e11/endchain_v1'))
sys.path.insert(0, str(RUNTIME_ROOT.parent))
import quota_candidate_v1
spec = importlib.util.spec_from_file_location('quota_candidate_v1.runtime_lifecycle',
                                               HERE/'runtime_lifecycle.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
import integral_io

RUN = '8bc257ad-77ec-46a8-b9a3-82c081f54eaa'
IDS = {'a_member':'00000000-0000-4000-8000-000000000001',
       'a_trainer':'00000000-0000-4000-8000-000000000002',
       'b_member':'00000000-0000-4000-8000-000000000003'}
SCHEMAS = ['fmz6e11_guard_'+RUN.replace('-',''), 'fmz6e11_am_'+RUN.replace('-','')]
ABSENCE = {name:0 for name in ('temporary_schemas','sessions','refresh_tokens','windows',
    'workspaces','participants','all_test_windows','all_test_workspaces','all_test_participants',
    'all_registered_sessions','all_registered_refresh_tokens')}
ACCESS = {name:True for name in ('database_ok','role_ok','pg17','ssl','registered','private_functions_safe')}


class Meter:
    def __init__(self):
        self.stopped = self.closed = False
        self.stops = []
        self.phases = {'preflight':0}
        self.events = []
    def charge(self, phase, count, *, action):
        self.phases[phase] += count
        self.events.append(dict(phase=phase,commands=count,action=action,confirmed=False))
        return len(self.events)
    def confirm(self, ticket):
        self.events[ticket-1]['confirmed'] = True
    def safety(self, action, count):
        self.events.append(dict(phase='safety',commands=count,action=action,confirmed=False))
        return len(self.events)
    confirm_safety = confirm
    def stop(self, reason):
        self.stopped = True
        self.stops.append(reason)


class History:
    local_version = '20261103120000'
    inspect_versions = ['20261018070231', '20261103120000']
    def __init__(self):
        self.before = self.after = None
    @staticmethod
    def safe(appended):
        return [dict(version=str(i),name='synthetic',sql_sha='a'*64)
                for i in range(48 if appended else 47)]
    def attest(self, rows, *, appended):
        safe = self.safe(appended)
        if len(rows) != len(safe):
            raise ValueError('synthetic_history_count')
        if appended:
            self.after = safe
        else:
            self.before = safe
        return dict(migrations=safe, history_count=len(safe))
    def check_observed(self, rows):
        if rows != self.after:
            raise ValueError('synthetic_history_drift')


class Catalog:
    def __init__(self, history):
        self.history = history
        self.artifact = {'manifest': {'sources': {}}}
        self.before = self.after = None
    def initial(self, value):
        self.before = copy.deepcopy(value)
        return {'status':'INITIAL47_VALIDATED','hash':'b'*64}
    def transition(self, value):
        self.after = copy.deepcopy(value)
        return {'status':'LOCAL48_DELTA_VALIDATED','hash':'c'*64}
    def check_observed(self, value):
        if value != self.after:
            raise ValueError('synthetic_catalog_drift')
        return {'status':'LOCAL48_CATALOG_UNCHANGED','hash':'d'*64}


class Stream:
    version = History.local_version
    run_id = RUN
    manifest_sha = 'e'*64
    def __init__(self):
        self.calls = []
        self.failure = None
        self.rollback_error = None
    def run(self, query, save, ids, context, label, expected):
        self.calls.append((label, copy.deepcopy(expected)))
        query('stream_'+label+'_begin', 'BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        primary = None
        try:
            if self.failure:
                raise self.failure
            for _ in range(39):
                query('stream_'+label+'_model', 'SELECT 1')
        except BaseException as error:
            primary = error
            raise
        finally:
            try:
                query('stream_'+label+'_rollback', 'ROLLBACK')
            except BaseException as error:
                if primary is None:
                    raise
                primary.add_note('rollback_failed:'+type(error).__name__)
        return dict(protocol_commands=41, tables={'synthetic':{}}, protected_equal=True)


class Cursor:
    def __init__(self, rows):
        self.description = bool(rows)
        self.rowcount = len(rows)
        self.rows = rows
    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, fixture):
        self.f = fixture
        self.info = types.SimpleNamespace(transaction_status=0)
        self.closed = False
        self.rollbacks = 0
    def execute(self, bound, params):
        f = self.f
        row = f.c.commands[-1]
        text, phase = row['sql'], row['phase']
        f.dispatches.append(dict(phase=phase,sql=text,safety=f.c.safety_label,
                                prepaid=row['prepaid']))
        if text.startswith('BEGIN '):
            self.info.transaction_status = 2
        if text == 'ROLLBACK':
            self.rollbacks += 1
        if f.driver_failure and f.driver_failure(phase, text):
            raise f.rollback_error if text == 'ROLLBACK' and f.rollback_error else f.primary
        if text == 'ROLLBACK':
            self.info.transaction_status = 0
            return Cursor([])
        if text.startswith('EXPLAIN '):
            target = text.split(') ',1)[1]
            qid = f.qid(target)
            plan = {'Query Identifier':qid}
            if text.startswith('EXPLAIN (ANALYZE'):
                plan.update(Plan={'Actual Rows':1,'WAL Bytes':0,'Temp Written Blocks':0},
                            **{'Execution Time':0.1})
            return Cursor([{'QUERY PLAN':[plan]}])
        if text == integral_io.SNAPSHOT:
            selected = set(json.loads(params[0]))
            values = [dict(queryid=str(q),calls=n,since='fixed',temp_read=0,
                           temp_written=f.temp.get(q,0),wal=str(f.wal.get(q,0)),
                           exec_ms=0.1*n)
                      for q,n in f.calls.items() if str(q) in selected]
            result = [{'value':{'reset':'fixed','dealloc':0,'statements':values,
                'background':{'temp_bytes':0,'reset':'fixed'},
                'health':{'io_wait':0,'long_active':0}}}]
        elif text == m.gates.ACCESS:
            result = [dict(ACCESS)]
        elif text == m.runtime_history.MIGRATIONS:
            result = [dict(row,source_statements=['PRIVATE_SOURCE_SENTINEL'])
                for row in History.safe('after_migration' in phase)]
        elif text in (m.runtime_catalog.CATALOG_BEFORE,m.runtime_catalog.CATALOG_AFTER):
            result = [{'value':{'source_body':'PRIVATE_SOURCE_SENTINEL','objects':'stable'}}]
        elif text == m.gates.ABSENCE:
            result = [dict(ABSENCE)]
        elif text == m.FINAL:
            stage = 'pre' if phase.startswith('gates_final_pre_') else 'post'
            value = {'access':dict(ACCESS),'migrations':History.safe(True),
                'catalog':{'source_body':'PRIVATE_SOURCE_SENTINEL','objects':'stable'},
                'absence':dict(ABSENCE,temporary_schemas=2 if stage=='pre' else 0),
                'temporary_schema_names':sorted(SCHEMAS) if stage=='pre' else [],
                'readonly':True,'statement_timeout':'5s','lock_timeout':'1s'}
            f.final_args.append((stage,params))
            result = [{'value':value}]
        elif 'transaction_read_only' in text:
            result = [{'readonly':True}]
        else:
            result = []
        if f.metadata_provider:
            result = f.metadata_provider(phase,text,result)
        if text == m.FINAL and f.final_mutation:
            f.final_mutation(result[0]['value'])
        if text in f.qids:
            qid = f.qid(text)
            f.calls[qid] = f.calls.get(qid,0)+1
            if f.wal_text == text:
                f.wal[qid] = f.wal.get(qid,0)+1
            if f.temp_text == text:
                f.temp[qid] = f.temp.get(qid,0)+1
        return Cursor(result)
    def close(self):
        if self.f.close_error:
            raise self.f.close_error
        self.closed = True


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.qids,self.calls,self.wal,self.temp = {},{},{},{}
        self.wal_text = self.temp_text = None
        self.driver_failure = self.final_mutation = self.before_failure = self.after_failure = None
        self.metadata_provider = None
        self.close_error = self.save_error = None
        self.rollback_error = None
        self.primary = RuntimeError('primary')
        self.saved,self.dispatches,self.connections,self.final_args = {},[],[],[]
        self.order = []
        self.history = History()
        self.stream = Stream()
        self.catalog = Catalog(self.history)
        self.c = types.SimpleNamespace(quota={'root':str(ROOT),'binding':{
                'run_id':RUN,'binding_sha':'e'*64},'manifest':{'sources':{}}},
            meter=Meter(),commands=[],safety_label=None,preflight_admitted=False,
            gate_baseline=None,preservation_baseline=None,fixture_context={'window':RUN},
            final_attempted=set(),final_pre_complete=False,final_dry_complete=False,
            final_post_complete=False,case_prefix_ready=False)
        self.c.abort = self.c.meter.stop
        def before(phase, text):
            if self.before_failure and self.before_failure(phase,text):
                raise self.primary
            self.c.commands.append({'phase':phase,'sql':text,'prepaid':True,'confirmed':False})
        def after(phase,text):
            self.c.commands[-1]['confirmed'] = True
            if self.after_failure and self.after_failure(phase,text):
                raise self.primary
        self.c.before_sql,self.c.after_sql = before,after
        def connect():
            value=Connection(self);self.connections.append(value);return value
        self.runtime=types.SimpleNamespace(environment='disposable_ci',connect=connect)
        self.c.native_runtime=lambda gate:self.runtime
        def admit(value):
            self.order.append('preflight');self.c.preflight_admitted=True
        self.c.admit_preflight=admit
        self.c.temporary_absence_confirmed=lambda:self.order.append('absence')
        def final_cleanup():
            self.order.append('final_cleanup')
            self.c.final_post_complete=True
        self.c.final_cleanup_confirmed=final_cleanup
        self.base_gate=types.SimpleNamespace()
        self.prefix=types.SimpleNamespace(gate=self.base_gate,composition=self.c,attempts=[],
            cli_protocol=[],version=History.local_version)
        def quota():
            self.order.append('quota72');self.prefix.attempts.append('quota')
            self.prefix.cli_protocol.append({'slot':'quota'})
        self.prefix.run_pending=quota
        def dry(gate):
            self.order.append('pre_auth36');self.prefix.attempts.append('pre_auth')
            self.prefix.cli_protocol.append({'slot':'pre_auth'})
        self.c.pre_auth_dry_run=dry
        def save(name,value):
            if self.save_error and self.save_error(name):
                raise OSError('storage')
            self.saved[name]=copy.deepcopy(value)
        self.gate=types.SimpleNamespace(prefix=self.prefix,_gate=self.base_gate,
            cli_protocol=self.prefix.cli_protocol,sources=ROOT.resolve(),save=save)
        self.lifecycle=types.SimpleNamespace(composition=self.c,gate=self.gate,
            installed=False,worker_owned=False,failed=False,removed=False,ids=IDS,run_id=RUN,
            guard=types.SimpleNamespace(scope=lambda run,ids:SCHEMAS[0]),
            audit=types.SimpleNamespace(scope=lambda run,ids:SCHEMAS[1]))
        self.owner=m.CasePreservation(self.c,history=self.history,stream=self.stream,catalog=self.catalog)
        self.c.case_history,self.c.case_preservation=self.history,self.owner
        self.preflight_patch=patch.object(m.runtime_history,'preflight',self.preflight)
        self.preflight_patch.start();self.addCleanup(self.preflight_patch.stop)

    def qid(self,text):
        if text not in self.qids:
            self.qids[text]=len(self.qids)+1
        return self.qids[text]

    def preflight(self,runtime,meter,history,save):
        history.before=History.safe(False)
        return {'complete':True,'migrations':history.before}

    def prefix_run(self):
        self.owner.prepare_prefix(self.gate,self.lifecycle,self.prefix)

    def after_prefix(self):
        self.prefix_run()
        self.c.case_prefix_ready=True
        self.owner.run(self.gate,IDS,'before_cleanup')

    def test_actual_queryio_counts_and_source_slots_47_to_48(self):
        self.prefix_run()
        phases=[r['phase'] for r in self.dispatches]
        self.assertEqual(sum(p.startswith('gates_before_') for p in phases),20)
        self.assertEqual(sum(p.startswith('gates_after_migration_') for p in phases),20)
        self.assertEqual(sum(p.startswith('stream_before_') for p in phases),41)
        self.assertEqual(self.order,['preflight','quota72','pre_auth36'])
        self.assertEqual(len(self.c.gate_baseline['migrations']),48)
        self.assertTrue(all(r['prepaid'] for r in self.dispatches))
        self.assertTrue(all(c.closed for c in self.connections))
        self.assertEqual([c.rollbacks for c in self.connections],[2,1])
        self.assertNotIn('PRIVATE_SOURCE_SENTINEL',json.dumps(self.saved))
        self.assertFalse(self.lifecycle.installed)
        self.assertFalse(self.lifecycle.worker_owned)

    def test_three_streams_and_final11_9_without_extra_stream(self):
        self.after_prefix()
        pre=self.owner.run(self.gate,IDS,'after_cleanup')
        self.assertEqual((pre['commands'],pre['stream_commands'],pre['gate_commands']),(52,41,11))
        self.assertTrue(self.c.final_pre_complete)
        self.c.final_dry_complete=True
        self.lifecycle.removed=True
        post=self.owner.run(self.gate,IDS,'final_post')
        self.assertEqual((post['commands'],post['stream_commands'],post['gate_commands']),(9,0,9))
        self.assertEqual([r[0] for r in self.stream.calls],['before','before_cleanup','after_cleanup'])
        self.assertEqual(self.order[-2:],['absence','final_cleanup'])
        self.assertTrue(self.c.final_post_complete)
        for stage,params in self.final_args:
            args=m.gates.final_parameters(IDS,self.c.fixture_context,stage)
            self.assertEqual(args[0],SCHEMAS if stage=='pre' else [])
            self.assertEqual(args[3],SCHEMAS)
            self.assertEqual(params,m.bind_parameters(m.FINAL,args)[1])

    def test_every_metadata_binding_is_readonly_in_real_queryio(self):
        self.after_prefix()
        self.owner.run(self.gate,IDS,'after_cleanup')
        for name,value in self.saved.items():
            if name.startswith('integral-gates-') and 'io' in value:
                self.assertTrue(all(v['readonly'] is True for v in value['io']['source_classes'].values()))
        self.assertIn(m.runtime_catalog.CATALOG_AFTER,m.FINAL)

    def test_no_prefix_or_before_retry_and_no_worker_prefix(self):
        self.prefix_run()
        count=len(self.dispatches)
        with self.assertRaisesRegex(ValueError,'prefix_retry'):self.prefix_run()
        with self.assertRaisesRegex(ValueError,'sequence_or_retry'):
            self.owner.run(self.gate,IDS,'before')
        self.assertEqual(len(self.dispatches),count)

    def test_prefix_wrong_gate_or_worker_owned_fails_before_sql(self):
        self.lifecycle.worker_owned=True
        with self.assertRaisesRegex(ValueError,'lifecycle_binding'):self.prefix_run()
        self.assertFalse(self.dispatches)
        self.lifecycle.worker_owned=False
        self.prefix.gate=object()
        with self.assertRaisesRegex(ValueError,'prefix_binding'):self.prefix_run()
        self.assertFalse(self.dispatches)

    def test_lost_begin_response_has_one_safety_rollback(self):
        self.driver_failure=lambda phase,text:text.startswith('BEGIN ')
        with self.assertRaises(RuntimeError) as caught:self.prefix_run()
        self.assertIs(caught.exception,self.primary)
        self.assertEqual(self.connections[0].rollbacks,1)
        self.assertEqual(self.dispatches[-1]['safety'],'rollback_reader')
        self.assertTrue(self.connections[0].closed)
        self.assertTrue(self.c.meter.stopped)

    def test_rollback_failure_is_not_retried_and_primary_survives_close_save(self):
        self.stream.failure=self.primary
        self.rollback_error=OSError('different_rollback_failure')
        self.driver_failure=lambda phase,text:text=='ROLLBACK'
        self.close_error=LookupError('close')
        self.save_error=lambda name:name.endswith('-stop.json')
        with self.assertRaises(RuntimeError) as caught:self.prefix_run()
        self.assertIs(caught.exception,self.primary)
        self.assertEqual(self.connections[0].rollbacks,1)
        notes=getattr(caught.exception,'__notes__',[])
        self.assertTrue(any('rollback_failed:OSError' in n for n in notes))
        self.assertTrue(any('close_secondary' in n for n in notes))
        self.assertTrue(any('stop_receipt_secondary' in n for n in notes))

    def test_gate_lost_begin_response_rolls_back_without_repeating_stream(self):
        self.driver_failure=lambda phase,text:phase=='gates_before_begin'
        with self.assertRaises(RuntimeError) as caught:self.prefix_run()
        self.assertIs(caught.exception,self.primary)
        self.assertEqual(self.connections[0].rollbacks,2)
        self.assertEqual([x[0] for x in self.stream.calls],['before'])

    def test_confirmed_rollback_after_hook_failure_never_repeats(self):
        self.after_failure=lambda phase,text:phase=='gates_before_rollback'
        with self.assertRaises(RuntimeError) as caught:self.prefix_run()
        self.assertIs(caught.exception,self.primary)
        self.assertEqual(self.connections[0].rollbacks,2)
        self.assertTrue(self.connections[0].closed)

    def test_readonly_wal_is_not_waived_and_failure_telemetry_safe(self):
        self.wal_text=m.gates.ACCESS
        self.save_error=lambda name:name.endswith('-io-failure.json')
        with self.assertRaisesRegex(ValueError,'io_read_wal') as caught:self.prefix_run()
        self.assertTrue(any('io_receipt_secondary' in n for n in caught.exception.__notes__))
        self.assertTrue(self.c.meter.stopped)
        self.assertEqual(self.connections[0].rollbacks,2)
        self.assertFalse(self.c.final_pre_complete)

    def test_temp_spill_still_fails(self):
        self.temp_text=m.gates.ACCESS
        with self.assertRaisesRegex(ValueError,'io_own_spill'):self.prefix_run()

    def test_final_post_requires_dry_and_sequence(self):
        self.after_prefix();self.owner.run(self.gate,IDS,'after_cleanup')
        count=len(self.dispatches)
        with self.assertRaisesRegex(ValueError,'final_sequence'):
            self.owner.run(self.gate,IDS,'final_post')
        self.assertEqual(len(self.dispatches),count)

    def test_final_metadata_fault_retains_guard_reserves_until_validation(self):
        self.after_prefix();self.owner.run(self.gate,IDS,'after_cleanup')
        self.c.final_dry_complete=True
        self.after_failure=lambda phase,text:phase=='gates_final_post_metadata'
        with self.assertRaises(RuntimeError) as caught:
            self.owner.run(self.gate,IDS,'final_post')
        self.assertIs(caught.exception,self.primary)
        self.assertNotIn('absence',self.order)
        self.assertFalse(self.c.final_post_complete)
        self.assertEqual(self.connections[-1].rollbacks,1)

    def test_final_bad_scope_or_timeout_never_releases(self):
        self.after_prefix()
        self.final_mutation=lambda value:value.update(statement_timeout='6s')
        with self.assertRaisesRegex(ValueError,'final_readonly_limits'):
            self.owner.run(self.gate,IDS,'after_cleanup')
        self.assertFalse(self.c.final_pre_complete)
        self.assertNotIn('absence',self.order)

    def test_no_flag_on_connection_close_failure(self):
        self.after_prefix()
        self.close_error=RuntimeError('close_primary')
        with self.assertRaises(RuntimeError) as caught:
            self.owner.run(self.gate,IDS,'after_cleanup')
        self.assertIs(caught.exception,self.close_error)
        self.assertFalse(self.c.final_pre_complete)
        self.assertTrue(self.c.meter.stopped)

    def test_gate_error_keeps_original_phase_after_cleanup(self):
        self.driver_failure=lambda phase,text:phase=='gates_before_access'
        self.rollback_error=OSError('rollback_secondary')
        self.close_error=LookupError('close_secondary')
        with self.assertRaises(RuntimeError) as caught:self.prefix_run()
        self.assertIs(caught.exception,self.primary)
        self.assertEqual(self.saved['integral-preservation-before-stop.json']['phase'],
                         'gates_before_access')

    def test_readonly_metadata_sql_is_exactly_one_select(self):
        from admission_quota_readonly import parser
        for sql in (m.FINAL,m.runtime_catalog.CATALOG_BEFORE,m.runtime_catalog.CATALOG_AFTER,
                    m.runtime_history.MIGRATIONS):
            nodes=parser().parse_sql(sql)
            self.assertEqual(len(nodes),1)
            self.assertEqual(type(nodes[0].stmt).__name__,'SelectStmt')



class PreflightConnection:
    """Only transport is synthetic; runtime_history.preflight itself is unchanged."""
    def __init__(self, fixture, rows):
        self.fixture,self.rows=fixture,copy.deepcopy(rows)
        self.trace=[]
        self.closed=False
    def execute(self, sql, params=None):
        meter=self.fixture.c.meter
        assert meter.events and not meter.events[-1]['confirmed']
        self.trace.append(sql)
        if sql == m.runtime_history.GUARD:
            return Cursor([dict(ro='on',db='postgres',role='postgres',ssl=True)])
        if 'source_statements' in sql:
            return Cursor(copy.deepcopy(self.rows))
        return Cursor([])
    def close(self):
        self.closed=True


class RealCatalogIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from quota_candidate_v1 import test_runtime_catalog as fixtures
        cls.fixtures=fixtures
        fixtures.ROOT=ROOT
        fixtures.CatalogTests.setUpClass()
        cls.addClassCleanup(fixtures.CatalogTests.tearDownClass)

    def setUp(self):
        data=self.fixtures.CatalogTests()
        data.setUp()
        self.before=copy.deepcopy(data.before)
        self.after=data.after()
        self.raw_before=copy.deepcopy(data.raw)
        sql=data.artifact['sql']
        self.raw_after=[*copy.deepcopy(data.raw),dict(
            version=data.history.local_version,name='disposable_case_quota_v1',
            sql_sha=self.fixtures.c.sha(sql.encode()),source_statements=[sql])]
        self.data=data
        self.f=LifecycleTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.f.preflight_patch.stop()
        self.f.history=m.runtime_history.CaseHistory(
            data.root,data.sources,local_version=data.history.local_version,local_sql=sql)
        self.f.catalog=m.runtime_catalog.CaseCatalog(
            data.root,data.sources,data.artifact,self.f.history)
        manifest=data.artifact['manifest']
        run_id=manifest['cases'][0]['id']
        c=self.f.c
        c.quota={'root':str(data.root),'manifest':copy.deepcopy(manifest),'binding':{
            'run_id':run_id,'binding_sha':self.fixtures.c.sha(self.fixtures.c.canonical(manifest))}}
        self.f.stream.run_id=run_id
        self.f.stream.manifest_sha=c.quota['binding']['binding_sha']
        self.f.gate.sources=data.root
        self.f.lifecycle.run_id=run_id
        schemas=['fmz6e11_guard_'+run_id.replace('-',''),'fmz6e11_am_'+run_id.replace('-','')]
        self.f.lifecycle.guard.scope=lambda run,ids:schemas[0]
        self.f.lifecycle.audit.scope=lambda run,ids:schemas[1]
        self.f.owner=m.CasePreservation(c,history=self.f.history,stream=self.f.stream,
                                        catalog=self.f.catalog)
        c.case_history,c.case_preservation=self.f.history,self.f.owner
        self.preflight_connection=PreflightConnection(self.f,self.raw_before)
        original_connect=self.f.runtime.connect
        def connect():
            if not c.preflight_admitted:
                return self.preflight_connection
            return original_connect()
        self.f.runtime.connect=connect

        def metadata(phase,text,default):
            if text == m.runtime_history.MIGRATIONS:
                return copy.deepcopy(self.raw_after if 'after_migration' in phase else self.raw_before)
            if text == m.runtime_catalog.CATALOG_BEFORE:
                return [{'value':copy.deepcopy(self.before['catalog'])}]
            if text == m.runtime_catalog.CATALOG_AFTER:
                return [{'value':copy.deepcopy(self.after['catalog'])}]
            if text == m.FINAL:
                value=default[0]['value']
                value['migrations']=copy.deepcopy(self.after['migrations'])
                value['catalog']=copy.deepcopy(self.after['catalog'])
                value['temporary_schema_names']=sorted(schemas) if 'final_pre_' in phase else []
            return default
        self.f.metadata_provider=metadata

    def final_pre(self):
        self.f.after_prefix()
        return self.f.owner.run(self.f.gate,IDS,'after_cleanup')

    def test_real_47_48_catalog_history_and_final20_11_9(self):
        pre=self.final_pre()
        self.assertEqual(pre['gate_commands'],11)
        self.assertEqual(len(self.preflight_connection.trace),4)
        self.assertTrue(self.preflight_connection.closed)
        self.assertEqual(self.f.c.meter.phases['preflight'],4)
        self.assertTrue(all(e['confirmed'] for e in self.f.c.meter.events))
        self.assertEqual(len(self.f.history.before),47)
        self.assertEqual(len(self.f.history.after),48)
        self.assertEqual(self.f.c.gate_baseline['migrations'],self.f.history.after)
        for label in ('before','after_migration'):
            self.assertEqual(sum(r['phase'].startswith('gates_'+label+'_')
                                 for r in self.f.dispatches),20)
        self.f.c.final_dry_complete=True
        self.f.lifecycle.removed=True
        post=self.f.owner.run(self.f.gate,IDS,'final_post')
        self.assertEqual(post['gate_commands'],9)
        self.assertEqual(post['stream_commands'],0)
        self.assertTrue(self.f.c.final_pre_complete)
        self.assertTrue(self.f.c.final_post_complete)
        self.assertEqual(self.f.order[-2:],['absence','final_cleanup'])
        self.assertEqual([v[0] for v in self.f.stream.calls],['before','before_cleanup','after_cleanup'])
        for name,value in self.f.saved.items():
            if name.startswith('integral-gates-') and 'io' in value:
                self.assertEqual(value['io']['last_pair']['own_wal_bytes'],0)
                self.assertEqual(value['io']['last_pair']['own_temp_written'],0)
        exported=json.dumps(self.f.saved)
        for forbidden in ('"source_statements":','"migration_statements":','CREATE FUNCTION','begin return'):
            self.assertFalse(forbidden in exported,'raw source field/body exported: '+forbidden)
        receipt=self.f.saved['integral-gates-final_pre.json']
        self.assertEqual(receipt['catalog_sha'],m.gates.digest(self.after['catalog']))

    def test_real_catalog_final_acl_drift_stops_before_absence_release(self):
        self.final_pre()
        self.f.c.final_dry_complete=True
        self.f.final_mutation=lambda value:value['catalog']['relations']['30'].update(acl='changed')
        with self.assertRaisesRegex(self.fixtures.c.CandidateStop,'post_drift'):
            self.f.owner.run(self.f.gate,IDS,'final_post')
        self.assertNotIn('absence',self.f.order)
        self.assertFalse(self.f.c.final_post_complete)
        self.assertEqual(self.f.connections[-1].rollbacks,1)

    def test_real_history_final_missing48_is_not_legacy45_success(self):
        self.f.after_prefix()
        self.f.final_mutation=lambda value:value.update(migrations=value['migrations'][:45])
        with self.assertRaisesRegex(self.fixtures.c.CandidateStop,'lifecycle_drift'):
            self.f.owner.run(self.f.gate,IDS,'after_cleanup')
        self.assertFalse(self.f.c.final_pre_complete)

    def test_raw_added_history_statement_tamper_fails_before_append(self):
        self.raw_before[-1]['source_statements']=['select 1']
        # The real preflight receives its own original list; the before gate sees the altered list.
        with self.assertRaisesRegex(self.fixtures.c.CandidateStop,'statement_mismatch'):
            self.f.prefix_run()
        self.assertNotIn('quota72',self.f.order)
        self.assertTrue(self.f.c.meter.stopped)

    def test_unknown_lease_row_rejected_by_real_catalog_transition(self):
        row=copy.deepcopy(self.after['catalog']['candidate']['leases'][0])
        row['run_id']='00000000-0000-4000-8000-000000000099'
        self.after['catalog']['candidate']['leases'].append(row)
        with self.assertRaisesRegex(self.fixtures.c.CandidateStop,'lease_binding'):
            self.f.prefix_run()
        self.assertNotIn('pre_auth36',self.f.order)
        self.assertTrue(self.f.c.meter.stopped)

    def test_real_catalog_metadata_still_rejects_wal_and_preserves_first_error(self):
        self.f.wal_text=m.runtime_catalog.CATALOG_AFTER
        self.f.save_error=lambda name:name.endswith('-io-failure.json')
        with self.assertRaisesRegex(ValueError,'io_read_wal') as caught:
            self.f.prefix_run()
        self.assertTrue(any('io_receipt_secondary' in n for n in caught.exception.__notes__))
        self.assertTrue(self.f.c.meter.stopped)

    def test_final_global_registered_session_nonzero_is_not_catalog_success(self):
        self.final_pre()
        self.f.c.final_dry_complete=True
        self.f.final_mutation=lambda value:value['absence'].update(all_registered_sessions=1)
        with self.assertRaisesRegex(ValueError,'lifecycle_cleanup_incomplete'):
            self.f.owner.run(self.f.gate,IDS,'final_post')
        self.assertNotIn('absence',self.f.order)
        self.assertFalse(self.f.c.final_post_complete)

    def test_final_post_leftover_temporary_schema_never_releases_reserve(self):
        self.final_pre()
        self.f.c.final_dry_complete=True
        self.f.final_mutation=lambda value:value.update(
            temporary_schema_names=self.f.c.fixture_context['temporary_schemas'])
        with self.assertRaisesRegex(ValueError,'final_temporary_scope'):
            self.f.owner.run(self.f.gate,IDS,'final_post')
        self.assertNotIn('absence',self.f.order)
        self.assertFalse(self.f.c.final_post_complete)


if __name__ == '__main__':
    unittest.main()
