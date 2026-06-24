import pytest
from unittest.mock import MagicMock, patch
import requests
from scraping.utils.product_scraping_utils.get_woolworths_categories import get_woolworths_categories


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.stdout.write = MagicMock()
    return cmd


class TestGetWoolworthsCategories:
    def _make_session_response(self, data):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = data
        return mock_resp

    def test_returns_list(self, command):
        api_data = {
            'Categories': [
                {'Children': []},
                {
                    'Description': 'Dairy',
                    'UrlFriendlyName': 'dairy',
                    'NodeId': '1000',
                    'Children': [
                        {'Description': 'Milk', 'UrlFriendlyName': 'milk', 'NodeId': '1001'},
                        {'Description': 'Cheese', 'UrlFriendlyName': 'cheese', 'NodeId': '1002'},
                    ],
                },
            ],
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        assert isinstance(result, list)

    def test_skips_specials_root(self, command):
        api_data = {
            'Categories': [
                {
                    'Description': 'Specials',
                    'UrlFriendlyName': 'specials',
                    'NodeId': '9998',
                    'Children': [
                        {'Description': 'Specials', 'UrlFriendlyName': 'specials', 'NodeId': '9999'},
                    ],
                },
                {
                    'Description': 'Dairy',
                    'UrlFriendlyName': 'dairy',
                    'NodeId': '1000',
                    'Children': [
                        {'Description': 'Milk', 'UrlFriendlyName': 'milk', 'NodeId': '1001'},
                    ],
                },
            ],
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        urls = [r['slug'] for r in result]
        assert 'specials' not in urls
        assert 'milk' in urls

    def test_raises_on_request_error(self, command):
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException('error')
            with pytest.raises(requests.exceptions.RequestException):
                get_woolworths_categories(command)

    def test_returns_empty_on_json_error(self, command):
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.side_effect = ValueError('bad json')
            mock_get.return_value = mock_resp
            result = get_woolworths_categories(command)
        assert result == []

    def test_returns_leaf_with_slug_node_id_and_path(self, command):
        api_data = {
            'Categories': [
                {'Children': []},
                {
                    'Description': 'Dairy, Eggs & Fridge',
                    'UrlFriendlyName': 'dairy-eggs-fridge',
                    'NodeId': '1000',
                    'Children': [
                        {
                            'Description': 'Yoghurt',
                            'UrlFriendlyName': 'yoghurt',
                            'NodeId': '1001',
                            'Children': [
                                {'Description': 'Kefir', 'UrlFriendlyName': 'kefir', 'NodeId': '1002'},
                            ],
                        },
                    ],
                },
            ],
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        assert {
            'slug': 'kefir',
            'node_id': '1002',
            'category_path': ['Dairy, Eggs & Fridge', 'Yoghurt', 'Kefir'],
        } in result

    def test_skips_merchandising_roots(self, command):
        api_data = {
            'Categories': [
                {
                    'Description': 'Lunch Box',
                    'UrlFriendlyName': 'lunch-box',
                    'NodeId': '2000',
                    'Children': [
                        {'Description': 'Drinks', 'UrlFriendlyName': 'drinks', 'NodeId': '2001'},
                    ],
                },
                {
                    'Description': 'Drinks',
                    'UrlFriendlyName': 'drinks',
                    'NodeId': '3000',
                    'Children': [
                        {'Description': 'Sports Drinks', 'UrlFriendlyName': 'sports-drinks', 'NodeId': '3001'},
                    ],
                },
            ],
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        assert [item['category_path'] for item in result] == [['Drinks', 'Sports Drinks']]
