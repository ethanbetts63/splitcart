
import os
import json
import tempfile
from django.test import TestCase
from api.utils.shop_scraping_utils.iga.save_progress import save_progress

class TestSaveProgress(TestCase):

    def setUp(self):
        """Set up a temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up the temporary file."""
        os.remove(self.temp_file_path)

    def test_save_progress(self):
        """Test that the progress data is saved correctly."""
        last_id = 123
        save_progress(self.temp_file_path, last_id)

        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        expected_data = {'last_id': 123}
        self.assertEqual(saved_data, expected_data)

    def test_overwrite_existing_progress(self):
        """Test that the function overwrites an existing progress file."""
        initial_data = {'last_id': 100}
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        new_last_id = 200
        save_progress(self.temp_file_path, new_last_id)

        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        expected_data = {'last_id': 200}
        self.assertEqual(saved_data, expected_data)
