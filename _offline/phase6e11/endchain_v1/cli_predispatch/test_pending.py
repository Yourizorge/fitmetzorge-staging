"""Offline pending-apply contracts, using the existing pure app CI profile."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
app = HERE.parents[2] / 'phase6e_server_v1'
if app.is_dir(): sys.path.insert(0, str(app))
import ci_profile

spec = importlib.util.spec_from_file_location('fmz_test_pending', HERE / 'pending.py')
pending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pending)


def evidence(policy):
    migration = policy['migrations'][0]
    body = [dict(event='dispatch', id=i+1, ast_sha256=h, kind='TransactionStmt', category='transaction')
            for i, h in enumerate(migration['ast_hashes'])]
    events = [dict(event='history_snapshot', count=len(policy['expected_history_versions']), matches_policy=True,
                   versions_sha256=pending.common.sha(json.dumps(policy['expected_history_versions'], separators=(',', ':')).encode()))]
    events += body + [dict(event='history_bind', migration_sha256=migration['sha256'],
        version=migration['version'], statement_count=len(body)),
        dict(event='dispatch', id=len(body)+1, category='migration_history', ast_sha256='c'*64, kind='InsertStmt')]
    return dict(terminal_recorded=True, header=dict(slot='quota', dry_run=False, cap=64,
        policy_sha256=pending.common.sha(json.dumps(policy, separators=(',', ':')).encode())),
        terminal=dict(complete=True, unknown_consumed=0, sql_dispatches=len(body)+1), events=events)


class PendingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cli_predispatch_')
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        self.saved = {}
        self.gate = SimpleNamespace(sources=root/'sources', work=root/'work', out=root/'out',
            cli_profile='local_app', cli_protocol=[], container='supabase_db_fmz-db41-ci',
            result=dict(commit='a'*40, candidate_sha256='b'*64, phase='local_app_schema'),
            save=lambda n,v: self.saved.update({n: json.loads(json.dumps(v))}))
        (self.gate.work/'supabase/migrations').mkdir(parents=True)
        self.gate.out.mkdir()
        self.hashes = {}
        names = [str(n).zfill(14)+'_synthetic.sql' for n in range(44)] + [ci_profile.QUOTA]
        for name in names:
            self.add_file('supabase/migrations/'+name)
        for name in pending.FILES:
            self.add_file(pending.APP+name, stage=name==pending.FILES[0])
        (self.gate.out/'candidate.json').write_text(json.dumps(dict(sha256='b'*64, sources=self.hashes)))
        (self.gate.work/'fmz-ci-ca.crt').write_text('synthetic-ca')
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, cli_meter=SimpleNamespace(source_commit=lambda r:r['commit'])).start()

    def add_file(self, relative, stage=True):
        source = self.gate.sources/relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b'BEGIN; COMMIT;\n')
        self.hashes[relative] = pending.common.sha(source.read_bytes())
        if stage: (self.gate.work/'supabase/migrations'/source.name).write_bytes(source.read_bytes())

    def plan(self):
        n = len(self.gate.cli_protocol)//2
        return pending.plan_pending(self.gate, ('migration','up','--local'), self.gate.sources/pending.APP/pending.FILES[n])

    def policy(self, plan):
        return dict(expected_history_versions=plan['expected_history_versions'], migrations=[dict(
            sha256=plan['target_sha256'], version=plan['target'].name.split('_')[0], ast_hashes=['1'*64,'2'*64])])

    def test_schema_uses_45_history_and_one_existing_pending_file(self):
        plan = self.plan()
        self.assertEqual(len(plan['expected_history_versions']), 45)
        self.assertEqual(len(plan['files']), 46)

    def test_outbox_uses_46_history_without_new_migration(self):
        self.gate.cli_protocol = [{}, {}]
        self.gate.result['phase'] = 'local_app_outbox'
        self.add_file(pending.APP+pending.FILES[1])
        plan = self.plan()
        self.assertEqual(len(plan['expected_history_versions']), 46)
        self.assertEqual(len(plan['files']), 47)

    def test_old_quota_cannot_be_expected_target(self):
        with self.assertRaisesRegex(ValueError, 'pending_target'):
            pending.plan_pending(self.gate, ('migration','up','--local'), self.gate.sources/'supabase/migrations'/ci_profile.QUOTA)

    def test_working_migration_tamper_is_rejected(self):
        (self.gate.work/'supabase/migrations'/pending.FILES[0]).write_bytes(b'SELECT 2;')
        with self.assertRaisesRegex(ValueError, 'pending_bytes'): self.plan()

    def test_extra_m48_is_rejected(self):
        (self.gate.work/'supabase/migrations/20990101000000_extra.sql').write_bytes(b'SELECT 1;')
        with self.assertRaisesRegex(ValueError, 'pending_inventory'): self.plan()

    def test_wrong_phase_is_rejected(self):
        self.gate.result['phase'] = 'migration'
        with self.assertRaisesRegex(ValueError, 'pending_slot'): self.plan()

    def test_exact_execution_and_existing_profile_contract(self):
        plan = self.plan(); policy = self.policy(plan); proof = evidence(policy)
        self.assertEqual(len(pending.prove_execution(proof, policy)), 3)
        receipt = dict(proof, complete=True, cli_exit_code=0, actual_migration_execution=True,
            observer_trace=[dict(confirmed=True, protocol_commands=1)]*8,
            numeric_coverage={'all_protocol_visible':True})
        compatible = pending.app_receipt(plan, receipt)
        self.assertEqual(ci_profile.cli_receipt(compatible, 0)['profile'], 'local_app')
        self.assertEqual(compatible['execution_mode'], 'source_instrumented_db_url')
        self.assertNotIn('capacity_reserved', compatible)

    def test_missing_history_write_is_not_actual_migration_pass(self):
        policy = self.policy(self.plan()); proof = evidence(policy)
        proof['events'] = [e for e in proof['events'] if e['event'] != 'history_bind']
        with self.assertRaisesRegex(ValueError, 'pending_execution'): pending.prove_execution(proof, policy)

    def test_wrong_statement_order_is_rejected(self):
        policy = self.policy(self.plan()); proof = evidence(policy)
        proof['events'][1], proof['events'][2] = proof['events'][2], proof['events'][1]
        with self.assertRaisesRegex(ValueError, 'pending_execution'): pending.prove_execution(proof, policy)

    def test_unknown_remains_no_go(self):
        policy = self.policy(self.plan()); proof = evidence(policy)
        proof['terminal']['unknown_consumed'] = 1
        with self.assertRaisesRegex(ValueError, 'pending_terminal'): pending.prove_execution(proof, policy)

    def exercise(self, fail=False):
        calls = []; compiled = {}; state = {'cleared':False}
        def bounded(argv, **kwargs):
            if argv[-1] == '--version': return 0, b'1.4.1'
            if argv[:2] == ['docker','port']: return 0, b'127.0.0.1:54322'
            if argv[:2] == ['docker','exec']: return 0, b'synthetic-private-password'
            if argv[1].endswith('policy.cjs'):
                p = json.loads(pathlib.Path(argv[2]).read_text())
                target = pathlib.Path(p.pop('migration_paths')[0])
                p['migrations'] = [dict(sha256=pending.common.sha(target.read_bytes()),
                    version=target.name.split('_')[0], ast_hashes=['1'*64,'2'*64])]
                compiled.update(p)
                return 0, json.dumps(p).encode()
            calls.append(argv)
            if fail: raise ValueError('synthetic_timeout')
            return 0, b'Applied private candidate migration'
        runtime = SimpleNamespace(clear=lambda:state.update(cleared=True))
        patch.dict(sys.modules, native_runtime=SimpleNamespace(NativeRuntime=SimpleNamespace(disposable=lambda g:runtime)),
            cli_stat_reader=SimpleNamespace(snapshot=lambda r:({'track':'all'},[dict(confirmed=True, protocol_commands=1)]*4),
                compare=lambda *a,**kw:dict(all_protocol_visible=True,temp_written=0))).start()
        patch.dict('os.environ', GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging', FMZ_CLI_PREDISPATCH_UPSTREAM=str(HERE)).start()
        patch.object(pending.common, 'source_binding', return_value={}).start()
        patch.object(pending.shutil, 'which', return_value='bun').start()
        patch.object(pending.common, 'bounded', side_effect=bounded).start()
        patch.object(pending.common, 'replay', side_effect=lambda *a,**kw:evidence(compiled)).start()
        patch.object(pending.common, 'isolated', side_effect=lambda g,r,m:m()).start()
        target = self.gate.sources/pending.APP/pending.FILES[0]
        if fail:
            with self.assertRaisesRegex(ValueError, 'synthetic_timeout'):
                pending.run_pending(self.gate, ('migration','up','--local'), target)
        else:
            result = pending.run_pending(self.gate, ('migration','up','--local'), target)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
        self.assertTrue(state['cleared'])
        self.assertEqual(len(calls), 1)
        self.assertIn('--include-all', calls[0])
        self.assertNotIn('--dry-run', calls[0])
        self.assertNotIn('synthetic-private-password', json.dumps(calls))
        self.assertNotIn('synthetic-private-password', json.dumps(self.saved))
        self.assertEqual(len(self.gate.cli_protocol), 1)

    def test_adapter_executes_once_and_appends_one_compatible_receipt(self):
        self.exercise()
        ci_profile.cli_receipt(self.gate.cli_protocol[0], 0)
        self.assertTrue(self.saved['cli-predispatch-pending-0.json']['actual_migration_execution'])

    def test_adapter_failure_consumes_reservation_without_retry(self):
        self.exercise(fail=True)
        self.assertFalse(self.gate.cli_protocol[0]['complete'])
        self.assertEqual(self.saved['cli-predispatch-pending-0.json']['reserved_sql_consumed_on_failure'], 64)


if __name__ == '__main__': unittest.main()
