"""Offline release-security checks. No database, HTTP, or hosted admission.

Requires the existing psycopg and pglast dependencies. Deliberately failing
regressions identify unfixed boundaries; do not skip or invert them for CI.
"""
import io
import os
import pathlib
import socket
import unittest
import urllib.request
import urllib.response
from email.message import Message
from unittest.mock import patch

from pglast import ast, parse_sql
from pglast.stream import RawStream
import store

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = pathlib.Path(__file__).resolve().parent
SCHEMA = "fmz6e_integration_private"


def sql_nodes(paths):
    return [raw.stmt for path in paths
            for raw in parse_sql(path.read_text(encoding="utf-8-sig"))]


def function_name(node):
    return ".".join(part.sval for part in node.funcname)


def function_body(node):
    return next(option.arg[0].sval for option in node.options
                if option.defname == "as")


class SqlSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = sql_nodes(sorted((ROOT / "supabase/migrations").glob("*.sql")))
        cls.app = sql_nodes(sorted((APP / "supabase/migrations").glob("*.sql")))
        cls.functions = {}
        for node in cls.canonical:
            if isinstance(node, ast.CreateFunctionStmt):
                cls.functions[function_name(node)] = node
        cls.policies = [n for n in cls.app if isinstance(n, ast.CreatePolicyStmt)]

    def test_effective_signup_does_not_authorize_from_user_metadata(self):
        body = function_body(self.functions["public.fmz_handle_new_auth_user"])
        self.assertNotIn("raw_user_meta_data", body)
        self.assertNotIn("fmz_bootstrap_trainer_profile", body)
        bootstrap = function_body(self.functions["public.fmz_bootstrap_trainer_profile"])
        self.assertIn("p_user_id is distinct from v_uid", bootstrap)
        self.assertIn("values(v_uid,'client'", bootstrap)

    def test_profile_identity_columns_are_not_browser_writable(self):
        path = ROOT / "supabase/migrations/20260904105918_phase6d0_legacy_authorization_gate.sql"
        nodes = sql_nodes([path])
        grants = [RawStream()(n) for n in nodes if isinstance(n, ast.GrantStmt)]
        self.assertIn("REVOKE ALL PRIVILEGES ON TABLE public.profiles FROM PUBLIC, anon, authenticated", grants)
        self.assertIn("GRANT UPDATE (name) ON TABLE public.profiles TO authenticated", grants)

    def test_all_six_app_tables_enable_rls(self):
        tables = {n.relation.relname for n in self.app if isinstance(n, ast.CreateStmt)}
        self.assertEqual(tables, {"subjects", "workspaces", "revisions", "requests", "audit", "outbox"})
        for table in tables:
            with self.subTest(table=table):
                self.assertTrue(any(isinstance(n, ast.AlterTableStmt)
                    and n.relation.relname == table
                    and any(c.subtype.name == "AT_EnableRowSecurity" for c in n.cmds)
                    for n in self.app))

    def test_app_policies_only_target_restricted_server_role(self):
        self.assertEqual(len(self.policies), 12)
        for policy in self.policies:
            with self.subTest(policy=policy.policy_name):
                self.assertEqual([r.rolename for r in policy.roles], ["fmz6e_integration_server"])
                self.assertIsNotNone(policy.qual or policy.with_check)

    def test_update_has_using_check_and_matching_select(self):
        updates = [p for p in self.policies if p.cmd_name == "update"]
        self.assertEqual({p.table.relname for p in updates}, {"workspaces", "outbox"})
        for policy in updates:
            with self.subTest(table=policy.table.relname):
                self.assertIsNotNone(policy.qual)
                self.assertIsNotNone(policy.with_check)
                self.assertTrue(any(p.cmd_name == "select"
                    and p.table.relname == policy.table.relname for p in self.policies))
                for expression in (policy.qual, policy.with_check):
                    self.assertIn(SCHEMA + ".actor()", RawStream()(expression))

    def test_app_functions_are_invoker_with_fixed_search_path(self):
        functions = [n for n in self.app if isinstance(n, ast.CreateFunctionStmt)]
        self.assertEqual({function_name(n) for n in functions},
                         {SCHEMA + "." + n for n in ("actor", "observe", "outbox_append")})
        for node in functions:
            with self.subTest(function=function_name(node)):
                security = next(o.arg.boolval for o in node.options if o.defname == "security")
                self.assertFalse(security)
                self.assertIn("SET search_path TO 'pg_catalog', 'pg_temp'", RawStream()(node))

    def test_no_new_views_or_storage_relations_in_release_sql(self):
        self.assertFalse(any(isinstance(n, ast.ViewStmt) for n in self.canonical + self.app))
        self.assertFalse(any(isinstance(n, ast.CreateStmt)
            and n.relation.schemaname == "storage" for n in self.canonical + self.app))

    def test_app_execute_and_schema_are_closed_to_browser_roles(self):
        rendered = "\n".join(RawStream()(n) for n in self.app if isinstance(n, ast.GrantStmt))
        self.assertIn("REVOKE ALL PRIVILEGES ON SCHEMA " + SCHEMA +
                      " FROM PUBLIC, anon, authenticated, service_role", rendered)
        self.assertIn("REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA " + SCHEMA +
                      " FROM PUBLIC, anon, authenticated, service_role", rendered)
        self.assertIn("REVOKE ALL PRIVILEGES ON FUNCTION " + SCHEMA +
                      ".outbox_append () FROM PUBLIC, anon, authenticated, service_role", rendered)

    def test_app_update_grants_cannot_change_identity_or_expiry(self):
        updates = [n for n in self.app if isinstance(n, ast.GrantStmt)
                   and n.is_grant and n.privileges
                   and any(p.priv_name == "update" for p in n.privileges)]
        actual = {n.objects[0].relname: [c.sval for p in n.privileges for c in (p.cols or ())]
                  for n in updates}
        self.assertEqual(actual, {"workspaces": ["version", "consent", "state_text", "state_sha"],
                                  "outbox": ["status", "history"]})

    def test_endchain_principal_requires_live_exact_synthetic_identity(self):
        body = function_body(self.functions["fmz6e11_private.principal"])
        for fragment in ("auth.sessions", "s.user_id=u", "session_id",
                         "s.not_after>clock_timestamp()", "identities where user_id=u and enabled",
                         "proof_hash", "p.role is distinct from", "a.email=case r.role"):
            self.assertIn(fragment, body)
        self.assertNotIn("user_metadata", body)

    def test_endchain_replay_is_session_actor_payload_and_pair_bound(self):
        body = function_body(self.functions["fmz6e11_request_private.call"])
        for fragment in ("current_user<>'postgres'", "old.actor<>(p->>'uid')::uuid",
                         "old.session_id<>(c->>'session_id')::uuid", "old.payload_sha<>payload_sha",
                         "old.idempotency_key<>(q->>'key')::uuid", "old.state<>'pair_validated'",
                         "request_previous_pair_incomplete"):
            self.assertIn(fragment, body)

    def test_endchain_seal_requires_new_transaction_and_unchanged_state(self):
        body = function_body(self.functions["fmz6e11_request_private.seal"])
        for fragment in ("current_user<>'postgres'", "r.xid=pg_current_xact_id()",
                         "h<>r.after_sha", "seal_pair"):
            self.assertIn(fragment, body)


class LocalBoundary(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")).start()
        patch.object(socket, "socket", side_effect=AssertionError("network forbidden")).start()
        self.connect = patch.object(store.psycopg, "connect",
                                    side_effect=AssertionError("database forbidden")).start()
        patch.object(store.pathlib.Path, "is_file", return_value=True).start()
        self.dsn = "host=127.0.0.1 sslmode=verify-full sslrootcert=synthetic-ca"

    def test_feature_and_package21_remain_default_off(self):
        with self.assertRaisesRegex(store.Denied, "feature_disabled"):
            store.Store(self.dsn, None)
        self.assertFalse(store.Store(self.dsn, None, enabled=True).full_day21)

    def test_remote_host_is_rejected_without_connecting(self):
        with self.assertRaisesRegex(store.Denied, "local_database_boundary"):
            store.Store(self.dsn.replace("127.0.0.1", "192.0.2.1"), None, enabled=True)
        self.connect.assert_not_called()

    def test_nonloopback_hostaddr_is_rejected_without_connecting(self):
        with self.assertRaisesRegex(store.Denied, "local_database_boundary"):
            store.Store(self.dsn + " hostaddr=192.0.2.1", None, enabled=True)
        self.connect.assert_not_called()

    def test_environment_hostaddr_cannot_redirect_local_connection(self):
        with patch.dict(os.environ, {"PGHOSTADDR": "192.0.2.1"}):
            try:
                instance = store.Store(self.dsn, None, enabled=True)
            except store.Denied:
                return
            self.connect.side_effect = None
            instance.connect()
            args, kwargs = self.connect.call_args
            settings = store.conninfo_to_dict(args[0])
            address = kwargs.get("hostaddr", settings.get("hostaddr", os.environ["PGHOSTADDR"]))
            self.assertIn(address, ("127.0.0.1", "::1"),
                          "Effective libpq address must not inherit a non-loopback PGHOSTADDR")

    def test_local_auth_cannot_redirect_bearer_off_loopback(self):
        observed = []

        def http_open(handler, request):
            observed.append((request.full_url, request.has_header("Authorization")))
            headers = Message()
            if len(observed) == 1:
                headers["Location"] = "http://outside.invalid/user"
                code, body = 302, b""
            else:
                code, body = 200, b"{}"
            response = urllib.response.addinfourl(io.BytesIO(body), headers, request.full_url, code)
            response.msg = "synthetic"
            return response

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with patch.object(urllib.request.HTTPHandler, "http_open", new=http_open), \
                patch.object(urllib.request, "_opener", opener):
            with self.assertRaises(store.Denied):
                store.LocalAuth("http://127.0.0.1:59999").call("/user", "synthetic-not-a-token")
        self.assertEqual(observed, [("http://127.0.0.1:59999/user", True)])

    def test_session_denial_precedes_claims_or_role_binding(self):
        class MissingSession:
            def __init__(self):
                self.calls = []

            def execute(self, query, parameters):
                self.calls.append(query)
                return self

            def fetchone(self):
                return {"live": False}

        db = MissingSession()
        with self.assertRaisesRegex(store.Denied, "session_expired_or_revoked"):
            object.__new__(store.Store).bind(db, {"sub": "synthetic", "session_id": "synthetic"}, "synthetic")
        self.assertEqual(len(db.calls), 1)
        self.assertIn("auth.sessions", db.calls[0])


if __name__ == "__main__":
    unittest.main()
