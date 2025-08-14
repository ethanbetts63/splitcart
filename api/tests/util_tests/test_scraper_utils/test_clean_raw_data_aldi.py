from django.test import TestCase
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi

class CleanRawDataAldiTest(TestCase):

    def setUp(self):
        self.company = "aldi"
        self.store_name = "Aldi Test Store"
        self.store_id = "12345"
        self.state = "NSW"
        self.category_slug = "test-category"
        self.page_num = 1
        self.timestamp = datetime.now()

    def test_basic_product_cleaning(self):
        raw_product_list = [
            {
                "sku": "SKU1",
                "name": "Aldi Product 1",
                "brandName": "Aldi Brand",
                "price": {"amount": 150, "comparison": 1500, "comparisonDisplay": "$15.00 / kg"},
                "urlSlugText": "aldi-product-1",
                "assets": [{"url": "http://image.com/img1.jpg"}],
                "notForSale": False,
                "quantityMax": 10,
                "sellingSize": "1kg",
                "categories": [{"name": "Dairy"}, {"name": "Milk"}]
            }
        ]
        cleaned_data = clean_raw_data_aldi(
            raw_product_list, self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )

        self.assertIn("metadata", cleaned_data)
        self.assertIn("products", cleaned_data)
        self.assertEqual(len(cleaned_data["products"]), 1)

        product = cleaned_data["products"][0]
        self.assertEqual(product["product_id_store"], "SKU1")
        self.assertEqual(product["name"], "Aldi Product 1")
        self.assertEqual(product["brand"], "Aldi Brand")
        self.assertEqual(product["price_current"], 1.50)
        self.assertEqual(product["price_unit"], 15.00)
        self.assertEqual(product["unit_of_measure"], "kg")
        self.assertEqual(product["url"], "https://www.aldi.com.au/product/aldi-product-1")
        self.assertEqual(product["image_url_main"], "http://image.com/img1.jpg")
        self.assertEqual(product["is_available"], True)
        self.assertEqual(product["purchase_limit"], 10)
        self.assertEqual(product["package_size"], "1kg")
        self.assertEqual(product["category_path"], ["Dairy", "Milk"])
        self.assertFalse(product["is_on_special"])

    def test_price_was_transformation(self):
        raw_product_list = [
            {
                "sku": "SKU2",
                "name": "On Special",
                "price": {"amount": 100, "wasPriceDisplay": "$2.00"}
            }
        ]
        cleaned_data = clean_raw_data_aldi(
            raw_product_list, self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertEqual(product["price_current"], 1.00)
        self.assertEqual(product["price_was"], 2.00)
        self.assertTrue(product["is_on_special"])
        self.assertEqual(product["price_save_amount"], 1.00)

    def test_missing_price_info(self):
        raw_product_list = [
            {
                "sku": "SKU3",
                "name": "No Price",
                "price": {}
            }
        ]
        cleaned_data = clean_raw_data_aldi(
            raw_product_list, self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertIsNone(product["price_current"])
        self.assertIsNone(product["price_was"])
        self.assertFalse(product["is_on_special"])
        self.assertIsNone(product["price_save_amount"])

    def test_unit_of_measure_parsing(self):
        raw_product_list = [
            {
                "sku": "SKU4",
                "name": "Unit Test",
                "price": {"amount": 100, "comparisonDisplay": "$1.00 / Each"}
            }
        ]
        cleaned_data = clean_raw_data_aldi(
            raw_product_list, self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertEqual(product["unit_of_measure"], "Each")

    def test_empty_raw_product_list(self):
        cleaned_data = clean_raw_data_aldi(
            [], self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        self.assertEqual(len(cleaned_data["products"]), 0)

    def test_metadata_correctness(self):
        raw_product_list = []
        cleaned_data = clean_raw_data_aldi(
            raw_product_list, self.company, self.store_name, self.store_id, 
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        metadata = cleaned_data["metadata"]
        self.assertEqual(metadata["company"], self.company)
        self.assertEqual(metadata["store_name"], self.store_name)
        self.assertEqual(metadata["store_id"], self.store_id)
        self.assertEqual(metadata["state"], self.state)
        self.assertEqual(metadata["category"], self.category_slug)
        self.assertEqual(metadata["page_number"], self.page_num)
        self.assertEqual(metadata["scraped_at"], self.timestamp.isoformat())
