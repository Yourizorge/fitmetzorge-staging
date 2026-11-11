"""Integrated source/HTTP/parent-engine tests; PG, Docker and root compiler mocked."""
import contextlib
import copy
import json
import pathlib
import types
import unittest
from unittest.mock import patch

import test_runtime_registered_bootstrap as base
from quota_candidate_v1 import runtime_registered_bootstrap as b
from quota_candidate_v1 import runtime_registered_cleanup as cleanup
from quota_candidate_v1 import runtime_registered_startup as startup
import auth_failure as af
import auth_failure_parent_finalizer as parent
import auth_failure_tracked as tracked
import fixture_producer_scope as producer
import test_fixture_producer_scope as catalogs


class FakeLedger:
    """Test double only; never passes Context._admit."""
    def __init__(self, binding):
        self._binding = binding
        self.events = []
        self.fail_name = None
        self.primary = RuntimeError("original bootstrap failure")
        self.pending = None
        self.deferred = []
        self.unions = []
    def precharge(self, name):
        if self.pending is not None:
            raise AssertionError("nested root precharge")
        if name == self.fail_name:
            raise self.primary
        ticket = types.SimpleNamespace(command_id=name)
        self.pending = ticket
        self.events.append(("precharge", name))
        return ticket
    def confirm(self, ticket, **kw):
        if self.pending is not ticket: raise AssertionError("wrong ticket")
        self.pending = None
        self.events.append(("confirmed", ticket.command_id, kw))
    def unknown(self, ticket, **kw):
        if self.pending is not ticket: raise AssertionError("wrong ticket")
        self.pending = None
        self.events.append(("unknown", ticket.command_id, kw))
    def fault(self, ticket, **kw):
        if self.pending is not ticket: raise AssertionError("wrong ticket")
        self.pending = None
        self.events.append(("fault", ticket.command_id, kw))
    def select_cleanup(self, context):
        if self.pending is not None: raise AssertionError("cleanup with active ticket")
        if context.execution_ledger is not self: raise AssertionError("foreign context")
        self.events.append(("select_cleanup",))
    def defer(self, ticket):
        if self.pending is not ticket: raise AssertionError("wrong ticket")
        self.pending = None
        self.deferred.append(ticket)
        self.events.append(("deferred", ticket.command_id))
    def defer_fault(self, ticket):
        if self.pending is not ticket: raise AssertionError("wrong ticket")
        self.pending = None
        self.deferred.append(ticket)
        self.events.append(("deferred_fault", ticket.command_id))
    def settle_deferred(self, ticket, **kw):
        self.deferred.remove(ticket)
        self.events.append(("settled", ticket.command_id, kw))
    def deferred_group(self, group):
        return tuple(t for t in self.deferred if t.command_id.startswith("auth.create.")
                     or t.command_id.endswith(":delete") or t.command_id == "case.core")
    def settle_union(self, tickets, *, observed_sql_commands):
        self.unions.append(observed_sql_commands)
        for ticket in tickets: self.deferred.remove(ticket)
    def close(self):
        return {"events": [{"state": "unknown_consumed"}],
                "observed_sql_commands": sum(self.unions), "test_only": True}
    def close_envelope(self, *args, **kw):
        self.events.append(("envelope_closed", kw))


class JoinTests(unittest.TestCase):
    stop_server = base.ContextTests.stop_server

    def setUp(self):
        base.ContextTests.setUp(self)
        self.gate.container = startup.PG_NAME
        self.saved = {}
        self.gate.save = self.publish
        self.gate.work = self.out
        manifest = {"sources": {p.relative_to(base.ROOT).as_posix(): tracked.sha(p.read_bytes())
                                for p in base.ROOT.rglob("*") if p.is_file()}}
        (self.out / "candidate.json").write_text(json.dumps(manifest))
        env = patch.dict(base.os.environ, {"GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "Yourizorge/fitmetzorge-staging", "GITHUB_REF": "refs/heads/main"})
        env.start(); self.addCleanup(env.stop)
        self.binding = {"run_id": self.run_id, "source_commit": "a"*40, "ci_run": "123"}
        self.ledger = FakeLedger(self.binding)
        self.ctx = b.Context(self.gate, binding=self.binding,
            stack={"status": "CLEAN47_BOOTSTRAP_PASS"}, ledger=self.ledger)
        self.ctx.ledger.__class__.__module__ = "admission_budget_root_runtime"
        self.wire = catalogs.Wire(catalogs.samples(producer.source_contract(self.gate)))
        self.fk = {"identities": 0, "operators": 0}
        self.backend_reads = []
        outer = self

        class Backend:
            autocommit = True
            def __init__(self):
                self.db = self
            def execute(self, sql, args=None):
                outer.backend_reads.append(sql)
                if sql == parent.BOUNDARY:
                    value = dict.fromkeys(("pg17", "tls", "bounded_statement", "bounded_lock", "privileged", "fresh"), True)
                elif sql == parent.FK:
                    value = outer.fk
                else:
                    raise AssertionError("unexpected SQL")
                return types.SimpleNamespace(fetchone=lambda: {"value": copy.deepcopy(value)})
            def snapshot(self, email, marker, actor, session_ids):
                outer.backend_reads.append("snapshot")
                user = outer.users.get(actor)
                counts = dict.fromkeys(("users", "identities", "sessions", "refresh_tokens",
                    "mfa_amr_claims", "mfa_factors", "one_time_tokens", "flow_state"), 0)
                counts["users"] = counts["identities"] = int(user is not None)
                return {"users": [{**user, "marker": None}] if user else [],
                        "session_ids": [], "counts": counts}
            def stats(self):
                outer.backend_reads.append("stats")
                return len(outer.requests)
            def difference(self, before, after):
                return {"commands": after-before, "mock_only": True}
            def close(self): pass

        class Server:
            def __init__(self, owner):
                self.owner = owner
                self.parameters = {"sslrootcert": str(outer.out / "ca"),
                                   "host": "127.0.0.1", "hostaddr": "127.0.0.1"}
                self.dsn, self.admin, self.anon = "PRIVATE_DSN", "PRIVATE_TEST_ADMIN", "PRIVATE_ANON"
                self.runtime = types.SimpleNamespace(context=lambda ids: {"registeredIds": ids})
                self.profile_receipt = {"mock_only": True}
                self.suspended = False
            def open(self):
                return {"test_only": True}
            @contextlib.contextmanager
            def suspend(self):
                self.suspended = True
                try: yield
                finally: self.suspended = False
            def close(self):
                return {"process_stopped": True, "managed_sql": {"commands": len(outer.requests)},
                        "account_deletion_proven": False}

        def admit(owner):
            owner.execution_ledger = outer.ledger
            owner._envelope = object()
            owner._admitted = True
            owner._managed_group = "auth.managed_lifetime"
            owner._extra_modules = [startup, cleanup, parent, producer, cleanup.pre, cleanup.durable]
            owner._extra_binding = b.source_binding.verify(owner.gate, owner._extra_modules)

        def scope_runtime(gate):
            self.assertTrue(outer.ctx.server.suspended)
            return outer.wire
        for target, name, value in (
                (b.Context, "_admit", admit), (startup, "LocalServer", Server),
                (af, "RealBackend", lambda _: Backend()), (af, "ORIGINS", (self.origin,)),
                (producer.NativeRuntime, "disposable", scope_runtime)):
            p = patch.object(target, name, value)
            p.start(); self.addCleanup(p.stop)

    def publish(self, name, value):
        self.saved[name] = copy.deepcopy(value)
        with (self.out / name).open("x") as stream:
            json.dump(value, stream, sort_keys=True)

    def run_prefix(self, count):
        if count < 3:
            self.ledger.fail_name = "auth.create." + b.ROLES[count]
        else:
            # Fault after last ownership is journaled but before any seed begins.
            original = b.BootstrapRequests.close
            def close(producer):
                value = original(producer)
                if not self.ctx._closing:
                    raise self.ledger.primary
                return value
            p = patch.object(b.BootstrapRequests, "close", close)
            p.start(); self.addCleanup(p.stop)
        with self.assertRaises(RuntimeError) as caught:
            with self.ctx: self.fail("failure prefix yielded")
        self.assertIs(caught.exception, self.ledger.primary)
        return self.ctx.closeout

    def assert_prefix(self, count):
        report = self.run_prefix(count)
        self.assertTrue(report["deletion_proven"], report)
        self.assertEqual(self.users, {})
        self.assertEqual(len(self.requests), count * 2)
        self.assertEqual(report["known_owners"], count)
        self.assertFalse(report["global_zero_claim"])
        self.assertFalse(report["full_chain_admission"])
        self.assertFalse(report["original_claims_released"])
        engine = report["cleanup"]
        self.assertEqual(engine["native_dispatches"], 3 + 5*count)
        self.assertEqual(engine["http_attempts"], count)
        self.assertEqual(engine["prepaid_consumed"], 3 + 133*count)
        self.assertEqual(len(self.wire.calls), 10)
        raw = json.dumps(report)
        self.assertNotIn("PRIVATE_DSN", raw)
        self.assertNotIn("PRIVATE_TEST_ADMIN", raw)

    def test_prefix_zero_actual_engine(self): self.assert_prefix(0)
    def test_prefix_one_actual_http_delete_and_engine(self): self.assert_prefix(1)
    def test_prefix_two_actual_http_delete_and_engine(self): self.assert_prefix(2)
    def test_prefix_three_actual_http_delete_and_engine(self): self.assert_prefix(3)

    def test_failed_C_catalog_blocks_before_delete(self):
        self.wire.data["privileges"][0]["createrole"] = True
        report = self.run_prefix(1)
        self.assertFalse(report["deletion_proven"])
        self.assertEqual(len(self.users), 1)
        self.assertEqual(self.backend_reads, [])
        self.assertEqual(len(self.requests), 1)

    def test_private_fk_blocks_before_delete(self):
        self.fk["identities"] = 1
        report = self.run_prefix(1)
        self.assertFalse(report["deletion_proven"])
        self.assertEqual(len(self.users), 1)

    def test_truncated_create_retained_no_cleanup(self):
        self.fail_request, self.response_kind = 2, "truncated"
        with self.assertRaises(base.transport.UnknownOutcome):
            with self.ctx: self.fail("unknown create yielded")
        self.assertEqual(len(self.users), 2)
        self.assertFalse(self.ctx.closeout["deletion_proven"])
        self.assertEqual(self.backend_reads, [])

    def test_stopped_process_does_not_delete_seeded_owners(self):
        with patch.object(b.Context, "_seed", lambda owner: setattr(owner, "_seed_attempted", True)):
            with self.assertRaisesRegex(tracked.Blocked, "cleanup_join_pending"):
                with self.ctx: pass
        self.assertEqual(len(self.users), 3)
        self.assertFalse(self.ctx.closeout["deletion_proven"])
        self.assertTrue(self.ctx.closeout["process"]["process_stopped"])

    def test_original_body_exception_retained(self):
        primary = LookupError("body")
        with patch.object(b.Context, "_seed", lambda owner: setattr(owner, "_seed_attempted", True)):
            with self.assertRaises(LookupError) as caught:
                with self.ctx: raise primary
        self.assertIs(caught.exception, primary)
        self.assertEqual(len(self.users), 3)

    def test_public_capability_cannot_be_forged(self):
        with self.assertRaises(TypeError): cleanup.Prerequisite()
        proof = object.__new__(cleanup.Prerequisite)
        with self.assertRaises(tracked.Blocked): _ = proof.roles

    def test_direct_cleanup_without_real_context_finalizer_denied(self):
        with self.assertRaisesRegex(tracked.Blocked, "context_finalizer_origin"):
            cleanup.run(self.ctx, RuntimeError("fake"))

    def test_close_receipt_failure_preserves_original(self):
        original = tracked.Records.save
        def save(records, kind, value):
            if kind == "closeout":
                raise OSError("synthetic write failure")
            return original(records, kind, value)
        with patch.object(tracked.Records, "save", save):
            report = self.run_prefix(0)
        self.assertEqual(report["original_exception_class"], "RuntimeError")
        self.assertTrue(any(v["phase"] == "receipt" for v in report["secondary_errors"]))

    def test_stop_failure_preserves_original(self):
        original = startup.LocalServer.close
        def close(server):
            original(server)
            raise TimeoutError("synthetic stop unknown")
        with patch.object(startup.LocalServer, "close", close):
            self.run_prefix(0)
        self.assertTrue(any(v["phase"] == "server_close" for v in self.ctx.closeout["secondary_errors"]))

    def test_seed_attempt_blocks_preseed_capability(self):
        original = b.Context._seed
        primary = RuntimeError("lost seed BEGIN")
        def seed(owner):
            owner._seed_attempted = True
            raise primary
        with patch.object(b.Context, "_seed", seed):
            with self.assertRaises(RuntimeError) as caught:
                with self.ctx: pass
        self.assertIs(caught.exception, primary)
        self.assertEqual(len(self.users), 3)
        self.assertEqual(self.backend_reads, [])

    def test_rejected_nonempty_producer_denies_future_create(self):
        original = b.BootstrapRequests.__init__
        def construct(instance, key, gate, auth, run_id):
            worker = auth.registry.start_worker(lambda: None)
            worker.join(2)
            return original(instance, key, gate, auth, run_id)
        with patch.object(b.BootstrapRequests, "__init__", construct):
            with self.assertRaisesRegex(tracked.Blocked, "fresh_exclusive_registry"):
                with self.ctx: pass
        self.assertEqual(self.ctx.auth.registry.phase, "CLOSED")
        with self.assertRaisesRegex(tracked.Blocked, "future_request_denied"):
            self.ctx.auth.call("/admin/users", "PRIVATE_TEST_ADMIN", {
                "email": "review-only@example.invalid", "email_confirm": True})
        self.assertEqual(self.requests, [])

    def test_closeout_ref_binds_original_complete_record(self):
        self.run_prefix(0)
        ref = self.ctx.closeout_ref
        self.assertIsNotNone(ref)
        data = (self.out / ref["path"]).read_bytes()
        self.assertEqual(tracked.sha(data), ref["sha256"])
        value = json.loads(data)
        self.assertEqual(value["kind"], "closeout")
        self.assertIn("ownership_evidence", value)
        self.assertFalse(value["global_zero_claim"])
        references = b._record_references(self.ctx)
        expected = {p.relative_to(self.out).as_posix() for folder in (
            self.ctx.records.folder, self.ctx.auth.budget.records.folder,
            self.ctx.auth.registry.records.folder, self.ctx.producer.records.folder)
            for p in folder.iterdir()}
        self.assertEqual({r["path"] for r in references}, expected)
        for ref in references:
            raw = (self.out / ref["path"]).read_bytes()
            self.assertEqual((ref["sha256"], ref["bytes"]), (tracked.sha(raw), len(raw)))

    def test_cleanup_selection_failure_still_closes_producer_without_deletes(self):
        with patch.object(self.ledger, "select_cleanup", side_effect=ValueError("suffix denial")):
            report = self.run_prefix(1)
        self.assertFalse(report["deletion_proven"])
        self.assertEqual(len(self.users), 1)
        self.assertEqual(len(self.requests), 1)
        self.assertNotEqual(self.ctx.auth.registry.phase, "OPEN")
        self.assertTrue(any(e["phase"] == "cleanup_selection" for e in report["secondary_errors"]))
        self.assertEqual(self.backend_reads, [])

    def test_terminal_consumer_rejects_changed_original_receipt(self):
        self.run_prefix(0)
        path = self.out / self.ctx.closeout_ref["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises((tracked.Blocked, ValueError)):
            b.validate_closeout(self.ctx, gate=self.gate, binding=self.binding)

    def test_terminal_consumer_does_not_promote_unknown_driver_partition(self):
        self.run_prefix(0)
        with self.assertRaisesRegex(tracked.Blocked, "incomplete_closeout"):
            b.validate_closeout(self.ctx, gate=self.gate, binding=self.binding)

    def test_forged_C_summary_blocks_before_auth_observer_or_delete(self):
        from quota_candidate_v1 import runtime_registered_fixture_closeout as physical
        with patch.object(b.Context, "_seed", lambda owner: setattr(owner, "_seed_ref", {})), patch.object(
                physical, "run", return_value={"physical_zero": True, "registry_absence_confirmed": True}):
            with self.assertRaises(RuntimeError) as caught:
                with self.ctx:
                    self.ctx._case = (object(), object())
                    raise self.ledger.primary
        self.assertIs(caught.exception, self.ledger.primary)
        self.assertEqual(len(self.users), 3)
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.backend_reads, [])
        self.assertFalse(self.ctx.closeout["deletion_proven"])
        self.assertTrue(self.ctx.closeout["cleanup_missing"])


class StartupTests(unittest.TestCase):
    def test_configuration_disables_background_sql_sources(self):
        config = startup.configuration()
        self.assertEqual(config["GOTRUE_DB_MAX_POOL_SIZE"], "1")
        self.assertEqual(config["GOTRUE_DB_CONN_PERCENTAGE"], "0")
        for key in ("GOTRUE_DB_CLEANUP_ENABLED", "GOTRUE_METRICS_ENABLED",
                    "GOTRUE_DB_ADVISOR_ENABLED", "GOTRUE_INDEX_WORKER_ENSURE_USER_SEARCH_INDEXES_EXIST"):
            self.assertEqual(config[key], "false")

    def test_localserver_rejects_fake_owner(self):
        with self.assertRaisesRegex(ValueError, "actual_admitted_context"):
            startup.LocalServer(types.SimpleNamespace(_entering=True, _admitted=True))

    def test_transaction_control_does_not_fetch_non_result(self):
        server = object.__new__(startup.LocalServer)
        cursor = types.SimpleNamespace(description=None,
            fetchone=lambda: self.fail("COMMIT has no rows"))
        server.db = types.SimpleNamespace(execute=lambda *_: cursor)
        server.owner = types.SimpleNamespace(_local_call=lambda name, kind, action: action())
        self.assertIsNone(server._sql("seed.commit", "COMMIT"))



    @contextlib.contextmanager
    def local_process(self, *, wrong_config=False, unknown_start=False, wrong_digest=False,
                      auth_tls=True, writable_ca=False, readiness_status="ready", readiness_polls=1):
        """Actual LocalServer orchestration; only OS/PG/health boundaries mocked."""
        import tempfile
        import hashlib
        import auth_protocol
        with tempfile.TemporaryDirectory() as temporary:
            out = pathlib.Path(temporary)
            ca = out / "fmz-ci-ca.crt"
            ca.write_bytes(b"SYNTHETIC_CA")
            gate = types.SimpleNamespace(work=out, container=startup.PG_NAME)
            owner = b.Context(gate, binding={"run_id": str(base.uuid.uuid4()),
                "source_commit": "a"*40, "ci_run": "123"},
                stack={"container": {"id": "1"*64}, "database_oid": 5,
                       "pg_system_identifier": "1234", "ca_sha256": hashlib.sha256(ca.read_bytes()).hexdigest()},
                ledger=None)
            owner._entering = owner._admitted = True
            owner._source_snapshot = {"test_only": True}
            calls, commands = [], []
            owner._local_call = lambda name, kind, action: (calls.append((name, kind)), action())[1]
            owner._remember = lambda kind, value: {"sha256": "a"*64}
            metadata = {"database": "postgres", "role": "postgres", "version": 170006,
                "oid": 5, "ssl": True, "statement_timeout": "5s", "lock_timeout": "1s",
                "sessions": 0, "registry_empty": True}
            class DB:
                closed = False
                autocommit = True
                def execute(self, sql, args=None):
                    if sql == startup.META: value = {"value": metadata}
                    elif sql == startup.ACTIVE: value = {"n": 0}
                    elif sql == startup.BOUND: value = {"n": 1, "tls": int(auth_tls)}
                    else: value = {"value": 0}
                    return types.SimpleNamespace(description=True, fetchone=lambda: value)
                def close(self): self.closed = True
            class Runtime:
                def __init__(self, *args, **kw): pass
                def connect(self): return DB()
                def clear(self): pass
            pg = {"Id": "1"*64, "State": {"Running": True},
                "Config": {"Env": ["POSTGRES_PASSWORD=PRIVATE"]},
                "NetworkSettings": {"Networks": {"local_net": {}},
                    "Ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54329"}]}}}
            image = {"Id": "sha256:"+"2"*64, "RepoDigests": [
                "supabase/gotrue@sha256:"+"3"*64 if wrong_digest else startup.IMAGE]}
            started_env = {}
            def run(args, **kw):
                commands.append(list(args))
                if args[1:3] == ["image", "inspect"]: data = [image]
                elif args[1] == "exec":
                    if args[2] == "4"*64:
                        self.assertEqual(args[3:], ["/bin/sh", "-c", startup.READINESS_SCRIPT])
                        self.assertEqual(kw["timeout"], startup.READINESS_TIMEOUT)
                        return types.SimpleNamespace(returncode=0, stdout=json.dumps({
                            "status": readiness_status, "polls": readiness_polls}))
                    return types.SimpleNamespace(returncode=0, stdout="PRIVATE_PASSWORD")
                elif args[1] == "run":
                    started_env.update(kw["env"])
                    from urllib.parse import urlsplit, parse_qs
                    url = urlsplit(started_env["GOTRUE_DB_DATABASE_URL"])
                    self.assertEqual(url.hostname, startup.PG_NAME)
                    self.assertEqual(parse_qs(url.query), {
                        "application_name": ["fmz-registered-auth-"+owner.binding["run_id"].replace("-", "")],
                        "sslmode": ["verify-full"], "sslrootcert": [startup.AUTH_CA]})
                    return types.SimpleNamespace(returncode=0, stdout="lost" if unknown_start else "4"*64)
                elif args[1] == "inspect":
                    if ".State" in args[3]: data = {"Running": False, "Pid": 0}
                    elif args[-1] == startup.PG_NAME: data = pg
                    else:
                        env = {**startup.configuration(),
                            "GOTRUE_DB_DATABASE_URL": started_env["GOTRUE_DB_DATABASE_URL"],
                            "GOTRUE_JWT_SECRET": started_env["GOTRUE_JWT_SECRET"]}
                        if wrong_config: env["GOTRUE_DB_CLEANUP_ENABLED"] = "true"
                        data = {"Id": "4"*64, "Image": image["Id"], "State": {"Running": True},
                            "Config": {"Cmd": ["auth", "serve"], "Image": startup.IMAGE,
                                "Labels": {"fmz.registered.run": owner.binding["run_id"]},
                                "Env": [k+"="+v for k,v in env.items()]},
                            "HostConfig": {"NetworkMode": "local_net"},
                            "Mounts": [{"Type": "bind", "Source": str(ca.resolve()),
                                "Destination": startup.AUTH_CA, "RW": writable_ca}],
                            "NetworkSettings": {"Networks": {"local_net": {"IPAddress": "172.18.0.2"}}}}
                else: return types.SimpleNamespace(returncode=0, stdout="")
                return types.SimpleNamespace(returncode=0, stdout=json.dumps(data))
            def profile_before_start(server):
                self.assertFalse(server.start_attempted)
                self.assertIsNone(server.started_stats)
                self.assertIsNone(server.container_id)
                self.assertIsNone(server.owner.auth)
                self.assertFalse(any(c[1] == "run" for c in commands))
                calls.append(("profile-before-start", "test_boundary"))
                return {"mock_only": True}
            with patch.object(startup.subprocess, "run", run), patch.object(
                    startup.native_runtime, "NativeRuntime", Runtime), patch.object(
                    startup, "health", return_value={"db_worker_terminal": False}), patch.object(
                    auth_protocol, "difference", return_value={"commands": 3}), patch.object(
                    startup.profile, "run", profile_before_start):
                server = startup.LocalServer(owner)
                yield server, calls, commands

    def test_actual_startup_orchestration_serve_only_six_explicit_reads(self):
        with self.local_process() as (server, calls, commands):
            isolation = server.open()
            result = server.close()
        start = next(args for args in commands if args[1] == "run")
        self.assertEqual(start[-2:], ["auth", "serve"])
        self.assertEqual(sum(kind == "native_sql" for _, kind in calls), 6)
        self.assertTrue(isolation["auth_database_bound"])
        self.assertTrue(isolation["auth_ssl"])
        self.assertEqual(isolation["auth_sslmode"], "verify-full")
        self.assertEqual(start[-3], startup.IMAGE)
        self.assertIn("--mount", start)
        self.assertTrue(result["process_stopped"])
        self.assertFalse(result["account_deletion_proven"])
        self.assertEqual(result["managed_sql"], {"commands": 3})
        self.assertIsNone(server.dsn)
        self.assertNotIn("Config", server.pg)

    def test_owned_process_stops_even_after_config_mismatch(self):
        with self.local_process(wrong_config=True) as (server, calls, commands):
            with self.assertRaisesRegex(ValueError, "auth_config_binding"):
                server.open()
            server.close()
        self.assertTrue(any(args[1] == "stop" and args[-1] == "4"*64 for args in commands))

    def test_unknown_start_never_stops_by_unproven_name(self):
        with self.local_process(unknown_start=True) as (server, calls, commands):
            with self.assertRaisesRegex(ValueError, "auth_start_unknown"):
                server.open()
            with self.assertRaisesRegex(ValueError, "unknown_container_retained"):
                server.close()
        self.assertFalse(any(args[1] == "stop" for args in commands))


if __name__ == "__main__":
    unittest.main()

