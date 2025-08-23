
import unittest
from unittest.mock import patch, Mock, MagicMock
import json
from bs4 import BeautifulSoup

# The module to be tested
from api.scrapers import scrape_and_save_coles

class TestScrapeAndSaveColes(unittest.TestCase):

    @patch('api.scrapers.scrape_and_save_coles.webdriver.Chrome')
    @patch('api.scrapers.scrape_and_save_coles.ChromeDriverManager')
    @patch('api.scrapers.scrape_and_save_coles.requests.Session')
    @patch('api.scrapers.scrape_and_save_coles.JsonlWriter')
    @patch('api.scrapers.scrape_and_save_coles.time.sleep') # To speed up test
    def test_scrape_and_save_coles_data(self, mock_sleep, mock_jsonl_writer, mock_session, mock_driver_manager, mock_chrome):

        # --- Setup Mocks ---

        # Mock Selenium WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # Mock Requests Session
        mock_requests_session = MagicMock()
        mock_session.return_value = mock_requests_session

        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Construct the __NEXT_DATA__ JSON
        next_data = {
            "props": {
                "pageProps": {
                    "initStoreId": "1234",
                    "searchResults": {
                        "noOfResults": 1,
                        "pageSize": 48,
                        "results": [
                            {
                                "_type": "PRODUCT",
                                "id": 3942620,
                                "name": "Graze Lamb Extra Trim Cutlets",
                                "brand": "Coles",
                                "description": "COLES GRAZE LAMB EXTRA TRIM CUTLETS 7 X 5",
                                "size": "approx. 300g",
                                "availability": True,
                                "pricing": {
                                    "now": 12.00,
                                    "was": 14.10,
                                    "unit": {"price": 40.00, "ofMeasureUnits": "kg"}
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        mock_response.text = f"""
        <html>
            <body>
                <script id="__NEXT_DATA__" type="application/json">
                {json.dumps(next_data)}
                </script>
            </body>
        </html>
        """
        mock_requests_session.get.return_value = mock_response

        # Mock JsonlWriter
        mock_writer_instance = MagicMock()
        mock_jsonl_writer.return_value = mock_writer_instance

        # --- Call the function ---
        scrape_and_save_coles.scrape_and_save_coles_data(
            company="coles",
            store_id="COL:1234",
            store_name="Test Store",
            state="NSW",
            categories_to_fetch=["meat-seafood"]
        )

        # --- Assertions ---

        # Check that the browser was initialized and quit
        mock_chrome.assert_called_once()
        mock_driver.quit.assert_called_once()

        # Check that requests.get was called for the category
        mock_requests_session.get.assert_called_with("https://www.coles.com.au/browse/meat-seafood?page=1", timeout=30)

        # Check that the JsonlWriter was used correctly
        mock_jsonl_writer.assert_called_with("coles", "test-store-1234", "NSW")
        mock_writer_instance.open.assert_called_once()
        
        # Check that write_product was called
        self.assertTrue(mock_writer_instance.write_product.called)
        
        # Check the content of what was written
        # The data passed to write_product is a (product, metadata) tuple
        args, kwargs = mock_writer_instance.write_product.call_args
        written_product, written_metadata = args
        
        self.assertEqual(written_product['name'], 'Graze Lamb Extra Trim Cutlets')
        self.assertEqual(written_product['brand'], 'Coles')
        self.assertEqual(written_product['price_current'], 12.00)

        mock_writer_instance.finalize.assert_called_with(True)


if __name__ == '__main__':
    unittest.main()
