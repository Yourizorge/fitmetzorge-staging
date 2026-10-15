"""Final counted receipt. No SQL execution or hosted admission."""
import json,pathlib
AUTHORIZATION = json.loads(pathlib.Path(__file__).with_name('authorization.json').read_text())
RUN_ID = AUTHORIZATION['run_id']
PURPOSE = AUTHORIZATION['purpose']
BOOTSTRAP = {'local_fixture_cleanup', 'local_observer_schema', 'local_observer_triggers',
             'profile_seed_a_member', 'profile_seed_a_trainer', 'profile_seed_b_member', 'operator_seed'}


def allowance(run_id, purpose):
    return AUTHORIZATION['maximum_sql'] if (run_id, purpose) == (RUN_ID, PURPOSE) else 128


def counted_close(trace, preflight, cli, auth, workflow, run_id, purpose):
    if (run_id, purpose) != (RUN_ID, PURPOSE):
        raise ValueError('closure_run_not_registered')
    if [c['command'] for c in trace] != list(range(1, len(trace) + 1)) or not all(c['confirmed'] for c in trace):
        raise ValueError('closure_incomplete_protocol')
    if any(c['phase'] == 'final_closure' for c in trace):
        raise ValueError('closure_already_attempted')
    if len(preflight['commands']) != 4 or not all(c['confirmed'] for c in preflight['commands']):
        raise ValueError('closure_preflight')
    if len(cli) != 2 or [x['protocol_commands'] for x in cli] != [14, 2] or not all(x['complete'] for x in cli):
        raise ValueError('closure_cli')
    for item in cli:
        observers=item.get('observer_commands',[])
        if len(observers)!=8 or not all(c['confirmed'] for c in observers) or item.get('total_commands')!=item['protocol_commands']+8:
            raise ValueError('closure_cli_observer_count')
    expected = {'issue': 11, 'verify': 21, 'getUser': 5, 'refresh': 27, 'logout': 10, 'revoked_denial': 4}
    keys = {(x['role'], x['operation']) for x in auth}
    if len(auth) != 18 or keys != {(r, op) for r in ('a_member', 'a_trainer', 'b_member') for op in expected}:
        raise ValueError('closure_auth_matrix')
    if any(x['commands'] != expected[x['operation']] or any(s['temp_written'] for s in x['statements']) for x in auth):
        raise ValueError('closure_auth_load')
    if workflow['commands'] != 360 or workflow['verified_calls'] != 72 or any(s['temp_written'] for s in workflow['statements']):
        raise ValueError('closure_workflow_auth')
    native = sum(c['phase'] not in BOOTSTRAP for c in trace)
    managed = sum(x['commands'] for x in auth) + workflow['commands']
    total = native + 4 + 32 + managed + 1
    if total > allowance(run_id, purpose):
        raise ValueError('closure_budget')
    return {'run_id': run_id, 'purpose': purpose, 'native_before_close': native,
            'managed_auth': managed, 'preflight': 4, 'cli': 32, 'closing_commands': 1,
            'global_commands': total, 'confirmed': False}
