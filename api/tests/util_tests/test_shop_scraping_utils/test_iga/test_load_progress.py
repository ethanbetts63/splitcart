
import os
import json
import tempfile
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.iga.load_progress import load_progress

class TestLoadProgress(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.gettempdir()
        self.progress_file = os.path.join(self.temp_dir, "progress.json")

    def tearDown(self):
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    @patch('os.path.exists', return_value=False)
    def test_no_progress_file(self, mock_exists):
        last_id = load_progress(self.progress_file)
        self.assertEqual(last_id, 0)

    def test_with_valid_progress_file(self):
        progress_data = {'last_id': 123}
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)

        last_id = load_progress(self.progress_file)
        self.assertEqual(last_id, 123)

    def test_with_corrupt_progress_file(self):
        with open(self.progress_file, 'w') as f:
            f.write("invalid json")

        last_id = load_progress(self.progress_file)
        self.assertEqual(last_id, 0)

    def test_with_missing_last_id_key(self):
        progress_data = {'other_key': 456}
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)

        last_id = load_progress(self.progress_file)
        self.assertEqual(last_id, 0)
