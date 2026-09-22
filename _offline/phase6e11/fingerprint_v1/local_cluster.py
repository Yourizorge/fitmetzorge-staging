"""Disposable local PostgreSQL only. Retain all new files, always stop its process."""
import ctypes as C
import json
import os
import pathlib
import socket
import subprocess
import tempfile
import time
from pq import BIN, LocalDB
from guard import Stop

HERE = pathlib.Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / 'inventory.json').read_text())['tables']


def uid(n):
    return '62000000-0000-4000-8000-' + f'{n:012d}'


SELECTION = {'accounts': {'a_member': uid(1), 'a_trainer': uid(2), 'b_member': uid(3)},
             'controls': [uid(4)], 'known': {'a_member': uid(1), 'a_trainer': uid(2),
             'b_member': uid(3), 'control': uid(4)}, 'windows': [uid(10)]}


def execute(name, args, timeout=60):
    r = subprocess.run([str(BIN / (name + '.exe')), *args], capture_output=True,
                       timeout=timeout, creationflags=0x08000000 if os.name == 'nt' else 0)
    if r.returncode:
        raise Stop('local_' + name + '_failed')
    return r


class Cluster:
    def __init__(self):
        self.path = pathlib.Path(tempfile.mkdtemp(prefix='fmz-fingerprint-offline-'))
        self.data = self.path / 'data'
        self.process = None
        for port in range(56110, 56140):
            with socket.socket() as s:
                try:
                    s.bind(('127.0.0.1', port))
                    self.port = port
                    break
                except OSError:
                    continue
        else:
            raise Stop('local_port_unavailable')

    def start(self):
        execute('initdb', ['-D', str(self.data), '-A', 'trust', '-U', 'postgres', '--locale=C', '--encoding=UTF8'])
        self.log = (self.path / 'postgres.log').open('xb')
        self.process = subprocess.Popen([str(BIN / 'postgres.exe'), '-D', str(self.data),
            '-h', '127.0.0.1', '-p', str(self.port), '-c', 'shared_buffers=64MB',
            '-c', 'log_temp_files=0', '-c', 'logging_collector=off', '-c', 'track_io_timing=on'],
            stdout=subprocess.DEVNULL, stderr=self.log,
            creationflags=0x08000000 if os.name == 'nt' else 0)
        for _ in range(60):
            try:
                db = LocalDB(self.port)
                if self.process.poll() is not None:
                    raise Stop('local_server_exited')
                actual = db.query("select current_setting('data_directory')")[0][0]
                if pathlib.Path(actual).resolve() != self.data.resolve():
                    db.close()
                    raise Stop('local_cluster_identity')
                return db
            except Stop:
                time.sleep(0.1)
        raise Stop('local_start_timeout')

    def stop(self):
        if self.process:
            execute('pg_ctl', ['-D', str(self.data), '-m', 'fast', '-w', 'stop'])
            self.process.wait(timeout=20)
            self.log.close()

    def fixture(self, db):
        for schema in sorted({x.split('.')[0] for x in EXPECTED} - {'public'}):
            db.query(f'create schema "{schema}"')
        for name in EXPECTED:
            schema, table = name.split('.')
            # Deliberately no key on most tables: duplicate multiplicity is required.
            special = ('id uuid,payload jsonb' if name == 'auth.audit_log_entries' else
                       'id uuid,session_id uuid' if name == 'auth.mfa_amr_claims' else
                       'id uuid,user_id uuid' if schema == 'auth' or name == 'public.profiles' else
                       'id uuid,window_id uuid,workspace_id uuid,user_id uuid')
            db.query(f'create table "{schema}"."{table}" ({special},n numeric(16,4),f double precision,'
                     'j json,jb jsonb,a integer[],stamp timestamptz,naive timestamp,span interval,'
                     'word text,blob bytea,flag boolean)')
        db.query("insert into auth.users(id,user_id,word) values " +
                 ','.join(f"('{uid(i)}','{uid(i)}','synthetic')" for i in (1,2,3,4,5)))
        db.query(f"insert into auth.sessions(id,user_id) values ('{uid(101)}','{uid(1)}'),('{uid(105)}','{uid(5)}')")
        db.query(f"insert into auth.mfa_amr_claims(id,session_id) values ('{uid(201)}','{uid(101)}'),('{uid(205)}','{uid(105)}')")
        db.query(f"""insert into auth.audit_log_entries(id,payload) values
        ('{uid(301)}','{{"actor_id":"{uid(1)}"}}'),('{uid(305)}','{{"actor_id":"{uid(5)}"}}')""")
        db.query(f"insert into public.profiles(id,user_id) values ('{uid(4)}','{uid(4)}'),('{uid(5)}','{uid(5)}')")
        db.query(f"insert into fmz6e11_private.windows(id,window_id) values ('{uid(10)}','{uid(10)}'),('{uid(11)}','{uid(11)}')")
        db.query(f"insert into fmz6e11_private.workspaces(id,window_id) values ('{uid(20)}','{uid(10)}')")
        db.query(f"insert into fmz6e11_private.plans(id,window_id,workspace_id) values ('{uid(30)}','{uid(10)}','{uid(20)}')")
        db.query(r"""insert into public.foods(n,f,j,jb,a,stamp,naive,span,word,blob,flag) values
        (1.2300,0.1,'{"b":2,"a":1,"a":3}','{"a":3,"b":2}',array[1,null,0],
        '2026-03-29 01:30:00+00','2026-03-29 01:30:00','1 day 02:03:04',
        U&'caf\00e9 \4f60\597d',decode('0001ff','hex'),true),
        (0,-0.0,'null','null',array[]::int[],'infinity','-infinity','-1 month',U&'cafe\0301',''::bytea,false),
        (null,'NaN',null,null,null,null,null,null,null,null,null)""")
        db.query('insert into public.foods select * from public.foods')
        db.query("insert into public.food_logs(id,user_id,word) values "
                 f"('{uid(1)}','{uid(4)}','excluded control'),('{uid(2)}',null,'null owner'),"
                 f"('{uid(3)}','{uid(5)}','protected synthetic')")
        db.query("insert into cron.job_run_details(word) values ('synthetic scheduled metadata')")

    def enlarge(self, db):
        for table, count in [('nutrition_off_products', 25000), ('nutrition_off_product_names', 75000)]:
            db.query(f"""insert into public.{table}(n,f,jb,a,stamp,word,blob)
            select g,0.125,jsonb_build_object('synthetic',g),array[g,0,null],
            '2026-01-01 00:00:00+00'::timestamptz,repeat(md5(g::text),16),
            decode(md5(g::text),'hex') from generate_series(1,{count}) g""", timeout=60)
        db.query('checkpoint')


def process_counters(pid):
    if os.name != 'nt':
        return {'available': False}
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [C.c_uint32,C.c_int,C.c_uint32]
    kernel.OpenProcess.restype = C.c_void_p
    kernel.CloseHandle.argtypes = [C.c_void_p]
    class Memory(C.Structure):
        _fields_ = [('cb',C.c_uint32),('PageFaultCount',C.c_uint32)] + [
            (x,C.c_size_t) for x in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage',
            'PagefileUsage','PeakPagefileUsage')]
    class IO(C.Structure):
        _fields_=[(x,C.c_uint64) for x in ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                                        'ReadTransferCount','WriteTransferCount','OtherTransferCount')]
    handle=kernel.OpenProcess(0x1000|0x10,False,pid)
    if not handle:
        return {'available':False}
    try:
        mem=Memory(); mem.cb=C.sizeof(mem); io=IO()
        psapi=C.WinDLL('psapi')
        psapi.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32]
        kernel.GetProcessIoCounters.argtypes=[C.c_void_p,C.c_void_p]
        if not psapi.GetProcessMemoryInfo(handle,C.byref(mem),mem.cb) or not kernel.GetProcessIoCounters(handle,C.byref(io)):
            return {'available':False}
        return {'available':True,'peak_working_set_bytes':mem.PeakWorkingSetSize,
                'read_transfer_bytes':io.ReadTransferCount,'write_transfer_bytes':io.WriteTransferCount,
                'other_transfer_bytes':io.OtherTransferCount}
    finally:
        kernel.CloseHandle(handle)
