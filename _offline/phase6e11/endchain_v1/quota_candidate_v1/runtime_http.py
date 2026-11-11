"""Source-bound monotone HTTP metadata, never token revocation or delete authority."""
import copy
import hashlib
import json
import os
import pathlib

PREFIX = '_offline/phase6e11/endchain_v1/quota_candidate_v1/'
ROLES = ('a_member', 'a_trainer', 'b_member')
OPERATIONS = ('issue', 'verify', 'getUser', 'refresh', 'logout', 'revoked_denial')


def require(value, code):
    if not value:
        raise ValueError('case_http_' + code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def shape(value):
    require(type(value) is dict and set(value) == {'format', 'sealed', 'rows'}
            and value['format'] == 'case-auth-http-v1' and type(value['sealed']) is bool,
            'snapshot')
    require(type(value['rows']) is list and len(value['rows']) <= 21, 'bound')
    for index, row in enumerate(value['rows']):
        require(type(row) is dict and set(row) == {
            'ordinal', 'role', 'operation', 'safety', 'attempted', 'terminal', 'status'}, 'row')
        require(type(row['ordinal']) is int and row['ordinal'] == index+1
                and row['role'] in ROLES and row['operation'] in OPERATIONS, 'intent')
        require(all(type(row[k]) is bool for k in ('safety', 'attempted', 'terminal'))
                and (not row['safety'] or row['operation'] == 'logout'), 'flags')
        require(row['status'] is None or type(row['status']) is int
                and 100 <= row['status'] <= 599, 'status')
        require(not row['terminal'] or row['attempted'] and row['status'] is not None, 'terminal')
        require(row['attempted'] or row['status'] is None, 'unattempted_status')
        require(index == len(value['rows'])-1 or row['terminal'], 'unresolved_prefix')
    return copy.deepcopy(value)


class HttpJournal:
    def __init__(self, gate, composition):
        self.gate, self.composition = gate, composition
        quota = composition.quota
        root = pathlib.Path(quota['root']).resolve(strict=True)
        sources = quota['manifest']['sources']
        self.sources = {}
        for name in ('runtime_http.py', 'runtime_http.mjs', 'runtime_auth.mjs'):
            path = root / (PREFIX + name)
            require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root), 'source_path')
            raw = path.read_bytes()
            require(sha(raw) == sources.get(PREFIX + name), 'source')
            self.sources[PREFIX + name] = sha(raw)
        require(sha(pathlib.Path(__file__).read_bytes()) == self.sources[PREFIX+'runtime_http.py'],
                'loaded_source')
        self.path = gate.out / 'case-auth-http.ledger.txt'
        self.snapshot = {'format':'case-auth-http-v1', 'sealed':False, 'rows':[]}
        self.raw = canonical({'format':'case-auth-http-journal-v1',
            'run_id':quota['binding']['run_id'], 'binding_sha':quota['binding']['binding_sha'],
            'source_hashes':self.sources}) + b'\n'
        with self.path.open('xb') as stream:
            require(stream.write(self.raw) == len(self.raw), 'short_write')
            stream.flush(); os.fsync(stream.fileno())
        require(self.path.read_bytes() == self.raw, 'readback')
        self.failed = False

    def accept(self, value):
        require(not self.failed, 'journal_failed')
        try:
            new = shape(value)
            old = self.snapshot
            require(not old['sealed'] or new == old, 'sealed_changed')
            require(len(old['rows']) <= len(new['rows']) <= len(old['rows'])+1, 'prefix')
            for before, after in zip(old['rows'], new['rows']):
                require(all(before[k] == after[k] for k in ('ordinal','role','operation','safety')),
                        'intent_changed')
                require(not before['attempted'] or after['attempted'], 'attempt_retracted')
                require(not before['terminal'] or after == before, 'terminal_changed')
                require(before['status'] is None or before['status'] == after['status'], 'status_changed')
            if new == old:
                return
            record = canonical({'previous_sha256':sha(self.raw), 'snapshot':new}) + b'\n'
            require(len(self.raw)+len(record) <= 262144, 'journal_bound')
            require(self.path.read_bytes() == self.raw, 'journal_changed')
            with self.path.open('ab', buffering=0) as stream:
                require(stream.write(record) == len(record), 'short_write')
                os.fsync(stream.fileno())
            self.raw += record
            require(self.path.read_bytes() == self.raw, 'readback')
            self.snapshot = new
        except BaseException:
            self.failed = True
            raise

    def receipt(self):
        require(not self.failed and self.path.read_bytes() == self.raw, 'journal_changed')
        value = copy.deepcopy(self.snapshot)
        return {'format':'case-auth-http-terminal-v1', 'run_id':self.composition.quota['binding']['run_id'],
            'source_hashes':self.sources, 'snapshot':value,
            'all_responses_terminal':value['sealed'] and all(r['terminal'] for r in value['rows']),
            'unknown_attempts':sum(r['attempted'] and not r['terminal'] for r in value['rows']),
            'unresolved_intents':sum(not r['terminal'] for r in value['rows']),
            'journal_ref':{'path':self.path.name,'sha256':sha(self.raw),'bytes':len(self.raw)},
            'worker_termination_proven':False, 'revocation_proven':False, 'deletion_admitted':False,
            'additional_http_requests':0, 'additional_sql_commands':0, 'additional_ipc_messages':0}


def workflow_receipt(composition, *, worker_terminated):
    """Called only after bridge reap; HTTP EOF is not identity, SQL, or revocation."""
    require(type(worker_terminated) is bool, 'workflow_reap')
    quota = composition.quota
    root = pathlib.Path(quota['root']).resolve(strict=True)
    sources = quota['manifest']['sources']
    names = [PREFIX + name for name in ('runtime_http.py', 'runtime_http.mjs',
        'runtime_dispatch.py', 'runtime_parent_workflow.py',
        'runtime_integral_workflow.mjs', 'runtime_recovery.py')]
    names.append('_offline/phase6e11/endchain_v1/auth_failure_transport.py')
    hashes = {}
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root), 'workflow_source_path')
        require(sha(path.read_bytes()) == sources.get(name), 'workflow_source')
        hashes[name] = sources[name]
    require(sha(pathlib.Path(__file__).read_bytes()) == hashes[PREFIX+'runtime_http.py'], 'loaded_source')
    dispatch = composition.workflow_dispatch.receipt()
    require(dispatch['format'] == 'quota-workflow-dispatch-v1'
            and dispatch['expected_calls'] == 72
            and dispatch['observed_attempts'] == len(dispatch['rows']) <= 72, 'workflow_dispatch')
    rows = []
    for index, row in enumerate(dispatch['rows']):
        require(row['index'] == index and row['dispatch_id'] == 'workflow_user_'+str(index)
                and row['dispatch_attempted'] is True and row['outcome'] in
                ('unknown_consumed','lost_response','response_received'), 'workflow_row')
        status = row.get('http_status')
        require(status is None if row['outcome'] != 'response_received'
                else type(status) is int and 100 <= status <= 599, 'workflow_status')
        rows.append({key:row[key] for key in ('index','dispatch_id','ticket','outcome')})
        rows[-1]['http_status'] = status
    return {'format':'case-workflow-http-terminal-v1',
        'run_id':quota['binding']['run_id'], 'binding_sha':quota['binding']['binding_sha'],
        'source_hashes':hashes, 'rows':rows, 'expected_calls':72,
        'observed_attempts':len(rows), 'pending':dispatch['pending'],
        'worker_terminated':worker_terminated,
        'all_responses_terminal':worker_terminated and dispatch['pending'] is None
            and all(row['outcome'] == 'response_received' for row in rows),
        'identity_verified':False, 'individual_sql_cost_observed':False,
        'revocation_proven':False, 'deletion_admitted':False, 'full_chain_admission':False,
        'additional_http_requests':0, 'additional_sql_commands':0, 'additional_ipc_messages':0}

