
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from api.scrapers.iga_scraper import scrape_and_save_iga_data

class TestScrapeAndSaveIga(unittest.TestCase):

    def setUp(self):
        self.company = "IGA"
        self.store_id = "IGA:1234"
        self.store_name = "Test IGA Store"
        self.state = "NSW"
        self.categories_to_fetch = ["coconut-milk"]
        self.timestamp = datetime(2025, 8, 23)

    @patch('api.scrapers.scrape_and_save_iga.requests.post')
    @patch('api.scrapers.scrape_and_save_iga.clean_raw_data_iga')
    @patch('api.scrapers.scrape_and_save_iga.JsonlWriter')
    def test_successful_scrape(self, MockJsonlWriter, MockCleanRawDataIga, MockRequestsPost):
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'pageProps': {
                'products': [
                    {
                        "productId": "31218",
                        "name": "Australia's Own Organic Coconut Milk Unsweetened",
                        "brand": "Australia's Own",
                        "priceNumeric": 3.35,
                        "unitOfSize": {
                            "size": 1,
                            "type": "litre"
                        },
                        "available": True
                    }
                ]
            }
        }
        MockRequestsPost.return_value = mock_response

        # Mock clean_raw_data_iga
        MockCleanRawDataIga.return_value = {
            'products': [{'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}],
            'metadata': {}
        }

        # Mock JsonlWriter
        mock_jsonl_writer = MagicMock()
        MockJsonlWriter.return_value = mock_jsonl_writer
        mock_jsonl_writer.write_product.return_value = True

        scrape_and_save_iga_data(
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            categories_to_fetch=self.categories_to_fetch
        )

        # Assertions
        self.assertEqual(MockRequestsPost.call_count, 1)
        MockCleanRawDataIga.assert_called_once()
        mock_jsonl_writer.open.assert_called_once()
        mock_jsonl_writer.write_product.assert_called_once_with({'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}, {})
        mock_jsonl_writer.finalize.assert_called_once_with(True)

if __name__ == '__main__':
    unittest.main()
