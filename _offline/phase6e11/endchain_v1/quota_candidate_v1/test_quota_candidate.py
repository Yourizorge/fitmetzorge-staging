"""Offline tests only. Synthetic catalog samples are not real CI evidence."""
import argparse
import copy
import pathlib
import shutil
import sys
import tempfile
import unittest
import uuid

import admission_quota_readonly as baseline
from quota_candidate_v1 import compiler as c

ROOT = pathlib.Path(__file__).resolve().parents[4]
START = '2026-11-03T12:00:00Z'
END = '2026-11-03T12:10:00Z'
NOW = '2026-11-03T12:01:00Z'


def evaluate_guard(node, values):
    """Evaluate only the parsed expiry predicate's small, closed AST vocabulary."""
    kind = node['@']
    if kind == 'BoolExpr':
        args = [evaluate_guard(x, values) for x in node['args']]
        return {'AND_EXPR': all, 'OR_EXPR': any}[node['boolop']['name']](args)
    if kind == 'ColumnRef':
        return values['.'.join(x['sval'] for x in node['fields'])]
    if kind == 'FuncCall' and [x['sval'] for x in node['funcname']] == ['clock_timestamp']:
        return values['now']
    if kind == 'A_Const':
        return node['val']['sval']
    if kind == 'A_Expr':
        left = evaluate_guard(node['lexpr'], values)
        if node['kind']['name'] == 'AEXPR_IN':
            return left in [evaluate_guard(x, values) for x in node['rexpr']]
        right = evaluate_guard(node['rexpr'], values)
        if node['kind']['name'] == 'AEXPR_DISTINCT':
            return left != right
        if node['kind']['name'] == 'AEXPR_OP' and [x['sval'] for x in node['name']] == ['>=']:
            return left >= right
    raise AssertionError('unsupported expiry guard AST')


def samples(root):
    baseline.parser()
    from pglast.stream import RawStream
    data = (root / c.binding.M45).read_bytes()
    contract = baseline.source_contract(data)
    nodes = [n.stmt for n in baseline.parser().parse_sql(data.decode())]
    constraint = next(cmd.def_ for n in nodes if type(n).__name__ == 'AlterTableStmt'
                      for cmd in n.cmds if cmd.def_ is not None)
    trigger = next(n for n in nodes if type(n).__name__ == 'CreateTrigStmt')
    return {
        'constraint': [{'name': baseline.CONSTRAINT, 'kind': 'c', 'validated': True,
            'noinherit': False, 'local': True, 'inherited': 0, 'deferrable': False,
            'deferred': False, 'schema': baseline.SCHEMA, 'relation': 'runs',
            'expression': RawStream()(constraint.raw_expr)}],
        'function': [{'schema': baseline.SCHEMA, 'name': baseline.FUNCTION, 'nargs': 0,
            'kind': 'f', 'returns_trigger': True, 'language': 'plpgsql', 'owner': 'postgres',
            'definer': False, 'leakproof': False, 'strict': False, 'volatility': 'v',
            'parallel': 'u', 'config': ['search_path=pg_catalog, pg_temp'],
            'body': contract['body'], 'effective_execute': {
                'anon': False, 'authenticated': False, 'service_role': False},
            'acl': [{'grantee': 'postgres', 'grantor': 'postgres',
                     'privilege': 'EXECUTE', 'grantable': False}]}],
        'trigger': [{'schema': baseline.SCHEMA, 'relation': 'runs', 'name': baseline.FUNCTION,
            'function_schema': baseline.SCHEMA, 'function_name': baseline.FUNCTION,
            'function_nargs': 0, 'type': 27, 'enabled': 'O', 'internal': False,
            'nonconstraint': True, 'deferrable': False, 'deferred': False, 'nargs': 0,
            'argument_bytes': 0, 'columns': '', 'unconditional': True,
            'old_transition': None, 'new_transition': None, 'definition': RawStream()(trigger)}],
        'empty': [dict.fromkeys(('runs_empty', 'steps_empty', 'evidence_empty',
                                'pg17', 'database_ok'), True)],
    }


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='quota-candidate-offline-')
        cls.root = pathlib.Path(cls.temp.name)
        names = set(c.PINS) | {c.PREFIX + name for name in c.SUPPORT}
        for name in names:
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        for name in c.OWN:
            target = cls.root / c.PREFIX / 'quota_candidate_v1' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(c.HERE / name, target)
        cls.original_pins = {n: (ROOT / n).read_bytes() for n in c.PINS}
        cls.source_map = c.source_files(cls.root)
        cls.catalog = samples(cls.root)

    @classmethod
    def tearDownClass(cls):
        for name, original in cls.original_pins.items():
            if (ROOT / name).read_bytes() != original:
                raise AssertionError('actual frozen source changed')
        cls.temp.cleanup()

    def setUp(self):
        self.manifest = c.prepare(self.root, source_commit='a' * 40,
            candidate_sha256='b' * 64, github_run='41619169140', created_at=START,
            expires_at=END, cases=[{'id': str(uuid.uuid4()), 'label': 'before_call', 'cap': 2349}],
            sources=self.source_map)
        self.catalog = copy.deepcopy(type(self).catalog)

    def compile(self):
        return c.compile_candidate(self.root, self.manifest, self.catalog, now=NOW)

    def reject(self, edit):
        edit(self.manifest)
        with self.assertRaises(c.CandidateStop):
            self.compile()

    def test_valid_bundle_exact_reproduction(self):
        result = self.compile()
        self.assertEqual(c.validate_candidate(self.root, result, self.catalog, now=NOW), result['plan'])
        self.assertEqual(result['plan']['top_level_statements'], 17)
        self.assertFalse(result['plan']['executed'])
        self.assertFalse(result['plan']['clean47_baseline'])
        self.assertFalse(result['plan']['hosted_permission'])
        self.assertFalse(result['plan']['runtime_budget_verified'])
        self.assertIsNone(result['plan']['actual_protocol_commands'])

    def test_parent_is_not_execution_identity(self):
        self.reject(lambda v: v['cases'][0].update(id=c.binding.NEW_RUN))

    def test_all_pinned_legacy_ids_rejected(self):
        for uid in c.legacy_ids(self.root):
            with self.subTest(uid=uid), self.assertRaises(c.CandidateStop):
                value = copy.deepcopy(self.manifest)
                value['cases'][0]['id'] = uid
                c.validate_manifest(value, self.root, now=NOW)

    def test_wrong_parent_purpose_environment(self):
        for field, value in [('parent_run', str(uuid.uuid4())), ('purpose', 'old_purpose'),
                             ('environment', 'staging'), ('branch', 'other')]:
            with self.subTest(field=field):
                v = copy.deepcopy(self.manifest); v[field] = value
                with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_permission_and_pass_claims_rejected(self):
        for field in ('hosted_permission', 'clean47_baseline', 'runtime_integrated'):
            for invalid in (True, 0, None):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(c.CandidateStop):
                    v = copy.deepcopy(self.manifest); v[field] = invalid
                    c.validate_manifest(v, self.root, now=NOW)

    def test_cap_boundaries_and_types(self):
        for invalid in (0, -1, 2350, True, 2349.0, '2349', None):
            with self.subTest(cap=invalid), self.assertRaises(c.CandidateStop):
                v = copy.deepcopy(self.manifest); v['cases'][0]['cap'] = invalid
                c.validate_manifest(v, self.root, now=NOW)
        for valid in (1, 128, 2349):
            self.manifest['cases'][0]['cap'] = valid
            self.compile()

    def test_uuid_type_canonical_and_fresh_version(self):
        for uid in (str(uuid.uuid1()), str(uuid.uuid4()).upper(), 'invalid', None):
            with self.subTest(uid=uid), self.assertRaises(c.CandidateStop):
                v = copy.deepcopy(self.manifest); v['cases'][0]['id'] = uid
                c.validate_manifest(v, self.root, now=NOW)

    def test_duplicate_case_and_labels(self):
        for duplicate_id in (True, False):
            v = copy.deepcopy(self.manifest)
            case = dict(v['cases'][0])
            if not duplicate_id: case['id'] = str(uuid.uuid4())
            v['cases'].append(case)
            with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_case_cardinality(self):
        for count in (0, 15):
            v = copy.deepcopy(self.manifest)
            v['cases'] = [dict(id=str(uuid.uuid4()), label='case_' + str(i), cap=128) for i in range(count)]
            with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_fourteen_cases_explicit_not_full_matrix_pass(self):
        self.manifest['cases'] = [dict(id=str(uuid.uuid4()), label='case_' + str(i), cap=2349) for i in range(14)]
        result = self.compile()
        self.assertEqual(len(result['plan']['case_ids']), 14)
        self.assertTrue(result['plan']['existing_github_run_unique_preserved'])
        self.assertNotIn('PASS', result['manifest']['status'])

    def test_expiry_bound_and_no_automatic_extension(self):
        for now in ('2026-11-03T11:59:59Z', END, '2026-11-03T12:11:00Z'):
            with self.subTest(now=now), self.assertRaises(c.CandidateStop):
                c.validate_manifest(self.manifest, self.root, now=now)
        for end in (START, '2026-11-03T12:10:01Z', 'invalid'):
            v = copy.deepcopy(self.manifest); v['expires_at'] = end
            with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_digest_and_github_identity(self):
        for field, value in [('source_commit', 'a'*39), ('candidate_sha256', 'raw_source'),
                             ('github_run', 123), ('github_run', '0'), ('github_run', '9223372036854775808')]:
            with self.subTest(field=field, value=value), self.assertRaises(c.CandidateStop):
                v = copy.deepcopy(self.manifest); v[field] = value
                c.validate_manifest(v, self.root, now=NOW)

    def test_extra_manifest_case_fields_rejected(self):
        for target in ('manifest', 'case'):
            v = copy.deepcopy(self.manifest)
            (v if target == 'manifest' else v['cases'][0])['override'] = True
            with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_source_hash_and_required_source(self):
        for mode in ('change', 'remove'):
            v = copy.deepcopy(self.manifest)
            if mode == 'change': v['sources'][c.binding.M45] = '0'*64
            else: del v['sources'][c.binding.M45]
            with self.assertRaises(c.CandidateStop): c.validate_manifest(v, self.root, now=NOW)

    def test_candidate_change_cannot_relabel_source_manifest(self):
        result = self.compile()
        result['manifest']['candidate_sha256'] = 'c'*64
        with self.assertRaises(c.CandidateStop):
            c.validate_candidate(self.root, result, self.catalog, now=NOW)

    def test_frozen_pins_cannot_be_replaced(self):
        self.reject(lambda v: v['preserved'].update({c.binding.M45: '0'*64}))

    def test_source_path_escape(self):
        for name in ('../escape', '/absolute', 'C:/absolute', 'folder\\file'):
            with self.subTest(name=name), self.assertRaises(c.CandidateStop):
                c.read_source(self.root, name)

    def test_baseline_changed_cap_rejected(self):
        self.catalog['constraint'][0]['expression'] = self.catalog['constraint'][0]['expression'].replace('128', '2349')
        with self.assertRaises(c.CandidateStop): self.compile()

    def test_baseline_acl_body_and_trigger_failclosed(self):
        for group, key, value in [('function', 'body', 'changed'), ('function', 'definer', True),
                                   ('function', 'acl', []), ('trigger', 'enabled', 'D')]:
            with self.subTest(group=group, key=key), self.assertRaises(c.CandidateStop):
                sample = copy.deepcopy(self.catalog); sample[group][0][key] = value
                c.compile_candidate(self.root, self.manifest, sample, now=NOW)

    def test_empty_registry_pg17_required(self):
        for key in self.catalog['empty'][0]:
            with self.subTest(key=key), self.assertRaises(c.CandidateStop):
                sample = copy.deepcopy(self.catalog); sample['empty'][0][key] = False
                c.compile_candidate(self.root, self.manifest, sample, now=NOW)

    def test_baseline_dollar_delimiter_injection_rejected(self):
        self.catalog['constraint'][0]['expression'] += ' /* $qc_guard$ */'
        with self.assertRaises(c.CandidateStop): self.compile()

    def test_sql_and_plan_mutation_rejected(self):
        for field in ('sql', 'plan'):
            artifact = self.compile()
            if field == 'sql': artifact['sql'] += '\nselect 1;'
            else: artifact['plan']['executed'] = True
            with self.assertRaises(c.CandidateStop):
                c.validate_candidate(self.root, artifact, self.catalog, now=NOW)

    def test_parser_only_new_objects_and_explicit_catalog_insert(self):
        nodes = [n.stmt for n in baseline.parser().parse_sql(self.compile()['sql'])]
        self.assertEqual([type(n).__name__ for n in nodes], ['TransactionStmt', 'VariableSetStmt',
            'VariableSetStmt', 'LockStmt', 'DoStmt', 'CreateStmt', 'GrantStmt', 'AlterTableStmt',
            'InsertStmt', 'AlterTableStmt', 'AlterTableStmt', 'CreateFunctionStmt', 'GrantStmt',
            'CreateTrigStmt', 'CreateTrigStmt', 'CreateTrigStmt', 'TransactionStmt'])
        function = next(n for n in nodes if type(n).__name__ == 'CreateFunctionStmt')
        self.assertEqual([x.sval for x in function.funcname], [c.SCHEMA, c.FUNCTION])
        self.assertFalse(function.replace)
        self.assertNotIn('SECURITY DEFINER', self.compile()['sql'].upper())
        inserts = [n for n in nodes if type(n).__name__ == 'InsertStmt']
        self.assertEqual(len(inserts), 1)
        self.assertEqual(inserts[0].relation.relname, 'quota_candidate_v1_cases')
        self.assertEqual(inserts[0].relation.schemaname, c.SCHEMA)

    def test_pg17_plpgsql_syntax_not_just_outer_sql(self):
        from pglast.stream import RawStream
        parser = baseline.parser()
        bodies = [n.stmt for n in parser.parse_sql(self.compile()['sql'])
                  if type(n.stmt).__name__ in ('CreateFunctionStmt', 'DoStmt')]
        self.assertEqual(len(bodies), 2)
        for body in bodies:
            self.assertTrue(parser.parse_plpgsql(RawStream()(body)))

    def test_catalog_admin_only_immutable_and_lease_lookup(self):
        sql = self.compile()['sql']
        for part in ('enable row level security', 'quota_candidate_catalog_immutable',
                     'select * into strict lease', 'NEW.command_count>lease.cap',
                     'before insert or update or delete or truncate',
                     'from public,anon,authenticated,service_role'):
            self.assertIn(part, sql)
        self.assertNotIn('grant select', sql.lower())

    def test_flat_integration_binding_exact_fields(self):
        value = c.binding_for_case(self.root, self.manifest, self.manifest['cases'][0]['id'], now=NOW)
        self.assertEqual(set(value), {'run_id', 'purpose', 'cap', 'parent_id', 'source_commit',
            'candidate_sha', 'ci_run', 'expiry', 'binding_sha', 'environment',
            'execution_admitted', 'hosted_permission'})
        self.assertFalse(value['execution_admitted'])
        self.assertEqual(value['parent_id'], c.binding.NEW_RUN)
        self.assertEqual(c.validate_case_binding(self.root, self.manifest, value, now=NOW), value)

    def test_flat_binding_tampering_and_unknown_case_denied(self):
        value = c.binding_for_case(self.root, self.manifest, self.manifest['cases'][0]['id'], now=NOW)
        for key, replacement in [('cap', 2350), ('run_id', c.binding.OLD_RUN),
            ('parent_id', str(uuid.uuid4())), ('execution_admitted', True), ('purpose', 'other'),
            ('candidate_sha', 'd'*64), ('ci_run', '1'), ('expiry', '2026-11-03T13:00:00Z')]:
            with self.subTest(key=key), self.assertRaises(c.CandidateStop):
                tampered = {**value, key: replacement}
                c.validate_case_binding(self.root, self.manifest, tampered, now=NOW)

    def test_old_caps_default_and_new_exact_cases_in_ast(self):
        nodes = [n.stmt for n in baseline.parser().parse_sql(self.compile()['sql'])]
        constraint = next(cmd.def_ for n in nodes if type(n).__name__ == 'AlterTableStmt'
                          for cmd in n.cmds if cmd.def_ is not None)
        case = baseline.strip_locations(constraint.raw_expr())['args'][1]['rexpr']
        caps = {b['expr']['rexpr']['arg']['val']['sval']: b['result']['val']['ival'] for b in case['args']}
        self.assertEqual(caps, {'1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d': 2237,
            c.binding.OLD_RUN: 2349, self.manifest['cases'][0]['id']: 2349})
        self.assertEqual(case['defresult']['val']['ival'], 128)
        self.assertNotIn(c.binding.NEW_RUN, caps)

    def test_retention_expiry_and_no_reset_are_emitted(self):
        sql = self.compile()['sql']
        for text in ("TG_OP='TRUNCATE'", "TG_OP='DELETE'", 'NEW.command_count<OLD.command_count',
            "OLD.state='stopped' and NEW.state not in ('stopped','closed')",
            "NEW.state in ('running','complete')", 'NEW.expires_at<>', 'NEW.manifest_sha<>',
            'NEW.github_run<>', 'NEW.head_sha<>', 'in access exclusive mode',
            'quota_candidate_registry_not_empty', 'quota_candidate_baseline_changed'):
            self.assertIn(text, sql)
        self.assertNotIn('disable trigger', sql.lower())
        self.assertNotIn('migration_history', sql)

    def expiry_guard(self):
        from pglast.stream import RawStream
        p = baseline.parser()
        function = next(n.stmt for n in p.parse_sql(self.compile()['sql'])
                        if type(n.stmt).__name__ == 'CreateFunctionStmt')
        found = []
        def walk(value):
            if isinstance(value, list):
                for item in value: walk(item)
            if isinstance(value, dict):
                stmt = value.get('PLpgSQL_stmt_if')
                if stmt:
                    query = stmt['cond']['PLpgSQL_expr']['query']
                    if query.startswith('clock_timestamp()>=lease.expiry'):
                        found.append(p.parse_sql('SELECT ' + query)[0].stmt.targetList[0].val())
                for item in value.values(): walk(item)
        walk(p.parse_plpgsql(RawStream()(function)))
        self.assertEqual(len(found), 1)
        return found[0]

    def test_expired_running_to_stopped_cannot_advance_actual_predicate(self):
        guard = self.expiry_guard()
        for now in (100, 101):
            for state in ('running', 'complete', 'stopped', 'closed'):
                for next_step in (1, -1):
                    with self.subTest(now=now, state=state, next_step=next_step):
                        self.assertTrue(evaluate_guard(guard, {'now': now, 'lease.expiry': 100,
                            'old.next_step': 0, 'new.next_step': next_step, 'new.state': state}))

    def test_expired_stop_close_keep_step_and_preexpiry_progress(self):
        guard = self.expiry_guard()
        for state in ('stopped', 'closed'):
            self.assertFalse(evaluate_guard(guard, {'now': 100, 'lease.expiry': 100,
                'old.next_step': 7, 'new.next_step': 7, 'new.state': state}))
        for state in ('running', 'complete'):
            self.assertTrue(evaluate_guard(guard, {'now': 100, 'lease.expiry': 100,
                'old.next_step': 7, 'new.next_step': 7, 'new.state': state}))
        self.assertFalse(evaluate_guard(guard, {'now': 99, 'lease.expiry': 100,
            'old.next_step': 7, 'new.next_step': 8, 'new.state': 'running'}))

    def target(self):
        ca = self.root / 'test-only-ca.pem'
        ca.write_text('synthetic test CA existence fixture', encoding='ascii')
        environment = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': c.binding.REPOSITORY,
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_SHA': self.manifest['source_commit'],
            'GITHUB_RUN_ID': self.manifest['github_run']}
        connection = dict(host='127.0.0.1', hostaddr='127.0.0.1', port=5432,
            dbname='postgres', user='postgres', sslmode='verify-full', sslrootcert=str(ca), connect_timeout=5)
        return dict(environment=environment, connection=connection, ca_path=ca, now=NOW)

    def test_target_preflight_does_not_claim_live_connection(self):
        result = c.validate_target(self.root, self.manifest, **self.target())
        self.assertFalse(result['executed'])
        self.assertFalse(result['live_ssl_attested'])

    def test_remote_plaintext_timeout_and_service_targets_denied(self):
        for key, value in [('host', 'db.example.com'), ('hostaddr', '10.0.0.1'),
                           ('sslmode', 'require'), ('connect_timeout', 6), ('port', True),
                           ('service', 'remote')]:
            args = self.target(); args['connection'][key] = value
            with self.subTest(key=key), self.assertRaises(c.CandidateStop):
                c.validate_target(self.root, self.manifest, **args)

    def test_ci_source_run_and_host_alias_mismatch_denied(self):
        for key, value in [('GITHUB_SHA', 'c'*40), ('GITHUB_RUN_ID', '123'),
            ('GITHUB_ACTIONS', 'false'), ('GITHUB_REPOSITORY', 'other/repo'),
            ('PGSERVICE', 'service'), ('PGHOSTADDR', '10.0.0.1')]:
            args = self.target(); args['environment'][key] = value
            with self.subTest(key=key), self.assertRaises(c.CandidateStop):
                c.validate_target(self.root, self.manifest, **args)

    def test_wrong_ca_and_expiry_denied(self):
        args = self.target(); args['connection']['sslrootcert'] = str(self.root / 'missing')
        with self.assertRaises(c.CandidateStop): c.validate_target(self.root, self.manifest, **args)
        args = self.target(); args['now'] = END
        with self.assertRaises(c.CandidateStop): c.validate_target(self.root, self.manifest, **args)


if __name__ == '__main__':
    args = argparse.ArgumentParser(add_help=False)
    args.add_argument('--source-root', type=pathlib.Path)
    options, remaining = args.parse_known_args()
    if options.source_root is not None:
        ROOT = options.source_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0], *remaining])
