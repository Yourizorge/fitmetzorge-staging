"""Synthetic receipt tampering tests only; no Docker, DB, Auth or CI execution."""
import argparse
import copy
import json
import pathlib
import sys
import tempfile
import types
import unittest

import admission_matrix_bootstrap as v

HERE = pathlib.Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p/'supabase/migrations').is_dir()), None)



class CollectorTests(unittest.TestCase):
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
        own = {v.OWN: b'# synthetic terminal source\n',
            v.PRODUCER: b"IDENTITY = 'select synthetic_identity'\nACCOUNTS = 'select synthetic_counts'\n"
                b"COMMANDS = ('BEGIN TRANSACTION READ ONLY', IDENTITY, ACCOUNTS, 'ROLLBACK')\n"
                b"SCOPE = 'CI_BOOTSTRAP_CLOSEOUT_SEPARATE_FROM_CASE_2349'\n"
                + ('DOCKER_ARGS = ' + repr(tuple(v.DOCKER_ARGV)) + '\n').encode(),
            v.BOUNDARY: b"METADATA = 'select synthetic_metadata'\n",
            v.RUNTIME: b"CHECK = 'select synthetic_check'\n",
            v.STACK: b"IMAGE='supabase/postgres:17.6.1.167'\nDIGEST='synthetic-pinned-digest'\n",
            v.PREFIX+'native_runtime.py': b'# synthetic native\n',
            '_offline/phase6e_server_v1/cli_isolation.py':
                b"SETTING = 'select synthetic_setting'\nACTIVE = 'select synthetic_active'\n",
            v.COLLECTOR: pathlib.Path(v.__file__).read_bytes()}
        self.commands = ('BEGIN TRANSACTION READ ONLY', 'select synthetic_identity',
                         'select synthetic_counts', 'ROLLBACK')
        self.scope = 'CI_BOOTSTRAP_CLOSEOUT_SEPARATE_FROM_CASE_2349'
        self.hashes = {}
        for name, source in {**mapping, **own}.items():
            target = self.sources/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source if isinstance(source, bytes) else source.read_bytes())
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
                    ['BEGIN TRANSACTION READ ONLY',v.literal((self.sources/v.RUNTIME).read_bytes(),'CHECK'),
                     v.literal((self.sources/v.BOUNDARY).read_bytes(),'METADATA'),'ROLLBACK']*2)])
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
        context = dict(**self.common, run_id=self.binding['run_id'], scope=self.scope)
        reservation = dict(**context, case_name=case, reserved_sql_commands=4, no_refund=True,
            no_retry=True, auth_started=False, worker_started=False, quota_appended=False,
            full_chain_admission=False, hosted_admission=False, complete=False, commands=[],
            command_sha256=[v.digest(s.encode()) for s in self.commands],
            docker_inventory_calls=1, docker_inventory_argv_sha256=v.digest(v.canonical(v.DOCKER_ARGV)))
        self.save('case-preauth-closeout-reservation.json', reservation)
        rows = [dict(id='2'*64, image='supabase/postgres:17.6.1.167', name=self.gate.container)]
        inventory = dict(pg_container='2'*64, gotrue_containers=0, containers_inspected=1,
            inventory_rows=rows, inventory_sha256=v.digest(v.canonical(rows)),
            coverage='all_existing_disposable_docker_containers; Auth uses Docker only')
        self.save('case-preauth-container-absence.json', dict(**context, **inventory,
            inventory_command=dict(argv=v.DOCKER_ARGV, exitcode=0, timeout_seconds=5, dispatch_calls=1)))
        identity = dict(database='postgres',role='postgres',version=17,readonly='on',ssl=True,
            statement_timeout='5s', lock_timeout='1s',database_oid=5,pg_system_identifier='12345678901')
        self.save('case-preauth-account-absence.json', dict(reservation, complete=True,
            commands=[dict(ordinal=i+1,sql_sha256=v.digest(s.encode()),confirmed=True)
                      for i,s in enumerate(self.commands)], rollback_confirmed=True,
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
        self.seal()

    def seal(self):
        """Rehash synthetic envelopes, so negative tests reach semantic checks."""
        stage, count, _ = v.EARLY[self.case]
        if count == 45:
            name = 'canonical-45-cli-predispatch-cli-isolation-0.json'
            if not (self.out/name).exists():
                self.save(name, dict(original='off', restored=True, commands=4,
                    primary_error_class=None, protocol=[
                        dict(statement_sha256=v.digest(sql.encode()), confirmed=True)
                        for sql in ('select synthetic_setting', 'select synthetic_setting',
                                    'select synthetic_active', 'select synthetic_setting')]))
            cli = self.load('cli-predispatch-canonical-45.json')
            cli.update(isolation_receipt=name, isolation_receipt_sha256=self.ref(name)['sha256'],
                       ci_cron_restored=True, ci_bootstrap_sql_commands=4)
            for key in ('ledger_ref', 'policy_ref'):
                cli[key] = {k:val for k,val in self.ref(cli[key]['path']).items() if k != 'bytes'}
            self.save('cli-predispatch-canonical-45.json', cli)
            post = self.load('migration-boundary-post.json')
            post['actual_migration_result'].update(
                receipt_sha256=self.ref('cli-predispatch-canonical-45.json')['sha256'],
                ledger_sha256=cli['ledger_ref']['sha256'],
                policy_file_sha256=cli['policy_ref']['sha256'],
                isolation_receipt_sha256=cli['isolation_receipt_sha256'], isolation_commands=4)
            self.save('migration-boundary-post.json', post)
        snapshot = self.load('case-stack-boundary-'+stage+'.json')
        snapshot['evidence_refs'] = [self.ref(r['path']) for r in snapshot['evidence_refs']]
        self.save('case-stack-boundary-'+stage+'.json', snapshot)
        fault = self.load('case-fault-boundary.json')
        fault['event']['evidence_refs'] = snapshot['evidence_refs']
        self.save('case-fault-boundary.json', fault)
        self.isolation['auth_absence'].update(
            container_inventory_ref=self.ref('case-preauth-container-absence.json'),
            account_inventory_ref=self.ref('case-preauth-account-absence.json'))
        required = [p.relative_to(ROOT).as_posix() for p in self.canonical] + [
            v.OWN, v.PRODUCER, v.BOUNDARY, v.RUNTIME, v.STACK, v.PREFIX+'native_runtime.py']
        names = ['candidate.json', 'case-fault-boundary.json',
            'case-stack-boundary-'+stage+'.json', 'migration-boundary-pre.json',
            'case-preauth-closeout-reservation.json', 'case-preauth-account-absence.json',
            'case-preauth-container-absence.json']
        if count == 45:
            names += ['migration-boundary-post.json', 'cli-predispatch-canonical-45.json',
                'cli-predispatch-canonical-45.ledger.txt', 'cli-predispatch-canonical-45.policy.json']
        self.save('case-bootstrap-termination.json', dict(
            format='quota-bootstrap-termination-v1', status='BOOTSTRAP_TERMINATION_VERIFIED',
            case_name=self.case, run_id=self.binding['run_id'], **self.common,
            history_count=count, boundary_stage=stage,
            isolation_sha256=v.digest(v.canonical(self.isolation)), auth_state='not_started',
            auth_absence_scope='docker_inventory_and_global_database_counts_at_closeout',
            non_docker_process_absence_proven=False, historical_never_started_proven=False,
            evidence_refs=[self.ref(n) for n in names],
            source_hashes={n:self.hashes[n] for n in required}, closeout_sql_commands=4,
            closeout_docker_calls=1, accounting_scope=self.scope, case_pass=False,
            full_chain_admission=False, hosted_admission=False, parent_terminal_validation_required=True))
        self.save('case-execution.json', dict(**self.common, case_name=self.case,
            parent_id=v.PARENT, run_id=self.binding['run_id'], isolation=self.isolation,
            status='INCOMPLETE', bootstrap_termination_ref=self.ref('case-bootstrap-termination.json')))
        self.save('result.json', dict(self.gate.result, case_name=self.case, status='INCOMPLETE',
            hosted_admitted=False, full_chain_admission=False))
        self.save('artifact-manifest.json', {p.name:v.digest(p.read_bytes())
                  for p in self.out.iterdir() if p.name != 'artifact-manifest.json'})

    def payloads(self):
        return {p.name:p.read_bytes() for p in self.out.iterdir()}

    def validate(self, **changes):
        args = dict(case_name=self.case, source_commit='a'*40, ci_run='123456789',
            candidate_sha256='b'*64, expected_sources=self.hashes, trusted_root=self.sources)
        args.update(changes)
        return v.verify_bootstrap_case(self.payloads(), **args)

    def mutate(self, name, change, seal=True):
        data = self.load(name)
        change(data)
        self.save(name, data)
        if seal:
            self.seal()

    def test_pre_and_post_scoped_evidence_not_case_admission(self):
        for case in v.EARLY:
            with self.subTest(case=case):
                # Each case gets independent synthetic envelopes.
                self.fixtures(case)
                result = self.validate()
                self.assertEqual(result['status'], 'BOOTSTRAP_ABSENCE_VERIFIED')
                self.assertEqual(result['history_count'], v.EARLY[case][1])
                self.assertIsNone(result['auth_container'])
                self.assertFalse(result['case_pass'])
                self.assertFalse(result['full_chain_admission'])
                self.assertFalse(result['hosted_admission'])
                self.assertFalse(result['cli_hashchain_replayed'])
                self.assertFalse(result['historical_never_started_proven'])
                self.assertEqual(result['closeout_sql_commands'], 4)
                for ref in result['evidence_refs']:
                    self.assertEqual(ref, self.ref(ref['path']))

    def test_exact_two_cases_only(self):
        self.fixtures()
        for case in ('normal', 'auth', 'post_migration_extra', ''):
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, 'case'):
                self.validate(case_name=case)

    def test_conflicting_head_commit_and_run_binding(self):
        self.fixtures()
        self.mutate('result.json', lambda x:x.update(head='f'*40), seal=False)
        with self.assertRaisesRegex(ValueError, 'result_binding'):
            self.validate()

    def test_every_top_level_case_binding_is_required(self):
        self.fixtures()
        original = self.load('case-execution.json')
        for key in ('parent_id', 'run_id', 'source_commit', 'ci_run', 'candidate_sha256'):
            with self.subTest(key=key):
                value = copy.deepcopy(original); value[key] = 'wrong'
                self.save('case-execution.json', value)
                with self.assertRaisesRegex(ValueError, 'case_binding'):
                    self.validate()

    def test_old_uuid_is_not_fresh_case(self):
        self.fixtures()
        self.isolation['run_id'] = '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'
        self.seal()
        with self.assertRaisesRegex(ValueError, 'run_id'):
            self.validate()

    def test_expected_source_map_not_artifact_manifest_is_authority(self):
        self.fixtures()
        changed = dict(self.hashes); changed[v.STACK] = '0'*64
        with self.assertRaisesRegex(ValueError, 'source_inventory'):
            self.validate(expected_sources=changed)
        (self.sources/v.STACK).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'source_changed'):
            self.validate()

    def test_loaded_collector_source_must_match_prepared_candidate(self):
        self.fixtures()
        changed = dict(self.hashes); changed[v.COLLECTOR] = '0'*64
        with self.assertRaisesRegex(ValueError, 'loaded_collector'):
            self.validate(expected_sources=changed)

    def test_command_hash_not_boolean_proof(self):
        self.fixtures()
        self.mutate('case-preauth-account-absence.json',
                    lambda x:x['commands'][2].update(sql_sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'account_trace'):
            self.validate()

    def test_reservation_hashes_match_trusted_producer(self):
        self.fixtures()
        self.mutate('case-preauth-closeout-reservation.json',
                    lambda x:x.update(command_sha256=['0'*64]*4))
        with self.assertRaisesRegex(ValueError, 'prepayment'):
            self.validate()

    def test_rollback_connection_close_and_confirmations_required(self):
        self.fixtures()
        name = 'case-preauth-account-absence.json'; original = self.load(name)
        for key in ('rollback_confirmed', 'connection_closed', 'complete'):
            with self.subTest(key=key):
                value = copy.deepcopy(original); value[key] = False
                self.save(name, value); self.seal()
                with self.assertRaisesRegex(ValueError, 'account_trace'):
                    self.validate()

    def test_global_zero_and_tls_identity_required(self):
        self.fixtures()
        name = 'case-preauth-account-absence.json'; original = self.load(name)
        changes = [lambda x:x['account_counts'].update(users=1),
            lambda x:x['account_counts'].update(history_count=True),
            lambda x:x['identity'].update(ssl=False),
            lambda x:x['identity'].update(database='other'),
            lambda x:x['identity'].update(statement_timeout='30s')]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                value=copy.deepcopy(original);mutate(value);self.save(name,value);self.seal()
                with self.assertRaises(ValueError): self.validate()

    def test_docker_rows_not_summary_or_claim_are_required(self):
        self.fixtures()
        name='case-preauth-container-absence.json';original=self.load(name)
        changes = [lambda x:x.update(inventory_rows=[]),
            lambda x:x['inventory_rows'][0].update(image='supabase/gotrue:v2.197.0'),
            lambda x:x['inventory_rows'].append(x['inventory_rows'][0].copy()),
            lambda x:x['inventory_command'].update(argv=['docker','ps']),
            lambda x:x['inventory_command'].update(exitcode=1),
            lambda x:x['inventory_command'].update(dispatch_calls=True)]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                value=copy.deepcopy(original);mutate(value);self.save(name,value);self.seal()
                with self.assertRaises(ValueError): self.validate()

    def test_auth_none_is_not_a_generic_bypass(self):
        self.fixtures()
        self.isolation['auth_container']='3'*64;self.seal()
        with self.assertRaisesRegex(ValueError, 'isolation'):
            self.validate()

    def test_isolation_refs_and_target_hash_cannot_diverge(self):
        self.fixtures()
        self.isolation['db_target_sha256']='0'*64;self.seal()
        with self.assertRaisesRegex(ValueError, 'isolation'):
            self.validate()

    def test_raw_receipt_tamper_missing_reference_and_duplicate_json(self):
        self.fixtures()
        payloads = self.payloads()
        name='case-preauth-account-absence.json'
        for raw in (b'{}', b'{"a":1,"a":2}'):
            with self.subTest(raw=raw):
                (self.out/name).write_bytes(raw)
                with self.assertRaises((ValueError, KeyError)): self.validate()
        (self.out/name).write_bytes(payloads[name])
        (self.out/'case-bootstrap-termination.json').unlink()
        with self.assertRaisesRegex(ValueError, 'receipt_missing'): self.validate()

    def test_terminal_evidence_cannot_drop_or_forge_refs(self):
        self.fixtures()
        name='case-bootstrap-termination.json';original=self.load(name)
        for mutate in (lambda x:x['evidence_refs'].pop(),
            lambda x:x['evidence_refs'][0].update(sha256='0'*64),
            lambda x:x.update(source_hashes={})):
            value=copy.deepcopy(original);mutate(value);self.save(name,value)
            case=self.load('case-execution.json');case['bootstrap_termination_ref']=self.ref(name)
            self.save('case-execution.json',case)
            with self.assertRaises(ValueError): self.validate()

    def test_boundary44_cannot_be_relabelled45(self):
        self.fixtures()
        self.mutate('migration-boundary-pre.json',
                    lambda x:x['after_failure'].update(history_count=45))
        with self.assertRaisesRegex(ValueError, 'boundary_state'): self.validate()

    def test_boundary_query_hash_matches_trusted_source(self):
        self.fixtures()
        self.mutate('migration-boundary-pre.json',
                    lambda x:x['read_only_dispatches'][1].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'boundary_trace'): self.validate()

    def test_post_45_raw_sidecars_are_not_reconstructed(self):
        self.fixtures('post_migration')
        name='cli-predispatch-canonical-45.ledger.txt'
        (self.out/name).write_bytes((self.out/name).read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'canonical_raw_hash'): self.validate()

    def test_isolator_restoration_ref_and_actual_commands_checked(self):
        self.fixtures('post_migration')
        self.mutate('canonical-45-cli-predispatch-cli-isolation-0.json',
                    lambda x:x['protocol'][0].update(statement_sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'canonical_isolation_trace'): self.validate()

    def test_pre_case_cannot_include_m45_execution_or_app_continuation(self):
        self.fixtures()
        self.save('cli-predispatch-canonical-45.json', {})
        with self.assertRaisesRegex(ValueError, 'unexpected_m45'): self.validate()
        (self.out/'cli-predispatch-canonical-45.json').unlink()
        self.save('cli-protocol-10.json', {})
        with self.assertRaisesRegex(ValueError, 'execution_continued'): self.validate()

    def test_literal_parser_never_executes_calls(self):
        self.assertEqual(v.source_literals(b"raise RuntimeError('never run')\nSCOPE='x'\n",
                                           ('SCOPE',)), {'SCOPE':'x'})
        with self.assertRaisesRegex(ValueError, 'source_expression'):
            v.source_literals(b"SCOPE=__import__('os').getcwd()\n", ('SCOPE',))

    def test_numeric_confirmation_is_not_true(self):
        self.fixtures()
        self.mutate('case-preauth-account-absence.json',
                    lambda x:x['commands'][0].update(confirmed=1))
        with self.assertRaisesRegex(ValueError, 'account_ordinal'):
            self.validate()

    def test_inventory_pg_image_matches_prepared_stack_source(self):
        self.fixtures()
        name='case-preauth-container-absence.json'
        value=self.load(name)
        value['inventory_rows'][0]['image']='postgres:16'
        value['inventory_sha256']=v.digest(v.canonical(value['inventory_rows']))
        self.save(name,value);self.seal()
        with self.assertRaisesRegex(ValueError, 'pg_image'):
            self.validate()

    def test_payload_paths_and_case_aliases_rejected(self):
        self.fixtures()
        payloads=self.payloads()
        for name in ('../bad.json', 'CASE-EXECUTION.JSON', 'code.py'):
            value=dict(payloads);value[name]=b'{}'
            with self.subTest(name=name), self.assertRaises(ValueError):
                v.verify_bootstrap_case(value, case_name=self.case, source_commit='a'*40,
                    ci_run='123456789',candidate_sha256='b'*64,
                    expected_sources=self.hashes,trusted_root=self.sources)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root', type=pathlib.Path)
    options,remaining=parser.parse_known_args()
    ROOT = options.source_root
    if ROOT is None:
        ROOT = next((p for p in HERE.parents if (p/'supabase/migrations').is_dir()), None)
    if ROOT is None:
        parser.error('--source-root required for isolated delivery')
    ROOT=ROOT.resolve(strict=True)
    unittest.main(argv=[sys.argv[0],*remaining])
