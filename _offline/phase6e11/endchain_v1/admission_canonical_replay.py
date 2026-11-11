"""Replay canonical originals without executing SQL, CLI, or artifact code.

Correlation is deliberately narrower than attribution. Raw numeric samples and
prepaid frames can close that check without proving a driver or WAL bound.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace

import admission_budget_prefix_originals as audit

PREFIX = '_offline/phase6e11/endchain_v1/'
SELF = PREFIX+'admission_canonical_replay.py'
ISOLATION = '_offline/phase6e_server_v1/cli_isolation.py'
ISOLATION_SHA = '93fe1c9a72abd88bc033cfaab03cead8232ada0ff68ccf5342ea2372eb1f114a'


def need(value, reason):
    if not value:
        raise ValueError('canonical_replay_'+reason)


def same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sample(value):
    need(type(value) is dict and set(value) ==
         {'reset','dealloc','track_utility','track','statements'}, 'sample_shape')
    need(type(value['reset']) is str and value['reset'] and type(value['dealloc']) is int
         and value['dealloc'] >= 0 and value['track'] in ('all','top')
         and value['track_utility'] == 'on', 'sample_tracking')
    rows = value['statements']
    need(type(rows) is list and len(rows) <= 10000, 'sample_rows')
    seen = set()
    for row in rows:
        need(type(row) is dict and set(row) ==
             {'queryid','calls','since','temp_written','wal'}, 'sample_row')
        qid = row['queryid']
        need(type(qid) is str and re.fullmatch('-?(0|[1-9][0-9]*)', qid)
             and -(2**63) <= int(qid) < 2**63 and str(int(qid)) == qid
             and qid not in seen, 'sample_queryid')
        seen.add(qid)
        need(type(row['since']) is str and row['since']
             and all(type(row[k]) is int and row[k] >= 0 for k in ('calls','temp_written'))
             and type(row['wal']) is str and re.fullmatch('0|[1-9][0-9]*', row['wal']),
             'sample_counter')


def ledger_shape(raw):
    """Strengthen the existing producer replay before its permissive JSON load."""
    need(0 < len(raw) <= 2_000_000 and raw.endswith(b'\n'), 'ledger_size')
    rows = [json.loads(line, object_pairs_hook=audit.prefix._pairs,
             parse_constant=lambda _: need(False,'ledger_nonfinite')) for line in raw.splitlines()]
    need(len(rows) <= 20000, 'ledger_rows')
    allowed = {'preregister','connect_attempt','dispatch','outcome','frontend_frame',
               'frontend_write_returned','history_bind','history_snapshot','terminal'}
    dispatched, framed, confirmed = {}, set(), set()
    connected = False
    for i, row in enumerate(rows, 1):
        need(type(row) is dict and row.get('event') in allowed
             and type(row.get('sequence')) is int and row['sequence'] == i, 'ledger_event')
        event = row['event']
        if event == 'connect_attempt':
            need(not connected and type(row.get('id')) is int and row['id'] == 1, 'connect_order')
            connected = True
        if event == 'dispatch':
            ident = row.get('id')
            need(connected and type(ident) is int and ident == len(dispatched)+1
                 and row.get('protocol') in ('simple','extended'), 'dispatch_order')
            dispatched[ident] = row
        if event == 'frontend_frame':
            ids = row.get('sql_ids')
            need(type(ids) is list and len(ids) == len(set(ids)), 'frame_ids')
            for ident in ids:
                need(type(ident) is int and ident in dispatched and ident not in framed,
                     'unpaid_or_duplicate_frame')
                need(row.get('type') == ('Q' if dispatched[ident]['protocol'] == 'simple' else 'E'),
                     'frame_protocol')
                framed.add(ident)
        if event == 'outcome':
            ident = row.get('id')
            need(type(ident) is int and ident in framed and ident not in confirmed, 'confirmation_order')
            confirmed.add(ident)
    need(set(dispatched) == framed == confirmed, 'unconfirmed_dispatch_consumed')
    return rows


def numeric(receipt, stat):
    before, after = receipt['numeric_before'], receipt['numeric_after']
    sample(before)
    sample(after)
    need(before['track'] == after['track'], 'tracking_changed')
    old = {r['queryid']:r for r in before['statements']}
    for row in after['statements']:
        prior = old.get(row['queryid'], dict(calls=0,temp_written=0,wal='0'))
        need(row['calls'] != prior['calls'] or
             (row['temp_written'] == prior['temp_written'] and row['wal'] == prior['wal']),
             'unattributed_counter_change')
    commands = receipt['terminal']['sql_dispatches']
    need(type(commands) is int and commands > 0, 'dispatch_count')
    computed = stat.compare(before, after, commands, between=3)
    need(same(computed, receipt['numeric_coverage']) and computed['all_protocol_visible'] is True
         and computed['temp_written'] == 0, 'numeric_coverage')
    # The observer SQL is a single source literal, not caller-supplied SQL.
    hashes = [sha(s.encode()) for s in ('BEGIN TRANSACTION READ ONLY',
        "select current_setting('transaction_read_only')='on' readonly", stat.SQL.strip(), 'ROLLBACK')]
    expected = [dict(sha256=h, kind='numeric_observer', protocol_commands=1, confirmed=True)
                for h in hashes]*2
    need(same(receipt.get('observer_trace'), expected)
         and type(receipt.get('observer_commands')) is int and receipt['observer_commands'] == 8
         and receipt.get('after_measurement_complete') is True, 'observer_trace')
    return computed


def isolation(receipt, value):
    original = value.get('original')
    need(original in ('on','off') and value.get('restored') is True
         and value.get('primary_error_class') is None, 'isolation_state')
    setting = "select current_setting('cron.launch_active_jobs') setting"
    sql = [setting]
    if original == 'on':
        sql += ["alter system set cron.launch_active_jobs='off'", 'select pg_reload_conf()']
    sql += [setting, "select count(*) n from pg_stat_activity where application_name='pg_cron' and state='active'"]
    if original == 'on':
        sql += ["alter system set cron.launch_active_jobs='on'", 'select pg_reload_conf()']
    sql += [setting]
    expected = [dict(statement_sha256=sha(s.encode()), confirmed=True) for s in sql]
    need(same(value.get('protocol'), expected) and type(value.get('commands')) is int
         and value['commands'] == len(sql) == receipt.get('ci_bootstrap_sql_commands')
         and receipt.get('ci_cron_restored') is True, 'isolation_trace')
    return len(sql)


def replay(evidence, trusted, binding):
    summary = evidence.obj(audit.NAME)
    candidate = evidence.obj('candidate.json')
    need(all(trusted.sources.get(name) == digest for name,digest in candidate['sources'].items()),
         'external_candidate_sources')
    need(sha(trusted.raw(ISOLATION)) == ISOLATION_SHA, 'isolation_source_changed')
    # Reuse all prior cross-case, catalog, provision and transitive ref checks.
    with tempfile.TemporaryDirectory(prefix='canonical-originals-') as temp:
        out = Path(temp)
        names = {audit.NAME, 'candidate.json', 'case-stack-catalog-before41-intent.json'}
        names.update(ref['path'] for row in summary['invocations'] for ref in row['original_refs'].values())
        names.add(summary['catalog_before41_ref']['path'])
        names.update(ref['path'] for ref in summary['catalog_original_refs'].values())
        names.update(ref['path'] for ref in summary['history_provision_refs'])
        for name in sorted(names):
            raw = evidence.raw(name)
            path = out/name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
        gate = SimpleNamespace(out=out, sources=trusted.root, result=dict(
            commit=binding['source_commit'], run_id=binding['ci_run'], candidate_sha256=binding['candidate_sha']))
        originals = audit.inspect_canonical_prefix(gate, binding=binding)
        # Legacy loader is admitted only by the surrounding exact-source child.
        pending_path = PREFIX+'cli_predispatch/pending.py'
        trusted.raw(pending_path)
        spec = importlib.util.spec_from_file_location('canonical_original_pending', trusted.root/pending_path)
        pending = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pending)
        stat = trusted.module('cli_stat_reader')
        output = []
        for row in summary['invocations']:
            refs = row['original_refs']
            receipt = evidence.obj(refs['receipt']['path'], refs['receipt'])
            policy = evidence.obj(refs['policy']['path'], refs['policy'])
            raw = evidence.raw(refs['ledger']['path'], refs['ledger'])
            ledger_shape(raw)
            replayed = pending.common.replay(out/refs['ledger']['path'], prefix_policy=policy)
            for key in ('header','terminal','events','terminal_recorded','journal_sha256','event_count'):
                need(same(receipt.get(key), replayed[key]), 'ledger_summary_substitution')
            pending.prove_execution(replayed, policy)
            need(type(receipt.get('cli_exit_code')) is int and receipt['cli_exit_code'] == 0, 'cli_exit')
            expected_history = [Path(v['migration_path']).name.split('_',1)[0]
                                for v in summary['invocations'][:row['ordinal']-1]]
            need(policy['expected_history_versions'] == expected_history, 'history_order')
            computed = numeric(receipt, stat)
            count = isolation(receipt, evidence.obj(refs['isolation']['path'], refs['isolation']))
            output.append(dict(ordinal=row['ordinal'], invocation_id=row['invocation_id'],
                migration_sha256=row['migration_sha256'], ledger_sha256=sha(raw),
                protocol_dispatches=computed['protocol_commands'], observer_commands=8,
                isolation_explicit_commands=count, unknown_consumed=0,
                top_level_correlation_replayed=True, driver_sql_bound=None))
    return dict(status='CANONICAL_ORIGINAL_CORRELATION_REPLAYED_UNVERIFIED',
        invocations=output, invocation_count=44, original_ref_closure=originals,
        known_explicit_commands=8+sum(r['protocol_dispatches']+8+r['isolation_explicit_commands'] for r in output),
        domain='local_ci_bootstrap', hosted_equivalent_commands=None,
        hosted_projection='not_applicable_local_clean_stack_creation', total_sql_commands=None,
        missing=['canonical_independent_JS_AST_derivation','canonical_driver_numeric_partitions',
                 'canonical_isolation_raw_results','canonical_auxiliary_driver_partitions',
                 'canonical_WAL_interval_attribution'],
        full_chain_admission=False, hosted_admitted=False)
