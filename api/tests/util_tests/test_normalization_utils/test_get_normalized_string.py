import unittest
from unittest.mock import patch
from api.utils.normalization_utils.get_normalized_string import get_normalized_string
from api.utils.normalization_utils.clean_value import clean_value # For expected output

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

    @patch('api.utils.normalization_utils.get_normalized_string.BRAND_SYNONYMS', {'abbotts': 'Abbott\'s Bakery'})
    def test_get_normalized_string_with_brand_synonym(self):
        product = {'name': 'Wholemeal Bread', 'brand': 'abbott\'s'}
        extracted_sizes = []
        
        # Expected cleaned name (from get_cleaned_name, then clean_value)
        # 'Wholemeal Bread' will be returned by get_cleaned_name, then clean_value will sort it.
        cleaned_name_part = clean_value('Wholemeal Bread') # This will result in 'breadwholemeal'
        
        # Expected canonical brand after clean_value
        final_brand_part = clean_value('Abbott\'s Bakery') 
        
        # Expected normalized string: cleaned_name + cleaned_brand + cleaned_sizes
        expected_normalized_string = cleaned_name_part + final_brand_part + '' # No sizes
        
        self.assertEqual(get_normalized_string(product, extracted_sizes), expected_normalized_string)

if __name__ == '__main__':
    unittest.main()
