import hashlib
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from repair_zip import repair

class ZipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.src=self.root/'input.zip'
    def tearDown(self):self.temp.cleanup()
    def write(self,items):
        with zipfile.ZipFile(self.src,'w') as z:
            for name,value in items:z.writestr(name,value)
    def test_unicode_metadata_and_content(self):
        self.write([('中文/示例.txt',b'keep bytes'),('__MACOSX/._x',b'junk'),('.DS_Store',b'junk')])
        old=self.src.read_bytes();r=repair(self.src)
        self.assertEqual(self.src.read_bytes(),old);self.assertEqual(r['sha256_verified_files'],1)
        with zipfile.ZipFile(r['output']) as z:
            self.assertEqual(z.namelist(),['中文/示例.txt']);self.assertEqual(z.read(z.namelist()[0]),b'keep bytes')
            self.assertTrue(z.infolist()[0].flag_bits&0x800)
    def test_missing_utf8_flag(self):
        self.write([('中文.txt',b'payload')]);raw=bytearray(self.src.read_bytes())
        for signature,offset in ((b'PK\x03\x04',6),(b'PK\x01\x02',8)):
            pos=raw.index(signature);flags=struct.unpack_from('<H',raw,pos+offset)[0]
            struct.pack_into('<H',raw,pos+offset,flags&~0x800)
        self.src.write_bytes(raw);r=repair(self.src)
        with zipfile.ZipFile(r['output']) as z:self.assertEqual(z.namelist(),['中文.txt'])
    def test_no_overwrite(self):
        self.write([('a.txt',b'a')]);output=self.root/'out.zip';output.write_bytes(b'original')
        with self.assertRaises(FileExistsError):repair(self.src,output)
        self.assertEqual(output.read_bytes(),b'original')
    def test_path_traversal(self):
        self.write([('../secret.txt',b'x')])
        with self.assertRaises(ValueError):repair(self.src)
    def test_duplicate_case_names(self):
        self.write([('A.txt',b'a'),('a.txt',b'b')])
        with self.assertRaises(ValueError):repair(self.src)
    def test_corrupt_archive_leaves_no_output(self):
        self.src.write_bytes(b'not a zip')
        with self.assertRaises(zipfile.BadZipFile):repair(self.src)
        self.assertFalse(self.src.with_name('input_Windows_UTF8.zip').exists())
    def test_same_path_rejected(self):
        self.write([('a',b'x')])
        with self.assertRaises(FileExistsError):repair(self.src,self.src)
    def test_symlink_member_rejected(self):
        with zipfile.ZipFile(self.src,'w') as z:
            info=zipfile.ZipInfo('link');info.external_attr=0o120777<<16;z.writestr(info,'target')
        with self.assertRaises(ValueError):repair(self.src)

if __name__=='__main__':unittest.main()
