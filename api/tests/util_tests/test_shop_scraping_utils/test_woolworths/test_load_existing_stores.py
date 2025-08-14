
import os
import json
import tempfile
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.woolworths.load_existing_stores import load_existing_stores

class TestLoadExistingStores(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.gettempdir()
        self.output_file = os.path.join(self.temp_dir, "stores.json")

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    @patch('os.path.exists', return_value=False)
    def test_no_existing_file(self, mock_exists):
        stores = load_existing_stores(self.output_file)
        self.assertEqual(stores, {})

    def test_with_valid_existing_file(self):
        stores_data = {"123": {"name": "Test Store"}}
        with open(self.output_file, 'w') as f:
            json.dump(stores_data, f)

        stores = load_existing_stores(self.output_file)
        self.assertEqual(stores, stores_data)

    def test_with_corrupt_existing_file(self):
        with open(self.output_file, 'w') as f:
            f.write("invalid json")

        stores = load_existing_stores(self.output_file)
        self.assertEqual(stores, {})

    def test_with_unexpected_format(self):
        with open(self.output_file, 'w') as f:
            json.dump([{"name": "Test Store"}], f)

        stores = load_existing_stores(self.output_file)
        self.assertEqual(stores, {})
