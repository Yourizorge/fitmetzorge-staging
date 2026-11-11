"""Isolated create-only context; concrete dispatch and owned pre-seed cleanup.

Fixed D API: context(gate, *, binding, stack, ledger). No factory callback.
Only a source-compiled admitted root ledger may dispatch. Current incomplete
root bounds deny entry before Docker, SQL or Auth. Startup/driver uncertainties
and actual post-body C/HTTP evidence are not resolved by component tests.
"""
import copy
import inspect
import json
import pathlib
import sys
import uuid

import admission_module_binding as source_binding
import auth_failure as af
import auth_failure_tracked as tracked
import auth_failure_transport as transport
import native_runtime

PREFIX = "registered-auth-bootstrap"
ROLES = ("a_member", "a_trainer", "b_member")
OWNER_ROLES = dict(zip(ROLES, ("a", "trainer", "b")))
ORIGIN = "http://127.0.0.1:59999"
CREATE_UNITS = 128
DELETE_UNITS = 128
_TOKEN = object()


def require(value, code):
    if not value:
        raise tracked.Blocked("registered_bootstrap_" + code)


def conditional_costs(attempts, owners):
    """Declared local units, not a measured managed-SQL bound or root total."""
    require(type(attempts) is int and type(owners) is int
            and 0 <= owners <= attempts <= 3, "prefix_counts")
    return {
        "create_attempts": attempts, "known_owners": owners,
        "create_declared_units": CREATE_UNITS * attempts,
        "existing_engine_suffix_reference": 13 + 133 * owners,
        "create_plus_reference_suffix": CREATE_UNITS * attempts + 13 + 133 * owners,
        "reference_suffix_join_implemented": True,
        "preseed_engine_join_implemented": True,
        "postbody_engine_join_implemented": True,
        "cleanup_condition": "complete_create_ownership_and_actual_terminal_seal_and_C_scope_PASS",
        "unknown_create_cleanup_admitted": False,
        "managed_bound_observed": False, "overall_bound": None,
        "claim_refund": 0, "hosted_fits": False}


def command_register():
    """Stage inventory; startup.source_program supplies explicit protocol counts.

    Null is deliberately not zero. Implemented dispatcher code does not itself
    establish managed/driver bounds or observed post-body C cleanup evidence.
    """
    return {
        "format": "registered-auth-bootstrap-cost-input-v1",
        "ordered_stages": [
            {"id": "source_preflight", "kind": "filesystem", "maximum_calls": 1, "sql_bound": 0},
            {"id": "native_discovery", "kind": "docker_private", "maximum_calls": None, "sql_bound": None},
            {"id": "auth_discovery", "kind": "docker_private", "maximum_calls": None, "sql_bound": None},
            {"id": "auth_image", "kind": "docker", "maximum_calls": None, "sql_bound": None},
            {"id": "auth_start", "kind": "docker_managed_startup", "maximum_calls": None, "sql_bound": None},
            {"id": "auth_health", "kind": "http_health", "maximum_calls": None, "sql_bound": None},
            {"id": "target_attestation", "kind": "native_sql", "maximum_calls": None, "sql_bound": None},
            {"id": "create_only", "kind": "managed_auth", "maximum_calls": 3,
             "declared_units_each": CREATE_UNITS, "sql_bound": None},
            {"id": "profile_seed", "kind": "native_sql", "maximum_calls": None, "sql_bound": None},
            {"id": "worker_body", "kind": "child_DAG", "maximum_calls": 1, "sql_bound": None},
            {"id": "C_registry_closure", "kind": "child_DAG", "maximum_calls": 1, "sql_bound": None},
            {"id": "parent_Auth_closure", "kind": "child_DAG", "maximum_calls": 1, "sql_bound": None},
            {"id": "auth_stop", "kind": "docker_managed_teardown", "maximum_calls": 1, "sql_bound": None}],
        "prototype_only_stages": [],
        "implemented_stages": ["source_preflight", "native_discovery", "auth_image", "auth_start",
            "auth_health", "target_attestation", "create_only", "profile_seed", "worker_body_binding",
            "preseed_parent_Auth_closure", "C_registry_closure", "postbody_parent_Auth_closure",
            "auth_stop", "root_lifetime_union"],
        "root_admission_API_available": True, "runtime_admitted": False, "all_costs_known": False,
        "root_total": None, "hosted_fits": False, "refunds": False}


def _modules():
    return [sys.modules[__name__], source_binding, tracked, transport, af, native_runtime]


def _source(gate):
    return source_binding.verify(gate, _modules())


class BootstrapRequests:
    """One create-only producer, exact registered aliases, durable original hashes.

    Internal handoff helper, not a public permission to create accounts.
    No raw owner records or credentials are exported. The caller must provide
    the exact freshly constructed TrackedAuth from the source-bound Context.
    This class does not accept arbitrary transport/finalizer callbacks.
    """
    def __init__(self, key, gate, auth, run_id):
        require(key is _TOKEN, "context_origin_required")
        require(type(auth) is tracked.TrackedAuth and type(auth.registry) is tracked.Registry,
                "actual_tracker_required")
        require(auth.url == ORIGIN and auth._wire.origin == ORIGIN, "loopback")
        af.binding(run_id)
        require(auth.registry.run_id == run_id and auth.budget.run_id == run_id,
                "run_binding")
        require(auth.registry.phase == "OPEN" and not auth.registry.requests
                and not auth.registry.workers and not auth._created and not auth._owners,
                "fresh_exclusive_registry")
        expected = [{"method": "POST", "route": "/admin/users", "units": CREATE_UNITS}
                    for _ in ROLES]
        require(auth.budget.plan == expected and auth.budget.index == 0, "create_only_plan")
        require(tuple(native_runtime.ALIASES) == ROLES, "registered_alias_contract")
        self.gate, self.auth, self.run_id = gate, auth, run_id
        self.source = _source(gate)
        self.records = tracked.Records(pathlib.Path(gate.out) / (PREFIX + "-private"))
        self.records.save("intent", {"run_id": run_id, "source_binding": self.source,
            "roles": list(ROLES), "alias_hashes": {
                r: tracked.sha(native_runtime.ALIASES[r].encode()) for r in ROLES},
            "maximum_create_declared_units": 3 * CREATE_UNITS,
            "managed_bound_observed": False, "login_requests": 0,
            "session_or_token_claims_manufactured": False, "refunds": False})
        auth.registry._recordsets.append(self.records)
        self._owned, self._calls = {}, []
        self._pending = None
        self._begun = self._finished = self._closed = False
        self._seal = None
        self._owner_snapshot = {}
        self._alias_snapshot = dict(native_runtime.ALIASES)
        self._cleanup_calls = []
        self._context = None

    def __repr__(self):
        return "<BootstrapRequests private owners redacted>"

    def _check(self):
        require(_source(self.gate) == self.source, "source_changed")
        require(native_runtime.ALIASES == self._alias_snapshot, "aliases_changed")
        self.auth.registry._validate_records()
        require(not self.auth.registry.workers, "unowned_worker")
        require(self.auth.registry.next_id == len(self._calls) + len(self._cleanup_calls), "unowned_request")
        require(self.auth._created == {v["id"]: tracked.sha(v["email"].encode())
                                      for v in self._owned.values()}, "created_changed")
        require(self.auth._owners == {OWNER_ROLES[r]: v["id"] for r, v in self._owned.items()},
                "owners_changed")
        require(self._owner_snapshot == self._owned, "original_owner_changed")
        all_admitted = [v["content"] for v in self.auth.registry.records.export().values()
                        if v["content"]["kind"] == "admitted"]
        admitted = [v for v in all_admitted if v["cleanup_only"] is False]
        cleanup = [v for v in all_admitted if v["cleanup_only"] is True]
        require(len(cleanup) == len(self._cleanup_calls)
                and len(set(self._cleanup_calls)) == len(self._cleanup_calls)
                and all(r in self.auth._owners for r in self._cleanup_calls)
                and all(v["method"] == "DELETE" and v["route"] == "/admin/users/{subject}"
                    and v["owner_sha256"] == tracked.sha(b"parent-cleanup") for v in cleanup),
                "cleanup_inventory")
        require(len(admitted) == len(self._calls), "request_record_count")
        for record in admitted:
            require(record["method"] == "POST" and record["route"] == "/admin/users"
                    and record["owner_sha256"] == tracked.sha(PREFIX.encode())
                    and record["cleanup_only"] is False, "untracked_route")
        owner_records = [v["content"] for v in self.auth.registry.records.export().values()
                         if v["content"]["kind"] == "parent_owner"]
        require(len(owner_records) == len(self._owned), "owner_record_count")
        for role, value in self._owned.items():
            require(sum(r.get("role") == OWNER_ROLES[role]
                and r.get("subject_sha256") == tracked.sha(value["id"].encode())
                and r.get("email_sha256") == tracked.sha(value["email"].encode())
                for r in owner_records) == 1, "original_owner_record")

    def _create_owned(self, role):
        email = self._alias_snapshot[role]
        self.records.save("create_intent", {
            "role": role, "email_sha256": tracked.sha(email.encode())})
        before = self.auth.registry.next_id
        self._pending = role
        try:
            response = self.auth.registry.dispatch(PREFIX, self.auth.budget.reserve,
                self.auth._wire.request, "POST", "/admin/users",
                {"email": email, "email_confirm": True})
        except BaseException:
            if self.auth.registry.next_id == before:
                self._pending = None
            raise
        finally:
            if self.auth.registry.next_id != before:
                self._calls.append(role)
        require(response["terminal"] is True and 200 <= response["status"] < 300,
                "create_http_not_confirmed")
        user = response["body"]
        actor = user.get("id") if type(user) is dict else None
        require(isinstance(actor, str) and str(uuid.UUID(actor)) == actor
                and actor not in (af.OLD_RUN, self.run_id)
                and actor not in self.auth._created and user.get("email") == email,
                "create_subject_or_alias")
        self.auth._created[actor] = tracked.sha(email.encode())
        self.auth.bind_owner(OWNER_ROLES[role], actor)
        self.records.save("owned", {"role": role, "subject_sha256": tracked.sha(actor.encode()),
            "email_sha256": tracked.sha(email.encode()), "terminal_create_confirmed": True})
        value = {"id": actor, "email": email}
        self._owned[role] = value
        self._owner_snapshot[role] = dict(value)
        self._pending = None
        self._check()
        if role == ROLES[-1]:
            self.records.save("complete", {"known_owners": 3, "create_requests": 3,
                "login_requests": 0, "tokens_issued_by_this_producer": 0,
                "database_session_zero_observed": False})

    def create_all(self):
        require(not self._begun and not self._closed, "create_replay")
        self._begun = True
        for role in ROLES:
            self._check()
            if self._context is None:
                self._create_owned(role)
            else:
                # The ticket covers validation and original ownership journaling,
                # not just receipt of the HTTP body.
                self._context._local_call("create." + role, "managed_auth",
                    lambda role=role: self._create_owned(role))
        self._finished = True
        return {r: v["id"] for r, v in self._owned.items()}

    def close(self):
        require(not self._closed, "close_replay")
        self._closed = True
        # Freeze future minting even when ownership/source verification fails.
        self._seal = self.auth.close_and_drain()
        self._check()
        require(self._pending is None, "unknown_create_owner")
        require(self.auth.registry.valid_proof(self._seal), "actual_terminal_required")
        return self._seal

    def handoff(self):
        """Private exact subset + live seal, not permission for engine deletion."""
        self._check()
        require(self._closed and self._pending is None
                and self.auth.registry.valid_proof(self._seal), "handoff_requires_actual_close")
        return {"auth": self.auth, "seal": self._seal, "run_id": self.run_id,
                "owned": copy.deepcopy(self._owned),
                "source_binding": copy.deepcopy(self.source),
                "journal_hashes": dict(self.records._hashes),
                "deletion_admitted": False}

    def receipt(self):
        self._check()
        return {"status": "NO_GO", "phase": self.auth.registry.phase,
            "known_owners": len(self._owned), "pending_create_unknown": self._pending is not None,
            "costs": conditional_costs(len(self._calls), len(self._owned)),
            "ownership_journal": self.records.export(), "tracked": self.auth.evidence(),
            "no_login_by_this_producer": True, "database_session_zero_observed": False,
            "deletion_proven": False, "original_claims_released": False,
            "global_zero_claim": False, "full_chain_admission": False}


class Context:
    """One-shot D context. Only A's source-admitted root ledger may start it."""
    role_map = OWNER_ROLES

    def __init__(self, gate, *, binding, stack, ledger):
        self.gate, self.binding, self.stack, self.ledger = gate, copy.deepcopy(binding), copy.deepcopy(stack), ledger
        self.runtime = self.ids = self.config = self.admission_connection = None
        self.ca_path = self.isolation = self.execution_ledger = None
        self.server = self.auth = self.producer = self.records = None
        self.closeout = None
        self.closeout_ref = None
        self._entered = self._entering = self._admitted = self._closing = False
        self._yielded = self._seed_attempted = self._finished = False
        self._cleanup_selected = False
        self._case = self._envelope = None
        self._case_owners = self._seed_ref = None
        self._fixture_registration = self._fixture_proof = None
        self._auth_cleanup_proof = None
        self._diagnostic_mode = False
        self._diagnostic_registry = self._diagnostic_seal = None
        self._diagnostic_report = None
        self._diagnostic_witness = None
        self._deferred = []
        self._calls = []

    def __repr__(self):
        return "<RegisteredBootstrapContext private configuration redacted>"

    def _validate(self):
        require(_source(self.gate) == self._source_snapshot, "source_changed")
        if self.records is not None:
            self.records.export()
        if self._admitted:
            require(self.ledger._binding == self.binding
                    and self.execution_ledger._binding == self.binding, "root_binding_changed")
        if self.ids is not None:
            require(self.producer is not None and self.ids == {
                role: value["id"] for role, value in self.producer._owned.items()},
                "original_subjects_changed")

    def _remember(self, kind, value):
        self._validate()
        return self.records.save(kind, value)

    def _admit(self):
        import admission_budget_root_runtime as root
        import auth_protocol
        from . import runtime_registered_startup as startup
        from . import runtime_registered_cleanup as cleanup
        from . import runtime_registered_fixture_closeout as physical
        self._extra_modules = [root, auth_protocol, startup, cleanup, cleanup.parent, cleanup.pre,
            cleanup.producer, cleanup.durable, startup.profile, startup.costs, *physical._modules()]
        if self._diagnostic_mode:
            from . import runtime_auth_failure_component as diagnostic
            self._extra_modules.extend([diagnostic, diagnostic.witness, diagnostic.archive])
        self._extra_binding = source_binding.verify(self.gate, self._extra_modules)
        require(root.MANAGED_OBSERVATION_GROUP == "auth.managed_lifetime", "root_union_contract")
        self._managed_group = root.MANAGED_OBSERVATION_GROUP
        require(type(self.ledger) is root._Ledger and self.ledger._binding == self.binding
                and self.ledger.receipt().get("runtime_admitted") is True,
                "root_register_and_closure_not_integrated")
        stack = cleanup.parent.cparent.read_record(self.gate.out, "case-stack-bootstrap.json")[0]
        require(stack == self.stack and stack.get("scope") == "DISPOSABLE_CI_ONLY"
                and stack.get("sslmode") == "verify-full" and stack.get("ssl") is True
                and stack.get("source_commit") == self.binding["source_commit"]
                and stack.get("ci_run") == self.binding["ci_run"], "original_stack_receipt")
        self._envelope, self.execution_ledger = self.ledger.open_envelope(
            "case.auth.failures" if self._diagnostic_mode else "case.auth.context")
        require(type(self.execution_ledger) is root._Ledger, "root_child_type")
        self._admitted = True

    def _local_call(self, name, kind, action):
        """Source-owned dispatch; reservation is durable before action."""
        self._validate()
        require(source_binding.verify(self.gate, self._extra_modules) == self._extra_binding,
                "dependency_changed")
        ledger = self.execution_ledger
        require(self._admitted and ledger is not None, "dispatch_without_root")
        require(not self._closing or self._cleanup_selected, "cleanup_branch_not_admitted")
        ticket = ledger.precharge("auth." + name)
        self._calls.append({"id": "auth." + name, "kind": kind, "confirmed": False})
        try:
            if kind in ("connection", "connection_close"):
                from .runtime_registered_costs import native_proof
                native_proof(self.server.parameters)
            value = action()
        except BaseException as primary:
            try:
                if kind == "managed_auth" or name == "auth_start":
                    ledger.defer_fault(ticket)
                    self._deferred.append(ticket)
                elif kind == "validation":
                    ledger.fault(ticket, observed_sql_commands=0, reason="validation_failed")
                else:
                    ledger.unknown(ticket, reason="not_terminal")
            except BaseException as secondary:
                primary.add_note("secondary_root_unknown:" + type(secondary).__name__)
            raise
        try:
            if kind == "managed_auth" or name == "auth_start":
                ledger.defer(ticket)
                self._deferred.append(ticket)
            else:
                count = 10 if kind == "scope" else 1 if kind == "native_sql" else 0
                ledger.confirm(ticket, observed_sql_commands=count)
            self._calls[-1]["confirmed"] = True
        except BaseException:
            # A failed ledger publication after execution cannot authorize retry.
            raise
        return value

    def _seed(self):
        provenance = tracked.sha(json.dumps(self.ids, sort_keys=True).encode())
        self._seed_attempted = True  # Even a lost BEGIN is an attempted writer.
        commit_attempted = rollback_attempted = False
        try:
            self.server._sql("seed.begin", "BEGIN")
            for role in ("a_trainer", "a_member", "b_member"):
                self.server._sql("seed.profile." + role,
                    "insert into public.profiles(id,email,role,name,trainer_id) "
                    "values(%s,%s,%s,'CI synthetic',%s) returning id",
                    [self.ids[role], native_runtime.ALIASES[role],
                     "trainer" if role == "a_trainer" else "client",
                     self.ids["a_trainer"] if role == "a_member" else None])
                self.server._sql("seed.identity." + role,
                    "insert into fmz6e11_private.identities(user_id,role,provenance_sha) "
                    "values(%s,%s,%s) returning user_id", [self.ids[role], role, provenance])
            self.server._sql("seed.operator",
                "insert into fmz6e11_private.operators(user_id,enabled) values(%s,true) returning user_id",
                [self.ids["a_trainer"]])
            commit_attempted = True
            self.server._sql("seed.commit", "COMMIT")
            self._seed_ref = self._remember("seed_confirmed", {"provenance_sha256": provenance,
                "actor_hashes": {r: tracked.sha(v.encode()) for r, v in self.ids.items()},
                "explicit_commands": 9, "adopted_existing_rows": False})
        except BaseException as primary:
            # Lost COMMIT remains unknown. Never issue a second COMMIT or infer
            # rollback from a fresh connection's idle state.
            if not commit_attempted and not rollback_attempted:
                rollback_attempted = True
                try: self.server._sql("seed.rollback", "ROLLBACK")
                except BaseException as error:
                    primary.add_note("secondary_seed_rollback:" + type(error).__name__)
            raise

    def __enter__(self):
        require(not self._entered, "context_replay")
        self._entered = self._entering = True
        self.closeout = {"status": "NO_GO", "dispatches": 0, "known_owners": 0,
            "original_claims_released": False, "deletion_proven": False,
            "global_zero_claim": False, "full_chain_admission": False, "secondary_errors": []}
        try:
            self._source_snapshot = _source(self.gate)
            self.closeout["source_binding"] = self._source_snapshot
            af.binding(self.binding["run_id"])
            require(type(self.stack) is dict and self.stack.get("status") == "CLEAN47_BOOTSTRAP_PASS",
                    "clean47_required")
            # Reject ducktyped/caller-signed admission before loading optional
            # integration dependencies or touching any external resource.
            require(type(self.ledger).__module__ == "admission_budget_root_runtime",
                    "root_register_and_closure_not_integrated")
            self._admit()
            self.records = tracked.Records(pathlib.Path(self.gate.out) / "registered-context-private")
            from .runtime_registered_startup import LocalServer
            self.server = LocalServer(self)
            self.isolation = self.server.open()
            self.closeout["runtime_profile"] = copy.deepcopy(self.server.profile_receipt)
            self.runtime, self.admission_connection = self.server.runtime, dict(self.server.parameters)
            self.ca_path = pathlib.Path(self.server.parameters["sslrootcert"])
            if self._diagnostic_mode:
                # This job creates no bootstrap identities or fixture. The
                # eleven cases retain ownership and cleanup of their own actors.
                return self
            registry = tracked.Registry(pathlib.Path(self.gate.out) / "registered-request-private",
                                        run_id=self.binding["run_id"])
            budget = tracked.ParentBudget(pathlib.Path(self.gate.out) / "registered-create-budget-private",
                [{"method": "POST", "route": "/admin/users", "units": 128} for _ in ROLES],
                run_id=self.binding["run_id"])
            self.auth = tracked.Factory(registry, budget)(ORIGIN, LocalServer, self.server.admin, ValueError)
            self.producer = BootstrapRequests(_TOKEN, self.gate, self.auth, self.binding["run_id"])
            self.producer._context = self
            self.ids = self.producer.create_all()
            self._local_call("bootstrap_close", "filesystem", self.producer.close)
            self._seed()
            self.config = {**self.runtime.context(self.ids), "admin": self.server.admin,
                "anon": self.server.anon, "sourceSha": self.binding["source_commit"],
                "ciRun": self.binding["ci_run"]}
            self._yielded = True
            return self
        except BaseException as primary:
            self._finish(primary)
            raise
        finally:
            self._entering = False

    def run_auth_failures(self):
        from . import runtime_auth_failure_component as diagnostic
        frame = inspect.currentframe().f_back
        require(frame.f_code is diagnostic.run.__code__
                and frame.f_locals.get("context") is self and not self._entered,
                "diagnostic_entry_origin")
        del frame
        self._diagnostic_mode = True
        with self:
            self._diagnostic_report = diagnostic.execute(self)
        return self._diagnostic_report

    def bind_case(self, lifecycle, composition):
        from . import runtime_case_entry as caller
        from .runtime_adapter import CaseLifecycle, CaseComposition
        frame = inspect.currentframe().f_back
        require(frame.f_code is caller.execute_registered.__code__
                and frame.f_locals.get("context") is self
                and frame.f_locals.get("lifecycle") is lifecycle
                and frame.f_locals.get("c") is composition, "actual_case_caller")
        owners = frame.f_locals.get("owners")
        require(type(owners) is dict and owners.get("composition") is composition
                and owners.get("lifecycle") is lifecycle, "actual_case_owner_register")
        del frame
        require(self._yielded and not self._closing and self._case is None
                and type(lifecycle) is CaseLifecycle and type(composition) is CaseComposition
                and lifecycle.ids == self.ids and lifecycle.composition is composition,
                "actual_case_objects")
        source_binding.verify(self.gate, [caller, sys.modules[CaseComposition.__module__]])
        self._case = (lifecycle, composition)
        self._case_owners = owners
        from . import runtime_registered_fixture_closeout as physical
        self._fixture_registration = physical.prepare(self)

    def _body_terminal(self):
        """Read the live source-owned D producers; this is not fixture deletion."""
        from . import runtime_http, runtime_dispatch, runtime_parent_workflow, runtime_recovery, runtime_terminal
        self._validate()
        require(self._case is not None and self._case_owners is not None, "body_not_owned")
        lifecycle, composition = self._case
        owners = self._case_owners
        require(owners.get("composition") is composition and owners.get("lifecycle") is lifecycle
                and lifecycle.composition is composition and lifecycle.ids == self.ids,
                "body_owner_changed")
        sources = source_binding.verify(self.gate, [
            runtime_http, runtime_dispatch, runtime_parent_workflow, runtime_recovery, runtime_terminal])
        fault = composition.phase_faults
        terminal = runtime_terminal.validate_runtime_termination(owners["gate"], composition, lifecycle,
            case_name=fault.case, fault=fault, worker_result=owners["result"],
            original_error=owners["original_error"], fixture_closeout={},
            isolation=self.isolation)
        require(terminal.get("worker_terminated") is True, "worker_reap_unconfirmed")
        from .runtime_registered_cleanup import parent
        require(owners.get("terminal_proof") == terminal
                and parent.cparent.read_record(self.gate.out, "case-runtime-terminal.json")[0] == terminal,
                "original_worker_terminal_receipt")
        journal = getattr(lifecycle, "http_journal", None)
        require(type(journal) is runtime_http.HttpJournal
                and journal.composition is composition and journal.gate is lifecycle.gate,
                "live_http_journal")
        http = journal.receipt()
        evidence = runtime_terminal.Evidence(owners["gate"])
        require(evidence.read("case-auth-http-terminal.json", prefixed=False) == http,
                "original_http_receipt")
        evidence.original(http["journal_ref"], "case-auth-http.ledger.txt", 262144)
        require(http["run_id"] == self.binding["run_id"]
                and http["snapshot"]["sealed"] is True and http["all_responses_terminal"] is True
                and http["unknown_attempts"] == http["unresolved_intents"] == 0,
                "body_http_unknown")
        expected = composition.quota["manifest"]["sources"]
        root = pathlib.Path(self.gate.sources).resolve()
        for name in ("runtime_http.mjs", "runtime_auth.mjs", "runtime_integral_workflow.mjs"):
            relative = "_offline/phase6e11/endchain_v1/quota_candidate_v1/" + name
            require(tracked.sha(runtime_terminal.read_under(root, relative)) == expected[relative],
                    "body_transport_source_changed")
        dispatch = getattr(composition, "workflow_dispatch", None)
        require(type(dispatch) is runtime_dispatch.WorkflowDispatch and dispatch.meter is composition.meter,
                "live_workflow_http_dispatch")
        recovery = getattr(composition, "workflow_recovery", None)
        require(type(recovery) is dict and evidence.read("case-workflow-recovery.json") == recovery
                and recovery.get("worker_terminated") is True, "original_workflow_reap")
        workflow = runtime_http.workflow_receipt(composition, worker_terminated=recovery["worker_terminated"])
        require(evidence.read("case-workflow-http-terminal.json") == workflow
                and workflow["run_id"] == self.binding["run_id"]
                and workflow["all_responses_terminal"] is True and workflow["pending"] is None,
                "original_workflow_dispatch")
        return {"source_binding": sources, "worker": terminal, "http": http,
                "workflow": workflow, "evidence_refs": list(evidence.refs.values()),
                "fixture_zero_proven": False, "deletion_admitted": False,
                "global_zero_claim": False, "full_chain_admission": False}

    def _finish(self, primary):
        if self._finished:
            return
        self._finished = self._closing = True
        errors = []
        if self.closeout is None:
            return
        def attempt(stage, action):
            try:
                return action()
            except BaseException as error:
                errors.append(error)
                self.closeout["secondary_errors"].append({"phase": stage, "class": type(error).__name__})
                if primary is not None: primary.add_note("secondary_context_" + stage + ":" + type(error).__name__)
                return None
        if self.execution_ledger is not None:
            # Selection reads this actual Context; no caller-supplied branch or
            # claim can grant a suffix. Failure still closes the HTTP producer.
            try:
                self.execution_ledger.select_cleanup(self)
                self._cleanup_selected = True
            except BaseException as error:
                errors.append(error)
                self.closeout["secondary_errors"].append(
                    {"phase": "cleanup_selection", "class": type(error).__name__})
                if primary is not None:
                    primary.add_note("secondary_context_cleanup_selection:" + type(error).__name__)
        if (self.producer is None and type(self.auth) is tracked.TrackedAuth
                and type(self.auth.registry) is tracked.Registry
                and self.auth.registry.phase == "OPEN"):
            # Failed producer construction grants no ownership. It still must
            # deny future work, including an unexpected nonempty worker set.
            attempt("rejected_producer_close", self.auth.close_and_drain)
        if self._diagnostic_registry is not None:
            self._diagnostic_seal = attempt("diagnostic_registry_close", lambda:
                self._local_call("failure_registry_close", "filesystem",
                                 self._diagnostic_registry.close_and_drain))
            if self._diagnostic_seal is not None:
                self.closeout["diagnostic_request_registry"] = attempt(
                    "diagnostic_registry_receipt", self._diagnostic_registry.records.export)
        if self.producer is not None:
            if not self.producer._closed:
                attempt("producer_close", self.producer.close)
            self.closeout["known_owners"] = len(self.producer._owned)
            if not self._seed_attempted and not self._yielded and primary is not None:
                from . import runtime_registered_cleanup as cleanup
                result = None
                try:
                    result = cleanup.run(self, primary)
                except BaseException as error:
                    errors.append(error)
                    self.closeout["secondary_errors"].append(
                        {"phase": "owned_cleanup", "class": type(error).__name__})
                    primary.add_note("secondary_context_owned_cleanup:" + type(error).__name__)
                if result is not None:
                    self.closeout["deletion_proven"] = result["suffix_status"] == "SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED"
                    self.closeout["cleanup"] = result
            else:
                if self._case is not None and self._seed_ref is not None:
                    from . import runtime_registered_fixture_closeout as physical
                    from . import runtime_registered_cleanup as cleanup
                    try:
                        # Both adapters require this exact source-owned caller.
                        # C validates live HTTP/worker closure before any DELETE.
                        self._fixture_proof = physical.run(self)
                        self.closeout["fixture_closure"] = self._fixture_proof.receipt
                        self.closeout["fixture_closure_ref"] = self._fixture_proof.ref
                        result = cleanup.run(self, primary, fixture_proof=self._fixture_proof)
                        self.closeout["cleanup"] = result
                        self.closeout["deletion_proven"] = (
                            result["suffix_status"] == "SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED")
                    except BaseException as error:
                        errors.append(error)
                        self.closeout["secondary_errors"].append(
                            {"phase": "registered_cleanup", "class": type(error).__name__})
                        if primary is not None:
                            primary.add_note("secondary_context_registered_cleanup:" + type(error).__name__)
                        self.closeout["cleanup_missing"] = ["registered_C_and_Auth_closure_unconfirmed"]
                else:
                    self.closeout["cleanup_missing"] = ["confirmed_seed_and_registered_case_required"]
        process_result = None
        if self.server is not None:
            process_result = attempt("server_close", self.server.close)
            if process_result is not None: self.closeout["process"] = process_result
        if self.execution_ledger is not None:
            attempt("root_close", lambda: self._settle_root(process_result))
        self.closeout["dispatches"] = len(self._calls)
        self.closeout["commands"] = copy.deepcopy(self._calls)
        self.closeout["original_exception_class"] = type(primary).__name__ if primary else None
        if self.producer is not None:
            evidence = attempt("ownership_receipt", self.producer.receipt)
            if evidence is not None:
                self.closeout["ownership_evidence"] = evidence
            else:
                self.closeout["deletion_proven"] = False
        if self.records is not None:
            reference = attempt("receipt", lambda: self.records.save("closeout", self.closeout))
            if reference is not None:
                self.closeout_ref = {"path": (self.records.folder / reference["name"]).relative_to(
                    self.gate.out).as_posix(), "sha256": reference["sha256"]}
        if self.config is not None:
            self.config.pop("admin", None)
            self.config.pop("anon", None)
        if self.admission_connection is not None: self.admission_connection.clear()
        if primary is None and (errors or self.closeout.get("cleanup_missing")):
            raise errors[0] if errors else tracked.Blocked("registered_bootstrap_cleanup_join_pending")

    def _settle_root(self, process_result):
        """Union the measured Auth lifetime once; do not sum overlapping calls."""
        self._validate()
        ledger = self.execution_ledger
        tickets = ledger.deferred_group(self._managed_group)
        if tickets:
            require(type(process_result) is dict and process_result.get("process_stopped") is True,
                    "managed_process_not_terminal")
            numeric = process_result.get("managed_sql")
            require(type(numeric) is dict and type(numeric.get("commands")) is int
                    and numeric["commands"] >= 0, "managed_lifetime_not_numeric")
            # Includes D's deferred core managed partition. Its native partition
            # was already recorded by D and is not added here a second time.
            ledger.settle_union(tickets, observed_sql_commands=numeric["commands"])
        for ticket in self._deferred:
            if ticket not in tickets:
                # Driver implicit SQL remains unknown, not an invented zero.
                ledger.settle_deferred(ticket, observed_sql_commands=None)
        receipt = ledger.close()
        complete = all(row["state"] in ("confirmed", "fault_numeric_confirmed", "covered_by_numeric_union")
                       for row in receipt["events"])
        observed = receipt["observed_sql_commands"] if complete else None
        self.ledger.close_envelope(self._envelope, ledger, observed_sql_commands=observed)
        self.closeout["root_accounting"] = receipt
        self.closeout["numeric_lifetime_complete"] = complete
        if not complete:
            self.closeout["root_observation_missing"] = "unproven_driver_or_other_native_partition"

    def __exit__(self, exc_type, primary, tb):
        self._finish(primary)
        return False


def context(gate, *, binding, stack, ledger):
    return Context(gate, binding=binding, stack=stack, ledger=ledger)


def _record_references(context):
    """Complete original tracked record sets, with no newly accepted hashes."""
    context._validate()
    collections = [context.records, context.auth.budget.records,
                   *context.auth.registry._recordsets]
    refs = {}
    for records in collections:
        require(type(records) is tracked.Records, "actual_recordset_required")
        snapshot = records.validate()
        for name, raw in snapshot.items():
            path = (records.folder / name).relative_to(context.gate.out).as_posix()
            ref = {"path": path, "sha256": records._hashes[name], "bytes": len(raw)}
            require(path not in refs or refs[path] == ref, "conflicting_original_reference")
            refs[path] = ref
    return [refs[name] for name in sorted(refs)]


def validate_closeout(context, *, gate, binding):
    """Read live closed capabilities and original bytes, never a summary flag.

    A successful scoped closeout does not erase the original case failure or
    unknown historical claims, and is not an endchain admission decision.
    """
    from . import runtime_registered_cleanup as cleanup
    require(type(context) is Context and gate is context.gate
            and binding == context.binding and context._finished and context._closing
            and context._admitted and context.closeout_ref is not None,
            "actual_closed_context")
    context._validate()
    require(source_binding.verify(gate, context._extra_modules) == context._extra_binding,
            "closeout_source_changed")
    original = cleanup.parent.cparent.reference(gate.out, context.closeout_ref)
    # The strict reference helper validates bytes and returns their content.
    require(type(original) is dict and original.get("kind") == "closeout"
            and {k: v for k, v in original.items() if k not in ("sequence", "kind")}
                == context.closeout, "original_closeout_changed")
    report = context.closeout
    require(not report["secondary_errors"] and not report.get("cleanup_missing")
            and report["deletion_proven"] is True and report.get("numeric_lifetime_complete") is True,
            "incomplete_closeout")
    proof = context._auth_cleanup_proof
    require(type(proof) is cleanup.Prerequisite and proof.state().owner is context
            and proof.state().consumed, "actual_auth_cleanup_proof")
    proof.unchanged()
    require(context.producer.receipt() == report["ownership_evidence"], "original_ownership_changed")
    if context._yielded:
        from . import runtime_registered_fixture_closeout as physical
        require(type(context._fixture_proof) is physical.Proof
                and context._fixture_proof is proof.state().fixture_proof
                and context._fixture_proof.owner is context, "actual_fixture_cleanup_proof")
        require(context._fixture_proof.ref == report["fixture_closure_ref"]
                and context._fixture_proof.receipt == report["fixture_closure"], "original_fixture_changed")
    else:
        require(proof.state().fixture_proof is None and not context._seed_attempted,
                "exact_preseed_closeout")
    engine = report["cleanup"]
    require(engine["suffix_status"] == "SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED"
            and all(v.get("acknowledged") is True for v in engine["deletes"].values())
            and set(engine["deletes"]) == set(proof.roles), "auth_delete_incomplete")
    folder = pathlib.Path(gate.out) / "auth-registered-bootstrap-engine-private"
    files = engine["retained_journal"]["files"]
    require(not folder.is_symlink() and {p.name for p in folder.iterdir()} == set(files),
            "original_engine_inventory_changed")
    refs = _record_references(context)
    state = proof.state()
    state.journal._inventory()
    for name, item in state.journal.entries.items():
        raw = state.journal._read(name, item)
        refs.append({"path": (state.journal.folder / name).relative_to(gate.out).as_posix(),
                     "sha256": item["sha256"], "bytes": len(raw)})
    for path, digest in proof.hashes.items():
        cleanup.parent.cparent.reference(gate.out, {"path": path, "sha256": digest})
        refs.append({"path": path, "sha256": digest, "bytes": (pathlib.Path(gate.out) / path).stat().st_size})
    for name, item in files.items():
        ref = {"path": (folder / name).relative_to(gate.out).as_posix(), "sha256": item["sha256"]}
        value = cleanup.parent.cparent.reference(gate.out, ref)
        require(value == item["content"] and (folder / name).stat().st_size == item["bytes"],
                "original_engine_record_changed")
        refs.append({**ref, "bytes": item["bytes"]})
    process = report["process"]
    require(context.server.closed and process["process_stopped"] is True
            and type(process["managed_sql"]["commands"]) is int, "process_not_terminal")
    profile = context.server.profile_receipt
    require(type(profile) is dict and profile == report["runtime_profile"]
            and profile["receipt"]["status"] == "LOCALONLY_RUNTIME_CAPABILITY_REDUCED"
            and profile["receipt"]["commit_confirmed"] is True
            and profile["receipt"]["commit_unknown"] is False, "original_runtime_profile")
    require(cleanup.parent.cparent.reference(gate.out, profile["ref"]) == profile["receipt"],
            "original_profile_receipt")
    require(type(profile.get("evidence_refs")) is list and profile["evidence_refs"],
            "complete_profile_evidence")
    for ref in profile["evidence_refs"]:
        cleanup.parent.cparent.reference(gate.out, {"path": ref["path"], "sha256": ref["sha256"]})
        require((pathlib.Path(gate.out) / ref["path"]).stat().st_size == ref["bytes"],
                "original_profile_record_size")
        refs.append(dict(ref))
    accounting = context.execution_ledger.receipt()
    require(accounting == report["root_accounting"] and accounting.get("closed") is True
            and accounting.get("program_exhausted") is True and accounting.get("pending") is False,
            "root_not_closed")
    require(all(row["state"] in ("confirmed", "fault_numeric_confirmed", "covered_by_numeric_union")
                for row in accounting["events"]), "unknown_root_partition")
    import admission_budget_root_runtime as root
    numeric = root.validate_terminal(context.execution_ledger, gate, binding)
    require(numeric["status"] == "NUMERIC_ACCOUNTING_CLOSED", "actual_numeric_root_terminal")
    unique = {}
    for ref in refs:
        require(ref["path"] not in unique or unique[ref["path"]] == ref, "conflicting_closeout_reference")
        unique[ref["path"]] = ref
    refs = [unique[name] for name in sorted(unique)]
    return {"status": "SCOPED_REGISTERED_CONTEXT_CLOSED", "binding": copy.deepcopy(binding),
            "source_binding": copy.deepcopy(context._source_snapshot), "evidence_refs": refs,
            "evidence_record_count": len(refs), "evidence_bytes": sum(r["bytes"] for r in refs),
            "closeout_ref": dict(context.closeout_ref),
            "original_error_class": report["original_exception_class"],
            "global_zero_claim": False, "original_claims_released": False,
            "full_chain_admission": False}

