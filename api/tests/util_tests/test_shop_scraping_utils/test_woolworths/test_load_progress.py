
import os
import json
import tempfile
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.woolworths.load_progress import load_progress

class TestLoadProgress(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.gettempdir()
        self.progress_file = os.path.join(self.temp_dir, "progress.json")
        self.default_lat = -33.86
        self.default_lon = 151.20

    def tearDown(self):
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    @patch('os.path.exists', return_value=False)
    @patch('random.uniform', side_effect=[0.5, 0.6])
    def test_no_progress_file(self, mock_uniform, mock_exists):
        lat, lon, lat_step, lon_step, stores_found = load_progress(self.progress_file, self.default_lat, self.default_lon)
        self.assertEqual(lat, self.default_lat)
        self.assertEqual(lon, self.default_lon)
        self.assertEqual(lat_step, 0.5)
        self.assertEqual(lon_step, 0.6)
        self.assertEqual(stores_found, 0)

    def test_with_valid_progress_file(self):
        progress_data = {
            'last_lat': -30.0,
            'last_lon': 150.0,
            'lat_step': 0.1,
            'lon_step': 0.2,
            'stores_found': 10
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)

        lat, lon, lat_step, lon_step, stores_found = load_progress(self.progress_file, self.default_lat, self.default_lon)
        self.assertEqual(lat, -30.0)
        self.assertEqual(lon, 150.0)
        self.assertEqual(lat_step, 0.1)
        self.assertEqual(lon_step, 0.2)
        self.assertEqual(stores_found, 10)

    @patch('random.uniform', side_effect=[0.5, 0.6])
    def test_with_corrupt_progress_file(self, mock_uniform):
        with open(self.progress_file, 'w') as f:
            f.write("invalid json")

        lat, lon, lat_step, lon_step, stores_found = load_progress(self.progress_file, self.default_lat, self.default_lon)
        self.assertEqual(lat, self.default_lat)
        self.assertEqual(lon, self.default_lon)
        self.assertEqual(lat_step, 0.5)
        self.assertEqual(lon_step, 0.6)
        self.assertEqual(stores_found, 0)

    @patch('random.uniform', side_effect=[0.5, 0.6])
    def test_with_missing_keys_in_progress_file(self, mock_uniform):
        progress_data = {
            'last_lat': -30.0,
            'last_lon': 150.0
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)

        lat, lon, lat_step, lon_step, stores_found = load_progress(self.progress_file, self.default_lat, self.default_lon)
        self.assertEqual(lat, self.default_lat)
        self.assertEqual(lon, self.default_lon)
        self.assertEqual(lat_step, 0.5)
        self.assertEqual(lon_step, 0.6)
        self.assertEqual(stores_found, 0)
