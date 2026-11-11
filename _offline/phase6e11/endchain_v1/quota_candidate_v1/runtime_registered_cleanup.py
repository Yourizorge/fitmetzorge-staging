"""Exact registered ownership capability; reuse the parent engine.

Pre-seed failures require C's real catalog validator and no seed attempt.
Post-body cleanup instead requires C's exact issued physical-closure Proof.
Unknown creates and caller-produced barrier dictionaries never grant authority.
"""
import copy
import contextlib
import inspect
import pathlib
import sys
import weakref

import admission_journal as durable
import admission_module_binding as binding
import auth_failure as af
import auth_failure_parent_finalizer as parent
import auth_failure_tracked as tracked
import auth_pre_fixture_closure as pre
import fixture_producer_scope as producer

PREFIX = "registered-auth-cleanup"
_ISSUED = weakref.WeakKeyDictionary()


def require(value, reason):
    parent.require(value, "registered_" + reason)


class Prerequisite:
    def __init__(self):
        raise TypeError("actual_registered_context_only")

    def state(self):
        require(type(self) is Prerequisite and self in _ISSUED, "unissued")
        return _ISSUED[self]

    @property
    def roles(self):
        return tuple(self.state().owned)

    @property
    def hashes(self):
        return dict(self.state().hashes)

    @property
    def original_error_class(self):
        primary = self.state().primary
        return type(primary).__name__ if primary is not None else None

    @property
    def kind(self):
        return ("LIVE_REGISTERED_CLOSED_FIXTURE" if self.state().fixture_proof is not None
                else "LIVE_REGISTERED_CREATE_ONLY_BOOTSTRAP")

    @property
    def original_commit_unknown(self):
        proof = self.state().fixture_proof
        return proof.receipt.get("original_commit_unknown", False) if proof is not None else False

    def consume(self, gate, ctx, auth, seal):
        state = self.state()
        require(not state.consumed, "proof_replay")
        state.consumed = True
        require(gate is state.owner.gate and ctx is state.ctx
                and auth is state.owner.auth and seal is state.owner.producer._seal
                and sys.exception() is state.primary, "live_context")
        self.unchanged()
        return self.owners()

    def unchanged(self):
        state = self.state()
        state.owner._validate()
        require(state.owner._closing, "actual_closing_context")
        if state.fixture_proof is None:
            require(not state.owner._seed_attempted and not state.owner._yielded
                    and state.owner._case is None, "pre_seed_only")
        else:
            state.fixture_proof.unchanged()
            require(state.fixture_proof.owner is state.owner, "fixture_owner_changed")
            original = state.fixture_proof.owners()
            require(set(original) == set(state.owned) and all(
                original[r]["actor"] == v["actor"] and original[r]["email"] == v["email"]
                for r, v in state.owned.items()), "fixture_owners_changed")
        state.owner.producer.handoff()
        require(binding.verify(state.owner.gate, state.modules) == state.source, "source_changed")
        if state.fixture_proof is None:
            pre._scope_unchanged({"closure": state, "gate": state.gate,
                "scope": state.catalog, "scope_result": state.catalog_result,
                "scope_contract": state.catalog_contract})
        state.journal._inventory()
        for name, ref in state.journal.entries.items():
            state.journal._read(name, ref)
        for path, digest in state.hashes.items():
            parent.cparent.reference(state.gate.out, {"path": path, "sha256": digest})

    def owners(self):
        self.unchanged()
        return copy.deepcopy(self.state().owned)

    def bind_snapshot(self, role, value):
        state = self.state()
        self.unchanged()
        require(role in state.owned and role not in state.snapshots, "snapshot_replay")
        item = state.owned[role]
        af.validate_snapshot(value)
        require(value["users"] == [{"id": item["actor"], "email": item["email"], "marker": None}],
                "original_create_owner")
        state.journal.save("sessions-" + role + ".json", {
            "actor_sha256": tracked.sha(item["actor"].encode()),
            "session_hashes": [tracked.sha(s.encode()) for s in sorted(value["session_ids"])]})
        state.snapshots.add(role)
        item["session_ids"] = list(value["session_ids"])

    def native(self, key, call):
        self.unchanged()
        return self.state().owner._local_call("engine." + key, "native_sql", call)

    def connect(self, config):
        self.unchanged()
        return self.state().owner._local_call("engine.connect", "connection",
                                             lambda: af.RealBackend(config))

    def close_backend(self, backend):
        return self.state().owner._local_call("engine.close", "connection_close", backend.close)

    def delete(self, role, ledger):
        state = self.state()
        self.unchanged()
        require(state.consumed and role in state.snapshots and role not in state.deleted,
                "delete_replay")
        state.deleted.add(role)
        owner = state.owner
        def dispatch():
            before = owner.auth.registry.next_id
            try:
                return owner.auth.registry.dispatch("parent-cleanup",
                    tracked.existing_prepaid(ledger, role + ":delete"), owner.auth._wire.request,
                    "DELETE", "/admin/users/" + state.owned[role]["actor"],
                    proof=owner.producer._seal)
            finally:
                if owner.auth.registry.next_id != before:
                    owner.producer._cleanup_calls.append(role)
        return owner._local_call("engine." + role + ":delete", "managed_auth", dispatch)


class _State:
    def __init__(self, owner, primary, fixture_proof=None):
        from .runtime_registered_bootstrap import Context
        frame = inspect.currentframe().f_back
        require(frame.f_code is run.__code__ and frame.f_locals.get("owner") is owner,
                "constructor_origin")
        del frame
        require(type(owner) is Context and owner._closing and primary is sys.exception(),
                "actual_context_finalizer")
        self.fixture_proof = fixture_proof
        if fixture_proof is None:
            require(not owner._seed_attempted and not owner._yielded and owner._case is None
                    and isinstance(primary, BaseException), "actual_pre_seed_failure")
        else:
            from . import runtime_registered_fixture_closeout as physical
            require(type(fixture_proof) is physical.Proof and fixture_proof.owner is owner
                    and owner._seed_ref is not None and owner._yielded and owner._case is not None,
                    "actual_registered_fixture_proof")
            fixture_proof.unchanged()
        self.owner, self.gate, self.primary = owner, owner.gate, primary
        self.scope, self.started = None, False
        self._scope_attempted, self._scope_units = False, 0
        self.consumed = False
        self.snapshots, self.deleted = set(), set()
        handoff = owner.producer.handoff()
        self.owned = {owner.role_map[r]: {"actor": v["id"], "email": v["email"],
                       "session_ids": None} for r, v in handoff["owned"].items()}
        if fixture_proof is not None:
            require(fixture_proof.owners() == self.owned, "fixture_exact_original_owners")
        self.ctx = {"auth": owner.auth, "auth_request_registry": owner.auth.registry,
            "dsn": owner.server.dsn, "test_admin_token": owner.server.admin,
            "suspend_admin": owner.server.suspend}
        self.modules = [sys.modules[__name__], parent, af, tracked, pre, producer, binding, durable,
                        sys.modules[producer.NativeRuntime.__module__]]
        if fixture_proof is not None:
            self.modules.append(physical)
        self.source = binding.verify(self.gate, self.modules)
        self.journal = durable.Journal(pathlib.Path(self.gate.out) / (PREFIX + "-private"),
                                       lambda *_: None, PREFIX)
        self.journal.save("intent.json", {"case_run": owner.binding["run_id"],
            "source_binding": self.source, "owner_hashes": {
                r: {"subject": tracked.sha(v["actor"].encode()),
                    "email": tracked.sha(v["email"].encode())} for r, v in self.owned.items()},
            "before_seed": fixture_proof is None,
            "fixture_proof_ref": fixture_proof.ref if fixture_proof is not None else None,
            "original_failure": type(primary).__name__ if primary is not None else None,
            "refunds": False, "full_chain_admission": False})
        self.hashes = {}
        if fixture_proof is not None:
            ref = fixture_proof.ref
            parent.cparent.reference(self.gate.out, ref)
            self.hashes[ref["path"]] = ref["sha256"]

    def attest(self):
        original_save = self.gate.save
        @contextlib.contextmanager
        def scoped_suspension():
            # Observer close/reconnect are siblings of the ten-read macro,
            # never nested precharges while that macro's ticket is pending.
            with self.owner.server.suspend():
                self.owner._validate()
                ledger = self.owner.execution_ledger
                ticket = ledger.precharge("auth.scope")
                item = {"id": "auth.scope", "kind": "scope", "confirmed": False}
                self.owner._calls.append(item)
                try:
                    yield
                except BaseException as primary:
                    try: ledger.unknown(ticket, reason="not_terminal")
                    except BaseException as error:
                        primary.add_note("secondary_scope_ledger:" + type(error).__name__)
                    raise
                else:
                    ledger.confirm(ticket, observed_sql_commands=10)
                    item["confirmed"] = True

        def publish(name, value):
            require(not (pathlib.Path(self.gate.out) / name).exists(), "publication_exists")
            original_save(name, value)
            actual, digest = parent.cparent.read_record(self.gate.out, name)
            require(durable.raw(actual) == durable.raw(value), "publication_readback")
            self.hashes[name] = digest
        self.ctx["suspend_admin"] = scoped_suspension
        self.catalog, self.catalog_result, self.catalog_contract = pre._attest_scope(
            self, self.ctx, self, self.journal, publish)
        for name, ref in self.journal.entries.items():
            self.hashes[(self.journal.folder / name).relative_to(self.gate.out).as_posix()] = ref["sha256"]


def run(owner, primary, *, fixture_proof=None):
    from .runtime_registered_bootstrap import Context
    frame = inspect.currentframe().f_back
    require(frame.f_code is Context._finish.__code__ and frame.f_locals.get("self") is owner,
            "context_finalizer_origin")
    del frame
    state = _State(owner, primary, fixture_proof)
    if fixture_proof is None:
        state.attest()
    proof = object.__new__(Prerequisite)
    _ISSUED[proof] = state
    owner._auth_cleanup_proof = proof
    return parent.finalize(owner.gate, state.ctx, owner.auth, owner.producer._seal, None,
        delete_costs=dict.fromkeys(proof.roles, 128), registered_bootstrap_proof=proof)

