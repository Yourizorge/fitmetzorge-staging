"""Positive B consumer boundary, not actual runtime admission.

Real localhost create/delete, tracked ownership, parent engine, C profile
protocol/packaging and A terminal validation execute. PostgreSQL/Docker remain
mocked. A's compiler is replaced ONLY while opening a zero-SQL unit program;
that fixture does not prove the complete Context budget or a real profile run.
Context admission/accounting are explicit test boundaries. The B consumer,
issued cleanup proof, immutable receipts and A terminal validator are not bypassed.
"""
import copy
import pathlib
import types
import unittest
from unittest.mock import patch

import test_runtime_registered_context_join as join
import admission_auth_runtime_profile as profile
import admission_budget_root_runtime as root

b = join.b


class ProfileProtocol:
    """SQL boundary model; execute C's real protocol and record packaging."""
    def __init__(self):
        self.phase = None
        self.executed = []
        self.connections = []
        self.runtime = types.SimpleNamespace(connect=self.connect)
        self.isolation = {"pg_system_identifier": "123", "database_oid": 5}

    def _local_call(self, name, kind, action):
        self.phase = name.removeprefix("profile.")
        return action()

    def connect(self):
        owner = self
        class Connection:
            autocommit = True
            closed = False
            def close(self): self.closed = True
            def execute(self, sql, args=()):
                phase = owner.phase
                owner.executed.append((phase, sql))
                rows = []
                if phase.endswith("_metadata"):
                    before, witness = phase == "before_metadata", phase == "witness_metadata"
                    role = dict(name="supabase_auth_admin", oid=42, superuser=False, inherit=True,
                        createrole=before, createdb=False, login=True, replication=False,
                        bypassrls=False, connlimit=-1, validuntil=None, config=None)
                    rows = [{"value": dict(cluster_id="123", datid=5, pid=11 if witness else 10,
                        postmaster_start="test-start", pg17=True, ssl=True, bounded=True,
                        postgres=True, origin=True, readonly=witness, no_prepared=True,
                        tracked=True, external=False, roles=[role], memberships=[])}]
                elif phase.endswith("_privileges"):
                    rows = [{"role": role, **{flag: phase == "before_privileges"
                        and role == "supabase_auth_admin" and flag == "createrole"
                        for flag in profile.scope.PRIVILEGE_FLAGS}}
                        for role in ("supabase_auth_admin", "anon", "authenticated", "service_role")]
                return types.SimpleNamespace(description=True, fetchall=lambda: copy.deepcopy(rows))
        connection = Connection()
        self.connections.append(connection)
        return connection


class TerminalConsumerTests(unittest.TestCase):
    def setUp(self):
        self.h = join.JoinTests(methodName="runTest")
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        self.h.binding["candidate_sha"] = "c" * 64
        self.h.ctx.binding = copy.deepcopy(self.h.binding)
        self.h.gate.result = {"candidate_sha256": "c" * 64,
            "commit": self.h.binding["source_commit"], "run_id": self.h.binding["ci_run"]}
        self.protocol = ProfileProtocol()
        fixture = self
        server_type = join.startup.LocalServer  # Existing OS boundary double.
        original_open, original_close = server_type.open, server_type.close

        def open_server(server):
            value = original_open(server)
            server.profile_receipt = fixture.pack_profile()
            return value

        def close_server(server):
            value = original_close(server)
            server.closed = True
            return value

        def close_root(context, process):
            # Explicit consumer boundary fixture, not a reconstructed full
            # Context budget. The real public opener writes original evidence.
            children = [{"command_id": "unit.consumer.no_sql", "units": 0,
                "reserve_after": 0, "domain": "test_only", "hosted_units": 0,
                "hosted_reserve_after": 0}]
            program = [{"command_id": "case.auth.context", "units": 0,
                "reserve_after": 0, "domain": "test_only", "hosted_units": 0,
                "hosted_reserve_after": 0, "children": children}]
            names = [pathlib.Path(module.__file__).relative_to(join.base.ROOT).as_posix()
                     for module in (b, root, profile)]
            register = dict(bound_complete=True, prefix_reserves_complete=True,
                source_inventory_complete=True, hosted_scope_complete=True, missing_costs=[],
                total_local_ci_upper_bound=0, total_hosted_equivalent_upper_bound=0,
                hosted_limit=2349, executable_program=program, test_only=True,
                source_hashes={name: join.tracked.sha((join.base.ROOT / name).read_bytes()) for name in names})
            register["full_register_sha256"] = root.digest(register)
            with patch.object(root, "build_root_register", return_value=register):
                parent = root.open_execution_ledger(context.gate, dag=register,
                    model={key: register[key] for key in root.MODEL_FIELDS}, binding=context.binding)
            envelope, child = parent.open_envelope("case.auth.context")
            child.confirm(child.precharge("unit.consumer.no_sql"), observed_sql_commands=0)
            child.close()
            parent.close_envelope(envelope, child, observed_sql_commands=0)
            context.ledger, context.execution_ledger, context._envelope = parent, child, envelope
            context.closeout["root_accounting"] = child.receipt()
            context.closeout["numeric_lifetime_complete"] = True

        for target, name, value in ((server_type, "open", open_server),
                (server_type, "close", close_server), (b.Context, "_settle_root", close_root)):
            p = patch.object(target, name, value)
            p.start(); self.addCleanup(p.stop)
        self.report = self.h.run_prefix(1)
        self.assertTrue(self.report["deletion_proven"], self.report)
        self.assertEqual(self.report["secondary_errors"], [])
        self.assertEqual(self.h.users, {})

    def pack_profile(self):
        folder = self.h.out / (profile.PREFIX + "-private")
        journal = profile.durable.Journal(folder, self.h.publish, profile.PREFIX + "-journal")
        journal.save("binding.json", {"test_only": True, "case_run": self.h.run_id,
                                      "actual_database_executed": False})
        def unchanged():
            journal._inventory()
            for name, ref in journal.entries.items(): journal._read(name, ref)
        result, error = profile._execute(self.protocol, journal, unchanged)
        self.assertIsNone(error)
        self.assertEqual(result["emitted_attempts"], 10)
        self.assertTrue(all(c.closed for c in self.protocol.connections))
        journal.save("result.json", result)
        index = journal.seal()
        return {"receipt": result,
            "ref": {"path": (folder / "result.json").relative_to(self.h.out).as_posix(),
                    "sha256": journal.entries["result.json"]["sha256"]},
            "evidence_refs": profile.evidence_refs(journal, index, self.h.out)}

    def consume(self):
        return b.validate_closeout(self.h.ctx, gate=self.h.gate, binding=self.h.binding)

    def assert_exact_call(self, spy):
        spy.assert_called_once()
        child, gate, binding = spy.call_args.args
        self.assertIs(child, self.h.ctx.execution_ledger)
        self.assertIs(gate, self.h.gate)
        self.assertIs(binding, self.h.binding)

    def test_positive_profile_packaging_and_actual_root_terminal_are_consumed(self):
        with patch.object(root, "validate_terminal", wraps=root.validate_terminal) as spy:
            result = self.consume()
        self.assert_exact_call(spy)
        self.assertEqual(result["status"], "SCOPED_REGISTERED_CONTEXT_CLOSED")
        self.assertEqual(self.h.ctx.execution_ledger._program_path, ("case.auth.context",))
        self.assertEqual(result["original_error_class"], "RuntimeError")
        self.assertFalse(result["original_claims_released"])
        self.assertFalse(result["full_chain_admission"])
        refs = {ref["path"]: ref for ref in result["evidence_refs"]}
        expected = self.h.ctx.server.profile_receipt["evidence_refs"]
        self.assertTrue(any(r["path"].endswith("-index.json") for r in expected))
        self.assertTrue(any(r["path"].endswith("-001.json") for r in expected))
        for ref in expected: self.assertEqual(refs[ref["path"]], ref)
        self.assertEqual(result["evidence_record_count"], len(refs))
        self.assertEqual(result["evidence_bytes"], sum(r["bytes"] for r in refs.values()))

    def assert_profile_tamper_rejected(self, suffix):
        ref = next(r for r in self.h.ctx.server.profile_receipt["evidence_refs"]
                   if r["path"].endswith(suffix))
        path = self.h.out / ref["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with patch.object(root, "validate_terminal", wraps=root.validate_terminal) as spy:
            with self.assertRaises(join.parent.cparent.Blocked): self.consume()
        spy.assert_not_called()
        self.assertEqual(ref["sha256"], next(r["sha256"] for r in
            self.report["runtime_profile"]["evidence_refs"] if r["path"] == ref["path"]))

    def test_profile_private_original_tamper_blocks_before_root_terminal(self):
        self.assert_profile_tamper_rejected("/witness.json")

    def test_profile_packaged_chunk_tamper_blocks_before_root_terminal(self):
        self.assert_profile_tamper_rejected("-001.json")

    def test_root_terminal_rejection_propagates_exact_primary(self):
        error = root.RootBlocked("test_root_terminal_denial")
        with patch.object(root, "validate_terminal", side_effect=error) as spy:
            with self.assertRaises(root.RootBlocked) as caught: self.consume()
        self.assertIs(caught.exception, error)
        self.assert_exact_call(spy)
        self.assertFalse(self.h.ctx.closeout["original_claims_released"])

    def test_actual_root_rejects_modified_original_program_payload(self):
        ref = next(r for r in self.h.ctx.execution_ledger._evidence_refs
                   if r["path"] == "root-original-00.txt")
        path = self.h.out / ref["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with patch.object(root, "validate_terminal", wraps=root.validate_terminal) as spy:
            with self.assertRaisesRegex(root.RootBlocked, "root_evidence_(size|modified)"):
                self.consume()
        self.assert_exact_call(spy)


if __name__ == "__main__":
    unittest.main()
