
import json
import os
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.aldi.load_progress import load_progress

class LoadProgressTest(TestCase):

    def setUp(self):
        self.PROGRESS_FILE = 'dummy_progress.json'
        self.LAT_MIN = -35.0
        self.LAT_STEP = 0.1
        self.LON_MIN = 115.0
        self.LON_MAX = 155.0
        self.LON_STEP = 0.1

    @patch('os.path.exists', return_value=True)
    def test_load_progress_continue_lon(self, mock_exists):
        """Test loading progress where longitude should be incremented."""
        mock_data = {'last_lat': -30.0, 'last_lon': 120.0}
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file:
            lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
            self.assertEqual(lat, -30.0)
            self.assertEqual(lon, 120.0 + self.LON_STEP)

    @patch('os.path.exists', return_value=True)
    def test_load_progress_rollover_lat(self, mock_exists):
        """Test loading progress where latitude should be incremented (longitude rollover)."""
        mock_data = {'last_lat': -30.0, 'last_lon': self.LON_MAX}
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file:
            lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
            self.assertEqual(lat, -30.0 + self.LAT_STEP)
            self.assertEqual(lon, self.LON_MIN)

    @patch('os.path.exists', return_value=False)
    def test_load_progress_no_file(self, mock_exists):
        """Test loading progress when the file does not exist."""
        lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
        self.assertEqual(lat, self.LAT_MIN)
        self.assertEqual(lon, self.LON_MIN)

    @patch('os.path.exists', return_value=True)
    def test_load_progress_invalid_json(self, mock_exists):
        """Test loading progress when the file contains invalid JSON."""
        with patch('builtins.open', mock_open(read_data='invalid json')) as mock_file:
            lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
            self.assertEqual(lat, self.LAT_MIN)
            self.assertEqual(lon, self.LON_MIN)

    @patch('os.path.exists', return_value=True)
    def test_load_progress_empty_file(self, mock_exists):
        """Test loading progress when the file is empty."""
        with patch('builtins.open', mock_open(read_data='')) as mock_file:
            lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
            self.assertEqual(lat, self.LAT_MIN)
            self.assertEqual(lon, self.LON_MIN)

    @patch('os.path.exists', return_value=True)
    def test_load_progress_missing_keys(self, mock_exists):
        """Test loading progress when last_lat or last_lon keys are missing."""
        mock_data = {'some_other_key': 123}
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file:
            lat, lon = load_progress(self.PROGRESS_FILE, self.LAT_MIN, self.LAT_STEP, self.LON_MIN, self.LON_MAX, self.LON_STEP)
            self.assertEqual(lat, self.LAT_MIN)
            self.assertEqual(lon, self.LON_MIN)
