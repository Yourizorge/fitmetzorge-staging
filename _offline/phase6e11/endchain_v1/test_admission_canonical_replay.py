"""Original semantics negative cases, not simulated PG or admission evidence."""
import copy
import json
import unittest

import admission_canonical_replay as replay
import cli_stat_reader as stat


def numeric_receipt():
    before = dict(reset='epoch',dealloc=0,track='all',track_utility='on',statements=[])
    after = copy.deepcopy(before)
    after['statements'] = [dict(queryid='1',calls=6,since='epoch',temp_written=0,wal='0')]
    statements = ('BEGIN TRANSACTION READ ONLY',
        "select current_setting('transaction_read_only')='on' readonly",stat.SQL.strip(),'ROLLBACK')
    trace = [dict(sha256=replay.sha(s.encode()),kind='numeric_observer',protocol_commands=1,
                  confirmed=True) for s in statements]*2
    return dict(numeric_before=before,numeric_after=after,terminal=dict(sql_dispatches=2),
        numeric_coverage=stat.compare(before,after,2,between=3),observer_trace=trace,
        observer_commands=8,after_measurement_complete=True)


class NumericTests(unittest.TestCase):
    def test_recomputes_known_correlation_not_complete_bound(self):
        value = replay.numeric(numeric_receipt(),stat)
        self.assertEqual(value['numeric_calls_minus_reader'],2)
        self.assertNotIn('full_chain_admission',value)

    def test_duplicate_queryid_is_not_dictionary_overwrite(self):
        value = numeric_receipt()
        value['numeric_after']['statements'] *= 2
        with self.assertRaisesRegex(ValueError,'sample_queryid'):
            replay.numeric(value,stat)

    def test_bool_counter_and_noncanonical_queryid_rejected(self):
        for key,value in (('calls',True),('queryid','01'),('wal','-1')):
            receipt=numeric_receipt();receipt['numeric_after']['statements'][0][key]=value
            with self.assertRaises(ValueError):replay.numeric(receipt,stat)

    def test_rehashed_summary_cannot_substitute_samples(self):
        value=numeric_receipt();value['numeric_after']['statements'][0]['calls']=5
        with self.assertRaisesRegex(ValueError,'numeric_coverage'):replay.numeric(value,stat)

    def test_reset_missing_observer_or_incomplete_after_denied(self):
        for kind in ('reset','observer','incomplete'):
            value=numeric_receipt()
            if kind=='reset':value['numeric_after']['reset']='new'
            if kind=='observer':value['observer_trace'].pop()
            if kind=='incomplete':value['after_measurement_complete']=False
            with self.assertRaises(ValueError):replay.numeric(value,stat)

    def test_zero_calls_with_wal_change_cannot_disappear(self):
        value=numeric_receipt()
        value['numeric_after']['statements'].append(
            dict(queryid='2',calls=0,since='epoch',temp_written=0,wal='4'))
        with self.assertRaisesRegex(ValueError,'unattributed_counter_change'):replay.numeric(value,stat)


class LedgerTests(unittest.TestCase):
    def rows(self):
        return [dict(event='preregister'),dict(event='connect_attempt',id=1),
            dict(event='dispatch',id=1,protocol='simple',outcome='unknown_consumed'),
            dict(event='frontend_frame',type='Q',sql_ids=[1]),
            dict(event='outcome',id=1,outcome='command_complete'),dict(event='terminal')]

    def raw(self,rows):
        return b''.join(json.dumps(dict(row,sequence=i)).encode()+b'\n' for i,row in enumerate(rows,1))

    def test_attempt_frame_then_confirmation(self):
        self.assertEqual(len(replay.ledger_shape(self.raw(self.rows()))),6)

    def test_unknown_is_consumed_never_silent_zero(self):
        rows=self.rows();rows.pop(4)
        with self.assertRaisesRegex(ValueError,'unconfirmed_dispatch_consumed'):
            replay.ledger_shape(self.raw(rows))

    def test_confirmation_before_frame_wrong_protocol_duplicate_frame(self):
        for kind in ('early','wrong','duplicate'):
            rows=self.rows()
            if kind=='early':rows[3],rows[4]=rows[4],rows[3]
            if kind=='wrong':rows[3]['type']='E'
            if kind=='duplicate':rows.insert(4,dict(rows[3]))
            with self.assertRaises(ValueError):replay.ledger_shape(self.raw(rows))

    def test_duplicate_json_keys_denied(self):
        with self.assertRaises(ValueError):
            replay.ledger_shape(b'{"event":"terminal","event":"preregister","sequence":1}\n')


if __name__=='__main__':unittest.main()
