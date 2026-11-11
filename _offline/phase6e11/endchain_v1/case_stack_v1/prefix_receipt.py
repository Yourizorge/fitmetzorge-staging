"""Preserve the canonical prefix originals; never infer missing driver costs."""
import hashlib
import json
import os
import pathlib
import uuid

MAX_ORIGINAL = 1400000
PRODUCERS = (
    'case_stack_v1/bootstrap.py', 'case_stack_v1/prefix_receipt.py',
    'cli_predispatch/prefix.py', 'cli_predispatch/pending.py',
    'cli_predispatch/ci.py', 'cli_predispatch/hook.cjs',
    'cli_predispatch/entry.mjs', 'cli_predispatch/policy.cjs',
)
PREFIX = '_offline/phase6e11/endchain_v1/'


def require(value, code):
    if not value:
        raise ValueError('canonical_prefix_' + code)


def raw(root, name):
    root = pathlib.Path(root).resolve(strict=True)
    require(isinstance(name, str) and pathlib.PurePosixPath(name).name == name
            and '\\' not in name and ':' not in name, 'path')
    path = root / name
    require(not path.is_symlink() and not (hasattr(path, 'is_junction') and path.is_junction())
            and path.is_file() and path.resolve(strict=True).parent == root, 'file')
    with path.open('rb') as stream:
        data = stream.read(MAX_ORIGINAL + 1)
    require(len(data) <= MAX_ORIGINAL, 'size')
    return data


def ref(root, name):
    data = raw(root, name)
    return dict(path=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def invocation(gate, source, ordinal, migration_path):
    tag = 'cli-predispatch-prefix-' + str(ordinal)
    receipt_raw = raw(gate.out, tag + '.json')
    receipt = json.loads(receipt_raw)
    require(receipt.get('complete') is True and receipt.get('profile') == 'canonical_prefix'
            and receipt.get('prefix_index') == ordinal
            and receipt.get('local_bootstrap_only') is True, 'incomplete_invocation')
    require(all(receipt.get(key) == source[key] for key in ('source_commit', 'candidate_sha256', 'run_id', 'ci_run'))
            and receipt.get('expected_migration') == migration_path
            and receipt.get('expected_migration_sha256') == source['migration_sources'][migration_path],
            'invocation_binding')
    refs = {'receipt': ref(gate.out, tag + '.json'),
            'preregister': ref(gate.out, tag + '-preregister.json')}
    for kind, suffix in (('policy', '.policy.json'), ('ledger', '.ledger.txt')):
        original = ref(gate.out, tag + suffix)
        require(receipt.get(kind + '_ref') == {key: original[key] for key in ('path', 'sha256')},
                'original_binding')
        refs[kind] = original
    isolation_name = 'prefix-' + str(ordinal) + '-cli-predispatch-cli-isolation-0.json'
    refs['isolation'] = ref(gate.out, isolation_name)
    require(receipt.get('isolation_receipt') == isolation_name
            and receipt.get('isolation_receipt_sha256') == refs['isolation']['sha256'], 'isolation_binding')
    # A summary is not an independent protocol/numeric verifier. Preserve the
    # original observations for that verifier, including unknown driver costs.
    require('numeric_before' in receipt and 'numeric_after' in receipt
            and 'observer_trace' in receipt and 'terminal' in receipt, 'observations_missing')
    require(receipt.get('requested_arguments') == ['migration', 'up', '--local']
            and receipt.get('executed_argument_shape') == ['db', 'push', '--db-url',
                '<private-loopback-verify-full>', '--skip-vault', '--yes', '--include-all',
                '--output-format', 'json'], 'argument_shape')
    identifier = receipt.get('invocation_id')
    require(isinstance(identifier, str) and str(uuid.UUID(identifier)) == identifier
            and uuid.UUID(identifier).version == 4, 'invocation_id')
    return dict(ordinal=ordinal, migration_path=migration_path,
        migration_sha256=source['migration_sources'][migration_path],
        invocation_id=receipt['invocation_id'], requested_arguments=receipt['requested_arguments'],
        executed_argument_shape=receipt['executed_argument_shape'], original_refs=refs)


def publish(gate, source, invocations):
    require([row['ordinal'] for row in invocations] == list(range(1, 45)), 'ordered_44')
    require(len({row['invocation_id'] for row in invocations}) == 44, 'invocation_reuse')
    paths = sorted(n for n in source['migration_sources'] if n.startswith('supabase/migrations/'))[:44]
    require(len(paths) == 44 and invocations == [invocation(gate, source, index, path)
            for index, path in enumerate(paths, 1)], 'invocation_changed')
    manifest_raw = raw(gate.out, 'candidate.json')
    require(hashlib.sha256(manifest_raw).hexdigest() == source['candidate_manifest_sha256'], 'manifest_changed')
    manifest = json.loads(manifest_raw)
    producer_sources = {}
    for relative in PRODUCERS:
        name = PREFIX + relative
        path = gate.sources / name
        require(not path.is_symlink() and path.is_file(), 'producer_file')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        require(manifest['sources'].get(name) == digest, 'producer_hash')
        producer_sources[name] = digest
    for row in invocations:
        for original in row['original_refs'].values():
            require(ref(gate.out, original['path']) == original, 'original_changed')
    provision_ref = ref(gate.out, 'cli-prefix-history-provision.json')
    provision = json.loads(raw(gate.out, provision_ref['path']))
    require(provision.get('complete') is True and provision.get('source_commit') == source['source_commit']
            and provision.get('candidate_sha256') == source['candidate_sha256']
            and provision.get('ci_run') == source['ci_run']
            and provision.get('run_id') == source['run_id'], 'provision')
    provision_refs = [provision_ref, ref(gate.out, 'cli-prefix-history-provision-reserve.json')]
    for item in provision['protocol']:
        for suffix in ('intent', 'confirmed'):
            provision_refs.append(ref(gate.out, 'cli-prefix-history-provision-' + str(item['ordinal']) + '-' + suffix + '.json'))
    catalog_ref = ref(gate.out, 'case-stack-catalog-before41.json')
    catalog = json.loads(raw(gate.out, catalog_ref['path']))
    require(catalog.get('confirmed') is True and catalog.get('migrations_applied') == 40
            and all(catalog.get(key) == source[key] for key in
                ('source_commit','ci_run','candidate_sha256','run_id')), 'catalog')
    catalog_originals = {}
    for kind in ('command','reservation'):
        original = catalog.get(kind + '_ref')
        require(isinstance(original,dict) and set(original) == {'path','sha256','bytes'}, 'catalog_original')
        require(ref(gate.out,original['path']) == original, 'catalog_original')
        catalog_originals[kind] = original
    require(catalog_originals['reservation']['path'] == 'case-stack-reserve-catalog-before41.json',
            'catalog_reservation')
    intent_ref = ref(gate.out,'case-stack-catalog-before41-intent.json')
    intent = json.loads(raw(gate.out,intent_ref['path']))
    expected_intent = {key:value for key,value in catalog.items() if key not in ('command_serial_after','command_ref')}
    expected_intent['confirmed'] = False
    require(intent == expected_intent, 'catalog_intent')
    catalog_originals['intent'] = intent_ref
    result = {key: source[key] for key in ('source_commit', 'ci_run', 'candidate_sha256',
        'run_id', 'candidate_manifest_sha256')}
    result.update(format='case-stack-canonical-prefix-v1', producer_sources=producer_sources,
        invocations=invocations, catalog_before41_ref=catalog_ref, catalog_original_refs=catalog_originals,
        history_provision_refs=provision_refs, original_refs_complete=True,
        independent_numeric_validation=False, implicit_driver_sql_commands=None,
        total_sql_commands=None, hosted_admission=False)
    data = (json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    require(len(data) <= MAX_ORIGINAL, 'summary_size')
    with (gate.out / 'case-stack-canonical-prefix.json').open('xb') as stream:
        require(stream.write(data) == len(data), 'short_write')
        stream.flush()
        os.fsync(stream.fileno())
    require(raw(gate.out, 'case-stack-canonical-prefix.json') == data, 'readback')
    return ref(gate.out, 'case-stack-canonical-prefix.json')
