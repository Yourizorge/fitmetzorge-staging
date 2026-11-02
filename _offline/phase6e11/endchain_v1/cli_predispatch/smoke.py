"""Execute patched upstream help only. No database, no hosted admission claim."""
import argparse
import importlib.util
import json
import os
import pathlib
import tempfile
import uuid

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fmz_predispatch_smoke_ci', HERE / 'ci.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


def smoke(upstream, bun, policy=None):
    upstream = pathlib.Path(upstream).resolve()
    build = ci.source_binding(upstream)
    with tempfile.TemporaryDirectory(prefix='cli-predispatch-smoke-') as temp:
        work = pathlib.Path(temp)
        policy = policy if policy is not None else dict(version=1, environment='disposable_ci', upstream_commit=ci.UPSTREAM,
            source_commit='0' * 40, candidate_sha256='0' * 64, invocation_id=str(uuid.uuid4()),
            slot='final', cap=28, closure_reserve=0, dry_run=True, host='127.0.0.1', port=65532,
            database='postgres', user='postgres', ca_sha256='0' * 64, migrations=[])
        (work / 'policy.json').write_text(json.dumps(policy))
        env = {k: v for k, v in os.environ.items() if not k.startswith(('PG', 'SUPABASE_', 'GH', 'NODE_', 'BUN_'))}
        env.update(DO_NOT_TRACK='1', SUPABASE_NO_UPDATE_NOTIFIER='1', SUPABASE_TELEMETRY_DISABLED='1',
            HOME=temp, USERPROFILE=temp, XDG_CONFIG_HOME=temp,
            FMZ_CLI_PREDISPATCH_POLICY=str(work / 'policy.json'),
            FMZ_CLI_PREDISPATCH_LEDGER=str(work / 'ledger.jsonl'))
        version, raw = ci.bounded([bun, '--version'], cwd=work, env=env, seconds=5)
        if version or raw.strip() != b'1.4.1':
            raise ValueError('cli_predispatch_bun_pin')
        code, output = ci.bounded([bun, str(upstream / 'apps/cli/src/main.ts'), 'db', 'push', '--help'],
                                 cwd=work, env=env)
        diagnostic = ci.invocation_diagnostic(code, output, work / 'ledger.jsonl')
        if code or b'--db-url' not in output:
            return dict(scope='OFFLINE_HELP_ONLY', build=build, complete=False,
                cli_diagnostic=diagnostic, hosted_admission=False, actual_database_execution=False)
        journal = ci.replay(work / 'ledger.jsonl')
        if journal['terminal']['sql_dispatches'] or journal['terminal']['connection_attempts']:
            raise ValueError('cli_predispatch_help_opened_connection')
        return dict(scope='OFFLINE_HELP_ONLY', build=build, complete=True, output_sha256=ci.sha(output),
            output_bytes=len(output), cli_diagnostic=diagnostic,
            policy_sha256=ci.sha(json.dumps(policy, separators=(',', ':')).encode()),
            expected_history_count=len(policy.get('expected_history_versions', [])),
            migration_statement_count=sum(len(m['ast_hashes']) for m in policy['migrations']),
            hosted_admission=False, actual_database_execution=False, journal=journal)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', required=True)
    parser.add_argument('--bun', required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--policy-receipt', help='Existing sanitized receipt containing the exact policy; help only')
    args = parser.parse_args()
    policy = json.loads(pathlib.Path(args.policy_receipt).read_bytes())['policy'] if args.policy_receipt else None
    result = smoke(args.upstream, args.bun, policy)
    with open(args.receipt, 'x') as file:
        json.dump(result, file, sort_keys=True, indent=2)
    print(json.dumps({key: result[key] for key in ('scope', 'complete', 'cli_diagnostic', 'actual_database_execution')}))
    raise SystemExit(0 if result['complete'] else 1)
