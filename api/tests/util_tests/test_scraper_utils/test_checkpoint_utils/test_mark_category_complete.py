
from django.test import TestCase
from unittest.mock import patch
from api.utils.scraper_utils.checkpoint_utils.mark_category_complete import mark_category_complete

class MarkCategoryCompleteTest(TestCase):

    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.read_checkpoints')
    def test_mark_category_complete_new_company(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test marking a category complete for a new company."""
        mock_read_checkpoints.return_value = {}
        company = 'new_company'
        store = 'store_a'
        completed_cats = []
        new_cat = 'cat1'

        mark_category_complete(company, store, completed_cats, new_cat)

        expected_checkpoint = {
            'new_company': {
                'current_store': 'store_a',
                'completed_categories': ['cat1'],
                'current_category': None,
                'last_completed_page': 0
            }
        }
        mock_write_checkpoints.assert_called_once_with(expected_checkpoint)

    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.read_checkpoints')
    def test_mark_category_complete_existing_company(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test marking a category complete for an existing company."""
        mock_read_checkpoints.return_value = {
            'existing_company': {
                'current_store': 'store_b',
                'completed_categories': ['cat1'],
                'current_category': 'cat2',
                'last_completed_page': 5
            }
        }
        company = 'existing_company'
        store = 'store_b'
        completed_cats = ['cat1']
        new_cat = 'cat2'

        mark_category_complete(company, store, completed_cats, new_cat)

        expected_checkpoint = {
            'existing_company': {
                'current_store': 'store_b',
                'completed_categories': ['cat1', 'cat2'],
                'current_category': None,
                'last_completed_page': 0
            }
        }
        mock_write_checkpoints.assert_called_once_with(expected_checkpoint)

    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.write_checkpoints')
    @patch('api.utils.scraper_utils.checkpoint_utils.mark_category_complete.read_checkpoints')
    def test_mark_category_already_complete(self, mock_read_checkpoints, mock_write_checkpoints):
        """Test that the completed categories list is not modified if the category is already present."""
        mock_read_checkpoints.return_value = {
            'company': {
                'completed_categories': ['cat1', 'cat2']
            }
        }
        company = 'company'
        store = 'store_c'
        completed_cats = ['cat1', 'cat2']
        new_cat = 'cat1'

        mark_category_complete(company, store, completed_cats, new_cat)

        expected_checkpoint = {
            'company': {
                'current_store': 'store_c',
                'completed_categories': ['cat1', 'cat2'],
                'current_category': None,
                'last_completed_page': 0
            }
        }
        mock_write_checkpoints.assert_called_once_with(expected_checkpoint)
