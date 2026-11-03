"""Unit-only boundaries/negative cases; never substitute for real CI receipts."""
import copy
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import migration_failure_boundaries as m

# Projection of verified-41507466863/candidate.json, not production SOURCES.
# Manifest raw SHA256: cab8979d9aeb8a329167e2b1cf35b30c1fe7276979bdf40cc3b3494da24c0a8f
# Current bytes are tested against this historical packaging layout, not passed
# off as the bytes or successful runtime evidence of the historical candidate.
CI1_HOOK_LAYOUT = frozenset(m.rt.PREFIX + name for name in (
    'admission_binding.py', 'admission_ci.py', 'admission_failure.py',
    'ci_source_binding.py', 'integral_failure_runtime.py',
    'migration_failure_boundaries.py', 'native_runtime.py', 'sql_protocol.py',
    'test_migration_failure_boundaries.py'))
CI1_MIGRATION_LAYOUT_SHA = '5de323e909067e5bb45790b844fc4ae90b3dbffba9b9e5037c7418a64f8a653d'
CI1_CHECKOUT_ONLY = '_offline/phase6e11/ci41/runner.py'


def observed_checkout_root():
    """CI tests run from candidate sources, but the harness stays in checkout."""
    workspace = os.environ.get('GITHUB_WORKSPACE')
    if workspace:
        checkout = pathlib.Path(workspace)
        if not checkout.is_absolute() or not checkout.is_dir():
            raise AssertionError('boundary_test_checkout_root')
        return checkout.resolve()
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        raise AssertionError('boundary_test_checkout_required')
    return m.ROOT.resolve()


def metadata(after=False):
    return {**dict.fromkeys(m.COUNTS, 0), 'history': ['v%02d' % i for i in range(1, 46 if after else 45)],
            'm44_function': 'a'*64, 'm45_function': 'b'*64 if after else None,
            'm45_trigger': 'c'*64 if after else None, 'quota_constraint': ('d' if after else 'e')*64}


class BoundariesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = pathlib.Path(self.temp.name)
        self.saved = {}
        self.gate = SimpleNamespace(out=self.folder, work=self.folder, binary=self.folder/'cli', serial=45,
            result={'phase':'migration_45', 'migrations_applied':44}, cli=Mock(side_effect=AssertionError('unexpected CLI')))
        self.gate.save = lambda name, value:self.saved.setdefault(name, copy.deepcopy(value))
        self.source = {'sources':{'unit-only':'a'*64},'source_commit':'b'*40}
        self.history = metadata(True)['history']

    def token(self):
        token = m.Boundary(self.gate, self.source, self.history)
        token.sample = metadata()
        self.gate._migration_failure_boundary = token
        return token

    def result(self, code=0):
        self.gate.serial += 1
        path = self.folder/('%03d-cli-migration.json' % self.gate.serial)
        path.write_text(json.dumps({'phase':'migration_45','exitcode':code}), encoding='utf-8')
        return subprocess.CompletedProcess([str(self.gate.binary),'--workdir',str(self.gate.work),
                                             'migration','up','--local'], code, 'private stdout', 'private stderr')

    def session(self, case):
        session = m.rt.Session(SimpleNamespace(), case, {'limit':12,'cleanup_reserve':4},time.monotonic()+180)
        return SimpleNamespace(clear=lambda:None), session

    def test_pre_dispatch_fault_never_enters_actual_dispatcher(self):
        with self.assertRaises(m.rt.InjectedFailure):m.reject_before_dispatch(self.gate.cli)
        self.gate.cli.assert_not_called()

    def test_before_observes_unchanged_real_boundary_without_cli(self):
        with patch.object(m,'binding',return_value=(self.source,self.history)), \
                patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                patch.object(m,'snapshot',side_effect=[metadata(),metadata()]):
            token = m.before(self.gate)
        receipt = self.saved[m.NAMES[1]]
        self.assertTrue(receipt['component_verified'])
        self.assertFalse(receipt['dispatcher_called'])
        self.assertFalse(receipt['terminal_complete'])
        self.assertTrue(receipt['original_failure']['injected'])
        self.assertEqual(token.sample,metadata())
        self.gate.cli.assert_not_called()

    def test_before_denies_repeat_without_native_call(self):
        self.gate._migration_failure_boundary = object()
        with patch.object(m,'binding',return_value=(self.source,self.history)), \
                patch.object(m,'native_session') as native, self.assertRaises(m.rt.Blocked):
            m.before(self.gate)
        native.assert_not_called()

    def test_predispatch_metadata_drift_retains_injected_error_and_blocks(self):
        changed=metadata();changed['quota_constraint']='f'*64
        with patch.object(m,'binding',return_value=(self.source,self.history)), \
                patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                patch.object(m,'snapshot',side_effect=[metadata(),changed]), self.assertRaises(m.rt.Blocked):
            m.before(self.gate)
        receipt=self.saved[m.NAMES[1]]
        self.assertFalse(receipt['component_verified'])
        self.assertTrue(receipt['original_failure']['injected'])
        self.assertEqual(len(receipt['secondary_failures']),1)

    def test_post_accepts_only_one_confirmed_parent_call_and_keeps_no_go(self):
        token=self.token();result=self.result()
        with patch.object(m,'binding',return_value=(self.source,self.history)), \
                patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                patch.object(m,'snapshot',side_effect=[metadata(True),metadata(True)]):
            receipt=m.after(self.gate,token,result)
        self.assertTrue(receipt['component_verified'])
        self.assertTrue(receipt['safe_closure_no_fixtures'])
        self.assertFalse(receipt['full_phase_semantics_verified'])
        self.assertFalse(receipt['full_chain_admission'])
        self.assertFalse(receipt['migration_rollback_claim'])
        self.assertEqual(receipt['actual_migration_result']['parent_bootstrap_dispatches'],1)
        self.assertNotIn('private stdout',json.dumps(receipt))
        self.assertNotIn('private stderr',json.dumps(receipt))
        self.gate.cli.assert_not_called()

    def test_unknown_nonzero_and_wrong_args_never_start_post_sql(self):
        for kind in ('unknown','nonzero','remote','extra'):
            with self.subTest(kind=kind):
                self.saved.clear();self.gate.serial=45
                token=self.token();result=self.result(1 if kind=='nonzero' else 0)
                if kind=='unknown':result=None
                if kind=='remote':result.args[-1]='--linked'
                if kind=='extra':self.gate.serial+=1
                with patch.object(m,'binding',return_value=(self.source,self.history)), \
                        patch.object(m,'native_session') as native, self.assertRaises(m.rt.Blocked):
                    m.after(self.gate,token,result)
                native.assert_not_called()
                self.assertTrue(token.consumed)
                self.assertFalse(self.saved[m.NAMES[2]]['component_verified'])
                with self.assertRaises(m.rt.Blocked):m.after(self.gate,token,result)

    def test_cli_receipt_required_and_exit_status_strict(self):
        token=self.token();result=self.result()
        path=self.folder/'046-cli-migration.json'
        for value in ({'phase':'migration_45','exitcode':True}, {'phase':'migration_44','exitcode':0}):
            path.write_text(json.dumps(value),encoding='utf-8')
            with self.assertRaises(m.rt.Blocked):m.confirmed_result(self.gate,token,result)
        path.unlink()
        with self.assertRaises(m.rt.Blocked):m.confirmed_result(self.gate,token,result)

    def test_post_source_drift_never_opens_native_session(self):
        token=self.token();result=self.result()
        with patch.object(m,'binding',return_value=({},self.history)), \
                patch.object(m,'native_session') as native, self.assertRaises(m.rt.Blocked):
            m.after(self.gate,token,result)
        native.assert_not_called()

    def test_m44_drift_and_missing_m45_do_not_verify(self):
        for key,value in (('m44_function','f'*64),('m45_function',None),('m45_trigger',None),
                          ('quota_constraint','e'*64)):
            with self.subTest(key=key):
                self.saved.clear();self.gate.serial=45
                token=self.token();result=self.result();sample=metadata(True);sample[key]=value
                with patch.object(m,'binding',return_value=(self.source,self.history)), \
                        patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                        patch.object(m,'snapshot',return_value=sample), self.assertRaises(m.rt.Blocked):
                    m.after(self.gate,token,result)
                self.assertFalse(self.saved[m.NAMES[2]]['component_verified'])

    def test_not_ci_or_inherited_remote_rejected_before_file_or_connection(self):
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':m.REPOSITORY,'GITHUB_REF':'refs/heads/main',
                     'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'12'}
        for overrides in ({'GITHUB_ACTIONS':'false'},{'PGHOSTADDR':'203.0.113.1'},{'PGSERVICE':'remote'},
                          {'PGSERVICEFILE':'remote-file'}):
            with patch.dict(os.environ,{**environment,**overrides},clear=True), self.assertRaises(m.rt.Blocked):
                m.binding(self.gate)

    def test_metadata_and_guard_are_single_real_pg17_statements(self):
        from sql_protocol import single
        self.assertEqual(single(m.METADATA)['protocol_commands'],1)
        self.assertEqual(single(m.rt.CHECK)['protocol_commands'],1)
        self.assertNotIn(m.rt.OLD_RUN,m.METADATA)
        self.assertNotIn(m.rt.NEW_RUN,m.METADATA)

    def test_exact_checkout_binding_and_m45_pin_without_database(self):
        gate,helper,environment=self.composed_checkout_and_candidate()
        path=self.folder/'candidate.json'
        candidate=json.loads(path.read_text())
        with patch.dict(os.environ,environment,clear=True):
            source,history=helper.binding(gate)
            self.assertEqual(source['sources'][m.M45],m.PRESERVED[m.M45])
            self.assertEqual(source['source_bytes'][m.M45]['canonicalization'],'byte-exact')
            self.assertEqual(sum(row['canonicalization']=='CRLF-to-LF-only'
                                 for row in source['source_bytes'].values()),44)
            self.assertLess(len(json.dumps({'source_binding':source},indent=2).encode()),m.RECEIPT_LIMIT-8192)
            self.assertEqual(len(history),45)
            self.assertEqual(history[-1],m.VERSION)
            candidate['sources'][m.rt.PREFIX+'migration_failure_boundaries.py']='0'*64
            path.write_text(json.dumps(candidate),encoding='utf-8')
            with self.assertRaises(m.rt.Blocked):helper.binding(gate)

    def composed_checkout_and_candidate(self):
        """Load the current real composed Gate, without constructing/running it."""
        dispatcher=m.rt.PREFIX+'admission_ci.py'
        checkout=observed_checkout_root()
        old_path=sys.path[:]
        try:
            spec=importlib.util.spec_from_file_location('boundary_unit_composed_ci',checkout/dispatcher)
            app=importlib.util.module_from_spec(spec)
            with patch('subprocess.run',side_effect=AssertionError('unexpected process')), \
                    patch('subprocess.Popen',side_effect=AssertionError('unexpected process')), \
                    patch('urllib.request.urlopen',side_effect=AssertionError('unexpected network')):
                spec.loader.exec_module(app)
        finally:
            sys.path[:]=old_path
        gate=object.__new__(app.Gate)
        gate.__dict__.update(vars(self.gate))
        del gate.cli
        candidate=self.folder/'candidate';work=self.folder/'work'
        migrations={p.relative_to(m.ROOT).as_posix() for p in (m.ROOT/'supabase/migrations').glob('*.sql')}
        self.assertEqual(m.sha(('\n'.join(sorted(migrations))+'\n').encode()),CI1_MIGRATION_LAYOUT_SHA)
        names=CI1_HOOK_LAYOUT|migrations
        for name in names:
            target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(m.ROOT/name,target)
        (work/m.M45).parent.mkdir(parents=True)
        shutil.copyfile(candidate/m.M45,work/m.M45)
        files={name:m.sha((candidate/name).read_bytes()) for name in names}
        self.assertNotIn(CI1_CHECKOUT_ONLY,files)
        self.assertFalse((candidate/CI1_CHECKOUT_ONLY).exists())
        (self.folder/'candidate.json').write_text(json.dumps({'sha256':'c'*64,'sources':files}),encoding='utf-8')
        gate.sources=candidate;gate.work=work
        spec=importlib.util.spec_from_file_location('boundary_unit_candidate_helper',
                                                   candidate/m.rt.PREFIX/'migration_failure_boundaries.py')
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':m.REPOSITORY,'GITHUB_REF':'refs/heads/main',
                     'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'12','GITHUB_WORKSPACE':str(checkout)}
        return gate,helper,environment

    def test_real_composed_checkout_dispatcher_with_candidate_loaded_helper(self):
        gate,helper,environment=self.composed_checkout_and_candidate()
        self.assertEqual(helper.ROOT,gate.sources)
        self.assertNotEqual(helper.ROOT,m.ROOT)
        with patch.dict(os.environ,environment,clear=True), \
                patch('subprocess.run',side_effect=AssertionError('unexpected process')), \
                patch('subprocess.Popen',side_effect=AssertionError('unexpected process')):
            source,history=helper.binding(gate)
        self.assertEqual(source['sources'][m.M45],m.PRESERVED[m.M45])
        self.assertEqual(len(history),45)
        self.assertEqual(source['loaded_locations'],{'dispatcher':'checkout','boundary_helper':'candidate'})
        self.assertNotIn(CI1_CHECKOUT_ONLY,source['sources'])
        self.assertEqual(source['checkout_harness'][CI1_CHECKOUT_ONLY]['distribution'],'pinned_checkout_harness')
        self.assertFalse(source['checkout_harness'][CI1_CHECKOUT_ONLY]['candidate_required'])

    def test_checkout_harness_uses_existing_pin_and_keeps_raw_hash(self):
        from ci_source_binding import HARNESS
        checkout=observed_checkout_root()
        result=m.harness_binding(checkout)[CI1_CHECKOUT_ONLY]
        raw=(checkout/CI1_CHECKOUT_ONLY).read_bytes()
        self.assertEqual(result['lf_sha256'],HARNESS[CI1_CHECKOUT_ONLY])
        self.assertEqual(result['checkout_sha256'],m.sha(raw))
        with patch.object(pathlib.Path,'read_bytes',return_value=raw+b'\n# changed harness\n'), \
                self.assertRaisesRegex(m.rt.Blocked,'checkout_harness_changed'):
            m.harness_binding(checkout)

    def test_ci_requires_explicit_absolute_existing_checkout(self):
        for workspace in ('', 'relative-checkout', str(self.folder/'missing')):
            with self.subTest(workspace=workspace), patch.dict(os.environ,
                    {'GITHUB_ACTIONS':'true','GITHUB_WORKSPACE':workspace}, clear=True), \
                    self.assertRaises(AssertionError):
                observed_checkout_root()
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(observed_checkout_root(),m.ROOT.resolve())

    def test_candidate_test_root_keeps_actual_checkout_harness_separate(self):
        checkout=observed_checkout_root()
        source_candidate=self.folder/'source-candidate'
        names=CI1_HOOK_LAYOUT|{p.relative_to(m.ROOT).as_posix()
            for p in (m.ROOT/'supabase/migrations').glob('*.sql')}
        for name in names:
            target=source_candidate/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(m.ROOT/name,target)
        self.assertFalse((source_candidate/CI1_CHECKOUT_ONLY).exists())
        self.assertFalse((source_candidate/'_offline/phase6e11/controller_v1/ci.py').exists())
        with patch.object(m,'ROOT',source_candidate), patch.dict(os.environ,
                {'GITHUB_ACTIONS':'true','GITHUB_WORKSPACE':str(checkout)}):
            self.assertEqual(observed_checkout_root(),checkout)
            gate,helper,environment=self.composed_checkout_and_candidate()
            with patch.dict(os.environ,environment,clear=True):
                source,history=helper.binding(gate)
        self.assertEqual(source['loaded_locations'],
                         {'dispatcher':'checkout','boundary_helper':'candidate'})
        self.assertEqual(len(history),45)
        self.assertNotIn(CI1_CHECKOUT_ONLY,source['sources'])
        self.assertFalse(source['checkout_harness'][CI1_CHECKOUT_ONLY]['candidate_required'])
        self.assertFalse((gate.sources/CI1_CHECKOUT_ONLY).exists())

    def test_missing_checkout_harness_is_not_replaced_by_candidate(self):
        with self.assertRaisesRegex(m.rt.Blocked,'checkout_harness_missing'):
            m.harness_binding(self.folder)

    def test_composed_roots_do_not_admit_missing_wrong_or_third_root(self):
        gate,helper,environment=self.composed_checkout_and_candidate()
        for workspace in ('',str(gate.sources),str(self.folder/'unrelated')):
            with self.subTest(workspace=workspace), \
                    patch.dict(os.environ,{**environment,'GITHUB_WORKSPACE':workspace},clear=True), \
                    self.assertRaises(m.rt.Blocked):
                helper.binding(gate)
        with patch.dict(os.environ,environment,clear=True), \
                patch.object(helper,'ROOT',self.folder/'unrelated'),self.assertRaises(m.rt.Blocked):
            helper.binding(gate)
        gate.cli=m.before
        with patch.dict(os.environ,environment,clear=True),self.assertRaises(m.rt.Blocked):
            helper.binding(gate)

    def test_candidate_loaded_helper_still_checks_checkout_dispatcher_bytes(self):
        gate,helper,environment=self.composed_checkout_and_candidate()
        path=gate.sources/m.DISPATCHER
        path.write_bytes(path.read_bytes()+b'\n# unit-only drift\n')
        manifest=self.folder/'candidate.json'
        candidate=json.loads(manifest.read_text())
        candidate['sources'][m.DISPATCHER]=m.sha(path.read_bytes())
        manifest.write_text(json.dumps(candidate),encoding='utf-8')
        with patch.dict(os.environ,environment,clear=True),self.assertRaises(m.rt.Blocked):
            helper.binding(gate)

    def test_historical_lf_equivalence_records_both_raw_and_lf_hashes(self):
        checkout=b'select 1;\n';candidate=b'select 1;\r\n'
        value=m.byte_binding(checkout,candidate,m.sha(candidate),historical=True)
        self.assertEqual(value['candidate_sha256'],m.sha(candidate))
        self.assertEqual(value['checkout_sha256'],m.sha(checkout))
        self.assertNotEqual(value['candidate_sha256'],value['checkout_sha256'])
        self.assertEqual(value['candidate_lf_sha256'],value['checkout_lf_sha256'])
        self.assertEqual(value['candidate_lf_sha256'],m.sha(checkout))

    def test_canonical_equivalence_never_replaces_candidate_raw_hash(self):
        checkout=b'select 1;\n';candidate=b'select 1;\r\n'
        with self.assertRaises(m.rt.Blocked):
            m.byte_binding(checkout,candidate,m.sha(checkout),historical=True)

    def test_m45_and_other_sources_require_byte_exactness(self):
        checkout=b'select 1;\n';candidate=b'select 1;\r\n'
        with self.assertRaises(m.rt.Blocked):
            m.byte_binding(checkout,candidate,m.sha(candidate),historical=False)

    def test_historical_semantic_whitespace_and_lone_cr_changes_rejected(self):
        candidate=b'select 1;\r\n'
        for checkout in (b'select 2;\n',b'select  1;\n',b'select 1;\r',b'select 1;'):
            with self.subTest(checkout=checkout),self.assertRaises(m.rt.Blocked):
                m.byte_binding(checkout,candidate,m.sha(candidate),historical=True)

    def test_original_error_is_not_replaced_when_receipt_save_fails(self):
        token=self.token();original=ValueError('unit only')
        with patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                patch.object(m,'save',side_effect=OSError('unit only')):
            with self.assertRaises(ValueError) as raised:
                m.observed(self.gate,token,'pre_migration',Mock(side_effect=original),m.NAMES[1])
        self.assertIs(raised.exception,original)
        secondary=self.gate.result['admission_secondary_failures']
        self.assertEqual(secondary,[{'phase':'pre_migration_receipt_storage','primary_class':'ValueError',
                                    'secondary_class':'OSError','status':'NO_GO'}])
        self.assertEqual(original.admission_secondary_failures,secondary)
        self.assertNotIn('unit only',json.dumps(self.gate.result))

    def test_post_validation_save_failure_attaches_secondary_and_keeps_primary(self):
        token=self.token();result=self.result();original=ValueError('private unit value')
        with patch.object(m,'binding',side_effect=original), \
                patch.object(m,'save',side_effect=OSError('private storage value')):
            with self.assertRaises(ValueError) as raised:m.after(self.gate,token,result)
        self.assertIs(raised.exception,original)
        failures=self.gate.result['admission_secondary_failures']
        self.assertEqual(failures[0]['phase'],'post_migration_receipt_storage')
        self.assertEqual(failures[0]['primary_class'],'ValueError')
        self.assertEqual(failures[0]['secondary_class'],'OSError')
        self.assertEqual(original.admission_secondary_failures,failures)
        self.assertNotIn('private',json.dumps(self.gate.result))

    def test_receipt_failure_without_prior_error_is_recorded_and_raised(self):
        token=self.token();original=OSError('private storage value')
        with patch.object(m,'native_session',side_effect=lambda g,c:self.session(c)), \
                patch.object(m,'save',side_effect=original):
            with self.assertRaises(OSError) as raised:
                m.observed(self.gate,token,'pre_migration',lambda _: {},m.NAMES[1])
        self.assertIs(raised.exception,original)
        self.assertIsNone(self.gate.result['admission_secondary_failures'][0]['primary_class'])

    def test_reader_snapshot_always_readonly_and_closes_after_injected_stop(self):
        guard=dict.fromkeys(('pg17','bounded_statement','bounded_lock','readonly','tls'),True)
        cursor=lambda value:SimpleNamespace(description=True,fetchall=lambda:value)
        connection=SimpleNamespace(execute=Mock(side_effect=[cursor([]),cursor([guard]),
            cursor([metadata()]),cursor([])]),close=Mock())
        session=m.rt.Session(SimpleNamespace(connect=lambda:connection),'pre_migration',
                             {'limit':12,'cleanup_reserve':4},time.monotonic()+180)
        session.fail(m.rt.InjectedFailure('unit'));session.safety=True
        sample=m.snapshot(session)
        self.assertEqual(sample,metadata())
        self.assertEqual(session.used,4)
        self.assertEqual(session.connections,[])
        self.assertEqual(connection.execute.call_args_list[0].args[0],'BEGIN TRANSACTION READ ONLY')
        self.assertEqual(connection.execute.call_args_list[-1].args[0],'ROLLBACK')
        connection.close.assert_called_once()

    def test_readonly_guard_failure_prevents_metadata(self):
        guard=dict.fromkeys(('pg17','bounded_statement','bounded_lock','readonly','tls'),True)
        guard['readonly']=False
        cursor=lambda value:SimpleNamespace(description=True,fetchall=lambda:value)
        connection=SimpleNamespace(execute=Mock(side_effect=[cursor([]),cursor([guard]),cursor([])]),close=Mock())
        session=m.rt.Session(SimpleNamespace(connect=lambda:connection),'pre_migration',
                             {'limit':12,'cleanup_reserve':4},time.monotonic()+180)
        with self.assertRaises(m.rt.Blocked):m.snapshot(session)
        self.assertEqual(connection.execute.call_count,2)
        session.close()
        self.assertNotIn(m.METADATA,[call.args[0] for call in connection.execute.call_args_list])
        self.assertEqual(session.connections,[])



class InstrumentedConfirmationTests(unittest.TestCase):
    """Synthetic offline receipts; no SQL, Auth, CLI process or CI proof."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=pathlib.Path(self.temp.name)
        self.gate=SimpleNamespace(out=self.folder,sources=m.ROOT,work=self.folder,serial=10,
            result={'phase':'migration_45','migrations_applied':44})
        (self.folder/'fmz-ci-ca.crt').write_bytes(b'unit-ca')
        names=set(m.SOURCES)
        names.update(p.relative_to(m.ROOT).as_posix() for p in (m.ROOT/'supabase/migrations').glob('*.sql'))
        names.update(m.INSTRUMENTED_PREFIX+n for n in ('ci.py','pending.py','prepare.py','policy.cjs',
            'hook.cjs','entry.mjs','package.json','pnpm-lock.yaml','pnpm-workspace.yaml'))
        names.update((m.rt.PREFIX+'cli_stat_reader.py',m.rt.PREFIX+'sql_protocol.py',
                      '_offline/phase6e_server_v1/cli_isolation.py'))
        self.hashes={n:m.sha((m.ROOT/n).read_bytes()) for n in names}
        (self.folder/'candidate.json').write_text(json.dumps({'sha256':'c'*64,'sources':self.hashes}))
        history=sorted(pathlib.PurePosixPath(n).name.split('_')[0]
                       for n in names if n.startswith('supabase/migrations/'))
        self.token=m.Boundary(self.gate,{'source_commit':'b'*40,'candidate_sha256':'c'*64,
                              'sources':self.hashes},history)
        self.saved={}
        self.gate.save=lambda n,v:self.saved.update({n:copy.deepcopy(v)})
        self.modules=m.instrumented_modules(self.gate,self.token)
        self.pending,prepare,reader,protocol,isolation,manifest=self.modules
        # Use the independently recorded Node-policy hashes, not the verifier's parser.
        self.asts=list(RealMigrationASTTests.EXPECTED)
        self.policy=dict(version=1,environment='disposable_ci',upstream_commit=prepare.UPSTREAM,
            source_commit='b'*40,candidate_sha256='c'*64,invocation_id='90c00000-0000-4000-8000-000000000009',
            slot='quota',cap=64,closure_reserve=1,dry_run=False,host='127.0.0.1',port=54322,
            database='postgres',user='postgres',ca_sha256=m.sha(b'unit-ca'),
            expected_history_versions=history[:-1],migrations=[dict(version=m.VERSION,
            name=pathlib.PurePosixPath(m.M45).stem.split('_',1)[1],sha256=m.PRESERVED[m.M45],
            ast_hashes=self.asts)])
        self.isolation=dict(original='on',restored=True,commands=8,primary_error_class=None,
            protocol=[dict(statement_sha256=m.sha(s.encode()),confirmed=True) for s in [
                isolation.SETTING,"alter system set cron.launch_active_jobs='off'",'select pg_reload_conf()',
                isolation.SETTING,isolation.ACTIVE,"alter system set cron.launch_active_jobs='on'",
                'select pg_reload_conf()',isolation.SETTING]])
        self.receipt=dict(scope='DISPOSABLE_CI_ONLY',hosted_admission=False,complete=True,
            profile='canonical_45',invocation_id=self.policy['invocation_id'],
            expected_migration=m.M45,expected_migration_sha256=m.PRESERVED[m.M45],
            requested_arguments=['migration','up','--local'],execution_mode='source_instrumented_db_url',
            executed_argument_shape=['db','push','--db-url','<private-loopback-verify-full>',
                '--skip-vault','--yes','--include-all','--output-format','json'],
            app_profile_mutated=False,application_run_started=False,
            phase='migration_45',source_commit='b'*40,candidate_sha256='c'*64,query_ms=5000,
            cli_seconds=45,output_max_bytes=8192,actual_migration_execution=True,cli_exit_code=0,
            output_sha256=m.sha(b''),migration_sources={k:v for k,v in self.hashes.items()
                if k.startswith('supabase/migrations/')},observer_commands=8,
            observer_trace=[dict(sha256=protocol.single(s)['sha256'],kind='numeric_observer',
                protocol_commands=1,confirmed=True) for s in ['BEGIN TRANSACTION READ ONLY',
                "select current_setting('transaction_read_only')='on' readonly",reader.SQL,'ROLLBACK']]*2,
            tracking=dict(before='top',after='top',utility_before='on',utility_after='on',valid=True),
            ci_cron_restored=True,ci_bootstrap_sql_commands=8,
            build=dict(upstream_commit=prepare.UPSTREAM,source_before_lf=prepare.PINS,hosted_admission=False,
                entry_sha256=m.sha(prepare.PATCHED_ENTRY.encode()),
                hook_sources={n:self.hashes[m.INSTRUMENTED_PREFIX+n] for n in prepare.COPY}))
        self.gate.serial=18
        self.regenerate()

    def reference(self,name,raw):
        path=self.folder/name;path.write_bytes(raw)
        return {'path':name,'sha256':m.sha(raw)}

    def regenerate(self):
        lines=[];events=[];previous='0'*64;frames={}
        def append(event,**data):
            nonlocal previous
            row=dict(sequence=len(events)+1,previous_sha256=previous,event=event,**data)
            raw=json.dumps(row,separators=(',', ':')).encode()
            previous=m.sha(raw);events.append(row);lines.append(raw+b'\n')
        append('preregister',policy_sha256=m.sha(json.dumps(self.policy,separators=(',', ':')).encode()),
            **{k:self.policy[k] for k in ('source_commit','candidate_sha256','upstream_commit','invocation_id',
                'environment','slot','cap','closure_reserve','dry_run')},
            observer_commands_reserved=8,hosted_admission=False,schema=1)
        append('connect_attempt',id=1,tls_verify_full=True)
        def frame(kind,ids):
            append('frontend_frame',type=kind,sql_ids=ids)
            append('frontend_write_returned',type=kind);frames[kind]=frames.get(kind,0)+1
        frame('SSLRequest',[]);frame('StartupMessage',[])
        commands=0
        def dispatch(category,ast):
            nonlocal commands
            commands+=1
            append('dispatch',id=commands,category=category,ast_sha256=ast,kind='UnitOnly',
                   protocol='simple',outcome='unknown_consumed')
            frame('Q',[commands]);append('outcome',id=commands,outcome='command_complete')
        dispatch('migration_metadata','e'*64)
        append('history_snapshot',command_id=1,count=len(self.policy['expected_history_versions']),
            matches_policy=True,versions_sha256=m.sha(json.dumps(self.policy['expected_history_versions'],
                separators=(',', ':')).encode()))
        for ast in self.policy['migrations'][0]['ast_hashes']:dispatch('migration',ast)
        target=self.policy['migrations'][0]
        append('history_bind',migration_sha256=target['sha256'],version=target['version'],
               statement_count=len(target['ast_hashes']))
        dispatch('migration_history','f'*64)
        append('terminal',complete=True,confirmed_sql=commands,sql_dispatches=commands,unknown_consumed=0,
            connection_attempts=1,frontend_frames_by_type=frames,frontend_write_returned_by_type=frames,
            hosted_admission=False,observer_commands=0)
        self.receipt['ledger_ref']=self.reference('canonical-unit.ledger.jsonl',b''.join(lines))
        self.receipt['policy_ref']=self.reference('canonical-unit.policy.json',
                                                  json.dumps(self.policy).encode())
        isolation_ref=self.reference('canonical-45-cli-predispatch-cli-isolation-0.json',
                                     json.dumps(self.isolation).encode())
        self.receipt['isolation_receipt']=isolation_ref['path']
        self.receipt['isolation_receipt_sha256']=isolation_ref['sha256']
        self.receipt.update(header=events[0],terminal=events[-1],events=events,
            terminal_recorded=True,journal_sha256=m.sha(b''.join(lines)),event_count=len(events))
        self.receipt['policy']=copy.deepcopy(self.policy)
        self.receipt['invocation_id']=self.policy['invocation_id']
        self.receipt['numeric_coverage']=dict(all_protocol_visible=True,query_text_read=False,
            protocol_commands=commands,numeric_calls_minus_reader=commands,temp_written=0,
            statements=[dict(queryid='1',calls=commands+4,temp_written=0,wal=123)])
        return self.write_receipt()

    def write_receipt(self):
        ref=self.reference(m.CANONICAL_RECEIPT,json.dumps(self.receipt,sort_keys=True).encode())
        return {'instrumented_receipt':ref['path'],'sha256':ref['sha256']}

    def confirm(self):
        return m.confirmed_result(self.gate,self.token,self.write_receipt())

    def test_instrumented_success_uses_real_file_hash_no_legacy_receipt(self):
        result=self.confirm()
        self.assertEqual(result['execution_mode'],'source_instrumented_db_url')
        self.assertEqual(result['parent_bootstrap_dispatches'],1)
        self.assertEqual(result['isolation_commands'],8)
        self.assertNotIn('stdout_sha256',result)
        self.assertFalse(list(self.folder.glob('*-cli-migration.json')))

    def test_policy_44_m45_source_identity_and_cap_are_not_labels(self):
        changes=[('cap',65),('expected_history_versions',self.token.history),('host','example.invalid'),
            ('source_commit','a'*40),('candidate_sha256','a'*64),('invocation_id',m.rt.OLD_RUN),
            ('invocation_id',m.rt.NEW_RUN),('dry_run',True),('ca_sha256','a'*64)]
        original=copy.deepcopy(self.policy)
        for key,value in changes:
            with self.subTest(key=key,value=value):
                self.policy=copy.deepcopy(original);self.policy[key]=value;self.regenerate()
                with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_self_consistent_wrong_m45_ast_still_rejected(self):
        self.policy['migrations'][0]['ast_hashes']=['d'*64]
        self.regenerate()
        with self.assertRaisesRegex(m.rt.Blocked,'m45_ast'):self.confirm()

    def test_wrong_m45_hash_and_second_migration_rejected(self):
        self.policy['migrations'][0]['sha256']='a'*64;self.regenerate()
        with self.assertRaises(m.rt.Blocked):self.confirm()
        self.policy['migrations'][0]['sha256']=m.PRESERVED[m.M45]
        self.policy['migrations'].append(copy.deepcopy(self.policy['migrations'][0]));self.regenerate()
        with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_receipt_hash_and_fixed_name_and_alias_are_checked(self):
        ref=self.write_receipt();ref['sha256']='a'*64
        with self.assertRaises(m.rt.Blocked):m.confirmed_result(self.gate,self.token,ref)
        ref=self.write_receipt();ref['instrumented_receipt']='../'+m.CANONICAL_RECEIPT
        with self.assertRaises(m.rt.Blocked):m.confirmed_result(self.gate,self.token,ref)
        self.receipt['policy_ref']=self.receipt['ledger_ref']
        with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_raw_sidecar_corruption_never_replays_sorted_receipt_as_original(self):
        for field in ('ledger_ref','policy_ref','isolation_receipt'):
            with self.subTest(field=field):
                self.regenerate()
                name=self.receipt[field] if field=='isolation_receipt' else self.receipt[field]['path']
                path=self.folder/name;path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_ledger_terminal_events_and_unknown_must_match_actual_replay(self):
        for key,change in [('terminal',lambda d:d.update(complete=False)),
                          ('terminal',lambda d:d.update(unknown_consumed=1)),
                          ('header',lambda d:d.update(invocation_id='a'*36)),
                          ('events',lambda d:d.pop())]:
            with self.subTest(key=key):
                self.regenerate();change(self.receipt[key])
                with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_failed_exit_unknown_boolean_or_incomplete_never_confirms(self):
        for key,value in [('complete',False),('cli_exit_code',1),('cli_exit_code',False),
                          ('actual_migration_execution',False),('phase','local_app_schema'),
                          ('profile','local_app'),('expected_migration','wrong.sql'),
                          ('expected_migration_sha256','a'*64),('requested_arguments',['db','push']),
                          ('executed_argument_shape',[]),('app_profile_mutated',True),
                          ('application_run_started',True),('invocation_id','a'*36)]:
            with self.subTest(key=key):
                old=self.receipt[key];self.receipt[key]=value
                with self.assertRaises(m.rt.Blocked):self.confirm()
                self.receipt[key]=old

    def test_eight_actual_observer_commands_required(self):
        original=copy.deepcopy(self.receipt['observer_trace'])
        for mode in ('missing','unconfirmed','different_hash','count_boolean'):
            with self.subTest(mode=mode):
                self.regenerate()
                self.receipt['observer_trace']=copy.deepcopy(original)
                self.receipt['observer_commands']=8
                if mode=='missing':self.receipt['observer_trace'].pop()
                if mode=='unconfirmed':self.receipt['observer_trace'][0]['confirmed']=False
                if mode=='different_hash':self.receipt['observer_trace'][0]['sha256']='a'*64
                if mode=='count_boolean':self.receipt['observer_commands']=True
                with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_numeric_counter_math_temp0_and_tracking_required(self):
        for mode in ('count','sum','temp','negative_wal','tracking','reset_queryid'):
            with self.subTest(mode=mode):
                self.regenerate();n=self.receipt['numeric_coverage']
                if mode=='count':n['protocol_commands']+=1
                if mode=='sum':n['statements'][0]['calls']+=1
                if mode=='temp':n['statements'][0]['temp_written']=1
                if mode=='negative_wal':n['statements'][0]['wal']=-1
                if mode=='tracking':self.receipt['tracking']['after']='none'
                if mode=='reset_queryid':n['statements'].append(copy.deepcopy(n['statements'][0]))
                with self.assertRaises(m.rt.Blocked):self.confirm()
                self.receipt['tracking']['after']='top'

    def test_isolation_restore_ref_trace_and_serial_are_required(self):
        original=copy.deepcopy(self.isolation)
        for mode in ('restored','trace','primary','serial'):
            with self.subTest(mode=mode):
                self.isolation=copy.deepcopy(original);self.gate.serial=18
                if mode=='restored':self.isolation['restored']=False
                if mode=='trace':self.isolation['protocol'][0]['confirmed']=False
                if mode=='primary':self.isolation['primary_error_class']='TimeoutExpired'
                if mode=='serial':self.gate.serial=19
                self.regenerate()
                with self.assertRaises(m.rt.Blocked):self.confirm()

    def test_changed_manifest_or_loaded_dependency_is_blocked(self):
        manifest=self.folder/'candidate.json';raw=manifest.read_bytes()
        manifest.write_bytes(raw+b' ')
        with self.assertRaises(m.rt.Blocked):self.confirm()
        manifest.write_bytes(raw)
        expected=pathlib.Path.read_bytes
        def changed(path):
            data=expected(path)
            return data+b'\n' if path.name=='pending.py' else data
        with patch.object(pathlib.Path,'read_bytes',changed),self.assertRaises(m.rt.Blocked):
            self.confirm()

    def test_prior_canonical_receipt_cannot_be_reused(self):
        token=m.Boundary(self.gate,self.token.binding,self.token.history)
        with self.assertRaisesRegex(m.rt.Blocked,'instrumented_result'):
            m.confirmed_result(self.gate,token,self.write_receipt())

    def test_after_failure_consumes_token_no_post_sql_or_success_receipt(self):
        self.token.sample=metadata()
        self.gate._migration_failure_boundary=self.token
        self.receipt['complete']=False
        result=self.write_receipt()
        with patch.object(m,'binding',return_value=(self.token.binding,self.token.history)), \
                patch.object(m,'native_session') as native,self.assertRaises(m.rt.Blocked):
            m.after(self.gate,self.token,result)
        native.assert_not_called();self.assertTrue(self.token.consumed)
        self.assertFalse(self.saved[m.NAMES[2]]['component_verified'])
        with self.assertRaises(m.rt.Blocked):m.after(self.gate,self.token,result)


class RealMigrationASTTests(unittest.TestCase):
    # Original policy bytes from CI41628119054, not a successful boundary receipt.
    EXPECTED = (
        'cf42ac1cd33d26233b52381753828b18e958da999940f2c3fd6aa07f05a982b2',
        '64a6a28f94caec1c70526bb9683ae0285153f9ab834c2a79e1cf02b335ea9e89',
        '136c59fb570535087dc0d55833c3883b2834912d8b46592ef5f3b6cc6dc9b12b',
        '3e2fb2c591919f629a6cb9c44770047da4f5bc69a4263eb9b6461db527e6962e',
        '9bd5738ada9607a7c80d7f683161a95e5d307bd4dfba8cdcbfd8c7056700de0a',
        '9fcc459403602b52bbdbecd7a0d953e5986654d74da6ff1ab05d6bdd5b3e0ec8',
        'bd833a3db029af6c6156451a99a3a444c312f86a918a01e66df0f76a89836ffd',
        'e70a01f9c1b94496486bd83473e7d35fd70631d085749be2978b3c58e579eb31',
        '11bdafe32146b29da55ccec779205b347d07ca916a713d6a241f3ec5af2cbf1b')

    def test_real_pinned_m45_matches_original_node_policy(self):
        import sql_protocol
        raw = (m.ROOT / m.M45).read_bytes()
        self.assertEqual(m.sha(raw), m.PRESERVED[m.M45])
        tree = json.loads(sql_protocol.parser().parser.parse_sql_json(raw.decode()))
        actual = tuple(m.sha(json.dumps(m.canonical_ast(row['stmt']),
                       separators=(',', ':'), ensure_ascii=False).encode())
                       for row in tree['stmts'])
        self.assertEqual(actual, self.EXPECTED)

    def test_only_defelem_integer_offset_is_ignored(self):
        base = {'DefElem': {'defname': 'as', 'arg': {'String': {'sval': 'body'}}, 'arg_location': 23}}
        moved = copy.deepcopy(base); moved['DefElem']['arg_location'] = 144
        self.assertEqual(m.canonical_ast(base), m.canonical_ast(moved))
        changed = copy.deepcopy(base); changed['DefElem']['arg']['String']['sval'] = 'different'
        self.assertNotEqual(m.canonical_ast(base), m.canonical_ast(changed))
        self.assertEqual(m.canonical_ast({'OtherNode': {'arg_location': 23}}),
                         {'OtherNode': {'arg_location': 23}})
        for value in (True, '23', None):
            changed['DefElem']['arg_location'] = value
            with self.assertRaises(m.rt.Blocked): m.canonical_ast(changed)


if __name__=='__main__':unittest.main()
