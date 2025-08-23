
import unittest
from api.utils.normalization_utils.extract_sizes import extract_sizes

class TestExtractSizes(unittest.TestCase):

    def test_simple_size(self):
        self.assertEqual(extract_sizes("product 500g"), ["500g"])

    def test_size_with_space(self):
        self.assertEqual(extract_sizes("product 1 l"), ["1 l"])

    def test_each_variations(self):
        self.assertCountEqual(extract_sizes("1 each product"), ["1 each"])
        self.assertCountEqual(extract_sizes("1each product"), ["1each"])
        self.assertCountEqual(extract_sizes("product each"), ["each"])

    def test_multipack(self):
        self.assertCountEqual(extract_sizes("product 4x250ml"), ["4x250ml"])

    def test_no_size(self):
        self.assertEqual(extract_sizes("product without size"), [])

    def test_decimal_size(self):
        self.assertEqual(extract_sizes("product 1.5kg"), ["1.5kg"])

if __name__ == '__main__':
    unittest.main()
