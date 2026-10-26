"""Reject stale checkout sources before disposable database work starts."""
import hashlib,pathlib,sys

HARNESS={
 '_offline/phase6e11/ci41/fixture_compat.py':'9f006933dfc7ef3ba97954c9988fed61e086cecb03e4201a63c1923c9f204729',
 '_offline/phase6e11/ci42/runner.py':'8e0ab728c58e47022a6002c7964070cf8faadbe79789605ddbfcca9327173402',
 '_offline/phase6e11/ci42/fixture_calendar.py':'1eb40ca1dff38ae4fc7f21bfb39a6d7595de60fc36e179aa969fb49b812270e0',
 '_offline/phase6e11/controller_v1/ci.py':'890ef5659b35b3840cde74cba9958baaaa7e5b006b9708a9a53601e2df55982e',
 '_offline/phase6e11/ci41/runner.py':'18f8efaa9dfc91be59926a40c805499cacce73f5717975b0756a52720839dc45'}
CANDIDATE_ONLY={'_offline/phase6e11/'+name for name in (
 'access_v1/cli_check.py','access_v1/jit.py','access_v1/migration_run.py','access_v1/migration_snapshot.py',
 'cursor_hosted_v2/canary.py','cursor_hosted_v2/discovery.py','cursor_v1/transfer.py','cursor_v2/adapter.py',
 'm41_tx_v2/install.py','m41_tx_v2/measure.py','migration_cursor_v2/install.py',
 'readiness_v1/targeted/query_load.py','readiness_v1/targeted/transport.py','readiness_v1/workflow_audit_v1/workflow_local.py',
 'textfree_tx_v2/connection.py','textfree_tx_v2/hosted.py','textfree_tx_v2/session.py','textfree_v1/monitor.py','textfree_v1/native.py')}

def verify_all(checkout,candidate,sources,*,harness=HARNESS,candidate_only=CANDIDATE_ONLY):
    checkout=pathlib.Path(checkout).resolve();candidate=pathlib.Path(candidate).resolve()
    found={}
    for relative,expected_sha in sources.items():
        if not relative.endswith('.py'):continue
        path=(candidate/relative).resolve()
        if not path.is_relative_to(candidate):raise ValueError('ci_source_path')
        expected=path.read_bytes()
        if hashlib.sha256(expected).hexdigest()!=expected_sha:raise ValueError('ci_candidate_module_changed')
        original=checkout/relative
        if not original.is_file():
            if relative not in candidate_only:raise ValueError('ci_checkout_dependency_missing')
            found[relative]={'candidate_sha256':expected_sha,'distribution':'explicit_candidate_only'}
            continue
        raw=original.read_bytes()
        if raw.replace(b'\r\n',b'\n')!=expected.replace(b'\r\n',b'\n'):raise ValueError('ci_loaded_source_mismatch')
        found[relative]={'checkout_sha256':hashlib.sha256(raw).hexdigest(),
            'candidate_sha256':expected_sha,'canonicalization':'CRLF-to-LF-only'}
    for relative,expected in harness.items():
        raw=(checkout/relative).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()!=expected:raise ValueError('ci_harness_changed')
        found[relative]={'checkout_sha256':hashlib.sha256(raw).hexdigest(),'lf_sha256':expected,'distribution':'pinned_harness'}
    if not found:raise ValueError('ci_loaded_sources_missing')
    return {'status':'ALL_PYTHON_SOURCE_BINDING_PASS','sources':found,
            'canonicalization':'CRLF-to-LF-only','candidate_only_does_not_authorize_hosted':True}

def verify(checkout,candidate,sources,modules=None):
    checkout=pathlib.Path(checkout).resolve();candidate=pathlib.Path(candidate).resolve()
    found={}
    for module in list((sys.modules if modules is None else modules).values()):
        name=getattr(module,'__file__',None)
        if not name:continue
        path=pathlib.Path(name).resolve()
        if path.suffix!='.py' or not path.is_relative_to(checkout):continue
        relative=path.relative_to(checkout).as_posix()
        if relative not in sources:continue
        raw=path.read_bytes();expected=(candidate/relative).read_bytes()
        if hashlib.sha256(expected).hexdigest()!=sources[relative]:raise ValueError('ci_candidate_module_changed')
        if raw.replace(b'\r\n',b'\n')!=expected.replace(b'\r\n',b'\n'):
            raise ValueError('ci_loaded_source_mismatch')
        found[relative]={'checkout_sha256':hashlib.sha256(raw).hexdigest(),
                         'candidate_sha256':sources[relative],'canonicalization':'CRLF-to-LF-only'}
    if not found:raise ValueError('ci_loaded_sources_missing')
    return {'status':'LOADED_SOURCE_BINDING_PASS','modules':found,'no_semantic_rewrite':True}
