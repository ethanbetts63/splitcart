import unittest
import json
from unittest.mock import MagicMock
from scraping.scrapers.store_scraper_coles import StoreScraperColes

class TestStoreScraperColes(unittest.TestCase):

    def setUp(self):
        # Mock the command object that the scraper expects
        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()
        
        # Instantiate the scraper
        self.scraper = StoreScraperColes(mock_command)
        
        # Manually create a mock driver and assign it to the scraper instance.
        # This allows us to test methods that use the driver without running the
        # scraper's real setup() method, which tries to open a browser.
        self.mock_driver = MagicMock()
        self.scraper.driver = self.mock_driver

    def test_fetch_data_for_item_success(self):
        """Test a successful api call via the mocked Selenium driver."""
        # Configure the mock driver to return a successful api response
        mock_api_response = {
            "data": {
                "stores": {
                    "results": [
                        {"store": {"id": "COL:1234", "name": "Coles Test Store"}}
                    ]
                }
            }
        }
        # The scraper expects the driver to return a JSON string
        self.mock_driver.execute_async_script.return_value = json.dumps(mock_api_response)

        # Call the method we are testing
        results = self.scraper.fetch_data_for_item((-37.81, 144.96))

        # Assert that the data was correctly extracted
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['store']['name'], "Coles Test Store")
        self.mock_driver.execute_async_script.assert_called_once()

    def test_fetch_data_for_item_api_error(self):
        """Test the handling of an api error returned within the JSON response."""
        # Configure the mock driver to return a response containing an error
        mock_api_response = {"error": "Something went wrong"}
        self.mock_driver.execute_async_script.return_value = json.dumps(mock_api_response)

        # Check that our method correctly raises an exception when it sees the error
        with self.assertRaises(Exception) as cm:
            self.scraper.fetch_data_for_item((-37.81, 144.96))
        
        self.assertIn("api Error: Something went wrong", str(cm.exception))

if __name__ == '__main__':
    unittest.main()