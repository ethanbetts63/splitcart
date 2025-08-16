from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.database_updating_utils.get_woolworths_substitutes import get_woolworths_substitutes

class GetWoolworthsSubstitutesTest(TestCase):
    @patch('api.utils.database_updating_utils.get_woolworths_substitutes.requests.post')
    def test_get_woolworths_substitutes_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Bundles": [
                {
                    "Products": [
                        {"Stockcode": "123", "Name": "Product A"},
                        {"Stockcode": "456", "Name": "Product B"}
                    ]
                }
            ]
        }
        mock_post.return_value = mock_response

        product_id = "test_product_id"
        session = MagicMock()
        
        substitutes = get_woolworths_substitutes(product_id, session)

        self.assertEqual(len(substitutes), 2)
        self.assertEqual(substitutes[0]['Stockcode'], '123')
        self.assertEqual(substitutes[1]['Stockcode'], '456')

    @patch('api.utils.database_updating_utils.get_woolworths_substitutes.requests.post')
    def test_get_woolworths_substitutes_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        product_id = "test_product_id"
        session = MagicMock()
        
        substitutes = get_woolworths_substitutes(product_id, session)
        self.assertEqual(substitutes, [])

    @patch('api.utils.database_updating_utils.get_woolworths_substitutes.requests.post')
    def test_get_woolworths_substitutes_json_decode_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        product_id = "test_product_id"
        session = MagicMock()
        
        substitutes = get_woolworths_substitutes(product_id, session)
        self.assertEqual(substitutes, [])

    @patch('api.utils.database_updating_utils.get_woolworths_substitutes.requests.post')
    def test_get_woolworths_substitutes_empty_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Bundles": []}
        mock_post.return_value = mock_response

        product_id = "test_product_id"
        session = MagicMock()
        
        substitutes = get_woolworths_substitutes(product_id, session)
        self.assertEqual(substitutes, [])
