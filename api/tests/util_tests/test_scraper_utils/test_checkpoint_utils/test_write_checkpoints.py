
import json
import os
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.scraper_utils.checkpoint_utils.write_checkpoints import write_checkpoints, CHECKPOINT_FILE

class WriteCheckpointsTest(TestCase):

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_write_checkpoints_success(self, mock_json_dump, mock_file_open, mock_makedirs):
        """Test that checkpoints are written correctly to the file."""
        test_data = {
            'coles': {'current_store': 'store_a', 'completed_categories': ['cat1']},
            'woolworths': {'current_store': 'store_b', 'completed_categories': ['catX']}
        }

        write_checkpoints(test_data)

        # Assert os.makedirs was called
        mock_makedirs.assert_called_once_with(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)

        # Assert open was called with the correct file path and mode
        mock_file_open.assert_called_once_with(CHECKPOINT_FILE, 'w')

        # Assert json.dump was called with the correct data and file handle
        mock_json_dump.assert_called_once_with(test_data, mock_file_open(), indent=2)

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_write_empty_checkpoints(self, mock_json_dump, mock_file_open, mock_makedirs):
        """Test that an empty dictionary is written correctly."""
        test_data = {}

        write_checkpoints(test_data)

        mock_makedirs.assert_called_once_with(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        mock_file_open.assert_called_once_with(CHECKPOINT_FILE, 'w')
        mock_json_dump.assert_called_once_with(test_data, mock_file_open(), indent=2)
