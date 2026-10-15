import unittest
from workday_preservation import preserved_body
class Tests(unittest.TestCase):
    def test_only_new_prefix_and_heading_can_change(self):
        old='# Title\n\n## Current\n\nOld evidence\n'
        new='# Title\n\n## New status\nNew facts\n\n## Historical\n\nOld evidence\n'
        self.assertTrue(preserved_body(old,new,'## Historical'))
        self.assertTrue(preserved_body(old.replace('\n','\r\n'),new,'## Historical'))
        for changed in (new.replace('Old evidence','Rewritten'),new.replace('# Title','# Other'),new+'Extra',new.replace('## Historical','## Historical\n## Historical')):
            self.assertFalse(preserved_body(old,changed,'## Historical'))
if __name__=='__main__':unittest.main()
