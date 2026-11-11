"""Actual loopback HTTP; synthetic server, no GoTrue, Docker or PostgreSQL."""
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import threading
import types
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

DELIVERY = pathlib.Path(__file__).parent
SOURCE = pathlib.Path(os.environ.get("AUTH_CONTEXT_SOURCE_ROOT", str(DELIVERY.parents[2]))).resolve()
ISOLATED = DELIVERY.name == "agent-b-tracked-context-20261103"
SOURCE_CORE = SOURCE / "_offline/phase6e11/endchain_v1"
if not ISOLATED and DELIVERY.resolve() != SOURCE_CORE.resolve():
    raise RuntimeError("registered_test_exact_source_root_required")
SNAPSHOT = tempfile.TemporaryDirectory()
ROOT = pathlib.Path(SNAPSHOT.name)
CORE = ROOT / "_offline/phase6e11/endchain_v1"
PACKAGE = CORE / "quota_candidate_v1"
PACKAGE.mkdir(parents=True)
for path in SOURCE_CORE.glob("*.py"):
    shutil.copyfile(path, CORE / path.name)
for path in (DELIVERY / "quota_candidate_v1").glob("*.py"):
    shutil.copyfile(path, PACKAGE / path.name)
if ISOLATED:
    # Explicit sibling deliveries only; canonical CI uses its own bundled files.
    fixture_source = DELIVERY.parent / "agent-c-registered-fixture-closeout-20261103/quota_candidate_v1/runtime_registered_fixture_closeout.py"
    shutil.copyfile(fixture_source, PACKAGE / fixture_source.name)
    profile_source = DELIVERY.parent / "agent-c-auth-runtime-profile-20261103/admission_auth_runtime_profile.py"
    shutil.copyfile(profile_source, CORE / profile_source.name)
    for path in (DELIVERY / "_offline/phase6e11/endchain_v1").glob("*.py"):
        shutil.copyfile(path, CORE / path.name)
    root_ledger_source = DELIVERY.parent / "agent-a-root-budget-20261103/admission_budget_root_runtime.py"
    shutil.copyfile(root_ledger_source, CORE / root_ledger_source.name)
(ROOT / "supabase/migrations").mkdir(parents=True)
for path in (SOURCE / "supabase/migrations").glob("*.sql"):
    shutil.copyfile(path, ROOT / "supabase/migrations" / path.name)
if ISOLATED:
    sys.path.insert(0, str(CORE))
from quota_candidate_v1 import runtime_registered_bootstrap as proposed
import auth_failure_tracked as tracked
import auth_failure_transport as transport


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = pathlib.Path(self.temp.name)
        self.gate = types.SimpleNamespace(sources=ROOT, out=self.out)
        self.manifest = {"sources": {p.relative_to(ROOT).as_posix(): tracked.sha(p.read_bytes())
                                     for p in ROOT.rglob("*.py")}}
        (self.out / "candidate.json").write_text(json.dumps(self.manifest))
        env = patch.dict(os.environ, {"GITHUB_WORKSPACE": str(ROOT)})
        env.start(); self.addCleanup(env.stop)
        self.run_id = str(uuid.uuid4())
        self.requests, self.users = [], {}
        self.fail_request = None
        self.response_kind = "normal"
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                length = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(length))
                outer.requests.append((self.path, body))
                if outer.fail_request == len(outer.requests) and outer.response_kind == "denied":
                    raw, status = b"{}", 401
                else:
                    actor = str(uuid.uuid4())
                    user = {"id": actor, "email": body["email"]}
                    outer.users[actor] = user
                    raw, status = json.dumps(user).encode(), 200
                    if outer.fail_request == len(outer.requests) and outer.response_kind == "wrong_email":
                        raw = json.dumps({**user, "email": "foreign@example.invalid"}).encode()
                    if outer.fail_request == len(outer.requests) and outer.response_kind == "truncated":
                        self.send_response(200)
                        self.send_header("Content-Length", str(len(raw) + 100))
                        self.end_headers()
                        self.wfile.write(raw)
                        self.close_connection = True
                        return
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_DELETE(self):
                outer.requests.append((self.path, None))
                actor = self.path.rsplit("/", 1)[-1]
                outer.users.pop(actor, None)
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.origin = "http://127.0.0.1:" + str(self.server.server_port)
        for obj, name, value in ((proposed, "ORIGIN", self.origin),
                                 (transport, "ORIGINS", (self.origin,))):
            p = patch.object(obj, name, value)
            p.start(); self.addCleanup(p.stop)
        self.registry = tracked.Registry(self.out / "registry", run_id=self.run_id)
        self.budget = tracked.ParentBudget(self.out / "budget", [
            {"method": "POST", "route": "/admin/users", "units": 128} for _ in range(3)],
            run_id=self.run_id)
        self.auth = tracked.Factory(self.registry, self.budget)(
            self.origin, object, "PRIVATE_TEST_ADMIN", ValueError)

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(5)
        self.server.server_close()

    def producer(self):
        return proposed.BootstrapRequests(proposed._TOKEN, self.gate, self.auth, self.run_id)

    def test_exact_three_creates_no_password_login_verify_or_tokens(self):
        producer = self.producer()
        ids = producer.create_all()
        self.assertEqual(set(ids), set(proposed.ROLES))
        self.assertEqual([path for path, _ in self.requests], ["/admin/users"] * 3)
        self.assertEqual([data for _, data in self.requests],
            [{"email": proposed.native_runtime.ALIASES[r], "email_confirm": True} for r in proposed.ROLES])
        self.assertEqual(self.budget.spent, 384)
        self.assertEqual(set(self.auth._owners), {"a", "trainer", "b"})
        seal = producer.close()
        self.assertTrue(self.registry.valid_proof(seal))
        handoff = producer.handoff()
        self.assertIs(handoff["seal"], seal)
        self.assertFalse(handoff["deletion_admitted"])
        self.assertEqual(len(handoff["owned"]), 3)
        receipt = producer.receipt()
        raw = json.dumps(receipt)
        self.assertNotIn("PRIVATE_TEST_ADMIN", raw)
        for uid in ids.values(): self.assertNotIn(uid, raw)
        for email in proposed.native_runtime.ALIASES.values(): self.assertNotIn(email, raw)
        self.assertTrue(receipt["no_login_by_this_producer"])
        self.assertFalse(receipt["database_session_zero_observed"])

    def test_owner_journal_precedes_next_request(self):
        producer = self.producer()
        original = self.auth._wire.request
        observed = []
        def wire(*args, **kw):
            observed.append(len([v for v in producer.records.export().values()
                                 if v["content"]["kind"] == "owned"]))
            return original(*args, **kw)
        with patch.object(self.auth._wire, "request", side_effect=wire):
            producer.create_all()
        self.assertEqual(observed, [0, 1, 2])

    def prefix(self, count):
        producer = self.producer()
        primary = RuntimeError("original stop")
        original = self.budget.reserve
        def reserve(*args):
            if self.budget.index == count: raise primary
            return original(*args)
        with patch.object(self.budget, "reserve", side_effect=reserve):
            with self.assertRaises(RuntimeError) as error: producer.create_all()
        self.assertIs(error.exception, primary)
        producer.close()
        self.assertEqual(len(producer.handoff()["owned"]), count)
        self.assertEqual(len(self.requests), count)
        self.assertEqual(self.budget.spent, count * 128)
        self.assertFalse(producer.receipt()["pending_create_unknown"])
        return producer

    def test_zero_owner_before_create(self): self.prefix(0)
    def test_one_owner_before_second_create(self): self.prefix(1)
    def test_two_owners_before_third_create(self): self.prefix(2)

    def test_unknown_create_retains_claim_and_denies_handoff(self):
        producer = self.producer()
        self.fail_request, self.response_kind = 2, "truncated"
        with self.assertRaises(transport.UnknownOutcome): producer.create_all()
        with self.assertRaises(tracked.Blocked): producer.close()
        with self.assertRaises(tracked.Blocked): producer.handoff()
        self.assertEqual(len(self.users), 2)
        self.assertEqual(len(self.auth._owners), 1)
        self.assertEqual(self.budget.spent, 256)
        self.assertEqual(self.registry.phase, "FAILED")
        self.assertIsNone(self.registry.proof)

    def test_terminal_bad_email_is_not_adopted(self):
        producer = self.producer()
        self.fail_request, self.response_kind = 2, "wrong_email"
        with self.assertRaises(tracked.Blocked): producer.create_all()
        with self.assertRaisesRegex(tracked.Blocked, "unknown_create_owner"): producer.close()
        self.assertEqual(len(self.auth._owners), 1)
        self.assertEqual(self.budget.spent, 256)
        with self.assertRaises(tracked.Blocked): producer.handoff()

    def test_terminal_error_is_not_an_owned_subject(self):
        producer = self.producer()
        self.fail_request, self.response_kind = 1, "denied"
        with self.assertRaisesRegex(tracked.Blocked, "create_http"): producer.create_all()
        with self.assertRaisesRegex(tracked.Blocked, "unknown_create_owner"): producer.close()
        self.assertEqual(self.users, {})
        self.assertEqual(self.budget.spent, 128)

    def test_create_replay_and_future_mint_denied(self):
        producer = self.producer()
        producer.create_all()
        with self.assertRaisesRegex(tracked.Blocked, "create_replay"): producer.create_all()
        producer.close()
        with self.assertRaisesRegex(tracked.Blocked, "future_request"):
            self.auth.call("/token?grant_type=password", data={"email": "unused", "password": "unused"})
        self.assertEqual(len(self.requests), 3)

    def test_close_replay(self):
        producer = self.prefix(0)
        with self.assertRaisesRegex(tracked.Blocked, "close_replay"): producer.close()

    def test_untracked_request_blocks_handoff(self):
        producer = self.producer()
        self.registry.next_id += 1
        with self.assertRaisesRegex(tracked.Blocked, "unowned_request"): producer.create_all()
        self.assertEqual(self.requests, [])

    def test_unknown_create_receipt_does_not_promote_cleanup(self):
        producer = self.producer()
        self.fail_request, self.response_kind = 1, "truncated"
        with self.assertRaises(transport.UnknownOutcome): producer.create_all()
        receipt = producer.receipt()
        self.assertTrue(receipt["pending_create_unknown"])
        self.assertFalse(receipt["deletion_proven"])
        self.assertFalse(receipt["original_claims_released"])

    def test_mutated_record_before_close(self):
        producer = self.producer()
        producer.create_all()
        path = next(producer.records.folder.glob("*owned.json"))
        path.write_bytes(b"{}")
        with self.assertRaises(tracked.Blocked): producer.close()
        self.assertIsNone(self.registry.proof)

    def test_mutated_record_after_close_before_export(self):
        producer = self.producer()
        producer.create_all()
        producer.close()
        path = next(producer.records.folder.glob("*owned.json"))
        path.write_bytes(b"{}")
        with self.assertRaises(tracked.Blocked): producer.receipt()
        with self.assertRaises(tracked.Blocked): producer.handoff()

    def test_mutated_in_memory_owner_denied(self):
        producer = self.producer()
        producer.create_all()
        producer._owned["a_member"]["id"] = str(uuid.uuid4())
        with self.assertRaises(tracked.Blocked): producer.close()

    def test_source_changed_before_first_request(self):
        producer = self.producer()
        manifest = self.out / "candidate.json"
        manifest.write_text(manifest.read_text() + " ")
        with self.assertRaisesRegex(tracked.Blocked, "source_changed"): producer.create_all()
        self.assertEqual(self.requests, [])

    def test_non_create_plan_rejected_before_dispatch(self):
        self.budget.plan[1]["route"] = "/token?grant_type=password"
        with self.assertRaisesRegex(tracked.Blocked, "create_only_plan"): self.producer()
        self.assertEqual(self.requests, [])

    def test_wrong_origin_rejected(self):
        self.auth.url = "https://example.invalid"
        with self.assertRaisesRegex(tracked.Blocked, "loopback"): self.producer()

    def test_old_run_rejected(self):
        with self.assertRaises(ValueError):
            proposed.BootstrapRequests(proposed._TOKEN, self.gate, self.auth, proposed.af.OLD_RUN)

    def test_new_root_interface_fails_before_dispatch_even_with_forged_ledger(self):
        ledger = types.SimpleNamespace(complete=True, admitted=True, reserve=lambda *_: True)
        ctx = proposed.context(self.gate, binding={"run_id": self.run_id},
                               stack={"status": "CLEAN47_BOOTSTRAP_PASS"}, ledger=ledger)
        with self.assertRaisesRegex(tracked.Blocked, "root_register_and_closure"):
            with ctx:
                self.fail("missing prerequisites yielded")
        self.assertEqual(self.requests, [])
        self.assertEqual(ctx.closeout["dispatches"], 0)
        self.assertIsNone(ctx.runtime)
        self.assertIsNone(ctx.isolation)
        self.assertFalse(ctx.closeout["deletion_proven"])

    def test_original_context_body_exception_not_suppressed(self):
        ctx = proposed.context(self.gate, binding={}, stack={}, ledger=None)
        primary = RuntimeError("body")
        self.assertFalse(ctx.__exit__(RuntimeError, primary, None))

    def test_conditional_costs_never_claim_full_bound(self):
        for attempts in range(4):
            for owners in range(attempts + 1):
                value = proposed.conditional_costs(attempts, owners)
                self.assertEqual(value["create_plus_reference_suffix"], 128 * attempts + 13 + 133 * owners)
                self.assertTrue(value["reference_suffix_join_implemented"])
                self.assertTrue(value["preseed_engine_join_implemented"])
                self.assertTrue(value["postbody_engine_join_implemented"])
                self.assertIsNone(value["overall_bound"])
                self.assertFalse(value["managed_bound_observed"])
        for args in ((True, 0), (1, True), (1, 2), (4, 3), (-1, 0)):
            with self.assertRaises(tracked.Blocked): proposed.conditional_costs(*args)

    def test_unknown_startup_health_cost_is_null_not_zero(self):
        register = proposed.command_register()
        rows = {r["id"]: r for r in register["ordered_stages"]}
        for key in ("auth_start", "auth_health", "auth_stop"):
            self.assertIsNone(rows[key]["sql_bound"])
        self.assertFalse(register["all_costs_known"])
        self.assertIsNone(register["root_total"])


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        SNAPSHOT.cleanup()

