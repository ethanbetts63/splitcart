
import json
from django.test import TestCase
from unittest.mock import patch, Mock
from requests.exceptions import RequestException
from scraping.utils.product_scraping_utils.get_aldi_categories import get_aldi_categories, _find_leaf_categories

class GetAldiCategoriesTest(TestCase):

    # --- Tests for _find_leaf_categories ---
    def test_find_leaf_categories_basic(self):
        nodes = [
            {'name': 'Dairy', 'children': [
                {'name': 'Milk', 'urlSlugText': 'milk', 'key': '1'},
                {'name': 'Cheese', 'urlSlugText': 'cheese', 'key': '2'}
            ]},
            {'name': 'Bakery', 'urlSlugText': 'bakery', 'key': '3'}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        self.assertEqual(sorted(leaf_categories), sorted([('milk', '1'), ('cheese', '2'), ('bakery', '3')]))

    def test_find_leaf_categories_nested(self):
        nodes = [
            {'name': 'Food', 'children': [
                {'name': 'Fresh', 'children': [
                    {'name': 'Fruit', 'urlSlugText': 'fruit', 'key': 'A'},
                    {'name': 'Veg', 'urlSlugText': 'veg', 'key': 'B'}
                ]},
                {'name': 'Pantry', 'urlSlugText': 'pantry', 'key': 'C'}
            ]}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        self.assertEqual(sorted(leaf_categories), sorted([('fruit', 'A'), ('veg', 'B'), ('pantry', 'C')]))

    def test_find_leaf_categories_empty_input(self):
        self.assertEqual(_find_leaf_categories([]), [])

    def test_find_leaf_categories_missing_keys(self):
        nodes = [
            {'name': 'Dairy', 'children': [
                {'name': 'Milk', 'urlSlugText': 'milk'}, # Missing key
                {'name': 'Cheese', 'key': '2'} # Missing urlSlugText
            ]},
            {'name': 'Bakery', 'urlSlugText': 'bakery', 'key': '3'}
        ]
        leaf_categories = _find_leaf_categories(nodes)
        # Only the fully formed leaf node should be included
        self.assertEqual(leaf_categories, [('bakery', '3')])

    # --- Tests for get_aldi_categories ---
    @patch('requests.Session.get')
    def test_get_aldi_categories_success(self, mock_get):
        """Test successful fetching and parsing of ALDI categories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'name': 'Category 1', 'children': [
                    {'name': 'SubCat A', 'urlSlugText': 'subcat-a', 'key': 'keyA'},
                    {'name': 'SubCat B', 'urlSlugText': 'subcat-b', 'key': 'keyB'}
                ]},
                {'name': 'Category 2', 'urlSlugText': 'cat-2', 'key': 'keyC'}
            ]
        }
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        mock_command = Mock()
        categories = get_aldi_categories(mock_command, 'store123', session)

        self.assertEqual(sorted(categories), sorted([('subcat-a', 'keyA'), ('subcat-b', 'keyB'), ('cat-2', 'keyC')]))
        mock_get.assert_called_once_with('https://api.aldi.com.au/v2/product-category-tree?serviceType=walk-in&servicePoint=store123', timeout=60)

    @patch('requests.Session.get')
    def test_get_aldi_categories_empty_data(self, mock_get):
        """Test handling of empty 'data' in API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        mock_command = Mock()
        categories = get_aldi_categories(mock_command, 'store123', session)

        self.assertEqual(categories, [])

    @patch('requests.Session.get')
    def test_get_aldi_categories_request_exception(self, mock_get):
        """Test handling of requests.exceptions.RequestException."""
        mock_get.side_effect = RequestException("Network error")

        session = Mock()
        session.get = mock_get
        mock_command = Mock()
        categories = get_aldi_categories(mock_command, 'store123', session)

        self.assertEqual(categories, [])

    @patch('requests.Session.get')
    def test_get_aldi_categories_json_decode_error(self, mock_get):
        """Test handling of json.JSONDecodeError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response

        session = Mock()
        session.get = mock_get
        mock_command = Mock()
        categories = get_aldi_categories(mock_command, 'store123', session)

        self.assertEqual(categories, [])
