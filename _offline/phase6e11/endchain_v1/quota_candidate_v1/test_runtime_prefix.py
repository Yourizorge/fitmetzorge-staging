"""Offline protocol/capacity tests; no real CLI, PostgreSQL or Auth proof."""
import copy
import json
import types
import unittest
from unittest import mock
from quota_candidate_v1 import runtime_prefix as p
from quota_candidate_v1.compiler import CandidateStop, sha


class Meter:
    def __init__(self): self.events=[]; self.stopped=False; self.closed=False; self.used=0
    def charge(self, phase, count, **kwargs):
        if self.stopped: raise ValueError('stopped')
        self.events.append(dict(phase=phase,commands=count,confirmed=False,**kwargs));self.used+=count
        return len(self.events)
    def confirm(self, ticket): self.events[ticket-1]['confirmed']=True


class PrefixTests(unittest.TestCase):
    def fixture(self, slot='quota'):
        policy=dict(environment='disposable_ci',source_commit='a'*40,candidate_sha256='b'*64,
            invocation_id='unit-only',slot=slot,cap=p.SLOTS[slot],dry_run=slot!='quota',
            closure_reserve=1 if slot=='quota' else 0,upstream_commit=p.common.UPSTREAM,
            host='127.0.0.1',database='postgres',user='postgres',
            expected_history_versions=[str(i) for i in range(47 if slot=='quota' else 48)],
            migrations=[dict(sha256='c'*64,version='20261103010101',ast_hashes=['d'*64]*17)] if slot=='quota' else [])
        rows=[dict(event='dispatch',id=i+1,category='migration',ast_sha256='d'*64,kind='ddl') for i in range(17)]
        rows += [dict(event='dispatch',id=18,category='migration_history',ast_sha256='e'*64,kind='insert')]
        if slot!='quota':rows=[dict(event='dispatch',id=1,category='history',ast_sha256='f'*64,kind='select')]
        rows += [dict(event='history_snapshot',matches_policy=True,count=len(policy['expected_history_versions']),
            versions_sha256=sha(json.dumps(policy['expected_history_versions'],separators=(',',':')).encode()))]
        if slot=='quota':rows += [dict(event='history_bind',migration_sha256='c'*64,version='20261103010101',statement_count=17)]
        receipt=dict(header={**policy, 'policy_sha256':sha(json.dumps(policy,separators=(',',':')).encode())},
            terminal=dict(complete=True,connection_attempts=1,unknown_consumed=0,sql_dispatches=18 if slot=='quota' else 1),
            terminal_recorded=True,events=rows,observer_trace=[{'confirmed':True} for _ in range(8)],
            tracking={'valid':True},numeric_coverage={'all_protocol_visible':True,'temp_written':0},
            slot=slot,complete=True,source_commit='a'*40,candidate_sha256='b'*64,run_id='unit-only',receipt_name='unit.json')
        context={'binding':{'source_commit':'a'*40,'candidate_sha':'b'*64}}
        return policy,receipt,context

    def test_exact_17_apply_and_48_history_empty_dry(self):
        for slot in p.NAMES:
            policy,receipt,context=self.fixture(slot)
            p.verify_policy(policy,context,slot,versions=policy['expected_history_versions'],target_sha='c'*64)
            p.validate_evidence(receipt,policy,b'up to date')
            self.assertEqual(p.charged(p.compatible(receipt)),72 if slot=='quota' else 36)

    def test_reject_partial_or_unknown_terminal_even_exit_zero(self):
        for field,value in [('complete',False),('connection_attempts',2),('unknown_consumed',1),('sql_dispatches',65)]:
            policy,receipt,_=self.fixture();receipt['terminal'][field]=value
            with self.subTest(field=field),self.assertRaises(CandidateStop):p.validate_evidence(receipt,policy,b'')

    def test_missing_durable_terminal_denied(self):
        policy,receipt,_=self.fixture();receipt['terminal_recorded']=False
        with self.assertRaises(CandidateStop):p.validate_evidence(receipt,policy,b'')

    def test_wrong_candidate_header_rejected(self):
        policy,receipt,_=self.fixture();receipt['header']['candidate_sha256']='0'*64
        with self.assertRaisesRegex(CandidateStop,'prefix_header_binding'):p.validate_evidence(receipt,policy,b'')

    def test_apply_cannot_reuse_canonical_receipt_or_sixteen_statements(self):
        for alter in (lambda p:p['migrations'][0].update(sha256='0'*64),lambda p:p['migrations'][0]['ast_hashes'].pop()):
            policy,receipt,context=self.fixture();alter(policy)
            with self.assertRaises(CandidateStop):p.verify_policy(policy,context,'quota',versions=policy['expected_history_versions'],target_sha='c'*64)

    def test_all_observers_numeric_and_temp_required(self):
        for alter in (lambda r:r['observer_trace'].pop(),lambda r:r['observer_trace'][0].update(confirmed=False),
                      lambda r:r['numeric_coverage'].update(temp_written=1),lambda r:r['tracking'].update(valid=False)):
            policy,receipt,_=self.fixture();alter(receipt)
            with self.assertRaises(CandidateStop):p.validate_evidence(receipt,policy,b'')

    def test_dry_cannot_claim_zero_pending_with_wrong_actual_history(self):
        policy,receipt,_=self.fixture('final');receipt['events'][-1]['count']=47
        with self.assertRaisesRegex(CandidateStop,'prefix_dry_history'):p.validate_evidence(receipt,policy,b'up to date')

    def test_dry_rejects_pending_or_body_dispatch(self):
        for output,category in [(b'would push', 'history'),(b'up to date','migration')]:
            policy,receipt,_=self.fixture('pre_auth');receipt['events'][0]['category']=category
            with self.assertRaises(CandidateStop):p.validate_evidence(receipt,policy,output)

    def prefix(self):
        value=object.__new__(p.PendingPrefix);meter=Meter()
        value.composition=types.SimpleNamespace(meter=meter,abort=lambda reason:setattr(meter,'stopped',True))
        value.context={'root':'unit','manifest':{},'binding':{'source_commit':'a'*40,'candidate_sha':'b'*64,'run_id':'unit'}}
        value.gate=types.SimpleNamespace(save=lambda *args:None)
        value.attempts=[];value.cli_protocol=[];value.migration_sources={};value.sql_sha='c'*64;value.version='20261103010101'
        return value,meter

    def test_full72_prepaid_before_attempt_unknown_keeps72_and_forbids_retry(self):
        prefix,meter=self.prefix()
        def lost(slot,receipt):
            self.assertEqual(meter.used,72);self.assertEqual(prefix.attempts,['quota'])
            raise RuntimeError('unit_lost_cli_result')
        prefix._invoke=lost
        with mock.patch.object(p,'validate_case_binding'):
            with self.assertRaisesRegex(RuntimeError,'unit_lost_cli_result'):prefix.run_pending()
            self.assertEqual(meter.used,72);self.assertFalse(meter.events[0]['confirmed'])
            self.assertTrue(meter.stopped)
            with self.assertRaisesRegex(CandidateStop,'prefix_slot_or_retry'):prefix.run_pending()

    def test_dry_requires_exact_unconfirmed_prepaid_ticket_never_doublecharges(self):
        prefix,meter=self.prefix()
        with self.assertRaises(CandidateStop):prefix._ticket('pre_auth',None)
        ticket=meter.charge('migration',36,action='pre_auth_empty_cli_dry_run',kind='cli_reserved')
        self.assertEqual(prefix._ticket('pre_auth',ticket),ticket);self.assertEqual(meter.used,36)
        meter.confirm(ticket)
        with self.assertRaises(CandidateStop):prefix._ticket('pre_auth',ticket)

    def test_save_secondary_does_not_replace_original(self):
        prefix,meter=self.prefix()
        prefix._invoke=mock.Mock(side_effect=RuntimeError('unit_original'))
        prefix.gate.save=mock.Mock(side_effect=OSError('unit_disk'))
        with mock.patch.object(p,'validate_case_binding'),self.assertRaisesRegex(RuntimeError,'unit_original') as raised:
            prefix.run_pending()
        self.assertEqual(raised.exception.__notes__,['prefix_receipt_secondary:OSError'])
        self.assertEqual(meter.used,72)

    def test_gate_rejects_legacy_apply_and_other_cli_arguments(self):
        prefix,meter=self.prefix();gate=p.PrefixGate(prefix.gate,prefix)
        self.assertFalse(hasattr(gate,'apply_endchain_migration'))
        with self.assertRaises(CandidateStop):gate.cli('migration','up','--local')
        with self.assertRaises(CandidateStop):gate.cli('db','push','--local','--dry-run','--skip-vault')


if __name__=='__main__':unittest.main()
