from django.test import TestCase
from datetime import datetime
from api.utils.clean_raw_data_coles import clean_raw_data_coles

class TestCleanRawDataColes(TestCase):

    def test_clean_raw_data_coles_with_valid_data(self):
        raw_product_list = [
            {
                "_type": "PRODUCT",
                "id": 12345,
                "name": "Test Product",
                "brand": "Test Brand",
                "size": "1kg",
                "pricing": {
                    "now": 10.00,
                    "was": 12.00,
                    "onlineSpecial": True,
                    "unit": {
                        "price": 1.00,
                        "ofMeasureQuantity": 100,
                        "ofMeasureUnits": "g"
                    }
                },
                "availability": True,
                "onlineHeirs": [
                    {
                        "subCategory": "Department",
                        "subCategoryId": "D123",
                        "category": "Category",
                        "categoryId": "C123",
                        "aisle": "Aisle",
                        "aisleId": "A123"
                    }
                ]
            }
        ]
        category = "test-category"
        page_num = 1
        timestamp = datetime.now()

        cleaned_data = clean_raw_data_coles(raw_product_list, category, page_num, timestamp)

        self.assertEqual(cleaned_data["metadata"]["store"], "coles")
        self.assertEqual(cleaned_data["metadata"]["category"], category)
        self.assertEqual(len(cleaned_data["products"]), 1)

        product = cleaned_data["products"][0]
        self.assertEqual(product["name"], "Test Product")
        self.assertEqual(product["brand"], "Test Brand")
        self.assertEqual(product["price"], 10.00)
        self.assertTrue(product["is_on_special"])
        self.assertEqual(product["departments"][0]["name"], "Department")
        self.assertEqual(product["categories"][0]["id"], "C123")

    def test_clean_raw_data_coles_with_empty_data(self):
        cleaned_data = clean_raw_data_coles([], "test", 1, datetime.now())
        self.assertEqual(len(cleaned_data["products"]), 0)