"""Retain already-read technical witnesses, without new SQL or HTTP requests."""
import copy
import math
import pathlib
import re
import uuid

import auth_failure as engine
import auth_failure_tracked as tracked
import auth_protocol


def require(value, code):
    if not value:
        raise ValueError('auth_witness_' + code)


def statistics(value):
    require(type(value) is dict and set(value) ==
            {'reset', 'dealloc', 'track_utility', 'statements'}, 'stats_shape')
    require(type(value['dealloc']) is int and value['dealloc'] >= 0
            and value['track_utility'] == 'on'
            and type(value['statements']) is list and len(value['statements']) <= 1024,
            'stats_bounds')
    def timestamp(item):
        return isinstance(item, str) and len(item) <= 128 and re.fullmatch(r'[0-9Tt:.+ Z-]+', item)
    require(timestamp(value['reset']), 'reset_timestamp')
    seen = set()
    for row in value['statements']:
        require(type(row) is dict and set(row) ==
                {'queryid', 'calls', 'since', 'temp_written', 'temp_read', 'wal_bytes', 'exec_ms'},
                'stats_row')
        require(isinstance(row['queryid'], str) and re.fullmatch(r'-?[0-9]{1,20}', row['queryid'])
                and row['queryid'] not in seen and timestamp(row['since']), 'stats_identity')
        seen.add(row['queryid'])
        require(all(type(row[k]) is int and row[k] >= 0 for k in ('calls', 'temp_written', 'temp_read'))
                and isinstance(row['wal_bytes'], str) and re.fullmatch(r'[0-9]+', row['wal_bytes'])
                and type(row['exec_ms']) in (int, float) and math.isfinite(row['exec_ms'])
                and row['exec_ms'] >= 0, 'stats_numeric')
    return copy.deepcopy(value)


def snapshot(value):
    engine.validate_snapshot(value)
    require(set(value) == {'users', 'session_ids', 'counts'}, 'snapshot_shape')
    users = []
    for user in value['users']:
        require(type(user) is dict and set(user) == {'id', 'email', 'marker'}
                and all(isinstance(user[k], str) for k in user), 'snapshot_user_shape')
        require(str(uuid.UUID(user['id'])) == user['id'], 'snapshot_uuid')
        users.append({k + '_sha256': engine.digest(v) for k, v in user.items()})
    return {'users': users, 'session_sha256': sorted(engine.digest(v) for v in value['session_ids']),
            'counts': copy.deepcopy(value['counts'])}


class Witnesses:
    def __init__(self, out):
        self.records = tracked.Records(pathlib.Path(out) / 'auth-failure-observer-private')
        self.seen = set()

    def record(self, run_id, case, scope, key, value):
        engine.binding(run_id)
        require(case in engine.CASES and scope in ('case', 'reconciliation'), 'case_scope')
        identity = (run_id, case, scope, key)
        require(identity not in self.seen, 'read_replay')
        native = engine.NATIVE_SLOTS if scope == 'case' else (
            'observe', 'stats_before_delete', 'stats_after_delete', 'verify_zero')
        require(key in native, 'unregistered_read')
        kind = 'statistics' if key.startswith('stats_') else 'snapshot'
        projected = statistics(value) if kind == 'statistics' else snapshot(value)
        self.records.save('native-read', {'run_id': run_id, 'case': case, 'scope': scope,
            'key': key, 'observation_kind': kind, 'value': projected,
            'additional_sql_commands': 0, 'query_text_read': False})
        self.seen.add(identity)


def managed_difference(before, after):
    return auth_protocol.difference(statistics(before), statistics(after))
