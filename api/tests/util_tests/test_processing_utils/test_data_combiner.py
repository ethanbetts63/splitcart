import os
import json
import tempfile
from django.test import TestCase
from unittest import mock
from api.utils.processing_utils.data_combiner import data_combiner

class TestDataCombiner(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file1_path = os.path.join(self.temp_dir.name, "coles_file1.json")
        self.file2_path = os.path.join(self.temp_dir.name, "coles_file2.json")
        
        # File 1 with metadata
        with open(self.file1_path, 'w') as f:
            json.dump({
                "metadata": {"company": "coles", "store_name": "Test Store"},
                "products": [{"name": "Product A", "category_path": ["cat1"]}]
            }, f)
            
        # File 2 as a list of products
        with open(self.file2_path, 'w') as f:
            json.dump([
                {"name": "Product B"},
                {"name": "Product C", "category_path": ["cat2"]}
            ], f)

    def tearDown(self):
        self.temp_dir.cleanup()

    @mock.patch('api.utils.processing_utils.data_combiner.get_category_path')
    def test_data_combiner(self, mock_get_category_path):
        """Test that data_combiner combines products and extracts metadata."""
        mock_get_category_path.return_value = ["mocked_cat"]
        
        page_files = [self.file1_path, self.file2_path]
        combined_products, metadata = data_combiner(page_files)
        
        # Check metadata
        self.assertEqual(metadata["company"], "coles")
        self.assertEqual(metadata["store_name"], "Test Store")
        
        # Check combined products
        self.assertEqual(len(combined_products), 3)
        self.assertEqual(combined_products[0]["name"], "Product A")
        self.assertEqual(combined_products[1]["name"], "Product B")
        self.assertEqual(combined_products[2]["name"], "Product C")
        
        # Check category_path generation
        self.assertEqual(combined_products[0]["category_path"], ["cat1"])
        self.assertEqual(combined_products[1]["category_path"], ["mocked_cat"])
        self.assertEqual(combined_products[2]["category_path"], ["cat2"])
        
        # Check that get_category_path was called once for Product B
        self.assertEqual(mock_get_category_path.call_count, 1)

    def test_data_combiner_empty_input(self):
        """Test that the function handles an empty list of files."""
        combined_products, metadata = data_combiner([])
        self.assertEqual(combined_products, [])
        self.assertEqual(metadata, {})

    def test_data_combiner_file_not_found(self):
        """Test that the function handles a file not found error."""
        combined_products, metadata = data_combiner(["/nonexistent/file.json"])
        self.assertEqual(combined_products, [])
        self.assertEqual(metadata, {})
