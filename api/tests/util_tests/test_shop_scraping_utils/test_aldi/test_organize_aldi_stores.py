import json
import os
import shutil
import tempfile
from datetime import date
from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from api.utils.shop_scraping_utils.aldi.organize_aldi_stores import organize_aldi_stores, SOURCE_FILE, BASE_OUTPUT_DIR

class OrganizeAldiStoresTest(TestCase):

    def setUp(self):
        # Create temporary directories for source and output files
        self.temp_source_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()

        # Patch SOURCE_FILE and BASE_OUTPUT_DIR to use temporary paths
        self.patcher_source_file = patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.SOURCE_FILE', os.path.join(self.temp_source_dir, 'aldi_stores_raw.json'))
        self.patcher_output_dir = patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.BASE_OUTPUT_DIR', self.temp_output_dir)
        
        self.patcher_source_file.start()
        self.patcher_output_dir.start()

        # Create a mock source file path
        self.mock_source_file_path = os.path.join(self.temp_source_dir, 'aldi_stores_raw.json')

    def tearDown(self):
        # Clean up temporary directories
        shutil.rmtree(self.temp_source_dir)
        shutil.rmtree(self.temp_output_dir)
        self.patcher_source_file.stop()
        self.patcher_output_dir.stop()

    def _create_mock_source_file(self, data):
        with open(self.mock_source_file_path, 'w') as f:
            json.dump(data, f)

    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.os.remove')
    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.create_aldi_stores_by_state')
    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.date')
    def test_organize_aldi_stores_success(self, mock_date, mock_create_aldi_stores_by_state, mock_os_remove):
        """Test successful organization of stores into state-specific files."""
        mock_date.today.return_value = date(2023, 1, 1)

        raw_stores_data = {
            "store1": {
                "id": "1", "name": "Aldi Sydney",
                "address": {"regionIsoCode": "NSW", "regionName": "New South Wales"}
            },
            "store2": {
                "id": "2", "name": "Aldi Melbourne",
                "address": {"regionIsoCode": "VIC", "regionName": "Victoria"}
            },
            "store3": {
                "id": "3", "name": "Aldi Newcastle",
                "address": {"regionIsoCode": "NSW", "regionName": "New South Wales"}
            },
            "store4": {
                "id": "4", "name": "Aldi Unknown",
                "address": {"regionIsoCode": "", "regionName": ""}
            } # Missing state info
        }
        self._create_mock_source_file(raw_stores_data)

        organize_aldi_stores()

        # Assert state-specific files are created and contain correct data
        nsw_file = os.path.join(self.temp_output_dir, 'nsw.json')
        vic_file = os.path.join(self.temp_output_dir, 'vic.json')
        unknown_file = os.path.join(self.temp_output_dir, 'unknown-state.json')

        self.assertTrue(os.path.exists(nsw_file))
        self.assertTrue(os.path.exists(vic_file))
        self.assertTrue(os.path.exists(unknown_file))

        with open(nsw_file, 'r') as f:
            nsw_data = json.load(f)
            self.assertEqual(nsw_data['metadata']['number_of_stores'], 2)
            self.assertEqual(nsw_data['metadata']['state_iso'], 'NSW')
            self.assertEqual(nsw_data['stores'][0]['id'], '1')
            self.assertEqual(nsw_data['stores'][1]['id'], '3')

        with open(vic_file, 'r') as f:
            vic_data = json.load(f)
            self.assertEqual(vic_data['metadata']['number_of_stores'], 1)
            self.assertEqual(vic_data['metadata']['state_iso'], 'VIC')
            self.assertEqual(vic_data['stores'][0]['id'], '2')

        with open(unknown_file, 'r') as f:
            unknown_data = json.load(f)
            self.assertEqual(unknown_data['metadata']['number_of_stores'], 1)
            self.assertEqual(unknown_data['metadata']['state_iso'], 'UNKNOWN-STATE')
            self.assertEqual(unknown_data['stores'][0]['id'], '4')

        # Assert original source file is removed
        mock_os_remove.assert_called_once_with(self.mock_source_file_path)

        # Assert create_aldi_stores_by_state is called
        mock_create_aldi_stores_by_state.assert_called_once()

    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.os.remove')
    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.create_aldi_stores_by_state')
    def test_organize_aldi_stores_file_not_found(self, mock_create_aldi_stores_by_state, mock_os_remove):
        """Test handling of FileNotFoundError for the source file."""
        # Do not create the source file
        organize_aldi_stores()

        # Assert no output files are created
        self.assertEqual(len(os.listdir(self.temp_output_dir)), 0)

        # Assert os.remove is not called
        mock_os_remove.assert_not_called()

        # Assert create_aldi_stores_by_state is not called
        mock_create_aldi_stores_by_state.assert_not_called()

    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.os.remove')
    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.create_aldi_stores_by_state')
    def test_organize_aldi_stores_json_decode_error(self, mock_create_aldi_stores_by_state, mock_os_remove):
        """Test handling of JSONDecodeError for a corrupted source file."""
        with open(self.mock_source_file_path, 'w') as f:
            f.write('invalid json content')

        organize_aldi_stores()

        # Assert no output files are created
        self.assertEqual(len(os.listdir(self.temp_output_dir)), 0)

        # Assert os.remove is not called
        mock_os_remove.assert_not_called()

        # Assert create_aldi_stores_by_state is not called
        mock_create_aldi_stores_by_state.assert_not_called()

    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.os.remove')
    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.create_aldi_stores_by_state')
    @patch('api.utils.shop_scraping_utils.aldi.organize_aldi_stores.date')
    def test_organize_aldi_stores_empty_source_file(self, mock_date, mock_create_aldi_stores_by_state, mock_os_remove):
        """Test with an empty source file (empty JSON object)."""
        mock_date.today.return_value = date(2023, 1, 1)
        self._create_mock_source_file({})

        organize_aldi_stores()

        # Assert no state files are created (as there are no stores)
        self.assertEqual(len(os.listdir(self.temp_output_dir)), 0)

        # Assert original source file is removed
        mock_os_remove.assert_called_once_with(self.mock_source_file_path)

        # Assert create_aldi_stores_by_state is called
        mock_create_aldi_stores_by_state.assert_called_once()