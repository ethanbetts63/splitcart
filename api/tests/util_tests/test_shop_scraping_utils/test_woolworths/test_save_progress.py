
import os
import json
import tempfile
from django.test import TestCase
from api.utils.shop_scraping_utils.woolworths.save_progress import save_progress

class TestSaveProgress(TestCase):

    def setUp(self):
        """Set up a  file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up the  file."""
        os.remove(self.temp_file_path)

    def test_save_progress(self):
        """Test that the progress data is saved correctly."""
        lat, lon = -33.86, 151.20
        lat_step, lon_step = 0.1, 0.1
        stores_found = 42
        
        save_progress(self.temp_file_path, lat, lon, lat_step, lon_step, stores_found)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        expected_data = {
            'last_lat': -33.86,
            'last_lon': 151.20,
            'lat_step': 0.1,
            'lon_step': 0.1,
            'stores_found': 42
        }
        self.assertEqual(saved_data, expected_data)

    def test_rounding_of_coordinates(self):
        """Test that latitude and longitude are rounded to 2 decimal places."""
        lat, lon = -33.86789, 151.20123
        save_progress(self.temp_file_path, lat, lon, 0.1, 0.1, 10)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data['last_lat'], -33.87)
        self.assertEqual(saved_data['last_lon'], 151.20)

    def test_overwrite_existing_progress(self):
        """Test that the function overwrites an existing progress file."""
        initial_data = {'last_lat': 0, 'last_lon': 0, 'lat_step': 1, 'lon_step': 1, 'stores_found': 0}
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
            
        lat, lon, stores_found = -10.5, 140.5, 5
        save_progress(self.temp_file_path, lat, lon, 0.5, 0.5, stores_found)
        
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        expected_data = {
            'last_lat': -10.5,
            'last_lon': 140.5,
            'lat_step': 0.5,
            'lon_step': 0.5,
            'stores_found': 5
        }
        self.assertEqual(saved_data, expected_data)
