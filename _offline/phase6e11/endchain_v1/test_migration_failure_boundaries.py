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


if __name__=='__main__':unittest.main()
