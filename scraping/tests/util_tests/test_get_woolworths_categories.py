import pytest
import json
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
                {'Children': []},  # index 0 (Specials) — skipped
                {
                    'Children': [
                        {'UrlFriendlyName': 'dairy', 'NodeId': '1001'},
                        {'UrlFriendlyName': 'bakery', 'NodeId': '1002'},
                    ]
                }
            ]
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        assert isinstance(result, list)

    def test_skips_first_category_specials(self, command):
        # The first category is Specials and must be skipped (index 0)
        api_data = {
            'Categories': [
                {
                    'Children': [
                        {'UrlFriendlyName': 'specials', 'NodeId': '9999'},
                    ]
                },
                {
                    'Children': [
                        {'UrlFriendlyName': 'dairy', 'NodeId': '1001'},
                    ]
                }
            ]
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        urls = [r[0] for r in result]
        assert 'specials' not in urls
        assert 'dairy' in urls

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

    def test_returns_tuple_of_url_and_node_id(self, command):
        api_data = {
            'Categories': [
                {'Children': []},
                {
                    'Children': [
                        {'UrlFriendlyName': 'dairy', 'NodeId': '1001'},
                    ]
                }
            ]
        }
        with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
            mock_get.return_value = self._make_session_response(api_data)
            result = get_woolworths_categories(command)
        assert ('dairy', '1001') in result
