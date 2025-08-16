from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories
import requests

class GetWoolworthsCategoriesTest(TestCase):
    @patch('api.utils.scraper_utils.get_woolworths_categories.requests.get')
    def test_get_woolworths_categories_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Categories": [
                {},
                {
                    "Children": [
                        {"UrlFriendlyName": "cat1-slug", "NodeId": "cat1-id"},
                        {"UrlFriendlyName": "cat2-slug", "NodeId": "cat2-id"}
                    ]
                },
                {
                    "Children": [
                        {"UrlFriendlyName": "cat3-slug", "NodeId": "cat3-id"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        self.assertEqual(categories, [
            ("cat1-slug", "cat1-id"),
            ("cat2-slug", "cat2-id"),
            ("cat3-slug", "cat3-id")
        ])
        mock_get.assert_called_once()

    @patch('api.utils.scraper_utils.get_woolworths_categories.requests.get')
    def test_get_woolworths_categories_api_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test Error")
        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('api.utils.scraper_utils.get_woolworths_categories.requests.get')
    def test_get_woolworths_categories_json_decode_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('api.utils.scraper_utils.get_woolworths_categories.requests.get')
    def test_get_woolworths_categories_empty_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Categories": []}
        mock_get.return_value = mock_response
        categories = get_woolworths_categories()
        self.assertEqual(categories, [])
