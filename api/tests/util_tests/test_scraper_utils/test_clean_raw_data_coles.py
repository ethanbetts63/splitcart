from django.test import TestCase
from datetime import datetime
from unittest.mock import patch, MagicMock
from api.utils.scraper_utils.clean_raw_data_coles import _create_coles_url_slug, clean_raw_data_coles

class CleanRawDataColesTest(TestCase):
    def test_create_coles_url_slug(self):
        self.assertEqual(_create_coles_url_slug("Coles Brand Milk", "2L"), "coles-brand-milk")
        self.assertEqual(_create_coles_url_slug("Coles Brand Milk 2L", "2L"), "coles-brand-milk")
        self.assertEqual(_create_coles_url_slug("Product with Special Chars!@#", "100g"), "product-with-special-chars")
        self.assertEqual(_create_coles_url_slug("", "100g"), "")
        self.assertEqual(_create_coles_url_slug("Product Name", ""), "")

    @patch('api.utils.scraper_utils.clean_raw_data_coles._create_coles_url_slug')
    def test_clean_raw_data_coles(self, mock_create_coles_url_slug):
        mock_create_coles_url_slug.return_value = "mock-slug"

        raw_product_list = [
            {
                "_type": "PRODUCT",
                "id": "123",
                "name": "Test Product",
                "size": "100g",
                "pricing": {
                    "now": 1.50,
                    "was": 2.00,
                    "promotionType": "SPECIAL",
                    "saveAmount": 0.50,
                    "unit": {"price": 1.50, "ofMeasureUnits": "100g", "comparable": "$1.50 per 100g"},
                    "onlineSpecial": True # Added this line
                },
                "onlineHeirs": [{"subCategory": "Dairy", "category": "Milk", "aisle": "Dairy & Chilled"}],
                "restrictions": {"retailLimit": 5},
                "imageUris": [{"uri": "/some/image.jpg"}],
                "availability": True
            },
            # Invalid product
            {"_type": "INVALID"}
        ]
        company = "Coles"
        store_id = "coles123"
        store_name = "Coles City"
        state = "NSW"
        category = "milk"
        page_num = 1
        timestamp = datetime.now()

        cleaned_data = clean_raw_data_coles(raw_product_list, company, store_id, store_name, state, category, page_num, timestamp)

        self.assertIn('metadata', cleaned_data)
        self.assertIn('products', cleaned_data)
        self.assertEqual(cleaned_data['metadata']['company'], company)
        self.assertEqual(cleaned_data['metadata']['store_id'], store_id)
        self.assertEqual(len(cleaned_data['products']), 1)

        cleaned_product = cleaned_data['products'][0]
        self.assertEqual(cleaned_product['product_id_store'], "123")
        self.assertEqual(cleaned_product['name'], "Test Product")
        self.assertEqual(cleaned_product['price_current'], 1.50)
        self.assertEqual(cleaned_product['price_was'], 2.00)
        self.assertTrue(cleaned_product['is_on_special'])
        self.assertEqual(cleaned_product['promotion_type'], "SPECIAL")
        self.assertEqual(cleaned_product['price_save_amount'], 0.50)
        self.assertEqual(cleaned_product['price_unit'], 1.50)
        self.assertEqual(cleaned_product['unit_of_measure'], "100g")
        self.assertEqual(cleaned_product['unit_price_string'], "$1.50 per 100g")
        self.assertTrue(cleaned_product['is_available'])
        self.assertEqual(cleaned_product['purchase_limit'], 5)
        self.assertEqual(cleaned_product['package_size'], "100g")
        self.assertEqual(cleaned_product['category_path'], ["Dairy", "Milk", "Dairy & Chilled"])
        self.assertEqual(cleaned_product['tags'], ["special"])
        self.assertEqual(cleaned_product['url'], f"https://www.coles.com.au/product/mock-slug-123")
        self.assertEqual(cleaned_product['image_url_main'], "https://www.coles.com.au/some/image.jpg")
        self.assertEqual(cleaned_product['image_urls_all'], ["https://www.coles.com.au/some/image.jpg"])

        mock_create_coles_url_slug.assert_called_once_with("Test Product", "100g")

    def test_clean_raw_data_coles_empty_list(self):
        cleaned_data = clean_raw_data_coles([], "Coles", "id", "name", "state", "cat", 1, datetime.now())
        self.assertEqual(len(cleaned_data['products']), 0)

    def test_clean_raw_data_coles_no_metadata(self):
        raw_product_list = [{"_type": "PRODUCT", "id": "123"}]
        cleaned_data = clean_raw_data_coles(raw_product_list, "Coles", "id", "name", "state", "cat", 1, datetime.now())
        self.assertEqual(len(cleaned_data['products']), 1) # Still processes products even if metadata is minimal