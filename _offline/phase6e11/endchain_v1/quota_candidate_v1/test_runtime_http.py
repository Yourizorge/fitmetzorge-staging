"""Actual local receipt IO and synthetic dispatch, not Auth/SQL evidence."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

from quota_candidate_v1 import runtime_http as h
from quota_candidate_v1.runtime_adapter import CaseLifecycle, RegisteredLifecycle
from quota_candidate_v1.runtime_dispatch import WorkflowDispatch


def snapshot(*, attempted=False, terminal=False, sealed=False, status=None):
    return {'format':'case-auth-http-v1','sealed':sealed,'rows':[
        {'ordinal':1,'role':'a_member','operation':'verify','safety':False,
         'attempted':attempted,'terminal':terminal,'status':status}]}


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        target=self.root/h.PREFIX;target.mkdir(parents=True)
        sources={}
        for name in ('runtime_http.py','runtime_http.mjs','runtime_auth.mjs',
                     'runtime_dispatch.py','runtime_parent_workflow.py',
                     'runtime_integral_workflow.mjs','runtime_recovery.py'):
            raw=(pathlib.Path(h.__file__).parent/name).read_bytes()
            (target/name).write_bytes(raw);sources[h.PREFIX+name]=h.sha(raw)
        import auth_failure_transport
        name='_offline/phase6e11/endchain_v1/auth_failure_transport.py'
        raw=pathlib.Path(auth_failure_transport.__file__).read_bytes()
        (self.root/name).write_bytes(raw);sources[name]=h.sha(raw)
        self.gate=types.SimpleNamespace(out=self.root)
        self.c=types.SimpleNamespace(quota={'root':self.root,'manifest':{'sources':sources},
            'binding':{'run_id':'unit','binding_sha':'a'*64}})
        self.journal=h.HttpJournal(self.gate,self.c)

    def test_full_body_evidence_separate_from_revocation_and_worker_reap(self):
        self.journal.accept(snapshot())
        self.journal.accept(snapshot(attempted=True,status=200))
        self.assertFalse(self.journal.receipt()['all_responses_terminal'])
        self.journal.accept(snapshot(attempted=True,status=200,terminal=True))
        self.assertFalse(self.journal.receipt()['all_responses_terminal'])
        self.journal.accept(snapshot(attempted=True,status=200,terminal=True,sealed=True))
        value=self.journal.receipt()
        self.assertTrue(value['all_responses_terminal'])
        for name in ('worker_termination_proven','revocation_proven','deletion_admitted'):
            self.assertFalse(value[name])
        self.assertEqual(value['journal_ref']['sha256'],h.sha(self.journal.path.read_bytes()))
        lines=[json.loads(line) for line in self.journal.path.read_bytes().splitlines()]
        self.assertEqual(len(lines),5)
        prefix=b''
        for index,line in enumerate(self.journal.path.read_bytes().splitlines(keepends=True)):
            if index:self.assertEqual(json.loads(line)['previous_sha256'],h.sha(prefix))
            prefix+=line

    def test_unknown_or_unattempted_intent_never_complete_even_sealed(self):
        for attempted in (False,True):
            self.journal.accept(snapshot(attempted=attempted))
            value=self.journal.receipt()
            self.assertFalse(value['all_responses_terminal'])
            self.assertEqual(value['unknown_attempts'],int(attempted))
            self.assertEqual(value['unresolved_intents'],1)
        self.journal.accept(snapshot(attempted=True,sealed=True))
        self.assertFalse(self.journal.receipt()['all_responses_terminal'])

    def test_extra_token_field_rejected_and_failure_sticky(self):
        value=snapshot();value['rows'][0]['token']='unit-secret'
        with self.assertRaisesRegex(ValueError,'case_http_row'):self.journal.accept(value)
        with self.assertRaisesRegex(ValueError,'journal_failed'):self.journal.accept(snapshot())
        self.assertNotIn(b'unit-secret',self.journal.path.read_bytes())

    def test_terminal_retraction_or_intent_rewrite_denied(self):
        self.journal.accept(snapshot(attempted=True,terminal=True,status=200))
        value=snapshot(attempted=True,terminal=True,status=200);value['rows'][0]['role']='b_member'
        with self.assertRaisesRegex(ValueError,'intent_changed'):self.journal.accept(value)

    def test_new_intent_after_unresolved_prefix_denied(self):
        value=snapshot(attempted=True,status=200)
        self.journal.accept(value)
        new=copy.deepcopy(value['rows'][0]);new['ordinal']=2;value['rows'].append(new)
        with self.assertRaisesRegex(ValueError,'unresolved_prefix'):self.journal.accept(value)

    def test_external_journal_modification_is_not_overwritten(self):
        altered=self.journal.path.read_bytes()+b'unit corruption\n'
        self.journal.path.write_bytes(altered)
        with self.assertRaisesRegex(ValueError,'journal_changed'):self.journal.accept(snapshot())
        self.assertEqual(self.journal.path.read_bytes(),altered)
        with self.assertRaises(ValueError):self.journal.receipt()

    def test_exclusive_creation_and_source_hashes_fail_closed(self):
        with self.assertRaises(FileExistsError):h.HttpJournal(self.gate,self.c)
        self.c.quota['manifest']['sources'][h.PREFIX+'runtime_http.mjs']='0'*64
        with self.assertRaisesRegex(ValueError,'case_http_source'):h.HttpJournal(self.gate,self.c)

    def test_unchanged_snapshot_does_not_append_or_add_commands(self):
        self.journal.accept(snapshot());raw=self.journal.path.read_bytes()
        self.journal.accept(snapshot());self.assertEqual(self.journal.path.read_bytes(),raw)
        for key in ('additional_sql_commands','additional_http_requests','additional_ipc_messages'):
            self.assertEqual(self.journal.receipt()[key],0)

    def workflow(self):
        tickets=tuple(range(1,73))
        meter=types.SimpleNamespace(events=[{'kind':'managed_auth','commands':5,'confirmed':False,
            'action':'gotrue_fixture_identity' if i==0 else 'gotrue_workflow_identity_'+str(i-1)}
            for i in range(72)],managed_pending=set(tickets),stopped=False,closed=False,used=10,state={})
        self.c.workflow_dispatch=WorkflowDispatch(meter,tickets)
        return self.c.workflow_dispatch

    def test_workflow_headers_lost_reply_and_unreaped_child_remain_unknown(self):
        dispatch=self.workflow();dispatch.before(0)
        value=h.workflow_receipt(self.c,worker_terminated=True)
        self.assertEqual(value['pending'],0)
        self.assertFalse(value['all_responses_terminal'])
        dispatch.after(0,'lost_response')
        value=h.workflow_receipt(self.c,worker_terminated=True)
        self.assertIsNone(value['pending']);self.assertFalse(value['all_responses_terminal'])
        self.assertFalse(value['deletion_admitted'])

    def test_workflow_complete_framed_response_never_proves_identity_or_sql_cost(self):
        dispatch=self.workflow();dispatch.before(0);dispatch.after(0,'response_received',500)
        value=h.workflow_receipt(self.c,worker_terminated=True)
        self.assertTrue(value['all_responses_terminal'])
        self.assertEqual(value['observed_attempts'],1)
        for key in ('identity_verified','individual_sql_cost_observed','full_chain_admission'):
            self.assertFalse(value[key])
        self.assertFalse(h.workflow_receipt(self.c,worker_terminated=False)['all_responses_terminal'])
        self.assertNotIn('state_before',value['rows'][0])

    def test_workflow_transport_source_drift_fails_before_terminal_claim(self):
        self.workflow()
        self.c.quota['manifest']['sources']['_offline/phase6e11/endchain_v1/auth_failure_transport.py']='0'*64
        with self.assertRaisesRegex(ValueError,'workflow_source'):
            h.workflow_receipt(self.c,worker_terminated=True)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.lifecycle=object.__new__(CaseLifecycle)
        self.lifecycle.http_journal=mock.Mock()
        self.lifecycle.composition=mock.Mock()
        self.lifecycle.failed=False

    def test_parent_dispatch_strips_metadata_only_after_journal_accept(self):
        order=[]
        self.lifecycle.http_journal.accept.side_effect=lambda value:order.append('journal')
        with mock.patch.object(RegisteredLifecycle,'dispatch',side_effect=lambda value:order.append(value)):
            self.lifecycle.dispatch({'op':'remove','http_terminal':snapshot()})
        self.assertEqual(order,['journal',{'op':'remove'}])

    def test_journal_failure_prevents_original_dispatch_and_aborts_without_masking(self):
        original=ValueError('unit journal failure')
        self.lifecycle.http_journal.accept.side_effect=original
        self.lifecycle.composition.abort.side_effect=RuntimeError('unit abort failure')
        with mock.patch.object(RegisteredLifecycle,'dispatch') as dispatch:
            with self.assertRaises(ValueError) as caught:
                self.lifecycle.dispatch({'op':'remove','http_terminal':snapshot()})
        self.assertIs(caught.exception,original);dispatch.assert_not_called()
        self.assertTrue(self.lifecycle.failed)
        self.assertEqual(original.__notes__,['case_http_abort_secondary:RuntimeError'])


if __name__=='__main__':unittest.main()
