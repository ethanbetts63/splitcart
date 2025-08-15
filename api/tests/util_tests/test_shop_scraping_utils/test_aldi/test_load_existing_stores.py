
import json
import os
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.aldi.load_existing_stores import load_existing_stores

class LoadExistingStoresTest(TestCase):

    @patch('os.path.exists', return_value=True)
    def test_load_valid_existing_stores_file(self, mock_exists):
        """Test loading a valid and existing stores file."""
        mock_data = {'123': {'name': 'Aldi Store 1'}}
        mock_file_content = json.dumps(mock_data)
        with patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
            stores = load_existing_stores('dummy_path.json')
            self.assertEqual(stores, mock_data)
            mock_file.assert_called_once_with('dummy_path.json', 'r', encoding='utf-8')

    @patch('os.path.exists', return_value=False)
    def test_stores_file_does_not_exist(self, mock_exists):
        """Test that an empty dictionary is returned if the file does not exist."""
        stores = load_existing_stores('dummy_path.json')
        self.assertEqual(stores, {})

    @patch('os.path.exists', return_value=True)
    def test_invalid_json_in_stores_file(self, mock_exists):
        """Test that an empty dictionary is returned if the file contains invalid JSON."""
        with patch('builtins.open', mock_open(read_data='invalid json')) as mock_file:
            stores = load_existing_stores('dummy_path.json')
            self.assertEqual(stores, {})

    @patch('os.path.exists', return_value=True)
    def test_empty_stores_file(self, mock_exists):
        """Test that an empty dictionary is returned if the file is empty, causing a JSONDecodeError."""
        with patch('builtins.open', mock_open(read_data='')) as mock_file:
            stores = load_existing_stores('dummy_path.json')
            self.assertEqual(stores, {})
