import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data

class TestScrapeAndSaveColes(unittest.TestCase):

    def setUp(self):
        self.company = "Coles"
        self.store_id = "COL:1234"
        self.store_name = "Test Coles Store"
        self.state = "NSW"
        self.categories_to_fetch = ["fresh-produce/fruit"]
        self.timestamp = datetime(2025, 8, 23)

    @patch('api.scrapers.scrape_and_save_coles.webdriver.Chrome')
    @patch('api.scrapers.scrape_and_save_coles.ChromeService')
    @patch('api.scrapers.scrape_and_save_coles.ChromeDriverManager')
    @patch('api.scrapers.scrape_and_save_coles.WebDriverWait')
    @patch('api.scrapers.scrape_and_save_coles.requests.Session')
    @patch('api.scrapers.scrape_and_save_coles.BeautifulSoup')
    @patch('api.scrapers.scrape_and_save_coles.json.loads')
    @patch('api.scrapers.scrape_and_save_coles.clean_raw_data_coles')
    @patch('api.scrapers.scrape_and_save_coles.JsonlWriter')
    def test_successful_scrape(self, MockJsonlWriter, MockCleanRawDataColes, MockJsonLoads, MockBeautifulSoup, MockRequestsSession, MockWebDriverWait, MockChromeDriverManager, MockChromeService, MockChrome):
        # Mock Selenium setup
        mock_driver = MagicMock()
        MockChrome.return_value = mock_driver
        mock_driver.get_cookies.return_value = [{'name': 'cookie1', 'value': 'value1'}]

        # Mock WebDriverWait
        mock_wait = MagicMock()
        MockWebDriverWait.return_value = mock_wait
        mock_wait.until.return_value = True

        # Mock requests session
        mock_session = MagicMock()
        MockRequestsSession.return_value = mock_session
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response
        mock_response.text = "<html><script id=\"__NEXT_DATA__\">{}</script></html>"

        # Mock json.loads
        MockJsonLoads.return_value = {
            "props": {
                "pageProps": {
                    "initStoreId": "1234",
                    "searchResults": {
                        "results": [{"id": 1, "name": "Product A"}],
                        "noOfResults": 1,
                        "pageSize": 48
                    }
                }
            }
        }

        # Mock clean_raw_data_coles
        MockCleanRawDataColes.return_value = {
            'products': [{'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}],
            'metadata': {}
        }

        # Mock JsonlWriter
        mock_jsonl_writer = MagicMock()
        MockJsonlWriter.return_value = mock_jsonl_writer
        mock_jsonl_writer.write_product.return_value = True

        scrape_and_save_coles_data(
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            categories_to_fetch=self.categories_to_fetch
        )

        # Assertions
        mock_driver.get.assert_called_once_with("https://www.coles.com.au")
        mock_driver.add_cookie.assert_called_once_with({'name': 'fulfillmentStoreId', 'value': '1234'})
        mock_driver.refresh.assert_called_once()
        mock_driver.quit.assert_called_once()

        mock_session.get.assert_called_once_with("https://www.coles.com.au/browse/fresh-produce/fruit?page=1", timeout=30)
        MockBeautifulSoup.assert_called_once()
        MockJsonLoads.assert_called_once()
        MockCleanRawDataColes.assert_called_once()
        mock_jsonl_writer.open.assert_called_once()
        mock_jsonl_writer.write_product.assert_called_once_with({'name': 'cleaned product a', 'normalized_name_brand_size': 'normalized_a'}, {})
        mock_jsonl_writer.finalize.assert_called_once_with(True)

if __name__ == '__main__':
    unittest.main()