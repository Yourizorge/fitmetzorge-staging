"""Offline adapter tests. Synthetic graphs/fake drivers are never real CI proof."""
import argparse
import ast
import copy
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
import uuid
from unittest import mock

from quota_candidate_v1 import compiler as c
from quota_candidate_v1 import runtime_adapter as a
from admission_budget_test import nominal_sized_fixture

ROOT = pathlib.Path(__file__).resolve().parents[4]


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='quota-runtime-offline-')
        cls.root = pathlib.Path(cls.temp.name).resolve()
        refs = json.loads((a.HERE / 'runtime_refs.json').read_text())
        names = set(c.PINS) | {c.PREFIX + n for n in c.SUPPORT} | set(refs['references']) | {a.DAG_SOURCE}
        for name in names:
            dest = cls.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        for name in set(c.OWN) | set(refs['runtime_files']):
            dest = cls.root / a.PREFIX / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(a.HERE / name, dest)
        cls.original = {n: (ROOT / n).read_bytes() for n in c.PINS}
        # The actual compiler's synthetic graph is a unit fixture, not an executor export.
        marker = 'unit-executor.json'
        (cls.root / marker).write_bytes(c.canonical({'scope': 'synthetic unit only; no execution'}))
        marker_sha = c.sha((cls.root / marker).read_bytes())
        plan = nominal_sized_fixture()
        def bind(value):
            if isinstance(value, dict):
                if value.get('source') == 'synthetic':
                    value.update(source=marker, source_sha256=marker_sha)
                for child in value.values(): bind(child)
            elif isinstance(value, list):
                for child in value: bind(child)
        bind(plan)
        cls.plan_name = 'unit-plan.json'
        (cls.root / cls.plan_name).write_bytes(c.canonical(plan))
        cls.sources = a.source_inputs(cls.root)
        cls.sources.update({marker: marker_sha,
                            cls.plan_name: c.sha((cls.root / cls.plan_name).read_bytes())})
        cls.ca = cls.root / 'unit-only-ca.pem'
        cls.ca.write_text('existence fixture only, no TLS connection', encoding='ascii')

    @classmethod
    def tearDownClass(cls):
        for name, expected in cls.original.items():
            if (ROOT / name).read_bytes() != expected:
                raise AssertionError('actual frozen source changed')
        cls.temp.cleanup()

    def setUp(self):
        self.actual_compile = a.compile_register
        patch = mock.patch.object(a,'compile_register',side_effect=lambda root,plan,sources:
                                  a.admission_budget.compile_release(plan,sources))
        patch.start();self.addCleanup(patch.stop)
        start = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        stamp = lambda v: v.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.now = stamp(start)
        self.case_id = str(uuid.uuid4())
        self.manifest = c.prepare(self.root, source_commit='a'*40, candidate_sha256='b'*64,
            github_run='41619169140', created_at=self.now, expires_at=stamp(start+dt.timedelta(seconds=180)),
            cases=[dict(id=self.case_id, label='unit_only', cap=2349)], sources=self.sources)
        self.binding = c.binding_for_case(self.root, self.manifest, self.case_id, now=self.now)
        self.isolation = dict(run_id=self.case_id, ci_run=self.binding['ci_run'], source_commit='a'*40,
            environment='disposable_ci', pg_container='1'*64, auth_container='2'*64,
            pg_system_identifier='12345678', database_oid=5, db_target_sha256='3'*64,
            auth_target_sha256='3'*64, registry_empty=True, pg17=True, ssl=True,
            auth_database_bound=True, reused=False, evidence_sha256='4'*64,
            native_ssl=True, auth_ssl=True, auth_sslmode='verify-full')
        self.env = dict(GITHUB_ACTIONS='true', GITHUB_REPOSITORY=c.binding.REPOSITORY,
            GITHUB_REF='refs/heads/main', GITHUB_SHA='a'*40, GITHUB_RUN_ID=self.binding['ci_run'])
        self.connection = dict(host='127.0.0.1', hostaddr='127.0.0.1', port=5432, dbname='postgres',
            user='postgres', sslmode='verify-full', sslrootcert=str(self.ca), connect_timeout=5)
        self.args = dict(plan_ref=dict(path=self.plan_name, sha256=self.sources[self.plan_name]),
            isolation=self.isolation, prior_cases=(), environment=self.env,
            connection=self.connection, ca_path=self.ca, now=self.now)

    def prepared(self):
        return a.prepare_case(self.root, self.manifest, self.case_id, **self.args)

    def test_compiled_unit_model_remains_not_execution_or_hosted_admission(self):
        config = self.prepared().config()
        self.assertEqual(config['register']['normal_capacity'], 2338)
        self.assertEqual(config['register']['worst_including_safety'], 2339)
        self.assertEqual(config['register']['approved_limit'], 2349)
        self.assertFalse(config['binding']['execution_admitted'])
        self.assertFalse(config['binding']['hosted_permission'])
        config['binding']['cap'] = 9999
        self.assertEqual(self.prepared().config()['binding']['cap'], 2349)

    def test_real_admission_cannot_accept_the_historical_synthetic_unit_graph(self):
        plan=json.loads((self.root/self.plan_name).read_bytes())
        with self.assertRaisesRegex(c.CandidateStop,'runtime_current_dag_required'):
            self.actual_compile(self.root,plan,self.sources)

    def test_register_uses_strict_authoritative_api_with_explicit_roots(self):
        plan=self.unit_current_dag()
        model=dict(status='NO_GO',bound_complete=False,fits=False)
        strict=types.SimpleNamespace(__file__=str(self.root/a.DAG_SOURCE),
            compile_release=mock.Mock(return_value=model))
        with mock.patch.dict(sys.modules,{'admission_budget_current_release':strict}):
            result=self.actual_compile(self.root,plan,self.sources)
        self.assertIs(result,model)
        strict.compile_release.assert_called_once_with(plan,self.sources,
            source_root=self.root,runtime_dir=a.HERE)

    def test_loaded_or_candidate_strict_compiler_mismatch_never_invoked(self):
        plan=self.unit_current_dag()
        strict=types.SimpleNamespace(__file__=str(self.root/a.DAG_SOURCE),compile_release=mock.Mock())
        with mock.patch.dict(sys.modules,{'admission_budget_current_release':strict}):
            changed={**self.sources,a.DAG_SOURCE:'f'*64}
            with self.assertRaisesRegex(c.CandidateStop,'runtime_current_compiler_source'):
                self.actual_compile(self.root,plan,changed)
            strict.__file__=str(a.HERE/'runtime_adapter.py')
            with self.assertRaisesRegex(c.CandidateStop,'runtime_loaded_current_compiler'):
                self.actual_compile(self.root,plan,self.sources)
        strict.compile_release.assert_not_called()

    def test_prepared_context_cannot_be_constructed_without_preflight(self):
        with self.assertRaisesRegex(c.CandidateStop, 'runtime_preflight_required'):
            a.PreparedCase(None, {})
        with self.assertRaisesRegex(c.CandidateStop, 'runtime_preflight_required'):
            a.CaseBudget({})

    def test_missing_or_unbound_plan_fails_before_connection(self):
        for plan in (None, {}, {'path': self.plan_name, 'sha256': '0'*64}):
            self.args['plan_ref'] = plan
            with self.subTest(plan=plan), self.assertRaises(c.CandidateStop): self.prepared()

    def unit_current_dag(self):
        return dict(format='admission-current-dispatch-dag-v1',plan_sha256='1'*64,
            source_hashes={a.PREFIX+'runtime_adapter.py':self.sources[a.PREFIX+'runtime_adapter.py']},
            register_source_hashes={'runtime_budget.py':self.sources[c.PREFIX+'runtime_budget.py']})

    def test_inmemory_dag_hash_and_source_checks_precede_compiler(self):
        self.args.pop('plan_ref')
        plan=self.unit_current_dag()
        for field in ('digest','source','ambiguous'):
            changed=copy.deepcopy(plan);digest=c.sha(c.canonical(changed))
            extra={}
            if field=='digest':digest='f'*64
            if field=='source':
                changed['register_source_hashes']['runtime_budget.py']='f'*64
                digest=c.sha(c.canonical(changed))
            if field=='ambiguous':extra['plan_ref']=dict(path=self.plan_name,sha256=self.sources[self.plan_name])
            with self.subTest(field=field),mock.patch.object(a,'compile_register') as compile:
                with self.assertRaises(c.CandidateStop):
                    a.prepare_case(self.root,self.manifest,self.case_id,current_plan=changed,
                        current_plan_sha256=digest,**self.args,**extra)
                compile.assert_not_called()

    def test_inmemory_dag_preserves_immutable_snapshot_and_separate_semantic_hash(self):
        self.args.pop('plan_ref');plan=self.unit_current_dag();digest=c.sha(c.canonical(plan))
        unit_model=a.admission_budget.compile_release(json.loads((self.root/self.plan_name).read_bytes()),self.sources)
        unit_model.update(dag_sha256=digest,plan_sha256=plan['plan_sha256'])
        with mock.patch.object(a,'compile_register',return_value=unit_model):
            prepared=a.prepare_case(self.root,self.manifest,self.case_id,current_plan=plan,
                current_plan_sha256=digest,**self.args)
        plan['plan_sha256']='changed_after_validation'
        self.assertEqual(prepared.config()['register']['dag_sha256'],digest)
        self.assertEqual(prepared.config()['register']['semantic_plan_sha256'],'1'*64)
        self.assertEqual(prepared.config()['current_dag']['plan_sha256'],'1'*64)

    def test_authoritative_model_handoff_is_hashed_and_not_mutable_by_caller(self):
        self.args.pop('plan_ref');plan=self.unit_current_dag();digest=c.sha(c.canonical(plan))
        model=a.admission_budget.compile_release(json.loads((self.root/self.plan_name).read_bytes()),self.sources)
        model.update(format='admission-actual-execution-release-v1',dag_sha256=digest,
                     plan_sha256=plan['plan_sha256'])
        with mock.patch.object(a,'compile_register',return_value=model):
            prepared=a.prepare_case(self.root,self.manifest,self.case_id,current_plan=plan,
                current_plan_sha256=digest,**self.args)
        expected=c.sha(c.canonical(model));model['bound_complete']=False
        value=prepared.config()
        self.assertEqual(value['register']['release_sha256'],expected)
        self.assertTrue(value['release_model']['bound_complete'])
        self.assertEqual(value['register']['release_format'],'admission-actual-execution-release-v1')

    def test_missing_scenario_body_is_rejected_before_workflow_capture(self):
        name='_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py'
        del self.manifest['sources'][name]
        with self.assertRaises(c.CandidateStop):self.prepared()

    def test_both_actual_worker_paths_use_verified_candidate_not_loaded_python_tree(self):
        composition=object.__new__(a.CaseComposition);composition.quota=self.prepared().config()
        self.assertNotEqual(self.root,a.HERE.parents[3])
        for name in ('runtime_auth.mjs','runtime_integral_workflow.mjs'):
            self.assertEqual(composition.worker_path(name),self.root/a.PREFIX/name)
        with self.assertRaises(c.CandidateStop):composition.worker_path('../integral_auth.mjs')
        composition.quota['manifest']['sources'][a.PREFIX+'runtime_auth.mjs']='f'*64
        with self.assertRaises(c.CandidateStop):composition.worker_path('runtime_auth.mjs')

    def test_source_tampering_fails_closed(self):
        self.manifest['sources'][c.PREFIX+'runtime_budget.py'] = '0'*64
        with self.assertRaises(c.CandidateStop): self.prepared()

    def test_loaded_meter_must_match_the_verified_candidate_bytes(self):
        module = sys.modules['runtime_budget']
        original = module.__file__
        try:
            module.__file__ = str(self.root / 'unit-executor.json')
            with self.assertRaisesRegex(c.CandidateStop, 'runtime_loaded_module'):
                self.prepared()
        finally:
            module.__file__ = original

    def test_incomplete_graph_never_becomes_complete_by_phase_totals(self):
        original = (self.root / self.plan_name).read_bytes()
        try:
            plan = json.loads(original)
            plan['executor_inventory']['complete'] = False
            raw = c.canonical(plan)
            (self.root / self.plan_name).write_bytes(raw)
            self.manifest['sources'][self.plan_name] = c.sha(raw)
            self.args['plan_ref']['sha256'] = c.sha(raw)
            with self.assertRaisesRegex(c.CandidateStop, 'runtime_full_register_incomplete'):
                self.prepared()
        finally:
            (self.root / self.plan_name).write_bytes(original)

    def test_case_and_ci_identity_must_match_inventory(self):
        for key, value in [('run_id', str(uuid.uuid4())), ('ci_run', '9'), ('source_commit', 'c'*40),
                           ('environment', 'staging'), ('registry_empty', False), ('ssl', False),
                           ('pg17', False), ('reused', True), ('auth_database_bound', False)]:
            changed = {**self.isolation, key: value}
            with self.subTest(key=key), self.assertRaises(c.CandidateStop):
                a.validate_isolation(changed, self.binding)

    def test_auth_must_target_the_case_database_not_a_shared_stack(self):
        for key, value in [('auth_target_sha256', 'f'*64), ('auth_container', '1'*64)]:
            with self.subTest(key=key), self.assertRaisesRegex(c.CandidateStop, 'runtime_auth_database'):
                a.validate_isolation({**self.isolation, key: value}, self.binding)

    def test_previous_case_pg_auth_and_cluster_identity_cannot_be_reused(self):
        fresh = {**self.isolation, 'run_id': str(uuid.uuid4()), 'pg_container': '5'*64,
                 'auth_container': '6'*64, 'pg_system_identifier': '987654321'}
        a.validate_isolation(self.isolation, self.binding, [fresh])
        for keys in [('run_id',), ('pg_container',), ('auth_container',),
                     ('pg_system_identifier', 'database_oid')]:
            prior = {**fresh, **{k: self.isolation[k] for k in keys}}
            with self.subTest(keys=keys), self.assertRaisesRegex(c.CandidateStop, 'runtime_database_reuse'):
                a.validate_isolation(self.isolation, self.binding, [prior])

    def test_fifteenth_case_accepts_fourteen_distinct_prior_inventories(self):
        prior = [{**self.isolation, 'run_id': str(uuid.uuid4()),
                  'pg_container': c.sha(('pg'+str(i)).encode()),
                  'auth_container': c.sha(('auth'+str(i)).encode()),
                  'pg_system_identifier': str(10000+i)} for i in range(14)]
        self.assertEqual(a.validate_isolation(self.isolation, self.binding, prior), self.isolation)
        with self.assertRaisesRegex(c.CandidateStop, 'runtime_database_reuse'):
            a.validate_isolation(self.isolation, self.binding, [*prior[:-1], self.isolation])

    def test_target_remote_tls_timeout_and_ci_mismatch_never_dispatch(self):
        for key, value in [('host', 'remote.invalid'), ('sslmode', 'require'), ('connect_timeout', 6)]:
            old = self.connection[key]
            self.connection[key] = value
            with self.subTest(key=key), self.assertRaises(c.CandidateStop): self.prepared()
            self.connection[key] = old
        self.env['GITHUB_RUN_ID'] = '123'
        with self.assertRaises(c.CandidateStop): self.prepared()

    def test_all_meter_enforcement_methods_are_inherited_unchanged(self):
        for name, method in vars(a.RuntimeBudget).items():
            if callable(method) and name not in ('__init__','_reserve','safety'):
                self.assertIs(getattr(a.CaseBudget, name), method, name)
        meter = a.CaseBudget(self.prepared(), clock=lambda: 10)
        self.assertEqual(meter.limit, 2349)
        self.assertEqual(sum(meter.limits.values()), 2338)

    def test_setup_safety_is_owned_prepaid_one_shot_and_keeps_unknown(self):
        meter=a.CaseBudget(self.prepared(),clock=lambda:10)
        self.assertEqual(meter._reserve(meter.phases,meter.state),
            a.RuntimeBudget._reserve(meter,meter.phases,meter.state)+1)
        meter.stop('original_failure')
        with self.assertRaises(a.BudgetStop):meter.safety('rollback_setup',1)
        meter.setup_connection_owned=True
        ticket=meter.safety('rollback_setup',1)
        self.assertEqual(meter.used,1)
        self.assertIn(ticket,meter.safety_pending)
        with self.assertRaises(a.BudgetStop):meter.safety('rollback_setup',1)
        self.assertEqual(meter.used,1)
        self.assertEqual(meter.stop_reason,'original_failure')

    def test_setup_safety_never_expands_kind_count_deadline_or_cap(self):
        for change in ('count','kind','cap','deadline','not_stopped'):
            meter=a.CaseBudget(self.prepared(),clock=lambda:10)
            meter.setup_connection_owned=True
            if change!='not_stopped':meter.stop('original_failure')
            if change=='cap':meter.used=meter.limit
            if change=='deadline':meter.started=-590
            with self.subTest(change=change),self.assertRaises(a.BudgetStop):
                meter.safety('rollback_setup',2 if change=='count' else 1,
                    kind='managed_auth' if change=='kind' else 'native')

    def test_versioned_workflow_precharges_all_360_before_any_native_work(self):
        composition = object.__new__(a.CaseComposition)
        composition.meter = a.CaseBudget(self.prepared())
        composition.scenario = a.scenario_source.capture()['workflow_actions']
        def stopped(*args, **kwargs):
            self.assertEqual(composition.meter.used, 360)
            self.assertEqual(len(composition.meter.managed_pending), 72)
            raise RuntimeError('unit_lost_workflow')
        with mock.patch.object(a.WorkflowBridge, 'workflow', stopped):
            with self.assertRaisesRegex(RuntimeError, 'unit_lost_workflow'):
                composition.workflow(None, None, None, None, None)
        self.assertEqual(composition.meter.used, 360)
        self.assertEqual(len(composition.meter.managed_pending), 72)

    def test_confirmed_versioned_workflow_confirms_exact_original_360(self):
        composition = object.__new__(a.CaseComposition)
        composition.meter = a.CaseBudget(self.prepared())
        composition.scenario = a.scenario_source.capture()['workflow_actions']
        with mock.patch.object(a.WorkflowBridge, 'workflow', return_value={'unit_only': True}):
            self.assertEqual(composition.workflow(), {'unit_only': True})
        self.assertEqual(composition.meter.used, 360)
        self.assertFalse(composition.meter.managed_pending)

    def test_lost_auth_result_keeps_reserve_and_original_stop(self):
        meter = a.CaseBudget(self.prepared(), clock=lambda: 10)
        ticket = meter.charge('auth', 11, action='unit_issue', kind='managed_auth',
                             state_after={'auth_maybe_live': True}, mutation=True)
        meter.stop('original_lost_reply')
        self.assertEqual(meter.used, 11)
        self.assertIn(ticket, meter.managed_pending)
        self.assertTrue(meter.state['auth_maybe_live'])
        with self.assertRaises(a.BudgetStop): meter.charge('auth', 1, action='retry')
        self.assertEqual(meter.stop_reason, 'original_lost_reply')
        self.assertEqual(meter.used, 11)

    def test_normal_precharge_cannot_release_auth_unknown(self):
        meter = a.CaseBudget(self.prepared(), clock=lambda: 10)
        ticket = meter.charge('auth', 1, action='unit', state_after={'auth_maybe_live': True})
        meter.confirm(ticket)
        with self.assertRaisesRegex(a.BudgetStop, 'runtime_auth_release_requires_known_zero'):
            meter.charge('auth', 1, action='wrong_release', state_after={'auth_maybe_live': False})
        self.assertTrue(meter.state['auth_maybe_live'])
        meter.confirm_auth_zero()
        self.assertFalse(meter.state['auth_maybe_live'])
        self.assertEqual(meter.state_confirmations[-1]['sql'], 0)

    def test_composition_denies_non_native_before_connection_or_m45_reapply(self):
        with self.assertRaisesRegex(c.CandidateStop, 'runtime_disposable_only'):
            a.CaseComposition(self.prepared(), runtime=object())
        with self.assertRaisesRegex(a.BudgetStop, 'runtime_canonical_migration_reapply_forbidden'):
            a.CaseComposition.apply_migration(None, None)

    def unit_runner_arguments(self):
        # Typed stubs exercise pre-worker checks only, not actual runtime/DB attestation.
        prepared = self.prepared()
        composition = object.__new__(a.CaseComposition)
        runtime = object.__new__(a.NativeRuntime)
        runtime.environment = 'disposable_ci'
        composition.quota = prepared.config()
        composition.runner=composition.worker_path('runtime_auth.mjs')
        composition.runtime = runtime
        composition.meter = a.CaseBudget(prepared)
        composition.case_prefix_ready=True
        lock = object.__new__(a.IdentitySession)
        lock.runtime = runtime
        lock.composition = composition
        gate = types.SimpleNamespace()
        lifecycle = object.__new__(a.RegisteredLifecycle)
        lifecycle.gate = gate
        lifecycle.composition = composition
        lifecycle.run_id = self.case_id
        lifecycle.ids = {role: str(uuid.uuid4()) for role in ('a_member', 'a_trainer', 'b_member')}
        lifecycle.worker_owned = False
        lifecycle.installed = False
        lifecycle.lock_query = lock.query
        config = dict(mode='registered_synthetic', environment='disposable_ci', registeredIds=lifecycle.ids)
        return gate, composition, lifecycle, config

    def test_execute_case_without_prefix_never_starts_worker(self):
        args = self.unit_runner_arguments()
        with mock.patch('quota_candidate_v1.runtime_worker_runner.execute') as execute:
            with self.assertRaisesRegex(c.CandidateStop, 'runtime_verified_prefix_required'):
                a.execute_case(*args)
            execute.assert_not_called()

    def test_execute_case_rejects_wrong_lifecycle_or_legacy_migration_hook(self):
        for mode in ('case', 'gate_hook', 'lock','worker_root'):
            gate, composition, lifecycle, config = self.unit_runner_arguments()
            if mode == 'case': lifecycle.run_id = c.binding.OLD_RUN
            if mode == 'gate_hook': gate.apply_endchain_migration = lambda: None
            if mode == 'lock': lifecycle.lock_query = lambda *_: None
            if mode == 'worker_root':composition.runner=a.HERE/'runtime_auth.mjs'
            with self.subTest(mode=mode), mock.patch('quota_candidate_v1.runtime_worker_runner.execute') as execute:
                with self.assertRaises(c.CandidateStop): a.execute_case(gate, composition, lifecycle, config)
                execute.assert_not_called()

    def test_execute_case_delegates_versioned_runner_without_promoting_result(self):
        gate, composition, lifecycle, config = self.unit_runner_arguments()
        for phase, count in [('preflight', 4), ('migration', 128)]:
            ticket = composition.meter.charge(phase, count, action='unit_prefix', kind='cli_bound')
            composition.meter.confirm(ticket)
        sentinel = {'unit_fake_only': True, 'full_chain_admission': False}
        with mock.patch('quota_candidate_v1.runtime_worker_runner.execute', return_value=sentinel) as execute:
            self.assertIs(a.execute_case(gate, composition, lifecycle, config), sentinel)
            execute.assert_called_once()
            call = execute.call_args.args
            self.assertEqual(call[:3], (gate, composition, lifecycle))
            self.assertEqual(call[3]['quota']['binding']['run_id'], self.case_id)
            self.assertNotIn('quota', config)

    def test_actual_workflow_tail_has_no_action_transport_or_cleanup_rewrite(self):
        old = (ROOT / c.PREFIX / 'workflow_composition.mjs').read_text()
        new = (a.HERE / 'runtime_workflow.mjs').read_text()
        self.assertEqual(new[new.index('const placeholder={};'):], old[old.index('const placeholder={};'):])

    def test_parent_workflow_only_changes_exact_bound_transport_fault_and_wait_hooks(self):
        old = (ROOT / c.PREFIX / 'integral_ci.py').read_text()
        old = old[old.index('    def workflow(self,'):]
        new = (a.HERE / 'runtime_parent_workflow.py').read_text()
        new = new[new.index('    def workflow(self,'):]
        expected = old.replace("str(HERE/'integral_workflow.mjs')",
                               "str(self.worker_path('runtime_integral_workflow.mjs'))")
        expected=expected.replace(
            "            for channel in ('setup','writer','reader','workflow'):connections[channel]=runtime.connect()\n"
            "        except Exception:\n            for connection in connections.values():connection.close()",
            "            for channel in ('setup','writer','reader','workflow'):\n"
            "                connections[channel]=runtime.connect()\n"
            "                if channel=='setup':self.meter.setup_connection_owned=True\n"
            "        except Exception as error:\n"
            "            self.abort('workflow_connection_failed')\n"
            "            for channel,connection in connections.items():\n"
            "                try:\n                    connection.close()\n"
            "                    if channel=='setup':self.meter.setup_connection_owned=False\n"
            "                except Exception as secondary:\n"
            "                    error.add_note('workflow_connection_close_secondary:'+type(secondary).__name__)")
        tail="""        finally:
            from .runtime_recovery import finish
            finish(self,gate,runtime,connections,query,raw_query,process=process,timer=timer,
                enable_attempted=enable_attempted,original=controls,enabled=enabled,
                restored=restored,primary=sys.exc_info()[1])
"""
        expected=expected[:expected.rindex('        finally:\n            if timer:')]+tail
        expected = expected.replace(
            "            with urllib.request.urlopen(req,timeout=5) as response:user=json.loads(response.read(20000))",
            """            self.workflow_dispatch.before(0)
            try:
                with urllib.request.urlopen(req,timeout=5) as response:
                    user=json.loads(response.read(20000));status=response.status
            except Exception:
                self.workflow_dispatch.after(0,'lost_response')
                raise
            self.workflow_dispatch.after(0,'response_received',status)""")
        expected = expected.replace("                    elif message['op']=='persist':",
            "                    elif message['op']=='workflow_auth':\n"
            "                        self.workflow_dispatch.worker_message(message)\n"
            "                    elif message['op']=='persist':")
        expected = expected.replace("            gate.save('workflow-auth-protocol.json',{'verified_calls':72,**auth_load})",
            "            gate.save('workflow-auth-protocol.json',{'verified_calls':72,**auth_load})\n"
            "            gate.save('case-workflow-auth-dispatch.json',self.workflow_dispatch.validated({'verified_calls':72,**auth_load}))")
        expected=expected.replace('        import psycopg\n',"""        import auth_failure_transport
        from .compiler import read_source, require, sha
        from .runtime_worker_evidence import bind,save,validate_result,WaitEvidence
        binding,worker_sources,case=bind(self)
        worker_evidence=WaitEvidence(binding,case,'workflow')
        transport_source = '_offline/phase6e11/endchain_v1/auth_failure_transport.py'
        require(sha(pathlib.Path(auth_failure_transport.__file__).read_bytes())
                == self.quota['manifest']['sources'].get(transport_source)
                == sha(read_source(self.quota['root'], transport_source)),
                'workflow_http_transport_source')
        import psycopg
""")
        expected=expected.replace('            import urllib.request,base64\n',
            '            import urllib.request,base64\n'
            '            from auth_failure_transport import complete_body, StrictHTTPHandler, NoRedirect\n')
        expected=expected.replace("""                with urllib.request.urlopen(req,timeout=5) as response:
                    user=json.loads(response.read(20000));status=response.status""", """                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),StrictHTTPHandler())
                with opener.open(req,timeout=5) as response:
                    body=complete_body(response)
                    if len(body)>20000:raise RuntimeError('ci_auth_body_bound')
                    user=json.loads(body);status=response.status""")
        expected=expected.replace('            timer=threading.Timer(125,process.kill);timer.start()',
            '            worker_evidence.attach(process)\n'
            '            timer=threading.Timer(125,lambda:worker_evidence.kill(watchdog=True))\n'
            '            worker_evidence.start_timer(timer,deadline=time.monotonic()+125)')
        expected=expected.replace("                if message['op']=='complete':result=message['result'];break",
            "                if message['op']=='complete':\n"
            "                    result=validate_result(message['result'],'workflow')\n"
            "                    save(gate,'case-workflow-worker-result.json',result)\n"
            "                    break")
        expected=expected.replace('            process.wait(timeout=5)',
            '            worker_evidence.wait()\n            worker_evidence.stop_timer(timer)')
        expected=expected.replace("            if process.returncode or not result or result.get('pairs')!=71:",
            "            if (not worker_evidence.known or worker_evidence.returncode or not result\n"
            "                    or result.get('status')!='LOCAL_COMPOSED_71_PASS' or result.get('pairs')!=71):")
        expected=expected.replace('restored=restored,primary=sys.exc_info()[1])',
            'restored=restored,primary=sys.exc_info()[1],worker_evidence=worker_evidence)')
        hook_blocks = [
            "faults=getattr(self,'phase_faults',None)",
            "if faults is not None:\n text,values=faults.prepare_native(channel,phase,text,values,self.action)",
            "if faults is not None:faults.native_after(channel,phase,text,self.action)",
            "if faults is not None:faults.native_error(channel,phase,text,self.action,e.sqlstate)",
            "if faults is not None:faults.pair_confirmed(message['event'])",
        ]
        allowed = {ast.dump(ast.parse(code).body[0]): 0 for code in hook_blocks}
        class StripExactHooks(ast.NodeTransformer):
            def visit(self, node):
                signature = ast.dump(node)
                if signature in allowed:
                    allowed[signature] += 1
                    return None
                return super().visit(node)
        stripped = StripExactHooks().visit(ast.parse(textwrap.dedent(new)))
        self.assertEqual(list(allowed.values()), [2, 1, 1, 1, 1])
        self.assertEqual(ast.dump(stripped),
                         ast.dump(ast.parse(textwrap.dedent(expected))))

    def test_node_entrypoints_parse_and_fake_driver_regressions(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required, no silent skipped regressions')
        package = self.root / a.PREFIX
        for name in ('runtime_node.mjs', 'runtime_auth.mjs', 'runtime_workflow.mjs', 'runtime_integral_workflow.mjs'):
            result = subprocess.run([node, '--check', str(package / name)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        config = self.root / 'unit-context.json'
        config.write_bytes(c.canonical(self.prepared().config()))
        env = {**os.environ, **self.env, 'QUOTA_UNIT_CONFIG': str(config)}
        try:
            result = subprocess.run([node, '--test', '--test-reporter=tap', str(package / 'test_runtime_node.mjs')],
                                    env=env, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired as error:
            output=error.stdout or b''
            self.fail('Node unit test deadline unchanged (60s):\n'+
                      (output.decode('utf-8',errors='replace') if isinstance(output,bytes) else output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('# pass 18', result.stdout)
        print('Node fake-driver tests: 18 passed; no real DB/Auth evidence')


class IsolationTLSContractTests(unittest.TestCase):
    def setUp(self):
        self.binding={'run_id':'unit','ci_run':'123','source_commit':'a'*40}
        self.value={**self.binding,'environment':'disposable_ci','pg_container':'1'*64,
            'auth_container':'2'*64,'pg_system_identifier':'12345','database_oid':5,
            'db_target_sha256':'3'*64,'auth_target_sha256':'3'*64,'registry_empty':True,
            'pg17':True,'ssl':True,'auth_database_bound':True,'reused':False,
            'evidence_sha256':'4'*64,'native_ssl':True,'auth_ssl':True,'auth_sslmode':'verify-full'}

    def test_exact_measured_tls_shape_is_accepted_without_adding_authority(self):
        result=a.validate_isolation(self.value,self.binding)
        self.assertEqual(result,self.value);self.assertIsNot(result,self.value)
        self.assertNotIn('case_pass',result)

    def test_legacy_shape_without_separate_auth_tls_evidence_is_rejected(self):
        for key in ('native_ssl','auth_ssl','auth_sslmode'):
            value=dict(self.value);value.pop(key)
            with self.subTest(key=key),self.assertRaisesRegex(c.CandidateStop,'isolation_shape'):
                a.validate_isolation(value,self.binding)

    def test_no_truthy_ssl_or_auth_tls_downgrade_is_accepted(self):
        for key,values in (('native_ssl',(False,1,'true')),('auth_ssl',(False,1,'true')),
                           ('auth_sslmode',('require','verify-ca','disable',None))):
            for value in values:
                with self.subTest(key=key,value=value),self.assertRaisesRegex(c.CandidateStop,'isolation_evidence'):
                    a.validate_isolation({**self.value,key:value},self.binding)

    def test_extra_fields_are_not_silently_ignored(self):
        with self.assertRaisesRegex(c.CandidateStop,'isolation_shape'):
            a.validate_isolation({**self.value,'arbitrary_admitted':True},self.binding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root', type=pathlib.Path)
    options, remaining = parser.parse_known_args()
    if options.source_root is not None: ROOT = options.source_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0], *remaining])
