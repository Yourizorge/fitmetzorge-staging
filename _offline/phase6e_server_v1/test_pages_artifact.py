import hashlib,io,tarfile,unittest
from pages_artifact import inspect
def bundle(names):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w') as archive:
        for name,raw in names:
            item=tarfile.TarInfo(name);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
    return output.getvalue()
class Tests(unittest.TestCase):
    def test_exact_runtime_and_no_private_roots(self):
        expected={'app.js':hashlib.sha256(b'fixed').hexdigest()}
        self.assertEqual(inspect(bundle([('./app.js',b'fixed')]),expected)['runtime_assets'],1)
        for items in [[('app.js',b'wrong')],[('app.js',b'fixed'),('_offline/test.js',b'x')],[('app.js',b'fixed'),('supabase/test.sql',b'x')],[('../app.js',b'fixed')],[('app.js',b'fixed'),('app.js',b'fixed')]]:
            with self.assertRaises(ValueError):inspect(bundle(items),expected)
        with self.assertRaises(ValueError):inspect(bundle([]),expected)
if __name__=='__main__':unittest.main()
