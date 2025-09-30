from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths

def create_mock_woolworths_bundle(products_list):
    """A minimal representation of a Bundle from Woolworths' product api."""
    return {"Products": products_list}

class ProductScraperWoolworthsTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.categories = [('fruit-veg', '1_DEB5342'), ('bakery', '1_D5A2235')]
        self.scraper = ProductScraperWoolworths(
            command=self.mock_command,
            company='woolworths',
            store_id='1234',
            store_name='Test Woolworths',
            state='NSW',
            categories_to_fetch=self.categories
        )
        # Mock dependencies that are normally created in setup()
        self.scraper.session = Mock()
        self.scraper.jsonl_writer = Mock()

    def test_get_work_items(self):
        """Test that get_work_items returns the categories passed in the constructor."""
        self.assertEqual(self.scraper.get_work_items(), self.categories)

    def test_fetch_data_for_item_with_pagination(self):
        """Test that product data is fetched correctly across multiple pages."""
        # Arrange
        # Page 1 has one product
        page1_bundle = create_mock_woolworths_bundle([{'Stockcode': 123}])
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {"Bundles": [page1_bundle]}
        mock_response1.status_code = 200

        # Page 2 has one product
        page2_bundle = create_mock_woolworths_bundle([{'Stockcode': 456}])
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"Bundles": [page2_bundle]}
        mock_response2.status_code = 200

        # Page 3 has no products, terminating the loop
        mock_response3 = MagicMock()
        mock_response3.json.return_value = {"Bundles": []}
        mock_response3.status_code = 200

        self.scraper.session.post.side_effect = [mock_response1, mock_response2, mock_response3]

        # Act
        results = self.scraper.fetch_data_for_item(('some-category-slug', 'some-category-id'))

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['Stockcode'], 123)
        self.assertEqual(results[1]['Stockcode'], 456)
        self.assertEqual(self.scraper.session.post.call_count, 3)

        # Check that the pageNumber in the payload was updated
        call_args_list = self.scraper.session.post.call_args_list
        self.assertEqual(call_args_list[0].kwargs['json']['pageNumber'], 1)
        self.assertEqual(call_args_list[1].kwargs['json']['pageNumber'], 2)
        self.assertEqual(call_args_list[2].kwargs['json']['pageNumber'], 3)

    @patch('scraping.scrapers.product_scraper_woolworths.DataCleanerWoolworths')
    def test_clean_raw_data_uses_data_cleaner(self, mock_data_cleaner):
        """Test that clean_raw_data correctly instantiates and uses DataCleanerWoolworths."""
        # Arrange
        raw_data = [{'Stockcode': 123}]
        mock_cleaner_instance = mock_data_cleaner.return_value
        mock_cleaner_instance.clean_data.return_value = {'cleaned': True}

        # Act
        cleaned_result = self.scraper.clean_raw_data(raw_data)

        # Assert
        mock_data_cleaner.assert_called_once()
        init_args = mock_data_cleaner.call_args.kwargs
        self.assertEqual(init_args['raw_product_list'], raw_data)
        self.assertEqual(init_args['company'], 'woolworths')
        self.assertEqual(init_args['store_id'], '1234')

        mock_cleaner_instance.clean_data.assert_called_once()
        self.assertEqual(cleaned_result, {'cleaned': True})
