import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles

class TestCleanRawDataColes(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_coles.get_normalized_string', return_value='normalized_string')
    @patch('api.utils.scraper_utils.clean_raw_data_coles.get_extracted_sizes', return_value=['approx. 300g'])
    def test_clean_raw_data_coles(self, mock_get_sizes, mock_get_string):
        raw_product_list = [
            {
                "_type": "PRODUCT",
                "id": 3942620,
                "name": "Graze Lamb Extra Trim Cutlets",
                "brand": "Coles",
                "description": "COLES GRAZE LAMB EXTRA TRIM CUTLETS 7 X 5",
                "size": "approx. 300g",
                "availability": True,
                "pricing": {
                    "now": 12.00,
                    "was": 14.10,
                    "saveAmount": 2.10,
                    "promotionType": "SPECIAL",
                    "onlineSpecial": True,
                    "unit": {"price": 40.00, "ofMeasureUnits": "kg"},
                    "comparable": "$40.00 per 1kg"
                },
                "onlineHeirs": [{
                    "subCategory": "Meat & Seafood",
                    "category": "Lamb",
                    "aisle": "Graze Grass-Fed Lamb"
                }],
                "restrictions": {"retailLimit": 20},
                "imageUris": [{"uri": "/3/3942620.jpg"}]
            },
            {
                "_type": "SINGLE_TILE" # This should be skipped
            }
        ]

        cleaned_data = clean_raw_data_coles(
            raw_product_list=raw_product_list,
            company="Coles",
            store_id="1234",
            store_name="Test Store",
            state="NSW",
            timestamp=datetime(2025, 8, 23)
        )

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['name'], 'graze lamb extra trim cutlets')
        self.assertEqual(product['brand'], 'coles')
        self.assertEqual(product['price_current'], 12.00)
        self.assertEqual(product['price_was'], 14.10)
        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['package_size'], 'approx. 300g')
        self.assertEqual(product['category_path'], ['Meat & Seafood', 'Lamb', 'Graze Grass-Fed Lamb'])
        self.assertIn('special', product['tags'])
        self.assertEqual(mock_get_sizes.call_count, 1)
        self.assertEqual(mock_get_string.call_count, 1)

if __name__ == '__main__':
    unittest.main()