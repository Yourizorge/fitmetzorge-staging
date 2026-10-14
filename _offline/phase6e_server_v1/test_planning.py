import unittest
from planning import occurrence
class Tests(unittest.TestCase):
    def test_explicit_timezone_winter_summer(self):
        self.assertEqual(occurrence('2026-01-05','08:00','Europe/Amsterdam',['08:00'],2)['utc'],'2026-01-05T07:00:00+00:00')
        self.assertEqual(occurrence('2026-07-05','08:00','Europe/Amsterdam',['08:00'],2)['utc'],'2026-07-05T06:00:00+00:00')
    def test_gap_and_overlap_need_explicit_choice(self):
        with self.assertRaisesRegex(ValueError,'nonexistent'):occurrence('2026-03-29','02:30','Europe/Amsterdam',['02:30'],1)
        with self.assertRaisesRegex(ValueError,'ambiguous'):occurrence('2026-10-25','02:30','Europe/Amsterdam',['02:30'],1)
        a=occurrence('2026-10-25','02:30','Europe/Amsterdam',['02:30'],1,fold=0)
        b=occurrence('2026-10-25','02:30','Europe/Amsterdam',['02:30'],1,fold=1)
        self.assertNotEqual(a['utc'],b['utc'])
    def test_missing_rules_and_bad_zone_denied(self):
        for args in [('2026-01-05','08:00','Unknown/Zone',['08:00'],1),('2026-01-05','08:00','UTC',[],1),('2026-01-05','08:00','UTC',['08:00'],0)]:
            with self.assertRaises(ValueError):occurrence(*args)
if __name__=='__main__':unittest.main()
