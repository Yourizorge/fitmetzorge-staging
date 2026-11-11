"""Source-instrumented local quota prefix: one append and two empty dry slots.

The append belongs only to a disposable case. It is not canonical migration 48,
clean47 evidence, hosted authority, or a replacement for the full-DAG admission.
"""
import copy
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import uuid
from urllib.parse import urlencode

from cli_predispatch import pending
from cli_envelope import OBSERVERS, SLOTS, local, charged
from cli_stat_reader import snapshot, compare
from native_runtime import NativeRuntime
from .compiler import require, validate_candidate, validate_target, validate_case_binding, sha

common = pending.common
NAMES = ('quota', 'pre_auth', 'final')
HERE = pathlib.Path(__file__).resolve().parent


def utc_now():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def verify_policy(policy, context, slot, *, versions, target_sha=None):
    b = context['binding']
    require(policy['environment'] == 'disposable_ci' and policy['source_commit'] == b['source_commit']
        and policy['candidate_sha256'] == b['candidate_sha'] and policy['slot'] == slot
        and policy['cap'] == SLOTS[slot] and policy['dry_run'] is (slot != 'quota')
        and policy['closure_reserve'] == (1 if slot == 'quota' else 0)
        and policy['upstream_commit'] == common.UPSTREAM
        and policy['host'] == '127.0.0.1' and policy['database'] == 'postgres'
        and policy['user'] == 'postgres' and policy['expected_history_versions'] == versions,
        'prefix_policy_binding')
    if slot == 'quota':
        require(len(policy['migrations']) == 1 and policy['migrations'][0]['sha256'] == target_sha
                and len(policy['migrations'][0]['ast_hashes']) == 17, 'prefix_candidate17')
    else:
        require(policy['migrations'] == [], 'prefix_dry_migration_forbidden')


def validate_evidence(receipt, policy, output):
    header, terminal = receipt['header'], receipt['terminal']
    require(all(header.get(k) == policy[k] for k in ('source_commit', 'candidate_sha256',
            'invocation_id', 'slot', 'cap', 'dry_run', 'environment'))
            and header['policy_sha256'] == sha(json.dumps(policy, separators=(',', ':')).encode()),
            'prefix_header_binding')
    require(receipt['terminal_recorded'] is True and terminal['complete'] is True
            and terminal['connection_attempts'] == 1 and terminal['unknown_consumed'] == 0
            and 0 < terminal['sql_dispatches'] <= policy['cap'], 'prefix_terminal_incomplete')
    rows = [e for e in receipt['events'] if e['event'] == 'dispatch']
    if policy['slot'] == 'quota':
        pending.prove_execution(receipt, policy)
    else:
        require(b'up to date' in output.lower() and b'would push' not in output.lower(), 'prefix_not_empty')
        require(not any(e['category'] in ('migration', 'migration_history') for e in rows),
                'prefix_dry_write')
        histories = [e for e in receipt['events'] if e['event'] == 'history_snapshot']
        require(len(histories) == 1 and histories[0]['matches_policy'] is True
            and histories[0]['count'] == len(policy['expected_history_versions'])
            and histories[0]['versions_sha256'] == sha(json.dumps(policy['expected_history_versions'],
                separators=(',', ':')).encode()), 'prefix_dry_history')
    numeric = receipt['numeric_coverage']
    require(len(receipt['observer_trace']) == OBSERVERS
        and all(row['confirmed'] is True for row in receipt['observer_trace'])
        and receipt['tracking']['valid'] is True and numeric['all_protocol_visible'] is True
        and numeric['temp_written'] == 0, 'prefix_numeric_incomplete')
    return rows


def compatible(receipt):
    rows = [e for e in receipt.get('events', []) if e['event'] == 'dispatch']
    return dict(slot=receipt['slot'], environment='disposable_ci', dry_run=receipt['slot'] != 'quota',
        capacity_reserved=SLOTS[receipt['slot']], charged_commands=SLOTS[receipt['slot']]+OBSERVERS,
        complete=receipt['complete'], protocol_commands=len(rows),
        numeric_protocol_coverage=receipt.get('numeric_coverage', {}).get('all_protocol_visible') is True,
        observer_commands=receipt.get('observer_trace', []),
        commands=[dict(sha256=e['ast_sha256'], kind=e['kind'], protocol_commands=1,
                       predispatch_id=e['id']) for e in rows],
        source_commit=receipt['source_commit'], candidate_sha256=receipt['candidate_sha256'],
        run_id=receipt['run_id'], instrumented_receipt=receipt['receipt_name'],
        exact_local_append=True, canonical_migration=False, hosted_admitted=False)


class PendingPrefix:
    def __init__(self, gate, composition, artifact, samples):
        from .runtime_adapter import CaseComposition, verify_runtime_sources
        require(isinstance(composition, CaseComposition), 'prefix_composition')
        self.gate, self.composition = gate, composition
        self.context = copy.deepcopy(composition.quota)
        q = self.context
        verify_runtime_sources(q['root'], q['manifest'])
        validate_case_binding(q['root'], q['manifest'], q['binding'], now=utc_now())
        validate_candidate(q['root'], artifact, samples, now=utc_now())
        require(artifact['manifest'] == q['manifest'] and artifact['plan']['top_level_statements'] == 17,
                'prefix_candidate_binding')
        require(pathlib.Path(q['root']).resolve() == gate.sources.resolve()
            and gate.result['candidate_sha256'] == q['binding']['candidate_sha']
            and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
            and gate.container == 'supabase_db_fmz-db41-ci', 'prefix_disposable_source')
        self.files, self.migration_sources = common.migration_inventory(gate)
        self.versions = sorted(p.name.split('_')[0] for p in self.files)
        self.sql = artifact['sql'].encode('ascii')
        self.version = dt.datetime.strptime(q['manifest']['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
        require(self.version > max(self.versions) and self.version not in self.versions, 'prefix_local_version')
        self.target_name = self.version + '_disposable_case_quota_v1.sql'
        self.sql_sha = artifact['plan']['sql_sha256']
        require(sha(self.sql) == self.sql_sha, 'prefix_sql_hash')
        self.attempts, self.cli_protocol = [], []

    def _ticket(self, slot, ticket):
        meter = self.composition.meter
        phase = 'final' if slot == 'final' else 'migration'
        if ticket is None:
            require(slot == 'quota', 'prefix_dry_precharge_required')
            ticket = meter.charge(phase, SLOTS[slot]+OBSERVERS,
                action='candidate_quota_migration_aware_cli', kind='cli_reserved', mutation=True)
        require(type(ticket) is int and 1 <= ticket <= len(meter.events), 'prefix_ticket')
        event = meter.events[ticket-1]
        require(not meter.stopped and not meter.closed and event['phase'] == phase
            and event['commands'] == SLOTS[slot]+OBSERVERS and event['kind'] == 'cli_reserved'
            and event['confirmed'] is False and event['action'] == {
                'quota': 'candidate_quota_migration_aware_cli', 'pre_auth': 'pre_auth_empty_cli_dry_run',
                'final': 'empty_cli_dry_run'}[slot], 'prefix_ticket_binding')
        return ticket

    def run_pending(self):
        return self.run('quota')

    def run(self, slot, *, prepaid_ticket=None):
        require(len(self.attempts) < 3 and slot == NAMES[len(self.attempts)]
                and len(self.cli_protocol) == len(self.attempts), 'prefix_slot_or_retry')
        q, gate = self.context, self.gate
        validate_case_binding(q['root'], q['manifest'], q['binding'], now=utc_now())
        ticket = self._ticket(slot, prepaid_ticket)
        self.attempts.append(slot)  # Never reuse a failed slot, even before transport.
        receipt = dict(receipt_name='case-cli-'+slot+'.json', slot=slot, complete=False,
            source_commit=q['binding']['source_commit'], candidate_sha256=q['binding']['candidate_sha'],
            run_id=q['binding']['run_id'], profile='disposable_quota_candidate_v1',
            canonical_migration=False, clean47_final=False, hosted_admission=False,
            migration_sources=self.migration_sources, local_append_sha256=self.sql_sha,
            local_history_version=self.version, expected_history_count=47 if slot == 'quota' else 48,
            query_ms=5000, cli_seconds=45, output_max_bytes=8192, meter_ticket=ticket,
            reserved_commands=SLOTS[slot]+OBSERVERS, sql_text_exported=False,
            isolation_accounting='separate_disposable_bootstrap_not_run_commands')
        primary = None
        try:
            self._invoke(slot, receipt)
            value = local(compatible(receipt), slot)
            charged(value)
            self.cli_protocol.append(value)
            gate.save('cli-protocol-'+str(len(self.cli_protocol)-1)+'.json', value)
            if slot == 'quota': self.composition.meter.confirm(ticket)
            return value
        except Exception as error:
            primary = error
            self.composition.abort('prefix_'+slot+'_incomplete')
            receipt.update(complete=False, failure_class=type(error).__name__,
                           reserved_commands_consumed=SLOTS[slot]+OBSERVERS)
            raise
        finally:
            try: gate.save(receipt['receipt_name'], receipt)
            except Exception as error:
                self.composition.abort('prefix_receipt_unconfirmed')
                receipt['complete'] = False
                if primary is None: raise
                primary.add_note('prefix_receipt_secondary:'+type(error).__name__)

    def _invoke(self, slot, receipt):
        gate, q = self.gate, self.context
        upstream = pathlib.Path(os.environ['FMZ_CLI_PREDISPATCH_UPSTREAM']).resolve()
        receipt['build'] = common.source_binding(upstream)
        bun = shutil.which(os.environ.get('FMZ_BUN', 'bun'))
        require(bun is not None, 'prefix_bun_missing')
        def private(argv):
            code, output = common.bounded(argv, cwd=gate.work, env=os.environ.copy(), seconds=5)
            require(code == 0, 'prefix_private_bootstrap')
            return output.decode().strip()
        require(private([bun, '--version']) == '1.4.1', 'prefix_bun_pin')
        endpoints = [x for x in private(['docker','port',gate.container,'5432/tcp']).splitlines()
                     if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+', x)]
        require(len(endpoints) == 1, 'prefix_loopback')
        port = int(endpoints[0].split(':')[1])
        ca = gate.work / 'fmz-ci-ca.crt'
        connection = dict(host='127.0.0.1', hostaddr='127.0.0.1', port=port, dbname='postgres',
            user='postgres', sslmode='verify-full', sslrootcert=str(ca), connect_timeout=5)
        validate_target(q['root'], q['manifest'], environment=dict(os.environ),
            connection=connection, ca_path=ca, now=utc_now())
        work = gate.work / ('case-cli-'+slot+'-'+uuid.uuid4().hex)
        migrations = work / 'supabase/migrations'
        migrations.mkdir(parents=True)
        (work / 'private-home').mkdir()
        for file in self.files:
            raw = file.read_bytes()
            require(sha(raw) == self.migration_sources[next(name for name in self.migration_sources
                    if pathlib.PurePosixPath(name).name == file.name)], 'prefix_frozen_changed')
            with (migrations / file.name).open('xb') as stream: stream.write(raw)
        with (migrations / self.target_name).open('xb') as stream: stream.write(self.sql)
        config_port = 65534 if port != 65534 else 65532
        (work / 'supabase/config.toml').write_text('project_id = "fmz-cli-predispatch"\n[db]\n'
            'major_version = 17\nport = '+str(config_port)+'\nshadow_port = 65533\n'
            '[db.migrations]\nenabled = true\n[db.seed]\nenabled = false\n', encoding='ascii')
        versions = self.versions if slot == 'quota' else sorted([*self.versions, self.version])
        policy = dict(version=1, environment='disposable_ci', upstream_commit=common.UPSTREAM,
            source_commit=q['binding']['source_commit'], candidate_sha256=q['binding']['candidate_sha'],
            invocation_id=str(uuid.uuid4()), slot=slot, cap=SLOTS[slot],
            closure_reserve=1 if slot == 'quota' else 0, dry_run=slot != 'quota', host='127.0.0.1',
            port=port, database='postgres', user='postgres', ca_sha256=sha(ca.read_bytes()),
            expected_history_versions=versions,
            migration_paths=[str(migrations / self.target_name)] if slot == 'quota' else [])
        input_file = work / 'policy-input.json'
        input_file.write_text(json.dumps(policy), encoding='ascii')
        code, output = common.bounded([bun,str(pending.HERE/'policy.cjs'),str(input_file)],
                                      cwd=work, env=os.environ.copy(), seconds=5)
        require(code == 0, 'prefix_policy_compile')
        policy = json.loads(output)
        verify_policy(policy, q, slot, versions=versions, target_sha=self.sql_sha)
        policy_file, ledger_file = work/'policy.json', work/'ledger.jsonl'
        policy_raw = json.dumps(policy).encode('ascii')
        policy_file.write_bytes(policy_raw)
        receipt.update(policy=policy, invocation_id=policy['invocation_id'])
        gate.save('case-cli-'+slot+'-preregister.json', receipt)
        password = private(['docker','exec',gate.container,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
        require(password and not password.startswith('sbp_'), 'prefix_private_password')
        env = {k:v for k,v in os.environ.items() if not k.startswith(('PG','SUPABASE_','GH','NODE_','BUN_'))}
        env.update(PGPASSWORD=password, DO_NOT_TRACK='1', SUPABASE_NO_UPDATE_NOTIFIER='1',
            SUPABASE_TELEMETRY_DISABLED='1', HOME=str(work/'private-home'), USERPROFILE=str(work/'private-home'),
            XDG_CONFIG_HOME=str(work/'private-home'), FMZ_CLI_PREDISPATCH_POLICY=str(policy_file),
            FMZ_CLI_PREDISPATCH_LEDGER=str(ledger_file))
        url = 'postgresql://postgres@127.0.0.1:'+str(port)+'/postgres?'+urlencode(dict(
            sslmode='verify-full',sslrootcert=str(ca),connect_timeout='5',
            options='-c statement_timeout=5000 -c lock_timeout=1000'))
        runtime, primary = None, None
        class View:
            container = gate.container
            def rows(self, sql): return gate.rows(sql)
            def command(self, label, *args, **kwargs): return gate.command('case-'+slot+'-'+label,*args,**kwargs)
            def save(self, name, value): return gate.save('case-'+slot+'-'+name,value)
        def measure():
            before, first = snapshot(runtime)
            receipt['observer_trace'] = first
            call_error = None
            try:
                code, output = common.bounded([bun,str(upstream/'apps/cli/src/main.ts'),'db','push',
                    '--db-url',url, *(['--include-all'] if slot == 'quota' else ['--dry-run']),
                    '--skip-vault','--yes','--output-format','json'],cwd=work,env=env)
            except Exception as error:
                call_error = error
                raise
            finally:
                try:
                    after, last = snapshot(runtime)
                    receipt['observer_trace'] = first + last
                except Exception as error:
                    if call_error is None: raise
                    call_error.add_note('prefix_after_observer_secondary:'+type(error).__name__)
            require(password.encode() not in output, 'prefix_private_output')
            common.check_invocation(receipt,code,output,ledger_file)
            receipt.update(common.replay(ledger_file))
            receipt['tracking'] = common.tracking_evidence(before,after)
            receipt['numeric_coverage'] = compare(before,after,receipt['terminal']['sql_dispatches'],between=3)
            validate_evidence(receipt,policy,output)
            receipt['complete'] = True
            return receipt
        try:
            runtime = NativeRuntime.disposable(gate)
            common.isolated(View(),receipt,measure)
            name = 'case-'+slot+'-cli-predispatch-cli-isolation-0.json'
            raw = (gate.out/name).read_bytes(); isolated = json.loads(raw)
            require(isolated['restored'] is True and isolated['commands'] in (4,8)
                and isolated['commands'] == receipt['ci_bootstrap_sql_commands']
                and len(isolated['protocol']) == isolated['commands']
                and all(r['confirmed'] is True for r in isolated['protocol']), 'prefix_isolation_restore')
            receipt['isolation_ref'] = dict(path=name,sha256=sha(raw))
        except Exception as error:
            primary = error
            receipt['complete'] = False
            try: receipt['failure_ledger'] = common.replay(ledger_file,allow_incomplete=True)
            except (OSError,ValueError,KeyError,TypeError): receipt['failure_ledger_unverifiable'] = True
            raise
        finally:
            env.pop('PGPASSWORD',None);password = None
            if runtime is not None: runtime.clear()
            try:
                require(pending.bounded_raw(policy_file,16384) == policy_raw, 'prefix_policy_changed')
                receipt['policy_ref'] = pending.exclusive_raw(gate.out,'case-cli-'+slot+'.policy.json',policy_raw,16384)
                receipt['ledger_ref'] = pending.exclusive_raw(gate.out,'case-cli-'+slot+'.ledger.txt',
                    pending.bounded_raw(ledger_file,262144),262144)
            except Exception as error:
                receipt['complete'] = False
                if primary is None: raise
                primary.add_note('prefix_raw_evidence_secondary:'+type(error).__name__)


class PrefixGate:
    """Delegate the existing Gate; only the two exact dry CLI calls are replaced."""
    def __init__(self, gate, prefix):
        require(prefix.gate is gate, 'prefix_gate_binding')
        self._gate, self.prefix = gate, prefix
        self.cli_protocol = prefix.cli_protocol
    def __getattr__(self, name):
        if name == 'apply_endchain_migration': raise AttributeError(name)
        return getattr(self._gate,name)
    def cli(self, *args, timeout=45):
        require(args == ('db','push','--local','--dry-run','--skip-vault') and timeout == 45,
                'prefix_cli_arguments')
        slot = NAMES[len(self.prefix.attempts)] if len(self.prefix.attempts)<3 else None
        require(slot in ('pre_auth','final'), 'prefix_cli_order')
        meter = self.prefix.composition.meter
        self.prefix.run(slot,prepaid_ticket=len(meter.events))
        return subprocess.CompletedProcess(list(args),0,stdout='',stderr='')
