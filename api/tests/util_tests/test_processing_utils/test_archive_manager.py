import os
import json
import tempfile
from datetime import datetime
from django.test import TestCase
from api.utils.processing_utils.save_processed_data import save_processed_data
from products.tests.test_helpers.model_factories import ProductFactory

class TestArchiveManager(TestCase):

    def setUp(self):
        # Create a temporary directory for our test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_data_path = self.temp_dir.name

    def tearDown(self):
        # Clean up the temporary directory and all its contents
        self.temp_dir.cleanup()

    def test_save_processed_data_creates_file_and_returns_true(self):
        """Tests that the archive manager successfully creates a valid JSON file."""
        store_name = "coles"
        scrape_date = datetime.now().strftime("%Y-%m-%d")
        category_name = "fruit-vegetables"
        # Create a list of simple, JSON-serializable dictionaries to mimic real data
        combined_products = [
            {
                'name': 'Test Product 1',
                'brand': 'Test Brand',
                'price': 1.99,
            },
            {
                'name': 'Test Product 2',
                'brand': 'Test Brand',
                'price': 2.50,
            }
        ]
        source_files = ["file1.json", "file2.json"]

        # Call the function under test
        result = save_processed_data(
            self.processed_data_path,
            store_name,
            scrape_date,
            category_name,
            combined_products,
            source_files
        )

        # 1. Check that the function reports success
        self.assertTrue(result)

        # 2. Check that the file was actually created in the right place
        expected_dir = os.path.join(self.processed_data_path, store_name, scrape_date)
        expected_file = os.path.join(expected_dir, f"{category_name}.json")
        self.assertTrue(os.path.exists(expected_file))

        # 3. Check that the content of the file is correct
        with open(expected_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["metadata"]["store"], store_name)
            self.assertEqual(data["metadata"]["category"], category_name)
            self.assertEqual(data["metadata"]["product_count"], len(combined_products))
            self.assertEqual(len(data["products"]), len(combined_products))

    def test_save_processed_data_returns_false_for_empty_products(self):
        """Tests that the function correctly handles an empty product list."""
        store_name = "coles"
        scrape_date = datetime.now().strftime("%Y-%m-%d")
        category_name = "fruit-vegetables"
        combined_products = [] # Empty list
        source_files = ["file1.json", "file2.json"]

        result = save_processed_data(
            self.processed_data_path,
            store_name,
            scrape_date,
            category_name,
            combined_products,
            source_files
        )

        # The function should return False and not create any files
        self.assertFalse(result)
        expected_dir = os.path.join(self.processed_data_path, store_name, scrape_date)
        self.assertFalse(os.path.exists(expected_dir))