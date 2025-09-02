import unittest
from unittest.mock import patch, MagicMock
from api.scrapers.store_scraper_woolworths2 import StoreScraperWoolworths2

class TestStoreScraperWoolworths2(unittest.TestCase):

    def setUp(self):
        # The scraper requires a 'command' object with a 'stdout' attribute.
        # We can create a mock object for this.
        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()
        self.scraper = StoreScraperWoolworths2(mock_command)

    @patch('requests.Session.get')
    def test_fetch_data_for_item_success(self, mock_get):
        """Test a successful API call that returns a list of stores."""
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_stores = [{'FulfilmentStoreId': '1234', 'Description': 'Test Store'}]
        mock_response.json.return_value = mock_stores
        mock_get.return_value = mock_response

        # Call the method we are testing
        result = self.scraper.fetch_data_for_item('2000')

        # Assertions
        self.assertEqual(result, mock_stores)
        mock_get.assert_called_once_with(
            self.scraper.api_url,
            params={"postcode": "2000"},
            timeout=60
        )
        # Ensure no error messages were written
        self.scraper.command.stdout.write.assert_not_called()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_http_error(self, mock_get):
        """Test an API call that results in an HTTP error."""
        # Configure the mock to simulate an HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response

        # Call the method
        result = self.scraper.fetch_data_for_item('9999')

        # Assertions
        self.assertEqual(result, [])
        # Check that an error message was printed to the mocked stdout
        self.scraper.command.stdout.write.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_empty_response(self, mock_get):
        """Test a successful API call that returns an empty list of stores."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [] # Empty list
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item('1234')

        self.assertEqual(result, [])
        self.scraper.command.stdout.write.assert_not_called()

if __name__ == '__main__':
    unittest.main()
