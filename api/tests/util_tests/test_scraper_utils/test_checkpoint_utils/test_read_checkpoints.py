
import json
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.scraper_utils.checkpoint_utils.read_checkpoints import read_checkpoints, CHECKPOINT_FILE

class ReadCheckpointsTest(TestCase):

    @patch('os.path.exists', return_value=True)
    def test_read_valid_checkpoints_file(self, mock_exists):
        """Test reading a valid and existing checkpoints file."""
        mock_data = {'coles': {'status': 'in_progress'}}
        mock_file_content = json.dumps(mock_data)
        with patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
            checkpoints = read_checkpoints()
            self.assertEqual(checkpoints, mock_data)
            mock_file.assert_called_once_with(CHECKPOINT_FILE, 'r')

    @patch('os.path.exists', return_value=False)
    def test_checkpoints_file_does_not_exist(self, mock_exists):
        """Test that an empty dictionary is returned if the file does not exist."""
        checkpoints = read_checkpoints()
        self.assertEqual(checkpoints, {})

    @patch('os.path.exists', return_value=True)
    def test_invalid_json_in_checkpoints_file(self, mock_exists):
        """Test that an empty dictionary is returned if the file contains invalid JSON."""
        with patch('builtins.open', mock_open(read_data='invalid json')) as mock_file:
            checkpoints = read_checkpoints()
            self.assertEqual(checkpoints, {})

    @patch('os.path.exists', return_value=True)
    def test_empty_checkpoints_file(self, mock_exists):
        """Test that an empty dictionary is returned if the file is empty, causing a JSONDecodeError."""
        with patch('builtins.open', mock_open(read_data='')) as mock_file:
            checkpoints = read_checkpoints()
            self.assertEqual(checkpoints, {})
