from django.test import TestCase
from unittest.mock import patch, Mock
from requests.exceptions import RequestException
from api.utils.management_utils.get_woolworths_categories import get_woolworths_categories

class GetWoolworthsCategoriesTest(TestCase):

    @patch('requests.get')
    def test_successful_category_fetch(self, mock_get):
        """Test that categories are fetched and parsed correctly on success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Categories": [
                {"Name": "Specials"}, # This one should be skipped
                {
                    "Name": "Fresh Food",
                    "Children": [
                        {"UrlFriendlyName": "fruit-veg", "NodeId": "123"},
                        {"UrlFriendlyName": "meat", "NodeId": "456"}
                    ]
                },
                {
                    "Name": "Pantry",
                    "Children": [
                        {"UrlFriendlyName": "pasta", "NodeId": "789"}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        self.assertEqual(categories, [
            ("fruit-veg", "123"),
            ("meat", "456"),
            ("pasta", "789")
        ])
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_empty_categories_response(self, mock_get):
        """Test handling of an empty 'Categories' list in the response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Categories": []}
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('requests.get')
    def test_missing_categories_key(self, mock_get):
        """Test handling of a missing 'Categories' key in the response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "some other data"}
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('requests.get')
    def test_request_exception_handling(self, mock_get):
        """Test handling of a RequestException during API call."""
        mock_get.side_effect = RequestException("Network error")

        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('requests.get')
    def test_json_decode_error_handling(self, mock_get):
        """Test handling of a JSONDecodeError during API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        self.assertEqual(categories, [])

    @patch('requests.get')
    def test_partial_children_data(self, mock_get):
        """Test handling of partial data in children categories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Categories": [
                {"Name": "Dummy First Category"}, # Added dummy
                {
                    "Name": "Fresh Food",
                    "Children": [
                        {"UrlFriendlyName": "fruit-veg"}, # Missing NodeId
                        {"NodeId": "456"} # Missing UrlFriendlyName
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        categories = get_woolworths_categories()
        # Expecting only valid tuples to be added
        self.assertEqual(categories, [("fruit-veg", None), (None, "456")])
