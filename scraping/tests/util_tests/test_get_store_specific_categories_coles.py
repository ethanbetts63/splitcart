import pytest
from unittest.mock import MagicMock
import requests
from scraping.utils.product_scraping_utils.get_store_specific_categories_coles import get_store_specific_categories


def _make_session(data):
    session = MagicMock()
    session.post.return_value.raise_for_status.return_value = None
    session.post.return_value.json.return_value = data
    return session


class TestGetStoreSpecificCategoriesColes:
    def test_returns_list(self):
        session = _make_session({'data': {'menuItems': {'items': []}}})
        result = get_store_specific_categories(session)
        assert isinstance(result, list)

    def test_extracts_seo_tokens_with_products(self):
        data = {
            'data': {
                'menuItems': {
                    'items': [
                        {'seoToken': 'meat-seafood', 'productCount': 100, 'childItems': []},
                        {'seoToken': 'specials', 'productCount': 0, 'childItems': []},  # 0 products — excluded
                    ]
                }
            }
        }
        session = _make_session(data)
        result = get_store_specific_categories(session)
        assert 'meat-seafood' in result
        assert 'specials' not in result

    def test_extracts_child_item_slugs(self):
        data = {
            'data': {
                'menuItems': {
                    'items': [
                        {
                            'seoToken': 'food',
                            'productCount': 5,
                            'childItems': [
                                {'seoToken': 'dairy', 'productCount': 20, 'childItems': None},
                            ]
                        },
                    ]
                }
            }
        }
        session = _make_session(data)
        result = get_store_specific_categories(session)
        assert 'food' in result
        assert 'dairy' in result

    def test_returns_empty_on_request_error(self):
        session = MagicMock()
        session.post.side_effect = requests.exceptions.RequestException('error')
        result = get_store_specific_categories(session)
        assert result == []

    def test_returns_empty_on_unexpected_error(self):
        session = MagicMock()
        session.post.return_value.json.side_effect = Exception('unexpected')
        session.post.return_value.raise_for_status.return_value = None
        result = get_store_specific_categories(session)
        assert result == []
