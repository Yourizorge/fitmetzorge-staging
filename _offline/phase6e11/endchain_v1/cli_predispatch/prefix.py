"""Exact disposable canonical 1..44 prefix; never a hosted apply route."""
import importlib.util
import json
import os
import pathlib
import re
import uuid

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fmz_cli_prefix_pending', HERE / 'pending.py')
pending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pending)
HISTORY_SETUP = (
    'BEGIN',
    'CREATE SCHEMA IF NOT EXISTS supabase_migrations',
    'CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (version text NOT NULL PRIMARY KEY)',
    'ALTER TABLE supabase_migrations.schema_migrations ADD COLUMN IF NOT EXISTS statements text[]',
    'ALTER TABLE supabase_migrations.schema_migrations ADD COLUMN IF NOT EXISTS name text',
    'SELECT version FROM supabase_migrations.schema_migrations ORDER BY version',
    'COMMIT',
)


def require(value, code):
    if not value:
        raise ValueError('cli_prefix_' + code)


def plan(gate, args):
    import ci_profile
    from cli_meter import source_commit
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
        and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
        and os.environ.get('GITHUB_REF') == 'refs/heads/main'
        and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
        and gate.container == 'supabase_db_fmz-db41-ci', 'disposable_only')
    phase = gate.result.get('phase', '')
    run_id = getattr(gate, '_case_stack_run_id', None)
    require(isinstance(run_id, str) and str(uuid.UUID(run_id)) == run_id
            and uuid.UUID(run_id).version == 4
            and run_id not in ('6f8c8909-9b79-4011-a9d1-db5e23c6b6c1',
                               '11a909f4-7113-424a-aa4b-ce9964720a3e'), 'case_run_id')
    ci_run = gate.result.get('run_id')
    require(isinstance(ci_run, str) and re.fullmatch('[1-9][0-9]{0,18}', ci_run)
            and os.environ.get('GITHUB_RUN_ID') == ci_run, 'ci_run')
    match = re.fullmatch(r'migration_([1-9][0-9]?)', phase)
    require(match is not None and tuple(args) == ('migration', 'up', '--local'), 'command')
    index = int(match[1])
    require(1 <= index <= 44 and type(gate.result.get('migrations_applied')) is int
        and gate.result['migrations_applied'] == index - 1
        and gate.cli_profile == 'local_app' and not getattr(gate, 'cli_protocol', []), 'sequence')
    commit = source_commit(gate.result)
    require(os.environ.get('GITHUB_SHA') == commit, 'source_commit')
    manifest = json.loads((gate.out / 'candidate.json').read_bytes())
    require(manifest['sha256'] == gate.result['candidate_sha256'], 'manifest')
    canonical = ci_profile.canonical(list(manifest['sources']))
    relative = canonical[:index]
    files = sorted((gate.work / 'supabase/migrations').glob('*.sql'))
    require({p.name for p in files} == {pathlib.PurePosixPath(n).name for n in relative}, 'inventory')
    hashes = {}
    for name in relative:
        source = gate.sources / name
        work = gate.work / name
        require(not source.is_symlink() and source.is_file() and not work.is_symlink(), 'source')
        digest = pending.common.sha(source.read_bytes())
        require(digest == manifest['sources'][name]
            and pending.common.sha(work.read_bytes()) == digest, 'bytes')
        hashes[name] = digest
    tag = 'cli-predispatch-prefix-' + str(index)
    require(index not in getattr(gate, '_cli_prefix_attempts', set())
        and not any((gate.out / (tag + suffix)).exists() for suffix in
            ('.json', '.ledger.txt', '.policy.json', '-preregister.json')), 'reuse')
    return dict(index=None, prefix_index=index, canonical_apply=True, phase=phase,
        run_id=run_id, ci_run=gate.result['run_id'],
        source_commit=commit, candidate_sha256=manifest['sha256'],
        requested_arguments=list(args), logical_arguments=list(args), files=files,
        migration_sources=hashes, target=gate.sources / relative[-1],
        target_sha256=hashes[relative[-1]],
        expected_history_versions=sorted(pathlib.PurePosixPath(n).name.split('_')[0] for n in relative[:-1]))


def provision(gate):
    """The pinned CLI reads history first; prepay its empty disposable CI ledger."""
    from native_runtime import NativeRuntime
    path = gate.out / 'cli-prefix-history-provision.json'
    require(not path.exists(), 'provision_reuse')
    receipt = dict(format='ci-prefix-history-provision-v1', complete=False,
        source_commit=gate.result.get('commit', gate.result.get('head')),
        candidate_sha256=gate.result['candidate_sha256'], ci_run=gate.result['run_id'],
        run_id=gate._case_stack_run_id,
        explicit_reserve=8, protocol=[], implicit_driver_sql_proven=False,
        local_bootstrap_only=True, hosted_admitted=False)
    pending.exclusive_raw(gate.out, 'cli-prefix-history-provision-reserve.json',
        json.dumps(receipt, sort_keys=True).encode(), 16384)
    runtime = None
    connection = None
    primary = None
    opened = False
    def dispatch(sql):
        ordinal = len(receipt['protocol']) + 1
        require(ordinal <= 8, 'provision_budget')
        row = dict(ordinal=ordinal, sql_sha256=pending.common.sha(sql.encode()), confirmed=False)
        receipt['protocol'].append(row)
        name = 'cli-prefix-history-provision-' + str(ordinal)
        pending.exclusive_raw(gate.out, name + '-intent.json', json.dumps(row).encode(), 4096)
        cursor = connection.execute(sql)
        rows = cursor.fetchall() if cursor.description else []
        row['confirmed'] = True
        pending.exclusive_raw(gate.out, name + '-confirmed.json', json.dumps(row).encode(), 4096)
        return rows
    try:
        runtime = NativeRuntime.disposable(gate)
        connection = runtime.connect()
        opened = True
        for sql in HISTORY_SETUP:
            rows = dispatch(sql)
            if sql == HISTORY_SETUP[-2]:
                require(rows == [], 'initial_history_not_empty')
        opened = False
        receipt['complete'] = True
    except Exception as error:
        primary = error
        receipt['failure_class'] = type(error).__name__
        raise
    finally:
        secondary = []
        if opened and connection is not None:
            try: dispatch('ROLLBACK')
            except Exception as error: secondary.append(type(error).__name__)
        try:
            if connection is not None: connection.close()
        except Exception as error: secondary.append(type(error).__name__)
        try:
            if runtime is not None: runtime.clear()
        except Exception as error: secondary.append(type(error).__name__)
        receipt['secondary_error_classes'] = secondary
        receipt['complete'] = receipt['complete'] and not secondary
        try:
            pending.exclusive_raw(gate.out, path.name,
                json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode(), 16384)
        except Exception as error:
            if primary is None: raise
            primary.add_note('cli_prefix_provision_receipt:' + type(error).__name__)
        if primary is None and secondary:
            raise ValueError('cli_prefix_provision_closeout')


def run(gate, args):
    value = plan(gate, args)
    attempts = getattr(gate, '_cli_prefix_attempts', set())
    attempts.add(value['prefix_index'])
    gate._cli_prefix_attempts = attempts
    if value['prefix_index'] == 1:
        provision(gate)
    return pending.run_apply(gate, args, value)
