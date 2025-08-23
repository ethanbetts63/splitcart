import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

class TestCleanRawDataIga(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_iga.get_normalized_string', return_value='normalized_string')
    @patch('api.utils.scraper_utils.clean_raw_data_iga.get_extracted_sizes', return_value=['1l'])
    def test_clean_raw_data_iga_available(self, mock_get_sizes, mock_get_string):
        raw_product_list = [
            {
                "sku": "31218",
                "barcode": "9315090204483",
                "name": "Australia's Own Organic Coconut Milk Unsweetened",
                "brand": "Australia's Own",
                "description": "Some description",
                "available": True,
                "priceNumeric": 3.35,
                "wholePrice": 3.35,
                "pricePerUnit": "$3.35/l",
                "priceSource": "regular",
                "sellBy": "Each",
                "unitOfMeasure": {"label": "Litre"},
                "categories": [
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
            timestamp=datetime(2025, 8, 23)
        )

        product = cleaned_data['products'][0]
        self.assertTrue(product['is_available'])
        self.assertEqual(mock_get_sizes.call_count, 1)
        self.assertEqual(mock_get_string.call_count, 1)

    @patch('api.utils.scraper_utils.clean_raw_data_iga.get_normalized_string', return_value='normalized_string')
    @patch('api.utils.scraper_utils.clean_raw_data_iga.get_extracted_sizes', return_value=[])
    def test_clean_raw_data_iga_unavailable(self, mock_get_sizes, mock_get_string):
        raw_product_list = [
            {
                "sku": "31218",
                "name": "Some Product",
                "brand": "Some Brand",
                # 'available' key is missing
            }
        ]

        cleaned_data = clean_raw_data_iga(
            raw_product_list=raw_product_list,
            company="IGA",
            store_id="1111",
            store_name="Test IGA",
            state="NSW",
            timestamp=datetime(2025, 8, 23)
        )

        product = cleaned_data['products'][0]
        self.assertIsNone(product['is_available'])
        self.assertEqual(mock_get_sizes.call_count, 1)
        self.assertEqual(mock_get_string.call_count, 1)

if __name__ == '__main__':
    unittest.main()
