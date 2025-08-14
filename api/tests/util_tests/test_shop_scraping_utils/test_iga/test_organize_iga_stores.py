
import os
import json
import tempfile
import shutil
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.iga.organize_iga_stores import organize_iga_stores

class TestOrganizeIgaStores(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('os.remove')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('api.utils.shop_scraping_utils.iga.organize_iga_stores.SOURCE_FILE', 'dummy/path/to/source.json')
    @patch('api.utils.shop_scraping_utils.iga.organize_iga_stores.BASE_OUTPUT_DIR')
    def test_organization_and_file_creation(self, mock_base_dir, mock_json_load, mock_open_func, mock_remove):
        mock_base_dir.return_value = self.temp_dir
        stores_data = [
            {"state": "NSW"},
            {"state": "VIC"},
            {"state": "NSW"}
        ]
        mock_json_load.return_value = stores_data

        organize_iga_stores()

        mock_remove.assert_called_once_with('dummy/path/to/source.json')

        # Check that the correct files were written
        written_files = [call[0][0] for call in mock_open_func.call_args_list if call[0][1] == 'w']
        self.assertIn(os.path.join(self.temp_dir, 'nsw.json'), written_files)
        self.assertIn(os.path.join(self.temp_dir, 'vic.json'), written_files)
