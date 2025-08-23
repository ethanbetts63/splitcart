
import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi

class TestCleanRawDataAldi(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_aldi.normalize_product_data', side_effect=lambda p: p)
    def test_clean_raw_data_aldi(self, mock_normalize):
        raw_product_list = [
            {
                "sku": "000000000000200998",
                "name": "Chocolate Chip Brioche Milk Rolls 8 Pack 280g",
                "brandName": "BON APPETIT",
                "urlSlugText": "bon-appetit-chocolate-chip-brioche-milk-rolls-8-pack-280g",
                "notForSale": False,
                "quantityMax": 99,
                "sellingSize": "280 g",
                "price": {
                    "amount": 469,
                    "comparisonDisplay": "$1.68 per 100 g",
                },
                "categories": [
                    {"name": "Bakery"},
                    {"name": "Speciality Breads & Rolls"}
                ],
                "assets": [
                    {"url": "https://example.com/image1.jpg"},
                    {"url": "https://example.com/image2.jpg"}
                ],
                "badges": [{"badgeText": "New"}]
            }
        ]

        cleaned_data = clean_raw_data_aldi(
            raw_product_list=raw_product_list,
            company="Aldi",
            store_id="9876",
            store_name="Test Aldi",
            state="QLD",
            timestamp=datetime(2025, 8, 23)
        )

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], '000000000000200998')
        self.assertEqual(product['name'], 'chocolate chip brioche milk rolls 8 pack 280g')
        self.assertEqual(product['brand'], 'bon appetit')
        self.assertEqual(product['price_current'], 4.69)
        self.assertTrue(product['is_available'])
        self.assertEqual(product['package_size'], '280 g')
        self.assertEqual(product['category_path'], ['Bakery', 'Speciality Breads & Rolls'])
        self.assertEqual(product['image_url_main'], 'https://example.com/image1.jpg')
        self.assertEqual(len(product['image_urls_all']), 2)
        self.assertIn('New', product['tags'])
        self.assertEqual(mock_normalize.call_count, 1)

if __name__ == '__main__':
    unittest.main()
