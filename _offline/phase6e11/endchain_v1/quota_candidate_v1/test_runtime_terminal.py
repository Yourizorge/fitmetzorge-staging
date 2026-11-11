"""Pure terminal fixtures and real producer-byte binding, not PG/worker proof."""
import argparse
import copy
import importlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p / 'supabase/migrations').is_dir()), None)
RUNTIME_ROOT = HERE
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root', type=pathlib.Path, default=ROOT)
    parser.add_argument('--runtime-root', type=pathlib.Path, default=HERE)
    options, rest = parser.parse_known_args()
    ROOT, RUNTIME_ROOT = options.source_root, options.runtime_root
    sys.argv = [sys.argv[0], *rest]
if ROOT is None:
    raise RuntimeError('isolated tests require --source-root and --runtime-root')
sys.path.insert(0, str(ROOT / '_offline/phase6e11/endchain_v1'))
sys.path.insert(0, str(RUNTIME_ROOT.parent))
from quota_candidate_v1 import runtime_terminal as m


def meter():
    return dict(used=3, limit=2349, phases={'baseline': 2, 'closure': 1}, complete=True,
        events=[dict(number=1, first_command=1, commands=2, phase='baseline', confirmed=True,
                     mutation=True, reserved_cleanup=3),
                dict(number=2, first_command=3, commands=1, phase='closure', confirmed=True)])


REGISTER = dict(complete_register=True, fits=True, approved_limit=2349,
    worst_including_safety=2349, phase_budgets={'baseline': 2, 'closure': 1})


def io():
    return dict(closing_temp_written=0, closing_wal_bytes=0, query_text_read=False,
        source_classes={'a'*64: {'queryid':'1', 'readonly':True}}, readonly_queryids=['1'],
        last_pair=dict(own_temp_written=0, own_wal_bytes=0,
            queries=[dict(queryid='1', calls=1, temp_read=0, temp_written=0, wal=0, exec_ms=1.2)]))


class NumericTests(unittest.TestCase):
    def test_known_meter(self):
        self.assertEqual(m.meter_summary(meter(), REGISTER), dict(charged_commands=3,
            unknown_commands=0, phase_commands={'baseline':2, 'closure':1}))

    def test_unknown_is_consumed(self):
        value = meter()
        value['events'][0]['confirmed'] = False
        value['complete'] = False
        self.assertEqual(m.meter_summary(value, REGISTER)['unknown_commands'], 2)
        self.assertEqual(m.meter_summary(value, REGISTER)['charged_commands'], 3)

    def test_sequence_no_refund_or_gap(self):
        for key, value in [('first_command', 2), ('number', 3), ('commands', 0), ('confirmed', 1)]:
            with self.subTest(key=key):
                data = meter()
                data['events'][0][key] = value
                with self.assertRaises(ValueError): m.meter_summary(data, REGISTER)

    def test_ceiling_and_phase(self):
        for used in [True, -1, 2350]:
            data = meter(); data['used'] = used
            with self.assertRaises(ValueError): m.meter_summary(data, REGISTER)
        data = meter(); data['phases']['baseline'] = 1
        with self.assertRaises(ValueError): m.meter_summary(data, REGISTER)

    def test_actual_mismatch_not_hidden(self):
        data = meter(); data['events'][0]['actual_commands'] = 3
        with self.assertRaisesRegex(ValueError, 'meter_mismatch'): m.meter_summary(data, REGISTER)

    def test_prefix_reserve(self):
        data = meter(); data['events'][0]['reserved_cleanup'] = 2348
        with self.assertRaisesRegex(ValueError, 'prefix_reserve'): m.meter_summary(data, REGISTER)

    def test_incomplete_model(self):
        for key, value in [('fits',False), ('complete_register',False), ('worst_including_safety',2352)]:
            with self.assertRaises(ValueError): m.meter_summary(meter(), {**REGISTER, key:value})

    def test_no_false_complete_unknown(self):
        data = meter(); data['events'][0]['confirmed'] = False
        with self.assertRaises(ValueError): m.meter_summary(data, REGISTER)

    def test_safety_still_charged_not_phase_refund(self):
        data = meter(); data['events'][1]['phase'] = 'safety'; del data['phases']['closure']
        self.assertEqual(m.meter_summary(data, REGISTER)['charged_commands'], 3)

    def test_readonly_zero(self):
        m.check_io(io(), readonly=True)

    def test_read_wal_never_benign(self):
        data = io(); data['last_pair']['queries'][0]['wal'] = 192
        data['last_pair']['own_wal_bytes'] = 192
        with self.assertRaises(ValueError): m.check_io(data)

    def test_write_family_wal_not_misattributed_as_read(self):
        data = io(); data['source_classes']['a'*64]['readonly'] = False
        data['readonly_queryids'] = []
        data['last_pair']['queries'][0]['wal'] = data['last_pair']['own_wal_bytes'] = 192
        m.check_io(data)
        with self.assertRaises(ValueError): m.check_io(data, readonly=True)

    def test_temp_timeout_closing_and_classes(self):
        for mutation in [lambda d:d.update(closing_wal_bytes=1),
                         lambda d:d.update(closing_temp_written=1),
                         lambda d:d.update(query_text_read=True),
                         lambda d:d.update(readonly_queryids=[]),
                         lambda d:d['last_pair']['queries'][0].update(temp_read=1),
                         lambda d:d['last_pair']['queries'][0].update(exec_ms=5001)]:
            data = io(); mutation(data)
            with self.assertRaises(ValueError): m.check_io(data)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='terminal-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.gate = types.SimpleNamespace(out=self.root, evidence_prefix='case-')

    def test_original_bytes_hashed_not_reencoded(self):
        raw = b'{ "count" : 2 }\n'
        (self.root / 'case-terminal.json').write_bytes(raw)
        e = m.Evidence(self.gate)
        self.assertEqual(e.read('terminal.json'), {'count':2})
        self.assertEqual(e.refs['case-terminal.json'], dict(path='case-terminal.json',
            bytes=len(raw), sha256=m.digest(raw)))
        self.assertNotEqual(m.digest(raw), m.digest(m.canonical({'count':2})))

    def test_no_missing_or_partial_receipt_success(self):
        e = m.Evidence(self.gate)
        with self.assertRaises(FileNotFoundError): e.read('missing.json')
        (self.root / 'case-terminal.json').write_bytes(b'{"count":')
        with self.assertRaises(ValueError): e.read('terminal.json')

    def test_duplicate_or_nonfinite_json(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]']:
            with self.assertRaises(ValueError): m.decode(raw)

    def test_path_traversal(self):
        for name in ['../x.json', '/x.json', 'C:/x.json', 'a//b.json']:
            with self.assertRaises(ValueError): m.read_under(self.root, name)
        self.gate.evidence_prefix = '../'
        with self.assertRaises(ValueError): m.Evidence(self.gate)

    def test_bounded_receipt(self):
        (self.root / 'x.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'size'): m.read_under(self.root,'x.json',1)


class SourceTests(unittest.TestCase):
    """Use exact current producer source bytes, without invoking their runtimes."""
    @classmethod
    def setUpClass(cls):
        for name in m.PRODUCERS:
            importlib.import_module(name)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='terminal-src-')
        self.addCleanup(self.temp.cleanup)
        root = pathlib.Path(self.temp.name)
        self.root, self.out = root/'source', root/'out'
        self.out.mkdir(); self.root.mkdir()
        sources = {}
        names = set(m.PRODUCERS.values()) | {m.OWN+n for n in (*m.WORKERS,*m.INPUTS)} | {m.OWN+'runtime_terminal.py'}
        for name in names:
            if name == m.OWN+'runtime_terminal.py': path = HERE/'runtime_terminal.py'
            elif name.startswith(m.OWN): path = RUNTIME_ROOT/pathlib.PurePosixPath(name).name
            else: path = ROOT/name
            raw = path.read_bytes()
            target = self.root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            sources[name] = m.digest(raw)
        binding = dict(source_commit='a'*40, ci_run='41630541810', candidate_sha='b'*64,
                       environment='disposable_ci', hosted_permission=False, execution_admitted=False)
        self.sources = sources
        self.c = types.SimpleNamespace(quota=dict(binding=binding, root=str(self.root),
            manifest=dict(sources=sources)), workflow_recovery={})
        self.gate = types.SimpleNamespace(sources=self.root, out=self.out, result=dict(commit='a'*40,
            run_id='41630541810', candidate_sha256='b'*64))
        self.write_candidate()

    def write_candidate(self):
        (self.out/'candidate.json').write_bytes(m.canonical(dict(sha256='b'*64,sources=self.sources)))

    def test_exact_loaded_final_producer_binding(self):
        value = m.source_binding(self.gate, self.c, m.Evidence(self.gate))
        for name in ('runtime_case_entry.py','runtime_lifecycle.py','runtime_terminal.py'):
            self.assertEqual(value[m.OWN+name], self.sources[m.OWN+name])

    def test_commit_head_conflict(self):
        self.gate.result['head'] = 'c'*40
        with self.assertRaisesRegex(ValueError, 'source_run'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_missing_canonical_commit(self):
        del self.gate.result['commit']
        with self.assertRaisesRegex(ValueError, 'source_run'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_no_wrong_ci_or_candidate(self):
        for key in ('run_id','candidate_sha256'):
            before = self.gate.result[key]; self.gate.result[key] = 'bad'
            with self.assertRaises(ValueError): m.source_binding(self.gate,self.c,m.Evidence(self.gate))
            self.gate.result[key] = before

    def test_changed_final_producer_bytes(self):
        (self.root/m.OWN/'runtime_case_entry.py').write_bytes(b'# altered\n')
        with self.assertRaisesRegex(ValueError, 'producer_source'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_candidate_disk_matches_but_loaded_old_rejected(self):
        path = self.root/m.OWN/'runtime_case_entry.py'
        path.write_bytes(path.read_bytes()+b'\n# changed candidate only\n')
        self.sources[m.OWN+'runtime_case_entry.py'] = m.digest(path.read_bytes())
        self.write_candidate()
        with self.assertRaisesRegex(ValueError,'loaded_producer'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_missing_producer_not_optional(self):
        del self.sources[m.OWN+'runtime_lifecycle.py']; self.write_candidate()
        with self.assertRaisesRegex(ValueError,'producer_source'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_hosted_denied(self):
        self.c.quota['binding']['environment'] = 'staging'
        with self.assertRaisesRegex(ValueError,'local_only'):
            m.source_binding(self.gate,self.c,m.Evidence(self.gate))

    def test_no_dummy_object_success(self):
        with self.assertRaisesRegex(ValueError,'owners'):
            m.validate_runtime_termination(self.gate,self.c,types.SimpleNamespace(),case_name='normal',
                fault=None,worker_result={'status':'PASS'},original_error=None,
                fixture_closeout={'complete':True},isolation={'complete':True})


class TerminalTests(SourceTests):
    """Construct real owner types with explicit synthetic terminal state.

    The already-tested prefix verifier is stubbed only because these fixtures
    deliberately are NOT an admitted current register. Full terminal validation
    (including source_binding and numerical receipts) executes unchanged.
    """
    def setUp(self):
        super().setUp()
        from quota_candidate_v1 import runtime_adapter as adapter
        from quota_candidate_v1.runtime_faults import PhaseFaults
        from runtime_budget import RuntimeBudget
        self.adapter = adapter
        binding = self.c.quota['binding']
        binding.update(run_id='8bc257ad-77ec-46a8-b9a3-82c081f54eaa', purpose='synthetic-test-only', cap=2349)
        c = object.__new__(adapter.CaseComposition); c.quota = self.c.quota
        c.commands = [dict(command=1,phase='setup',confirmed=True),
                      dict(command=2,phase='final_closure',confirmed=True)]
        c.meter = object.__new__(adapter.CaseBudget)
        self.meter_value = meter()
        self.meter_value.update(used=744,phases={'baseline':743,'closure':1},state={
            'auth_maybe_live':False,'guard':False,'observer':False,'controls':False},
            state_confirmations=[],safety={},stopped=False,stop_reason=None)
        self.meter_value['events'][0]['commands'] = 743
        self.meter_value['events'][1]['first_command'] = 744
        c.quota['register'] = {**REGISTER,'phase_budgets':{'baseline':743,'closure':1}}
        for attr, key in [('used','used'),('limit','limit'),('phases','phases'),('state','state'),
                          ('state_confirmations','state_confirmations'),('safety_spent','safety'),
                          ('stopped','stopped'),('stop_reason','stop_reason'),('events','events')]:
            setattr(c.meter,attr,copy.deepcopy(self.meter_value[key]))
        c.meter.closed = True
        self.assertEqual(RuntimeBudget.receipt(c.meter),self.meter_value)
        c.final_pre_complete = c.final_dry_complete = c.final_post_complete = True
        c.case_preservation = types.SimpleNamespace(attempts=list(m.LABELS))
        c.auth_zero_proof = {'source':'synthetic-test-only'}
        c.case_history = types.SimpleNamespace(after=[{'version':str(i)} for i in range(48)])
        c.workflow_recovery = dict(complete=True,worker_terminated=True,secondary=[])
        fault = object.__new__(PhaseFaults)
        fault.case='normal'; fault.binding=binding; fault.fired=None
        fault.selector={}; fault.timeout_armed=False; fault.seen=1
        c.phase_faults=fault
        self.c=c; self.fault=fault
        self.life=object.__new__(adapter.CaseLifecycle)
        self.life.composition=c; self.life.gate=self.gate; self.life.run_id=binding['run_id']
        self.life.removed=self.life.workflow_complete=True; self.life.failed=False
        isolation={k:'1'*64 for k in ('pg_container','db_target_sha256','auth_target_sha256','evidence_sha256')}
        isolation.update(run_id=binding['run_id'],ci_run=binding['ci_run'],source_commit=binding['source_commit'],
            environment='disposable_ci',auth_container='2'*64,pg_system_identifier='123',database_oid=5,
            registry_empty=True,pg17=True,ssl=True,auth_database_bound=True,reused=False,
            native_ssl=True,auth_ssl=True,auth_sslmode='verify-full')
        c.quota['isolation']=isolation
        self.isolation=isolation
        self.original=None
        self.worker=dict(status='INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS',checks=18,durable_steps=89,
            closure='confirmed',environment='disposable_ci',hosted_requests=0,emails_sent=0,
            workflow=dict(pairs=71,deletes=123,next_step=83),
            proof=[dict(role=role,operation=op,after=dict(pair_complete=True,exact_contract=True))
                for role in ('a_member','a_trainer','b_member')
                for op in ('issue','verify','getUser','refresh','logout','revoked_denial')])
        self.terminal=dict(worker_terminated=True,automatic_retry=False,secrets_exported=False,messages=150,
            termination_error_class=None,cleanup_errors=[],complete=True,guard_audit_removed=True)
        from quota_candidate_v1.runtime_prefix import compatible
        cli=[]
        for index,(slot,cap) in enumerate([('quota',64),('pre_auth',28),('final',28)]):
            n=17 if index==0 else 2
            policy=dict(slot=slot,invocation_id='test-'+slot)
            policy_raw=b'  '+m.canonical(policy)+b'\n'
            ledger_raw=b'{"test_only_not_real_protocol":true}\n'
            isolated=dict(restored=True,commands=4,protocol=[{'confirmed':True} for _ in range(4)])
            full=dict(slot=slot,complete=True,run_id=binding['run_id'],source_commit=binding['source_commit'],
                candidate_sha256=binding['candidate_sha'],receipt_name='case-cli-'+slot+'.json',
                events=[dict(event='dispatch',ast_sha256='a'*64,kind='query',id=i) for i in range(n)],
                observer_trace=[{'confirmed':True} for _ in range(8)],
                numeric_coverage=dict(all_protocol_visible=True,numeric_calls_minus_reader=n,temp_written=0),
                terminal=dict(complete=True,unknown_consumed=0,sql_dispatches=n),policy=policy,
                invocation_id=policy['invocation_id'])
            for key,name,raw in [('policy_ref','case-cli-'+slot+'.policy.json',policy_raw),
                ('ledger_ref','case-cli-'+slot+'.ledger.txt',ledger_raw),
                ('isolation_ref','case-'+slot+'-cli-predispatch-cli-isolation-0.json',m.canonical(isolated))]:
                (self.out/name).write_bytes(raw); full[key]=dict(path=name,sha256=m.digest(raw))
            self.save(full['receipt_name'],full)
            row=compatible(full)
            cli.append(row); self.save('cli-protocol-'+str(index)+'.json',row)
        self.gate.cli_protocol=cli
        auth=[]
        for role in ('a_member','a_trainer','b_member'):
            for op,count in dict(issue=11,verify=21,getUser=5,refresh=27,logout=10,revoked_denial=4).items():
                row=dict(role=role,operation=op,commands=count,statements=[{'temp_written':0}])
                self.save('auth-protocol-%02d.json'%len(auth),row); auth.append(row)
        preflight={'commands':[{'confirmed':True} for _ in range(4)]}
        workflow=dict(commands=360,verified_calls=72,statements=[{'temp_written':0}])
        self.save('integral-preflight.json',preflight); self.save('workflow-auth-protocol.json',workflow)
        c.closing_receipt=adapter.counted_close(c.commands[:-1],preflight,cli,auth,workflow,
            binding['run_id'],binding['purpose'],binding)
        self.assertEqual(c.closing_receipt['global_commands'],744)
        self.save('integral-closure.json',{**c.closing_receipt,'confirmed':True})
        self.save('runtime-command-meter.json',c.meter.receipt())
        self.save('integral-complete-protocol-trace.json',dict(commands=c.commands,outer_sql_commands=2,
            environment='disposable_ci',full_chain_admission=False))
        for label in ('before','after_migration','final_pre','after_cleanup'):
            self.save('integral-gates-'+label+'.json',dict(unchanged=True,io=io(),stage='post',
                catalog_excluded_schemas=[],temporary_schema_names=[],migrations=c.case_history.after,
                absence={'all_registered_sessions':0,'all_registered_refresh_tokens':0}))
        self.save('integral-workflow-io.json',dict(terminal=io(),pairs=[io()['last_pair'] for _ in range(71)]))
        for index in range(71): self.save('integral-io-pair-%03d.json'%index,io()['last_pair'])
        for label in ('fixture_setup','fixture_closeout'): self.save('integral-'+label+'-io.json',io())
        for label in ('before','before_cleanup','after_cleanup'):
            self.save('integral-stream-'+label+'.json',dict(label=label,protected_equal=True,query_text_read=False,
                complete_by_same_snapshot_capacity=True,rows=0,protected_rows_bounded=0,tables={},plan=[],
                profiles=[io()['last_pair']],source_sha256=self.sources[m.OWN+'runtime_stream.py']))
        self.save('case-workflow-recovery.json',c.workflow_recovery)
        self.sync()

    def save(self,name,value):
        (self.out/name).write_bytes(m.canonical(value))

    def sync(self):
        self.save('registered-worker-terminal.json',self.terminal)
        self.save('case-registered-finally.json',dict(retry=False,worker_owned=True,covered_by='case.core',
            complete=self.original is None,original_exception_class=type(self.original).__name__ if self.original else None,
            fault=self.fault.receipt(),runtime_meter=self.c.meter.receipt(),secondary=[],
            commands=[{**row,'covered_by':'case.core'} for row in self.c.commands]))

    def validate(self,fixture=None):
        with patch.object(self.adapter,'verify_runtime_sources'):
            return m.validate_runtime_termination(self.gate,self.c,self.life,case_name=self.fault.case,
                fault=self.fault,worker_result=self.worker,original_error=self.original,
                fixture_closeout=fixture,isolation=self.isolation)

    def test_normal_component_never_full_case(self):
        result=self.validate({'complete':True,'case_pass':True})
        self.assertEqual(result['status'],'REGISTERED_WORKER_COMPLETE')
        self.assertEqual(result['meter']['charged_commands'],744)
        self.assertEqual([row['observed_sql_commands'] for row in result['cli']],[17,2,2])
        self.assertEqual([row['charged_commands'] for row in result['cli']],[72,36,36])
        self.assertFalse(result['case_pass']); self.assertFalse(result['full_chain_admission'])
        self.assertFalse(result['hosted_admitted']); self.assertFalse(result['fixture_closeout_validated'])
        self.assertIn('independent_fixture_auth_closeout_join',result['pending_proofs'])
        self.assertEqual(result['additional_sql_commands'],0)

    def test_missing_or_nonverifying_tls_isolation_is_rejected(self):
        original=copy.deepcopy(self.isolation)
        for key,bad in (('native_ssl',False),('auth_ssl',False),('auth_sslmode','require')):
            with self.subTest(field=key,mode='missing'):
                self.isolation=dict(original); del self.isolation[key]
                self.c.quota['isolation']=self.isolation
                with self.assertRaisesRegex(ValueError,'runtime_isolation_shape'): self.validate()
            with self.subTest(field=key,mode='invalid'):
                self.isolation={**original,key:bad}
                self.c.quota['isolation']=self.isolation
                with self.assertRaisesRegex(ValueError,'runtime_isolation_evidence'): self.validate()
        self.isolation=original
        self.c.quota['isolation']=original

    def test_worker_summary_not_enough(self):
        self.worker['proof'].pop()
        with self.assertRaisesRegex(ValueError,'auth_pairs'): self.validate()

    def test_terminal_must_reap_worker(self):
        self.terminal['worker_terminated']=False; self.sync()
        with self.assertRaisesRegex(ValueError,'worker_terminal'): self.validate()

    def test_numeric_pair_tamper(self):
        value=io()['last_pair']; value['queries'][0]['wal']=1
        self.save('integral-io-pair-003.json',value)
        with self.assertRaisesRegex(ValueError,'workflow_pair_binding'): self.validate()

    def test_nonzero_final_absence(self):
        path=self.out/'integral-gates-after_cleanup.json'; value=m.decode(path.read_bytes())
        value['absence']['all_registered_sessions']=1; self.save(path.name,value)
        with self.assertRaisesRegex(ValueError,'final_absence'): self.validate()

    def test_fault_preserves_wrapped_error_and_unknown_charge(self):
        self.fault.case='controller'; self.fault.selector={'stage':'controller_before'}
        self.fault.fired=dict(case='controller',run_id=self.life.run_id,source_commit='a'*40,
            ci_run='41630541810',candidate_sha='b'*64,original_error_code='case_injected_controller',
            event={'stage':'controller_before'},automatic_retry=False)
        self.c.meter.stopped=True; self.c.meter.events[0]['confirmed']=False
        self.original=RuntimeError('registered_worker_failed'); self.worker=None
        self.terminal['complete']=False; self.sync()
        self.save('case-fault-boundary.json',self.fault.fired)
        self.save('registered-incomplete-protocol-trace.json',dict(commands=self.c.commands,
            runtime_meter=self.c.meter.receipt(),complete=False,automatic_retry=False))
        value=self.validate()
        self.assertEqual(value['original_exception_class'],'RuntimeError')
        self.assertEqual(value['original_fault_code'],'case_injected_controller')
        self.assertEqual(value['meter']['unknown_commands'],743)
        self.assertEqual(value['meter']['charged_commands'],744)
        self.assertFalse(value['case_pass'])

    def test_early_cases_not_generic_null_auth_bypass(self):
        self.fault.case='pre_migration'
        with self.assertRaisesRegex(ValueError,'runtime_terminal_case'): self.validate()

    def test_original_error_must_match_finally(self):
        self.original=RuntimeError('not exported')
        with self.assertRaisesRegex(ValueError,'original_error'): self.validate()

    def test_raw_ledger_tamper(self):
        (self.out/'case-cli-quota.ledger.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw_hash'): self.validate()

    def test_cli_numeric_vs_reserved_not_confused(self):
        path=self.out/'case-cli-quota.json'; full=m.decode(path.read_bytes())
        full['numeric_coverage']['numeric_calls_minus_reader']=64
        self.save(path.name,full)
        with self.assertRaisesRegex(ValueError,'cli_actual_binding'): self.validate()

    def test_cli_isolation_must_restore(self):
        name='case-quota-cli-predispatch-cli-isolation-0.json'
        value=m.decode((self.out/name).read_bytes()); value['restored']=False
        self.save(name,value)
        full=m.decode((self.out/'case-cli-quota.json').read_bytes())
        full['isolation_ref']['sha256']=m.digest((self.out/name).read_bytes())
        self.save('case-cli-quota.json',full)
        with self.assertRaisesRegex(ValueError,'cli_restoration'): self.validate()


if __name__ == '__main__':
    unittest.main()
