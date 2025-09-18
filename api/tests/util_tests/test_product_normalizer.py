from django.test import TestCase
from api.utils.product_normalizer import ProductNormalizer

class ProductNormalizerTests(TestCase):

    def test_get_fully_normalized_name(self):
        """Test the get_fully_normalized_name method with various inputs."""
        
        # --- Test Case 1: Simple cleaning with punctuation and mixed case ---
        product_data_1 = {'name': '  Red APPLE!! '}
        normalizer_1 = ProductNormalizer(product_data_1)
        # The _get_cleaned_name method will strip leading/trailing spaces.
        # get_fully_normalized_name should then lowercase and remove punctuation.
        self.assertEqual(normalizer_1.get_fully_normalized_name(), 'red apple')

        # --- Test Case 2: Stripping brand and size information ---
        # The normalizer's internal _get_cleaned_name method should remove brand and size first.
        brand_cache = {
            'kelloggs': {
                'name': 'Kelloggs',
                'name_variations': []
            }
        }
        product_data_2 = {'name': 'Kelloggs Corn Flakes 500g', 'brand': 'Kelloggs'}
        normalizer_2 = ProductNormalizer(product_data_2, brand_cache=brand_cache)
        # After 'Kelloggs' and '500g' are stripped, "Corn Flakes" remains.
        self.assertEqual(normalizer_2.get_fully_normalized_name(), 'corn flakes')

        # --- Test Case 3: Unicode characters and extra spaces ---
        product_data_3 = {'name': 'Crème  Brûlée (dessert)'}
        normalizer_3 = ProductNormalizer(product_data_3)
        # Should handle unicode, remove parentheses, and collapse spaces.
        self.assertEqual(normalizer_3.get_fully_normalized_name(), 'creme brulee dessert')

        # --- Test Case 4: Empty and whitespace-only names ---
        product_data_4 = {'name': '   '}
        normalizer_4 = ProductNormalizer(product_data_4)
        self.assertEqual(normalizer_4.get_fully_normalized_name(), '')

        product_data_5 = {'name': ''}
        normalizer_5 = ProductNormalizer(product_data_5)
        self.assertEqual(normalizer_5.get_fully_normalized_name(), '')