"""Fixed, read-only real PG17 probe. Private DSN enters only through stdin."""
import json
import os
import pathlib
import sys

CASES = ('readonly', 'statement_timeout', 'lost_result')


def main():
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    from psycopg.rows import dict_row
    if sys.platform != 'linux' or os.environ.get('GITHUB_ACTIONS') != 'true':
        return 2
    raw = sys.stdin.buffer.readline(65537)
    if len(raw) > 65536:
        return 2
    payload = json.loads(raw)
    if set(payload) != {'dsn', 'case'} or payload['case'] not in CASES:
        return 2
    params = conninfo_to_dict(payload['dsn'])
    if (params.get('host') != '127.0.0.1' or params.get('hostaddr', '127.0.0.1') != '127.0.0.1'
            or params.get('dbname') != 'postgres' or params.get('sslmode') != 'verify-full'
            or not pathlib.Path(params.get('sslrootcert', '')).is_file()
            or any(k in params for k in ('service', 'servicefile'))
            or any(os.environ.get(k) for k in ('PGSERVICE', 'PGSERVICEFILE'))
            or os.environ.get('PGHOSTADDR', '127.0.0.1') != '127.0.0.1'):
        return 2
    commands = 0
    result = {'case': payload['case'], 'pg17_tls_readonly': False, 'query_confirmed': False,
              'sqlstate': None, 'rollback_confirmed': False, 'explicit_commands': 0,
              'connection_closed': False, 'libpq_version': psycopg.pq.version(),
              'implicit_native_sql_bound': None, 'full_chain_admission': False}
    db = psycopg.connect(payload['dsn'], hostaddr='127.0.0.1', autocommit=True,
        prepare_threshold=None, row_factory=dict_row, connect_timeout=5,
        options='-c statement_timeout=5000 -c lock_timeout=1000')
    payload['dsn'] = None
    try:
        commands += 1; db.execute('BEGIN READ ONLY')
        commands += 1
        row = db.execute("SELECT current_setting('server_version_num')::int version, "
            "current_setting('transaction_read_only')='on' readonly, ssl "
            'FROM pg_stat_ssl WHERE pid=pg_backend_pid()').fetchone()
        if not (row and row['version'] // 10000 == 17 and row['readonly'] is True and row['ssl'] is True):
            raise ValueError('local_attestation')
        result['pg17_tls_readonly'] = True
        try:
            commands += 1
            value = db.execute('SELECT pg_sleep(6)' if payload['case'] == 'statement_timeout' else 'SELECT 1 value').fetchone()
            result['query_confirmed'] = payload['case'] != 'statement_timeout' and value == {'value': 1}
        except psycopg.Error as error:
            if payload['case'] != 'statement_timeout' or error.sqlstate != '57014':
                raise
            result['sqlstate'] = '57014'
    finally:
        try:
            commands += 1; db.execute('ROLLBACK'); result['rollback_confirmed'] = True
        finally:
            db.close(); result['connection_closed'] = db.closed
    result['explicit_commands'] = commands
    if payload['case'] != 'lost_result':
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')))
        sys.stdout.flush()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        # Never expose a private DSN, exception message, SQL or row data.
        raise SystemExit(2) from None
