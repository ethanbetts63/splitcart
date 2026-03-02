import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.product_scraping_utils.get_aldi_categories import _find_leaf_categories, get_aldi_categories


class TestFindLeafCategories:
    def test_empty_list(self):
        assert _find_leaf_categories([]) == []

    def test_single_leaf_node(self):
        nodes = [{'urlSlugText': 'dairy', 'key': 'cat-1', 'children': []}]
        result = _find_leaf_categories(nodes)
        assert result == [('dairy', 'cat-1')]

    def test_node_without_children_key(self):
        nodes = [{'urlSlugText': 'dairy', 'key': 'cat-1'}]
        result = _find_leaf_categories(nodes)
        assert result == [('dairy', 'cat-1')]

    def test_nested_tree_returns_only_leaves(self):
        nodes = [
            {
                'urlSlugText': 'food', 'key': 'cat-0', 'children': [
                    {'urlSlugText': 'dairy', 'key': 'cat-1', 'children': []},
                    {'urlSlugText': 'bakery', 'key': 'cat-2', 'children': []},
                ]
            }
        ]
        result = _find_leaf_categories(nodes)
        assert ('dairy', 'cat-1') in result
        assert ('bakery', 'cat-2') in result
        assert ('food', 'cat-0') not in result

    def test_deeply_nested_tree(self):
        nodes = [
            {'urlSlugText': 'top', 'key': 'k0', 'children': [
                {'urlSlugText': 'mid', 'key': 'k1', 'children': [
                    {'urlSlugText': 'leaf', 'key': 'k2', 'children': []}
                ]}
            ]}
        ]
        result = _find_leaf_categories(nodes)
        assert result == [('leaf', 'k2')]

    def test_node_missing_required_keys_excluded(self):
        nodes = [
            {'key': 'cat-1', 'children': []},   # missing urlSlugText
            {'urlSlugText': 'dairy', 'children': []},  # missing key
        ]
        result = _find_leaf_categories(nodes)
        assert result == []


class TestGetAldiCategories:
    def test_returns_empty_list_on_request_error(self):
        import requests
        command = MagicMock()
        session = MagicMock()
        session.get.side_effect = requests.exceptions.RequestException('Network error')
        with pytest.raises(requests.exceptions.RequestException):
            get_aldi_categories(command, 'G123', session)

    def test_returns_leaf_categories_from_api(self):
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.return_value = {
            'data': [
                {'urlSlugText': 'dairy', 'key': 'k1', 'children': []}
            ]
        }
        session.get.return_value.raise_for_status.return_value = None
        result = get_aldi_categories(command, 'G123', session)
        assert ('dairy', 'k1') in result

    def test_returns_empty_on_json_decode_error(self):
        import json
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.side_effect = json.JSONDecodeError('err', '', 0)
        session.get.return_value.raise_for_status.return_value = None
        result = get_aldi_categories(command, 'G123', session)
        assert result == []
