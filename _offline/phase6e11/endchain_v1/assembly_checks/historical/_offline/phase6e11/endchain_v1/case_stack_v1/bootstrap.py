"""Build exact clean47 using existing CLI dispatch, without app/browser/Auth suites.

Call once on a fresh admission_ci.Gate after fetch/install. Main owns the
same-source app proof, fresh-runner matrix, collection and subsequent case lease.
"""
import hashlib
import inspect
import json
import os
import pathlib
import re
import sys

PREFIX = '_offline/phase6e11/endchain_v1/case_stack_v1/'
SOURCES = tuple(PREFIX + name for name in (
    '__init__.py', '__main__.py', 'bootstrap.py', 'test_bootstrap.py', 'README.txt',
    'ci.py', 'test_ci.py'))
CONTAINER = 'supabase_db_fmz-db41-ci'
IMAGE_ID = 'sha256:66089200353d90686fe9b252a47d17d078364bf47c50190852c33dc850a0191f'
IMAGE = 'supabase/postgres:17.6.1.167'
DIGEST = 'supabase/postgres@sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb'
IMAGES = {IMAGE: DIGEST, 'public.ecr.aws/' + IMAGE: 'public.ecr.aws/' + DIGEST}
HISTORY = 'select version from supabase_migrations.schema_migrations order by version'
META = """select current_database() database,current_user::text role,
 current_setting('server_version_num') version,
 current_setting('statement_timeout') statement_timeout,
 current_setting('lock_timeout') lock_timeout,
 current_setting('transaction_read_only') readonly,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 (select oid::bigint from pg_database where datname=current_database()) database_oid,
 not exists(select 1 from pg_namespace where nspname like 'fmz6e11%') app_absent,
 not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relkind in ('r','p')) public_empty"""
EMPTY = """select not exists(select 1 from fmz6e11_controller_private.runs) runs_empty,
 not exists(select 1 from fmz6e11_controller_private.steps) steps_empty,
 not exists(select 1 from fmz6e11_controller_private.evidence) evidence_empty"""
CONTROL_SQL = ("begin read only;set local statement_timeout='5s';"
    "set local lock_timeout='1s';select system_identifier::text from pg_control_system();rollback;")


class StackStop(ValueError):
    pass


def require(value, code):
    if not value:
        raise StackStop(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _durable(gate, name, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')
    with (gate.out / name).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': name, 'sha256': sha(raw), 'bytes': len(raw)}


def _reserve(gate, kind, stage, commands):
    commit = gate.result.get('commit', gate.result.get('head'))
    require(gate.result.get('head', commit) == commit, 'case_stack_source_conflict')
    return _durable(gate, 'case-stack-reserve-' + kind + '-' + stage + '.json', {
        'source_commit': commit, 'ci_run': gate.result['run_id'],
        'candidate_sha256': gate.result['candidate_sha256'],
        'scope': 'CI_BOOTSTRAP_SEPARATE_FROM_CASE_2349', 'stage': stage,
        'commands': list(commands), 'reserved': len(commands),
        'state': 'PREPAID_UNKNOWN_UNTIL_CONFIRMED', 'no_refund': True, 'no_retry': True})


def _secondary(gate, stage, error):
    gate.result.setdefault('case_stack_secondary', []).append(
        {'stage': stage, 'error_class': type(error).__name__})


def _dependencies(gate):
    # Lazy imports keep candidate test imports independent of checkout harnesses.
    import admission_ci
    import cli_profile
    import cli_meter
    import ci_source_binding
    import native_runtime
    gate.bind_modules(sys.modules[__name__], sys.modules[__package__],
        admission_ci, admission_ci.app, cli_profile, cli_meter, ci_source_binding, native_runtime)
    require(getattr(gate.cli, '__func__', None) is admission_ci.Gate.cli,
            'case_stack_dispatcher')
    return admission_ci.app, cli_profile, cli_meter, ci_source_binding, native_runtime.NativeRuntime


def _file(root, relative):
    root = pathlib.Path(root).resolve(strict=True)
    path = root / relative
    require(not pathlib.PurePosixPath(relative).is_absolute() and
            '..' not in pathlib.PurePosixPath(relative).parts, 'case_stack_path')
    require(all(not p.is_symlink() and not (hasattr(p, 'is_junction') and p.is_junction())
                for p in (path, *path.parents)), 'case_stack_symlink')
    require(path.resolve(strict=True).is_relative_to(root), 'case_stack_path')
    return path


def _source(gate, migrations, profile, meter, binding):
    env = os.environ
    require(env.get('GITHUB_ACTIONS') == 'true' and
            env.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging' and
            env.get('GITHUB_REF') == 'refs/heads/main' and
            env.get('GITHUB_RUN_ATTEMPT') == '1', 'case_stack_ci_only')
    commit = meter.source_commit(gate.result)
    run = env.get('GITHUB_RUN_ID', '')
    require(re.fullmatch('[1-9][0-9]{0,18}', run) and int(run) <= 9223372036854775807
            and gate.result.get('run_id') == run and env.get('GITHUB_SHA') == commit,
            'case_stack_source_run')
    manifest_raw = (gate.out / 'candidate.json').read_bytes()
    manifest = json.loads(manifest_raw)
    digest = gate.result.get('candidate_sha256')
    require(isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest)
            and manifest.get('sha256') == digest and env.get('CANDIDATE_SHA256') == digest,
            'case_stack_candidate')
    files = manifest['sources']
    require(set(SOURCES) <= set(files), 'case_stack_sources_missing')
    require(migrations == profile.canonical(list(files)) and
            migrations == profile.canonical(migrations), 'case_stack_migrations')
    app_paths = ['_offline/phase6e_server_v1/supabase/migrations/' + name
                 for name in (profile.M45, profile.M46)]
    hashes = {}
    for name in list(SOURCES) + migrations + app_paths:
        raw = _file(gate.sources, name).read_bytes()
        require(name in files and sha(raw) == files[name], 'case_stack_source_hash')
        hashes[name] = files[name]
    gate.save('case-stack-loaded-source-before.json',
              binding.verify_all(pathlib.Path(env['GITHUB_WORKSPACE']), gate.sources, files))
    return {'source_commit': commit, 'ci_run': run, 'candidate_sha256': digest,
            'candidate_manifest_sha256': sha(manifest_raw),
            'migration_sources': {name: hashes[name] for name in migrations + app_paths}}


def _container(gate, stage):
    output = gate.command('case-stack-container-' + stage, ['docker', 'inspect', '--format',
        '{"id":"{{.Id}}","image_id":"{{.Image}}","image":"{{.Config.Image}}","running":{{.State.Running}}}',
        CONTAINER], timeout=5)
    value = json.loads(output.stdout)
    require(set(value) == {'id', 'image_id', 'image', 'running'} and
            isinstance(value['id'], str) and re.fullmatch('[a-f0-9]{64}', value['id'])
            and value['running'] is True and value['image_id'] == IMAGE_ID
            and value['image'] in IMAGES, 'case_stack_container_image')
    platform = gate.result['platform']
    require(platform.get('image_id') == value['image_id'] and
            platform.get('image') == value['image'] and
            IMAGES[value['image']] in platform.get('repository_digests', []) and
            platform.get('server', [{}])[0].get('num') == '170006',
            'case_stack_platform_binding')
    return value


def _sample(gate, runtime_type, trace, stage, *, fresh):
    commands = ('begin_read_only', 'metadata') + (() if fresh else ('registry_empty',)) + ('rollback',)
    reservation = _reserve(gate, 'native', stage, commands)
    runtime = runtime_type.disposable(gate)
    connection = None
    def execute(label, text):
        item = {'stage': stage, 'command': label, 'confirmed': False,
                'reservation_ref': reservation}
        trace.append(item)
        intent_error = None
        try:
            _durable(gate, 'case-stack-native-' + stage + '-' + label + '-intent.json', item)
        except Exception as error:
            if label != 'rollback':
                raise
            # The exact rollback slot is already durably prepaid before BEGIN.
            intent_error = error
            _secondary(gate, 'rollback_intent', error)
        try:
            result = connection.execute(text)
        except Exception as error:
            if intent_error is not None:
                _secondary(gate, 'rollback_dispatch', error)
                raise intent_error from None
            raise
        item['confirmed'] = True
        if intent_error is not None:
            raise intent_error
        _durable(gate, 'case-stack-native-' + stage + '-' + label + '-confirmed.json', item)
        return result
    try:
        connection = runtime.connect()
        try:
            execute('begin_read_only', 'BEGIN READ ONLY')
            rows = execute('metadata', META).fetchall()
            require(len(rows) == 1, 'case_stack_metadata_shape')
            value = dict(rows[0])
            for key, expected in {'database': 'postgres', 'role': 'postgres', 'version': '170006',
                                  'readonly': 'on', 'ssl': True}.items():
                require(type(value.get(key)) is type(expected) and value[key] == expected,
                        'case_stack_metadata_' + key)
            require(value.get('statement_timeout') in ('5s', '5000ms') and
                    value.get('lock_timeout') in ('1s', '1000ms'), 'case_stack_session_bounds')
            require(type(value.get('database_oid')) is int and value['database_oid'] > 0,
                    'case_stack_database_oid')
            if fresh:
                require(value.get('app_absent') is True and value.get('public_empty') is True,
                        'case_stack_not_fresh')
            else:
                empty = execute('registry_empty', EMPTY).fetchall()
                require(len(empty) == 1 and set(empty[0]) ==
                        {'runs_empty', 'steps_empty', 'evidence_empty'} and
                        all(v is True for v in empty[0].values()), 'case_stack_registry_not_empty')
        finally:
            primary = sys.exc_info()[1]
            try:
                execute('rollback', 'ROLLBACK')
            except Exception as error:
                _secondary(gate, 'native_rollback', error)
                if primary is None:
                    raise
        return value
    finally:
        primary = sys.exc_info()[1]
        cleanup_error = None
        try:
            if connection is not None:
                connection.close()
        except Exception as error:
            cleanup_error = error
            _secondary(gate, 'native_close', error)
        try:
            runtime.clear()
        except Exception as error:
            _secondary(gate, 'runtime_clear', error)
            if cleanup_error is None:
                cleanup_error = error
        if primary is None and cleanup_error is not None:
            raise cleanup_error


def _copy_migration(gate, name, hashes):
    relative = '_offline/phase6e_server_v1/supabase/migrations/' + name
    raw = _file(gate.sources, relative).read_bytes()
    require(sha(raw) == hashes[relative], 'case_stack_app_source_changed')
    with (gate.work / 'supabase/migrations' / name).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _history(gate, migrations, profile, stage, trace):
    reservation = _reserve(gate, 'history', stage, ('history',))
    entry = {'stage': stage, 'protocol_commands': 1, 'confirmed': False,
             'reservation_ref': reservation}
    trace.append(entry)
    rows = gate.rows(HISTORY)
    entry['confirmed'] = True
    _durable(gate, 'case-stack-history-' + stage + '-confirmed.json', entry)
    contract = profile.history_contract(rows, migrations, stage)
    gate.save('case-stack-history-' + stage + '.json', {'history': rows, **contract})
    return rows


def _dry(gate, phase):
    gate.result['phase'] = phase
    result = gate.cli('db', 'push', '--local', '--dry-run', '--skip-vault', timeout=45)
    text = (result.stdout + result.stderr).lower()
    require(result.returncode == 0 and 'up to date' in text and
            not re.search(r'would (?:be )?push|\d{14}_[a-z0-9_-]+\.sql', text),
            'case_stack_dry_not_empty')


def _receipt_ref(gate, name):
    raw = _file(gate.out, name).read_bytes()
    require(len(raw) <= 2000000, 'case_stack_receipt_size')
    return {'path': name, 'sha256': sha(raw), 'bytes': len(raw)}


def _bind_hooks(gate, hooks):
    if hooks is None:
        return
    modules = []
    for name in ('before45', 'after45'):
        method = getattr(hooks, name, None)
        require(inspect.ismethod(method) and method.__self__ is hooks,
                'case_stack_bound_hook_required')
        module = inspect.getmodule(method)
        require(module is not None, 'case_stack_hook_module')
        if module not in modules:
            modules.append(module)
    gate.bind_modules(*modules)


def _boundary_module(gate):
    import migration_failure_boundaries
    gate.bind_modules(migration_failure_boundaries, migration_failure_boundaries.rt)
    return migration_failure_boundaries


class _CanonicalView:
    """Intercept exactly M45; leave the actual Gate dispatcher and serial intact."""
    def __init__(self, gate, hooks, source):
        self.gate, self.hooks, self.source = gate, hooks, source
        self.attempted = False

    def __getattr__(self, name):
        return getattr(self.gate, name)

    def notify(self, stage, count, refs):
        value = {key: self.source[key] for key in ('source_commit', 'ci_run', 'candidate_sha256')}
        value.update(stage=stage, history_count=count, evidence_refs=refs,
                     full_chain_admission=False, hosted_admission=False)
        self.gate.result['case_stack_boundary'] = stage
        self.gate.save('case-stack-boundary-' + stage + '.json', value)
        getattr(self.hooks, stage)(json.loads(json.dumps(value)))

    def cli(self, *args, timeout=120):
        gate = self.gate
        if gate.result.get('phase') != 'migration_45':
            return gate.cli(*args, timeout=timeout)
        require(not self.attempted and args == ('migration', 'up', '--local'),
                'case_stack_boundary_reuse_or_command')
        self.attempted = True
        boundary = _boundary_module(gate)
        token = boundary.before(gate)
        require(len(token.sample['history']) == 44, 'case_stack_boundary_history44')
        self.notify('before45', 44, [_receipt_ref(gate, 'migration-boundary-pre.json')])
        result = gate.instrumented_cli().run_canonical(gate, args, gate.sources / boundary.M45)
        report = boundary.after(gate, token, result)
        require(report.get('component_verified') is True and
                report.get('after_m45', {}).get('history_count') == 45,
                'case_stack_boundary_history45')
        gate.result['migrations_applied'] = 45
        self.notify('after45', 45, [_receipt_ref(gate, 'cli-predispatch-canonical-45.json'),
                                  _receipt_ref(gate, 'migration-boundary-post.json')])
        return result


def bootstrap(gate, canonical_migrations, *, hooks=None):
    """One clean47 bootstrap; quota/app-suite/full-chain authority is excluded."""
    require(gate.container == CONTAINER and getattr(gate, 'cli_profile', None) == 'local_app'
            and getattr(gate, 'cli_namespace', '') == '',
            'case_stack_target')
    require(not hasattr(gate, '_case_stack_attempted') and
            not (gate.out / 'case-stack-attempt.json').exists(), 'case_stack_reuse')
    require(type(gate.result.get('migrations_applied')) is int and
            gate.result['migrations_applied'] == 0 and not getattr(gate, 'cli_protocol', []),
            'case_stack_already_started')
    require(not hasattr(gate, '_cli_predispatch_canonical_attempted'), 'case_stack_canonical_reuse')
    dest = gate.work / 'supabase/migrations'
    require(not dest.is_symlink() and
            (not dest.exists() or not list(dest.iterdir())), 'case_stack_migration_directory')
    app, profile, meter, binding, runtime_type = _dependencies(gate)
    source = _source(gate, canonical_migrations, profile, meter, binding)
    _bind_hooks(gate, hooks)
    gate._case_stack_attempted = True
    _durable(gate, 'case-stack-attempt.json', {**source, 'scope': 'FRESH_DISPOSABLE_CI_BOOTSTRAP',
              'no_retry': True, 'hosted_admission': False,
              'additional_sql_dispatch_max': 15, 'native_metadata_max': 7,
              'history_reads_max': 3, 'system_identifier_batch_max': 5,
              'additional_sql_prepaid': 15, 'no_refund': True,
              'bootstrap_total_sql_commands': None})
    trace = []
    history_trace = []
    serial_start = gate.serial
    stage = 'preflight'
    admin_reserved = 0
    admin_confirmed = None
    try:
        initial = _container(gate, 'before')
        before = _sample(gate, runtime_type, trace, 'before', fresh=True)
        ca = _file(gate.work, 'fmz-ci-ca.crt').read_bytes()
        require(ca.startswith(b'-----BEGIN CERTIFICATE-----'), 'case_stack_ca')
        stage = 'canonical45'
        view = gate if hooks is None else _CanonicalView(gate, hooks, source)
        app.base.Gate.rebuild(view, canonical_migrations)
        require(gate.result.get('migrations_applied') == 45 and
                not getattr(gate, 'cli_protocol', []), 'case_stack_canonical_profile')
        _history(gate, canonical_migrations, profile, 'canonical', history_trace)
        stage = 'app46'
        _copy_migration(gate, profile.M45, source['migration_sources'])
        gate.result['phase'] = 'local_app_schema'
        gate.cli('migration', 'up', '--local', timeout=45)
        _history(gate, canonical_migrations, profile, 'minimal', history_trace)
        stage = 'minimal_dry'
        _dry(gate, 'local_app_schema')
        stage = 'app47'
        _copy_migration(gate, profile.M46, source['migration_sources'])
        gate.result['phase'] = 'local_app_outbox'
        gate.cli('migration', 'up', '--local', timeout=45)
        history = _history(gate, canonical_migrations, profile, 'complete', history_trace)
        stage = 'final_dry'
        _dry(gate, 'advisors_and_dryrun')
        require(len(gate.cli_protocol) == 4, 'case_stack_cli_count')
        for index, receipt in enumerate(gate.cli_protocol):
            profile.cli_receipt(receipt, index)
            require(json.loads((gate.out / ('cli-protocol-' + str(index) + '.json')).read_bytes())
                    == receipt, 'case_stack_cli_receipt_changed')
        stage = 'attestation'
        after = _sample(gate, runtime_type, trace, 'after', fresh=False)
        final = _container(gate, 'after')
        require(final == initial and before['database_oid'] == after['database_oid'] and
                _file(gate.work, 'fmz-ci-ca.crt').read_bytes() == ca, 'case_stack_target_changed')
        admin_reserved = 5
        admin_ref = _reserve(gate, 'admin', 'system_identifier',
            ('begin_read_only', 'statement_timeout', 'lock_timeout', 'system_identifier', 'rollback'))
        control = gate.command('case-stack-system-identifier', ['docker', 'exec', '-i', CONTAINER,
            'psql', '-X', '-U', 'supabase_admin', '-d', 'postgres', '-qAt',
            '-v', 'ON_ERROR_STOP=1'], sql=CONTROL_SQL, timeout=5)
        admin_confirmed = 5
        _durable(gate, 'case-stack-admin-system_identifier-confirmed.json', {
            'reservation_ref': admin_ref, 'confirmed_commands': 5})
        system_id = control.stdout.strip()
        require(re.fullmatch('[1-9][0-9]{0,19}', system_id), 'case_stack_system_identifier')
        manifest_raw = (gate.out / 'candidate.json').read_bytes()
        require(sha(manifest_raw) == source['candidate_manifest_sha256'], 'case_stack_manifest_changed')
        files = json.loads(manifest_raw)['sources']
        require({p.name for p in dest.iterdir()} ==
                {pathlib.PurePosixPath(n).name for n in source['migration_sources']},
                'case_stack_work_migrations_changed')
        for name, expected in source['migration_sources'].items():
            require(sha(_file(gate.sources, name).read_bytes()) == expected and
                    sha(_file(dest, pathlib.PurePosixPath(name).name).read_bytes()) == expected,
                    'case_stack_migration_bytes_changed')
        gate.save('case-stack-loaded-source-after.json',
                  binding.verify_all(pathlib.Path(os.environ['GITHUB_WORKSPACE']), gate.sources, files))
        refs = [_receipt_ref(gate, name) for name in (
            'candidate.json', 'platform.json', 'integral-local-tls.json',
            'cli-predispatch-canonical-45.json', 'migration-boundary-post.json',
            'cli-protocol-0.json', 'cli-protocol-1.json', 'cli-protocol-2.json', 'cli-protocol-3.json',
            'case-stack-history-canonical.json', 'case-stack-history-minimal.json',
            'case-stack-history-complete.json')]
        if hooks is not None:
            refs += [_receipt_ref(gate, 'case-stack-boundary-' + stage + '.json')
                     for stage in ('before45', 'after45')]
        receipt = {**source, 'status': 'CLEAN47_BOOTSTRAP_PASS', 'scope': 'DISPOSABLE_CI_ONLY',
            'evidence_refs': refs,
            'history': history, 'canonical_count': 45, 'private_app_count': 2,
            'container': final, 'pg_system_identifier': system_id, 'database_oid': after['database_oid'],
            'database': 'postgres', 'ssl': True, 'sslmode': 'verify-full', 'ca_sha256': sha(ca),
            'registry_empty': True, 'auth_database_bound': False,
            'app_suite_repeated': False, 'full_same_source_app_ci_required': True,
            'quota_applied': False, 'claim_created': False, 'database_reset': False,
            'full_chain_admission': False, 'hosted_admission': False, 'hosted_calls': 0,
            'accounting_scope': 'CI_BOOTSTRAP_SEPARATE_FROM_CASE_2349',
            'serial_before': serial_start, 'serial_after': gate.serial,
            'native_commands': trace, 'history_commands': history_trace,
            'additional_sql_dispatch_max': 15,
            'additional_sql_prepaid': 15, 'no_refund': True,
            'admin_reservation_ref': admin_ref,
            'admin_sql_reserved': admin_reserved, 'admin_sql_confirmed': admin_confirmed,
            'bootstrap_total_sql_commands': None,
            'canonical_1_44_sql_count': 'NOT_MEASURED_BY_THIS_HELPER',
            'cli_profile': 'local_app', 'cli_slots': [r['slot'] for r in gate.cli_protocol]}
        gate.save('case-stack-bootstrap.json', receipt)
        gate.result['migrations_applied'] = 47
        gate.result['clean_rebuild'] = '47/47_PASS_LOCAL_CANDIDATE'
        gate.result['case_stack'] = 'CLEAN47_BOOTSTRAP_PASS'
        return receipt
    except Exception as error:
        try:
            gate.save('case-stack-failure.json', {**source, 'status': 'NO_GO', 'stage': stage,
                'boundary_stage': gate.result.get('case_stack_boundary'),
                'error_class': type(error).__name__, 'native_commands': trace,
                'history_commands': history_trace, 'additional_sql_dispatch_max': 15,
                'additional_sql_prepaid': 15, 'no_refund': True,
                'admin_sql_reserved': admin_reserved, 'admin_sql_confirmed': admin_confirmed,
                'full_chain_admission': False,
                'hosted_admission': False, 'automatic_retry': False})
        except Exception as secondary:
            gate.result.setdefault('case_stack_secondary', []).append(
                {'stage': 'failure_receipt', 'error_class': type(secondary).__name__})
        raise
