
from django.test import TestCase
from unittest.mock import patch
from api.utils.scraper_utils.checkpoint_utils.update_page_progress import update_page_progress

class UpdatePageProgressTest(TestCase):

    @patch('api.utils.scraper_utils.checkpoint_utils.update_page_progress.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.update_page_progress.read_checkpoints')
    def test_update_progress_for_new_company(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test updating progress for a company not previously in the checkpoint file."""
        mock_read_checkpoints.return_value = {}
        company = 'new_company'
        store = 'store_123'
        completed = ['catA']
        current = 'catB'
        page = 2

        update_page_progress(company, store, completed, current, page)

        expected_checkpoint = {
            'new_company': {
                'current_store': 'store_123',
                'completed_categories': ['catA'],
                'current_category': 'catB',
                'last_completed_page': 2
            }
        }
        mock_write_checkpoints.assert_called_once_with(expected_checkpoint)

    @patch('api.utils.scraper_utils.checkpoint_utils.update_page_progress.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.update_page_progress.read_checkpoints')
    def test_update_progress_for_existing_company(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test updating progress for a company already in the checkpoint file."""
        mock_read_checkpoints.return_value = {
            'existing_company': {
                'current_store': 'store_456',
                'completed_categories': ['catX'],
                'current_category': 'catY',
                'last_completed_page': 1
            }
        }
        company = 'existing_company'
        store = 'store_789'
        completed = ['catX', 'catY']
        current = 'catZ'
        page = 5

        update_page_progress(company, store, completed, current, page)

        expected_checkpoint = {
            'existing_company': {
                'current_store': 'store_789',
                'completed_categories': ['catX', 'catY'],
                'current_category': 'catZ',
                'last_completed_page': 5
            }
        }
        mock_write_checkpoints.assert_called_once_with(expected_checkpoint)
