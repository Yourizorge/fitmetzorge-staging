"""Fetch once, restart from candidate sources, admit before any platform install."""
import argparse
import hashlib
import importlib
import json
import os
import pathlib
import re
import sys

# The isolated child executes this exact candidate file, not a checkout module.
if __package__ in (None, ''):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    __package__ = 'case_stack_v1'
from .bootstrap import SOURCES, bootstrap, require

PREFIX = '_offline/phase6e11/endchain_v1/'
HANDOFF = 'case-entry-handoff.json'
RESULT_FIELDS = frozenset(('status', 'phase', 'run_id', 'commit', 'cli', 'cli_sha256',
    'migrations_applied', 'hosted_requests', 'member_data_used', 'external_ai_calls',
    'production_touched', 'case_name', 'case_execution_started', 'cli_profile',
    'candidate_sha256', 'full_chain_admission', 'hosted_admitted',
    'package21_released', 'admission_components'))


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'case_entry_duplicate_json')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def _adapter():
    return importlib.import_module('quota_candidate_v1.case_ci')


def _environment(env, adapter):
    require(env.get('GITHUB_ACTIONS') == 'true' and
            env.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging' and
            env.get('GITHUB_REF') == 'refs/heads/main' and
            env.get('GITHUB_RUN_ATTEMPT') == '1', 'case_entry_ci_scope')
    require(re.fullmatch('[a-f0-9]{40}', env.get('GITHUB_SHA', '')) and
            re.fullmatch('[1-9][0-9]{0,18}', env.get('GITHUB_RUN_ID', '')) and
            int(env['GITHUB_RUN_ID']) <= 9223372036854775807, 'case_entry_source_run')
    require(re.fullmatch('[a-f0-9]{40}', env.get('CANDIDATE_BLOB', '')) and
            re.fullmatch('[a-f0-9]{64}', env.get('CANDIDATE_SHA256', '')), 'case_entry_candidate')
    names = getattr(adapter, 'CASE_NAMES', ())
    require(type(names) is tuple and len(names) == 15 and len(set(names)) == 15
            and 'normal' in names and all(isinstance(n, str) and
                re.fullmatch('[a-z][a-z0-9_]{0,63}', n) for n in names), 'case_entry_names')
    name = env.get('CASE_NAME')
    require(name in names, 'case_entry_name')
    require(getattr(adapter, 'READY', False) is True and
            callable(getattr(adapter, 'run', None)) and
            callable(getattr(adapter, 'prepare_execution', None)), 'case_entry_adapter_not_ready')
    sources = getattr(adapter, 'SOURCES', ())
    require(type(sources) is tuple and bool(sources) and len(set(sources)) == len(sources)
            and PREFIX + 'quota_candidate_v1/case_ci.py' in sources
            and all(isinstance(p, str) and p.startswith('_offline/') and
                    '\\' not in p and '..' not in pathlib.PurePosixPath(p).parts
                    for p in sources), 'case_entry_adapter_sources')
    return name, set(sources) | set(SOURCES)


def _paths():
    from admission_module_binding import checked_path
    temp = checked_path(os.environ['RUNNER_TEMP'])
    return temp, *(checked_path(temp / name) for name in
                  ('fmz-db41-evidence', 'fmz-db41-stack', 'fmz-db41-sources'))


def _source_check(gate, required, *, receipt):
    import ci_source_binding
    from admission_module_binding import checked_path
    raw = checked_path(gate.out / 'candidate.json').read_bytes()
    require(len(raw) <= 2000000, 'case_entry_manifest_size')
    manifest = _json(raw)
    require(manifest['blob'] == os.environ['CANDIDATE_BLOB'] and
            manifest['sha256'] == os.environ['CANDIDATE_SHA256'], 'case_entry_manifest_binding')
    sources = manifest['sources']
    require(required | set(ci_source_binding.HARNESS) <= sources.keys(), 'case_entry_sources_missing')
    for name, digest in sources.items():
        path = checked_path(gate.sources / name)
        require(path.is_relative_to(gate.sources.resolve()) and _sha(path.read_bytes()) == digest,
                'case_entry_candidate_bytes')
    gate.save(receipt, ci_source_binding.verify_all(
        pathlib.Path(os.environ['GITHUB_WORKSPACE']), gate.sources, sources))
    return raw, sources


def _check_origin(gate, *modules):
    root = gate.sources.resolve()
    checkout = pathlib.Path(os.environ['GITHUB_WORKSPACE']).resolve()
    for module in modules:
        require(pathlib.Path(module.__file__).resolve().is_relative_to(root),
                'case_entry_candidate_origin')
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = pathlib.Path(filename).resolve()
            require(not path.is_relative_to(checkout) or path.is_relative_to(root),
                    'case_entry_checkout_module_loaded')
    gate.bind_modules(*modules)


def _handoff(gate, migrations):
    require(set(vars(gate)) == {'temp', 'out', 'work', 'sources', 'result', 'serial'}
            and gate.serial == 0 and set(gate.result) == RESULT_FIELDS,
            'case_entry_not_pristine')
    require((gate.temp.resolve(), gate.out.resolve(), gate.work.resolve(), gate.sources.resolve())
            == _paths(), 'case_entry_transport_paths')
    raw = (gate.out / 'candidate.json').read_bytes()
    state = {'format': 'case-preinstall-handoff-v1', 'manifest_sha256': _sha(raw),
             'migrations': migrations, 'result': gate.result, 'serial': gate.serial}
    # Gate.save is exclusive and fsyncs. No environment, URLs or credentials are serialized.
    gate.save(HANDOFF, state)
    state_raw = (gate.out / HANDOFF).read_bytes()
    require(len(state_raw) <= 65536, 'case_entry_handoff_size')
    entry = gate.sources / PREFIX / 'case_stack_v1/ci.py'
    env = {k: v for k, v in os.environ.items() if k not in (
        'GH_READ_TOKEN', 'GITHUB_TOKEN', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD',
        'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP')}
    os.execve(sys.executable, [sys.executable, '-B', '-I', str(entry),
                              '--candidate-state-sha256', _sha(state_raw)], env)
    raise RuntimeError('case_entry_exec_returned')


def _restore(admission, state_sha):
    from admission_module_binding import checked_path
    temp, out, work, sources = _paths()
    require(pathlib.Path(__file__).resolve() == sources / PREFIX / 'case_stack_v1/ci.py',
            'case_entry_resume_origin')
    raw = checked_path(out / HANDOFF).read_bytes()
    require(len(raw) <= 65536 and _sha(raw) == state_sha, 'case_entry_handoff_hash')
    state = _json(raw)
    require(set(state) == {'format', 'manifest_sha256', 'migrations', 'result', 'serial'} and
            state['format'] == 'case-preinstall-handoff-v1' and state['serial'] == 0,
            'case_entry_handoff_shape')
    manifest_raw = checked_path(out / 'candidate.json').read_bytes()
    require(_sha(manifest_raw) == state['manifest_sha256'], 'case_entry_handoff_manifest')
    manifest = _json(manifest_raw)
    migrations = sorted(p for p in manifest['sources'] if p.startswith('supabase/migrations/'))
    require(state['migrations'] == migrations and len(migrations) == 45, 'case_entry_handoff_migrations')
    result = state['result']
    require(set(result) == RESULT_FIELDS and result['commit'] == os.environ['GITHUB_SHA']
            and result['run_id'] == os.environ['GITHUB_RUN_ID']
            and result['candidate_sha256'] == os.environ['CANDIDATE_SHA256']
            and result['case_name'] == os.environ['CASE_NAME']
            and result['phase'] == 'candidate' and result['status'] == 'NO_GO'
            and result['case_execution_started'] is False and result['migrations_applied'] == 0
            and result['hosted_requests'] == 0 and result['admission_components'] == {}
            and result['full_chain_admission'] is False and result['hosted_admitted'] is False,
            'case_entry_handoff_identity')
    # Fetch has no live handles. Do not recreate directories, refetch, or reopen a ledger.
    gate = admission.Gate.__new__(admission.Gate)
    gate.temp, gate.out, gate.work, gate.sources = temp, out, work, sources
    gate.result, gate.serial = result, 0
    return gate, migrations


def _parser_dependency(gate):
    """Exact existing app dependency command, separate from database installation."""
    target = gate.sources / 'supabase/.temp/phase6e11-pg17-parser'
    gate.result['phase'] = 'case_parser_dependency'
    gate.command('case-parser-install', ['python3', '-m', 'pip', 'install',
        '--disable-pip-version-check', '--only-binary=:all:', '--target', str(target),
        'pglast==7.20', 'psycopg[binary]==3.2.10'], timeout=120)
    sys.path.insert(0, str(target))
    import sql_protocol
    _check_origin(gate, sql_protocol)
    sql_protocol.parser()


def _execute(gate, migrations, name, adapter):
    _parser_dependency(gate)
    gate.result['phase'] = 'case_preinstall_admission'
    prepared = adapter.prepare_execution(gate, name)
    import admission_budget_root_runtime as root
    _check_origin(gate, root)
    # This source-owned operation must prepay AND observe the complete install.
    # The explicit 13 SQL inventory is not a total startup bound or observation.
    install = getattr(root, 'install_platform', None)
    require(callable(install), 'case_platform_observer_missing')
    gate.result['phase'] = 'case_stack_install'
    install(gate, ledger=prepared.ledger)
    gate.result['case_execution_started'] = True
    return adapter.run(gate, migrations, name, bootstrap=bootstrap, prepared=prepared)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-state-sha256', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    gate = None
    code = 1
    summary = {'status': 'ADAPTER_NOT_READY', 'full_chain_admission': False, 'hosted_admitted': False}
    try:
        adapter = _adapter()
        name, sources = _environment(os.environ, adapter)
        import admission_ci
        admission_ci.EXTRA |= sources
        admission_ci.app.previous.prior.old.EXTRA |= sources
        if args.candidate_state_sha256 is None:
            gate = admission_ci.Gate()
            gate.result.update(case_name=name, phase='candidate', case_execution_started=False)
            migrations = gate.fetch()
            _source_check(gate, sources, receipt='case-entry-loaded-source.json')
            _handoff(gate, migrations)
        else:
            require(re.fullmatch('[a-f0-9]{64}', args.candidate_state_sha256), 'case_entry_state_digest')
            gate, migrations = _restore(admission_ci, args.candidate_state_sha256)
            _source_check(gate, sources, receipt='case-entry-candidate-source.json')
            _check_origin(gate, sys.modules[__name__], adapter, admission_ci)
            report = _execute(gate, migrations, name, adapter)
            require(isinstance(report, dict) and report.get('status') == 'CASE_PASS'
                    and report.get('case_name') == name
                    and report.get('source_commit') == os.environ['GITHUB_SHA']
                    and report.get('ci_run') == os.environ['GITHUB_RUN_ID']
                    and report.get('candidate_sha256') == os.environ['CANDIDATE_SHA256'],
                    'case_entry_actual_report')
            gate.save('case-execution.json', report)
            summary.update(status='CASE_PASS', case_name=name)
            code = 0
    except Exception as error:
        summary.update(status='NO_GO' if gate is not None else 'ADAPTER_NOT_READY',
                       error_type=type(error).__name__)
    finally:
        if gate is not None:
            gate.result.update(summary)
            gate.result['matrix_aggregation_required'] = True
            try:
                gate.save('result.json', gate.result)
            except Exception as error:
                code = 1
                summary['status'] = 'NO_GO'
                summary.setdefault('error_type', type(error).__name__)
                summary['result_write_error_type'] = type(error).__name__
                gate.result.update(summary)
        print(json.dumps(summary, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
