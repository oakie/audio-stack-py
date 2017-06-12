import unittest
from lnk import bits_to_bytes, bytes_to_bits


class TestLnkLayer(unittest.TestCase):
    def test_bits_to_bytes(self):
        cases = [
            ([], []),
            ([1, 1, 1, 1, 1, 1, 1], []),
            ([1, 1, 1, 1, 1, 1, 1, 1], [0xff]),
            ([1, 1, 1, 1, 1, 1, 1, 1, 1], [0xff]),
            ([0, 0, 0, 0, 0, 0, 0, 0], [0x00]),
            ([0, 0, 0, 0, 0, 0, 0, 1], [0x01]),
            ([1, 0, 0, 0, 0, 0, 0, 0], [0x80]),
            ([1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1], [0x80, 0xff])
        ]
        for bits, expected in cases:
            actual = bits_to_bytes(bits)
            msg = '\nbits: ' + str(bits) + '\nexpected: ' + str(expected) + '\nactual:  ' + str(actual)
            self.assertListEqual(expected, actual, msg)

    def test_bytes_to_bits(self):
        cases = [
            ([], []),
            ([0xff], [1, 1, 1, 1, 1, 1, 1, 1]),
            ([0x00], [0, 0, 0, 0, 0, 0, 0, 0]),
            ([0x01], [0, 0, 0, 0, 0, 0, 0, 1]),
            ([0x80], [1, 0, 0, 0, 0, 0, 0, 0]),
            ([0x80, 0xff], [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1])
        ]
        for bytes, expected in cases:
            actual = bytes_to_bits(bytes)
            msg = '\nbytes: ' + str(bytes) + '\nexpected: ' + str(expected) + '\nactual:  ' + str(actual)
            self.assertListEqual(expected, actual, msg)


if __name__ == '__main__':
    unittest.main()
