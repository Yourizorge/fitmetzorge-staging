import io
import pathlib
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import admission_tools as t


class Tests(unittest.TestCase):
    def archive(self, names):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:gz') as a:
            for name, kind in names:
                m=tarfile.TarInfo(name);m.type=kind
                m.size=1 if kind==tarfile.REGTYPE else 0
                if kind==tarfile.SYMTYPE:m.linkname='/outside'
                if kind==tarfile.LNKTYPE:m.linkname='pnpm'
                a.addfile(m,io.BytesIO(b'x') if m.size else None)
        return data.getvalue()

    def test_digest_mismatch_fails_before_extract(self):
        with patch.object(t.urllib.request,'urlopen') as get:
            get.return_value.__enter__.return_value.read.return_value=b'bad'
            with self.assertRaisesRegex(ValueError,'digest'):t.fetch(t.BUN)

    def test_tool_archive_is_regular_and_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            target=pathlib.Path(folder)
            exe=t.extract_pnpm(self.archive([('pnpm',tarfile.REGTYPE)]),target)
            self.assertEqual(exe.read_bytes(),b'x')

    def test_traversal_alias_symlink_and_missing_binary_rejected(self):
        for names in ([('../outside',tarfile.REGTYPE)], [('pnpm',tarfile.SYMTYPE)],
                      [('pnpm',tarfile.REGTYPE),('PNPM',tarfile.REGTYPE)], [('other',tarfile.REGTYPE)]):
            with self.subTest(names=names),tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):t.extract_pnpm(self.archive(names),pathlib.Path(folder))

    def test_internal_hardlink_becomes_a_regular_independent_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target=pathlib.Path(folder)
            t.extract_pnpm(self.archive([('pnpm',tarfile.REGTYPE),('duplicate',tarfile.LNKTYPE)]),target)
            self.assertEqual((target/'duplicate').read_bytes(),b'x')
            self.assertFalse((target/'duplicate').is_symlink())

    def test_materialized_hardlinks_count_towards_size_before_extraction(self):
        original=tarfile.TarInfo('pnpm');original.size=60000000
        duplicate=tarfile.TarInfo('duplicate');duplicate.type=tarfile.LNKTYPE;duplicate.linkname='pnpm'
        with patch.object(t.tarfile,'open') as opened:
            archive=opened.return_value.__enter__.return_value
            archive.getmembers.return_value=[original,duplicate]
            with self.assertRaisesRegex(ValueError,'archive_size'):
                t.extract_pnpm(b'',pathlib.Path('unused'))
            archive.extractall.assert_not_called()


if __name__=='__main__':unittest.main()
