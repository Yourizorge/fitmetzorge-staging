"""Replay original HTTP metadata bytes without importing candidate/artifact code.

This is one terminal-verifier dependency, not a full terminal verifier. Successful
replay is not proof of user identity, SQL cost, process exit, or token revocation.
The caller supplies the trusted candidate source inventory and binding; neither
is taken on authority from an exported receipt.
"""
import ast
import hashlib
import json
import pathlib
import re

PREFIX = '_offline/phase6e11/endchain_v1/quota_candidate_v1/'
SELF = PREFIX + 'runtime_exported_http.py'
PRODUCERS = tuple(PREFIX + n for n in ('runtime_http.py', 'runtime_http.mjs', 'runtime_auth.mjs'))
JOURNAL = 'case-auth-http.ledger.txt'
RECEIPT = 'case-auth-http-terminal.json'
MAX_JOURNAL = 262144


def require(value, code):
    if not value:
        raise ValueError('exported_http_' + code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_key')
            result[key] = value
        return result
    try:
        result = json.loads(raw, object_pairs_hook=unique,
            parse_constant=lambda _: require(False, 'nonfinite'))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('exported_http_json') from error
    require(type(result) is dict, 'object')
    return result


def _path(value):
    require(type(value) is str and re.fullmatch('[A-Za-z0-9_./-]+', value)
            and all(p not in ('', '.', '..') for p in value.split('/')), 'path')
    return value


def _source(root, name, expected):
    name = _path(name)
    require(type(expected.get(name)) is str and re.fullmatch('[a-f0-9]{64}', expected[name]),
            'source_missing')
    path = root / name
    require(path.resolve(strict=True).is_relative_to(root)
            and all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *path.parents)), 'source_escape')
    require(path.stat().st_size <= 2000000, 'source_size')
    raw = path.read_bytes()
    require(len(raw) <= 2000000 and digest(raw) == expected[name], 'source_hash')
    return raw


def _literals(raw):
    values = {}
    for node in ast.parse(raw).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('ROLES', 'OPERATIONS'):
                require(target.id not in values, 'source_literal_duplicate')
                values[target.id] = ast.literal_eval(node.value)
    require(set(values) == {'ROLES', 'OPERATIONS'}
            and values['ROLES'] == ('a_member', 'a_trainer', 'b_member')
            and values['OPERATIONS'] == ('issue', 'verify', 'getUser', 'refresh', 'logout', 'revoked_denial'),
            'source_literals')
    return values['ROLES'], values['OPERATIONS']


def _snapshot(value, roles, operations):
    require(type(value) is dict and set(value) == {'format', 'sealed', 'rows'}
            and value['format'] == 'case-auth-http-v1' and type(value['sealed']) is bool,
            'snapshot')
    rows = value['rows']
    require(type(rows) is list and len(rows) <= 21, 'rows')
    for index, row in enumerate(rows, 1):
        require(type(row) is dict and set(row) == {
            'ordinal', 'role', 'operation', 'safety', 'attempted', 'terminal', 'status'}, 'row')
        require(type(row['ordinal']) is int and row['ordinal'] == index
                and row['role'] in roles and row['operation'] in operations, 'intent')
        require(all(type(row[k]) is bool for k in ('safety', 'attempted', 'terminal'))
                and (not row['safety'] or row['operation'] == 'logout'), 'flags')
        require(row['status'] is None or type(row['status']) is int
                and 100 <= row['status'] <= 599, 'status')
        require(not row['terminal'] or row['attempted'] and row['status'] is not None,
                'terminal')
        require(row['attempted'] or row['status'] is None, 'unattempted_status')
        require(index == len(rows) or row['terminal'], 'unresolved_prefix')
    return value


def verify_exported_http(originals, *, run_id, binding_sha, expected_sources, trusted_root):
    """Return an independently derived transport observation, never CASE_PASS.

    `originals` must come from the separately verified original archive. This
    function still checks the terminal's exact raw journal reference, canonical
    chained bytes, monotone state and all derived counters. Unknown/lost replies
    remain unknown even if the worker sealed its ledger. A sealed empty prefix
    is not evidence that any requests occurred.
    """
    require(type(originals) is dict and 1 <= len(originals) <= 4096, 'originals')
    require(all(type(k) is str for k in originals)
            and len({k.casefold() for k in originals}) == len(originals), 'original_alias')
    require(type(run_id) is str and re.fullmatch(
        '[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', run_id)
        and run_id not in ('11a909f4-7113-424a-aa4b-ce9964720a3e',
                          '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'), 'run_id')
    require(type(binding_sha) is str and re.fullmatch('[a-f0-9]{64}', binding_sha), 'binding')
    require(type(expected_sources) is dict and 1 <= len(expected_sources) <= 4096
            and all(type(k) is str for k in expected_sources)
            and len({k.casefold() for k in expected_sources}) == len(expected_sources), 'sources')
    root = pathlib.Path(trusted_root).resolve(strict=True)
    raw_sources = {name: _source(root, name, expected_sources) for name in (SELF, *PRODUCERS)}
    require(digest(pathlib.Path(__file__).read_bytes()) == expected_sources[SELF], 'loaded_collector')
    roles, operations = _literals(raw_sources[PRODUCERS[0]])
    source_hashes = {name: digest(raw_sources[name]) for name in PRODUCERS}
    raw, terminal_raw = originals.get(JOURNAL), originals.get(RECEIPT)
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JOURNAL
            and type(terminal_raw) is bytes and 0 < len(terminal_raw) <= 65536, 'missing_or_oversize')
    lines = raw.splitlines(keepends=True)
    require(lines and len(lines) <= 128 and all(line.endswith(b'\n') for line in lines), 'line_bound')
    header = decode(lines[0])
    require(lines[0] == canonical(header) + b'\n', 'canonical')
    require(header == dict(format='case-auth-http-journal-v1', run_id=run_id,
        binding_sha=binding_sha, source_hashes=source_hashes), 'header_binding')
    state = dict(format='case-auth-http-v1', sealed=False, rows=[])
    prefix = lines[0]
    for line in lines[1:]:
        entry = decode(line)
        require(line == canonical(entry) + b'\n', 'canonical')
        require(set(entry) == {'previous_sha256', 'snapshot'}
                and entry['previous_sha256'] == digest(prefix), 'hash_chain')
        new = _snapshot(entry['snapshot'], roles, operations)
        require(not state['sealed'], 'sealed_changed')
        require(new != state, 'duplicate_snapshot')
        require(len(state['rows']) <= len(new['rows']) <= len(state['rows'])+1, 'prefix')
        for before, after in zip(state['rows'], new['rows']):
            require(all(before[k] == after[k] for k in ('ordinal', 'role', 'operation', 'safety')),
                    'intent_changed')
            require(not before['attempted'] or after['attempted'], 'attempt_retracted')
            require(not before['terminal'] or after == before, 'terminal_changed')
            require(before['status'] is None or before['status'] == after['status'], 'status_changed')
        state = new
        prefix += line
    unknown = sum(row['attempted'] and not row['terminal'] for row in state['rows'])
    unresolved = sum(not row['terminal'] for row in state['rows'])
    complete = state['sealed'] and unresolved == 0
    reference = dict(path=JOURNAL, sha256=digest(raw), bytes=len(raw))
    terminal = decode(terminal_raw)
    expected = dict(format='case-auth-http-terminal-v1', run_id=run_id,
        source_hashes=source_hashes, snapshot=state, all_responses_terminal=complete,
        unknown_attempts=unknown, unresolved_intents=unresolved, journal_ref=reference,
        worker_termination_proven=False, revocation_proven=False, deletion_admitted=False,
        additional_http_requests=0, additional_sql_commands=0, additional_ipc_messages=0)
    # Comparing canonical bytes also rejects bool/int substitutions hidden by ==.
    require(canonical(terminal) == canonical(expected), 'terminal_mismatch')
    return dict(format='exported-http-replay-v1', status='HTTP_OBSERVATIONS_REPLAYED',
        run_id=run_id, binding_sha=binding_sha, snapshot=state,
        observed_intents=len(state['rows']), observed_attempts=sum(row['attempted'] for row in state['rows']),
        unknown_attempts=unknown, unresolved_intents=unresolved, all_responses_terminal=complete,
        evidence_refs=[reference, dict(path=RECEIPT, sha256=digest(terminal_raw), bytes=len(terminal_raw))],
        collector_source_hashes={name: digest(value) for name, value in raw_sources.items()},
        case_terminal_verified=False, identity_verified=False, worker_termination_proven=False,
        revocation_proven=False, deletion_admitted=False, full_chain_admission=False,
        hosted_admitted=False, additional_sql_commands=0)
