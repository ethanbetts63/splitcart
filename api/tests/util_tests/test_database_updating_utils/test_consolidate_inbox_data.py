import unittest
import tempfile
import shutil
import json
import os
from unittest.mock import MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data

class ConsolidateInboxDataTest(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_command = MagicMock()

        # Product data - same product, different stores
        self.product_data_1 = {
            "metadata": {"store_id": "S001", "company": "TestCorp"},
            "product": {
                "normalized_name_brand_size": "prod-a-1kg",
                "price_current": 1.99,
                "product_id_store": "P1_S1",
                "category_path": ["Bakery", "Bread"]
            }
        }
        self.product_data_2 = {
            "metadata": {"store_id": "S002", "company": "TestCorp"},
            "product": {
                "normalized_name_brand_size": "prod-a-1kg",
                "price_current": 1.89,
                "product_id_store": "P1_S2",
                "category_path": ["Bakery", "Rolls"]
            }
        }
        # A different product
        self.product_data_3 = {
            "metadata": {"store_id": "S001", "company": "TestCorp"},
            "product": {
                "normalized_name_brand_size": "prod-b-500g",
                "price_current": 3.50,
                "product_id_store": "P2_S1",
                "category_path": ["Dairy", "Milk"]
            }
        }

        # Create a dummy .jsonl file
        with open(os.path.join(self.test_dir, "data.jsonl"), 'w') as f:
            f.write(json.dumps(self.product_data_1) + '\n')
            f.write(json.dumps(self.product_data_2) + '\n')
            f.write(json.dumps(self.product_data_3) + '\n')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_consolidation_logic(self):
        consolidated_data, processed_files = consolidate_inbox_data(self.test_dir, self.mock_command)

        # We expect 2 unique products
        self.assertEqual(len(consolidated_data), 2)

        # Check the consolidated data for the first product
        key1 = "prod-a-1kg"
        self.assertIn(key1, consolidated_data)
        product1_data = consolidated_data[key1]

        # Check price history
        self.assertEqual(len(product1_data['price_history']), 2)
        prices = {p['price'] for p in product1_data['price_history']}
        self.assertEqual(prices, {1.99, 1.89})

        # Check category paths
        self.assertEqual(len(product1_data['category_paths']), 2)
        self.assertIn(tuple(["Bakery", "Bread"]), product1_data['category_paths'])
        self.assertIn(tuple(["Bakery", "Rolls"]), product1_data['category_paths'])

        # Check the second product
        key2 = "prod-b-500g"
        self.assertIn(key2, consolidated_data)
        self.assertEqual(len(consolidated_data[key2]['price_history']), 1)
