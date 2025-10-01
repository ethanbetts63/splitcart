import unittest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerAldi import DataCleanerAldi

class TestDataCleanerAldi(unittest.TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.base_raw_product = {
            "sku": "12345",
            "name": "Aldi Test Product",
            "brandName": "Aldi Brand",
            "sellingSize": "1kg",
            "assets": [
                {
                    "url": "/image.png"
                }
            ],
            "categories": [
                {"name": "Groceries"},
                {"name": "Pantry"}
            ],
            "price": {
                "amount": 500,
                "wasPriceDisplay": "$6.00",
                "comparisonDisplay": "$5.00 per 1kg"
            },
            "urlSlugText": "aldi-test-product",
            "notForSale": False
        }

    def test_standard_product_cleaning(self):
        """Test basic cleaning and mapping of a standard Aldi product."""
        cleaner = DataCleanerAldi(
            raw_product_list=[self.base_raw_product],
            company="aldi",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['sku'], "12345")
        self.assertEqual(product['name'], "Aldi Test Product")
        self.assertEqual(product['brand'], "Aldi Brand")
        self.assertEqual(product['size'], "1kg")
        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['price_current'], 5.00)
        self.assertEqual(product['price_was'], 6.00)
        self.assertEqual(product['category_path'], ["Groceries", "Pantry"])
        self.assertEqual(product['url'], "https://www.aldi.com.au/product/aldi-test-product-12345")

    def test_price_in_cents_conversion(self):
        """Test that the price in cents is correctly converted to dollars."""
        self.base_raw_product['price']['amount'] = 1234
        cleaner = DataCleanerAldi(
            raw_product_list=[self.base_raw_product],
            company="aldi",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()
        product = cleaned_data['products'][0]

        self.assertEqual(product['price_current'], 12.34)

    def test_was_price_parsing(self):
        """Test that the 'was' price is correctly parsed from a string."""
        self.base_raw_product['price']['wasPriceDisplay'] = "was $10.99"
        cleaner = DataCleanerAldi(
            raw_product_list=[self.base_raw_product],
            company="aldi",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()
        product = cleaned_data['products'][0]

        self.assertEqual(product['price_was'], 10.99)

if __name__ == '__main__':
    unittest.main()