
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data

class TestScrapeAndSaveAldi(unittest.TestCase):

    def setUp(self):
        self.company = "Aldi"
        self.store_id = "ALDI:1234"
        self.store_name = "Test Aldi Store"
        self.state = "NSW"
        self.categories_to_fetch = ["bakery"]
        self.timestamp = datetime(2025, 8, 23)

    @patch('api.scrapers.scrape_and_save_aldi.requests.get')
    @patch('api.scrapers.scrape_and_save_aldi.clean_raw_data_aldi')
    @patch('api.scrapers.scrape_and_save_aldi.JsonlWriter')
    def test_successful_scrape(self, MockJsonlWriter, MockCleanRawDataAldi, MockRequestsGet):
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    "sku": "000000000000200998",
                    "name": "Chocolate Chip Brioche Milk Rolls 8 Pack 280g",
                    "brandName": "BON APPETIT",
                    "price": {
                        "amount": 469,
                    },
                    "sellingSize": "280 g"
                }
            ]
        }
        MockRequestsGet.return_value = mock_response

        # Mock clean_raw_data_aldi
        MockCleanRawDataAldi.return_value = {
            'products': [{'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}],
            'metadata': {}
        }

        # Mock JsonlWriter
        mock_jsonl_writer = MagicMock()
        MockJsonlWriter.return_value = mock_jsonl_writer
        mock_jsonl_writer.write_product.return_value = True

        scrape_and_save_aldi_data(
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            categories_to_fetch=self.categories_to_fetch
        )

        # Assertions
        self.assertEqual(MockRequestsGet.call_count, 1)
        MockCleanRawDataAldi.assert_called_once()
        mock_jsonl_writer.open.assert_called_once()
        mock_jsonl_writer.write_product.assert_called_once_with({'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}, {})
        mock_jsonl_writer.finalize.assert_called_once_with(True)

if __name__ == '__main__':
    unittest.main()
