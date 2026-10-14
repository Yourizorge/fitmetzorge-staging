import unittest
from datetime import datetime,timedelta,timezone
import outbox
class Tests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,14,tzinfo=timezone.utc);self.expires=self.now+timedelta(minutes=10)
        self.state={'consent':True,'sourceHash':'a'*64,'notices':[{'id':'b'*64,'status':'current'}],'review':None}
    def changes(self,rows,action='record',selected=None,now=None):return outbox.changes(rows,self.state,action,now or self.now,self.expires,'request',selected)
    def row(self):return self.changes([])[0]
    def test_dedupe_seen_and_source_correction(self):
        row=self.row();self.assertEqual(self.changes([row]),[])
        update=self.changes([row],'notice_seen','b'*64)[0]
        self.assertEqual(update['status'],'seen');self.assertEqual(len(update['history']),2)
        self.state['notices'][0]['status']='superseded'
        self.assertEqual(self.changes([row])[0]['status'],'superseded')
    def test_terminal_states_and_expiry_never_reopen(self):
        row=self.row()
        for action,status in [('reject','declined'),('block','declined'),('apply','applied')]:
            updated={**row,**self.changes([row],action)[0]};self.assertEqual(updated['status'],status)
            self.assertEqual(self.changes([updated]),[])
        self.assertEqual(self.changes([row],now=self.expires)[0]['status'],'expired')
        self.assertEqual(outbox.visible(row,self.expires)['status'],'expired')
    def test_withdrawal_no_new_events_and_exact_expiry(self):
        row=self.row();self.state['consent']=False
        self.assertEqual(self.changes([]),[]);self.assertEqual(self.changes([row])[0]['status'],'withdrawn')
        self.state['consent']=True
        self.assertEqual(self.changes([],now=self.expires),[])
        with self.assertRaises(ValueError):self.changes([row],'notice_seen','b'*64,self.expires)
    def test_approval_does_not_duplicate_proposal_event(self):
        self.state['review']={'source':'a'*64,'kind':'checkin','target':{'at':'08:00'},'base':1,'member':False}
        rows=self.changes([]);self.state['review']['member']=True
        self.assertEqual(self.changes(rows,'confirm'),[])
        self.state['review']['target']['at']='20:00'
        delta=self.changes(rows,'edit');self.assertEqual([r['operation'] for r in delta],['UPDATE','INSERT'])
if __name__=='__main__':unittest.main()
