"""Join original worker, root, Auth and fixture evidence; no SQL or authority."""
import copy
import importlib
import json
import pathlib

from .compiler import canonical, read_source, require, sha


def original(gate, reference):
    require(type(reference) is dict and type(reference.get('path')) is str,
            'case_terminal_reference')
    name = pathlib.PurePosixPath(reference['path'])
    require(not name.is_absolute() and '\\' not in reference['path']
            and name.as_posix() == reference['path']
            and all(part not in ('', '.', '..') for part in name.parts),
            'case_terminal_reference_path')
    root = pathlib.Path(gate.out).resolve(strict=True)
    path = root.joinpath(*name.parts)
    require(path.resolve(strict=True).is_relative_to(root)
            and not any(p.is_symlink() for p in (path, *path.parents) if p != root),
            'case_terminal_reference_escape')
    raw = path.read_bytes()
    require(0 < len(raw) <= 2_000_000 and sha(raw) == reference.get('sha256'),
            'case_terminal_reference_hash')
    for key in ('bytes', 'size'):
        require(key not in reference or type(reference[key]) is int
                and reference[key] == len(raw), 'case_terminal_reference_size')
    return raw


def saved(gate, name, value):
    path = gate.out / name
    require(not path.exists(), 'case_terminal_receipt_exists')
    gate.save(name, value)
    raw = path.read_bytes()
    require(json.loads(raw) == value, 'case_terminal_receipt_readback')
    reference = {'path':name, 'sha256':sha(raw), 'bytes':len(raw)}
    original(gate, reference)
    return reference


def finish(owner, gate, context, owners, *, original_error):
    """Only actual issued objects can authorize a single-case result, never hosted."""
    from . import runtime_case_entry as entry
    require(type(owner) is entry.PreparedExecution and owner._key is entry._PREPARED_KEY
            and owner._gate is gate and owner._used and not owner._terminal_attempted,
            'case_terminal_execution_owner')
    owner._terminal_attempted = True
    require(owner._current_identity(gate) == owner._identity, 'case_terminal_identity_changed')
    for name, digest in owner._sources.items():
        require(sha(read_source(owner._root, name)) == digest, 'case_terminal_source_changed')
    require(sha(pathlib.Path(__file__).read_bytes()) == owner._sources.get(
        entry.OWN+'runtime_case_terminal.py'), 'case_terminal_loaded_source')
    binding, case = owner.binding, owner.case_name
    fault = owner._faults
    if case == 'normal':
        require(original_error is None and fault.fired is None, 'case_terminal_normal_failed')
    else:
        require(original_error is not None and fault.fired is not None
                and fault.fired['original_error_code'] == 'case_injected_'+case,
                'case_terminal_expected_fault_missing')
    references = {}
    originals = {}
    def retain(reference):
        raw = original(gate, reference)
        normalized = {'path':reference['path'], 'sha256':sha(raw), 'bytes':len(raw)}
        require(normalized['path'] not in originals or originals[normalized['path']] == normalized,
                'case_terminal_conflicting_reference')
        originals[normalized['path']] = normalized
        return raw
    if case in ('pre_migration','post_migration'):
        require(context is None and not owners and owner._bootstrap_termination,
                'case_terminal_early_continued')
        early = owner._bootstrap_termination
        numeric = early.get('numeric_prefix')
        require(type(numeric) is dict and early.get('original_failure_ref') is not None,
                'case_terminal_bootstrap_numeric_missing')
        require(json.loads(retain(numeric['ref'])) == numeric['proof'],
                'case_terminal_bootstrap_numeric_original')
        for reference in numeric['proof']['evidence_refs']:
            retain(reference)
        failure = json.loads(retain(early['original_failure_ref']))
        require(failure.get('original_exception_class') == type(original_error).__name__
                and failure.get('original_fault_code') == 'case_injected_' + case
                and failure.get('bootstrap_numeric_prefix_ref') == numeric['ref']
                and failure.get('bootstrap_numeric_confirmed') is True
                and failure.get('ledger_stopped') is True, 'case_terminal_bootstrap_original_failure')
        references['bootstrap_numeric_prefix_ref'] = numeric['ref']
        references['bootstrap_original_failure_ref'] = early['original_failure_ref']
        close_numeric = early.get('closeout_numeric')
        require(type(close_numeric) is dict
                and json.loads(retain(close_numeric['ref'])) == close_numeric['proof'],
                'case_terminal_bootstrap_closeout_numeric')
        for reference in close_numeric['proof']['evidence_refs']:
            retain(reference)
        references['bootstrap_closeout_numeric_ref'] = close_numeric['ref']
        terminal = entry.dependency(owner._root, owner._sources, 'runtime_terminal_bootstrap')
        proof = terminal.validate_bootstrap_termination(gate, binding, case, fault, early['isolation'])
        require(proof == early['proof'] and proof.get('status') == 'BOOTSTRAP_TERMINATION_VERIFIED',
                'case_terminal_bootstrap_proof')
        path = gate.out/'case-bootstrap-termination.json'
        reference = {'path':path.name,'sha256':sha(path.read_bytes())}
        require(json.loads(retain(reference)) == proof, 'case_terminal_bootstrap_original')
        references['bootstrap_termination_ref'] = reference
        isolation = copy.deepcopy(early['isolation'])
    else:
        require(context is not None and owners.get('terminal_proof') is not None,
                'case_terminal_body_missing')
        terminal = entry.dependency(owner._root, owner._sources, 'runtime_terminal')
        proof = terminal.validate_runtime_termination(owners['gate'], owners['composition'],
            owners['lifecycle'], case_name=case, fault=fault, worker_result=owners['result'],
            original_error=owners['original_error'], fixture_closeout=context.closeout,
            isolation=context.isolation)
        require(proof == owners['terminal_proof'] and proof.get('status') == (
            'REGISTERED_WORKER_COMPLETE' if case == 'normal' else 'REGISTERED_FAULT_TERMINATED'),
            'case_terminal_worker_proof')
        path = gate.out/'case-runtime-terminal.json'
        reference = {'path':path.name,'sha256':sha(path.read_bytes())}
        require(json.loads(retain(reference)) == proof, 'case_terminal_worker_original')
        references['runtime_termination_ref'] = reference
        from .runtime_worker_evidence import export as export_worker
        worker_ref,worker_refs=export_worker(gate,owners['composition'],case,owners['result'])
        references['worker_export_ref']=worker_ref
        for worker_original in worker_refs:
            retain(worker_original)
        registered = entry.dependency(owner._root, owner._sources, 'runtime_registered_bootstrap')
        validator = getattr(registered, 'validate_closeout', None)
        require(callable(validator), 'case_terminal_auth_validator_missing')
        auth = validator(context, gate=gate, binding=binding)
        require(auth.get('status') == 'SCOPED_REGISTERED_CONTEXT_CLOSED'
                and auth.get('binding') == binding, 'case_terminal_auth_binding')
        for reference in auth['evidence_refs']:
            retain(reference)
        retain(auth['closeout_ref'])
        references['auth_closeout_ref'] = auth['closeout_ref']
        references['auth_terminal_ref'] = saved(gate, 'case-auth-context-terminal.json', auth)
        fixtures = entry.dependency(owner._root, owner._sources, 'runtime_registered_fixture_closeout')
        physical = context._fixture_proof
        require(type(physical) is fixtures.Proof and physical.owner is context,
                'case_terminal_fixture_owner')
        physical.unchanged()
        result = physical.receipt
        require(result.get('status') == 'SCOPED_PHYSICAL_CLOSURE_CONFIRMED_ORIGINAL_STATUS_UNCHANGED'
                and all(result.get(k) is True for k in ('physical_zero','registry_absence_confirmed',
                    'registry_commit_confirmed')) and result.get('registry_commit_unknown') is False,
                'case_terminal_fixture_unconfirmed')
        require(json.loads(retain(physical.ref)) == result, 'case_terminal_fixture_original')
        fixture_refs = getattr(physical, 'evidence_refs', None)
        require(type(fixture_refs) is list and fixture_refs, 'case_terminal_fixture_evidence_missing')
        for reference in fixture_refs:
            retain(reference)
        references['fixture_closeout_ref'] = physical.ref
        isolation = copy.deepcopy(context.isolation)
    require(type(proof.get('evidence_refs')) is list and proof['evidence_refs'],
            'case_terminal_worker_evidence_missing')
    for reference in proof['evidence_refs']:
        retain(reference)
    root = importlib.import_module('admission_budget_root_runtime')
    require(sha(pathlib.Path(root.__file__).read_bytes()) == owner._sources.get(entry.ROOT_ADMISSION),
            'case_terminal_root_source')
    require(callable(getattr(root,'validate_terminal',None)), 'case_terminal_root_validator_missing')
    owner.ledger.close()
    accounting = root.validate_terminal(owner.ledger, gate, binding)
    require(accounting.get('status') == 'NUMERIC_ACCOUNTING_CLOSED'
            and accounting.get('run_id') == binding['run_id']
            and accounting.get('register_sha256') == owner._report['root_dag']['full_register_sha256']
            and accounting.get('hosted_limit') == 2349, 'case_terminal_root_binding')
    require(type(accounting.get('fault_retained')) is bool
            and accounting['fault_retained'] == (case != 'normal'), 'case_terminal_root_fault')
    root_refs = accounting.get('evidence_refs')
    require(type(root_refs) is list and root_refs, 'case_terminal_root_originals_missing')
    for reference in root_refs:
        retain(reference)
    for reference in accounting['journal_refs']:
        raw = retain(reference)
        rows = [json.loads(line) for line in raw.splitlines()]
        require(rows and [row['sequence'] for row in rows] == list(range(1,len(rows)+1))
                and rows[-1].get('closed') is True
                and all(row.get('register_sha256') == accounting['register_sha256'] for row in rows),
                'case_terminal_root_journal')
    references['root_terminal_ref'] = saved(gate, 'case-root-terminal.json', accounting)
    for reference in references.values():
        retain(reference)
    original_refs = [originals[name] for name in sorted(originals)]
    archive = importlib.import_module('admission_case_archive')
    require(sha(pathlib.Path(archive.__file__).read_bytes()) == owner._sources.get(entry.ARCHIVE_SOURCE)
            and callable(getattr(archive, 'pack', None)), 'case_terminal_archive_source')
    archive_ref = archive.pack(gate, copy.deepcopy(original_refs))
    require(type(archive_ref) is dict and set(archive_ref) == {'path','sha256','bytes'}
            and archive_ref['path'] == 'case-original-index.json'
            and archive_ref['path'] not in originals, 'case_terminal_archive_ref')
    original(gate, archive_ref)
    result = {'format':'disposable-case-terminal-v1', 'status':'CASE_PASS',
        'scope':'single_disposable_case_only',
        'case_name':case, 'run_id':binding['run_id'], 'parent_id':binding['parent_id'],
        'source_commit':binding['source_commit'], 'ci_run':binding['ci_run'],
        'candidate_sha256':binding['candidate_sha'], 'isolation':isolation,
        'fault':fault.receipt(), 'original_exception_class':type(original_error).__name__
            if original_error is not None else None, **references,
        'original_refs':original_refs, 'original_archive_ref':archive_ref,
        'terminal_source_hashes':copy.deepcopy(owner._sources),
        'case_pass':True, 'matrix_aggregation_required':True, 'full_chain_admission':False,
        'hosted_admitted':False, 'additional_sql_commands':0}
    owner._terminal_proof = copy.deepcopy(result)
    return result
