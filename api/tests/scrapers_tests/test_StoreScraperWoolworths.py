import unittest
from unittest.mock import patch, MagicMock
from api.scrapers.store_scraper_woolworths import StoreScraperWoolworths

class TestStoreScraperWoolworths1(unittest.TestCase):

    def setUp(self):
        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()
        self.scraper = StoreScraperWoolworths(mock_command)

    @patch('requests.Session.get')
    def test_fetch_data_for_item_success(self, mock_get):
        """Test a successful API call that returns stores."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_stores = {"Stores": [{"StoreNo": 5678, "Name": "Test Geo Store"}]}
        mock_response.json.return_value = mock_stores
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item((-33.87, 151.20))

        self.assertEqual(result, mock_stores["Stores"])
        mock_get.assert_called_once()
        self.scraper.command.stdout.write.assert_not_called()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_http_error(self, mock_get):
        """Test an API call that results in an HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item((-40.0, 140.0))

        self.assertEqual(result, [])
        self.scraper.command.stdout.write.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_no_stores(self, mock_get):
        """Test a successful API call that returns no stores."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Stores": []} # Empty list of stores
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item((0.0, 0.0))

        self.assertEqual(result, [])
        self.scraper.command.stdout.write.assert_not_called()

if __name__ == '__main__':
    unittest.main()
