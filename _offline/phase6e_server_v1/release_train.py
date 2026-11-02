"""Read-only package12-20 compiler/checker. Never executes or admits a release.

CI integration: add this module and its test to ci.NEW; union input_files(ROOT)
into ci.EXTRA. After unit checks, build/verify against Gate.sources and save the
returned document as release-train.json. The generated JSON is never an input.
"""
import argparse
import copy
import json
import pathlib
import sys

import ci_profile
from release_selection import FORBIDDEN, SLICES, selection_allows
from workday_release import closure, commands, digest, permissions, raw, safe_file, writeset

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = '_offline/phase6e_server_v1/'
FORMAT = 'fmz-release-train-v1'
OFFLINE = 'COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY'
OWNER_BASE = '9715ac8600bad89ff813ad399e745360028ce48a'
HISTORY = PREFIX + 'receipts/ci-40354972820/'
HISTORY_COMMIT = '06b9ac0ad961705a3f7fc8de2fb80d3cf82637a4'
HISTORY_CANDIDATE = '93a6798a0e55156ed0a14d13021cd3976fce540a3f701b4535e0023188849829'
FREEZE_PINS = {
    12: '05b712a515a785d52c89ca9dd2318e0fc427c1f4a460862726bacc4fb648144e',
    13: '3230b98f35d0754e3393b213aaa9788d6bf544ef262e0770f5027fa1d0c3582e',
    14: '1eccab5b53af0673e86ad2f85e2f2712586d7652d772eafb1e27780d774fa697',
    15: '5301900decb6245c7d5f9881b5ee9a9f1eda3f476924902f2312897a8d296563',
    16: '3175e466181790f160c3cc4cff711c236ef78dc5e778e0673dac11500bcd84c8',
    17: '24e076c162021ed349c279ae06311ed84b29c61385078f9645a20a66a9bb8c17',
    18: 'ed4bae49a3874cc9fbdc8dea2fb11843614891406d3cfdabd28797d5b5853a68',
    19: 'f59dc5874e03d45e29f174f767ea82c3a233dae43cfc1d54c393781c6494fa11',
    20: '6b53f7b37695bfc62ce7117656ecde18e812b5e859c77efa1e8d2c3a19283b11',
}
HISTORY_PINS = {
    'artifact-manifest.json': 'a0ec129339d9ebc886ed88fd037e05da6f686d921a56daabfff6fe7f1be232a8',
    'candidate.json': 'c617aafedebebb428b52163bc651a9e0f2a394b885ee4268d673c9acee6ff1a9',
    'collection.json': '763bfa5d8c82c2013a776940d491c3bf4f65eba22a49a2707dc377050598773a',
    'result.json': '1e6a6e5ed9dd11a17c7e073711de52fc7fed6207dda9e2eeb634c712f610a25c',
    'loaded-source-preflight.json': '4cc91fec55eaf10c05d3957f46b778ed68736c1fd11ad79422f0c683f4ed54ad',
    'loaded-source-final.json': '4cc91fec55eaf10c05d3957f46b778ed68736c1fd11ad79422f0c683f4ed54ad',
}
# Conservative release sequencing from PHASE6E_WORKDAY_RELEASE_ORDER, not a
# claim that independently frozen demos have numeric runtime dependencies.
PLAN = (
    (12, 'Historical registration/reflection', 'registration12', ()),
    (13, 'Source-bound comparison', 'signals13_14', (12,)),
    (14, 'Signal proposal and source correction', 'signals13_14', (13,)),
    (15, 'Route B intake', 'intake15', (14,)),
    (16, 'Training plan editing', 'plans16_17', (15,)),
    (17, 'Nutrition plan editing', 'plans16_17', (16,)),
    (18, 'Joint review and separate apply', 'review18', (16, 17)),
    (19, 'Recovery and check-in', 'recovery19_today20', (18,)),
    (20, 'Today integration', 'recovery19_today20', (19,)),
)
COMMON = (
    'server.py', 'worker.cjs', 'protocol.py', 'store.py', 'registration_store.py',
    'composed_store.py', 'release_selection.py', 'release_selection_http.py',
    'release_matrix.py', 'ui.html', 'ui.js', 'ui.css', 'panels.js', 'display.js',
    'draft_queue.js', 'queue_ui.js', 'sync_contract.cjs', 'account_center.cjs',
    'account_center.test.cjs', 'account_center_browser.cjs',
    'offline_shell.test.cjs', 'offline_shell_browser.cjs', 'offline_queue_ui.test.cjs',
    'draft_queue.test.cjs', 'ui_session.test.cjs',
)
TOOLING = ('release_train.py', 'test_release_train.py', 'ci.py', 'ci_profile.py',
           'workday_release.py', 'registration_scope.py')
RELEASE_BLOCKERS = (
    'fresh_same_source_composed_endchain_and_app_ci_not_attested_here',
    'complete_hosted_6e11_and_required_review_not_attested_here',
    'selected_release_owner_review_and_authorization_not_attested_here',
    'selected_hosted_migration_identity_and_dry_run_not_attested_here',
    'selected_measured_register_prefix_reserve_cleanup_not_attested_here',
)


def canonical_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True).encode())


def file_hash(root, name):
    return digest(raw(safe_file(root, name)))


def read_json(root, name):
    return json.loads(raw(safe_file(root, name)).decode('utf-8-sig'))


def pinned(root, name, expected):
    actual = file_hash(root, name)
    if actual != expected:
        raise ValueError('pinned_source_drift:' + name)
    return actual


def validate_plan(plan=PLAN):
    seen = set()
    known = {spec['id'] for spec in SLICES}
    for number, title, selected, dependencies in plan:
        if type(number) is not int or number in seen or selected not in known or not title:
            raise ValueError('release_plan')
        if any(type(n) is not int or n not in seen for n in dependencies):
            raise ValueError('dependency_order')
        seen.add(number)
    if seen != set(range(12, 21)):
        raise ValueError('packages_12_through_20_only')


def frozen(root, number):
    evidence = f'docs/PHASE6E{number}_FREEZE_EVIDENCE.json'
    files = {evidence: pinned(root, evidence, FREEZE_PINS[number])}
    receipt = read_json(root, evidence)
    if receipt['package'] != f'6E-{number}' or receipt['status'] != OFFLINE or not receipt['sources']:
        raise ValueError('frozen_contract')
    for source in receipt['sources']:
        name = source['file']
        if name in files:
            raise ValueError('duplicate_frozen_source')
        files[name] = pinned(root, name, source['working_sha256'])
    reports = dict(receipt.get('reports', {}))
    for key in ('technical_evidence_sha256', 'evidence_sha256'):
        if key in receipt:
            reports[f'docs/PHASE6E{number}_EVIDENCE.json'] = receipt[key]
    if 'publication_receipt_sha256' in receipt:
        reports[f'docs/PHASE6E{number}_PUBLICATION_RECEIPT.md'] = receipt['publication_receipt_sha256']
    for name, expected in reports.items():
        files[name] = pinned(root, name, expected)
    name = f'docs/PHASE6E{number}_FREEZE_RECEIPT.md'
    files[name] = file_hash(root, name)
    return {'status': OFFLINE, 'accepted_on': receipt['accepted_on'],
            'live_acceptance': False, 'sources': dict(sorted(files.items())),
            'source_bundle_sha256': canonical_hash(files)}


def historical(root):
    files = {HISTORY + n: pinned(root, HISTORY + n, h) for n, h in HISTORY_PINS.items()}
    manifest = read_json(root, HISTORY + 'artifact-manifest.json')
    for name in HISTORY_PINS.keys() - {'artifact-manifest.json', 'collection.json'}:
        if manifest.get(name) != files[HISTORY + name]:
            raise ValueError('historical_artifact_binding')
    result = read_json(root, HISTORY + 'result.json')
    collection = read_json(root, HISTORY + 'collection.json')
    candidate = read_json(root, HISTORY + 'candidate.json')
    if (result['status'] != 'CLEAN_CI_PASS' or result['commit'] != HISTORY_COMMIT
            or result['candidate_sha256'] != HISTORY_CANDIDATE
            or candidate['sha256'] != HISTORY_CANDIDATE or collection['verified'] is not True):
        raise ValueError('historical_ci_identity')
    return {
        'status': 'HISTORICAL_REAL_APP_CI_ONLY', 'run_id': result['run_id'],
        'commit': HISTORY_COMMIT, 'candidate_sha256': HISTORY_CANDIDATE,
        'archive_sha256_recorded': collection['archive_sha256'],
        'archive_reverified_here': False, 'selected_receipts_hash_verified': True,
        'source_hashes': files, 'candidate_sources': candidate['sources'],
        'selected_release_slices': result['selected_release_slices'],
        'selected_release_checks': result['selected_release_checks'],
        'fresh_full_ci_claimed': False, 'hosted_admission': False,
    }


def slice_contract(root, spec, historic_sources, shared_sources):
    selected = spec['id']
    primary = spec['adapter'] == 'Store'
    needs_outbox = primary or selected == 'workout12'
    sources = dict(shared_sources)
    migrations = [PREFIX + 'supabase/migrations/' + ci_profile.M45]
    if needs_outbox:
        migrations.append(PREFIX + 'supabase/migrations/' + ci_profile.M46)
    for name in migrations:
        sources[name] = file_hash(root, name)
    for action in FORBIDDEN:
        for role in ('member', 'trainer', 'owner'):
            for route in ('A', 'B'):
                if selection_allows(spec, action, role, route):
                    raise ValueError('package21_action_exposed')
    return {
        'id': selected, 'adapter': spec['adapter'], 'entry_files': [PREFIX + n for n in spec['entries']],
        'source_hashes': dict(sorted(sources.items())), 'source_bundle_sha256': canonical_hash(sources),
        'source_scope': 'Shared selected-app runtime/test closure. Loaded code is not an action grant.',
        'historical_exact_byte_mismatches': sorted(n for n, h in sources.items()
                                                   if historic_sources.get(n) != h),
        'historical_comparison': 'Exact bytes only; missing or newline-different is not a match.',
        'actions': copy.deepcopy(spec['actions']), 'edit_domains': list(spec['edit_domains']),
        'routes': ['B'] if selected in ('intake15', 'plans16_17') else ['A', 'B'],
        'workspace_kind': 'primary' if primary else 'registration12',
        'storage': {'schema': 'fmz6e_integration_private', 'state_writes': list(spec['state']),
                    'writeset': writeset(primary), 'grants': permissions(needs_outbox)},
        'auth_rls': {'authority_sources': [PREFIX + n for n in ('server.py', 'store.py', 'registration_store.py')],
                     'contract': 'Verified GoTrue /user plus live auth.sessions; server actor/role/workspace binding; private RLS.',
                     'scope': 'Existing local synthetic adapter only; no new hosted Auth grant.'},
        'api': {'transport': 'existing loopback HTTP server, not deployed Edge',
                'routes': ['POST /api/login', 'GET /api/today', 'POST /api/action', 'POST /api/logout'],
                'action_envelope': ['workspace', 'request_id', 'version', 'request'],
                'action_guard': 'Application.authorize_action uses fresh verified Store.read context.',
                'edge_deployment': None},
        'version': {'cas': 'exact workspace version; source/state SHA256; append-only revision history',
                    'snapshot': 'immutable original fixture/source; restore requires a new separately approved version'},
        'idempotency': {'key': ['workspace_id', 'request_id'], 'binding': ['actor_id', 'payload_sha'],
                        'same_request': 'existing result; zero new committed rows',
                        'changed_payload': 'duplicate_conflict', 'stale_version': 'version_conflict',
                        'lost_response': 'reconcile exact request; never invent a replacement key'},
        'migration': {'local_candidates': [{'path': n, 'sha256': sources[n],
                                            'count_after_apply_on_clean_ci': 46 + i}
                                           for i, n in enumerate(migrations)],
                      'canonical_hosted_identity': None, 'hosted_applied': False,
                      'outbox_reason': 'Store/composed primary mount accesses outbox even when delivery is disabled'
                                       if needs_outbox else 'minimal RegistrationStore has no outbox'},
        'invariants': list(spec['invariants']), 'rollback': spec['rollback'],
        'cleanup': {'executor': None, 'scope': 'only separately authorized exact newly owned synthetic keys',
                    'preserve': 'frozen sources, historical fixtures, revisions and audit; no broad or historical cleanup',
                    'closure': 'unknown outcome is NO_GO; require measured absence and protected-content equality'},
        'tests': {'local_commands': commands(spec), 'required_cases': list(spec['checks']),
                  'real_stack_entries': [PREFIX + n for n in spec['integration']],
                  'fresh_stack_executed_by_helper': False},
        'gate': {'enabled': False, 'full_day21': False, 'real_member_ai': False,
                 'blockers': list(RELEASE_BLOCKERS)},
    }


def build(root=ROOT):
    root = pathlib.Path(root).resolve()
    validate_plan()
    history = historical(root)
    entries = set(COMMON)
    for spec in SLICES:
        for field in ('entries', 'python', 'node', 'integration'):
            entries.update(spec[field])
    shared_sources = closure(root, [PREFIX + n for n in sorted(entries)] + [
        'assets/fit-met-zorge-logo-cropped.png', 'assets/training-workout-model.js'])
    slices = {s['id']: slice_contract(root, s, history['candidate_sources'], shared_sources)
              for s in SLICES}
    sources = dict(history['source_hashes'])
    packages = []
    for number, title, selected, dependencies in PLAN:
        contract = frozen(root, number)
        sources.update(contract['sources'])
        peers = [n for n, _, s, _ in PLAN if s == selected]
        packages.append({'package': number, 'title': title, 'depends_on': list(dependencies),
                         'frozen_contract': contract, 'selected_slice': selected,
                         'coupled_packages': peers, 'independent_action_gate': len(peers) == 1,
                         'implementation': copy.deepcopy(slices[selected])})
    for selected in slices.values():
        sources.update(selected['source_hashes'])
    tooling = closure(root, [PREFIX + n for n in TOOLING])
    sources.update(tooling)
    order_doc = 'docs/PHASE6E_WORKDAY_RELEASE_ORDER.md'
    sources[order_doc] = file_hash(root, order_doc)
    canonical = ci_profile.canonical(p.relative_to(root).as_posix()
                                     for p in (root / 'supabase/migrations').glob('*.sql'))
    sources.update({n: file_hash(root, n) for n in canonical})
    if PREFIX + 'release_train.json' in sources:
        raise ValueError('generated_manifest_is_not_an_input')
    return {
        'format': FORMAT, 'status': 'LOCAL_SOURCE_BOUND_MANIFEST_NOT_RELEASED',
        'owner_confirmed_base': OWNER_BASE, 'base_is_not_a_git_attestation': True,
        'source_binding_scope': 'selected app, local CI entry, frozen contracts and pinned historical receipts; not all endchain/CI sources',
        'source_hashes': dict(sorted(sources.items())), 'source_bundle_sha256': canonical_hash(sources),
        'hash_policy': 'SHA256 exact file bytes; JSON excludes itself; rebuild never creates CI evidence',
        'release_order': list(range(12, 21)), 'dependency_policy_source': order_doc,
        'migration_baseline': {'canonical_count': 45, 'canonical_sources': {n: sources[n] for n in canonical},
                               'local_app_counts': [46, 47], 'hosted_count_measured_here': None},
        'packages': packages,
        'post_train_supplements': [{'after_packages': list(range(12, 21)),
                                   'implementation': slices[n]} for n in ('workout12', 'preferences')],
        'historical_ci': {k: v for k, v in history.items() if k != 'candidate_sources'},
        'excluded': {'package21': True, 'default_off': True, 'actions': list(FORBIDDEN)},
        'gate': {'enabled': False, 'fresh_full_ci_claimed': False, 'hosted_admission': False,
                 'real_member_ai': False, 'blockers': list(RELEASE_BLOCKERS)},
        'authorization_boundary': {'endchain_limit_unchanged': 2349, 'temp_bytes_limit': 0,
                                   'read_wal_limit': 0, 'additional_hosted_commands_authorized': 0},
    }


def input_files(root=ROOT):
    """Candidate packaging inputs; no generated JSON or execution side effects."""
    return set(build(root)['source_hashes'])


def verify(document, root=ROOT):
    if not isinstance(document, dict) or document.get('format') != FORMAT:
        raise ValueError('release_train_format')
    sources = document.get('source_hashes', {})
    if not sources or document.get('source_bundle_sha256') != canonical_hash(sources):
        raise ValueError('source_bundle_binding')
    for name, expected in sources.items():
        pinned(root, name, expected)
    if document != build(root):
        raise ValueError('release_train_drift_rebuild_and_review')
    return {'status': 'MANIFEST_VALID_NOT_RELEASED', 'packages': 9,
            'fresh_full_ci_claimed': False, 'hosted_admission': False}


def gate(document, selected, root=ROOT):
    verify(document, root)
    if not selected or any(type(n) is not int or n not in range(12, 21) for n in selected):
        raise ValueError('packages_12_through_20_only')
    if len(selected) != len(set(selected)):
        raise ValueError('duplicate_package')
    chosen = set(selected)
    blockers = list(RELEASE_BLOCKERS)
    for package in document['packages']:
        if package['package'] not in chosen:
            continue
        missing = sorted(set(package['depends_on']) - chosen)
        peers = sorted(set(package['coupled_packages']) - chosen)
        if missing:
            blockers.append('dependency_selection_missing:' + ','.join(map(str, missing)))
        if peers:
            blockers.append('coupled_selection_missing:' + ','.join(map(str, peers)))
    return {'status': 'NO_GO', 'enabled': False, 'packages': sorted(chosen),
            'blockers': sorted(set(blockers)), 'hosted_admission': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check', 'gate', 'inputs'))
    parser.add_argument('--package', type=int, action='append')
    parser.add_argument('--manifest', type=pathlib.Path,
                        help='Existing local generated snapshot, for check/gate only')
    args = parser.parse_args(argv)
    try:
        # CLI is read-only: main/CI owns serialization and artifact collection.
        if args.manifest is not None and args.command not in ('check', 'gate'):
            raise ValueError('manifest_input_command')
        document = (json.loads(raw(args.manifest).decode('utf-8-sig'))
                    if args.manifest is not None else build())
        if args.command == 'build':
            value = document
        elif args.command == 'inputs':
            value = sorted(document['source_hashes'])
        elif args.command == 'check':
            value = verify(document)
        else:
            value = gate(document, args.package or [])
        print(json.dumps(value, sort_keys=True, indent=2))
        return 3 if args.command == 'gate' else 0
    except (ValueError, KeyError, TypeError, OSError):
        print(json.dumps({'status': 'NO_GO', 'reason': 'release_train_validation_failed',
                          'hosted_admission': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
