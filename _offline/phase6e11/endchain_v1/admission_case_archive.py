"""Lossless explicit case references in flat CI artifacts; no recursive export."""
import base64
import hashlib
import json
import os
import pathlib
import re

INDEX = 'case-original-index.json'
FORMAT = 'fmz-case-original-archive-v1'
MAX_FILES = 4096
MAX_RECORD = 2000000
MAX_RAW = 16000000
MAX_MEMBER = 2000000
CHUNK_RAW = 1000000


def require(value, code):
    if not value:
        raise ValueError('case_archive_' + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def object_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate_json_key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs)
    require(type(value) is dict, 'object_required')
    return value


def references(values):
    require(type(values) is list and 0 < len(values) <= MAX_FILES, 'reference_count')
    result, aliases = {}, set()
    for value in values:
        require(type(value) is dict and {'path', 'sha256'} <= set(value)
                and set(value) <= {'path', 'sha256', 'bytes', 'size'}, 'reference_shape')
        name = value['path']
        require(type(name) is str and len(name) <= 240
                and re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_./-]*\.(json|txt)', name)
                and all(p not in ('', '.', '..') for p in name.split('/'))
                and all(not p.endswith('.') and not re.fullmatch(
                    r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.IGNORECASE)
                    for p in name.split('/'))
                and len(name.split('/')) <= 4
                and not name.startswith('case-original-'), 'reference_path')
        require(name.casefold() not in aliases, 'reference_alias')
        require(type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['sha256']),
                'reference_digest')
        for key in ('bytes', 'size'):
            require(key not in value or type(value[key]) is int
                    and 0 < value[key] <= MAX_RECORD, 'reference_size')
        require(not {'bytes', 'size'} <= set(value) or value['bytes'] == value['size'],
                'reference_size_conflict')
        result[name] = dict(value)
        aliases.add(name.casefold())
    return result


def record(raw, reference):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_RECORD, 'record_size')
    require(sha(raw) == reference['sha256'], 'record_digest')
    require(all(key not in reference or reference[key] == len(raw) for key in ('bytes', 'size')),
            'record_length')


def read_original(root, reference):
    path = root.joinpath(*reference['path'].split('/'))
    require(path.resolve(strict=True).is_relative_to(root), 'source_escape')
    for part in (path, *path.parents):
        require(not part.is_symlink() and not (hasattr(part, 'is_junction') and part.is_junction()),
                'source_link')
        if part == root:
            break
    require(path.is_file() and path.stat().st_size <= MAX_RECORD, 'source_size')
    raw = path.read_bytes()
    record(raw, reference)
    return raw


def publish(root, name, value):
    raw = encoded(value)
    require(len(raw) <= MAX_MEMBER, 'member_size')
    # Exclusive publication deliberately leaves a failed/partial file in place.
    with (root / name).open('xb') as stream:
        require(stream.write(raw) == len(raw), 'short_write')
        stream.flush()
        os.fsync(stream.fileno())
    require((root / name).read_bytes() == raw, 'publication_readback')
    return {'path': name, 'sha256': sha(raw), 'bytes': len(raw)}


def pack(gate, original_refs):
    refs = references(original_refs)
    root = pathlib.Path(gate.out).resolve(strict=True)
    require(not any(root.glob('case-original-*')), 'already_attempted')
    entries, chunks, total, size = {}, {}, 0, 0
    records = {}
    def flush():
        if not entries:
            return
        name = 'case-original-%03d.json' % (len(chunks) + 1)
        ref = publish(root, name, {'format': FORMAT, 'entries': dict(entries)})
        chunks[name] = {**ref, 'records': len(entries)}
    for name in sorted(refs):
        raw = read_original(root, refs[name])
        total += len(raw)
        require(total <= MAX_RAW, 'total_raw_size')
        value = {'path': name, 'sha256': sha(raw), 'bytes': len(raw)}
        records[name] = value
        # Large original ledgers stay intact logically but fit flat 2 MB artifacts.
        part_size = min(CHUNK_RAW, 750000)
        for offset in range(0, len(raw), part_size):
            part = raw[offset:offset+part_size]
            if entries and (size + len(part) > CHUNK_RAW or len(entries) >= 64 or name in entries):
                flush()
                entries, size = {}, 0
            entries[name] = {'path': name, 'sha256': sha(raw), 'total_bytes': len(raw),
                             'offset': offset, 'bytes': len(part),
                             'base64': base64.b64encode(part).decode('ascii')}
            size += len(part)
    flush()
    for name in refs:
        read_original(root, refs[name])
    index = {'format': FORMAT, 'complete': True, 'records': records,
             'chunks': chunks, 'raw_bytes': total, 'record_count': len(records),
             'explicit_references_only': True, 'hosted_calls': 0}
    reference = publish(root, INDEX, index)
    payloads = {name: (root / name).read_bytes() for name in (*chunks, INDEX)}
    verify(payloads, reference, original_refs)
    return reference


def verify(payloads, index_ref, original_refs):
    """Independent ZIP-side readback, preserving exact original bytes and paths."""
    refs = references(original_refs)
    require(type(index_ref) is dict and set(index_ref) == {'path', 'sha256', 'bytes'}
            and index_ref['path'] == INDEX and type(index_ref['bytes']) is int
            and 0 < index_ref['bytes'] <= MAX_MEMBER, 'index_reference')
    raw = payloads[INDEX]
    require(type(raw) is bytes and len(raw) == index_ref['bytes']
            and sha(raw) == index_ref['sha256'], 'index_digest')
    index = object_json(raw)
    require(set(index) == {'format', 'complete', 'records', 'chunks', 'raw_bytes',
                          'record_count', 'explicit_references_only', 'hosted_calls'}
            and index['format'] == FORMAT and index['complete'] is True
            and index['explicit_references_only'] is True
            and type(index['hosted_calls']) is int and index['hosted_calls'] == 0,
            'index_contract')
    require(type(index['chunks']) is dict and 0 < len(index['chunks']) <= MAX_FILES
            and set(index['records']) == set(refs), 'index_inventory')
    expected_chunks = ['case-original-%03d.json' % n for n in range(1, len(index['chunks']) + 1)]
    require(sorted(index['chunks']) == expected_chunks
            and {n for n in payloads if n.startswith('case-original-')} == set(expected_chunks) | {INDEX},
            'chunk_inventory')
    found, normalized, total = {}, {}, 0
    fragments, declared = {}, {}
    for name in expected_chunks:
        expected = index['chunks'][name]
        require(type(expected) is dict and set(expected) == {'path', 'sha256', 'bytes', 'records'}
                and expected['path'] == name and type(expected['bytes']) is int
                and 0 < expected['bytes'] <= MAX_MEMBER, 'chunk_reference')
        raw = payloads[name]
        require(type(raw) is bytes and len(raw) == expected['bytes']
                and sha(raw) == expected['sha256'], 'chunk_digest')
        value = object_json(raw)
        require(set(value) == {'format', 'entries'} and value['format'] == FORMAT
                and type(value['entries']) is dict and type(expected['records']) is int
                and 0 < len(value['entries']) == expected['records'] <= 64, 'chunk_contract')
        for path, item in value['entries'].items():
            require(path in refs and type(item) is dict
                    and set(item) == {'path', 'sha256', 'total_bytes', 'offset', 'bytes', 'base64'}
                    and item['path'] == path and type(item['bytes']) is int
                    and 0 < item['bytes'] <= CHUNK_RAW and type(item['offset']) is int
                    and item['offset'] >= 0 and type(item['total_bytes']) is int
                    and 0 < item['total_bytes'] <= MAX_RECORD
                    and type(item['base64']) is str and len(item['base64']) <= 4 * ((CHUNK_RAW+2)//3),
                    'entry_contract')
            data = base64.b64decode(item['base64'], validate=True)
            require(len(data) == item['bytes'] and item['sha256'] == refs[path]['sha256'], 'fragment_length_or_digest')
            previous = fragments.get(path, b'')
            require(item['offset'] == len(previous) and len(previous)+len(data) <= item['total_bytes'],
                    'fragment_order')
            current = {'path': path, 'sha256': item['sha256'], 'bytes': item['total_bytes']}
            require(path not in declared or declared[path] == current, 'fragment_identity')
            declared[path] = current
            fragments[path] = previous + data
            total += len(data)
            require(total <= MAX_RAW, 'total_raw_size')
    for path, data in fragments.items():
        record(data, refs[path])
        record(data, declared[path])
        found[path] = data
        normalized[path] = {'path': path, 'sha256': sha(data), 'bytes': len(data)}
        require(path not in payloads or payloads[path] == data, 'flat_original_conflict')
    require(normalized == index['records'] and set(found) == set(refs)
            and type(index['record_count']) is int and index['record_count'] == len(found)
            and type(index['raw_bytes']) is int and index['raw_bytes'] == total, 'incomplete')
    return found
