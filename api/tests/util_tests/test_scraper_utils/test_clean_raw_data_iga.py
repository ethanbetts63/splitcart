from django.test import TestCase
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

class CleanRawDataIgaTest(TestCase):

    def setUp(self):
        self.company = "iga"
        self.store_id = "IGA123"
        self.store_name = "IGA Test Store"
        self.state = "WA"
        self.category_slug = "bakery"
        self.page_num = 1
        self.timestamp = datetime.now()

    def _get_base_product_data(self):
        return {
            "sku": "SKU001",
            "barcode": "1234567890123",
            "name": "Test IGA Product",
            "brand": "IGA Brand",
            "wholePrice": 5.50,
            "available": True,
            "image": {"default": "http://example.com/iga_img.jpg"},
            "categories": [
                {"categoryBreadcrumb": "Food / Bakery"}
            ],
            "description": "Delicious bread. Country of Origin: Australia."
        }

    def test_basic_product_cleaning(self):
        raw_product_list = [self._get_base_product_data()]
        cleaned_data = clean_raw_data_iga(
            raw_product_list, self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )

        self.assertIn("metadata", cleaned_data)
        self.assertIn("products", cleaned_data)
        self.assertEqual(len(cleaned_data["products"]), 1)

        product = cleaned_data["products"][0]
        self.assertEqual(product["product_id_store"], "SKU001")
        self.assertEqual(product["barcode"], "1234567890123")
        self.assertEqual(product["name"], "Test IGA Product")
        self.assertEqual(product["brand"], "IGA Brand")
        self.assertEqual(product["price_current"], 5.50)
        self.assertIsNone(product["price_was"])
        self.assertFalse(product["is_on_special"])
        self.assertEqual(product["description_long"], "Delicious bread. Country of Origin: Australia.")
        self.assertEqual(product["country_of_origin"], "Australia")
        self.assertEqual(product["image_url_main"], "http://example.com/iga_img.jpg")
        self.assertEqual(product["category_path"], ["Food", "Bakery"])
        self.assertTrue(product["is_available"])

    def test_special_price_tpr(self):
        product_data = self._get_base_product_data()
        product_data["wasWholePrice"] = 10.00
        product_data["tprPrice"] = [{"wholePrice": 7.50}]
        product_data["priceSource"] = "special"

        cleaned_data = clean_raw_data_iga(
            [product_data], self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertEqual(product["price_current"], 7.50)
        self.assertEqual(product["price_was"], 10.00)
        self.assertTrue(product["is_on_special"])
        self.assertEqual(product["price_save_amount"], 2.50)
        self.assertEqual(product["promotion_type"], "special")

    def test_price_numeric_fallback(self):
        product_data = self._get_base_product_data()
        del product_data["wholePrice"]
        product_data["priceNumeric"] = 6.00

        cleaned_data = clean_raw_data_iga(
            [product_data], self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertEqual(product["price_current"], 6.00)

    def test_country_of_origin_extraction(self):
        product_data = self._get_base_product_data()
        product_data["description"] = "Product details. Country of Origin: New Zealand. More text."
        cleaned_data = clean_raw_data_iga(
            [product_data], self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        product = cleaned_data["products"][0]
        self.assertEqual(product["country_of_origin"], "New Zealand")

    def test_empty_raw_product_list(self):
        cleaned_data = clean_raw_data_iga(
            [], self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        self.assertEqual(len(cleaned_data["products"]), 0)

    def test_metadata_correctness(self):
        raw_product_list = []
        cleaned_data = clean_raw_data_iga(
            raw_product_list, self.company, self.store_id, self.store_name,
            self.state, self.category_slug, self.page_num, self.timestamp
        )
        metadata = cleaned_data["metadata"]
        self.assertEqual(metadata["company"], self.company)
        self.assertEqual(metadata["store_id"], self.store_id)
        self.assertEqual(metadata["store_name"], self.store_name)
        self.assertEqual(metadata["state"], self.state)
        self.assertEqual(metadata["category"], self.category_slug)
        self.assertEqual(metadata["page_number"], self.page_num)
        self.assertEqual(metadata["scraped_at"], self.timestamp.isoformat())
