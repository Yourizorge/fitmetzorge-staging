"""One-shot disposable component CI. Source handoff before platform installation."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import uuid
import traceback

if __package__ in (None, ''):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    __package__ = 'pg_auth_component'

from . import inventory

HANDOFF = 'pg-component-entry-handoff.json'
PREFIX = '_offline/phase6e11/endchain_v1/'


def need(value, reason):
    if not value: raise ValueError('pg_component_entry_' + reason)


def environment(env):
    need(sys.platform == 'linux' and sys.version_info[:2] == (3, 12)
        and env.get('GITHUB_ACTIONS') == 'true'
        and env.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
        and env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_RUN_ATTEMPT') == '1', 'scope')
    for key, regex in (('GITHUB_SHA','[a-f0-9]{40}'),('GITHUB_RUN_ID','[1-9][0-9]{0,18}'),
                       ('CANDIDATE_BLOB','[a-f0-9]{40}'),('CANDIDATE_SHA256','[a-f0-9]{64}')):
        need(re.fullmatch(regex, env.get(key, '')), 'identity')


def resumed_environment(env):
    keys = ('GITHUB_ACTIONS','GITHUB_REPOSITORY','GITHUB_REF','GITHUB_RUN_ATTEMPT',
            'GITHUB_SHA','GITHUB_RUN_ID','GITHUB_WORKSPACE','RUNNER_TEMP',
            'CANDIDATE_BLOB','CANDIDATE_SHA256','PATH','HOME')
    result = {key: env[key] for key in keys}
    result.update(LANG='C.UTF-8', LC_ALL='C.UTF-8')
    return result


def publish_handoff(gate, migrations):
    need(gate.result['migrations_applied'] == 0 and gate.serial == 0, 'already_installed')
    raw = (gate.out/'candidate.json').read_bytes()
    state = {'format':'pg-auth-component-handoff-v1', 'manifest_sha256':hashlib.sha256(raw).hexdigest(),
        'migrations':migrations, 'result':gate.result, 'run_id':str(uuid.uuid4())}
    gate.save(HANDOFF, state)
    original = (gate.out/HANDOFF).read_bytes()
    need(json.loads(original) == state and len(original) <= 65536, 'handoff_readback')
    entry = gate.sources/PREFIX/'pg_auth_component/entry.py'
    os.execve(sys.executable, [sys.executable,'-B','-I',str(entry),
        '--state-sha256',hashlib.sha256(original).hexdigest()], resumed_environment(os.environ))
    raise RuntimeError('pg_component_exec_returned')


def restore(admission, expected):
    from case_stack_v1.ci import _paths
    temp, out, work, sources = _paths()
    need(pathlib.Path(__file__).resolve() == sources/PREFIX/'pg_auth_component/entry.py', 'candidate_origin')
    raw = (out/HANDOFF).read_bytes()
    need(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == expected, 'handoff_hash')
    state = json.loads(raw)
    need(set(state) == {'format','manifest_sha256','migrations','result','run_id'}
        and state['format'] == 'pg-auth-component-handoff-v1', 'handoff_shape')
    manifest_raw = (out/'candidate.json').read_bytes()
    need(hashlib.sha256(manifest_raw).hexdigest() == state['manifest_sha256'], 'candidate_manifest')
    manifest = json.loads(manifest_raw)
    need(state['migrations'] == sorted(name for name in manifest['sources'] if name.startswith('supabase/migrations/'))
        and len(state['migrations']) == 45, 'migration_set')
    value = state['result']
    need(value['commit'] == os.environ['GITHUB_SHA'] and value['run_id'] == os.environ['GITHUB_RUN_ID']
        and value['candidate_sha256'] == os.environ['CANDIDATE_SHA256']
        and value['migrations_applied'] == 0 and value['status'] == 'NO_GO'
        and value['full_chain_admission'] is False and value['hosted_admitted'] is False, 'handoff_identity')
    need(str(uuid.UUID(state['run_id'])) == state['run_id'] and uuid.UUID(state['run_id']).version == 4,
        'disposable_uuid')
    gate = admission.Gate.__new__(admission.Gate)
    gate.temp, gate.out, gate.work, gate.sources = temp, out, work, sources
    gate.result, gate.serial = value, 0
    return gate, state['migrations'], state['run_id']


def diagnostic(error, phase):
    """Preserve original class/location, never exception text, SQL or locals."""
    root = pathlib.Path(__file__).resolve().parents[4]
    frames = []
    for frame in traceback.extract_tb(error.__traceback__)[-16:]:
        path = pathlib.Path(frame.filename).resolve()
        if path.is_relative_to(root) and path.is_file():
            frames.append({'source':path.relative_to(root).as_posix(), 'line':frame.lineno,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    name = getattr(error, 'name', None)
    return {'phase':phase, 'error_class':type(error).__name__,
        'import_name':name if type(name) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_.]{0,160}', name) else None,
        'frames':frames, 'exception_text_exported':False, 'full_chain_admission':False}


def save_early_failure(expected, detail):
    """Write only beside the authenticated resume handoff, before Gate exists."""
    need(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected), 'failure_state_pin')
    from admission_module_binding import checked_path
    temp = checked_path(os.environ['RUNNER_TEMP'])
    out = checked_path(temp/'fmz-db41-evidence')
    sources = checked_path(temp/'fmz-db41-sources')
    entry = checked_path(sources/PREFIX/'pg_auth_component/entry.py')
    need(pathlib.Path(__file__).resolve() == entry, 'failure_origin')
    raw = checked_path(out/HANDOFF).read_bytes()
    need(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == expected, 'failure_handoff')
    state = json.loads(raw)
    manifest_raw = checked_path(out/'candidate.json').read_bytes()
    need(len(manifest_raw) <= 2000000 and hashlib.sha256(manifest_raw).hexdigest() == state['manifest_sha256'],
         'failure_manifest')
    manifest = json.loads(manifest_raw)
    need(manifest['sources'][PREFIX+'pg_auth_component/entry.py'] == hashlib.sha256(entry.read_bytes()).hexdigest()
        and manifest['sha256'] == os.environ['CANDIDATE_SHA256']
        and state['result']['commit'] == os.environ['GITHUB_SHA']
        and state['result']['run_id'] == os.environ['GITHUB_RUN_ID'], 'failure_binding')
    value = {'format':'pg-component-entry-failure-v1','status':'NO_GO',
        'source_commit':os.environ['GITHUB_SHA'],'ci_run':os.environ['GITHUB_RUN_ID'],
        'candidate_sha256':os.environ['CANDIDATE_SHA256'],'handoff_sha256':expected,
        'original_error':detail,'full_chain_admission':False,'hosted_admitted':False}
    data = (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    need(len(data) <= 16384, 'failure_size')
    path = out/'pg-component-entry-failure.json'
    with path.open('xb') as stream:
        need(stream.write(data) == len(data), 'failure_short_write')
        stream.flush(); os.fsync(stream.fileno())
    need(checked_path(path).read_bytes() == data, 'failure_readback')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-sha256')
    args = parser.parse_args(argv)
    gate = None; code = 1
    summary = {'status':'NO_GO','full_chain_admission':False,'hosted_admitted':False,'READY':False}
    phase = 'environment'
    try:
        environment(os.environ)
        phase = 'admission_import'
        import admission_ci
        phase = 'stack_import'
        from case_stack_v1.ci import _source_check, _check_origin
        phase = 'parent_import'
        from . import parent
        phase = 'inventory_register'
        names = inventory.register(admission_ci)
        if args.state_sha256 is None:
            phase = 'fetch'
            gate = admission_ci.Gate()
            migrations = gate.fetch()
            phase = 'checkout_source'
            _source_check(gate, names, receipt='pg-component-checkout-source.json')
            phase = 'publish_handoff'
            publish_handoff(gate, migrations)
        else:
            phase = 'restore'
            need(re.fullmatch('[a-f0-9]{64}', args.state_sha256), 'state_pin')
            gate, migrations, run_id = restore(admission_ci, args.state_sha256)
            phase = 'candidate_source'
            _source_check(gate, names, receipt='pg-component-candidate-source.json')
            phase = 'candidate_origin'
            _check_origin(gate, sys.modules[__name__], inventory, parent, admission_ci)
            phase = 'parent_run'
            result = parent.run(gate, migrations, run_id)
            need(result['status'] == 'LOCAL_PG_AUTH_COMPONENT_RECORDED'
                and result['database_process_stopped'] is True, 'component_incomplete')
            summary.update(status=result['status'], run_id=run_id)
            code = 0
    except BaseException as error:
        summary['error_class'] = type(error).__name__
        summary['failure_phase'] = phase
        try:
            detail = diagnostic(error, phase)
            summary['original_error'] = detail
            if gate is None and args.state_sha256 is not None:
                save_early_failure(args.state_sha256, detail)
        except BaseException as secondary:
            summary['diagnostic_error_class'] = type(secondary).__name__
    finally:
        if gate is not None:
            gate.result.update(summary)
            try: gate.save('result.json', gate.result)
            except BaseException as error:
                code = 1; summary['status'] = 'NO_GO'; summary['result_write_error'] = type(error).__name__
        print(json.dumps(summary, sort_keys=True))
    return code


if __name__ == '__main__': raise SystemExit(main())
