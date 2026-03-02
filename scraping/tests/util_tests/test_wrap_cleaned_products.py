import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.wrap_cleaned_products import wrap_cleaned_products


@pytest.fixture
def products():
    return [{'name': 'Milk', 'price_current': 2.50}]


@pytest.fixture
def timestamp():
    return datetime(2024, 6, 15, 10, 30, 0)


class TestWrapCleanedProducts:
    def test_returns_metadata_and_products_keys(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'Woolworths Sydney', 'WOW123', 'nsw', timestamp)
        assert 'metadata' in result
        assert 'products' in result

    def test_company_is_lowercased(self, products, timestamp):
        result = wrap_cleaned_products(products, 'WOOLWORTHS', 'Woolworths Sydney', 'WOW123', 'nsw', timestamp)
        assert result['metadata']['company'] == 'woolworths'

    def test_company_is_stripped(self, products, timestamp):
        result = wrap_cleaned_products(products, '  Woolworths  ', 'Woolworths Sydney', 'WOW123', 'nsw', timestamp)
        assert result['metadata']['company'] == 'woolworths'

    def test_store_name_is_lowercased(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'WOOLWORTHS SYDNEY', 'WOW123', 'nsw', timestamp)
        assert result['metadata']['store_name'] == 'woolworths sydney'

    def test_state_is_lowercased(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'Woolworths Sydney', 'WOW123', 'NSW', timestamp)
        assert result['metadata']['state'] == 'nsw'

    def test_store_id_is_stripped(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'Woolworths Sydney', '  WOW123  ', 'nsw', timestamp)
        assert result['metadata']['store_id'] == 'WOW123'

    def test_scraped_date_is_iso_format(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'Woolworths Sydney', 'WOW123', 'nsw', timestamp)
        assert result['metadata']['scraped_date'] == '2024-06-15'

    def test_products_list_passed_through(self, products, timestamp):
        result = wrap_cleaned_products(products, 'Woolworths', 'Woolworths Sydney', 'WOW123', 'nsw', timestamp)
        assert result['products'] == products

    def test_empty_products_list(self, timestamp):
        result = wrap_cleaned_products([], 'Coles', 'Coles Test', 'COL001', 'vic', timestamp)
        assert result['products'] == []
