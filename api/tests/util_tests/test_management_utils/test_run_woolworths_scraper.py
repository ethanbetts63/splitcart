from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from api.utils.management_utils.run_woolworths_scraper import run_woolworths_scraper

# Define a simple class to mimic the Store model for testing
class MockStore:
    def __init__(self, name, store_id, state):
        self.name = name
        self.store_id = store_id
        self.state = state
        self.last_scraped_products = None # Initialize
        self.save = MagicMock() # Make save a MagicMock

class RunWoolworthsScraperTest(TestCase):
    @patch('api.utils.management_utils.run_woolworths_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_woolworths_categories')
    @patch('api.utils.management_utils.run_woolworths_scraper.scrape_and_save_woolworths_data')
    @patch('api.utils.management_utils.run_woolworths_scraper.timezone.now')
    def test_run_woolworths_scraper_success(self, mock_timezone_now, mock_scrape_and_save_woolworths_data,
                                           mock_get_woolworths_categories, mock_get_active_stores_for_company,
                                           mock_get_company_by_name):
        # Mock company and stores
        mock_woolworths_company = MagicMock(name='Woolworths')
        mock_woolworths_company.name = 'Woolworths' # Explicitly set the attribute
        mock_get_company_by_name.return_value = mock_woolworths_company

        mock_store1 = MockStore(name='Store 1', store_id='1', state='WA')
        mock_store2 = MockStore(name='Store 2', store_id='2', state='VIC')
        mock_stores_queryset = MagicMock()
        mock_stores_queryset.order_by.return_value = [mock_store1, mock_store2]
        mock_get_active_stores_for_company.return_value = mock_stores_queryset

        # Mock categories
        mock_categories = [('cat1_slug', 'cat1_id'), ('cat2_slug', 'cat2_id')]
        mock_get_woolworths_categories.return_value = mock_categories

        # Mock timezone.now()
        mock_now = timezone.datetime(2025, 1, 1, 10, 0, 0)
        mock_timezone_now.return_value = mock_now

        batch_size = 2
        raw_data_path = '/tmp/raw_data'

        run_woolworths_scraper(batch_size, raw_data_path)

        # Assertions
        mock_get_company_by_name.assert_called_once_with('Woolworths')
        mock_get_active_stores_for_company.assert_called_once_with(mock_woolworths_company)
        mock_stores_queryset.order_by.assert_called_once_with('last_scraped_products')
        mock_get_woolworths_categories.assert_called_once()

        self.assertEqual(mock_scrape_and_save_woolworths_data.call_count, 2)
        mock_scrape_and_save_woolworths_data.assert_any_call(
            company='Woolworths',
            state='WA',
            stores=[{'store_name': 'Store 1', 'store_id': '1'}],
            categories_to_fetch=mock_categories,
            save_path=raw_data_path
        )
        mock_scrape_and_save_woolworths_data.assert_any_call(
            company='Woolworths',
            state='VIC',
            stores=[{'store_name': 'Store 2', 'store_id': '2'}],
            categories_to_fetch=mock_categories,
            save_path=raw_data_path
        )

        self.assertEqual(mock_store1.save.call_count, 1)
        self.assertEqual(mock_store2.save.call_count, 1)
        self.assertEqual(mock_store1.last_scraped_products, mock_now)
        self.assertEqual(mock_store2.last_scraped_products, mock_now)

    @patch('api.utils.management_utils.run_woolworths_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_woolworths_categories')
    @patch('api.utils.management_utils.run_woolworths_scraper.scrape_and_save_woolworths_data')
    def test_run_woolworths_scraper_no_company(self, mock_scrape_and_save_woolworths_data, mock_get_woolworths_categories, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_get_company_by_name.return_value = None
        run_woolworths_scraper(1, '/tmp/raw_data')
        mock_get_company_by_name.assert_called_once_with('Woolworths')
        mock_get_active_stores_for_company.assert_not_called() # Corrected assertion
        mock_get_woolworths_categories.assert_not_called()
        mock_scrape_and_save_woolworths_data.assert_not_called()

    @patch('api.utils.management_utils.run_woolworths_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_woolworths_categories')
    @patch('api.utils.management_utils.run_woolworths_scraper.scrape_and_save_woolworths_data')
    def test_run_woolworths_scraper_no_active_stores(self, mock_scrape_and_save_woolworths_data, mock_get_woolworths_categories, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_woolworths_company = MagicMock(name='Woolworths')
        mock_woolworths_company.name = 'Woolworths'
        mock_get_company_by_name.return_value = mock_woolworths_company
        mock_get_active_stores_for_company.return_value = None
        run_woolworths_scraper(1, '/tmp/raw_data')
        mock_get_company_by_name.assert_called_once_with('Woolworths')
        mock_get_active_stores_for_company.assert_called_once_with(mock_woolworths_company)
        mock_get_woolworths_categories.assert_not_called()
        mock_scrape_and_save_woolworths_data.assert_not_called()

    @patch('api.utils.management_utils.run_woolworths_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_woolworths_scraper.get_woolworths_categories')
    @patch('api.utils.management_utils.run_woolworths_scraper.scrape_and_save_woolworths_data')
    def test_run_woolworths_scraper_no_categories(self, mock_scrape_and_save_woolworths_data, mock_get_woolworths_categories, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_woolworths_company = MagicMock(name='Woolworths')
        mock_woolworths_company.name = 'Woolworths'
        mock_get_company_by_name.return_value = mock_woolworths_company
        mock_get_active_stores_for_company.return_value = MagicMock(order_by=MagicMock(return_value=[])) # Return empty queryset
        mock_get_woolworths_categories.return_value = None # Simulate no categories
        run_woolworths_scraper(1, '/tmp/raw_data')
        mock_get_company_by_name.assert_called_once_with('Woolworths')
        mock_get_active_stores_for_company.assert_called_once_with(mock_woolworths_company)
        mock_get_woolworths_categories.assert_called_once()
        mock_scrape_and_save_woolworths_data.assert_not_called()