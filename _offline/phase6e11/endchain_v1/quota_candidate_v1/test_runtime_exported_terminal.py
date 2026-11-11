"""Pure original-byte regressions; synthetic records are not actual CI proof."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

from quota_candidate_v1 import runtime_exported_terminal as m


def inventory(values):
    raw = {name:m.canonical(value) for name,value in values.items()}
    refs = [{'path':name,'sha256':m.sha(data),'bytes':len(data)} for name,data in raw.items()]
    return m.Originals(raw,refs)


def journal(rows):
    raw = b''
    for i,row in enumerate(rows,1):
        row = {'sequence':i,'register_sha256':'a'*64,
            'previous_bytes_sha256':m.sha(raw),**row}
        raw += m.canonical(row)+b'\n'
    name = 'root-command-ledger.ledger.txt'
    ref = {'path':name,'sha256':m.sha(raw),'bytes':len(raw)}
    return m.Originals({name:raw},[ref]),[ref]


def events():
    event = {'command_id':'sample','node_id':'sample','units':1,'reserve_after':0,
        'hosted_units':1,'hosted_reserve_after':0,'domain':'local',
        'state':'precharged','numeric_confirmed':False}
    base = {'event_ordinal':0,'reserved_consumed':1,'observed_sql_commands':0,
        'hosted_equivalent_reserved':1,'stopped':False,'closed':False,'event':event}
    confirmed = {**base,'observed_sql_commands':1,'event':{**event,'state':'confirmed',
        'numeric_confirmed':True,'observed_sql_commands':1}}
    return [base,confirmed,{**confirmed,'closed':True}]


class OriginalTests(unittest.TestCase):
    def test_exact_inventory(self):
        e = inventory({'a.json':{'value':1}})
        self.assertEqual(e.obj('a.json'),{'value':1})

    def test_missing_original(self):
        with self.assertRaises(m.Missing):
            inventory({'a.json':{}}).raw('b.json')

    def test_duplicate_json_rejected(self):
        with self.assertRaisesRegex(m.Invalid,'duplicate_json_key'):
            m.decode(b'{"value":1,"value":2}')

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(m.Invalid,'nonfinite_json'):
            m.decode(b'{"value":NaN}')

    def test_case_alias_rejected(self):
        raw = {'a.json':b'{}','A.json':b'{}'}
        with self.assertRaisesRegex(m.Invalid,'original_alias'):
            m.Originals(raw,[{'path':k,'sha256':m.sha(v),'bytes':2} for k,v in raw.items()])

    def test_bool_size_rejected(self):
        with self.assertRaisesRegex(m.Invalid,'original_size'):
            m.Originals({'a.json':b'0'},[{'path':'a.json','sha256':m.sha(b'0'),'bytes':True}])

    def test_unlisted_original_rejected(self):
        with self.assertRaisesRegex(m.Invalid,'original_exact_inventory'):
            m.Originals({'a.json':b'{}','extra.json':b'{}'},[{'path':'a.json','sha256':m.sha(b'{}'),'bytes':2}])

    def test_tampered_original_rejected(self):
        with self.assertRaisesRegex(m.Invalid,'original_bytes'):
            m.Originals({'a.json':b'{}'},[{'path':'a.json','sha256':'f'*64,'bytes':2}])

    def test_unsafe_paths(self):
        for name in ('../a.json','/a.json','C:/a.json','a\\b.json','a/CON.txt','a//b.json'):
            with self.subTest(name=name),self.assertRaises(m.Invalid):
                m.path_name(name)


class RootTests(unittest.TestCase):
    def test_replays_numeric_prefix(self):
        e,refs = journal(events())
        result = m.root_chains(e,'a'*64,refs)
        self.assertEqual(result[0]['observed_sql_commands'],1)
        self.assertEqual(result[0]['unknown_event_ordinals'],[])
        self.assertNotIn('case_pass',result[0])

    def test_first_confirm_without_precharge_denied(self):
        e,refs = journal(events()[1:])
        with self.assertRaisesRegex(m.Invalid,'root_precharge_first'):
            m.root_chains(e,'a'*64,refs)

    def test_mutated_units_denied(self):
        rows = events(); rows[1]['event']['units'] = 2
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_event_mutation'):
            m.root_chains(e,'a'*64,refs)

    def test_refund_denied(self):
        rows = events(); rows[-1]['reserved_consumed'] = 0
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_journal_numeric'):
            m.root_chains(e,'a'*64,refs)

    def test_bool_counter_denied(self):
        rows = events(); rows[0]['reserved_consumed'] = True
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_journal_numeric'):
            m.root_chains(e,'a'*64,refs)

    def test_unsealed_denied(self):
        e,refs = journal(events()[:-1])
        with self.assertRaisesRegex(m.Invalid,'root_journal_not_closed'):
            m.root_chains(e,'a'*64,refs)

    def test_append_after_close_denied(self):
        rows = events();rows.append(copy.deepcopy(rows[-1]))
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_journal_latch'):
            m.root_chains(e,'a'*64,refs)

    def test_stopped_latch_cannot_clear(self):
        rows = events();rows[1]['stopped'] = True
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_journal_latch'):
            m.root_chains(e,'a'*64,refs)

    def test_unknown_cannot_become_confirmed(self):
        rows = events();rows[1]['event']['state'] = 'unknown_consumed'
        rows[2]['event'] = {**rows[1]['event'],'state':'confirmed'}
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_unknown_reclassified'):
            m.root_chains(e,'a'*64,refs)

    def test_unknown_retained_not_success(self):
        rows = events()
        for row in rows[1:]:
            row['event'] = {**row['event'],'state':'unknown_consumed','numeric_confirmed':False}
        e,refs = journal(rows)
        self.assertEqual(m.root_chains(e,'a'*64,refs)[0]['unknown_event_ordinals'],[0])

    def test_hosted_cap_unchanged(self):
        rows = events();rows[-1]['hosted_equivalent_reserved'] = 2352
        e,refs = journal(rows)
        with self.assertRaisesRegex(m.Invalid,'root_journal_numeric'):
            m.root_chains(e,'a'*64,refs)

    def test_register_reconstruction(self):
        binding = {'run_id':'77777777-7777-4777-8777-000000000001'}
        register = {'executable_program':None,'bound_complete':False}
        register['full_register_sha256'] = m.sha(m.canonical(register))
        value = {'format':'admission-root-original-evidence-v1','binding':binding,
            'program':None,'register':register}
        payload = m.canonical(value)
        member = {'path':'root-original-00.txt','sha256':m.sha(payload),'bytes':len(payload)}
        index = {'format':'admission-root-original-index-v1','members':[member],
            'payload_sha256':m.sha(payload),'payload_bytes':len(payload),
            'register_sha256':register['full_register_sha256'],'binding_sha256':m.sha(m.canonical(binding))}
        raw = {'root-original-00.txt':payload,'root-original-index.json':m.canonical(index)}
        e = m.Originals(raw,[{'path':k,'sha256':m.sha(v),'bytes':len(v)} for k,v in raw.items()])
        self.assertEqual(m.root_original(e,binding),value)
        with self.assertRaisesRegex(m.Invalid,'root_binding'):
            m.root_original(e,{'run_id':'wrong'})


class AdmissionTests(unittest.TestCase):
    def test_no_status_only_pass(self):
        case = {'status':'CASE_PASS'}
        with self.assertRaises(m.Invalid):
            m.verify_exported_terminal({'case-execution.json':m.canonical(case)},case,
                originals={},source_commit='a'*40,ci_run='1',candidate_sha256='b'*64,
                expected_sources={},trusted_root=pathlib.Path(__file__).parent)

    def test_case_argument_must_equal_original(self):
        with self.assertRaisesRegex(m.Invalid,'case_not_original'):
            m.verify_exported_terminal({'case-execution.json':b'{"status":"NO_GO"}'},{'status':'CASE_PASS'},
                originals={},source_commit='a'*40,ci_run='1',candidate_sha256='b'*64,
                expected_sources={},trusted_root=pathlib.Path(__file__).parent)

    def test_artifact_python_never_loaded(self):
        payloads = {'case-execution.json':b'{}','malicious.py':b'raise AssertionError("executed")'}
        with self.assertRaises(m.Invalid):
            m.verify_exported_terminal(payloads,{},originals={},source_commit='a'*40,
                ci_run='1',candidate_sha256='b'*64,expected_sources={},trusted_root=pathlib.Path(__file__).parent)


def sample():
    return {'reset':'2026-11-11T00:00:00Z','dealloc':0,
        'background':{'reset':'2026-11-11T00:00:00Z','temp_bytes':0},
        'health':{'io_wait':0,'long_active':0},'statements':[
            {'queryid':'123','calls':1,'since':'2026-11-11T00:00:00Z',
             'temp_read':0,'temp_written':0,'wal':'0','wal_records':'0','wal_fpi':'0','exec_ms':0.25}]}


class NumericShapeTests(unittest.TestCase):
    def test_actual_snapshot_field_types(self):
        self.assertIsNone(m.sample_shape(sample()))

    def test_duplicate_query_id_cannot_hide_bad_first_row(self):
        value=sample();value['statements'].insert(0,{**value['statements'][0],'wal':'100'})
        with self.assertRaisesRegex(m.Invalid,'io_queryid'):m.sample_shape(value)

    def test_bool_integer_counter_denied(self):
        value=sample();value['statements'][0]['calls']=True
        with self.assertRaisesRegex(m.Invalid,'io_integer_counter'):m.sample_shape(value)

    def test_lossless_canonical_signed_int64_query_id(self):
        for qid in ('01','-0',str(2**63),str(-(2**63)-1),123,True):
            with self.subTest(qid=qid):
                value=sample();value['statements'][0]['queryid']=qid
                with self.assertRaisesRegex(m.Invalid,'io_queryid'):m.sample_shape(value)

    def test_negative_or_nonfinite_time_denied(self):
        for time in (-1,float('nan'),float('inf'),True):
            value=sample();value['statements'][0]['exec_ms']=time
            with self.subTest(time=time),self.assertRaisesRegex(m.Invalid,'io_time'):m.sample_shape(value)

    def test_missing_numeric_wal_class_denied(self):
        value=sample();del value['statements'][0]['wal_records']
        with self.assertRaisesRegex(m.Invalid,'io_row_shape'):m.sample_shape(value)

    def test_wal_value_not_coerced_from_bool_or_float(self):
        for wal in (False,0.0,'-1','NaN','01'):
            value=sample();value['statements'][0]['wal']=wal
            with self.subTest(wal=wal),self.assertRaisesRegex(m.Invalid,'io_wal_counter'):m.sample_shape(value)

    def test_background_counter_cannot_be_bool(self):
        value=sample();value['background']['temp_bytes']=False
        with self.assertRaisesRegex(m.Invalid,'io_background'):m.sample_shape(value)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.folder='unit-originals'
        self.plan=(('read','SELECT 1'),)
        source='unit/source.py';raw=b'# source-only unit fixture\n'
        self.trusted=types.SimpleNamespace(sources={source:m.sha(raw)},raw=lambda _:raw)
        bound={'status':'SELECTED_MODULE_SOURCE_BINDING_PASS','selected_module_count':1,
            'modules':[{'relative_path':source,'candidate_sha256':m.sha(raw),
                'actual_sha256':m.sha(raw),'canonicalization':'byte-exact'}]}
        event={'ordinal':1,'phase':'read','sql_sha256':m.sha(b'SELECT 1'),'confirmed':True}
        rows=[{'value':1}]
        self.values={self.folder+'/charge-01.json':{**event,'confirmed':False},
            self.folder+'/query-01-read.json':{'format':'c-query-observation-v1',
                'case_run':'unit','component':'unit','phase':'read','scope_sha256':'a'*64,
                'protocol':event,'rows':rows,'rows_sha256':m.sha(m.canonical(rows)),
                'raw_rows_sha256':m.sha(m.canonical(rows)),'source_binding':bound,
                'query_io':{'observed':False,'reason':'not_instrumented_by_this_dispatch'}}}

    def replay(self):
        return m.protocol(inventory(self.values),self.folder,self.plan,run_id='unit',
            scope_sha='a'*64,trusted=self.trusted,component='unit')

    def record(self):
        return self.values[self.folder+'/query-01-read.json']

    def test_projection_replayed_without_inventing_io(self):
        self.assertEqual(self.replay(),{'read':[{'value':1}]})

    def test_no_precharge_no_replay(self):
        del self.values[self.folder+'/charge-01.json']
        with self.assertRaises(m.Missing):self.replay()

    def test_changed_row_commitment_denied(self):
        self.record()['rows'][0]['value']=2
        with self.assertRaisesRegex(m.Invalid,'protocol_rows'):self.replay()

    def test_boolean_command_ordinal_denied(self):
        self.record()['protocol']['ordinal']=True
        with self.assertRaisesRegex(m.Invalid,'protocol_return'):self.replay()

    def test_asserted_measured_io_cannot_replace_unmeasured_contract(self):
        self.record()['query_io']={'observed':True,'wal':0}
        with self.assertRaisesRegex(m.Invalid,'protocol_io_contract'):self.replay()

    def test_other_case_projection_denied(self):
        self.record()['case_run']='different'
        with self.assertRaisesRegex(m.Invalid,'protocol_binding'):self.replay()

    def test_extra_query_not_silently_ignored(self):
        self.values[self.folder+'/query-02-extra.json']=copy.deepcopy(self.record())
        with self.assertRaisesRegex(m.Invalid,'protocol_extra_or_missing_query'):self.replay()

    def test_source_change_denied(self):
        self.record()['source_binding']['modules'][0]['candidate_sha256']='b'*64
        with self.assertRaisesRegex(m.Invalid,'source_binding_hash'):self.replay()


class RootBridgeTests(unittest.TestCase):
    def test_incomplete_compiler_cannot_use_closed_journal_as_authority(self):
        register={'bound_complete':False,'total_local_ci_upper_bound':None,
            'total_hosted_equivalent_upper_bound':None,'hosted_limit':2349,
            'source_inventory_complete':False,'missing_costs':['source_gap']}
        module=types.SimpleNamespace(build_root_register=lambda *args,**kwargs:register)
        trusted=types.SimpleNamespace(root=pathlib.Path('.'),module=mock.Mock(return_value=module))
        result=m.root_replay(None,trusted,{}, {'status':'NUMERIC_ACCOUNTING_CLOSED'},register)
        self.assertEqual(result['status'],'ROOT_SOURCE_BOUND_INCOMPLETE')
        self.assertIn('root_source_bound_incomplete',result['missing'])
        trusted.module.assert_called_once_with('admission_budget_root_runtime')

    def test_archive_register_cannot_replace_source_rebuild(self):
        module=types.SimpleNamespace(build_root_register=lambda *args,**kwargs:{'bound_complete':False})
        trusted=types.SimpleNamespace(root=pathlib.Path('.'),module=lambda _:module)
        with self.assertRaisesRegex(m.Invalid,'root_source_register_changed'):
            m.root_replay(None,trusted,{}, {},{'bound_complete':True})

    def test_archive_and_flat_collision_rejected_before_bootstrap_replay(self):
        module=types.SimpleNamespace(verify_bootstrap_case=mock.Mock())
        trusted=types.SimpleNamespace(module=lambda _:module)
        with self.assertRaisesRegex(m.Invalid,'bootstrap_payload_collision'):
            m.bootstrap(inventory({'same.json':{'value':1}}),trusted,
                {'same.json':b'{"value":2}'},{},'a'*40,'1','b'*64)
        module.verify_bootstrap_case.assert_not_called()


if __name__=='__main__':
    unittest.main()
