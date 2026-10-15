"""Conservative full-chain rebudget from immutable integral CI, not admission.

Every old protocol/action/writeset and every cleanup prefix remains represented.
CLI envelopes replace claimed session attribution. No SQL or run is executed.
"""
import collections, copy, hashlib, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'endchain_v1'))
from complete_register import reserve_prefixes
from hosted_gate import disk

RUN = '4b0bb35f-02b5-4a9d-92d7-c29995691460'
APPROVED = 2237
ARCHIVE = HERE.parent / 'endchain_v1/receipts/reserved-ci-38753289792'


def build(old, cli_cap=64):
    if old.get('normal_capacity') != 2226 or old.get('worst_including_safety') != 2237:
        raise ValueError('historical_register_changed')
    if type(cli_cap) is not int or cli_cap < 14:
        raise ValueError('cli_reservation_not_supported')
    rows = copy.deepcopy(old['rows'])
    if len(rows) != 2226 or any(r['sql'] != 1 for r in rows):
        raise ValueError('historical_register_not_complete')
    # These historical actions include eight native observer commands each.
    groups = [('candidate_44_migration_aware_cli', 'migration', 14),
              ('empty_cli_dry_run', 'final', 2)]
    envelopes = []
    for action, phase, previous in groups:
        indices = [i for i, row in enumerate(rows) if row['action'] == action]
        if len(indices) != previous + 8:
            raise ValueError('historical_cli_group_changed')
        for index in indices:
            rows[index]['historical_only'] = True
            rows[index]['new_execution_classification'] = 'NATIVE_OBSERVER_OR_CLI_CAPACITY_NOT_HOSTED_ACTUAL'
        extra = []
        for n in range(cli_cap - previous):
            extra.append(dict(id='unassigned', phase=phase, action='cli_unattributed_capacity',
                              sql=1, ordinal_in_action=n, retry=False, writeset=[],
                              reservation_only=True, observed_commands=None,
                              stop='NO_GO if the numeric unknown upper bound exceeds the envelope'))
        rows[indices[-1]+1:indices[-1]+1] = extra
        envelopes.append(dict(action=action, cli_reserved=cli_cap, native_observers=8,
                              old_cli_claim=previous, observed_cli_commands=None,
                              maximum_charged=cli_cap+8, no_refund_on_incomplete_metadata=True))
    for i, row in enumerate(rows):
        row['id'] = 'cmd_' + str(i+1).zfill(5)
    prefixes = reserve_prefixes(rows)
    normal = sum(r['sql'] for r in rows)
    worst = max(p['required_total'] for p in prefixes)
    return dict(run_id=RUN, approved_limit=APPROVED, normal_capacity=normal,
                worst_including_safety=worst, extra_above_limit=max(0,worst-APPROVED),
                phase_budgets=dict(collections.Counter(r['phase'] for r in rows)),
                fits_current_limit=worst <= APPROVED, cli_envelopes=envelopes,
                rows=rows, prefixes=prefixes,
                original_rows_preserved=2226, historical_source_bundle_sha=old['source_bundle_sha'],
                scope='OFFLINE CONSERVATIVE MODEL; NOT NEW INTEGRAL CI OR HOSTED ADMISSION',
                attribution='Reservations are not actual execution; all unassigned numeric activity remains UNKNOWN',
                migration_state='M44 exact/installed; never reapply; new UUID currently has database cap128',
                remaining_source_work=['Exact forward-only new-run quota binding and its CLI cost proof',
                    'New integral Auth/controller/A/B/cleanup CI for pending and already-present migration branches',
                    'Bind this conservative register to the new runtime meter before any hosted mutation'],
                no_budget_increase_applied=True, hosted_admitted=False, attempt_consumed=False)


def historical():
    manifest = json.loads(disk(ARCHIVE/'MANIFEST.json').read_bytes())
    def read(name):
        raw = disk(ARCHIVE/name).read_bytes()
        if manifest['files'][name] != hashlib.sha256(raw).hexdigest():
            raise ValueError('historical_manifest')
        return json.loads(raw)
    result = read('complete-command-register.json')
    rows = [row for phase in result['phase_budgets'] for row in read('register-phase-'+phase+'.json')['rows']]
    result['rows'] = sorted(rows, key=lambda r:r['id'])
    if [r['id'] for r in result['rows']] != ['cmd_'+str(i+1).zfill(5) for i in range(len(rows))]:
        raise ValueError('historical_row_sequence')
    return result


if __name__ == '__main__':
    result = build(historical())
    if len(sys.argv) == 2:
        target = pathlib.Path(sys.argv[1]).resolve()
        if not target.is_relative_to(ROOT/'supabase/.temp'):
            raise ValueError('output_scope')
        with disk(target).open('xb') as output:
            output.write((json.dumps(result, sort_keys=True, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','prefixes')},indent=2))
