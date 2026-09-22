"""Local-only libpq single-row transport; no credentials, remote hosts or retries."""
import ctypes as C
import os
import pathlib
import time
from guard import Stop

BIN = pathlib.Path(os.environ.get('FMZ_LOCAL_PG_BIN', 'C:/Program Files/PostgreSQL/18/bin'))


class LocalDB:
    def __init__(self, port, ledger=None):
        if type(port) is not int or not 55000 <= port <= 59999:
            raise Stop('local_port_only')
        self.dll_directory = os.add_dll_directory(str(BIN)) if os.name == 'nt' else None
        self.lib = C.CDLL(str(BIN / ('libpq.dll' if os.name == 'nt' else 'libpq.so')))
        signatures = {
            'PQconnectdb': (C.c_void_p, [C.c_char_p]), 'PQstatus': (C.c_int, [C.c_void_p]),
            'PQfinish': (None, [C.c_void_p]), 'PQsendQuery': (C.c_int, [C.c_void_p, C.c_char_p]),
            'PQsetSingleRowMode': (C.c_int, [C.c_void_p]), 'PQconsumeInput': (C.c_int, [C.c_void_p]),
            'PQisBusy': (C.c_int, [C.c_void_p]), 'PQgetResult': (C.c_void_p, [C.c_void_p]),
            'PQresultStatus': (C.c_int, [C.c_void_p]), 'PQntuples': (C.c_int, [C.c_void_p]),
            'PQnfields': (C.c_int, [C.c_void_p]), 'PQgetisnull': (C.c_int, [C.c_void_p, C.c_int, C.c_int]),
            'PQgetvalue': (C.c_char_p, [C.c_void_p, C.c_int, C.c_int]),
            'PQcmdTuples': (C.c_char_p, [C.c_void_p]), 'PQclear': (None, [C.c_void_p]),
            'PQresultErrorField': (C.c_char_p, [C.c_void_p, C.c_int])}
        for name, (restype, argtypes) in signatures.items():
            function = getattr(self.lib, name)
            function.restype, function.argtypes = restype, argtypes
        # No DSN/environment credential fallback or selectable remote hostname.
        dsn = f"host=127.0.0.1 hostaddr=127.0.0.1 port={port} dbname=postgres user=postgres password='' connect_timeout=3 sslmode=disable application_name=fmz_offline_fingerprint"
        self.conn = self.lib.PQconnectdb(dsn.encode())
        if not self.conn or self.lib.PQstatus(self.conn) != 0:
            self.close()
            raise Stop('local_connection_failed')
        self.ledger = ledger
        self.queries = 0
        self.bytes_received = 0
        self.terminal_count = None

    def rows(self, sql, timeout=30):
        if self.ledger:
            self.ledger.reserve_query()
        self.queries += 1
        self.terminal_count = None
        start = time.monotonic()
        if not self.conn or self.lib.PQsendQuery(self.conn, sql.encode()) != 1:
            raise Stop('query_send')
        if self.lib.PQsetSingleRowMode(self.conn) != 1:
            raise Stop('single_row_mode')
        count, terminal = 0, False
        while True:
            while self.lib.PQisBusy(self.conn):
                if time.monotonic() - start > timeout:
                    self.close()
                    raise Stop('query_timeout')
                if self.lib.PQconsumeInput(self.conn) != 1:
                    raise Stop('query_transport')
                time.sleep(0.001)
            result = self.lib.PQgetResult(self.conn)
            if not result:
                break
            try:
                status = self.lib.PQresultStatus(result)
                if status == 9:  # PGRES_SINGLE_TUPLE
                    if terminal or self.lib.PQntuples(result) != 1:
                        raise Stop('stream_order')
                    row = []
                    for i in range(self.lib.PQnfields(result)):
                        v = None if self.lib.PQgetisnull(result, 0, i) else self.lib.PQgetvalue(result, 0, i).decode()
                        self.bytes_received += len(v.encode()) if v is not None else 0
                        row.append(v)
                    count += 1
                    yield row
                elif status in (1, 2):  # command or terminal tuples
                    if terminal:
                        raise Stop('multiple_statements_not_allowed')
                    terminal = True
                    raw = self.lib.PQcmdTuples(result).decode()
                    self.terminal_count = int(raw) if raw else 0
                    if status == 2 and self.terminal_count != count:
                        raise Stop('terminal_row_count')
                else:
                    state = self.lib.PQresultErrorField(result, ord('C'))
                    raise Stop('sqlstate_' + (state.decode() if state else 'unknown'))
            finally:
                self.lib.PQclear(result)
        if not terminal:
            raise Stop('missing_terminal')

    def query(self, sql, timeout=30):
        return list(self.rows(sql, timeout))

    def close(self):
        if getattr(self, 'conn', None):
            self.lib.PQfinish(self.conn)
            self.conn = None
