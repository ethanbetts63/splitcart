from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from api.utils.management_utils.run_iga_scraper import run_iga_scraper

# Define a simple class to mimic the Store model for testing
class MockStore:
    def __init__(self, name, store_id, retailer_store_id, state):
        self.name = name
        self.store_id = store_id
        self.retailer_store_id = retailer_store_id
        self.state = state
        self.last_scraped_products = None # Initialize
        self.is_online_shopable = False # Initialize
        self.save = MagicMock() # Make save a MagicMock

class RunIgaScraperTest(TestCase):
    @patch('api.utils.management_utils.run_iga_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_iga_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_iga_scraper.scrape_and_save_iga_data')
    @patch('api.utils.management_utils.run_iga_scraper.timezone.now')
    def test_run_iga_scraper_success(self, mock_timezone_now, mock_scrape_and_save_iga_data,
                                      mock_get_active_stores_for_company, mock_get_company_by_name):
        # Mock company and stores
        mock_iga_company = MagicMock(name='Iga')
        mock_iga_company.name = 'Iga' # Explicitly set the attribute
        mock_get_company_by_name.return_value = mock_iga_company

        mock_store1 = MockStore(name='IGA Store 1', store_id='1', retailer_store_id='retailer1', state='WA')
        mock_store2 = MockStore(name='IGA Fresh Store 2', store_id='2', retailer_store_id='retailer2', state='VIC')
        mock_stores_queryset = MagicMock()
        mock_stores_queryset.order_by.return_value = [mock_store1, mock_store2]
        mock_get_active_stores_for_company.return_value = mock_stores_queryset

        # Mock scrape_and_save_iga_data to return True for success
        mock_scrape_and_save_iga_data.return_value = True

        # Mock timezone.now()
        mock_now = timezone.datetime(2025, 1, 1, 10, 0, 0)
        mock_timezone_now.return_value = mock_now

        batch_size = 2
        raw_data_path = '/tmp/raw_data'

        run_iga_scraper(batch_size, raw_data_path)

        # Assertions
        mock_get_company_by_name.assert_called_once_with('Iga')
        mock_get_active_stores_for_company.assert_called_once_with(mock_iga_company)
        mock_stores_queryset.order_by.assert_called_once_with('last_scraped_products')

        self.assertEqual(mock_scrape_and_save_iga_data.call_count, 2)
        mock_scrape_and_save_iga_data.assert_any_call(
            company='Iga',
            store_id='1',
            retailer_store_id='retailer1',
            store_name='IGA Store 1',
            store_name_slug='store-1', # slugify('IGA Store 1'.lower().replace('iga', '').replace('fresh', ''))
            state='WA',
            save_path=raw_data_path
        )
        mock_scrape_and_save_iga_data.assert_any_call(
            company='Iga',
            store_id='2',
            retailer_store_id='retailer2',
            store_name='IGA Fresh Store 2',
            store_name_slug='store-2', # slugify('IGA Fresh Store 2'.lower().replace('iga', '').replace('fresh', ''))
            state='VIC',
            save_path=raw_data_path
        )

        self.assertEqual(mock_store1.save.call_count, 1)
        self.assertEqual(mock_store2.save.call_count, 1)
        self.assertEqual(mock_store1.last_scraped_products, mock_now)
        self.assertEqual(mock_store2.last_scraped_products, mock_now)
        self.assertTrue(mock_store1.is_online_shopable)
        self.assertTrue(mock_store2.is_online_shopable)

    @patch('api.utils.management_utils.run_iga_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_iga_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_iga_scraper.scrape_and_save_iga_data')
    @patch('api.utils.management_utils.run_iga_scraper.timezone.now')
    def test_run_iga_scraper_scrape_fails(self, mock_timezone_now, mock_scrape_and_save_iga_data,
                                          mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_iga_company = MagicMock(name='Iga')
        mock_iga_company.name = 'Iga'
        mock_get_company_by_name.return_value = mock_iga_company

        mock_store1 = MockStore(name='IGA Store 1', store_id='1', retailer_store_id='retailer1', state='WA')
        mock_stores_queryset = MagicMock()
        mock_stores_queryset.order_by.return_value = [mock_store1]
        mock_get_active_stores_for_company.return_value = mock_stores_queryset

        mock_scrape_and_save_iga_data.return_value = False # Simulate scrape failure

        run_iga_scraper(1, '/tmp/raw_data')

        self.assertEqual(mock_store1.save.call_count, 1)
        self.assertFalse(mock_store1.is_online_shopable)
        self.assertIsNone(mock_store1.last_scraped_products) # Should not be updated on failure

    @patch('api.utils.management_utils.run_iga_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_iga_scraper.get_active_stores_for_company')
    def test_run_iga_scraper_no_company(self, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_get_company_by_name.return_value = None
        run_iga_scraper(1, '/tmp/raw_data')
        mock_get_company_by_name.assert_called_once_with('Iga')
        mock_get_active_stores_for_company.assert_not_called()

    @patch('api.utils.management_utils.run_iga_scraper.get_company_by_name')
    @patch('api.utils.management_utils.run_iga_scraper.get_active_stores_for_company')
    @patch('api.utils.management_utils.run_iga_scraper.scrape_and_save_iga_data')
    def test_run_iga_scraper_no_active_stores(self, mock_scrape_and_save_iga_data, mock_get_active_stores_for_company, mock_get_company_by_name):
        mock_iga_company = MagicMock(name='Iga')
        mock_iga_company.name = 'Iga'
        mock_get_company_by_name.return_value = mock_iga_company
        mock_get_active_stores_for_company.return_value = None
        run_iga_scraper(1, '/tmp/raw_data')
        mock_get_company_by_name.assert_called_once_with('Iga')
        mock_get_active_stores_for_company.assert_called_once_with(mock_iga_company)
        mock_scrape_and_save_iga_data.assert_not_called()