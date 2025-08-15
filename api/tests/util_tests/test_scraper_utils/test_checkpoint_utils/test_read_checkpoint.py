
from django.test import TestCase
from unittest.mock import patch
from api.utils.scraper_utils.checkpoint_utils.read_checkpoint import read_checkpoint

class ReadCheckpointTest(TestCase):

    @patch('api.utils.scraper_utils.checkpoint_utils.read_checkpoint.read_checkpoints')
    def test_read_existing_checkpoint(self, mock_read_checkpoints):
        """Test reading an existing company's checkpoint."""
        sample_checkpoints = {
            'woolworths': {
                'current_store': 'store_a',
                'completed_categories': ['cat1'],
                'current_category': 'cat2',
                'last_completed_page': 3
            }
        }
        mock_read_checkpoints.return_value = sample_checkpoints

        checkpoint = read_checkpoint('woolworths')

        self.assertEqual(checkpoint, sample_checkpoints['woolworths'])

    @patch('api.utils.scraper_utils.checkpoint_utils.read_checkpoint.read_checkpoints')
    def test_read_nonexistent_checkpoint(self, mock_read_checkpoints):
        """Test reading a checkpoint for a company that does not exist."""
        mock_read_checkpoints.return_value = {
            'coles': {'some_data': 'here'}
        }

        checkpoint = read_checkpoint('woolworths')

        expected_default = {
            "current_store": None,
            "completed_categories": [],
            "current_category": None,
            "last_completed_page": 0
        }
        self.assertEqual(checkpoint, expected_default)

    @patch('api.utils.scraper_utils.checkpoint_utils.read_checkpoint.read_checkpoints')
    def test_read_checkpoint_from_empty_file(self, mock_read_checkpoints):
        """Test reading a checkpoint when the checkpoints file is empty."""
        mock_read_checkpoints.return_value = {}

        checkpoint = read_checkpoint('any_company')

        expected_default = {
            "current_store": None,
            "completed_categories": [],
            "current_category": None,
            "last_completed_page": 0
        }
        self.assertEqual(checkpoint, expected_default)
