
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
        in_atascii = self.atascii_path + 'COMPLETE.TXT'
        out_utf8 = self.out_path + 'COMPLETE-UTF8.TXT'
        out_atascii = self.out_path + 'COMPLETE-ATA.TXT'

        to_utf8(in_atascii, out_utf8)
        to_atascii(out_utf8, out_atascii)
        self.assertTrue(filecmp.cmp(in_atascii, out_atascii, shallow=False))

    def test_utf8_roundtrip(self):
        in_utf8 = self.utf8_path + 'TEST.TXT'
        out_utf8 = self.out_path + 'TEST-UTF8.TXT'
        out_atascii = self.out_path + 'TEST-ATA.TXT'

        to_atascii(in_utf8, out_atascii)
        to_utf8(out_atascii, out_utf8)
        self.assertFilesMatch(out_utf8, out_utf8)

    def __init__(self, methodName="runTest"):
        data_path = 'testdata/'
        self.out_path = data_path + 'out/'
        self.atascii_path = data_path + 'atascii/'
        self.utf8_path = data_path + 'utf8/'

        super().__init__(methodName)

    # Compare files line by line so that we can gracefully handle different 
    # line endings
    def assertFilesMatch(self, file1, file2):
        l1 = l2 = True
        #self.fail(f'{file1}, {file2}')
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            while l1 and l2:
                l1 = f1.readline()
                l2 = f2.readline()
                if l1 != l2:
                    self.fail(f'Lines don\'t match:\n\t{l1}\n\t{l2}')

if __name__ == '__main__':
    unittest.main()
