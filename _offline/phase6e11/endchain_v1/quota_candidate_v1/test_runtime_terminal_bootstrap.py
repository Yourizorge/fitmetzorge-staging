"""Synthetic receipt tampering tests only; no Docker, DB, Auth or CI execution."""
import argparse
import copy
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import types
import unittest

from quota_candidate_v1 import runtime_bootstrap_closeout as producer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = None
spec = importlib.util.spec_from_file_location('quota_candidate_v1.runtime_terminal_bootstrap',
    HERE / 'runtime_terminal_bootstrap.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROOT is None:
            raise AssertionError('explicit --source-root required')
        cls.canonical = sorted((ROOT / 'supabase/migrations').glob('*.sql'))
        if len(cls.canonical) != 45:
            raise AssertionError('actual canonical45 source required')

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        self.out, self.sources = root/'out', root/'sources'
        self.out.mkdir(); self.sources.mkdir()
        mapping = {p.relative_to(ROOT).as_posix(): p for p in self.canonical}
        mapping.update({v.OWN: HERE/'runtime_terminal_bootstrap.py',
            v.PRODUCER: pathlib.Path(producer.__file__),
            v.BOUNDARY: ROOT/v.BOUNDARY, v.RUNTIME: ROOT/v.RUNTIME, v.STACK: ROOT/v.STACK,
            v.PREFIX+'native_runtime.py': ROOT/v.PREFIX/'native_runtime.py'})
        self.hashes = {}
        for name, source in mapping.items():
            target = self.sources/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            self.hashes[name] = v.digest(target.read_bytes())
        self.binding = dict(parent_id=v.PARENT, run_id='8bc257ad-77ec-46a8-b9a3-82c081f54eaa',
            environment='disposable_ci', hosted_permission=False, execution_admitted=False,
            source_commit='a'*40, candidate_sha='b'*64, ci_run='123456789')
        self.common = dict(source_commit='a'*40, candidate_sha256='b'*64, ci_run='123456789')
        self.gate = types.SimpleNamespace(out=self.out, sources=self.sources,
            container='supabase_db_fmz-db41-ci', cli_protocol=[],
            result=dict(commit='a'*40, candidate_sha256='b'*64, run_id='123456789'))
        self.save('candidate.json', dict(sha256='b'*64, sources=self.hashes))

    def save(self, name, value):
        (self.out/name).write_bytes(v.canonical(value))

    def load(self, name):
        return json.loads((self.out/name).read_bytes())

    def ref(self, name):
        raw = (self.out/name).read_bytes()
        return dict(path=name, sha256=v.digest(raw), bytes=len(raw))

    def fixtures(self, case='pre_migration'):
        stage, count, observations = v.EARLY[case]
        versions = [p.name.split('_')[0] for p in self.canonical]
        base = dict(**{k:0 for k in v.COUNTS}, history_count=44,
            history_sha256=v.digest(v.canonical(versions[:44])), m44_function='c'*64,
            m45_function=None, m45_trigger=None, quota_constraint='d'*64)
        source = dict(**self.common, sources={p:self.hashes[p] for p in self.hashes
                                             if p.startswith('supabase/migrations/')})
        common = dict(component_verified=True, reader_connections_closed=True,
            secondary_failures=[], unknown_outcome=False, safe_closure_no_fixtures=True,
            local_diagnostic_commands=8, full_chain_admission=False, hosted_admission=False,
            source_binding=source, source_binding_sha256=v.digest(v.canonical(source)),
            read_only_dispatches=[dict(ordinal=i+1,cost=1,kind='sql',confirmed=True,
                reply_delivered=True,sha256=v.digest(text.encode())) for i,text in enumerate(
                    ['BEGIN TRANSACTION READ ONLY',v.literal((ROOT/v.RUNTIME).read_bytes(),'CHECK'),
                     v.literal((ROOT/v.BOUNDARY).read_bytes(),'METADATA'),'ROLLBACK']*2)])
        pre = dict(**common, phase='pre_migration', before=base, after_failure=base,
                   dispatcher_called=False, dispatcher_command_count_delta=0)
        self.save('migration-boundary-pre.json', pre)
        names = ['migration-boundary-pre.json']
        if count == 45:
            ledger='cli-predispatch-canonical-45.ledger.txt'
            policy='cli-predispatch-canonical-45.policy.json'
            (self.out/ledger).write_bytes(b'{"fixture":"original raw ledger"}\n')
            (self.out/policy).write_bytes(b'{"fixture":"original raw policy"}\n')
            cli = dict(source_commit=self.common['source_commit'],
                candidate_sha256=self.common['candidate_sha256'],complete=True, cli_exit_code=0,
                ledger_ref={k:x for k,x in self.ref(ledger).items() if k!='bytes'},
                policy_ref={k:x for k,x in self.ref(policy).items() if k!='bytes'},
                profile='canonical_45',expected_migration=v.M45,expected_migration_sha256=v.M45_SHA,
                actual_migration_execution=True,app_profile_mutated=False,application_run_started=False,
                numeric_coverage=dict(all_protocol_visible=True,temp_written=0),observer_commands=8)
            self.save('cli-predispatch-canonical-45.json', cli)
            after = dict(base, history_count=45, history_sha256=v.digest(v.canonical(versions)),
                         m45_function='e'*64, m45_trigger='f'*64, quota_constraint='1'*64)
            self.save('migration-boundary-post.json', dict(**common, phase='post_migration',
                before=base, after_m45=after, after_failure=after, migration_rollback_claim=False,
                actual_migration_result=dict(receipt='cli-predispatch-canonical-45.json',
                    receipt_sha256=self.ref('cli-predispatch-canonical-45.json')['sha256'],
                    returncode=0, parent_bootstrap_dispatches=1,
                    ledger_sha256=cli['ledger_ref']['sha256'], policy_file_sha256=cli['policy_ref']['sha256'])))
            names = ['cli-predispatch-canonical-45.json', 'migration-boundary-post.json']
        refs = [self.ref(name) for name in names]
        self.save('case-stack-boundary-'+stage+'.json', dict(**self.common, stage=stage,
            history_count=count, evidence_refs=refs, full_chain_admission=False, hosted_admission=False))
        fired = dict(case=case, run_id=self.binding['run_id'], source_commit='a'*40,
            ci_run='123456789', candidate_sha='b'*64, original_error_code='case_injected_'+case,
            observations_before_fault=observations, automatic_retry=False, full_chain_admission=False,
            event=dict(stage=stage, history_count=count, evidence_refs=refs, dispatch_confirmed=count==45))
        self.save('case-fault-boundary.json', fired)
        self.fault = types.SimpleNamespace(case=case, binding=self.binding, fired=fired)
        context = dict(**self.common, run_id=self.binding['run_id'], scope=producer.SCOPE)
        reservation = dict(**context, case_name=case, reserved_sql_commands=4, no_refund=True,
            no_retry=True, auth_started=False, worker_started=False, quota_appended=False,
            full_chain_admission=False, hosted_admission=False, complete=False, commands=[],
            command_sha256=[v.digest(s.encode()) for s in producer.COMMANDS],
            docker_inventory_calls=1, docker_inventory_argv_sha256=v.digest(v.canonical(v.DOCKER_ARGV)))
        self.save('case-preauth-closeout-reservation.json', reservation)
        rows = [dict(id='2'*64, image='supabase/postgres:17.6.1.167', name=self.gate.container)]
        inventory = producer.inventory('\n'.join(json.dumps(r) for r in rows), self.gate.container)
        self.save('case-preauth-container-absence.json', dict(**context, **inventory,
            inventory_command=dict(argv=v.DOCKER_ARGV, exitcode=0, timeout_seconds=5, dispatch_calls=1)))
        identity = dict(database='postgres',role='postgres',version=17,readonly='on',ssl=True,
            statement_timeout='5s', lock_timeout='1s',database_oid=5,pg_system_identifier='12345678901')
        self.save('case-preauth-account-absence.json', dict(reservation, complete=True,
            commands=[dict(ordinal=i+1,sql_sha256=v.digest(s.encode()),confirmed=True)
                      for i,s in enumerate(producer.COMMANDS)], rollback_confirmed=True,
            connection_closed=True, error_class=None, identity=identity,
            account_counts=dict(users=0,sessions=0,refresh_tokens=0,controller_runs=0,history_count=count)))
        target = v.digest(v.canonical(dict(pg_container='2'*64,pg_system_identifier='12345678901',database_oid=5)))
        self.isolation = dict(run_id=self.binding['run_id'],ci_run='123456789',source_commit='a'*40,
            environment='disposable_ci',pg_system_identifier='12345678901',database_oid=5,
            pg_container='2'*64,db_target_sha256=target,reused=False,auth_state='not_started',
            auth_container=None,auth_database_bound=False,auth_target_sha256=None,
            auth_absence=dict(verified=True,
                container_inventory_ref=self.ref('case-preauth-container-absence.json'),
                account_inventory_ref=self.ref('case-preauth-account-absence.json')))
        self.case = case

    def validate(self):
        return v.validate_bootstrap_termination(self.gate,self.binding,self.case,self.fault,self.isolation)

    def test_pre_migration_returns_narrow_diagnostic_not_case_pass(self):
        self.fixtures()
        result = self.validate()
        self.assertEqual(result['status'], 'BOOTSTRAP_TERMINATION_VERIFIED')
        self.assertEqual(result['history_count'], 44)
        self.assertEqual(result['isolation_sha256'], v.digest(v.canonical(self.isolation)))
        for key in ('case_pass','full_chain_admission','hosted_admission',
                    'non_docker_process_absence_proven','historical_never_started_proven'):
            self.assertFalse(result[key])
        for ref in result['evidence_refs']:
            self.assertEqual(ref, self.ref(ref['path']))

    def test_post_migration_preserves_real45_and_original_sidecar_hashes(self):
        self.fixtures('post_migration')
        self.assertEqual(self.validate()['history_count'], 45)
        (self.out/'cli-predispatch-canonical-45.ledger.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'canonical_raw_hash'): self.validate()

    def test_confirmed_trace_rollback_and_close_are_mandatory(self):
        self.fixtures()
        name='case-preauth-account-absence.json'; original=self.load(name)
        changes=[lambda x:x.update(complete=False),lambda x:x.update(rollback_confirmed=False),
            lambda x:x.update(connection_closed=False),lambda x:x['commands'][0].update(confirmed=False),
            lambda x:x['commands'][2].update(sql_sha256='0'*64),
            lambda x:x['account_counts'].update(users=1),lambda x:x['account_counts'].update(history_count=45)]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                value=copy.deepcopy(original);mutate(value);self.save(name,value)
                self.isolation['auth_absence']['account_inventory_ref']=self.ref(name)
                with self.assertRaises(ValueError): self.validate()

    def test_inventory_summary_cannot_replace_actual_rows_or_failed_command(self):
        self.fixtures(); name='case-preauth-container-absence.json'; original=self.load(name)
        for mutate in (lambda x:x.pop('inventory_rows'),lambda x:x['inventory_command'].update(exitcode=1),
                       lambda x:x['inventory_rows'].append(dict(id='3'*64,image='supabase/gotrue:v2.197.0',name='other'))):
            value=copy.deepcopy(original);mutate(value);self.save(name,value)
            self.isolation['auth_absence']['container_inventory_ref']=self.ref(name)
            with self.assertRaises(ValueError): self.validate()

    def test_source_change_or_wrong_gate_binding_is_rejected(self):
        self.fixtures(); self.gate.result['head']='9'*40
        with self.assertRaisesRegex(ValueError,'gate_binding'):self.validate()
        del self.gate.result['head']
        (self.sources/v.STACK).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source_changed'):self.validate()

    def test_wrong_fault_case_or_boundary_hash_is_rejected(self):
        self.fixtures();self.fault.case='normal'
        with self.assertRaisesRegex(ValueError,'fault_object'):self.validate()
        self.fault.case=self.case
        (self.out/'migration-boundary-pre.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'reference_hash'):self.validate()

    def test_missing_reservation_and_duplicate_json_are_rejected(self):
        self.fixtures();name='case-preauth-closeout-reservation.json'
        (self.out/name).unlink()
        with self.assertRaises(FileNotFoundError):self.validate()
        (self.out/name).write_bytes(b'{"complete":false,"complete":true}')
        with self.assertRaisesRegex(ValueError,'duplicate_json_key'):self.validate()

    def test_isolation_ref_forgery_and_auth_fiction_are_rejected(self):
        self.fixtures();self.isolation['auth_absence']['account_inventory_ref']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'reference_hash'):self.validate()
        self.isolation['auth_absence']['account_inventory_ref']=self.ref('case-preauth-account-absence.json')
        self.isolation['auth_container']='3'*64
        with self.assertRaisesRegex(ValueError,'isolation'):self.validate()

    def test_post_fault_continuation_or_late_case_is_not_early_proof(self):
        self.fixtures();self.gate.cli_protocol=[{}]
        with self.assertRaisesRegex(ValueError,'execution_continued'):self.validate()
        self.case='normal'
        with self.assertRaisesRegex(ValueError,'case'):self.validate()

    def test_container_numeric_booleans_do_not_equal_real_observations(self):
        self.fixtures();name='case-preauth-container-absence.json'
        value=self.load(name);value['inventory_command']['exitcode']=False;self.save(name,value)
        self.isolation['auth_absence']['container_inventory_ref']=self.ref(name)
        with self.assertRaisesRegex(ValueError,'inventory_numeric'):self.validate()

    def test_reservation_command_fingerprint_cannot_be_substituted(self):
        self.fixtures();name='case-preauth-closeout-reservation.json'
        value=self.load(name);value['command_sha256'][1]='0'*64;self.save(name,value)
        with self.assertRaisesRegex(ValueError,'prepayment'):self.validate()

    def test_boundary_query_fingerprint_is_independently_checked(self):
        self.fixtures();name='migration-boundary-pre.json'
        value=self.load(name);value['read_only_dispatches'][1]['sha256']='0'*64;self.save(name,value)
        ref=self.ref(name)
        snapshot=self.load('case-stack-boundary-before45.json');snapshot['evidence_refs']=[ref]
        self.save('case-stack-boundary-before45.json',snapshot)
        self.fault.fired['event']['evidence_refs']=[ref];self.save('case-fault-boundary.json',self.fault.fired)
        with self.assertRaisesRegex(ValueError,'boundary_trace'):self.validate()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root',required=True,type=pathlib.Path)
    options,remaining=parser.parse_known_args()
    ROOT=options.source_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0],*remaining])
