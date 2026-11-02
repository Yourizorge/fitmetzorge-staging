"""Offline catalog-tampering tests; no PostgreSQL or historical UUID execution."""
import copy
import os
import re
import types
import unittest
from unittest.mock import Mock, patch

import admission_quota_readonly as quota
from sql_protocol import ROOT, parser

CI_ENV = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
          'GITHUB_REF': 'refs/heads/main'}


def sample():
    data = (ROOT / quota.M45).read_bytes()
    contract = quota.source_contract(data)
    from pglast.stream import RawStream
    nodes = [n.stmt for n in parser().parse_sql(data.decode())]
    constraint = next(c.def_ for n in nodes if type(n).__name__ == 'AlterTableStmt'
                      for c in n.cmds if c.def_ is not None)
    trigger = next(n for n in nodes if type(n).__name__ == 'CreateTrigStmt')
    return contract, {
        'constraint': [{'name': quota.CONSTRAINT, 'kind': 'c', 'validated': True,
            'noinherit': False, 'local': True, 'inherited': 0, 'deferrable': False,
            'deferred': False, 'schema': quota.SCHEMA, 'relation': 'runs',
            'expression': RawStream()(constraint.raw_expr)}],
        'function': [{'schema': quota.SCHEMA, 'name': quota.FUNCTION, 'nargs': 0, 'kind': 'f',
            'returns_trigger': True, 'language': 'plpgsql', 'owner': 'postgres', 'definer': False,
            'leakproof': False, 'strict': False, 'volatility': 'v', 'parallel': 'u',
            'config': ['search_path=pg_catalog, pg_temp'], 'body': contract['body'],
            'effective_execute': {'anon': False, 'authenticated': False, 'service_role': False},
            'acl': [{'grantee': 'postgres', 'grantor': 'postgres', 'privilege': 'EXECUTE', 'grantable': False}]}],
        'trigger': [{'schema': quota.SCHEMA, 'relation': 'runs', 'name': quota.FUNCTION,
            'function_schema': quota.SCHEMA, 'function_name': quota.FUNCTION, 'function_nargs': 0,
            'type': 27, 'enabled': 'O', 'internal': False, 'nonconstraint': True,
            'deferrable': False, 'deferred': False, 'nargs': 0, 'argument_bytes': 0, 'columns': '',
            'unconditional': True, 'old_transition': None, 'new_transition': None,
            'definition': RawStream()(trigger)}],
        'empty': [dict.fromkeys(('runs_empty', 'steps_empty', 'evidence_empty', 'pg17', 'database_ok'), True)],
    }


class QuotaReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.contract, self.samples = sample()

    def assert_bad(self, group, key, values):
        for value in values:
            with self.subTest(group=group, key=key, value=value):
                samples = copy.deepcopy(self.samples)
                samples[group][0][key] = value
                with self.assertRaises((quota.QuotaStop, ValueError, TypeError)):
                    quota.validate(samples, self.contract)

    def test_canonical_catalog_and_new_preparation_remain_ordinary_128(self):
        result = quota.validate(self.samples, self.contract)
        self.assertEqual(result['ordinary_cap'], 128)
        self.assertEqual(result['new_preparation_cap'], 128)
        self.assertNotIn(quota.NEW_RUN, self.samples['constraint'][0]['expression'])

    def test_m45_byte_change_rejected_even_comment_only(self):
        data = (ROOT / quota.M45).read_bytes()
        self.assertEqual(quota.sha(data), quota.M45_SHA)
        for mutated in (data + b'\n', data.replace(b'2349', b'2350'), data.replace(b'else 128', b'else 2349')):
            with self.assertRaisesRegex(quota.QuotaStop, 'm45_source_hash'): quota.source_contract(mutated)

    def test_ast_ignores_locations_parentheses_case_and_sql_comments_only(self):
        samples = copy.deepcopy(self.samples)
        text = samples['constraint'][0]['expression']
        samples['constraint'][0]['expression'] = '\n(/* inert source-coordinate shift */\n' + text + ')'
        quota.validate(samples, self.contract)
        self.assertEqual(quota.strip_locations({'location': 1, 'stmt_len': 9,
            'expr': {'arg_location': 2, 'sval': 'keep'}}), {'expr': {'sval': 'keep'}})

    def test_constraint_tampering_cannot_pass_by_containing_canonical_text(self):
        canonical = self.samples['constraint'][0]['expression']
        changes = [canonical + ' OR true', 'true /* ' + canonical + ' */',
            canonical.replace('>= 0', '> 0'), canonical.replace('2237', '2349'),
            canonical.replace('2349', '2350'), canonical.replace('ELSE 128', 'ELSE 2349'),
            canonical.replace('command_count', 'next_step'),
            canonical + '; SELECT 1', canonical.replace('AND', 'OR')]
        for expression in changes:
            self.assertNotEqual(expression, canonical)
            with self.subTest(expression=expression):
                samples = copy.deepcopy(self.samples)
                samples['constraint'][0]['expression'] = expression
                with self.assertRaises(Exception): quota.validate(samples, self.contract)

    def test_preparation_id_exception_is_rejected_not_granted_2349(self):
        expression = self.samples['constraint'][0]['expression']
        historical = re.findall(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', expression)[1]
        self.assert_bad('constraint', 'expression', [expression.replace(historical, quota.NEW_RUN)])

    def test_unvalidated_or_wrong_constraint_identity_blocks(self):
        for key, values in {'validated': [False, 1], 'kind': ['f'], 'noinherit': [True],
                'local': [False], 'inherited': [1], 'schema': ['public'], 'relation': ['steps'],
                'name': ['different'], 'deferrable': [True], 'deferred': [True]}.items():
            self.assert_bad('constraint', key, values)

    def test_function_body_and_security_properties_are_exact(self):
        for key, values in {'body': ['begin return NEW; end', self.contract['body'] + '\n'],
                'definer': [True, 0], 'owner': ['authenticated'], 'language': ['sql'],
                'nargs': [1], 'returns_trigger': [False], 'kind': ['p'],
                'leakproof': [True], 'strict': [True], 'volatility': ['i'], 'parallel': ['s'],
                'config': [None, [], ['search_path=public, pg_catalog, pg_temp'],
                           ['search_path=pg_catalog, pg_temp', 'row_security=off']]}.items():
            self.assert_bad('function', key, values)

    def test_effective_acl_or_extra_grantee_blocks(self):
        for role in ('anon', 'authenticated', 'service_role'):
            permissions = dict.fromkeys(('anon', 'authenticated', 'service_role'), False)
            permissions[role] = True
            self.assert_bad('function', 'effective_execute', [permissions])
        owner = self.samples['function'][0]['acl'][0]
        self.assert_bad('function', 'acl', [None, [], [dict(owner, grantable=True)], [dict(owner, grantable=0)],
            [owner, dict(owner, grantee='PUBLIC')], [owner, dict(owner, grantee='another_role')]])
        self.assert_bad('function', 'effective_execute', [{'anon': 0, 'authenticated': False, 'service_role': False}])

    def test_trigger_identity_events_enabled_and_condition_are_exact(self):
        for key, values in {'function_schema': ['public'], 'function_name': ['single_endchain_receipt'],
                'function_nargs': [1], 'relation': ['steps'], 'schema': ['public'], 'type': [25, 31],
                'enabled': ['D', 'A', 'R'], 'internal': [True], 'nonconstraint': [False],
                'deferrable': [True], 'deferred': [True], 'nargs': [1], 'argument_bytes': [1],
                'columns': ['1'], 'unconditional': [False], 'old_transition': ['old_rows'],
                'new_transition': ['new_rows']}.items():
            self.assert_bad('trigger', key, values)
        definition = self.samples['trigger'][0]['definition']
        self.assert_bad('trigger', 'definition', [definition.replace('BEFORE', 'AFTER'),
            definition.replace('FOR EACH ROW', 'FOR EACH STATEMENT'), definition + '; SELECT 1'])

    def test_nonempty_evidence_or_wrong_server_blocks(self):
        for field in self.samples['empty'][0]: self.assert_bad('empty', field, [False, 1])

    def test_missing_or_duplicate_catalog_object_blocks(self):
        for name in self.samples:
            for replacement in ([], None, self.samples[name] * 2):
                samples = copy.deepcopy(self.samples); samples[name] = replacement
                with self.assertRaises(quota.QuotaStop): quota.validate(samples, self.contract)

    def test_queries_never_send_uuid_values_or_mutating_ast(self):
        forbidden = {'InsertStmt', 'UpdateStmt', 'DeleteStmt', 'MergeStmt', 'CallStmt', 'DoStmt',
                     'CreateFunctionStmt', 'AlterTableStmt', 'TransactionStmt'}
        def visit(value):
            if isinstance(value, dict):
                self.assertNotIn(value.get('@'), forbidden)
                for child in value.values(): visit(child)
            elif isinstance(value, list):
                for child in value: visit(child)
        for query in quota.QUERIES.values():
            self.assertFalse(re.search(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', query))
            visit(quota.single_node(query, 'SelectStmt')())

    def gate(self):
        saved = {}
        def save(name, value):
            self.assertNotIn(name, saved); saved[name] = copy.deepcopy(value)
        gate = types.SimpleNamespace(sources=ROOT, container='supabase_db_fmz-db41-ci', save=save,
                                     rows=Mock(side_effect=[self.samples[k] for k in quota.QUERIES]))
        return gate, saved

    def test_run_uses_only_four_rows_calls_and_flat_receipt(self):
        gate, saved = self.gate()
        with patch.dict(os.environ, CI_ENV): result = quota.run(gate)
        self.assertEqual(result['status'], 'COMPONENT_PASS')
        self.assertEqual(result['sql_commands_confirmed'], 4)
        self.assertEqual(result['mutation_commands'], 0)
        self.assertEqual(result['new_preparation_cap'], 128)
        self.assertFalse(result['quota_2349_admitted'])
        self.assertTrue(all(not isinstance(v, (list, dict)) for v in result.values()))
        self.assertEqual([c.args[0] for c in gate.rows.call_args_list], list(quota.QUERIES.values()))
        self.assertEqual(len(saved), 2)

    def test_run_rejects_non_ci_or_wrong_container_before_rows(self):
        for field, value in (('GITHUB_ACTIONS', 'false'), ('GITHUB_REPOSITORY', 'other/repo'),
                             ('GITHUB_REF', 'refs/heads/other'), ('container', 'hosted')):
            gate, saved = self.gate(); env = dict(CI_ENV)
            if field == 'container': gate.container = value
            else: env[field] = value
            with patch.dict(os.environ, env), self.assertRaises(quota.QuotaStop): quota.run(gate)
            gate.rows.assert_not_called()
            self.assertEqual(saved['admission-quota-readonly.json']['sql_commands_attempted'], 0)

    def test_run_tampering_raises_and_persists_no_go(self):
        gate, saved = self.gate()
        self.samples['constraint'][0]['validated'] = False
        with patch.dict(os.environ, CI_ENV), self.assertRaises(quota.QuotaStop): quota.run(gate)
        self.assertEqual(saved['admission-quota-readonly.json']['status'], 'NO_GO')

    def test_run_source_hash_failure_stops_before_any_catalog_dispatch(self):
        gate, saved = self.gate()
        with patch.dict(os.environ, CI_ENV), patch.object(quota.pathlib.Path, 'read_bytes', return_value=b'tampered'):
            with self.assertRaisesRegex(quota.QuotaStop, 'm45_source_hash'): quota.run(gate)
        gate.rows.assert_not_called()
        self.assertEqual(saved['admission-quota-readonly.json']['sql_commands_attempted'], 0)

    def test_transport_failure_is_charged_sanitized_and_not_retried(self):
        gate, saved = self.gate(); gate.rows.side_effect = RuntimeError('secret-connection-material')
        with patch.dict(os.environ, CI_ENV), self.assertRaises(quota.QuotaStop): quota.run(gate)
        result = saved['admission-quota-readonly.json']
        self.assertEqual((result['sql_commands_attempted'], result['sql_commands_confirmed']), (1, 0))
        self.assertEqual(gate.rows.call_count, 1)
        self.assertNotIn('secret-connection-material', str(saved))


if __name__ == '__main__': unittest.main()
