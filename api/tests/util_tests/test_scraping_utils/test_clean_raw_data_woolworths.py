from django.test import TestCase
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths

class TestCleanRawDataWoolworths(TestCase):

    def test_clean_raw_data_woolworths_with_valid_data(self):
        raw_product_list = [
            {
                "Stockcode": 12345,
                "UrlFriendlyName": "test-product",
                "Name": "Test Product",
                "Brand": "Test Brand",
                "Barcode": "1234567890123",
                "PackageSize": "1kg",
                "Price": 10.00,
                "WasPrice": 12.00,
                "IsOnSpecial": True,
                "IsAvailable": True,
                "CupPrice": 1.00,
                "CupMeasure": "100g",
                "AdditionalAttributes": {
                    "piesdepartmentnamesjson": '["Department"]'
                }
            }
        ]
        category = "test-category"
        page_num = 1
        timestamp = datetime.now()

        cleaned_data = clean_raw_data_woolworths(raw_product_list, category, page_num, timestamp)

        self.assertEqual(cleaned_data["metadata"]["store"], "woolworths")
        self.assertEqual(cleaned_data["metadata"]["category"], category)
        self.assertEqual(len(cleaned_data["products"]), 1)

        product = cleaned_data["products"][0]
        self.assertEqual(product["name"], "Test Product")
        self.assertEqual(product["brand"], "Test Brand")
        self.assertEqual(product["price"], 10.00)
        self.assertTrue(product["is_on_special"])
        self.assertEqual(product["departments"][0]["name"], "Department")

    def test_clean_raw_data_woolworths_with_empty_data(self):
        cleaned_data = clean_raw_data_woolworths([], "test", 1, datetime.now())
        self.assertEqual(len(cleaned_data["products"]), 0)