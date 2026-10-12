"""Bounded Management API metadata journal. No raw response/error text is saved."""
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('controller_install_diagnostic', HERE / 'install.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ROOT, jit = m.ROOT, m.p.jit
BASE = '/v1/projects/' + jit.PROJECT
LIMIT = 100000


class Rejected(RuntimeError):
    def __init__(self, phase, code):
        self.phase, self.code = phase, code
        super().__init__(code)


def classify(raw):
    """Recognize fixed diagnostic conditions; never echo arbitrary server values."""
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return {'json': False, 'bytes': len(raw), 'condition': 'non_json_response'}
    out = {'json': True, 'bytes': len(raw), 'condition': 'unclassified_response'}
    if not isinstance(value, dict):
        return out
    out['fields'] = sorted(k for k in value if k in ('code', 'message', 'error', 'details', 'hint', 'statusCode'))
    code = value.get('code')
    if isinstance(code, str) and re.fullmatch(r'PGRST[0-9]{3}|[0-9]{2}[A-Z0-9]{3}', code):
        out['code'] = code
    text = ' '.join(str(value.get(k, '')) for k in ('message', 'error', 'details', 'hint')).lower()
    rules = [
        ('configuration_not_applied', r'(?:config|setting|change).*?(?:not.*?applied|in progress|pending)|appl(?:y|ying).*?(?:config|setting)'),
        ('jit_disabled', r'(?:jit|temporary access).*?(?:disabled|not enabled)'),
        ('ssl_required', r'(?:ssl|tls).*?(?:required|enable|enforce)'),
        ('mapping_absent', r'(?:0 rows|zero rows|no rows|mapping.*?not found|mapping.*?does not exist)'),
        ('mapping_not_single', r'(?:multiple.*?rows|single json object|single row)'),
        ('project_not_active', r'project.*?(?:paused|not active|not running)'),
        ('feature_unavailable', r'(?:feature|jit|temporary).*?(?:not available|not supported|not allowed)'),
        ('permission_denied', r'(?:permission denied|not authorized|unauthorized|insufficient.*?permission)'),
        ('request_throttled', r'(?:rate limit|too many|cooldown)'),
        ('owner_not_member', r'(?:user|owner).*?(?:not.*?member|not found)'),
        ('invalid_expiry', r'(?:expir|timestamp).*?(?:invalid|past|greater|less|maximum)'),
        ('already_enabled', r'already enabled'),
    ]
    for label, pattern in rules:
        if re.search(pattern, text):
            out['condition'] = label
            break
    out['condition_terms'] = [term for term in ('disabled', 'enabled', 'ssl', 'restart', 'pending',
        'wait', 'seconds', 'minutes', 'hour', 'cooldown', 'limit', 'permission', 'postgres', 'not found')
        if re.search(r'\b'+re.escape(term)+r'\b', text)]
    return out


def headers_metadata(headers):
    out = {}
    for name in ('cf-ray', 'x-request-id', 'sb-request-id', 'x-supabase-request-id'):
        value = headers.get(name)
        if isinstance(value, str) and (re.fullmatch(r'[0-9a-fA-F-]{16,64}', value) or
                re.fullmatch(r'[0-9a-fA-F]{16,32}-[A-Z]{3}', value)):
            out[name] = value
    return out


class Journal:
    def __init__(self, token, folder, opener=None):
        self.token, self.folder = token, folder
        self.opener = opener or urllib.request.build_opener(jit.NoRedirect())
        self.calls = 0
        self.deadline = time.monotonic() + 600
        self.owner = None

    def request(self, phase, path, method='GET', body=None):
        allowed = {'/v1/profile', BASE, BASE + '/jit-access', BASE + '/database/jit',
                   BASE + '/database/jit/list', BASE + '/ssl-enforcement', BASE + '/config/auth'}
        deleting = self.owner is not None and path == BASE + '/database/jit/' + self.owner and method == 'DELETE'
        if path not in allowed and not deleting:
            raise Rejected(phase, 'api_scope')
        if method not in ('GET', 'PUT', 'DELETE') or method == 'DELETE' and not deleting:
            raise Rejected(phase, 'method_scope')
        if method == 'PUT':
            if path == BASE + '/jit-access':
                if body not in ({'state': 'enabled'}, {'state': 'disabled'}):
                    raise Rejected(phase, 'configuration_scope')
            elif path == BASE + '/database/jit':
                roles = body.get('roles', []) if isinstance(body, dict) else []
                if not self.owner or set(body) != {'user_id', 'roles'} or body['user_id'] != self.owner or len(roles) != 1:
                    raise Rejected(phase, 'grant_scope')
                role = roles[0]
                if set(role) != {'role', 'expires_at'} or role['role'] != 'postgres' or type(role['expires_at']) is not int or not int(time.time()*1000) < role['expires_at'] <= int(time.time()*1000)+300000:
                    raise Rejected(phase, 'grant_scope')
            else:
                raise Rejected(phase, 'mutation_scope')
        if self.calls >= 24 or time.monotonic() >= self.deadline:
            raise Rejected(phase, 'api_budget')
        self.calls += 1
        label = f'{self.calls:02d}-{phase}'
        record = {'phase': phase, 'method': method, 'at_ms': int(time.time()*1000), 'automatic_retry': False}
        m.save(self.folder / (label + '-started.json'), record)
        req = urllib.request.Request(jit.API + path, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        started = time.monotonic()
        try:
            with self.opener.open(req, timeout=15) as response:
                raw = response.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise Rejected(phase, 'response_budget')
                record.update(http_status=response.status, request_ids=headers_metadata(response.headers))
                value = json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            raw = error.read(LIMIT + 1)
            record.update(http_status=error.code, request_ids=headers_metadata(error.headers),
                          response=classify(raw[:LIMIT]), oversized=len(raw)>LIMIT)
            raise Rejected(phase, 'management_http_' + str(error.code)) from None
        except Rejected:
            raise
        except Exception:
            record['error_class'] = 'management_transport_or_format'
            raise Rejected(phase, 'management_transport_or_format') from None
        finally:
            record['duration_ms'] = round((time.monotonic()-started)*1000)
            m.save(self.folder / (label + '-result.json'), record)
        return value

    def inspect(self):
        profile = self.request('owner', '/v1/profile')
        owner = profile.get('gotrue_id', '')
        if hashlib.sha256(owner.encode()).hexdigest() != jit.OWNER_HASH:
            raise Rejected('owner', 'owner_identity_mismatch')
        self.owner = owner
        project = self.request('project', BASE)
        if project.get('id') != jit.PROJECT or project.get('status') != 'ACTIVE_HEALTHY':
            raise Rejected('project', 'project_binding_or_health')
        ssl = self.request('ssl', BASE + '/ssl-enforcement')
        if ssl.get('appliedSuccessfully') is not True or ssl.get('currentConfig', {}).get('database') is not True:
            raise Rejected('ssl', 'ssl_not_applied')
        state = self.request('state', BASE + '/jit-access')
        mappings = self.request('mappings', BASE + '/database/jit/list')
        summary = {'owner_verified': True, 'project': jit.PROJECT, 'health': 'ACTIVE_HEALTHY',
            'ssl_applied': True, 'jit_state': state.get('state') if state.get('state') in ('enabled','disabled') else 'unknown',
            'jit_applied': state.get('appliedSuccessfully') is True,
            'mappings': len(mappings['items']) if isinstance(mappings.get('items'), list) else None}
        m.save(self.folder / 'inspection.json', summary)
        if summary['jit_state'] != 'disabled' or summary['mappings'] != 0:
            raise Rejected('inspection', 'existing_jit_access_not_owned')
        return summary

    def grant(self):
        value = self.request('enable', BASE + '/jit-access', 'PUT', {'state': 'enabled'})
        ready = self.request('enable_applied', BASE + '/jit-access')
        m.save(self.folder / 'enable-readiness.json', {
            'response_enabled': value.get('state') == 'enabled',
            'response_applied': value.get('appliedSuccessfully') is True,
            'readback_enabled': ready.get('state') == 'enabled',
            'readback_applied': ready.get('appliedSuccessfully') is True})
        if ready.get('state') != 'enabled' or ready.get('appliedSuccessfully') is not True:
            raise Rejected('enable_applied', 'configuration_not_applied')
        expires = int(time.time()*1000) + 300000
        self.request('role_grant', BASE + '/database/jit', 'PUT',
            {'user_id': self.owner, 'roles': [{'role': 'postgres', 'expires_at': expires}]})
        mapping = self.request('mapping_confirm', BASE + '/database/jit')
        roles = mapping.get('user_roles', [])
        if mapping.get('user_id') != self.owner or len(roles) != 1 or roles[0].get('role') != 'postgres' or roles[0].get('expires_at') != expires:
            raise Rejected('mapping_confirm', 'mapping_mismatch')
        m.save(self.folder / 'lease-confirmed.json', {'owner_sha256': jit.OWNER_HASH,
            'role': 'postgres', 'expires_at': expires, 'seconds': 300, 'jit': True,
            'cidr': None, 'cidr_reason': 'native_tcp_egress_not_independently_proven'})

    def close(self):
        # Revoke only the exact previously verified owner; never another mapping.
        failures = []
        for phase, path, body, method in [
            ('owner_revoke', BASE+'/database/jit/'+self.owner, None, 'DELETE'),
            ('disable', BASE+'/jit-access', {'state':'disabled'}, 'PUT')]:
            try:
                self.request(phase, path, method, body)
            except Rejected as error:
                failures.append({'phase': error.phase, 'code': error.code})
        state = self.request('closed_state', BASE+'/jit-access')
        mappings = self.request('closed_mappings', BASE+'/database/jit/list')
        ssl = self.request('closed_ssl', BASE+'/ssl-enforcement')
        confirmed = state.get('state') == 'disabled' and state.get('appliedSuccessfully') is True and mappings.get('items') == [] and ssl.get('appliedSuccessfully') is True and ssl.get('currentConfig',{}).get('database') is True
        m.save(self.folder/'closed.json', {'confirmed': confirmed, 'disabled':state.get('state')=='disabled',
            'applied':state.get('appliedSuccessfully') is True, 'remaining_mappings':len(mappings['items']) if isinstance(mappings.get('items'),list) else None,
            'ssl_enforced':ssl.get('currentConfig',{}).get('database') is True, 'request_failures':failures})
        if not confirmed:
            raise Rejected('close', 'revocation_not_proven')


def probe_metadata(token, folder):
    connect=json.loads((m.c.CONNECT/'connect.json').read_text())
    m.c.parameters(connect, token, m.c.CA)
    db=None;tx=None;ledger=None;result={'status':'NO_GO','sql_commands':0,'phase':'verified_tls_connect'}
    try:
        db=m.c.Connection(connect,token,m.c.CA)
        s=m.stream.t.old.s
        ledger=m.Ledger(folder/'metadata-ledger',lock_scope=folder/'metadata-lock')
        tx=s.Transaction(db,folder,ledger)
        result['phase']='begin_read_only'
        tx.command(s.BEGIN,'begin')
        result['phase']='read_only_check'
        tx.transaction=s.identity(tx.command(s.CHECK,'immediate_readonly_confirmation'))
        m.save(folder/'transaction-confirmed.json',tx.transaction)
        result['phase']='project_metadata'
        meta=json.loads(tx.command(m.TAG+jit.META_SQL,'metadata')[0][0])
        if meta['instance_sha256']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15' or meta['database']!='postgres' or meta['role']!='postgres' or meta['read_only']!='on':
            raise Rejected(result['phase'],'project_metadata_mismatch')
        local=[p.stem.split('_',1) for p in sorted((ROOT/'supabase/migrations').glob('*.sql'))]
        actual=[[r['version'],r['name']] for r in meta['migrations']]
        if local[:-1]!=actual or len(local)!=43:
            raise Rejected(result['phase'],'expected_42_43_identity')
        result.update(status='SECURE_PROJECT_BOUND_METADATA_PASS',project=jit.PROJECT,
            database='postgres',role='postgres',pg_version=meta['pg_version'],read_only='on',
            local_migrations=len(local),hosted_migrations=len(actual),only_m43_pending=True,
            verify_full=True,ca_hostname_validated=True,jit=True,pooler_mode='session',port=5432)
    except Rejected as error:
        result.update(phase=error.phase,reason=error.code)
    except Exception as error:
        result['reason']=str(error) if isinstance(error,m.Stop) and re.fullmatch('[a-z0-9_]+',str(error)) else 'connection_or_query_failed'
    finally:
        if tx:
            result['rollback']=tx.rollback()['confirmed']
            if not result['rollback']:result['status']='NO_GO'
        if db:
            result['sql_commands']=db.queries
            db.close()
        if ledger:ledger.close()
        m.save(folder/'metadata.json',result)
    if result['status']!='SECURE_PROJECT_BOUND_METADATA_PASS':
        raise Rejected(result['phase'],result.get('reason','metadata_failed'))
    return result


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('inspect','probe'):
        raise RuntimeError('mode_required')
    mode=sys.argv[1]
    folder = ROOT / 'supabase/.temp' / ('phase6e11-jit-diagnose-' + uuid.uuid4().hex)
    folder.mkdir()
    m.save(folder / 'contract.json', {'read_only_management': mode=='inspect', 'maximum_http_requests': 5 if mode=='inspect' else 24,
        'database_connections': 0 if mode=='inspect' else 1, 'application_writes': 0, 'auth_calls': 0, 'retries': 0,
        'query_cap':4,'max_seconds':600,'lease_seconds':300,'grant_readback_required':True,
        'hypothesis':'prior_enable_configuration_not_applied_before_role_grant',
        'source_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
    result = {'status': 'NO_GO', 'folder': folder.name, 'database_connections': 0, 'sql_commands': 0}
    journal = None;started=False
    try:
        if mode=='probe':
            m.save(ROOT/'supabase/.temp/phase6e11-jit-406-phase-probe-once.json',{'folder':folder.name,'retries':0})
        journal = Journal(jit.sb.credential(), folder)
        result.update(status='READ_ONLY_INSPECTION_PASS', **journal.inspect())
        if mode=='probe':
            started=True
            journal.grant()
            result['database_connections']=1
            metadata=probe_metadata(journal.token,folder)
            result.update(status='JIT_PROBE_PASS',sql_commands=metadata['sql_commands'],
                migration_identity='hosted42_local43',cause_of_historical_406='not_reconstructed')
    except Rejected as error:
        result.update(status='NO_GO', phase=error.phase, reason=error.code)
    except Exception:
        result.update(status='NO_GO', phase='local_admission', reason='local_failure')
    finally:
        if journal:
            if started:
                try:
                    journal.close();result['jit_revoked']=True
                except Rejected as error:
                    result.update(status='NO_GO',jit_revoked=False,close_phase=error.phase,close_reason=error.code)
            journal.token = None
            result['http_requests'] = journal.calls
        if (folder/'metadata.json').exists():
            result['sql_commands']=json.loads((folder/'metadata.json').read_text())['sql_commands']
        m.save(folder / 'result.json', result)
    print(json.dumps(result))
    return 0 if result['status'] in ('READ_ONLY_INSPECTION_PASS','JIT_PROBE_PASS') else 2


if __name__ == '__main__':
    sys.exit(main())
