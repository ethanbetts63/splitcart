
import json
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock

from scraping.scrapers.product_scraper_iga import IgaScraper

def create_mock_iga_product_api_response(products_list):
    """A minimal representation of the JSON structure from IGA's product API."""
    return {"items": products_list}

class ProductScraperIgaTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.scraper = IgaScraper(
            command=self.mock_command,
            company='iga',
            store_id='1234',
            retailer_store_id='1111',
            store_name='Test IGA',
            state='NSW'
        )
        # Mock dependencies that are normally created in setup()
        self.scraper.session = Mock()
        self.scraper.jsonl_writer = Mock()

    @patch('scraping.scrapers.product_scraper_iga.get_iga_categories')
    def test_get_work_items(self, mock_get_iga_categories):
        """Test that get_work_items calls the helper function and returns its result."""
        # Arrange
        expected_categories = [{'identifier': 'fruits-veg'}]
        mock_get_iga_categories.return_value = expected_categories

        # Act
        work_items = self.scraper.get_work_items()

        # Assert
        self.assertEqual(work_items, expected_categories)
        mock_get_iga_categories.assert_called_once_with(
            self.mock_command, self.scraper.retailer_store_id, self.scraper.session
        )

    def test_fetch_data_for_item_with_pagination(self):
        """Test that product data is fetched correctly across multiple pages."""
        # Arrange
        # Page 1 has one product
        page1_data = create_mock_iga_product_api_response([{'sku': '1'}])
        mock_response1 = MagicMock()
        mock_response1.json.return_value = page1_data
        mock_response1.status_code = 200

        # Page 2 has one product
        page2_data = create_mock_iga_product_api_response([{'sku': '2'}])
        mock_response2 = MagicMock()
        mock_response2.json.return_value = page2_data
        mock_response2.status_code = 200

        # Page 3 has no products, terminating the loop
        page3_data = create_mock_iga_product_api_response([])
        mock_response3 = MagicMock()
        mock_response3.json.return_value = page3_data
        mock_response3.status_code = 200

        self.scraper.session.get.side_effect = [mock_response1, mock_response2, mock_response3]

        # Act
        results = self.scraper.fetch_data_for_item({'identifier': 'some-category-identifier'})

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['sku'], '1')
        self.assertEqual(results[1]['sku'], '2')
        self.assertEqual(self.scraper.session.get.call_count, 3)
        
        # Check that 'skip' and 'take' parameters were updated in the calls
        call_args_list = self.scraper.session.get.call_args_list
        self.assertEqual(call_args_list[0].kwargs['params']['skip'], 0)
        self.assertEqual(call_args_list[1].kwargs['params']['skip'], 36)
        self.assertEqual(call_args_list[2].kwargs['params']['skip'], 72)

    @patch('scraping.scrapers.product_scraper_iga.DataCleanerIga')
    def test_clean_raw_data_uses_data_cleaner(self, mock_data_cleaner):
        """Test that clean_raw_data correctly instantiates and uses DataCleanerIga."""
        # Arrange
        raw_data = [{'sku': '1'}]
        mock_cleaner_instance = mock_data_cleaner.return_value
        mock_cleaner_instance.clean_data.return_value = {'cleaned': True}

        # Act
        cleaned_result = self.scraper.clean_raw_data(raw_data)

        # Assert
        mock_data_cleaner.assert_called_once()
        init_args = mock_data_cleaner.call_args.kwargs
        self.assertEqual(init_args['raw_product_list'], raw_data)
        self.assertEqual(init_args['company'], 'iga')
        self.assertEqual(init_args['store_id'], '1234')

        mock_cleaner_instance.clean_data.assert_called_once()
        self.assertEqual(cleaned_result, {'cleaned': True})
