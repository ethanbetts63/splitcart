import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

class TestCleanRawDataIga(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_iga.normalize_product_data', side_effect=lambda p: p)
    def test_clean_raw_data_iga_available(self, mock_normalize):
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

    @patch('api.utils.scraper_utils.clean_raw_data_iga.normalize_product_data', side_effect=lambda p: p)
    def test_clean_raw_data_iga_unavailable(self, mock_normalize):
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

if __name__ == '__main__':
    unittest.main()