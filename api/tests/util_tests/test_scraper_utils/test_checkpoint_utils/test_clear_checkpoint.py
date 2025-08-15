
from django.test import TestCase
from unittest.mock import patch, Mock
from api.utils.scraper_utils.checkpoint_utils.clear_checkpoint import clear_checkpoint

class ClearCheckpointTest(TestCase):

    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.read_checkpoints')
    def test_clear_existing_checkpoint(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test that an existing company checkpoint is cleared."""
        mock_read_checkpoints.return_value = {
            'coles': {'some_data': 'here'},
            'woolworths': {'other_data': 'there'}
        }

        clear_checkpoint('coles')

        expected_checkpoints = {'woolworths': {'other_data': 'there'}}
        mock_write_checkpoints.assert_called_once_with(expected_checkpoints)

    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.read_checkpoints')
    def test_clear_nonexistent_checkpoint(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test that nothing happens if the company checkpoint does not exist."""
        mock_read_checkpoints.return_value = {
            'woolworths': {'other_data': 'there'}
        }

        clear_checkpoint('coles')

        mock_write_checkpoints.assert_not_called()

    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.clear_checkpoint.read_checkpoints')
    def test_clear_checkpoint_empty_file(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test that nothing happens when the checkpoints file is empty."""
        mock_read_checkpoints.return_value = {}

        clear_checkpoint('coles')

        mock_write_checkpoints.assert_not_called()
