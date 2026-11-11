"""One-shot disposable component CI. Source handoff before platform installation."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import uuid

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-sha256')
    args = parser.parse_args(argv)
    gate = None; code = 1
    summary = {'status':'NO_GO','full_chain_admission':False,'hosted_admitted':False,'READY':False}
    try:
        environment(os.environ)
        import admission_ci
        from case_stack_v1.ci import _source_check, _check_origin
        from . import parent
        names = inventory.register(admission_ci)
        if args.state_sha256 is None:
            gate = admission_ci.Gate()
            migrations = gate.fetch()
            _source_check(gate, names, receipt='pg-component-checkout-source.json')
            publish_handoff(gate, migrations)
        else:
            need(re.fullmatch('[a-f0-9]{64}', args.state_sha256), 'state_pin')
            gate, migrations, run_id = restore(admission_ci, args.state_sha256)
            _source_check(gate, names, receipt='pg-component-candidate-source.json')
            _check_origin(gate, sys.modules[__name__], inventory, parent, admission_ci)
            result = parent.run(gate, migrations, run_id)
            need(result['status'] == 'LOCAL_PG_AUTH_COMPONENT_RECORDED'
                and result['database_process_stopped'] is True, 'component_incomplete')
            summary.update(status=result['status'], run_id=run_id)
            code = 0
    except BaseException as error:
        summary['error_class'] = type(error).__name__
    finally:
        if gate is not None:
            gate.result.update(summary)
            try: gate.save('result.json', gate.result)
            except BaseException as error:
                code = 1; summary['status'] = 'NO_GO'; summary['result_write_error'] = type(error).__name__
        print(json.dumps(summary, sort_keys=True))
    return code


if __name__ == '__main__': raise SystemExit(main())
