import os
import json
import tempfile
import shutil
from django.test import TestCase
from unittest.mock import patch
from datetime import date
from api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores import organize_woolworths_stores, slugify

class TestOrganizeWoolworthsStores(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.source_file_path = os.path.join(self.temp_dir, 'woolworths_stores_raw.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_fake_source_file(self, data):
        with open(self.source_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.SOURCE_FILE')
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.BASE_OUTPUT_DIR')
    def test_organization_and_file_creation(self, mock_base_dir, mock_source_file):
        mock_source_file.return_value = self.source_file_path
        mock_base_dir.return_value = self.temp_dir

        stores_data = {
            "1": {"Division": "Woolworths", "State": "NSW"},
            "2": {"Division": "Woolworths", "State": "VIC"},
            "3": {"Division": "BWS", "State": "NSW"}
        }
        self.create_fake_source_file(stores_data)

        organize_woolworths_stores()

        # Check if source file is deleted
        self.assertFalse(os.path.exists(self.source_file_path))

        # Check for new files
        woolies_nsw_path = os.path.join(self.temp_dir, 'woolworths', 'nsw.json')
        woolies_vic_path = os.path.join(self.temp_dir, 'woolworths', 'vic.json')
        bws_nsw_path = os.path.join(self.temp_dir, 'bws', 'nsw.json')

        self.assertTrue(os.path.exists(woolies_nsw_path))
        self.assertTrue(os.path.exists(woolies_vic_path))
        self.assertTrue(os.path.exists(bws_nsw_path))

        # Check content of one file
        with open(woolies_nsw_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['metadata']['number_of_stores'], 1)
            self.assertEqual(data['metadata']['brand'], 'woolworths')
            self.assertEqual(data['metadata']['state'], 'NSW')
            self.assertEqual(len(data['stores']), 1)
            self.assertEqual(data['stores'][0]['State'], 'NSW')

class TestSlugify(TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Test Store 1"), "test-store-1")
        self.assertEqual(slugify("BWS Liquor"), "bws-liquor")
        self.assertEqual(slugify("  Spaces & Chars! "), "-spaces-chars-")