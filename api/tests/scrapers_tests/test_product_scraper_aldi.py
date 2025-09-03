from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock

from api.scrapers.product_scraper_aldi import ProductScraperAldi

class ProductScraperAldiTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.scraper = ProductScraperAldi(
            command=self.mock_command, 
            company='aldi', 
            store_id='123', 
            store_name='Test Aldi', 
            state='NSW'
        )
        # The scraper's setup() method initializes the session, so we call it here
        # We will patch the session's methods in individual tests
        self.scraper.setup()

    @patch('api.scrapers.product_scraper_aldi.get_aldi_categories')
    def test_get_work_items(self, mock_get_categories):
        """Test that get_work_items calls the category utility function."""
        # Arrange
        expected_categories = [('cat-a', 'key-a'), ('cat-b', 'key-b')]
        mock_get_categories.return_value = expected_categories

        # Act
        work_items = self.scraper.get_work_items()

        # Assert
        self.assertEqual(work_items, expected_categories)
        mock_get_categories.assert_called_once_with(self.mock_command, '123', self.scraper.session)

    @patch('requests.Session.get')
    def test_fetch_data_for_item_paginates_correctly(self, mock_get):
        """Test that fetch_data_for_item handles API pagination."""
        # Arrange
        # Simulate two pages of results, then an empty page to stop the loop
        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = {'data': [{'id': 1}, {'id': 2}]}
        mock_response_page1.status_code = 200

        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = {'data': [{'id': 3}]}
        mock_response_page2.status_code = 200

        mock_response_page3 = MagicMock()
        mock_response_page3.json.return_value = {'data': []} # Empty list to terminate
        mock_response_page3.status_code = 200

        mock_get.side_effect = [mock_response_page1, mock_response_page2, mock_response_page3]

        # Act
        results = self.scraper.fetch_data_for_item(('test-slug', 'test-key'))

        # Assert
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], 1)
        self.assertEqual(results[2]['id'], 3)
        self.assertEqual(mock_get.call_count, 3)

        # Check that the offset parameter was updated correctly for pagination
        first_call_params = mock_get.call_args_list[0].kwargs['params']
        second_call_params = mock_get.call_args_list[1].kwargs['params']
        self.assertEqual(first_call_params['offset'], 0)
        self.assertEqual(second_call_params['offset'], 30)

    @patch('api.scrapers.product_scraper_aldi.DataCleanerAldi')
    def test_clean_raw_data_uses_data_cleaner(self, mock_data_cleaner):
        """Test that clean_raw_data correctly instantiates and uses DataCleanerAldi."""
        # Arrange
        raw_data = [{'id': 1}, {'id': 2}]
        mock_cleaner_instance = mock_data_cleaner.return_value
        mock_cleaner_instance.clean_data.return_value = {'cleaned': True}

        # Act
        cleaned_result = self.scraper.clean_raw_data(raw_data)

        # Assert
        mock_data_cleaner.assert_called_once()
        # Check that the cleaner was initialized with the correct arguments
        init_args = mock_data_cleaner.call_args.kwargs
        self.assertEqual(init_args['raw_product_list'], raw_data)
        self.assertEqual(init_args['company'], 'aldi')
        self.assertEqual(init_args['store_id'], '123')

        mock_cleaner_instance.clean_data.assert_called_once()
        self.assertEqual(cleaned_result, {'cleaned': True})
