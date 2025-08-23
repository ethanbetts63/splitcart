
import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

class TestCleanRawDataIga(unittest.TestCase):

    # This test fails because clean_raw_data_iga.py has a local import of normalize_product_data
    # inside the function, which prevents the mock patch from working correctly.
    # The import should be at the module level.
    @patch('api.utils.scraper_utils.clean_raw_data_iga.normalize_product_data', side_effect=lambda p: p)
    def test_clean_raw_data_iga(self, mock_normalize):
        raw_product_list = [
            {
                "sku": "31218",
                "barcode": "9315090204483",
                "name": "Australia's Own Organic Coconut Milk Unsweetened",
                "brand": "Australia's Own",
                "description": "Country of Origin: Made in Australia",
                "available": True,
                "priceNumeric": 3.35,
                "wholePrice": 3.35,
                "pricePerUnit": "$3.35/l",
                "priceSource": "regular",
                "sellBy": "Each",
                "unitOfMeasure": {"label": "Litre"},
                "categories": [
                    {"categoryBreadcrumb": "Grocery"},
                    {"categoryBreadcrumb": "Grocery/Drinks/Long Life Milk/Coconut Milk"}
                ],
                "image": {"default": "https://example.com/image.jpg"}
            }
        ]

        cleaned_data = clean_raw_data_iga(
            raw_product_list=raw_product_list,
            company="IGA",
            store_id="1111",
            store_name="Test IGA",
            state="NSW",
            category_slug="coconut-milk",
            page_num=1,
            timestamp=datetime(2025, 8, 23)
        )

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], '31218')
        self.assertEqual(product['barcode'], '9315090204483')
        self.assertEqual(product['name'], "australia's own organic coconut milk unsweetened")
        self.assertEqual(product['brand'], "australia's own")
        self.assertEqual(product['price_current'], 3.35)
        self.assertFalse(product['is_on_special'])
        self.assertEqual(product['package_size'], 'each')
        self.assertEqual(product['country_of_origin'], 'Made in Australia')
        self.assertEqual(product['category_path'], ['Grocery', 'Drinks', 'Long Life Milk', 'Coconut Milk'])
        self.assertEqual(product['image_url_main'], 'https://example.com/image.jpg')
        self.assertEqual(mock_normalize.call_count, 1)

if __name__ == '__main__':
    unittest.main()
