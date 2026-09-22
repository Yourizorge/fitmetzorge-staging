"""Immutable offline admission ledger; no automatic retries or stale-lock takeover."""
import hashlib
import json
import os
import pathlib
import tempfile
import time
import uuid


class Stop(RuntimeError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def save(path, value):
    path = pathlib.Path(path)
    if os.name == 'nt' and not str(path).startswith(chr(92) * 2 + '?'):
        path = pathlib.Path(chr(92) * 2 + '?' + chr(92) + str(path.resolve()))
    data = encoded(value)
    temporary = path.with_name(path.name + '.pending-' + uuid.uuid4().hex)
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if os.name == 'nt':
        os.rename(temporary, path)
    else:
        os.link(temporary, path)
    if path.read_bytes() != data:
        raise Stop('evidence_readback')
    return hashlib.sha256(data).hexdigest()


class Ledger:
    MAX_FULL = 3
    MAX_QUERIES = 128
    MAX_SECONDS = 900
    MAX_TARGETED = 0  # No independently proven write coverage yet.

    def __init__(self, directory, lock_scope=None):
        self.path = pathlib.Path(directory)
        self.path.mkdir(parents=True, exist_ok=True)
        project = str(pathlib.Path(__file__).resolve().parents[3]).casefold()
        shared = pathlib.Path(lock_scope) if lock_scope is not None else pathlib.Path(tempfile.gettempdir()) / ('fmz-fingerprint-single-' + hashlib.sha256(project.encode()).hexdigest()[:16])
        shared.mkdir(parents=True, exist_ok=True)
        self.lock = shared / 'active.lock'
        try:
            self.fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise Stop('concurrent_or_interrupted_run') from None
        self.run_id = str(uuid.uuid4())
        os.write(self.fd, self.run_id.encode())
        os.fsync(self.fd)
        self.started = time.monotonic()
        self.active = False
        self.pending = None
        self.phase = 'admission'
        try:
            events = [json.loads(p.read_text()) for p in sorted(self.path.glob('event-*.json'))]
            self.previous = None
            for i, event in enumerate(events, 1):
                if event.get('sequence') != i or event.get('previous') != self.previous:
                    raise Stop('ledger_chain')
                self.previous = digest(event)
            self.number = len(events)
            self.full = sum(x['kind'] == 'full_reserved' for x in events)
            self.queries = sum(x['kind'] == 'query_reserved' for x in events)
            self.halted = any(x['kind'] == 'halt' for x in events)
            if self.halted:
                raise Stop('retained_halt')
            self.event('run_started')
        except BaseException:
            self.close()
            raise

    def event(self, kind, **data):
        self.number += 1
        event = {'run_id': self.run_id, 'kind': kind, 'phase': self.phase,
                 'time_ns': time.time_ns(), 'sequence': self.number,
                 'previous': self.previous, **data}
        save(self.path / f'event-{self.number:06d}.json', event)
        self.previous = digest(event)

    def check(self):
        if self.halted:
            raise Stop('retained_halt')
        if time.monotonic() - self.started > self.MAX_SECONDS:
            self.fail('run_deadline')

    def fail(self, code):
        if not self.halted:
            self.halted = True
            self.event('halt', code=code, cleanup_allowed=False, next_step_allowed=False)
        raise Stop(code)

    def reserve_query(self):
        self.check()
        if self.queries >= self.MAX_QUERIES:
            self.fail('query_budget')
        self.queries += 1
        self.event('query_reserved', used=self.queries)

    def begin_cycle(self):
        self.check()
        if self.active:
            self.fail('duplicate_cycle')
        if self.full >= self.MAX_FULL:
            self.fail('full_cycle_budget')
        self.full += 1
        self.active = True
        self.phase = 'cycle_started'
        self.event('full_reserved', used=self.full)

    def end_cycle(self, identity_path):
        if not self.active:
            self.fail('cycle_not_active')
        value = json.loads(pathlib.Path(identity_path).read_text())
        if value.get('status') != 'complete' or len(value.get('tables', [])) != 143:
            self.fail('incomplete_identity')
        self.event('cycle_complete', identity_sha256=digest(value))
        self.active = False
        self.phase = 'idle'

    def targeted(self):
        self.fail('write_coverage_not_proven')

    def before(self, identity):
        self.check()
        if self.pending is not None or self.active:
            self.fail('previous_pair_not_validated')
        value = json.loads(pathlib.Path(identity).read_text())
        if value.get('status') != 'complete' or len(value.get('tables', [])) != 143:
            self.fail('invalid_before')
        self.pending = value
        self.phase = 'before_saved'
        self.event(self.phase, sha256=digest(value))

    def start_action(self):
        if self.phase != 'before_saved':
            self.fail('phase_order')
        self.phase = 'action_started'
        self.event(self.phase)

    def confirm_action(self, receipt):
        if self.phase != 'action_started':
            self.fail('phase_order')
        self.phase = 'action_confirmed'
        self.event(self.phase, receipt_sha256=digest(receipt))

    def after(self, identity, allowed_raw=()):
        if self.phase != 'action_confirmed':
            self.fail('phase_order')
        value = json.loads(pathlib.Path(identity).read_text())
        if value.get('status') != 'complete':
            self.fail('invalid_after')
        self.phase = 'after_saved'
        self.event(self.phase, sha256=digest(value))
        old = self.pending
        for key in ('algorithm', 'schema_sha256', 'selection_sha256', 'canonical'):
            if old.get(key) != value.get(key):
                self.fail('pair_contract_changed')
        if [x['name'] for x in old['tables']] != [x['name'] for x in value['tables']]:
            self.fail('pair_inventory_changed')
        for a, b in zip(old['tables'], value['tables']):
            if a['cohorts']['protected'] != b['cohorts']['protected']:
                self.fail('protected_drift')
            if a != b and a['name'] not in allowed_raw:
                self.fail('unexplained_raw_drift')
        self.phase = 'pair_validated'
        self.event(self.phase)
        self.pending = None
        self.phase = 'next_step_allowed'
        self.event(self.phase)

    def cleanup_allowed(self):
        self.check()
        if self.pending is not None or self.active or self.phase != 'next_step_allowed':
            self.fail('cleanup_without_valid_pair')
        return True

    def close(self):
        if getattr(self, 'fd', None) is not None:
            if (self.active or self.pending is not None) and not getattr(self, 'halted', True):
                self.halted = True
                self.event('halt', code='interrupted_step', cleanup_allowed=False, next_step_allowed=False)
            os.close(self.fd)
            self.fd = None
            if self.lock.read_text() == self.run_id:
                self.lock.unlink()
