
import json
from django.test import TestCase
from unittest.mock import patch, Mock
from requests.exceptions import RequestException
from api.utils.scraper_utils.get_iga_categories import get_iga_categories, _find_leaf_categories

class GetIgaCategoriesTest(TestCase):

    # --- Tests for _find_leaf_categories ---
    def test_find_leaf_categories_basic(self):
        nodes = [
            {'displayName': 'Dairy', 'children': [
                {'displayName': 'Milk', 'identifier': 'milk-id'},
                {'displayName': 'Cheese', 'identifier': 'cheese-id'}
            ]},
            {'displayName': 'Bakery', 'identifier': 'bakery-id'}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        expected = [
            {'displayName': 'Milk', 'identifier': 'milk-id'},
            {'displayName': 'Cheese', 'identifier': 'cheese-id'},
            {'displayName': 'Bakery', 'identifier': 'bakery-id'}
        ]
        self.assertEqual(sorted(leaf_categories, key=lambda x: x['identifier']), sorted(expected, key=lambda x: x['identifier']))

    def test_find_leaf_categories_nested(self):
        nodes = [
            {'displayName': 'Food', 'children': [
                {'displayName': 'Fresh', 'children': [
                    {'displayName': 'Fruit', 'identifier': 'fruit-id'},
                    {'displayName': 'Veg', 'identifier': 'veg-id'}
                ]},
                {'displayName': 'Pantry', 'identifier': 'pantry-id'}
            ]}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        expected = [
            {'displayName': 'Fruit', 'identifier': 'fruit-id'},
            {'displayName': 'Veg', 'identifier': 'veg-id'},
            {'displayName': 'Pantry', 'identifier': 'pantry-id'}
        ]
        self.assertEqual(sorted(leaf_categories, key=lambda x: x['identifier']), sorted(expected, key=lambda x: x['identifier']))

    def test_find_leaf_categories_empty_input(self):
        self.assertEqual(_find_leaf_categories([]), [])

    def test_find_leaf_categories_missing_keys(self):
        nodes = [
            {'displayName': 'Dairy', 'children': [
                {'displayName': 'Milk'}, # Missing identifier
                {'identifier': 'cheese-id'} # Missing displayName
            ]},
            {'displayName': 'Bakery', 'identifier': 'bakery-id'}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        # Only the fully formed leaf node should be included
        expected = [{'displayName': 'Bakery', 'identifier': 'bakery-id'}]
        self.assertEqual(leaf_categories, expected)

    # --- Tests for get_iga_categories ---
    @patch('requests.Session.get')
    def test_get_iga_categories_success(self, mock_get):
        """Test successful fetching and parsing of IGA categories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'children': [
                {'displayName': 'Category 1', 'children': [
                    {'displayName': 'SubCat A', 'identifier': 'subcat-a-id'},
                    {'displayName': 'SubCat B', 'identifier': 'subcat-b-id'}
                ]},
                {'displayName': 'Category 2', 'identifier': 'cat-2-id'}
            ]
        }
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        categories = get_iga_categories('store123', session, 'session456')

        expected = [
            {'displayName': 'SubCat A', 'identifier': 'subcat-a-id'},
            {'displayName': 'SubCat B', 'identifier': 'subcat-b-id'},
            {'displayName': 'Category 2', 'identifier': 'cat-2-id'}
        ]
        self.assertEqual(sorted(categories, key=lambda x: x['identifier']), sorted(expected, key=lambda x: x['identifier']))
        mock_get.assert_called_once_with('https://www.igashop.com.au/api/storefront/stores/store123/categoryHierarchy?sessionId=session456', timeout=60)

    @patch('requests.Session.get')
    def test_get_iga_categories_empty_children_data(self, mock_get):
        """Test handling of empty 'children' in API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'children': []}
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        categories = get_iga_categories('store123', session, 'session456')

        self.assertEqual(categories, [])

    @patch('requests.Session.get')
    def test_get_iga_categories_request_exception(self, mock_get):
        """Test handling of requests.exceptions.RequestException."""
        mock_get.side_effect = RequestException("Network error")

        session = Mock()
        session.get = mock_get
        categories = get_iga_categories('store123', session, 'session456')

        self.assertEqual(categories, [])

    @patch('requests.Session.get')
    def test_get_iga_categories_json_decode_error(self, mock_get):
        """Test handling of json.JSONDecodeError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        categories = get_iga_categories('store123', session, 'session456')

        self.assertEqual(categories, [])
