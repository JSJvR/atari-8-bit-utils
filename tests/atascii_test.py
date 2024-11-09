
import filecmp
import os
import unittest
from atari_8_bit_utils.atascii import to_utf8, to_atascii, files_to_utf8, files_to_atascii, clear_dir

# Tests for ATASCII <-> UTF-8 conversion code
class TestAtasciiConversions(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        
        clear_dir(self.out_path)
        return super().setUp()

    def test_dir_to_utf8(self):
        files_to_utf8(self.atascii_path, self.out_path)

    def test_dir_to_atascii(self):
        files_to_atascii(self.utf8_path, self.out_path)

    def test_atascii_roundtrip(self):        
        in_atascii = self.atascii_path + 'TEST.TXT'
        out_utf8 = self.out_path + 'TEST-UTF8.TXT'
        out_atascii = self.out_path + 'TEST-ATA.TXT'

        to_utf8(in_atascii, out_utf8)
        to_atascii(out_utf8, out_atascii)
        self.assertTrue(filecmp.cmp(in_atascii, out_atascii, shallow=False))

    def test_utf8_roundtrip(self):        
        in_utf8 = self.utf8_path + 'TEST.TXT'
        out_utf8 = self.out_path + 'TEST-UTF8.TXT'
        out_atascii = self.out_path + 'TEST-ATA.TXT'

        to_atascii(in_utf8, out_atascii)
        to_utf8(out_atascii, out_utf8)
        self.assertTrue(filecmp.cmp(in_utf8, out_utf8, shallow=False))

    def __init__(self, methodName = "runTest"):
        data_path = 'testdata/'
        self.out_path = data_path + 'out/'
        self.atascii_path = data_path + 'atascii/'
        self.utf8_path = data_path + 'utf8/'

        super().__init__(methodName)

if __name__ == '__main__':
    unittest.main()