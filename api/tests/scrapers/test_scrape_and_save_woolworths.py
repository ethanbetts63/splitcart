
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from api.scrapers.woolworths_scraper import scrape_and_save_woolworths_data

class TestScrapeAndSaveWoolworths(unittest.TestCase):

    def setUp(self):
        self.company = "Woolworths"
        self.store_id = "1101"
        self.store_name = "Test Woolworths Store"
        self.state = "NSW"
        self.categories_to_fetch = ["fruit-veg"]
        self.timestamp = datetime(2025, 8, 23)

    @patch('api.scrapers.scrape_and_save_woolworths.requests.post')
    @patch('api.scrapers.scrape_and_save_woolworths.clean_raw_data_woolworths')
    @patch('api.scrapers.scrape_and_save_woolworths.JsonlWriter')
    def test_successful_scrape(self, MockJsonlWriter, MockCleanRawDataWoolworths, MockRequestsPost):
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Bundles': [
                {
                    'Products': [
                        {
                            "Stockcode": 136341,
                            "Name": "Woolworths Bird's Eye Chilli Hot",
                            "Price": 0.14,
                            "PackageSize": "each",
                            "IsAvailable": True,
                            "IsOnSpecial": False,
                            "WasPrice": 0.14,
                            "Brand": "Woolworths",
                            "DisplayName": "Woolworths Bird's Eye Chilli Hot each"
                        }
                    ]
                }
            ]
        }
        MockRequestsPost.return_value = mock_response

        # Mock clean_raw_data_woolworths
        MockCleanRawDataWoolworths.return_value = {
            'products': [{'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}],
            'metadata': {}
        }

        # Mock JsonlWriter
        mock_jsonl_writer = MagicMock()
        MockJsonlWriter.return_value = mock_jsonl_writer
        mock_jsonl_writer.write_product.return_value = True

        scrape_and_save_woolworths_data(
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            categories_to_fetch=self.categories_to_fetch
        )

        # Assertions
        self.assertEqual(MockRequestsPost.call_count, 1)
        MockCleanRawDataWoolworths.assert_called_once()
        mock_jsonl_writer.open.assert_called_once()
        mock_jsonl_writer.write_product.assert_called_once_with({'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}, {})
        mock_jsonl_writer.finalize.assert_called_once_with(True)

if __name__ == '__main__':
    unittest.main()
