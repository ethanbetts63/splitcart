import json
from django.test import TestCase
from datetime import datetime
from api.utils.scraper_utils.DataCleanerWoolworths import DataCleanerWoolworths
from api.utils.scraper_utils.DataCleanerColes import DataCleanerColes

class TestDataCleanerWoolworths(TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.base_raw_product = {
            "Stockcode": 12345,
            "Name": "Test Product",
            "Brand": "Test Brand",
            "Barcode": "9300633489801",
            "Description": "A great test product.",
            "PackageSize": "500g",
            "LargeImageFile": "image.jpg",
            "UrlFriendlyName": "test-product",
            "AdditionalAttributes": {
                "piesdepartmentnamesjson": '["Bakery", "Bread"]'
            },
            "Price": 5.00,
            "WasPrice": 0.0, # Not on special
            "CupString": "$1.00 / 100G",
            "InstoreCupPrice": 1.0,
            "CupMeasure": "100G",
            "Rating": {
                "Average": 4.5,
                "ReviewCount": 10
            }
        }

    def test_standard_product_cleaning(self):
        """Test basic cleaning and mapping of a standard product."""
        cleaner = DataCleanerWoolworths(
            raw_product_list=[self.base_raw_product],
            company="woolworths",
            store_name="Test Store",
            store_id="1234",
            state="NSW",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], 12345)
        self.assertEqual(product['name'], "Test Product")
        self.assertEqual(product['brand'], "Test Brand")
        self.assertEqual(product['size'], "500g")
        self.assertEqual(product['url'], "https://www.woolworths.com.au/shop/productdetails/12345/test-product")
        self.assertEqual(product['category_path'], ["Bakery", "Bread"])
        self.assertEqual(product['average_user_rating'], 4.5)
        self.assertFalse(product['is_on_special'])

    def test_special_price_calculation(self):
        """Test that special prices are calculated correctly."""
        special_product = self.base_raw_product.copy()
        special_product["Price"] = 4.00
        special_product["WasPrice"] = 5.00

        cleaner = DataCleanerWoolworths([special_product], "woolworths", "s", "s", "s", self.timestamp)
        product = cleaner.clean_data()['products'][0]

        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['price_current'], 4.00)
        self.assertEqual(product['price_was'], 5.00)
        self.assertAlmostEqual(product['price_save_amount'], 1.00)

    def test_post_processing_normalization(self):
        """Test that the post-processing steps like normalization are run."""
        cleaner = DataCleanerWoolworths([self.base_raw_product], "woolworths", "s", "s", "s", self.timestamp)
        product = cleaner.clean_data()['products'][0]

        self.assertIn('sizes', product)
        self.assertIn('normalized_name_brand_size', product)
        self.assertIsNotNone(product['normalized_name_brand_size'])
        self.assertEqual(product['barcode'], "9300633489801") # Check barcode is cleaned


class TestDataCleanerColes(TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.base_raw_product = {
            "_type": "PRODUCT",
            "id": "34567",
            "name": "Coles Test Product",
            "brand": "Coles Brand",
            "description": "A fine product from Coles.",
            "size": "1L",
            "imageUris": [{"uri": "image.png"}],
            "onlineHeirs": [[
                {"id": "1", "name": "Dairy"},
                {"id": "2", "name": "Milk"}
            ]],
            "pricing": {
                "now": 2.50,
                "was": 3.00,
                "comparable": "$2.50 / 1L",
                "unit": {
                    "price": 2.50,
                    "ofMeasureUnits": "L"
                }
            }
        }

    def test_standard_product_cleaning(self):
        """Test basic cleaning and mapping of a standard Coles product."""
        cleaner = DataCleanerColes(
            raw_product_list=[self.base_raw_product],
            company="coles",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], "34567")
        self.assertEqual(product['name'], "Coles Test Product")
        self.assertEqual(product['brand'], "Coles Brand")
        self.assertEqual(product['size'], "1L")
        self.assertEqual(product['image_url'], "https://www.coles.com.au/image.png")
        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['price_current'], 2.50)

    def test_category_path_cleaning(self):
        """Test that the nested category path is cleaned correctly."""
        cleaner = DataCleanerColes([self.base_raw_product], "coles", "s", "s", "s", self.timestamp)
        product = cleaner.clean_data()['products'][0]

        self.assertEqual(product['category_path'], ["Dairy", "Milk"])