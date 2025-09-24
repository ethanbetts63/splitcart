import unittest
from unittest.mock import patch, MagicMock
from scraping.scrapers.store_scraper_aldi import StoreScraperAldi

class TestStoreScraperAldi(unittest.TestCase):

    def setUp(self):
        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()
        self.scraper = StoreScraperAldi(mock_command)

    @patch('requests.Session.get')
    def test_fetch_data_for_item_success(self, mock_get):
        """Test a successful data_management call that returns store data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_stores_data = {"data": [{"id": "ALDI-1", "name": "ALDI Test Store"}]}
        mock_response.json.return_value = mock_stores_data
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item((-33.87, 151.20))

        self.assertEqual(result, mock_stores_data["data"])
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_http_error(self, mock_get):
        """Test an data_management call that results in an HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response

        result = self.scraper.fetch_data_for_item((-40.0, 140.0))

        self.assertEqual(result, [])
        self.scraper.command.stdout.write.assert_called_once()

    @patch('scraping.scrapers.store_scraper_aldi.StoreCleanerAldi')
    def test_clean_raw_data(self, MockStoreCleanerAldi):
        """Test that the clean_raw_data method uses the StoreCleanerAldi."""
        mock_cleaner_instance = MagicMock()
        mock_cleaner_instance.clean.return_value = {"cleaned": "data"}
        MockStoreCleanerAldi.return_value = mock_cleaner_instance
        
        raw_data = {"id": "ALDI-1", "name": "ALDI Test Store"}
        result = self.scraper.clean_raw_data(raw_data)

        self.assertEqual(result, {"cleaned": "data"})
        MockStoreCleanerAldi.assert_called_once_with(raw_data, self.scraper.company, unittest.mock.ANY)
        mock_cleaner_instance.clean.assert_called_once()

if __name__ == '__main__':
    unittest.main()
