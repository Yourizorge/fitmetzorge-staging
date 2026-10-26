"""Pure disposable app-CI contracts; no execution or endchain capacity grant."""
import pathlib

PROFILE = 'local_app'
CANONICAL_COUNT = 45
QUOTA = '20261018070231_phase6e11_recovery_run_quota.sql'
M45 = '20261014105919_phase6e_synthetic_server_candidate.sql'
M46 = '20261014160019_phase6e_local_outbox.sql'
SLOTS = ('app_schema', 'minimal_dry_run', 'app_outbox', 'final_dry_run')
APPLY = ('db', 'push', '--local', '--skip-vault', '--yes', '--include-all')
DRY = ('db', 'push', '--local', '--dry-run', '--skip-vault')


def canonical(files):
    paths = sorted(p for p in files if p.startswith('supabase/migrations/'))
    versions = [pathlib.PurePosixPath(p).name.split('_')[0] for p in paths]
    if len(paths) != CANONICAL_COUNT or len(set(versions)) != CANONICAL_COUNT or \
       pathlib.PurePosixPath(paths[-1]).name != QUOTA:
        raise ValueError('app_canonical_45_required')
    return paths


def history_contract(history, files, stage):
    paths = canonical(files)
    if stage not in ('canonical', 'minimal', 'complete'):
        raise ValueError('app_history_stage')
    added = [] if stage == 'canonical' else [M45] if stage == 'minimal' else [M45, M46]
    versions = sorted([pathlib.PurePosixPath(p).name.split('_')[0] for p in paths] +
                      [p.split('_')[0] for p in added])
    if [r.get('version') for r in history] != versions:
        raise ValueError('app_history_identity_' + stage)
    return {'profile': PROFILE, 'stage': stage, 'canonical_count': CANONICAL_COUNT,
            'app_migrations': added, 'count': len(versions), 'sorted_last': versions[-1],
            'hosted_applied': False}


def cli_arguments(args, phase, index):
    if index not in range(len(SLOTS)):
        raise ValueError('app_cli_invocation_count')
    expected_phase = ('local_app_schema', 'local_app_schema', 'local_app_outbox',
                      'advisors_and_dryrun')[index]
    request = ('migration', 'up', '--local') if index in (0, 2) else DRY
    if tuple(args) != request or phase != expected_phase:
        raise ValueError('app_cli_sequence')
    return APPLY if index in (0, 2) else DRY


def cli_receipt(receipt, index):
    if index not in range(len(SLOTS)):
        raise ValueError('app_cli_invocation_count')
    expected = APPLY if index in (0, 2) else DRY
    commands = receipt.get('commands', [])
    observers = receipt.get('observer_commands', [])
    if receipt.get('profile') != PROFILE or receipt.get('complete') is not True or \
       receipt.get('numeric_protocol_coverage') is not True or receipt.get('exitcode') != 0 or \
       receipt.get('arguments') != list(expected) or receipt.get('dry_run') is not (index in (1, 3)) or \
       not commands or receipt.get('protocol_commands') != len(commands) or \
       len(observers) != 8 or not all(x.get('confirmed') is True and x.get('protocol_commands') == 1 for x in observers):
        raise ValueError('app_cli_evidence')
    if any(k in receipt for k in ('capacity_reserved', 'charged_commands')) or \
       receipt.get('slot') in ('quota', 'pre_auth', 'final'):
        raise ValueError('app_cli_endchain_capacity')
    if receipt.get('slot') != 'app_' + str(index):
        raise ValueError('app_cli_slot')
    return {'index': index, 'step': SLOTS[index], 'protocol_commands': len(commands),
            'observer_commands': len(observers), 'profile': PROFILE}
