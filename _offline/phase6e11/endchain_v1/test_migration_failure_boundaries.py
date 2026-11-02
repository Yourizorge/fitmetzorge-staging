"""Unit-only boundaries/negative cases; never substitute for real CI receipts."""
import copy
import json
import os
import pathlib
import subprocess
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import migration_failure_boundaries as m


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
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':m.REPOSITORY,'GITHUB_REF':'refs/heads/main',
                     'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'12'}
        names=set(m.SOURCES) | {p.relative_to(m.ROOT).as_posix() for p in (m.ROOT/'supabase/migrations').glob('*.sql')}
        files={name:m.sha((m.ROOT/name).read_bytes()) for name in names}
        candidate={'sha256':'c'*64,'sources':files}
        path=self.folder/'candidate.json'
        path.write_text(json.dumps(candidate),encoding='utf-8')
        self.gate.sources=m.ROOT;self.gate.work=m.ROOT;self.gate.cli=m.before
        with patch.dict(os.environ,environment,clear=True):
            source,history=m.binding(self.gate)
            self.assertEqual(source['sources'][m.M45],m.PRESERVED[m.M45])
            self.assertEqual(source['source_bytes'][m.M45]['canonicalization'],'byte-exact')
            self.assertEqual(sum(row['canonicalization']=='CRLF-to-LF-only'
                                 for row in source['source_bytes'].values()),44)
            self.assertLess(len(json.dumps({'source_binding':source},indent=2).encode()),m.RECEIPT_LIMIT-8192)
            self.assertEqual(len(history),45)
            self.assertEqual(history[-1],m.VERSION)
            files[m.rt.PREFIX+'migration_failure_boundaries.py']='0'*64
            path.write_text(json.dumps(candidate),encoding='utf-8')
            with self.assertRaises(m.rt.Blocked):m.binding(self.gate)

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
