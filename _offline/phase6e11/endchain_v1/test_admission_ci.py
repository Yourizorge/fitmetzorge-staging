"""Offline orchestration boundaries, not real PG17/GoTrue proof."""
import ast
import contextlib
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]


class AdmissionCIContract(unittest.TestCase):
    def suspended_admin(self, connection, reconnect, tracked=True):
        # Execute the actual nested context-manager body, not a copied model.
        tree = ast.parse((ROOT/'_offline/phase6e_server_v1/ci_auth.py').read_text())
        function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                        and n.name == 'suspend_admin')
        wrapper = ast.parse('def factory(admin, connect_admin, tracked_auth_factory):\n'
                            '    suspended = False\n').body[0]
        wrapper.body += [function, ast.Return(ast.Name(id='suspend_admin', ctx=ast.Load()))]
        module = ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[]))
        namespace = {'contextlib': contextlib, 'sys': sys}
        exec(compile(module, '<actual-ci-admin-context>', 'exec'), namespace)
        admin = types.SimpleNamespace(connection=connection)
        return admin, namespace['factory'](admin, reconnect, object() if tracked else None)

    def test_admin_is_closed_during_scope_check_and_reconnected_once(self):
        old = Mock(closed=False)
        old.close.side_effect = lambda: setattr(old, 'closed', True)
        new = Mock(closed=False); reconnect = Mock(return_value=new)
        admin, suspend = self.suspended_admin(old, reconnect)
        with suspend():
            self.assertTrue(old.closed)
            reconnect.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, 'suspend_scope'):
                with suspend(): pass
        reconnect.assert_called_once_with()
        self.assertIs(admin.connection, new)

    def test_scope_error_survives_failed_admin_reconnect(self):
        old = Mock(closed=False)
        old.close.side_effect = lambda: setattr(old, 'closed', True)
        _, suspend = self.suspended_admin(old, Mock(side_effect=OSError('private detail')))
        with self.assertRaisesRegex(ValueError, 'scope failure') as caught:
            with suspend(): raise ValueError('scope failure')
        self.assertEqual(caught.exception.__notes__, ['secondary_admin_reconnect_failure:OSError'])

    def test_admin_suspend_never_available_to_default_auth_flow(self):
        old = Mock(closed=False); reconnect = Mock()
        _, suspend = self.suspended_admin(old, reconnect, tracked=False)
        with self.assertRaisesRegex(RuntimeError, 'suspend_scope'):
            with suspend(): pass
        old.close.assert_not_called(); reconnect.assert_not_called()

    def test_reconnected_admin_is_owned_by_exitstack(self):
        text = (ROOT/'_offline/phase6e_server_v1/ci_auth.py').read_text()
        self.assertIn('with contextlib.ExitStack() as connections:', text)
        self.assertIn('return connections.enter_context(psycopg.connect(dsn,autocommit=True,', text)
        self.assertIn("ctx.pop('suspend_admin',None)", text)

    def test_local_contracts_precede_expensive_app_matrix(self):
        tree = ast.parse((HERE/'admission_ci.py').read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == 'regressions')
        calls = [ast.unparse(n.value.func) for n in method.body
                 if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
        self.assertEqual(calls[:2], ['self.admission_units', 'super().regressions'])
        nested = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
        component = next(n for n in nested if ast.unparse(n.func) == 'self.run_components')
        budget = next(n for n in nested if ast.unparse(n.func) == 'admission_budget.run')
        application = next(n for n in nested if ast.unparse(n.func) == 'super().regressions')
        self.assertLess(component.lineno, budget.lineno)
        self.assertLess(budget.lineno, application.lineno)

    def test_budget_modules_are_verified_before_publication(self):
        tree = ast.parse((HERE/'admission_ci.py').read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == 'regressions')
        calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
        binding = next(n for n in calls if ast.unparse(n.func) == 'self.bind_modules')
        publish = next(n for n in calls if ast.unparse(n.func) == 'admission_budget.run')
        self.assertLess(binding.lineno, publish.lineno)
        self.assertEqual([ast.unparse(arg) for arg in binding.args],
                         ['admission_budget', 'admission_budget_register',
                          'admission_budget_receipts', 'admission_budget_graph'])

    def test_new_workflow_is_main_only_disposable_without_hosted_secrets(self):
        text = (ROOT/'.github/workflows/phase6e-admission-local-ci.yml').read_text()
        for value in ("github.repository == 'Yourizorge/fitmetzorge-staging'",
                      "github.ref == 'refs/heads/main'", 'github.run_attempt == 1',
                      'persist-credentials: false', 'contents: read', 'timeout-minutes: 25'):
            self.assertIn(value, text)
        for forbidden in ('secrets.', 'id-token: write', 'supabase db push',
                          'hosted_gate.py', 'secrets: inherit', 'continue-on-error: true'):
            self.assertNotIn(forbidden, text)

    def test_strict_wal_no_fourth_diagnostic_or_admission_bypass(self):
        text = (HERE/'admission_ci.py').read_text()
        ast.parse(text)
        self.assertNotIn('ci_wal_diagnostic', text)
        self.assertNotIn('warmup', text)
        self.assertIn("'exhausted_wal_diagnostic_reexecuted': False", text)
        self.assertIn("raise RuntimeError('complete_admission_blocked_not_component_failure')", text)
        self.assertNotIn("['full_chain_admission'] = True", text)

    def test_original_application_entry_remains_default(self):
        text = (ROOT/'_offline/phase6e_server_v1/ops.py').read_text()
        self.assertIn("WORKFLOW='phase6e-server-local-ci.yml'", text)
        new = (HERE/'admission_ops.py').read_text()
        self.assertIn("ops.WORKFLOW = 'phase6e-admission-local-ci.yml'", new)
        self.assertNotIn('hosted_gate', new)

    def test_test_admin_capability_is_private_opt_in_and_removed(self):
        text = (ROOT/'_offline/phase6e_server_v1/ci_auth.py').read_text()
        self.assertIn('include_test_admin=False', text)
        self.assertIn("if include_test_admin:ctx['test_admin_token']=admin_token", text)
        self.assertIn("ctx.pop('test_admin_token',None)", text)
        self.assertIn("if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging'", text)
        for line in text.splitlines():
            if 'test_admin_token' in line:
                self.assertNotIn('save(', line)
                self.assertNotIn('print(', line)

    def test_old_binding_is_not_mutated_by_new_preparation(self):
        module = ast.parse((HERE/'admission_binding.py').read_text())
        for node in ast.walk(module):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, ('write_text', 'write_bytes', 'unlink', 'rename'))
                if node.func.attr == 'replace':
                    self.assertEqual(ast.unparse(node), "value.replace('Z', '+00:00')")

    def test_auth_environment_closure_retains_its_receipt_namespace(self):
        tree = ast.parse((HERE/'admission_ci.py').read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == 'run_components')
        context = next(n for n in ast.walk(method) if isinstance(n, ast.With))
        cleanup = next(n for n in context.body if isinstance(n, ast.Try)).finalbody
        self.assertIn('auth_failure_context.clear()', ast.unparse(cleanup[0]))
        self.assertIn("original_save('admission-auth-' + name, value)",
                      ast.unparse(cleanup[-1]))

    def test_unconfirmed_fault_cleanup_blocks_following_fixture_mutation(self):
        tree = ast.parse((HERE/'admission_ci.py').read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == 'run_components')
        check = next(n for n in ast.walk(method) if isinstance(n, ast.If)
                     and 'diagnostic_subset_verified' in ast.unparse(n.test))
        self.assertIn("matrix.get('diagnostic_subset_verified') is not True", ast.unparse(check.test))
        self.assertIsInstance(check.body[0], ast.Raise)
        predicate = compile(ast.Expression(check.test), '<actual-admission-guard>', 'eval')
        for matrix, blocked in (({}, True), ({'diagnostic_subset_verified': False}, True),
                                ({'diagnostic_subset_verified': True}, False),
                                ({'diagnostic_subset_verified': True,
                                  'bootstrap_or_runner_failure': 'failure'}, True)):
            self.assertEqual(bool(eval(predicate, {'__builtins__': {}}, {'matrix': matrix})), blocked)
        mutation = next(n for n in ast.walk(method) if isinstance(n, ast.Call)
                        and ast.unparse(n.func) == 'admission_fixture_context.run')
        self.assertLess(check.lineno, mutation.lineno)


if __name__ == '__main__': unittest.main()
