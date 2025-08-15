
import json
import os
import tempfile
import shutil
from datetime import datetime
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state import create_aldi_stores_by_state, SOURCE_DIR, OUTPUT_FILE

class CreateAldiStoresByStateTest(TestCase):

    def setUp(self):
        # Create temporary directories for source and output files
        self.temp_source_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()

        # Patch SOURCE_DIR and OUTPUT_FILE to use temporary paths
        self.patcher_source_dir = patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.SOURCE_DIR', self.temp_source_dir)
        self.patcher_output_file = patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.OUTPUT_FILE', os.path.join(self.temp_output_dir, 'aldi_stores_by_state.json'))
        
        self.patcher_source_dir.start()
        self.patcher_output_file.start()

    def tearDown(self):
        # Clean up temporary directories
        shutil.rmtree(self.temp_source_dir)
        shutil.rmtree(self.temp_output_dir)
        self.patcher_source_dir.stop()
        self.patcher_output_file.stop()

    def _create_mock_json_file(self, filename, data):
        filepath = os.path.join(self.temp_source_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return filepath

    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.datetime')
    def test_create_aldi_stores_by_state_success(self, mock_datetime):
        """Test successful aggregation of store data by state."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        # Create mock input files
        self._create_mock_json_file('nsw.json', {
            'metadata': {'state_iso': 'NSW'},
            'stores': [{'name': 'Store A', 'id': '1'}, {'name': 'Store B', 'id': '2'}]
        })
        self._create_mock_json_file('vic.json', {
            'metadata': {'state_iso': 'VIC'},
            'stores': [{'name': 'Store C', 'id': '3'}]
        })
        self._create_mock_json_file('other.txt', 'not json') # Non-json file
        self._create_mock_json_file('aldi_stores_by_state.json', {'existing': 'data'}) # Should be ignored

        create_aldi_stores_by_state()

        # Verify output file content
        output_filepath = os.path.join(self.temp_output_dir, 'aldi_stores_by_state.json')
        self.assertTrue(os.path.exists(output_filepath))

        with open(output_filepath, 'r') as f:
            output_data = json.load(f)

        self.assertEqual(output_data['metadata']['last_updated_timestamp'], mock_now.isoformat())
        self.assertEqual(output_data['metadata']['total_stores_scraped'], 3)
        self.assertIn('NSW', output_data['stores_by_state'])
        self.assertIn('VIC', output_data['stores_by_state'])
        self.assertEqual(len(output_data['stores_by_state']['NSW']), 2)
        self.assertEqual(len(output_data['stores_by_state']['VIC']), 1)
        self.assertEqual(output_data['stores_by_state']['NSW'][0]['store_name'], 'Store A')

    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.datetime')
    def test_create_aldi_stores_by_state_empty_source_dir(self, mock_datetime):
        """Test with an empty source directory."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        create_aldi_stores_by_state()

        output_filepath = os.path.join(self.temp_output_dir, 'aldi_stores_by_state.json')
        self.assertTrue(os.path.exists(output_filepath))

        with open(output_filepath, 'r') as f:
            output_data = json.load(f)

        self.assertEqual(output_data['metadata']['total_stores_scraped'], 0)
        self.assertEqual(output_data['stores_by_state'], {})

    @patch('api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state.datetime')
    def test_create_aldi_stores_by_state_missing_metadata(self, mock_datetime):
        """Test handling of files with missing metadata or state_iso."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        self._create_mock_json_file('no_meta.json', {
            'stores': [{'name': 'Store D', 'id': '4'}]
        }) # Missing metadata
        self._create_mock_json_file('no_state.json', {
            'metadata': {'other_key': 'value'},
            'stores': [{'name': 'Store E', 'id': '5'}]
        }) # Missing state_iso

        create_aldi_stores_by_state()

        output_filepath = os.path.join(self.temp_output_dir, 'aldi_stores_by_state.json')
        with open(output_filepath, 'r') as f:
            output_data = json.load(f)

        self.assertIn('unknown', output_data['stores_by_state'])
        self.assertEqual(len(output_data['stores_by_state']['unknown']), 2)
        self.assertEqual(output_data['metadata']['total_stores_scraped'], 2)
