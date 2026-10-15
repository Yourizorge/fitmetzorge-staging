import copy, unittest
from selected_accounting import register

class Tests(unittest.TestCase):
    def row(self,n=1):return dict(call_id='synthetic',ordinal=n,phase='completed',confirmed=True,operation='read')
    def test_actual_count_by_operation(self):self.assertEqual(register([self.row(),self.row(2)],2),{'read':2})
    def test_duplicate_not_double_counted(self):
        with self.assertRaises(ValueError):register([self.row(),self.row()],2)
    def test_missing_terminal_denied(self):
        with self.assertRaises(ValueError):register([self.row()],2)
    def test_attempt_not_confirmation(self):
        row=self.row();row['confirmed']=False
        with self.assertRaises(ValueError):register([row],1)
    def test_different_session_same_ordinal(self):
        row=self.row();row['call_id']='other'
        self.assertEqual(register([self.row(),row],2),{'read':2})

if __name__=='__main__':unittest.main()
