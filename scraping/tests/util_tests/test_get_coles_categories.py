import pytest
from scraping.utils.product_scraping_utils.get_coles_categories import get_coles_categories


class TestGetColesCategories:
    def test_returns_list(self):
        result = get_coles_categories()
        assert isinstance(result, list)

    def test_not_empty(self):
        result = get_coles_categories()
        assert len(result) > 0

    def test_contains_expected_categories(self):
        result = get_coles_categories()
        assert 'meat-seafood' in result
        assert 'dairy-eggs-fridge' in result
        assert 'fruit-vegetables' in result

    def test_all_items_are_strings(self):
        result = get_coles_categories()
        assert all(isinstance(c, str) for c in result)

    def test_returns_same_list_each_call(self):
        assert get_coles_categories() == get_coles_categories()
