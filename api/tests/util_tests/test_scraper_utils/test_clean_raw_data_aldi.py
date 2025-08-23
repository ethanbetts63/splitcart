import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi

class TestCleanRawDataAldi(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_aldi.get_normalized_string', return_value='normalized_string')
    @patch('api.utils.scraper_utils.clean_raw_data_aldi.get_extracted_sizes', return_value=['100g'])
    def test_clean_raw_data_aldi(self, mock_get_sizes, mock_get_string):
        raw_product_list = [
            {
                "sku": "12345",
                "name": "Aldi Product 100g",
                "brandName": "Aldi Brand",
                "urlSlugText": "aldi-product-100g",
                "price": {"amount": 150, "comparison": 150, "comparisonDisplay": "$1.50 / 100g"},
                "categories": [{"name": "Dairy"}],
                "assets": [{"url": "image.jpg"}],
                "badges": [{"badgeText": "Special"}],
                "notForSale": False,
                "quantityMax": 10,
                "sellingSize": "100g"
            }
        ]

        cleaned_data = clean_raw_data_aldi(
            raw_product_list=raw_product_list,
            company="Aldi",
            store_name="Test Aldi",
            store_id="aldi123",
            state="NSW",
            timestamp=datetime(2025, 8, 23)
        )

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], '12345')
        self.assertEqual(product['name'], 'Aldi Product 100g')
        self.assertEqual(product['brand'], 'Aldi Brand')
        self.assertEqual(product['price_current'], 1.50)
        self.assertEqual(product['unit_of_measure'], '100g')
        self.assertEqual(product['category_path'], ['Dairy'])
        self.assertIn('Special', product['tags'])
        self.assertEqual(mock_get_sizes.call_count, 1)
        self.assertEqual(mock_get_string.call_count, 1)

if __name__ == '__main__':
    unittest.main()