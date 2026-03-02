import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.BaseStoreCleaner import BaseStoreCleaner


class ConcreteStoreCleaner(BaseStoreCleaner):
    """Minimal concrete subclass for testing base class methods."""
    FIELD_MAP = {
        'store_id': 'id',
        'store_name': 'name',
        'postcode': 'address.postcode',
    }

    @property
    def field_map(self):
        return self.FIELD_MAP

    def _transform_store(self):
        return {k: self._get_value(k) for k in self.field_map}


@pytest.fixture
def raw_store():
    return {
        'id': 'S001',
        'name': 'Test Store',
        'address': {'postcode': '2000'},
    }


@pytest.fixture
def cleaner(raw_store):
    return ConcreteStoreCleaner(raw_store, 'Test', datetime(2024, 6, 15))


class TestGetValue:
    def test_flat_field(self, cleaner):
        assert cleaner._get_value('store_id') == 'S001'

    def test_nested_dot_notation(self, cleaner):
        assert cleaner._get_value('postcode') == '2000'

    def test_missing_field_returns_none(self, cleaner):
        assert cleaner._get_value('unknown_field') is None

    def test_none_map_entry_returns_none(self, cleaner):
        cleaner.FIELD_MAP['store_id'] = None
        assert cleaner._get_value('store_id') is None
        cleaner.FIELD_MAP['store_id'] = 'id'  # restore


class TestCleanPostcode:
    def test_valid_4_digit_postcode(self, cleaner):
        assert cleaner._clean_postcode('2000') == '2000'

    def test_3_digit_postcode_gets_leading_zero(self, cleaner):
        assert cleaner._clean_postcode('800') == '0800'

    def test_non_numeric_returns_none(self, cleaner):
        assert cleaner._clean_postcode('ABCD') is None

    def test_too_short_returns_none(self, cleaner):
        assert cleaner._clean_postcode('20') is None

    def test_too_long_returns_none(self, cleaner):
        assert cleaner._clean_postcode('20001') is None

    def test_non_string_type_returns_none(self, cleaner):
        assert cleaner._clean_postcode(2000) is None

    def test_leading_whitespace_is_stripped_before_check(self, cleaner):
        # _clean_postcode strips before length/digit check, so ' 2000' → '2000' → valid
        assert cleaner._clean_postcode(' 2000') == '2000'


class TestClean:
    def test_returns_metadata_and_store_data(self, cleaner):
        result = cleaner.clean()
        assert 'metadata' in result
        assert 'store_data' in result

    def test_metadata_contains_company(self, cleaner):
        result = cleaner.clean()
        assert result['metadata']['company'] == 'Test'

    def test_metadata_contains_scraped_date(self, cleaner):
        result = cleaner.clean()
        assert result['metadata']['scraped_date'] == '2024-06-15'

    def test_store_data_contains_mapped_fields(self, cleaner):
        result = cleaner.clean()
        assert result['store_data']['store_id'] == 'S001'
        assert result['store_data']['store_name'] == 'Test Store'
