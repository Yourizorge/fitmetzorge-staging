"""Compile/check eight offline release packets; never enable or deploy a slice.

SQL profiles describe source paths, not measurements or a hosted budget. Existing
receipt helpers supply historical measurements without modifying those receipts.
"""
import argparse
import ast
import copy
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

from registration_accounting import build as transport_accounting
from receipt_accounting import meter_controls
from registration_scope import sha
from release_selection import SLICES, FORBIDDEN, selection_allows

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = '_offline/phase6e_server_v1/'
PACKETS = HERE / 'workday_release_packets.json'
ARCHIVE = HERE / 'receipts/ci-38746007554-completion'
M45 = PREFIX + 'supabase/migrations/20261014105919_phase6e_synthetic_server_candidate.sql'
M46 = PREFIX + 'supabase/migrations/20261014160019_phase6e_local_outbox.sql'
SCHEMA = 'fmz6e_integration_private'
TOOLING = ('workday_release.py', 'test_workday_release.py', 'release_selection.py', 'test_release_selection.py',
           'registration_release.py', 'registration_accounting.py',
           'receipt_accounting.py', 'registration_scope.py')


def disk(path):
    path = pathlib.Path(path).resolve()
    return pathlib.Path('\\\\?\\' + str(path)) if os.name == 'nt' else path


def raw(path):
    return disk(path).read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_file(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('source_path')
    relative = pathlib.PurePosixPath(name)
    path = (root / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(root.resolve()):
        raise ValueError('source_path')
    if not disk(path).is_file():
        raise ValueError('source_missing:' + name)
    return path


def closure(root, entries):
    """Follow literal JS requires and local Python imports, as existing CI does."""
    pending = list(entries)
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        path = safe_file(root, name)
        seen.add(name)
        if path.suffix not in ('.py', '.js', '.cjs', '.mjs'):
            continue
        text = raw(path).decode('utf-8-sig')
        targets = []
        if path.suffix == '.py':
            for node in ast.walk(ast.parse(text)):
                modules = ([node.module] if isinstance(node, ast.ImportFrom) else
                           [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                for module in modules:
                    if module:
                        target = path.parent / (module.replace('.', '/') + '.py')
                        if disk(target).is_file():
                            targets.append(target)
                # The existing server's static map and tuple whitelist contain
                # literal filenames, including concurrently added shell assets.
                if (path.name == 'server.py' and isinstance(node, ast.Constant)
                        and isinstance(node.value, str)
                        and re.fullmatch(r'[A-Za-z0-9_-]+\.(?:html|css|js|cjs)', node.value)):
                    targets.append(path.parent / node.value)
        else:
            targets = [path.parent / ref for ref in re.findall(r'''require\(["'](\.[^"']+)["']\)''', text)]
        for target in targets:
            if not target.resolve().is_relative_to(root.resolve()):
                raise ValueError('dependency_escape')
            pending.append(target.resolve().relative_to(root.resolve()).as_posix())
    return {name: digest(raw(safe_file(root, name))) for name in sorted(seen)}


def sql_value(node, lock=False):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id == 'SCHEMA':
        return SCHEMA
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return sql_value(node.left, lock) + sql_value(node.right, lock)
    if isinstance(node, ast.IfExp) and isinstance(node.test, ast.Name) and node.test.id == 'lock':
        return sql_value(node.body if lock else node.orelse, lock)
    raise ValueError('unresolved_sql_template')


def statements(root, file, method, lock=False):
    name = PREFIX + file
    tree = ast.parse(raw(safe_file(root, name)).decode('utf-8-sig'))
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == method]
    if len(functions) != 1:
        raise ValueError('sql_method_binding')
    calls = sorted((n for n in ast.walk(functions[0]) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == 'execute'), key=lambda n: n.lineno)
    result = []
    for node in calls:
        sql = sql_value(node.args[0], lock)
        result.append({'source': name, 'line': node.lineno, 'method': method,
                       'sql': sql, 'template_sha256': digest(sql.encode())})
    return result


def sql_profiles(root):
    # protocol.py has a method and a function with the same name. Bind the
    # top-level transaction explicitly, without importing a database adapter.
    name = PREFIX + 'protocol.py'
    tree = ast.parse(raw(root / name).decode('utf-8-sig'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'transaction')
    ends = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'execute':
            sql = sql_value(node.args[0])
            ends[sql] = dict(source=name, line=node.lineno, method='transaction', sql=sql, template_sha256=digest(sql.encode()))
    if set(ends) != {'BEGIN', 'COMMIT', 'ROLLBACK'}:
        raise ValueError('transaction_terminals')
    bind = statements(root, 'store.py', 'bind')
    minimal = statements(root, 'registration_store.py', 'execute')
    primary = statements(root, 'store.py', 'execute')
    row = statements(root, 'registration_store.py', 'row')
    locked = statements(root, 'registration_store.py', 'row', True)
    read12 = statements(root, 'registration_store.py', 'read')
    read = statements(root, 'store.py', 'read')
    if tuple(map(len, (bind, minimal, primary, row, read12, read))) != (4, 5, 9, 1, 1, 3):
        raise ValueError('sql_structure_changed')
    b, c = [ends['BEGIN']], [ends['COMMIT']]
    profiles = {
        'registration_read': b + read12 + bind + row + c,
        'registration_changed': b + bind + locked + minimal + c,
        'registration_replay': b + bind + locked + minimal[:1] + c,
        'member_read': b + read[:1] + bind + read[1:] + c,
        'trainer_read': b + read[:1] + bind + read[1:2] + c,
        'primary_changed': b + bind + primary[:6] + primary[8:] + c,
        'primary_unchanged': b + bind + primary[:2] + primary[4:6] + primary[8:] + c,
        'primary_replay': b + bind + primary[:2] + c,
    }
    catalog = {}
    def reference(row):
        key = row['source'] + ':' + row['method'] + ':' + row['template_sha256']
        catalog[key] = row
        return key
    rollback = reference(ends['ROLLBACK'])
    output = {}
    for key, sequence in profiles.items():
        refs = [reference(row) for row in sequence]
        output[key] = {'classification': 'STATIC_SOURCE_MODEL_NOT_MEASURED', 'sequence': refs,
                       'base_commands': len(refs), 'managed_auth_commands': None,
                       'outbox_commands': 'one per exact INSERT/UPDATE from outbox.changes' if key.startswith('primary_') and key != 'primary_replay' else 0,
                       'failure_prefixes': [{'attempted_commands': i, 'rollback_template': rollback,
                                            'with_one_attempted_rollback': i + 1} for i in range(1, len(refs) + 1)],
                       'note': 'Terminal failure can be uncertain. Close connection; recover same request before any retry. Full safe closure is unbound.'}
    extra = {operation: reference(primary[index]) for operation, index in [('INSERT', 6), ('UPDATE', 7)]}
    return {'templates': catalog, 'profiles': output, 'outbox_templates': extra,
            'outbox_placement': 'after outbox SELECT FOR UPDATE and before audit SELECT; repeat for exact selected keys'}


def historical_evidence(root, archive=ARCHIVE):
    if not disk(archive / 'MANIFEST.json').is_file():
        return {'classification': 'ARCHIVE_NOT_AVAILABLE', 'source_hashes': {},
                'registration12_observed_sql': None, 'transport_observed_sql': None,
                'transport_pair_count': None, 'current_source_ci': 'NOT_ESTABLISHED_BY_THIS_HELPER',
                'hosted_authorized': False,
                'note': 'CI need not ship historical receipts. No measured totals or historical source match claimed without the verified archive.'}
    manifest = json.loads(raw(archive / 'MANIFEST.json'))
    used = {}
    def read(name):
        data = raw(safe_file(archive, name))
        if manifest['files'].get(name) != digest(data):
            raise ValueError('receipt_hash:' + name)
        used[name] = digest(data)
        return json.loads(data)
    result, collection = read('result.json'), read('collection.json')
    sources, dossier = read('source-hashes.json'), read('registration12-release-dossier.json')
    if (result['status'] != 'CLEAN_CI_PASS' or collection['verified'] is not True
            or str(collection['run']) != result['run_id']
            or not manifest['head'] == collection['head'] == result['commit'] == dossier['head']
            or manifest['candidate_sha256'] != result['candidate_sha256']
            or manifest['archive_sha256'] != collection['archive_sha256']
            or dossier['source_hashes'] != sources):
        raise ValueError('historical_binding')
    measured = transport_accounting(read, manifest['files'])
    if measured != read('registration12-transport-register.json'):
        raise ValueError('historical_transport_register')
    controls = meter_controls(manifest['files'], read)
    if dossier['phases'][-1] != controls or sum(p['commands'] for p in dossier['phases']) != dossier['observed_sql_total']:
        raise ValueError('historical_meter_accounting')
    return {'classification': 'HISTORICAL_DISPOSABLE_CI_ONLY', 'run': collection['run'],
            'head': result['commit'], 'candidate_sha256': result['candidate_sha256'],
            'archive_sha256': collection['archive_sha256'],
            'receipt_directory': archive.relative_to(root).as_posix(),
            'manifest_sha256': digest(raw(archive / 'MANIFEST.json')), 'consumed_receipts': used,
            'source_hashes': sources, 'registration12_observed_sql': dossier['observed_sql_total'],
            'transport_observed_sql': measured['observed_commands'], 'transport_pair_count': measured['pair_count'],
            'transport_register_sha256': measured['register_sha256'],
            'not_additive': 'Minimal and private-transport runs are separate scopes; neither is a per-slice or hosted allowance.',
            'current_source_ci': 'NOT_ESTABLISHED_BY_THIS_HELPER', 'hosted_authorized': False}


def commands(spec):
    rows = [{'cwd': PREFIX.rstrip('/'), 'argv': ['python', '-B', 'test_release_selection.py'],
             'kind': 'local_unit', 'network': False}]
    for name in spec['python']:
        rows.append({'cwd': PREFIX.rstrip('/'), 'argv': ['python', '-B', name], 'kind': 'local_unit', 'network': False})
    if spec['node']:
        rows.append({'cwd': PREFIX.rstrip('/'), 'argv': ['node', '--test', *spec['node']], 'kind': 'local_unit', 'network': False})
    return rows


def permissions(primary):
    return {'schema': SCHEMA, 'Data_API_exposed': False,
            'denied_schema_roles': ['PUBLIC', 'anon', 'authenticated', 'service_role'],
            'server_role': 'fmz6e_integration_server', 'role_flags': ['NOLOGIN', 'NOSUPERUSER', 'NOINHERIT', 'NOBYPASSRLS'],
            'rls': 'enabled on every candidate table; exact verified actor, live session and workspace binding; browser role is not authority',
            'server_grants': {'subjects': ['SELECT self'], 'workspaces': ['SELECT', 'UPDATE(version,consent,state_text,state_sha)'],
                              'revisions': ['SELECT', 'INSERT'], 'requests': ['SELECT', 'INSERT'], 'audit': ['SELECT', 'INSERT via observer'],
                              **({'outbox': ['SELECT', 'INSERT', 'UPDATE(status,history)']} if primary else {})},
            'functions': ['actor()', 'observe()'] + (['outbox_append()'] if primary else []),
            'function_security': 'SECURITY INVOKER; search_path=pg_catalog,pg_temp; PUBLIC execute revoked',
            'sequence': 'USAGE for audit identity; sequence gaps on rollback are possible',
            'role_membership': 'Existing local SET-only postgres membership; no new hosted grant prepared',
            'delete': 'No application DELETE grant. Separate operator cleanup must prove exact owned synthetic keys and retained delete audit.',
            'integration_needed': 'These are existing schema grants, not per-action isolation. Bind the selected action allowlist at the private server boundary.'}


def writeset(primary):
    return {'changed': [dict(table=SCHEMA + '.workspaces', operation='UPDATE', key=['workspace_id'], count=1,
                            columns=['version', 'consent', 'state_text', 'state_sha']),
                        dict(table=SCHEMA + '.revisions', operation='INSERT', key=['workspace_id', 'next_version'], count=1),
                        dict(table=SCHEMA + '.requests', operation='INSERT', key=['workspace_id', 'request_id'], count=1)],
            'outbox': {'enabled_in_adapter': primary, 'allowed_operations': ['INSERT', 'UPDATE'] if primary else [],
                       'key': ['workspace_id', 'event_key'], 'count': 'len(outbox.changes(...))' if primary else 0,
                       'binding': 'derive exact event keys/status/history from locked state, server clock, action and request; no wildcard allowance'},
            'no_op': 'Store: one requests INSERT, plus exact outbox delta; no workspace/revision write' if primary else 'No general no-op path; identical request replay writes zero rows',
            'replay_denial_rollback': 'zero committed application and audit rows; rollback may consume audit sequence values',
            'audit': 'one metadata row per application row; exact SHA256 PostgreSQL JSON key encoding, actor SHA256, request and one xid; reject extra/missing/reordered writes',
            'other_members': 'zero allowed writes',
            'cleanup': 'entry disabled first; requests then revisions then workspace (outbox first if present); only manifest-owned fixtures, preserve revisions/audit unless fixture deletion separately admitted'}


def accounting(spec):
    primary = spec['adapter'] == 'Store'
    profiles = (['member_read', 'trainer_read', 'primary_changed', 'primary_unchanged', 'primary_replay'] if primary else
                ['registration_read', 'registration_changed', 'registration_replay'])
    phases = [
        ('identity_sources_rights', 'project/schema/ACL/session/source identities and exact synthetic bindings'),
        ('migration_and_dry_run', 'selected canonical identity, exact CLI protocol, observers AND meter controls; candidate names are not reserved slots'),
        ('protected_baseline', 'full protected-content baseline; numeric size is insufficient'),
        ('fixtures_guards_auth', 'exact owned fixtures/guard and all managed Auth internal statements'),
        ('selected_application', 'ordered reads/writes/replay/conflict/fault/relogin scenarios, exact requests and SQL profiles'),
        ('precleanup_measurement', 'scoped before/action/after validated pairs and protected comparison'),
        ('cleanup', 'exact fixture deletions, session revocation and retained audit/delete proof'),
        ('terminal_closure', 'protected final comparison, empty dry-run, IO observers, access/JIT revoke and confirmation'),
    ]
    return {'profiles': profiles, 'modeled_not_measured': True,
            'future_command_register': [{'ordinal': i + 1, 'phase': phase, 'required_binding': binding,
                                         'commands': None, 'state': 'REQUIRES_EXACT_RUN_BINDING'} for i, (phase, binding) in enumerate(phases)],
            'safe_stop': ['rollback and close owned connection', 'disable selected entry/subjects', 'revoke exact test sessions',
                          'audit/delete only confirmed owned fixtures or preserve them', 'protected terminal comparison',
                          'dry-run with all observers/meter controls', 'revoke temporary guard/JIT and confirm closure'],
            'prefix_rule': 'Before EVERY mutation reserve attempted command plus all reachable safe-stop commands, including managed Auth/observers. Preserve first error; no dependent write after stop.',
            'automatic_retries': 0, 'query_timeout_seconds': 5, 'lock_timeout_seconds': 1,
            'normal_commands': None, 'safe_stop_maximum': None, 'hosted_approved_limit': None,
            'local_boundary_overhead': 'Selected Application.authorize_action performs fresh read before execute: registration_read8 or primary member_read9/trainer_read8 plus managed Auth. Denied neighboring actions still consume that read. These costs are additional to execute profiles and must be measured in CI; no prior register is reclassified.',
            'missing': ['exact run/actor/workspace/request IDs', 'current selected-source clean CI',
                        'hosted guard/Auth/CLI/observer/cleanup counts and prefix closure proof',
                        'per-slice protected filters and full row-content preservation proof'],
            'budget_boundary': 'The authorized106496/2237 run belongs to11 only. Neither it nor old4135 nor local measured counts authorize these slices.'}


def gate(spec):
    return {'enabled': False, 'runtime_enforced_by_this_helper': False, 'hosted_released': False,
            'local_boundary_implemented': True, 'local_boundary_source': PREFIX + 'server.py',
            'operator_selection_env': 'FMZ_LOCAL_RELEASE_SLICE',
            'local_action_guard': {'module': 'release_selection.py', 'function': 'require_action', 'generated_json_required': False,
                                   'context': 'verified server role, route and workspace_kind; never browser fields',
                                   'optional_local_boundary': 'Application.release_slice; None preserves existing local-only bulk mode outside the guard'},
            'local_entry': 'FMZ_LOCAL_REGISTRATION12_ENABLED' if spec['id'] == 'registration12' else 'FMZ_LOCAL_INTEGRATION_ENABLED',
            'local_entry_is_bulk_candidate': spec['id'] != 'registration12',
            'full_day21': False, 'real_member_ai': False,
            'required': ['complete11 hosted chain for the separately authorized exact run', 'required physical owner review',
                         'separate selected-slice release decision', 'exact source CI, identities, ACL, migration, writesets and command budget',
                         'hosted private per-action runtime gate and measured safe closure'],
            'integration_needed': (['Registration transport Candidate exists but has no deployed listener/activation entry. Bind existing registration_scope admission and full command register.']
                                   if spec['id'] == 'registration12' else
                                   ['Parent wired optional LOCAL Application.release_slice with fresh verified read before require_action and execute; real HTTP/PG/Auth result remains separate evidence.',
                                    'Source-bound HOSTED adapter, per-slice measured accounting, CI and safe closure are still required.']),
            'denied_actions': list(FORBIDDEN), 'journey12': spec['id'] == 'workout12'}


def build(root=ROOT, archive=ARCHIVE):
    history = historical_evidence(root, archive)
    packets = []
    common = ['server.py', 'worker.cjs', 'protocol.py', 'release_selection.py', 'release_selection_http.py', 'ui.html', 'ui.js', 'ui.css', 'panels.js',
              'display.js', 'queue_ui.js', 'draft_queue.js', 'sync_contract.cjs']
    for ordinal, spec in enumerate(SLICES, 1):
        primary = spec['adapter'] == 'Store'
        entries = list(dict.fromkeys(spec['entries'] + common + spec['python'] + spec['node'] + spec['integration']))
        files = closure(root, [PREFIX + name for name in entries] + ['assets/fit-met-zorge-logo-cropped.png'])
        selected = [M45] + ([M46] if primary or spec['id'] == 'workout12' else [])
        files.update({name: digest(raw(safe_file(root, name))) for name in selected})
        mismatches = [name for name, value in files.items() if history['source_hashes'].get(name) != value]
        packets.append({'ordinal': ordinal, 'id': spec['id'], 'title': spec['title'],
                        'release_after': SLICES[ordinal - 2]['id'] if ordinal > 1 else 'hosted11_and_owner_review',
                        'functions': spec['functions'], 'entry_files': [PREFIX + n for n in spec['entries']],
                        'source_hashes': dict(sorted(files.items())), 'source_bundle_sha256': sha(files),
                        'source_note': 'Exact working-file bytes including transitive local imports. Shared loaded code is not an action grant. Do not normalize newline drift into a CI match.',
                        'historical_ci_byte_mismatches': sorted(mismatches),
                        'database': {'candidates': [{'path': n, 'sha256': files[n]} for n in selected],
                                     'canonical_hosted_migration': None, 'hosted_applied': False,
                                     'objects': ['subjects', 'workspaces', 'revisions', 'requests', 'audit'] + (['outbox'] if len(selected) == 2 else []),
                                     'reason': 'M45 for historical adapter; composed mount also requires M46 for primary Store' if spec['id'] == 'workout12' else
                                               'Store unconditionally accesses M46 outbox, even before slice6; delivery remains off' if primary else 'Minimal registration uses M45 only'},
                        'permissions': permissions(primary or spec['id'] == 'workout12'),
                        'actions': copy.deepcopy(spec['actions']), 'edit_domains': spec['edit_domains'],
                        'routes': ['B'] if spec['id'] in ('intake15', 'plans16_17') else ['A', 'B'],
                        'state_writes': spec['state'], 'invariants': spec['invariants'], 'writeset': writeset(primary),
                        'tests': {'local_commands': commands(spec), 'required_cases': spec['checks'],
                                  'real_stack': {'command': ['python', '-B', PREFIX + 'ci.py'], 'cwd': '.',
                                                 'preconditions': 'Existing isolated CI runner/candidate environment with PG17, GoTrue, verified TLS, psycopg and Playwright; not a standalone Windows unit command',
                                                 'entry_files': [PREFIX + n for n in spec['integration'] + ['release_selection_http.py']], 'executed_by_helper': False}},
                        'accounting': accounting(spec), 'gate': gate(spec), 'rollback': spec['rollback'],
                        'status': {'built': 'LOCAL_PACKET_COMPILED', 'local_ci': 'CURRENT_CI_NOT_CLAIMED',
                                   'hosted': 'NOT_PROVEN', 'review': 'NOT_RECORDED', 'released': False,
                                   'dependency': ['selected source CI completion', 'complete hosted11 and required review',
                                                  'separate selected release and runtime/accounting integration']}})
    canonical = {p.relative_to(root).as_posix(): digest(raw(p)) for p in sorted((root / 'supabase/migrations').glob('*.sql'))}
    return {'format': 'fmz-workday-release-packets-v1', 'status': 'LOCAL_PACKETS_NOT_HOSTED_ADMISSION',
            'snapshot_finality': 'WORKTREE_SNAPSHOT_NOT_CI_ATTESTATION; regenerate only after all selected source edits finish, then collect from exact CI candidate',
            'repository': 'Yourizorge/fitmetzorge-staging', 'branch': 'main', 'project': 'mokxyyullfhkfalopbzd',
            'request': 'f39c835e-3db0-4149-9011-998f00aff831/Geplakte tekst.txt section8; scoped local-only instruction takes precedence',
            'tooling_source_hashes': {PREFIX + n: digest(raw(root / PREFIX / n)) for n in TOOLING},
            'canonical_migration_baseline': canonical, 'history': history,
            'sql_model': sql_profiles(root), 'packets': packets,
            'integration_needed': ['Parent ci.py now includes workday_release.py, test_workday_release.py, release_selection.py, test_release_selection.py, release_selection_http.py, receipt_accounting.py and test_receipt_accounting.py; existing registration helpers remain required',
                                   'After parallel source edits finish, run tests then build/check on the selected exact candidate and collect the GENERATED packet as an artifact. Do not add the generated packet to candidate inputs. Historical archives are optional; never compare working-copy hashes to differently checked-out bytes or claim old CI covers new tooling',
                                   'Keep existing registration_release/accounting exports; add per-slice source-bound executed registers and closure proof before release',
                                   'Optional local server gate is implemented; collect actual release_selection_http PG/Auth evidence and account for its fresh context reads. Hosted boundary/admission remains separate'],
            'hosted_calls': 0, 'migrations_created': 0, 'hosted_released': False}


def verify(document, root=ROOT, archive=ARCHIVE):
    if document != build(root, archive):
        raise ValueError('packet_drift_rebuild_and_review_required')
    return {'status': 'PACKETS_VALID_NOT_RELEASED', 'slices': len(document['packets']),
            'source_bundle_sha256': sha([p['source_bundle_sha256'] for p in document['packets']]),
            'hosted_released': False, 'current_ci_claimed': False}


def status_rows(register):
    """Tolerate older registers and in-progress parent updates without inventing PASS."""
    known = {row['id']: row for row in register.get('functions', [])}
    rows = []
    for spec in SLICES:
        items = [known.get(key, {}) for key in spec['functions']]
        rows.append({'id': spec['id'], 'built': 'PACKET_AVAILABLE',
                     'local_ci': [row.get('local_ci', row.get('evidence', 'NOT_RECORDED')) for row in items],
                     'hosted': [row.get('hosted', 'NOT_RECORDED') for row in items],
                     'review': [row.get('review', 'NOT_RECORDED') for row in items],
                     'released': [row.get('released', False) for row in items],
                     'dependency': [row.get('dependency', row.get('remaining', 'NOT_RECORDED')) for row in items]})
    return {'hosted11': register.get('hosted11', 'NOT_RECORDED'), 'slices': rows,
            'note': 'Parent-owned current statuses; historical evidence and in-progress CI do not imply current PASS.'}


def selected(document, name):
    return next(row for row in document['packets'] if row['id'] == name)


def local_test_commands(document, slice_id=None):
    rows = [{'cwd': PREFIX.rstrip('/'), 'argv': ['python', '-B', name], 'kind': 'local_unit', 'network': False}
            for name in ('test_workday_release.py', 'test_release_selection.py')]
    for packet in document['packets']:
        if slice_id is None or packet['id'] == slice_id:
            rows.extend(packet['tests']['local_commands'])
    unique = {}
    for row in rows:
        unique.setdefault(tuple(row['argv']), row)
    return list(unique.values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'check', 'show', 'gate', 'test', 'status'])
    parser.add_argument('--slice', choices=[s['id'] for s in SLICES])
    args = parser.parse_args(argv)
    if args.mode == 'status':
        print(json.dumps(status_rows(json.loads(raw(HERE / 'work_register.json'))), indent=2))
        return 0
    if args.mode == 'build':
        document = build()
        disk(PACKETS).write_text(json.dumps(document, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps({'status': document['status'], 'slices': len(document['packets']), 'file': PACKETS.name}))
        return 0
    document = json.loads(raw(PACKETS))
    checked = verify(document)
    if args.mode == 'show':
        print(json.dumps(selected(document, args.slice) if args.slice else document, indent=2))
    elif args.mode == 'gate':
        print(json.dumps({'status': 'CLOSED_NOT_HOSTED_ADMISSION', 'enabled': False,
                          'required': selected(document, args.slice or 'registration12')['gate']['required']}))
        return 3
    elif args.mode == 'test':
        # Execute only freshly compiled allowlisted unit commands, never packet
        # shell text or the CI/hosted command descriptions.
        for row in local_test_commands(document, args.slice):
            command = list(row['argv'])
            if command[0] == 'python':
                command[0] = sys.executable
            print(json.dumps({'running': row['argv'], 'cwd': row['cwd']}), flush=True)
            result = subprocess.run(command, cwd=ROOT / row['cwd'], timeout=120, check=False)
            if result.returncode:
                return result.returncode
        verify(document)
        print(json.dumps({'status': 'LOCAL_UNIT_PASS_ONLY', 'current_ci_claimed': False, 'hosted_released': False}))
    else:
        print(json.dumps(checked))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, StopIteration, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status': 'NO_GO', 'error': str(error)}), file=sys.stderr)
        sys.exit(2)
