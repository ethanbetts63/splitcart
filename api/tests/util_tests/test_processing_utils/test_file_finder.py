import os
import json
import tempfile
from django.test import TestCase
from api.utils.processing_utils.file_finder import file_finder

class TestFileFinder(TestCase):

    def setUp(self):
        """Set up a temporary directory and create some fake raw data files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_data_path = self.temp_dir.name
        
        # Create some fake data
        self.create_fake_json_file("file1.json", "coles", "WA", "Test Store", "123", "fruit-veg", "2025-08-15T10:00:00Z", 2)
        self.create_fake_json_file("file2.json", "coles", "WA", "Test Store", "123", "fruit-veg", "2025-08-15T10:00:00Z", 1)
        self.create_fake_json_file("file3.json", "woolworths", "NSW", "Another Store", "456", "meat", "2025-08-16T11:00:00Z", 1)
        self.create_fake_json_file("file4.json", "coles", "WA", "Test Store", "123", "dairy", "2025-08-15T10:00:00Z", 1)
        self.create_fake_json_file("file5.json", "coles", "WA", "Test Store", "123", "fruit-veg", "2025-08-16T10:00:00Z", 1)
        # A file with missing metadata
        with open(os.path.join(self.raw_data_path, "file6.json"), 'w') as f:
            json.dump({"data": "some data"}, f)
        # A non-json file
        with open(os.path.join(self.raw_data_path, "file7.txt"), 'w') as f:
            f.write("not json")

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def create_fake_json_file(self, filename, company, state, store_name, store_id, category, scraped_at, page_number):
        """Helper function to create a fake raw data file."""
        data = {
            "metadata": {
                "company": company,
                "state": state,
                "store_name": store_name,
                "store_id": store_id,
                "category": category,
                "scraped_at": scraped_at,
                "page_number": page_number
            },
            "products": []
        }
        with open(os.path.join(self.raw_data_path, filename), 'w') as f:
            json.dump(data, f)

    def test_file_finder_structure(self):
        """Test that the file_finder returns the correct nested structure."""
        result = file_finder(self.raw_data_path)
        
        self.assertIn("coles", result)
        self.assertIn("woolworths", result)
        
        self.assertIn("WA", result["coles"])
        self.assertIn("123", result["coles"]["WA"])
        self.assertIn("2025-08-15", result["coles"]["WA"]["123"])
        self.assertIn("fruit-veg", result["coles"]["WA"]["123"]["2025-08-15"])
        
        self.assertEqual(len(result["coles"]["WA"]["123"]["2025-08-15"]["fruit-veg"]), 2)

    def test_file_finder_sorting(self):
        """Test that the file paths are sorted by page_number."""
        result = file_finder(self.raw_data_path)
        
        file_paths = result["coles"]["WA"]["123"]["2025-08-15"]["fruit-veg"]
        self.assertTrue(file_paths[0].endswith("file2.json"))
        self.assertTrue(file_paths[1].endswith("file1.json"))

    def test_file_finder_nonexistent_path(self):
        """Test that the function handles a nonexistent path gracefully."""
        result = file_finder("/nonexistent/path")
        self.assertEqual(result, {})
