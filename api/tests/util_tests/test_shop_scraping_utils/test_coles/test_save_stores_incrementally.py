
import os
import json
import tempfile
from django.test import TestCase
from api.utils.shop_scraping_utils.coles.save_stores_incrementally import save_stores_incrementally

class TestSaveStoresIncrementally(TestCase):

    def setUp(self):
        """Set up a  file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up the  file."""
        os.remove(self.temp_file_path)

    def test_save_stores_incrementally(self):
        """Test that the stores dictionary is saved correctly."""
        stores_dict = {
            "123": {"name": "Coles Test Store"},
            "456": {"name": "Another Coles"}
        }
        
        save_stores_incrementally(self.temp_file_path, stores_dict)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, stores_dict)

    def test_save_empty_dictionary(self):
        """Test that an empty dictionary is saved correctly."""
        stores_dict = {}
        
        save_stores_incrementally(self.temp_file_path, stores_dict)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, stores_dict)

    def test_overwrite_existing_file(self):
        """Test that the function overwrites an existing file."""
        initial_data = {"789": {"name": "Initial Store"}}
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
            
        new_stores_dict = {"123": {"name": "New Store"}}
        save_stores_incrementally(self.temp_file_path, new_stores_dict)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data, new_stores_dict)
