"""Synthetic evidence-reference tests, not actual CLI/database admission."""
import json
import pathlib
import unittest
import uuid

from case_stack_v1 import prefix_receipt as p


def emit(gate, ordinal):
    """Deliberately fake originals for orchestration tests only."""
    if ordinal == 1:
        value = dict(complete=True, source_commit=gate.result['commit'],
            run_id=gate._case_stack_run_id,
            candidate_sha256=gate.result['candidate_sha256'], ci_run=gate.result['run_id'],
            protocol=[dict(ordinal=i) for i in range(1, 8)])
        gate.save('cli-prefix-history-provision.json', value)
        gate.save('cli-prefix-history-provision-reserve.json', {'synthetic': True})
        for i in range(1, 8):
            for suffix in ('intent', 'confirmed'):
                gate.save('cli-prefix-history-provision-' + str(i) + '-' + suffix + '.json', {'synthetic': True})
    tag = 'cli-predispatch-prefix-' + str(ordinal)
    manifest = json.loads((gate.out / 'candidate.json').read_bytes())
    migration = sorted(n for n in manifest['sources'] if n.startswith('supabase/migrations/'))[ordinal-1]
    value = dict(complete=True, profile='canonical_prefix', prefix_index=ordinal,
        run_id=gate._case_stack_run_id, ci_run=gate.result['run_id'],
        local_bootstrap_only=True, source_commit=gate.result['commit'],
        candidate_sha256=gate.result['candidate_sha256'], expected_migration=migration,
        expected_migration_sha256=manifest['sources'][migration], invocation_id=str(uuid.uuid4()),
        requested_arguments=['migration', 'up', '--local'],
        executed_argument_shape=['db', 'push', '--db-url', '<private-loopback-verify-full>',
            '--skip-vault', '--yes', '--include-all', '--output-format', 'json'],
        numeric_before={'synthetic': True}, numeric_after={'synthetic': True},
        observer_trace=[], terminal={'synthetic': True})
    for kind, suffix in (('policy', '.policy.json'), ('ledger', '.ledger.txt')):
        gate.save(tag + suffix, {'synthetic': True})
        original = p.ref(gate.out, tag + suffix)
        value[kind + '_ref'] = {k: original[k] for k in ('path', 'sha256')}
    isolation = 'prefix-' + str(ordinal) + '-cli-predispatch-cli-isolation-0.json'
    gate.save(isolation, {'synthetic': True})
    value.update(isolation_receipt=isolation,
        isolation_receipt_sha256=p.ref(gate.out, isolation)['sha256'])
    gate.save(tag + '-preregister.json', {'synthetic': True})
    gate.save(tag + '.json', value)


class PrefixReceiptTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from case_stack_v1.test_bootstrap import FakeGate, MIGRATIONS
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.g = FakeGate(pathlib.Path(self.temp.name))
        manifest = json.loads((self.g.out / 'candidate.json').read_bytes())
        self.source = dict(source_commit=self.g.result['commit'], ci_run=self.g.result['run_id'],
            candidate_sha256=self.g.result['candidate_sha256'], run_id=str(uuid.uuid4()),
            candidate_manifest_sha256=p.ref(self.g.out, 'candidate.json')['sha256'],
            migration_sources={n: manifest['sources'][n] for n in MIGRATIONS})
        self.paths = MIGRATIONS[:44]
        self.g._case_stack_run_id = self.source['run_id']
        for i in range(1, 45): emit(self.g, i)
        self.g.save('case-stack-reserve-catalog-before41.json', dict(commands=['catalog'], reserved=1))
        self.g.save('041-psql.json', dict(phase='migration_41', exitcode=0))
        catalog = {key:self.source[key] for key in ('source_commit','ci_run','candidate_sha256','run_id')}
        catalog.update(confirmed=False, attempted=True, migrations_applied=40,
            command_serial_before=40, sql_sha256='a'*64, implicit_driver_sql_commands=None,
            reservation_ref=p.ref(self.g.out,'case-stack-reserve-catalog-before41.json'))
        self.g.save('case-stack-catalog-before41-intent.json', catalog)
        catalog.update(confirmed=True, command_serial_after=41, command_ref=p.ref(self.g.out,'041-psql.json'))
        self.g.save('case-stack-catalog-before41.json', catalog)
        self.rows = [p.invocation(self.g, self.source, i, path) for i, path in enumerate(self.paths, 1)]

    def rewrite(self, name, change):
        path = self.g.out / name
        value = json.loads(path.read_bytes())
        change(value)
        path.write_text(json.dumps(value))  # Owned synthetic TemporaryDirectory only.

    def test_complete_original_links_do_not_claim_numeric_or_hosted_pass(self):
        ref = p.publish(self.g, self.source, self.rows)
        value = json.loads((self.g.out / ref['path']).read_bytes())
        self.assertEqual(value['run_id'], self.source['run_id'])
        self.assertEqual(len(value['invocations']), 44)
        self.assertTrue(value['original_refs_complete'])
        self.assertIsNone(value['total_sql_commands'])
        self.assertIsNone(value['implicit_driver_sql_commands'])
        self.assertFalse(value['independent_numeric_validation'])
        self.assertFalse(value['hosted_admission'])
        self.assertEqual(ref, p.ref(self.g.out, ref['path']))

    def test_missing_prefix_or_duplicate_identity_blocks_summary(self):
        with self.assertRaisesRegex(ValueError, 'ordered_44'):
            p.publish(self.g, self.source, self.rows[:-1])
        self.rows[-1]['invocation_id'] = self.rows[0]['invocation_id']
        with self.assertRaisesRegex(ValueError, 'invocation_reuse'):
            p.publish(self.g, self.source, self.rows)

    def test_changed_raw_ledger_cannot_be_hidden_by_old_summary(self):
        (self.g.out / self.rows[0]['original_refs']['ledger']['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'original_binding'):
            p.publish(self.g, self.source, self.rows)

    def test_changed_producer_rejected(self):
        (self.g.sources / (p.PREFIX + p.PRODUCERS[0])).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'producer_hash'):
            p.publish(self.g, self.source, self.rows)

    def test_unconfirmed_catalog_blocks_summary(self):
        self.rewrite('case-stack-catalog-before41.json', lambda r: r.update(confirmed=False))
        with self.assertRaisesRegex(ValueError, 'catalog'):
            p.publish(self.g, self.source, self.rows)

    def test_catalog_missing_command_blocks_completeness_claim(self):
        (self.g.out/'041-psql.json').unlink()
        with self.assertRaises(ValueError): p.publish(self.g,self.source,self.rows)
        self.assertFalse((self.g.out/'case-stack-canonical-prefix.json').exists())

    def test_catalog_replaced_command_blocks_completeness_claim(self):
        self.rewrite('041-psql.json',lambda r:r.update(exitcode=1))
        with self.assertRaisesRegex(ValueError,'catalog_original'):
            p.publish(self.g,self.source,self.rows)

    def test_catalog_changed_reservation_blocks_completeness_claim(self):
        self.rewrite('case-stack-reserve-catalog-before41.json',lambda r:r.update(commands=[],reserved=0))
        with self.assertRaisesRegex(ValueError,'catalog_original'):
            p.publish(self.g,self.source,self.rows)

    def test_catalog_changed_intent_blocks_completeness_claim(self):
        self.rewrite('case-stack-catalog-before41-intent.json',lambda r:r.update(run_id=str(uuid.uuid4())))
        with self.assertRaisesRegex(ValueError,'catalog_intent'):
            p.publish(self.g,self.source,self.rows)

    def test_catalog_other_candidate_or_ci_run_blocks_summary(self):
        for key,value in (('candidate_sha256','f'*64),('ci_run','987654')):
            with self.subTest(key=key):
                self.rewrite('case-stack-catalog-before41.json',lambda r:r.update({key:value}))
                with self.assertRaisesRegex(ValueError,'catalog'):
                    p.publish(self.g,self.source,self.rows)
                self.rewrite('case-stack-catalog-before41.json',lambda r:r.update({key:self.source[key]}))

    def test_no_secret_bearing_argument_is_exported(self):
        self.rewrite('cli-predispatch-prefix-1.json', lambda r: r.update(
            executed_argument_shape=['db', 'push', '--db-url', 'PRIVATE_SENTINEL']))
        with self.assertRaisesRegex(ValueError, 'argument_shape'):
            p.invocation(self.g, self.source, 1, self.paths[0])

    def test_missing_numeric_originals_not_replaced_by_boolean(self):
        self.rewrite('cli-predispatch-prefix-1.json', lambda r: r.pop('numeric_before'))
        with self.assertRaisesRegex(ValueError, 'observations_missing'):
            p.invocation(self.g, self.source, 1, self.paths[0])

    def test_another_case_same_commit_and_candidate_is_not_admitted(self):
        self.rewrite('cli-predispatch-prefix-1.json', lambda r: r.update(run_id=str(uuid.uuid4())))
        with self.assertRaisesRegex(ValueError, 'invocation_binding'):
            p.invocation(self.g, self.source, 1, self.paths[0])

    def test_existing_summary_never_overwritten(self):
        ref = p.publish(self.g, self.source, self.rows)
        before = (self.g.out / ref['path']).read_bytes()
        with self.assertRaises(FileExistsError): p.publish(self.g, self.source, self.rows)
        self.assertEqual(before, (self.g.out / ref['path']).read_bytes())

    def test_path_escape_and_oversized_original_rejected(self):
        for name in ('../outside', 'C:/file', 'folder\\file'):
            with self.assertRaisesRegex(ValueError, 'path'): p.ref(self.g.out, name)
        (self.g.out / 'large').write_bytes(b'x' * (p.MAX_ORIGINAL + 1))
        with self.assertRaisesRegex(ValueError, 'size'): p.ref(self.g.out, 'large')


if __name__ == '__main__': unittest.main()
