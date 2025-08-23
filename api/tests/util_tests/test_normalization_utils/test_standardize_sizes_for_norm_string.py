
import unittest
from api.utils.normalization_utils.standardize_sizes_for_norm_string import standardize_sizes_for_norm_string

class TestStandardizeSizes(unittest.TestCase):

    def test_each_variations(self):
        self.assertEqual(standardize_sizes_for_norm_string(["1 each"]), ["1ea"])
        self.assertEqual(standardize_sizes_for_norm_string(["1each"]), ["1ea"])
        self.assertEqual(standardize_sizes_for_norm_string(["each"]), ["1ea"])

    def test_pack_variations(self):
        self.assertEqual(standardize_sizes_for_norm_string(["4 pack"]), ["4pk"])
        self.assertEqual(standardize_sizes_for_norm_string(["6pk"]), ["6pk"])
        self.assertEqual(standardize_sizes_for_norm_string(["pack"]), ["1pk"])

    def test_standard_units(self):
        self.assertEqual(standardize_sizes_for_norm_string(["500g"]), ["500g"])
        self.assertEqual(standardize_sizes_for_norm_string(["1 l"]), ["1l"])
        self.assertEqual(standardize_sizes_for_norm_string(["1.5kg"]), ["1.5kg"])

    def test_no_unit(self):
        self.assertEqual(standardize_sizes_for_norm_string(["no size here"]), ["nosizehere"])

    def test_mixed_list(self):
        sizes = ["1 each", "500g", "pack"]
        expected = ["1ea", "1pk", "500g"]
        self.assertCountEqual(standardize_sizes_for_norm_string(sizes), expected)

if __name__ == '__main__':
    unittest.main()
