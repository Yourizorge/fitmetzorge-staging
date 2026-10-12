"""Offline verification and write-once manifest; never opens a hosted connection."""
import hashlib,json,os,pathlib,sys

FILES=['contract','result','action-before','action-after','action-events','action-pair',
       'action-confirmed','closed','metadata-removal-pair','removal-pair','io-admission']

def validate(records):
    r=records['result'];c=records['contract'];closed=records['closed']
    if r.get('status')!='AUTH_METADATA_HOSTED_CANARY_PASS' or r.get('auth_calls')!=0 or r.get('application_writes')!=0:
        raise ValueError('seal_result')
    if r['commands']>128 or r['elapsed_seconds']>180 or c['max_commands']!=128 or c['max_seconds']!=180:
        raise ValueError('seal_budget')
    if not all(r.get(k) for k in ('guard_removed','catalog_restored','jit_revoked')) or not closed.get('disabled') or closed.get('remaining_mappings')!=0 or not closed.get('ssl_enforced'):
        raise ValueError('seal_access')
    if records['action-before']!=records['action-after'] or records['action-after']['fixture_rows']!=0:
        raise ValueError('seal_drift')
    events=records['action-events']
    if len(events)!=3 or [e['operation'] for e in events]!=['INSERT','UPDATE','DELETE'] or len({e['xid'] for e in events})!=1 or len({e['backend'] for e in events})!=1:
        raise ValueError('seal_writes')
    if any(e['table_name']!='auth.sessions' or e['action_id']!=c['action'] or e['key_sha']!=c['fixture_sha'] or e['actor_sha']!=c['actor_sha'] for e in events):
        raise ValueError('seal_binding')
    if records['action-confirmed']['statements']!=3:raise ValueError('seal_commit')
    if records['metadata-removal-pair']['own_additions']!=0 or not records['metadata-removal-pair']['existing_equal'] or records['removal-pair']['own_additions']!=0 or not records['removal-pair']['existing_objects_equal']:
        raise ValueError('seal_objects')
    plans=records['action-pair']['plans']
    if len(plans)!=3 or any(p['own_temp_read_blocks'] or p['own_temp_written_blocks'] or p['execution_ms']>1000 for p in plans):
        raise ValueError('seal_action_io')
    io=records['io-admission']
    if not io.get('all_reader_calls_covered') or io['closing']['temp_blks_written'] or io['closing']['temp_blks_read']:
        raise ValueError('seal_read_io')
    for p in io['profiles']+[io['reader']]:
        if not p['acceptable'] or p['delta']['temp_blks_read'] or p['delta']['temp_blks_written']:raise ValueError('seal_read_io')
    return {'status':'SCOPED_AUDIT_PROOF_SEALED','commands':r['commands'],
            'elapsed_seconds':r['elapsed_seconds'],'inserts':1,'updates':1,'deletes':1,
            'fixture_remaining':0,'temporary_objects_remaining':0,'jit_mappings':0,
            'hosted_http_auth_proven':False,'whole_6e11':'NO_GO'}

def main():
    root=pathlib.Path(__file__).resolve().parents[3];folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=root/'supabase/.temp' or not folder.name.startswith('phase6e11-auth-metadata-hosted-'):raise ValueError('seal_scope')
    records={n:json.loads((folder/(n+'.json')).read_text()) for n in FILES}
    value=validate(records)
    for n,h in records['contract']['sources'].items():
        p=root/n
        if os.name=='nt':p=pathlib.Path('\\\\?\\'+str(p))
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('seal_source_changed')
    hashes={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}
    value.update(run=records['contract']['run'],ci_run=records['contract']['ci_run'],
                 source_count=len(records['contract']['sources']),files=hashes)
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    with (folder/'sealed-manifest.json').open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:v for k,v in value.items() if k!='files'}|{'files':len(hashes),'manifest_sha256':hashlib.sha256(raw).hexdigest()}))

if __name__=='__main__':main()
