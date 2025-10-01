import unittest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga

class TestDataCleanerIga(unittest.TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.base_raw_product = {
            "productId": "12345",
            "name": "IGA Test Product",
            "brand": "IGA Brand",
            "barcode": "9300633489801",
            "description": "A fine product from IGA.",
            "unitOfSize": {
                "size": "500",
                "abbreviation": "g"
            },
            "image": {
                "default": "/image.png"
            },
            "defaultCategory": [
                {
                    "categoryBreadcrumb": "Groceries/Pantry/Spreads"
                }
            ],
            "priceNumeric": 5.00,
            "wholePrice": 5,
            "wasWholePrice": None,
            "tprPrice": [],
            "pricePerUnit": "$1.00 per 100g",
            "available": True,
            "sellBy": "each"
        }

    def test_standard_product_cleaning(self):
        """Test basic cleaning and mapping of a standard IGA product."""
        cleaner = DataCleanerIga(
            raw_product_list=[self.base_raw_product],
            company="iga",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['sku'], "12345")
        self.assertEqual(product['name'], "IGA Test Product")
        self.assertEqual(product['brand'], "IGA Brand")
        self.assertEqual(product['size'], "500g each")
        self.assertFalse(product['is_on_special'])
        self.assertEqual(product['price_current'], 5.00)
        self.assertEqual(product['category_path'], ["Groceries", "Pantry", "Spreads"])

    def test_special_price_calculation(self):
        """Test that special prices are calculated correctly."""
        special_product = self.base_raw_product.copy()
        special_product["wasWholePrice"] = 6
        special_product["tprPrice"] = [{"wholePrice": 4}]

        cleaner = DataCleanerIga(
            raw_product_list=[special_product],
            company="iga",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()
        product = cleaned_data['products'][0]

        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['price_current'], 4)
        self.assertEqual(product['price_was'], 6)

    def test_category_path_with_numeric_index(self):
        """Test that the category path is correctly extracted when using a numeric index."""
        self.base_raw_product['defaultCategory'][0]['categoryBreadcrumb'] = "Fruit & Veg/Fruit/Apples"
        cleaner = DataCleanerIga(
            raw_product_list=[self.base_raw_product],
            company="iga",
            store_name="Test Store",
            store_id="5678",
            state="VIC",
            timestamp=self.timestamp
        )
        cleaned_data = cleaner.clean_data()
        product = cleaned_data['products'][0]

        self.assertEqual(product['category_path'], ["Fruit & Veg", "Fruit", "Apples"])

if __name__ == '__main__':
    unittest.main()