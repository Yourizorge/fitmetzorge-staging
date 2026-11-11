"""Independent replay of the eleven original Auth probes, not root admission.

Main first authenticates the same-source CI ZIP. This reader returns a byte-bound
semantic proof; Main/A must still join archive authority and root terminal proof
before issuing AUTH_FAILURE_COVERAGE_VERIFIED. No engine execution or DB access.
"""
import hashlib
import re
import uuid

import admission_case_archive as archive
import auth_failure as engine
from . import runtime_auth_failure_witness as witness

CASES = ('before_dispatch', 'create_lost_reply', 'partial_user', 'partial_session',
         'login_timeout', 'logout_timeout', 'admin_unknown', 'duplicate_request',
         'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup')
HTTP = ((), ('create', 'delete'), ('create', 'delete'), ('create', 'login', 'delete'),
        ('create', 'login', 'delete'), ('create', 'login', 'logout', 'delete'),
        ('create', 'login', 'delete'), ('create', 'login', 'delete'), ('create', 'login'),
        ('create', 'login'), ('create', 'login', 'delete'))
RETAINED = ('admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier')
LOST = dict(create_lost_reply='create', partial_session='login', login_timeout='login',
            logout_timeout='logout', admin_unknown='delete')
SESSION_PREFIX = {'partial_session', 'login_timeout', 'admin_unknown', 'duplicate_request',
                  'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup'}
ROUTES = {'create': ('POST', '/admin/users'), 'login': ('POST', '/token?grant_type=password'),
          'logout': ('POST', '/logout?scope=global'), 'delete': ('DELETE', '/admin/users/{subject}')}


def require(value, code):
    if not value:
        raise ValueError('auth_replay_' + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def replay(payloads, *, binding, expected_sources):
    """Consume original bytes from Main's accepted flat archive, never flags alone."""
    job_raw = payloads['auth-job-result.json']
    job = archive.object_json(job_raw)
    require(job['case_names'] == list(CASES), 'exact_case_names')
    require(all(job[k] == binding[v] for k, v in (
        ('source_commit', 'source_commit'), ('ci_run', 'ci_run'),
        ('candidate_sha256', 'candidate_sha'), ('parent_id', 'run_id'))), 'job_binding')
    sources = archive.object_json(payloads['candidate.json'])
    require(sources['sources'] == expected_sources and sources['sha256'] == binding['candidate_sha'],
            'same_source_manifest')
    originals = archive.verify(payloads, job['original_archive_ref'], job['original_refs'])
    def read(name):
        return archive.object_json(originals[name])
    def reference(ref):
        archive.record(originals[ref['path']], ref)
        return read(ref['path'])
    component = reference(job['component_ref'])
    require(component['preparation_run_id'] == binding['run_id']
            and tuple(r['case'] for r in component['cases']) == CASES
            and tuple(r['case'] for r in component['safety_reconciliations']) == RETAINED,
            'original_case_set')
    for name, digest in component['source_sha256'].items():
        require(digest == expected_sources['_offline/phase6e11/endchain_v1/' + name], 'engine_source')
    require(set(component['source_sha256']) == {'auth_failure.py', 'auth_failure_transport.py'}, 'engine_source_set')
    require(component['contract'] == engine.contract(dict.fromkeys(engine.OPERATIONS, 128))
            and component['retained_claims'] == list(RETAINED)
            and job['retained_claims'] == list(RETAINED), 'original_contract_or_claims')

    observed, witness_names = {}, []
    for name in sorted(originals):
        if not name.startswith('auth-failure-observer-private/'):
            continue
        row = read(name)
        require(row['kind'] == 'native-read' and row['additional_sql_commands'] == 0
                and row['query_text_read'] is False, 'witness_kind')
        key = (row['case'], row['scope'], row['key'])
        require(key not in observed and row['sequence'] == len(witness_names)
                and name.endswith('/%04d-native-read.json' % row['sequence']), 'witness_inventory')
        observed[key] = row
        witness_names.append(name)
    consumed, requests, actors, sessions = set(), {}, {}, {}
    native_total = managed_total = reserve_total = spent_total = 0
    case_ids = set()

    def observe(case, scope, key):
        identity = (case['case'], scope, key)
        require(identity not in consumed and identity in observed, 'read_missing_or_replayed')
        row = observed[identity]
        require(row['run_id'] == case['run_id'], 'read_owner')
        consumed.add(identity)
        return row['value']

    def ownership(case, value):
        name, run = case['case'], case['run_id']
        counts = value['counts']
        require(set(counts) == engine.SNAPSHOT_COUNTS and
                all(type(v) is int and v >= 0 for v in counts.values()), 'snapshot_counts')
        users, keys = value['users'], value['session_sha256']
        require(type(users) is list and len(users) == counts['users'] <= 1
                and type(keys) is list and len(keys) == counts['sessions'] <= 2
                and len(set(keys)) == len(keys), 'snapshot_cardinality')
        require(all(isinstance(k, str) and re.fullmatch('[a-f0-9]{64}', k) for k in keys), 'session_digest')
        email = 'fmz-af-' + uuid.uuid5(uuid.UUID(run), name).hex + '@example.invalid'
        marker = engine.digest(run + ':' + name)
        for user in users:
            require(set(user) == {'id_sha256', 'email_sha256', 'marker_sha256'}
                    and user['email_sha256'] == engine.digest(email)
                    and user['marker_sha256'] == engine.digest(marker), 'exact_owned_comparands')
            actor = user['id_sha256']
            require(isinstance(actor, str) and re.fullmatch('[a-f0-9]{64}', actor), 'actor_digest')
            require(name not in actors or actors[name] == actor, 'actor_changed')
            actors[name] = actor
        sessions.setdefault(name, set()).update(keys)
        require(len(sessions[name]) <= 2, 'historical_session_bounds')
        return counts

    def journal(case, scope):
        folder = 'auth_failure_' + binding['run_id'] + '/' + case['case']
        if scope == 'reconciliation': folder += '/safety-reconciliation'
        files = case['retained_journal']['files']
        require({n for n in originals if n.startswith(folder + '/') and '/' not in n[len(folder)+1:]}
                == {folder + '/' + name for name in files}, 'journal_inventory')
        for name, ref in files.items():
            require('/' not in name and '\\' not in name, 'journal_name')
            raw = originals[folder + '/' + name]
            require(sha(raw) == ref['sha256'] and len(raw) == ref['bytes']
                    and archive.object_json(raw) == ref['content'], 'journal_original')
        require(read(folder + '/result.json') == {k: v for k, v in case.items() if k != 'retained_journal'},
                'original_case_result')
        claim = read(folder + '/claim.json')
        require(claim['run_id'] == case['run_id'] and claim['case'] == case['case'], 'claim_owner')
        events = [read(folder + '/' + n) for n in sorted(files) if n.startswith('event-')]
        require([r['sequence'] for r in events] == list(range(len(events))), 'journal_sequences')
        before = [r for r in events if r['phase'] == 'before_dispatch']
        require(len({r['key'] for r in before}) == len(before), 'duplicate_dispatch')
        for row in before:
            op = row['key']
            expected = 128 if op in engine.OPERATIONS else 1
            require(type(row['units']) is int and row['units'] == expected, 'prepaid_units')
            if op in engine.OPERATIONS:
                identity = (sha(originals[folder + '/claim.json']),
                            sha(originals[folder + '/event-%03d.json' % row['sequence']]))
                require(identity not in requests, 'prepaid_reused')
                requests[identity] = (case, op, scope)
        return folder, claim, events, before

    def replay_reads(case, scope, events, before):
        snapshots, loads = {}, {}
        for event in before:
            key = event['key']
            if key in engine.OPERATIONS: continue
            value = observe(case, scope, key)
            if key.startswith('stats_'):
                witness.statistics(value)
                continue
            snapshots[key] = value
            counts = ownership(case, value)
            event_rows = [r for r in events if r['phase'] == 'snapshot' and r['key'] == key]
            require(len(event_rows) == 1 and event_rows[0]['counts'] == counts, 'snapshot_event')
        for operation in [r['key'] for r in before if r['key'] in engine.OPERATIONS]:
            a = observed[(case['case'], scope, 'stats_before_' + operation)]['value']
            z = observed[(case['case'], scope, 'stats_after_' + operation)]['value']
            measured = witness.managed_difference(a, z)
            matches = [r for r in events if r['phase'] == 'managed_observed' and r['key'] == operation]
            require(len(matches) == 1 and matches[0]['load'] == measured
                    and measured['commands'] <= 128 and matches[0]['within_prepaid'] is True,
                    'original_counter_difference')
            loads[operation] = measured['commands']
        return snapshots, loads

    for case, http in zip(component['cases'], HTTP):
        name = case['case']
        engine.binding(case['run_id'])
        require(case['run_id'] not in case_ids and case['run_id'] != binding['run_id'], 'fresh_case_uuid')
        case_ids.add(case['run_id'])
        require(case['evidence_kind'] == 'REAL_LOCAL_PG17_GOTRUE', 'actual_backend_not_unit_model')
        require(case['execution_status'] == 'NO_GO' and case['refunds'] == 0
                and case['retry'] is False and case['hosted_requests'] == 0
                and case['full_chain_admission'] is False and not case['journal_failures'], 'original_no_go')
        expected_primary = {'before_dispatch': 'auth_failure_stop_before_dispatch',
            'partial_user': 'auth_failure_stop_after_user', 'duplicate_request': 'auth_failure_duplicate_dispatch'}
        expected = expected_primary.get(name, 'auth_failure_http_unknown' if name in LOST and name != 'admin_unknown'
            else 'auth_failure_injected_' + name)
        require(case['primary_failure'] == expected, 'requested_failure_observed')
        folder, claim, events, before = journal(case, 'case')
        require(claim['released'] is False and claim['plan'] == component['contract'], 'claim_not_rewritten')
        actual_http = tuple(op for op in engine.OPERATIONS if op in {r['key'] for r in before})
        require(actual_http == http and case['http_dispatches'] == list(http), 'exact_http_program')
        require(all(r['key'] in engine.NATIVE_SLOTS or r['key'] in engine.OPERATIONS for r in before), 'native_program')
        snaps, loads = replay_reads(case, 'case', events, before)
        require(not any(snaps['preflight']['counts'].values()), 'fresh_owned_scope')
        prefix = snaps['prefix']['counts']
        require(prefix == case['prefix_counts'] and prefix['users'] == int(name != 'before_dispatch')
                and prefix['sessions'] == int(name in SESSION_PREFIX), 'actual_partial_prefix')
        require(loads == case['observed_managed_sql'], 'case_managed_total')
        native = len(before) - len(http)
        spent = sum(r['units'] for r in before)
        require(case['native_sql_dispatches'] == native and case['prepaid_consumed'] == spent
                and case['reserved'] == 524 and spent <= 524, 'case_numeric')
        for op in http:
            outcomes = [r for r in events if r['key'] == op and r['phase'] in ('confirmed', 'unknown')]
            require(len(outcomes) == 1, 'http_outcome')
            outcome = outcomes[0]
            if LOST.get(name) == op:
                require(outcome['phase'] == 'unknown' and outcome['terminal'] is True
                        and outcome['failure']['error_class'] == 'UnknownOutcome', 'injected_unknown_retained')
            else:
                require(outcome['phase'] == 'confirmed' and type(outcome['http_status']) is int
                        and 200 <= outcome['http_status'] < 300, 'http_confirmation')
        released = name not in RETAINED
        require(case['claim_released'] is released and case['cleanup']['confirmed'] is released,
                'retained_claim_not_promoted')
        require(case['mint_barrier'] is (name != 'missing_mint_barrier'), 'missing_barrier_retained')
        if released or name == 'admin_unknown':
            require(not any(snaps['final']['counts'].values()), 'scoped_final_absence')
        if name == 'admin_unknown':
            require(case['cleanup']['delete_confirmed'] is False, 'unknown_delete_not_acknowledged')
        if name == 'duplicate_cleanup':
            require(case['cleanup']['duplicate_blocked'] is True
                    and case['cleanup']['duplicate_zero_dispatch'] is True, 'duplicate_cleanup')
        native_total += native
        managed_total += sum(loads.values())
        reserve_total += 524
        spent_total += spent

    recon_native = recon_http = recon_spent = 0
    for case in component['safety_reconciliations']:
        name = case['case']
        original = next(r for r in component['cases'] if r['case'] == name)
        folder, claim, events, before = journal(case, 'reconciliation')
        original_path = folder.removesuffix('/safety-reconciliation') + '/result.json'
        require(case['run_id'] == original['run_id'] and claim['original_result_sha256'] == sha(originals[original_path])
                and case['original_result_sha256'] == sha(originals[original_path])
                and case['original_result_unchanged'] is True and case['original_claim_released'] is False,
                'original_unknown_preserved')
        snaps, loads = replay_reads(case, 'reconciliation', events, before)
        keys = [r['key'] for r in before]
        expected = ['observe', 'stats_before_delete', 'delete', 'stats_after_delete', 'verify_zero'] \
            if name == 'cleanup_interrupted' else ['observe']
        require(keys == expected, 'reconciliation_no_replay')
        count = len(keys) - int('delete' in keys)
        spent = sum(r['units'] for r in before)
        require(case['native_sql_dispatches'] == count and case['http_dispatches'] == int('delete' in keys)
                and case['prepaid_consumed'] == spent
                and case['combined_prepaid_consumed'] == original['prepaid_consumed'] + spent <= 524
                and case['refunds'] == 0, 'reconciliation_same_reserve')
        if name == 'cleanup_interrupted':
            require(case['status'] == 'LOCAL_SCOPED_RECONCILIATION_CONFIRMED'
                    and case['delete_confirmed'] is True and case['reconciliation_confirmed'] is True
                    and not any(snaps['verify_zero']['counts'].values()), 'reconciliation_absence')
        else:
            require(case['status'] == 'BLOCKED' and case['delete_confirmed'] is False
                    and case['reconciliation_confirmed'] is False, 'unknown_not_promoted')
        recon_native += count
        recon_http += int('delete' in keys)
        recon_spent += spent
    require(consumed == set(observed), 'complete_native_witness_inventory')

    registry = [read(n) for n in sorted(originals) if n.startswith('auth-failure-request-private/')]
    require([r['sequence'] for r in registry] == list(range(len(registry)))
            and registry[0]['kind'] == 'registry' and registry[0]['run_id'] == binding['run_id'], 'registry_sequence')
    admitted = [r for r in registry if r['kind'] == 'admitted']
    completed = [r for r in registry if r['kind'] == 'completed']
    require(len(admitted) == len(completed) == len(requests) == 28, 'tracked_request_count')
    seen = set()
    for ordinal, (start, end) in enumerate(zip(admitted, completed)):
        reservation = start['reservation']
        identity = (reservation['claim_sha256'], reservation['event_sha256'])
        require(identity in requests and identity not in seen, 'original_precharge_link')
        seen.add(identity)
        case, op, scope = requests[identity]
        require(start['request_id'] == end['request_id'] == ordinal
                and start['owner_sha256'] == engine.digest(case['run_id'])
                and (start['method'], start['route']) == ROUTES[op]
                and reservation['units'] == 128 and end['terminal'] is True
                and type(end['delivery_confirmed']) is bool
                and end['delivery_confirmed'] is not (scope == 'case' and LOST.get(case['case']) == op),
                'actual_tracked_request')
    require([r['kind'] for r in registry] == ['registry'] + ['admitted', 'completed'] * 28 + ['closing', 'closed'],
            'tracked_program_order')
    close = registry[-1]
    require(close['admitted_requests'] == 28 and close['active_requests'] == 0
            and close['all_registered_upstream_terminal'] is True
            and close['future_regular_dispatch_denied'] is True
            and close['server_writers_quiescent_proven'] is False, 'actual_registered_close')
    totals = component['diagnostic_totals']
    require(totals['native_sql_dispatched'] == native_total == 95
            and totals['http_dispatched'] == 27 and totals['reserved'] == reserve_total == 5764
            and totals['prepaid_consumed'] == spent_total
            and totals['observed_managed_sql'] == managed_total, 'original_component_totals')
    require(component['reconciliation_diagnostic_totals']['native_sql_dispatches'] == recon_native == 6
            and component['reconciliation_diagnostic_totals']['http_dispatches'] == recon_http == 1
            and component['reconciliation_diagnostic_totals']['prepaid_consumed'] == recon_spent,
            'original_reconciliation_totals')
    return {'status': 'AUTH_FAILURE_PROBE_SEMANTICS_VERIFIED', 'case_names': list(CASES),
        'binding': dict(binding), 'job_sha256': sha(job_raw),
        'source_manifest_sha256': sha(payloads['candidate.json']),
        'original_index_ref': job['original_archive_ref'], 'original_refs': job['original_refs'],
        'native_sql_commands': native_total + recon_native, 'http_dispatches': len(requests),
        'declared_local_capacity': reserve_total, 'retained_claims': list(RETAINED),
        'independent_root_terminal_verified': False,
        'required_coverage_joins': ['authenticated_same_source_archive', 'independent_root_terminal'],
        'full_auth_cleanup_proven': False, 'full_chain_admission': False, 'hosted_admitted': False}
