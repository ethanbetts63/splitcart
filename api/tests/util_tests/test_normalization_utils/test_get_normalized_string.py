import unittest
from api.utils.normalization_utils.get_normalized_string import get_normalized_string

class GetNormalizedStringTest(unittest.TestCase):

    def test_get_normalized_string(self):
        product = {'name': 'Test Product', 'brand': 'Test Brand'}
        extracted_sizes = ['100g']
        self.assertEqual(get_normalized_string(product, extracted_sizes), 'producttestbrandtest100g')

    def test_get_normalized_string_no_sizes(self):
        product = {'name': 'Test Product', 'brand': 'Test Brand'}
        extracted_sizes = []
        self.assertEqual(get_normalized_string(product, extracted_sizes), 'producttestbrandtest')

    def test_get_normalized_string_no_brand(self):
        product = {'name': 'Test Product', 'brand': ''}
        extracted_sizes = ['100g']
        self.assertEqual(get_normalized_string(product, extracted_sizes), 'producttest100g')

if __name__ == '__main__':
    unittest.main()
