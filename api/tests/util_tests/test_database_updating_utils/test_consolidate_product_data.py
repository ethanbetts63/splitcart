import tempfile
import shutil
import json
import os
from django.test import TestCase
from api.utils.database_updating_utils.consolidate_product_data import consolidate_product_data

class ConsolidateProductDataTest(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.company_dir = os.path.join(self.test_dir, "company_a")
        os.makedirs(self.company_dir)

        # Create dummy store files
        self.store1_data = {
            "metadata": {"store_id": "S001", "company_name": "Company A"},
            "products": [
                {
                    "name": "Test Product 1",
                    "brand": "Brand X",
                    "size": "100g",
                    "price_history": [{"price": 1.99}],
                    "category_paths": [["Bakery", "Bread"]]
                },
                {
                    "name": "Test Product 2",
                    "brand": "Brand Y",
                    "size": "200g",
                    "price_history": [{"price": 2.99}],
                    "category_paths": [["Dairy", "Milk"]]
                }
            ]
        }
        with open(os.path.join(self.company_dir, "store1.json"), 'w') as f:
            json.dump(self.store1_data, f)

        self.store2_data = {
            "metadata": {"store_id": "S002", "company_name": "Company A"},
            "products": [
                {
                    "name": "Test Product 1", # Same as in store1
                    "brand": "Brand X",
                    "size": "100g",
                    "price_history": [{"price": 1.89}],
                    "category_paths": [["Bakery", "Bread"]]
                }
            ]
        }
        with open(os.path.join(self.company_dir, "store2.json"), 'w') as f:
            json.dump(self.store2_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_consolidate_product_data(self):
        consolidated_data = consolidate_product_data(self.test_dir)

        self.assertEqual(len(consolidated_data), 2)

        key1 = ("test product 1", "brand x", "100g")
        key2 = ("test product 2", "brand y", "200g")

        self.assertIn(key1, consolidated_data)
        self.assertIn(key2, consolidated_data)

        # Check product 1 data
        self.assertEqual(len(consolidated_data[key1]['price_history']), 2)
        self.assertEqual(consolidated_data[key1]['price_history'][0]['price'], 1.99)
        self.assertEqual(consolidated_data[key1]['price_history'][1]['price'], 1.89)
        self.assertIn(tuple(["Bakery", "Bread"]), consolidated_data[key1]['category_paths'])

        # Check product 2 data
        self.assertEqual(len(consolidated_data[key2]['price_history']), 1)
        self.assertEqual(consolidated_data[key2]['price_history'][0]['price'], 2.99)
