import unittest
from api.utils.normalization_utils.get_extracted_sizes import get_extracted_sizes

class GetExtractedSizesTest(unittest.TestCase):

    def test_extract_sizes_from_name(self):
        product = {'name': 'Test Product 100g', 'brand': 'Test Brand', 'sizes': []}
        self.assertEqual(get_extracted_sizes(product), ['100g'])

    def test_extract_sizes_from_brand(self):
        product = {'name': 'Test Product', 'brand': 'Test Brand 200ml', 'sizes': []}
        self.assertEqual(get_extracted_sizes(product), ['200ml'])

    def test_combine_sizes(self):
        product = {'name': 'Test Product 100g', 'brand': 'Test Brand 200ml', 'sizes': ['300l']}
        self.assertEqual(get_extracted_sizes(product), ['100g', '200ml', '300l'])

    def test_no_sizes(self):
        product = {'name': 'Test Product', 'brand': 'Test Brand', 'sizes': []}
        self.assertEqual(get_extracted_sizes(product), [])

    def test_extract_sizes_from_package_size(self):
        product = {'name': 'Test Product', 'brand': 'Test Brand', 'package_size': 'approx. 500ml'}
        self.assertEqual(get_extracted_sizes(product), ['500ml'])

if __name__ == '__main__':
    unittest.main()
