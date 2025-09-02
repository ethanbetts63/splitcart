import unittest
import json
from unittest.mock import patch, MagicMock
from api.scrapers.store_scraper_iga import StoreScraperIga

class TestStoreScraperIga(unittest.TestCase):

    def setUp(self):
        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()
        self.scraper = StoreScraperIga(mock_command)

    @patch('requests.Session.get')
    def test_fetch_data_for_item_success(self, mock_get):
        """Test a successful fetch and parse of IGA store data from JSONP."""
        # Arrange: Create a realistic JSONP response structure
        store_info = {"storeId": 123, "storeName": "Test IGA"}
        store_data_attr = json.dumps(store_info)
        html_content = f'<div data-storedata="{store_data_attr}"></div>'
        json_payload = json.dumps({"content": html_content})
        jsonp_response = f"callback({json_payload});"

        mock_response = MagicMock()
        mock_response.text = jsonp_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = self.scraper.fetch_data_for_item(1)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], store_info)
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_data_for_item_request_error(self, mock_get):
        """Test that an empty list is returned on a request exception."""
        mock_get.side_effect = Exception("Network Error")
        result = self.scraper.fetch_data_for_item(1)
        self.assertEqual(result, [])

    def test_parse_and_clean_stores(self):
        """Test the parsing of the HTML content."""
        store_info1 = {"storeId": 1, "name": "IGA A", "distance": 1.2}
        store_info2 = {"storeId": 2, "name": "IGA B", "distance": 2.3}
        html_content = f'<div data-storedata=\'{json.dumps(store_info1)}\''></div><div data-storedata=\'{json.dumps(store_info2)}\''></div>'
        
        result = self.scraper.parse_and_clean_stores(html_content)

        self.assertEqual(len(result), 2)
        # The 'distance' key should be removed
        self.assertNotIn('distance', result[0])
        self.assertEqual(result[0]['name'], 'IGA A')
        self.assertEqual(result[1]['name'], 'IGA B')

    @patch('api.scrapers.store_scraper_iga.StoreCleanerIga')
    def test_clean_raw_data(self, MockStoreCleanerIga):
        """Test that the clean_raw_data method uses the StoreCleanerIga."""
        mock_cleaner_instance = MagicMock()
        mock_cleaner_instance.clean.return_value = {"cleaned": "data"}
        MockStoreCleanerIga.return_value = mock_cleaner_instance
        
        raw_data = {"storeId": 123, "storeName": "Test IGA"}
        result = self.scraper.clean_raw_data(raw_data)

        self.assertEqual(result, {"cleaned": "data"})
        MockStoreCleanerIga.assert_called_once_with(raw_data, self.scraper.company, unittest.mock.ANY)
        mock_cleaner_instance.clean.assert_called_once()

if __name__ == '__main__':
    unittest.main()
