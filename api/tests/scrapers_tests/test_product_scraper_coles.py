import json
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock

from api.scrapers.product_scraper_coles import ColesScraper

# A minimal representation of the JSON structure found in Coles' __NEXT_DATA__ script
def create_mock_next_data(products_list, store_id, page_num=1, total_results=1, page_size=48):
    return {
        "props": {
            "pageProps": {
                "initStoreId": store_id,
                "searchResults": {
                    "results": products_list,
                    "noOfResults": total_results,
                    "pageSize": page_size
                }
            }
        }
    }

class ProductScraperColesTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.categories = ['meat-seafood/beef', 'bakery/bread-rolls-wraps']
        self.scraper = ColesScraper(
            command=self.mock_command,
            company='coles',
            store_id='0584',
            store_name='Test Coles',
            state='NSW',
            categories_to_fetch=self.categories
        )
        # We mock the dependencies that are normally created in setup()
        self.scraper.session = Mock()
        self.scraper.jsonl_writer = Mock()

    def test_get_work_items(self):
        """Test that get_work_items returns the categories passed in the constructor."""
        self.assertEqual(self.scraper.get_work_items(), self.categories)

    def test_fetch_data_for_item_with_pagination(self):
        """Test that product data is fetched correctly across multiple pages."""
        # Arrange
        store_id = self.scraper.store_id
        # Page 1 has one product
        page1_data = create_mock_next_data([{'id': 1}], store_id, total_results=2, page_size=1)
        page1_html = f'<script id="__NEXT_DATA__">{json.dumps(page1_data)}</script>'
        mock_response1 = MagicMock()
        mock_response1.text = page1_html

        # Page 2 has one product
        page2_data = create_mock_next_data([{'id': 2}], store_id, total_results=2, page_size=1)
        page2_html = f'<script id="__NEXT_DATA__">{json.dumps(page2_data)}</script>'
        mock_response2 = MagicMock()
        mock_response2.text = page2_html

        # Page 3 has no products, terminating the loop
        page3_data = create_mock_next_data([], store_id, total_results=2, page_size=1)
        page3_html = f'<script id="__NEXT_DATA__">{json.dumps(page3_data)}</script>'
        mock_response3 = MagicMock()
        mock_response3.text = page3_html

        self.scraper.session.get.side_effect = [mock_response1, mock_response2, mock_response3]

        # Act
        results = self.scraper.fetch_data_for_item('some-category-slug')

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 1)
        self.assertEqual(results[1]['id'], 2)
        self.assertEqual(self.scraper.session.get.call_count, 2)
        # Check that the page parameter was updated in the URL
        self.assertIn('page=1', self.scraper.session.get.call_args_list[0].args[0])
        self.assertIn('page=2', self.scraper.session.get.call_args_list[1].args[0])

    @patch('api.scrapers.product_scraper_coles.DataCleanerColes')
    def test_clean_raw_data_uses_data_cleaner(self, mock_data_cleaner):
        """Test that clean_raw_data correctly instantiates and uses DataCleanerColes."""
        # Arrange
        raw_data = [{'id': 1}]
        mock_cleaner_instance = mock_data_cleaner.return_value
        mock_cleaner_instance.clean_data.return_value = {'cleaned': True}

        # Act
        cleaned_result = self.scraper.clean_raw_data(raw_data)

        # Assert
        mock_data_cleaner.assert_called_once()
        init_args = mock_data_cleaner.call_args.kwargs
        self.assertEqual(init_args['raw_product_list'], raw_data)
        self.assertEqual(init_args['company'], 'coles')

        mock_cleaner_instance.clean_data.assert_called_once()
        self.assertEqual(cleaned_result, {'cleaned': True})

    @patch('api.scrapers.product_scraper_coles.ColesBarcodeScraper')
    def test_post_scrape_enrichment_calls_barcode_scraper(self, mock_barcode_scraper):
        """Test that post_scrape_enrichment calls the barcode scraper."""
        # Arrange
        self.scraper.jsonl_writer.temp_file_path = '/tmp/test.jsonl'
        mock_scraper_instance = mock_barcode_scraper.return_value

        # Act
        self.scraper.post_scrape_enrichment()

        # Assert
        mock_barcode_scraper.assert_called_once_with(
            command=self.mock_command, 
            source_file_path='/tmp/test.jsonl'
        )
        mock_scraper_instance.run.assert_called_once()
