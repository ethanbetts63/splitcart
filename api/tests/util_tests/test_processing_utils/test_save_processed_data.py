import os
import json
import tempfile
from django.test import TestCase
from api.utils.processing_utils.save_processed_data import save_processed_data

class TestSaveProcessedData(TestCase):

    def setUp(self):
        """Set up a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_data_path = self.temp_dir.name

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def test_save_processed_data_success(self):
        """Test that the data packet is saved correctly."""
        data_packet = {
            "metadata": {
                "store_id": "123",
                "scrape_date": "2025-08-15",
                "company": "test_company"
            },
            "products": [{"name": "Product A"}]
        }
        
        success = save_processed_data(self.processed_data_path, data_packet)
        self.assertTrue(success)
        
        expected_filepath = os.path.join(self.processed_data_path, "test_company_123_2025-08-15.json")
        self.assertTrue(os.path.exists(expected_filepath))
        
        with open(expected_filepath, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, data_packet)

    def test_save_processed_data_missing_key(self):
        """Test that the function returns False if a key is missing."""
        data_packet = {
            "metadata": {
                "scrape_date": "2025-08-15",
                "company": "test_company"
            },
            "products": [{"name": "Product A"}]
        }
        
        success = save_processed_data(self.processed_data_path, data_packet)
        self.assertFalse(success)
        
        # Ensure no file was created
        self.assertEqual(len(os.listdir(self.processed_data_path)), 0)

    def test_save_processed_data_invalid_path(self):
        """Test that the function handles an invalid path."""
        data_packet = {
            "metadata": {
                "store_id": "123",
                "scrape_date": "2025-08-15",
                "company": "test_company"
            },
            "products": [{"name": "Product A"}]
        }
        
        # Use a path that cannot be created (e.g., a file instead of a directory)
        invalid_path = os.path.join(self.temp_dir.name, "invalid_file.txt")
        with open(invalid_path, 'w') as f:
            f.write("This is a file")
        
        success = save_processed_data(invalid_path, data_packet)
        self.assertFalse(success)
        
        # Ensure no file was created in the invalid path
        self.assertFalse(os.path.exists(os.path.join(invalid_path, "test_company_123_2025-08-15.json")))
