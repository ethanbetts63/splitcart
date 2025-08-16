import requests
from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.substitution_utils.fetch_substitutes_from_api import fetch_substitutes_from_api

class FetchSubstitutesFromApiTest(TestCase):
    @patch('api.utils.substitution_utils.fetch_substitutes_from_api.requests.Session.get')
    def test_fetch_substitutes_from_api_success(self, mock_session_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Result": [
                {
                    "SubstituteProductList": [
                        {"Product": {"Stockcode": "sub1"}},
                        {"Product": {"Stockcode": "sub2"}}
                    ]
                }
            ]
        }
        mock_session_get.return_value = mock_response

        session = requests.Session()
        substitutes = fetch_substitutes_from_api("test_product_id", session)

        self.assertEqual(len(substitutes), 2)
        self.assertEqual(substitutes[0]['Stockcode'], 'sub1') # Corrected assertion
        self.assertEqual(substitutes[1]['Stockcode'], 'sub2') # Corrected assertion
        mock_session_get.assert_called_once()

    @patch('api.utils.substitution_utils.fetch_substitutes_from_api.requests.Session.get')
    def test_fetch_substitutes_from_api_no_result(self, mock_session_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Result": []}
        mock_session_get.return_value = mock_response

        session = requests.Session()
        substitutes = fetch_substitutes_from_api("test_product_id", session)
        self.assertEqual(substitutes, [])

    @patch('api.utils.substitution_utils.fetch_substitutes_from_api.requests.Session.get')
    def test_fetch_substitutes_from_api_empty_substitute_list(self, mock_session_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Result": [{"SubstituteProductList": []}]}
        mock_session_get.return_value = mock_response

        session = requests.Session()
        substitutes = fetch_substitutes_from_api("test_product_id", session)
        self.assertEqual(substitutes, [])

    @patch('api.utils.substitution_utils.fetch_substitutes_from_api.requests.Session.get')
    def test_fetch_substitutes_from_api_request_exception(self, mock_session_get):
        mock_session_get.side_effect = requests.exceptions.RequestException("Test Error")
        session = requests.Session()
        with self.assertRaises(requests.exceptions.RequestException):
            fetch_substitutes_from_api("test_product_id", session)

    @patch('api.utils.substitution_utils.fetch_substitutes_from_api.requests.Session.get')
    def test_fetch_substitutes_from_api_value_error(self, mock_session_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session_get.return_value = mock_response
        session = requests.Session()
        with self.assertRaises(ValueError):
            fetch_substitutes_from_api("test_product_id", session)