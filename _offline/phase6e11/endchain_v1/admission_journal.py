"""Durable per-dispatch local records with bounded, lossless artifact packaging."""
import base64
import hashlib
import json
import os
import pathlib
import re

MAX_RECORD = 1000000
MAX_CHUNK_RAW = 1000000
MAX_RECORDS = 1800
MAX_PACKAGED_BYTES = 2000000


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False, default=str)+'\n').encode('ascii')


def sha(value): return hashlib.sha256(value).hexdigest()


class Journal:
    def __init__(self, folder, publish, prefix):
        if not re.fullmatch('[a-z][a-z0-9-]{1,60}', prefix):
            raise ValueError('journal_prefix')
        self.folder = pathlib.Path(folder)
        self.folder.mkdir(exist_ok=False)
        self.publish, self.prefix = publish, prefix
        self.entries = {}
        self.sealed = False
        self.poisoned = False
        self.failure = None

    def _poison(self, stage, name, error):
        self.poisoned = True
        # Preserve the first failure without exporting exception text or paths.
        if self.failure is None:
            self.failure = {'stage': stage, 'record': name, 'error_class': type(error).__name__}

    def _inventory(self):
        if self.folder.is_symlink() or not self.folder.is_dir():
            raise ValueError('journal_directory_changed')
        names = set()
        for path in self.folder.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ValueError('journal_nonregular_record')
            names.add(path.name)
            if len(names) > MAX_RECORDS:
                raise ValueError('journal_inventory_capacity')
        if names != set(self.entries):
            raise ValueError('journal_unregistered_or_missing_records')

    def _read(self, name, expected):
        path = self.folder/name
        if path.is_symlink(): raise ValueError('journal_symlink')
        data = path.read_bytes()
        if len(data) != expected['bytes'] or sha(data) != expected['sha256']:
            raise ValueError('journal_changed_before_packaging')
        return data

    def save(self, name, value):
        if self.poisoned:
            raise ValueError('journal_poisoned')
        if self.sealed or not re.fullmatch(r'[A-Za-z0-9_.-]+\.json', name):
            raise ValueError('journal_name_or_closed')
        if name.casefold() in {n.casefold() for n in self.entries} or len(self.entries) >= MAX_RECORDS:
            raise ValueError('journal_duplicate_or_capacity')
        data = raw(value)
        if len(data) > MAX_RECORD:
            raise ValueError('journal_record_size')
        stage = 'open'
        try:
            with (self.folder/name).open('xb') as stream:
                stage = 'write'
                if stream.write(data) != len(data):
                    raise OSError('journal_short_write')
                stage = 'flush'
                stream.flush()
                stage = 'fsync'
                os.fsync(stream.fileno())
                stage = 'close'
            stage = 'register'
            self.entries[name] = {'sha256': sha(data), 'bytes': len(data)}
        except BaseException as error:
            self._poison(stage, name, error)
            # Partial or unconfirmed files are evidence, never removed or retried.
            raise

    def seal(self):
        if self.poisoned:
            raise ValueError('journal_poisoned')
        if self.sealed:
            raise ValueError('journal_already_sealed')
        # A packaging failure is not retried under the same artifact namespace.
        self.sealed = True
        try:
            return self._seal()
        except BaseException as error:
            self._poison('seal', None, error)
            raise

    def _seal(self):
        # Interrupted registration can leave a real file outside entries. Never
        # silently omit it, even in an otherwise zero-record journal.
        self._inventory()
        chunks, entries, size = {}, {}, 0
        def flush():
            if not entries: return
            name = self.prefix+'-%03d.json' % (len(chunks)+1)
            value = {'format': 'fmz-lossless-journal-chunk-v1', 'entries': dict(entries)}
            if len(raw(value)) > MAX_PACKAGED_BYTES: raise ValueError('journal_chunk_size')
            chunks[name] = {'canonical_content_sha256': sha(raw(value)), 'records': len(entries)}
            self.publish(name, value)
        for name, expected in self.entries.items():
            data = self._read(name, expected)
            if entries and (size+len(data) > MAX_CHUNK_RAW or len(entries) >= 64):
                flush(); entries = {}; size = 0
            entries[name] = {**expected, 'base64': base64.b64encode(data).decode('ascii')}
            size += len(data)
        flush()
        # A callback must not make the final inventory stale. Partial chunks
        # remain uncommitted evidence if this second check fails.
        self._inventory()
        for name, expected in self.entries.items():
            self._read(name, expected)
        index = {'format': 'fmz-lossless-journal-index-v1', 'records': dict(self.entries),
                 'chunks': chunks, 'complete': True, 'record_count': len(self.entries),
                 'raw_bytes': sum(v['bytes'] for v in self.entries.values()),
                 'hosted_calls': 0, 'contents_omitted': False}
        self.publish(self.prefix+'-index.json', index)
        return index


def verify(index, load_chunk):
    if (index.get('format') != 'fmz-lossless-journal-index-v1' or index.get('complete') is not True
            or index.get('contents_omitted') is not False or index.get('hosted_calls') != 0):
        raise ValueError('journal_index')
    found = {}
    for name, expected in index['chunks'].items():
        if not re.fullmatch(r'[a-z0-9-]+-\d{3}\.json', name): raise ValueError('journal_chunk_path')
        chunk = load_chunk(name)
        if len(raw(chunk)) > MAX_PACKAGED_BYTES or len(chunk.get('entries', {})) > 64:
            raise ValueError('journal_chunk_size')
        if sha(raw(chunk)) != expected['canonical_content_sha256'] or chunk.get('format') != 'fmz-lossless-journal-chunk-v1':
            raise ValueError('journal_chunk_changed')
        if len(chunk['entries']) != expected['records']: raise ValueError('journal_chunk_count')
        for key, entry in chunk['entries'].items():
            if not re.fullmatch(r'[A-Za-z0-9_.-]+\.json', key) or key.casefold() in {n.casefold() for n in found}:
                raise ValueError('journal_duplicate_or_path')
            if not isinstance(entry.get('base64'), str) or len(entry['base64']) > 4*((MAX_RECORD+2)//3):
                raise ValueError('journal_encoded_record_size')
            data = base64.b64decode(entry['base64'], validate=True)
            if len(data)>MAX_RECORD or len(data)!=entry['bytes'] or sha(data)!=entry['sha256']:
                raise ValueError('journal_record_changed')
            found[key] = {'bytes': len(data), 'sha256': sha(data)}
    if (found != index['records'] or len(found) != index['record_count'] or len(found)>MAX_RECORDS
            or sum(v['bytes'] for v in found.values()) != index['raw_bytes']):
        raise ValueError('journal_incomplete')
    return {'records': len(found), 'raw_bytes': index['raw_bytes'], 'complete': True}
