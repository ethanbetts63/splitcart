import pytest
from unittest.mock import MagicMock
from scraping.utils.product_scraping_utils.get_iga_categories import _find_leaf_categories, get_iga_categories


class TestFindLeafCategories:
    def test_empty_list(self):
        assert _find_leaf_categories([]) == []

    def test_single_leaf_node(self):
        nodes = [{'displayName': 'Dairy', 'identifier': 'cat-dairy', 'children': []}]
        result = _find_leaf_categories(nodes)
        assert result == [{'displayName': 'Dairy', 'identifier': 'cat-dairy'}]

    def test_nested_tree_returns_only_leaves(self):
        nodes = [
            {
                'displayName': 'Food', 'identifier': 'food', 'children': [
                    {'displayName': 'Dairy', 'identifier': 'dairy', 'children': []},
                    {'displayName': 'Bakery', 'identifier': 'bakery', 'children': []},
                ]
            }
        ]
        result = _find_leaf_categories(nodes)
        assert {'displayName': 'Dairy', 'identifier': 'dairy'} in result
        assert {'displayName': 'Bakery', 'identifier': 'bakery'} in result
        assert not any(r.get('displayName') == 'Food' for r in result)

    def test_node_missing_required_keys_excluded(self):
        nodes = [
            {'identifier': 'cat-1', 'children': []},   # missing displayName
            {'displayName': 'Dairy', 'children': []},  # missing identifier
        ]
        result = _find_leaf_categories(nodes)
        assert result == []


class TestGetIgaCategories:
    def test_returns_leaf_categories_from_api(self):
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.return_value = {
            'children': [
                {'displayName': 'Dairy', 'identifier': 'dairy', 'children': []}
            ]
        }
        session.get.return_value.raise_for_status.return_value = None
        result = get_iga_categories(command, 'iga-001', session)
        assert {'displayName': 'Dairy', 'identifier': 'dairy'} in result

    def test_returns_empty_on_request_error(self):
        import requests
        command = MagicMock()
        session = MagicMock()
        session.get.side_effect = requests.exceptions.RequestException('error')
        result = get_iga_categories(command, 'iga-001', session)
        assert result == []

    def test_returns_empty_on_json_error(self):
        import json
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.side_effect = json.JSONDecodeError('e', '', 0)
        session.get.return_value.raise_for_status.return_value = None
        result = get_iga_categories(command, 'iga-001', session)
        assert result == []
