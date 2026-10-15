import unittest
from archive_reserved import safe

class Tests(unittest.TestCase):
    def test_numeric_and_hashed_metadata_allowed(self):safe(b'{"calls":1,"sha":"abc"}')
    def test_secret_shape_and_oversize_rejected(self):
        for raw in [b'{"v":"sbp_'+b'x'*32+b'"}',b'{"v":"eyJ'+b'x'*20+b'.'+b'y'*20+b'.z"}',b' '*2000001]:
            with self.assertRaises(ValueError):safe(raw)

if __name__=='__main__':unittest.main()
