"""Exact legacy table-hash reducer, streaming row digests into bounded local sort runs."""
import hashlib
import heapq
import json
import pathlib
import re
import time
from guard import Stop, digest, save

ALGORITHM = 'fmz-legacy-sha256-multiset-pinned-v1'
SETTINGS = {'TimeZone': 'UTC', 'DateStyle': 'ISO, YMD', 'IntervalStyle': 'postgres',
            'extra_float_digits': '3', 'bytea_output': 'hex', 'client_encoding': 'UTF8',
            'lc_numeric': 'C', 'lc_monetary': 'C', 'lc_time': 'C', 'search_path': 'pg_catalog',
            'max_parallel_workers_per_gather': '0', 'work_mem': '2184kB',
            'statement_timeout': '30000', 'lock_timeout': '3000',
            'idle_in_transaction_session_timeout': '30000'}
SCHEMA_SQL = """select n.nspname,c.relname,a.attname,format_type(a.atttypid,a.atttypmod),
a.attnotnull::text,a.attnum::text,coalesce(coll.collname,'')
from pg_class c join pg_namespace n on n.oid=c.relnamespace
join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
left join pg_collation coll on coll.oid=a.attcollation
where c.relkind in ('r','p') and n.nspname not in ('pg_catalog','information_schema')
order by n.nspname collate "C",c.relname collate "C",a.attnum"""
ROW_HASH = "encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex')"
END_HASH = "encode(sha256(convert_to(coalesce(string_agg(h,',' order by h),''),'UTF8')),'hex')"


def identifier(value):
    if not re.fullmatch('[a-zA-Z_][a-zA-Z0-9_]*', value):
        raise Stop('identifier')
    return '"' + value + '"'


def ids(values):
    if any(not re.fullmatch('[0-9a-f-]{36}', x) for x in values):
        raise Stop('identity_format')
    return ','.join("'" + x + "'" for x in sorted(set(values))) or 'null'


def predicates(name, columns, selection):
    schema, table = name.split('.')
    exact, extra = selection['accounts'], selection['controls']
    all_ids, control_ids = ids(list(exact.values()) + extra), ids(extra)
    keep = 'true'
    if schema == 'fmz6e11_private' or name == 'cron.job_run_details':
        keep = 'false'
    if schema == 'auth':
        if table == 'users':
            keep = 'id not in(' + all_ids + ')'
        elif 'user_id' in columns:
            keep = 'user_id is null or user_id::text not in(' + all_ids + ')'
        elif table == 'mfa_amr_claims':
            keep = 'session_id not in(select id from auth.sessions where user_id in(' + all_ids + '))'
        elif table == 'audit_log_entries':
            keep = "coalesce(payload->>'actor_id','') not in(" + all_ids + ')'
    if schema == 'public' and extra:
        if table == 'profiles':
            keep = 'id not in(' + control_ids + ')'
        elif 'user_id' in columns:
            keep = 'user_id is null or user_id::text not in(' + control_ids + ')'
    result = {'protected': keep}
    if schema == 'auth' and ('user_id' in columns or table == 'users'):
        for role, uid in sorted(selection['known'].items()):
            identifier(role)
            result['actor_' + role] = ('id' if table == 'users' else 'user_id') + '::text=' + ids([uid])
    if schema == 'fmz6e11_private':
        windows = ids(selection['windows'])
        result['retained'] = ('id in(' + windows + ')' if table == 'windows' else
            'window_id in(' + windows + ')' if 'window_id' in columns else
            'workspace_id in(select id from fmz6e11_private.workspaces where window_id in(' + windows + '))'
            if 'workspace_id' in columns else 'true')
    return result


def plan(schema, selection, expected):
    tables = {}
    for s, t, column, *_ in schema:
        tables.setdefault(s + '.' + t, []).append(column)
    if sorted(tables) != sorted(expected) or len(tables) != 143:
        raise Stop('inventory_mismatch')
    return [{'name': n, 'cohorts': predicates(n, tables[n], selection)} for n in sorted(tables)]


def stream_sql(plans):
    parts = []
    for i, p in enumerate(plans):
        table = '.'.join(identifier(x) for x in p['name'].split('.'))
        flags = "||".join("(case when (" + x + ") then '1' else '0' end)" for x in p['cohorts'].values())
        parts.append(f"select {i}::text,{ROW_HASH},({flags}) from {table} t")
    return ' union all '.join(parts)


def legacy_sql(plans):
    parts = []
    for i, p in enumerate(plans):
        table = '.'.join(identifier(x) for x in p['name'].split('.'))
        fields, columns = [], []
        for n, (name, expression) in enumerate({'raw': 'true', **p['cohorts']}.items()):
            columns.append(f'({expression}) c{n}')
            aggregate = f"encode(sha256(convert_to(coalesce(string_agg(h,',' order by h) filter(where c{n}),''),'UTF8')),'hex')"
            fields.append(f"'{name}',jsonb_build_object('rows',count(*) filter(where c{n}),'sha256',{aggregate})")
        parts.append(f"select {i}::text,jsonb_build_object({','.join(fields)})::text from "
                     f"(select {ROW_HASH} h,{','.join(columns)} from {table} t) q")
    return ' union all '.join(parts)


class Reducer:
    MAX_ROWS = 1000000
    MAX_BYTES = 128 * 1024 * 1024
    MAX_CHUNKS = 64

    def __init__(self, plans, directory, chunk_rows=16384):
        if not 1 <= chunk_rows <= 16384:
            raise Stop('chunk_limit')
        self.plans = plans
        self.path = pathlib.Path(directory)
        self.path.mkdir(exist_ok=False)
        self.chunk_rows = chunk_rows
        self.buffer, self.chunks = [], []
        self.rows = self.written = self.read = 0
        self.started = time.monotonic()

    def add(self, row):
        if time.monotonic() - self.started > 120:
            raise Stop('cycle_timeout')
        if len(row) != 3 or not all(isinstance(x, str) for x in row):
            raise Stop('row_shape')
        index, h, flags = row
        if not index.isdigit() or not 0 <= int(index) < len(self.plans):
            raise Stop('table_index')
        if not re.fullmatch('[0-9a-f]{64}', h) or not re.fullmatch('[01]+', flags):
            raise Stop('hash_or_flag')
        if len(flags) != len(self.plans[int(index)]['cohorts']):
            raise Stop('cohort_count')
        self.rows += 1
        if self.rows > self.MAX_ROWS:
            raise Stop('row_budget')
        self.buffer.append(f'{int(index):04d}:{h}:{flags}\n'.encode())
        if len(self.buffer) >= self.chunk_rows:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        if len(self.chunks) >= self.MAX_CHUNKS:
            raise Stop('chunk_budget')
        self.buffer.sort()
        data = b''.join(self.buffer)
        if self.written + len(data) > self.MAX_BYTES:
            raise Stop('byte_budget')
        file = self.path / f'chunk-{len(self.chunks):03d}.hashes'
        with file.open('xb') as stream:
            stream.write(data)
        self.chunks.append((file, hashlib.sha256(data).hexdigest(), len(data)))
        self.written += len(data)
        self.buffer.clear()

    def finish(self, acknowledged_rows):
        if type(acknowledged_rows) is not int or acknowledged_rows != self.rows:
            raise Stop('incomplete_stream')
        self.flush()
        hashes, counts = [], []
        for p in self.plans:
            names = ['raw', *p['cohorts']]
            hashes.append({k: hashlib.sha256() for k in names})
            counts.append(dict.fromkeys(names, 0))
        streams = []
        try:
            def verified_lines(stream, expected_sha, expected_size):
                check, length = hashlib.sha256(), 0
                for line in stream:
                    check.update(line)
                    length += len(line)
                    if not re.fullmatch(rb'[0-9]{4}:[0-9a-f]{64}:[01]+\n', line):
                        raise Stop('chunk_corrupt')
                    yield line
                if length != expected_size or check.hexdigest() != expected_sha:
                    raise Stop('chunk_corrupt')
            iterators = []
            for file, sha, size in self.chunks:
                stream = file.open('rb')
                streams.append(stream)
                iterators.append(verified_lines(stream, sha, size))
            merged = 0
            for line in heapq.merge(*iterators):
                if time.monotonic() - self.started > 120:
                    raise Stop('cycle_timeout')
                self.read += len(line)
                index, h, flags = line.rstrip(b'\n').split(b':')
                i = int(index)
                selected = ['raw'] + [k for k, bit in zip(self.plans[i]['cohorts'], flags) if bit == ord('1')]
                for name in selected:
                    if counts[i][name]:
                        hashes[i][name].update(b',')
                    hashes[i][name].update(h)
                    counts[i][name] += 1
                merged += 1
            if merged != self.rows:
                raise Stop('merge_count')
        finally:
            for stream in streams:
                stream.close()
        return [{'name': p['name'], 'cohorts': {k: {'rows': counts[i][k], 'sha256': h.hexdigest()}
                 for k, h in hashes[i].items()}} for i, p in enumerate(self.plans)]


def configure(db):
    db.query('begin isolation level repeatable read read only')
    # Separate statements are counted; set_config is session-local to this transaction.
    expressions = ["set_config('" + k + "','" + v + "',true)" for k, v in SETTINGS.items()]
    db.query('select ' + ','.join(expressions))


def collect(db, ledger, directory, expected, selection, method='stream'):
    ledger.begin_cycle()
    directory = pathlib.Path(directory)
    directory.mkdir(exist_ok=False)
    started, start_queries, start_bytes = time.monotonic(), db.queries, db.bytes_received
    try:
        ledger.phase = 'configure'
        configure(db)
        ledger.phase = 'schema'
        schema = db.query(SCHEMA_SQL)
        plans = plan(schema, selection, expected)
        metadata = db.query("select current_setting('server_version_num'),current_setting('server_encoding'),datcollate from pg_database where datname=current_database()")
        if metadata[0][1] != 'UTF8':
            raise Stop('encoding')
        ledger.phase = 'row_stream'
        if method == 'stream':
            reducer = Reducer(plans, directory / 'chunks')
            for row in db.rows(stream_sql(plans)):
                reducer.add(row)
            ledger.phase = 'terminal_and_sort'
            tables = reducer.finish(db.terminal_count)
            counters = {'local_sort_write_bytes': reducer.written, 'local_sort_read_bytes': reducer.read,
                        'local_sort_files': len(reducer.chunks), 'max_buffer_records': reducer.chunk_rows}
        elif method == 'legacy':
            tables = [{'name': p['name'], 'cohorts': {}} for p in plans]
            for index, cohorts in db.rows(legacy_sql(plans)):
                tables[int(index)]['cohorts'] = json.loads(cohorts)
            counters = {'local_sort_write_bytes': 0, 'local_sort_read_bytes': 0, 'local_sort_files': 0}
        else:
            raise Stop('unknown_method')
        ledger.phase = 'transaction_finish'
        db.query('commit')
        identity = {'status': 'complete', 'algorithm': ALGORITHM, 'schema_sha256': digest(schema),
                    'selection_sha256': digest(selection), 'canonical': {'settings': SETTINGS,
                    'postgres_version': metadata[0][0], 'source_collation': metadata[0][2]},
                    'tables': tables}
        ledger.phase = 'identity_saved'
        save(directory / 'identity.json', identity)
        ledger.end_cycle(directory / 'identity.json')
        metrics = {**counters, 'elapsed_seconds': time.monotonic()-started,
                   'query_commands': db.queries-start_queries, 'result_payload_bytes': db.bytes_received-start_bytes,
                   'full_cycles': 1, 'retries': 0}
        save(directory / 'metrics.json', metrics)
        return identity, metrics
    except BaseException as error:
        # Closing aborts this read-only transaction; no hosted cleanup exists here.
        db.close()
        code = str(error) if isinstance(error, Stop) else type(error).__name__
        ledger.fail(code)
