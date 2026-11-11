"""One actual clean47 + local component lifetime; no root/endchain admission."""
import importlib
import json
import os
import re
import sys

from . import context as lifetime, lifecycle, runner, worker
from .lifecycle import need

DB_NAME = 'supabase_db_fmz-db41-ci'
DB_IMAGE = 'sha256:66089200353d90686fe9b252a47d17d078364bf47c50190852c33dc850a0191f'


def producers_terminal(context):
    if context is None:
        return True
    if context.body_started and not context.body_terminal:
        return False
    # AuthContainer.__init__ performs only inventory; create marks its attempt
    # before dispatch. An absent/unstarted producer is not a stopped producer.
    if context.server is None or not context.server.create_attempted:
        return not context.body_started
    return context.server.stopped is True


def db_state(gate, identity):
    need(re.fullmatch('[a-f0-9]{64}', identity), 'db_identity')
    raw = gate.command('component-database-state', ['docker','--context','default','inspect','--format',
        '{"id":"{{.Id}}","name":"{{.Name}}","image":"{{.Image}}","running":{{.State.Running}},"pid":{{.State.Pid}}}',
        identity], timeout=5).stdout
    value = json.loads(raw)
    need(set(value) == {'id','name','image','running','pid'} and value['id'] == identity
         and value['name'] == '/'+DB_NAME and value['image'] == DB_IMAGE
         and type(value['running']) is bool and type(value['pid']) is int, 'db_state')
    return value


def run(gate, migrations, run_id):
    import admission_ci
    stack = importlib.import_module('case_stack_v1.bootstrap')
    need(type(gate) is admission_ci.Gate, 'actual_gate')
    lifecycle.local_environment()
    records = lifecycle.Records(gate, 'component-parent',
        [sys.modules[__name__], lifetime, stack, runner, worker, admission_ci])
    gate.bind_modules(sys.modules[__name__], lifetime, stack, runner, worker)
    endpoint = gate.command('component-local-engine', ['docker','--context','default','context',
        'inspect','default','--format','{{.Endpoints.docker.Host}}'], timeout=5).stdout.strip()
    need(endpoint == 'unix:///var/run/docker.sock', 'local_engine')
    existing = gate.command('component-database-absence', ['docker','--context','default','ps','--all',
        '--filter','name=^/'+DB_NAME+'$','--format','{{.ID}}'], timeout=5).stdout.strip()
    need(not existing, 'preexisting_database')
    records.save('database-intent.json', {'exact_name':DB_NAME,'exact_image':DB_IMAGE,
        'absent_before_install':True,'source_commit':os.environ['GITHUB_SHA'],
        'run_id':run_id,'partial_install_ownership_admitted':False})
    owned = context = None
    primary = None
    result = {'status':'NO_GO','run_id':run_id,'source_commit':os.environ['GITHUB_SHA'],
        'ci_run':os.environ['GITHUB_RUN_ID'],'candidate_sha256':os.environ['CANDIDATE_SHA256'],
        'database_process_stopped':False,'full_chain_admission':False,'READY':False,
        'global_cleanup':False,'database_volume_removed':False,
        'hosted_admitted':False,'wal_admission_proven':False,'secondary_errors':[]}
    try:
        gate.install()
        observed = gate.command('component-database-id', ['docker','--context','default','ps','--all',
            '--no-trunc','--filter','name=^/'+DB_NAME+'$','--format','{{.ID}}'], timeout=5).stdout.strip()
        state = db_state(gate, observed)
        need(state['running'] and state['pid'] > 0, 'database_running')
        records.save('database-owned.json', state)
        owned = state
        result['clean47'] = stack.bootstrap(gate, migrations, run_id=run_id)
        result['canonical_44_semantic_replay'] = 'PENDING_INDEPENDENT_REPLAY'
        context = lifetime.Context(gate, result['clean47'], run_id)
        with context as ctx:
            result['worker'] = worker.run(gate, ctx, run_id=run_id)
            result['auth'] = runner.run(gate, ctx, run_id=run_id)
            context.confirm_body_terminal(result['worker'], result['auth'])
        need(context.result['status'] == 'LOCAL_PARENT_LIFECYCLE_CONFIRMED', 'parent_lifecycle_incomplete')
        result['parent_lifecycle'] = context.result
        result['status'] = 'LOCAL_PG_AUTH_COMPONENT_RECORDED'
    except BaseException as error:
        primary = error
        result['original_error_class'] = type(error).__name__
        raise
    finally:
        def secondary(stage, error):
            result['status'] = 'NO_GO'
            result['secondary_errors'].append({'phase':stage,'error_class':type(error).__name__})
            if primary is not None: primary.add_note('component_parent_'+stage+':'+type(error).__name__)
        try:
            # Never infer ownership after an incomplete install. Never stop the DB
            # under an unconfirmed managed producer or unreaped body worker.
            if owned is not None:
                need(producers_terminal(context), 'producer_stop_unknown')
                before = db_state(gate, owned['id'])
                need(before['running'] and before['pid'] > 0, 'database_changed')
                gate.command('component-database-stop', ['docker','--context','default','stop',
                    '--time','5',owned['id']], timeout=10)
                after = db_state(gate, owned['id'])
                need(not after['running'] and after['pid'] == 0, 'database_stop_unknown')
                records.save('database-stopped.json', after)
                result['database_process_stopped'] = True
                result['database_volume_retained'] = True
            else:
                result['partial_install_unowned'] = True
        except BaseException as error:
            secondary('database_close', error)
        try:
            records.save('result.json', result)
            records.seal()
            gate.save('pg-auth-parent-result.json', result)
        except BaseException as error:
            if primary is None: raise
            secondary('export', error)
        if primary is None and result['secondary_errors']:
            raise RuntimeError('component_parent_close_incomplete')
    return result
