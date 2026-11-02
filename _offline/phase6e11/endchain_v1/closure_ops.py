"""Compose two source-bound real CI stacks. No Supabase or hosted entry."""
import hashlib,io,json,os,pathlib,re,stat,sys,zipfile

ROOT=pathlib.Path(__file__).resolve().parents[3]

WORKFLOW='phase6e-closure-ci.yml'

def inputs_for(chain,app,head):
    if not re.fullmatch('[0-9a-f]{40}',head):raise ValueError('closure_head')
    result={}
    for kind,folder in (('chain',chain),('app',app)):
        if json.loads((folder/'before.json').read_text())['head']!=head:
            raise ValueError('closure_stale_candidate')
        if (folder/'dispatch.json').exists():raise ValueError('closure_no_retry')
        blob=json.loads((folder/'blob.json').read_text())
        if not re.fullmatch('[0-9a-f]{40}',blob['blob']) or not re.fullmatch('[0-9a-f]{64}',blob['sha256']):
            raise ValueError('closure_blob_binding')
        if hashlib.sha256(disk(folder/'candidate.json').read_bytes()).hexdigest()!=blob['sha256']:
            raise ValueError('closure_candidate_changed')
        result[kind+'_blob']=blob['blob'];result[kind+'_sha256']=blob['sha256']
    return result

def compare_results(chain,app,chain_sources,app_sources):
    if chain.get('status')!='CLEAN_CI_PASS' or chain.get('full_chain_admission') is not True:
        raise ValueError('closure_endchain_incomplete')
    if (app.get('status')!='CLEAN_CI_PASS' or app.get('migrations_applied')!=47
        or app.get('dry_run')!='EMPTY' or app.get('member_data_used') is not False
        or app.get('external_ai_calls')!=0 or app.get('hosted_requests')!=0):
        raise ValueError('closure_application_incomplete')
    if chain.get('commit')!=app.get('commit') or str(chain.get('run_id'))!=str(app.get('run_id')):
        raise ValueError('closure_not_one_source_and_run')
    for key in ('commit','run_id'):
        if not chain.get(key):raise ValueError('closure_identity_missing')
    overlap=set(chain_sources)&set(app_sources)
    if not overlap or any(chain_sources[n]!=app_sources[n] for n in overlap):
        raise ValueError('closure_shared_source_mismatch')
    return {'status':'COMPOSED_CI_PASS_PENDING_INDEPENDENT_REVIEW',
        'commit':chain['commit'],'run_id':str(chain['run_id']),
        'shared_sources':len(overlap),'hosted_admitted':False,
        'package21_released':False,'owner_accepted':False}

APP_PROOFS={'candidate.json','result.json','loaded-source-preflight.json',
    'loaded-source-final.json','composed-browser.json','app-cli-profile.json','release-train.json'}
CHAIN_PROOFS={'candidate.json','result.json','integral-migration-pair.json',
    'runtime-command-meter.json','complete-command-register.json'}
APP_PROOF_SOURCES={'_offline/phase6e_server_v1/release_train.py',
                   '_offline/phase6e_server_v1/test_release_security.py'}


def disk(path):
    path=pathlib.Path(path)
    return pathlib.Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path


def bounded_read(path,limit):
    try:
        with disk(path).open('rb') as stream:raw=stream.read(limit+1)
    except OSError as error:raise ValueError('closure_evidence_missing') from error
    if len(raw)>limit:raise ValueError('closure_evidence_size')
    return raw


def object_json(raw):
    def unique(pairs):
        value={}
        for key,item in pairs:
            if key in value:raise ValueError('closure_duplicate_json_key')
            value[key]=item
        return value
    value=json.loads(raw,object_pairs_hook=unique)
    if not isinstance(value,dict):raise ValueError('closure_json_object_required')
    return value


def verify_archive(folder,kind):
    # Mirror each existing collector's bounds, without extracting any ZIP entry.
    if kind not in ('app','chain'):raise ValueError('closure_archive_kind')
    max_files,max_bytes=(1100,30000000) if kind=='app' else (2200,80000000)
    pattern=r'[A-Za-z0-9_.-]+\.(json|txt|png)' if kind=='app' else r'[A-Za-z0-9_.-]+\.(json|txt)'
    collection=object_json(bounded_read(folder/'collection.json',2000000))
    raw=bounded_read(folder/'evidence.zip',30000000)
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=collection.get('archive_sha256'):raise ValueError('closure_'+kind+'_archive_changed')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist();names=[entry.filename for entry in entries]
            if (not names or len(names)>max_files or len(set(n.casefold() for n in names))!=len(names)
                or any(not re.fullmatch(pattern,n) for n in names)
                or any(entry.flag_bits&1 or stat.S_IFMT(entry.external_attr>>16) not in (0,stat.S_IFREG)
                       for entry in entries)):
                raise ValueError('closure_archive_paths')
            if any(entry.file_size>2000000 for entry in entries) or sum(entry.file_size for entry in entries)>max_bytes:
                raise ValueError('closure_archive_size')
            manifest_raw=archive.read('artifact-manifest.json')
            manifest=object_json(manifest_raw)
            if (not manifest or 'artifact-manifest.json' in manifest or 'collection.json' in manifest
                or set(names)!=set(manifest)|{'artifact-manifest.json'}):
                raise ValueError('closure_archive_manifest_set')
            if not (APP_PROOFS if kind=='app' else CHAIN_PROOFS)<=manifest.keys():
                raise ValueError('closure_'+kind+'_proof_missing')
            if bounded_read(folder/'artifact-manifest.json',2000000)!=manifest_raw:
                raise ValueError('closure_archive_manifest_changed')
            payloads={}
            for name,expected in manifest.items():
                if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):
                    raise ValueError('closure_archive_manifest_digest')
                payload=archive.read(name)
                if hashlib.sha256(payload).hexdigest()!=expected:
                    raise ValueError('closure_archive_entry_changed')
                if bounded_read(folder/name,2000000)!=payload:
                    raise ValueError('closure_'+kind+'_evidence_changed')
                payloads[name]=payload
    except (zipfile.BadZipFile,KeyError,RuntimeError,NotImplementedError) as error:
        raise ValueError('closure_archive_invalid') from error
    result=object_json(payloads['result.json'])
    flag='verified' if kind=='app' else 'all_file_hashes_valid'
    if (collection.get(flag) is not True or collection.get('head')!=result.get('commit')
        or str(collection.get('run'))!=str(result.get('run_id'))):
        raise ValueError('closure_'+kind+'_archive_binding')
    return {'payloads':payloads,'collection':collection,'archive_sha256':digest}


def verify_app(folder,root):
    bundle=verify_archive(folder,'app');payloads=bundle['payloads']
    read=lambda name:object_json(payloads[name])
    result=read('result.json');sources=read('candidate.json')['sources']
    if not isinstance(sources,dict) or not APP_PROOF_SOURCES<=sources.keys():
        raise ValueError('closure_app_proof_source_missing')
    for name,digest in sources.items():
        path=(root/name).resolve()
        if (not path.is_relative_to(root.resolve()) or not isinstance(digest,str)
            or not re.fullmatch('[0-9a-f]{64}',digest)
            or hashlib.sha256(disk(path).read_bytes()).hexdigest()!=digest):
            raise ValueError('closure_app_source_changed')
    security=[name for name in payloads if re.fullmatch(r'[0-9]{3,}-release-security\.json',name)]
    if len(security)!=1:raise ValueError('closure_app_security_proof_missing_or_ambiguous')
    receipt=read(security[0])
    if type(receipt.get('exitcode')) is not int or receipt['exitcode']!=0:
        raise ValueError('closure_app_security_failed')
    read('release-train.json')
    return result,sources


def validate_bundle(chain,app,root=ROOT):
    # Bind every disk receipt consumed by legacy admission to its actual ZIP first.
    bundle=verify_archive(chain,'chain')
    result,sources=verify_app(app,root)
    from hosted_gate import admission
    admitted=admission(chain,root=root)  # Validation only; never calls hosted main().
    chain_result=object_json(bundle['payloads']['result.json'])
    chain_sources=object_json(bundle['payloads']['candidate.json'])['sources']
    if (admitted['archive_sha256']!=bundle['archive_sha256'] or admitted['sources']!=chain_sources
        or admitted['head']!=chain_result.get('commit')
        or str(admitted['ci_run'])!=str(chain_result.get('run_id'))
        or admitted['register']!=object_json(bundle['payloads']['complete-command-register.json'])):
        raise ValueError('closure_chain_admission_binding')
    value=compare_results(chain_result,result,chain_sources,sources)
    value['endchain_archive_sha256']=bundle['archive_sha256']
    value['application_archive_sha256']=object_json(bounded_read(app/'collection.json',2000000))['archive_sha256']
    return value

def main():
    if len(sys.argv)!=4 or sys.argv[1] not in ('dispatch','validate'):
        raise ValueError('closure_usage_dispatch_or_validate_chain_folder_app_folder')
    import ops  # Checkout-only dispatch harness; never needed for candidate test imports.
    chain=pathlib.Path(sys.argv[2]).resolve();app=pathlib.Path(sys.argv[3]).resolve()
    if sys.argv[1]=='validate':
        if not all(folder.is_relative_to(ops.ROOT/'supabase/.temp') for folder in (chain,app)):
            raise ValueError('closure_evidence_scope')
        value=validate_bundle(chain,app,root=ops.ROOT)
        ops.g.write(chain/'composed-admission.json',value)
        print(json.dumps(value));return
    for folder,prefix in ((chain,'phase6e11-endchain-ci-'),(app,'phase6e-server-ci-')):
        if folder.parent!=ops.ROOT/'supabase/.temp' or not folder.name.startswith(prefix):
            raise ValueError('closure_folder_scope')
    head=ops.g.git('rev-parse','HEAD')
    if ops.g.git('branch','--show-current')!='main':raise ValueError('closure_branch')
    remote=ops.g.git('ls-remote','origin','refs/heads/main').split()[0]
    if remote!=head:raise ValueError('closure_remote_source')
    values=inputs_for(chain,app,head)
    intent={'head':head,'inputs':values,'workflow':WORKFLOW,
        'composed':True,'hosted_calls':0,'automatic_retry':False}
    # Both exclusive intents are durable before dispatch; ambiguous outcomes never retry.
    ops.g.write(chain/'dispatch.json',intent);ops.g.write(app/'dispatch.json',intent)
    ops.g.api('/actions/workflows/'+WORKFLOW+'/dispatches','POST',{'ref':'main','inputs':values})
    print('COMPOSED_CI_DISPATCHED_ONCE')

if __name__=='__main__':main()
