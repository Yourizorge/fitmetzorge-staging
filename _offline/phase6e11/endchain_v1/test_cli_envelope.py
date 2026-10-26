import copy,unittest
from cli_envelope import attribution,charged,local,CAP,CHARGE
from test_cli_stat_reader import snap

class Tests(unittest.TestCase):
    def receipt(self):
        return dict(environment='staging',complete=True,protocol_commands=None,commands=[],slot='quota',dry_run=False,
            observer_commands=[{'confirmed':True}]*8,capacity_reserved=CAP,charged_commands=CHARGE,
            attribution=attribution(snap(),snap(10)))
    def test_numeric_delta_never_becomes_session_attribution(self):
        r=self.receipt();self.assertEqual(charged(r),72)
        self.assertIsNone(r['attribution']['cli_confirmed_commands'])
        self.assertIsNone(r['attribution']['background_confirmed_commands'])
        self.assertEqual(r['attribution']['unattributed_calls'],4)
    def test_two_separate_readonly_slots_have_stricter_cap(self):
        for slot in ('pre_auth','final'):
            a=attribution(snap(),snap(34),slot=slot)
            self.assertEqual(a['unattributed_calls'],28)
            with self.assertRaisesRegex(ValueError,'exceeded'):attribution(snap(),snap(35),slot=slot)
            r={**self.receipt(),'slot':slot,'dry_run':True,'capacity_reserved':28,'charged_commands':36,'attribution':a}
            self.assertEqual(charged(r),36)
            with self.assertRaisesRegex(ValueError,'readonly'):charged({**r,'dry_run':False})
            with self.assertRaisesRegex(ValueError,'capacity'):charged({**r,'capacity_reserved':64})
        with self.assertRaisesRegex(ValueError,'slot_invalid'):attribution(snap(),snap(),slot='unregistered')
    def test_exact_boundary_and_excess(self):
        self.assertEqual(attribution(snap(),snap(70))['unattributed_calls'],64)
        with self.assertRaisesRegex(ValueError,'exceeded'):attribution(snap(),snap(71))
    def test_temp_reset_duplicate_tracking_are_fail_closed(self):
        for key,value in [('reset','different'),('track','none'),('dealloc',1)]:
            a=snap(10);a[key]=value
            with self.assertRaises(ValueError):attribution(snap(),a)
        a=snap(10);a['statements'][0]['temp_written']=1
        with self.assertRaisesRegex(ValueError,'temp_writes'):attribution(snap(),a)
        a=snap(10);a['statements']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):attribution(snap(),a)
    def test_local_actual_count_and_reservation_are_separate(self):
        r=local(dict(protocol_commands=14,complete=True,numeric_protocol_coverage=True,
            observer_commands=[{'confirmed':True}]*8))
        self.assertEqual(r['protocol_commands'],14);self.assertEqual(charged(r),72)
        for n in (0,65,None,True):
            with self.assertRaises(ValueError):local({**r,'protocol_commands':n})
    def test_cannot_relabel_template_or_missing_observer_as_hosted_pass(self):
        for key,value in [('protocol_commands',14),('commands',[{'template':True}]),
                          ('observer_commands',[]),('charged_commands',16),('complete',False)]:
            with self.assertRaises(ValueError):charged({**self.receipt(),key:value})

if __name__=='__main__':unittest.main()
