"""Disposable composition of distinct fixture and Auth closure proofs.

An unknown historical commit never becomes confirmed. The optional physical
zero suffix permits only new, separately evidenced registry/Auth cleanup.
"""
import sys
import auth_pre_fixture_closure
import fixture_db_terminality as db
import fixture_producer_scope as producer
import fixture_parent_physical_zero as physical
import fixture_parent_closure as parent
import auth_failure_parent_finalizer as auth_parent
from fixture_cleanup_runtime import Blocked


def file_ref(out, name):
    _, digest = parent.read_record(out, name)
    return {'path': name, 'sha256': digest}


class Closure:
    def __init__(self, gate, save):
        self.gate, self.save = gate, save
        self.scope = self.tracked = self.terminal_ref = None
        self.started = self.finalized = False
        self.fixture_mutation_started = False
        self.pre_fixture = auth_pre_fixture_closure.Guard(self)

    def before_bootstrap_write(self):
        self.pre_fixture.before_bootstrap_write()
        self.fixture_mutation_started = True

    def begin(self, ctx):
        if self.started:
            raise Blocked('composition_duplicate_bootstrap')
        self.started = True
        with ctx['suspend_admin']():
            self.scope = producer.Scope(self.gate)
            self.scope.before_bootstrap()
        self.tracked = db.TrackedRuntime.disposable(self.gate, self.save)
        return self.tracked

    def bind_terminal(self):
        # Only the sealed original journal may supply the observed terminal.
        evidence = parent.Evidence(self.gate)
        record = evidence.get('fixture-cleanup-db-terminal.json')
        if (record.get('component_status') != 'COMPONENT_PASS'
                or record.get('terminal', {}).get('db_terminality_proven') is not True):
            raise Blocked('composition_fixture_terminal_missing')
        self.save('admission-fixture-terminal.json', record['terminal'])
        self.terminal_ref = file_ref(self.gate.out, 'admission-fixture-terminal.json')
        evidence.unchanged()

    def finalize(self, ctx, auth, seal):
        if self.finalized:
            raise Blocked('composition_duplicate_finalizer')
        self.finalized = True
        primary = sys.exception()
        if self.tracked is None and not self.fixture_mutation_started and primary is not None:
            previous_save = self.gate.save
            self.gate.save = self.save
            try:
                return auth_pre_fixture_closure.cleanup(self, ctx, auth, seal,
                    primary=primary, delete_costs={'a': 128, 'trainer': 128, 'b': 128})
            finally:
                self.gate.save = previous_save
        if (self.tracked is None or self.scope is None or self.terminal_ref is None
                or not auth.registry.valid_proof(seal)):
            raise Blocked('composition_incomplete_fixture_or_auth_proof')
        previous_save = self.gate.save
        self.gate.save = self.save
        try:
            name = 'admission-auth-request-registry/' + seal.refs['name']
            close_ref = file_ref(self.gate.out, name)
            if close_ref['sha256'] != seal.refs['sha256']:
                raise Blocked('composition_auth_seal_changed')
            with ctx['suspend_admin']():
                result = physical.run(self.gate, scope=self.scope, tracked=self.tracked,
                    terminal_ref=self.terminal_ref, auth_close_ref=close_ref)
            if (result.get('registry_deletion_proven') is not True
                    or result.get('registry_absence_confirmed') is not True
                    or result.get('original_receipts_unchanged') is not True):
                raise Blocked('composition_registry_closure_incomplete')
            ref = file_ref(self.gate.out, 'fixture-parent-physical-zero-private/result.json')
            return auth_parent.finalize(self.gate, ctx, auth, seal, ref,
                delete_costs={'a': 128, 'trainer': 128, 'b': 128})
        finally:
            self.gate.save = previous_save
