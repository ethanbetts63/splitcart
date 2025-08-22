from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from api.utils.management_utils.run_aldi_scraper import run_aldi_scraper

# Define a simple class to mimic the Store model for testing
class MockStore:
    def __init__(self, name, store_id, state):
        self.name = name
        self.store_id = store_id
        self.state = state
        self.last_scraped_products = None # Initialize
    
    def save(self):
        pass # Mock the save method

class RunAldiScraperTest(TestCase):
    @patch('api.utils.management_utils.run_aldi_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_aldi_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_aldi_scraper.scrape_and_save_aldi_data')
    @patch('api.utils.management_utils.run_aldi_scraper.timezone.now')
    def test_run_aldi_scraper_success(self, mock_timezone_now, mock_scrape_and_save_aldi_data,
                                      mock_get_active_stores_for_company, mock_get_company_by_name):
        # Mock company and stores
        mock_aldi_company = MagicMock(name='Aldi') # Reverted
        mock_aldi_company.name = 'Aldi' # Explicitly set the attribute
        mock_get_company_by_name.return_value = mock_aldi_company

        mock_store1 = MockStore(name='Store 1', store_id='1', state='WA')
        mock_store2 = MockStore(name='Store 2', store_id='2', state='VIC')

        mock_stores_queryset = MagicMock()
        mock_stores_queryset.order_by.return_value = [mock_store1, mock_store2]
        mock_get_active_stores_for_company.return_value = mock_stores_queryset

        # Mock timezone.now()
        mock_now = timezone.datetime(2025, 1, 1, 10, 0, 0)
        mock_timezone_now.return_value = mock_now

        batch_size = 2

        run_aldi_scraper(batch_size)

        # Assertions
        mock_get_company_by_name.assert_called_once_with('Aldi')
        mock_get_active_stores_for_company.assert_called_once_with(mock_aldi_company)
        mock_stores_queryset.order_by.assert_called_once_with('last_scraped_products')

        self.assertEqual(mock_scrape_and_save_aldi_data.call_count, 2)
        mock_scrape_and_save_aldi_data.assert_any_call(
            company='Aldi',
            store_name='Store 1',
            store_id='1',
            state='WA'
        )
        mock_scrape_and_save_aldi_data.assert_any_call(
            company='Aldi',
            store_name='Store 2',
            store_id='2',
            state='VIC'
        )

        # Assert on the attributes of the MockStore instances
        self.assertEqual(mock_store1.last_scraped_products, mock_now)
        self.assertEqual(mock_store2.last_scraped_products, mock_now)

    @patch('api.utils.management_utils.run_aldi_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_aldi_scraper.get_active_stores_for_company')
    def test_run_aldi_scraper_no_company(self, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_get_company_by_name.return_value = None
        run_aldi_scraper(1)
        mock_get_company_by_name.assert_called_once_with('Aldi')
        mock_get_active_stores_for_company.assert_not_called() # Corrected assertion

    @patch('api.utils.management_utils.run_aldi_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_aldi_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_aldi_scraper.scrape_and_save_aldi_data') # Added this patch
    def test_run_aldi_scraper_no_active_stores(self, mock_scrape_and_save_aldi_data, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_aldi_company = MagicMock(name='Aldi')
        mock_get_company_by_name.return_value = mock_aldi_company
        mock_get_active_stores_for_company.return_value = None
        run_aldi_scraper(1)
        mock_get_company_by_name.assert_called_once_with('Aldi')
        mock_get_active_stores_for_company.assert_called_once_with(mock_aldi_company)
        mock_scrape_and_save_aldi_data.assert_not_called() # Corrected assertion