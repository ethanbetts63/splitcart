import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.BaseDataCleaner import BaseDataCleaner


class ConcreteDataCleaner(BaseDataCleaner):
    """Minimal concrete subclass for testing base class methods."""
    FIELD_MAP = {
        'sku': 'id',
        'name': 'name',
        'price_current': 'pricing.now',
        'nested_list_field': 'items.0.value',
    }

    @property
    def field_map(self):
        return self.FIELD_MAP

    def _transform_product(self, raw_product: dict) -> dict:
        return {k: self._get_value(raw_product, k) for k in self.field_map}


@pytest.fixture
def cleaner():
    return ConcreteDataCleaner(
        raw_product_list=[],
        company='Test',
        store_name='Test Store',
        store_id='TST001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


class TestGetValue:
    def test_flat_field(self, cleaner):
        raw = {'id': '123', 'name': 'Milk'}
        assert cleaner._get_value(raw, 'sku') == '123'

    def test_nested_dot_notation(self, cleaner):
        raw = {'pricing': {'now': 2.50}}
        assert cleaner._get_value(raw, 'price_current') == 2.50

    def test_list_index_access(self, cleaner):
        raw = {'items': [{'value': 'first'}]}
        assert cleaner._get_value(raw, 'nested_list_field') == 'first'

    def test_missing_top_level_key_returns_none(self, cleaner):
        assert cleaner._get_value({}, 'sku') is None

    def test_missing_nested_key_returns_none(self, cleaner):
        raw = {'pricing': {}}
        assert cleaner._get_value(raw, 'price_current') is None

    def test_empty_string_in_nested_path_returns_none(self, cleaner):
        # The whitespace-to-None coercion only applies in the dot-notation path
        raw = {'pricing': {'now': '   '}}
        assert cleaner._get_value(raw, 'price_current') is None

    def test_none_field_map_entry_returns_none(self, cleaner):
        # If the field map maps to None, returns None
        cleaner.FIELD_MAP['sku'] = None
        assert cleaner._get_value({'id': '123'}, 'sku') is None
        cleaner.FIELD_MAP['sku'] = 'id'  # restore

    def test_out_of_range_list_index_returns_none(self, cleaner):
        raw = {'items': []}  # empty list, index 0 doesn't exist
        assert cleaner._get_value(raw, 'nested_list_field') is None


class TestCalculatePriceInfo:
    def test_on_special(self, cleaner):
        result = cleaner._calculate_price_info(current_price=2.00, was_price=3.00)
        assert result['is_on_special'] is True
        assert result['price_save_amount'] == 1.00
        assert result['price_current'] == 2.00
        assert result['price_was'] == 3.00

    def test_not_on_special_no_was_price(self, cleaner):
        result = cleaner._calculate_price_info(current_price=3.00, was_price=None)
        assert result['is_on_special'] is False
        assert result['price_save_amount'] is None

    def test_was_price_equal_to_current_not_on_special(self, cleaner):
        result = cleaner._calculate_price_info(current_price=3.00, was_price=3.00)
        assert result['is_on_special'] is False

    def test_none_prices(self, cleaner):
        result = cleaner._calculate_price_info(current_price=None, was_price=None)
        assert result['is_on_special'] is False
        assert result['price_save_amount'] is None

    def test_save_amount_rounded_to_2dp(self, cleaner):
        result = cleaner._calculate_price_info(current_price=1.99, was_price=3.00)
        assert result['price_save_amount'] == 1.01


class TestCleanCategoryPath:
    def test_titles_each_part(self, cleaner):
        result = cleaner._clean_category_path(['dairy', 'milk'])
        assert result == ['Dairy', 'Milk']

    def test_strips_whitespace(self, cleaner):
        result = cleaner._clean_category_path(['  dairy  '])
        assert result == ['Dairy']

    def test_filters_out_none(self, cleaner):
        result = cleaner._clean_category_path([None, 'dairy', None])
        assert result == ['Dairy']

    def test_filters_out_empty_string(self, cleaner):
        result = cleaner._clean_category_path(['', 'dairy'])
        assert result == ['Dairy']

    def test_empty_list_returns_empty(self, cleaner):
        result = cleaner._clean_category_path([])
        assert result == []

    def test_none_input_returns_empty(self, cleaner):
        result = cleaner._clean_category_path(None)
        assert result == []


class TestGetStandardizedUnitPriceInfo:
    def test_per_100g_converted_to_per_1kg(self, cleaner):
        price_data = {
            'per_unit_price_value': 1.50,
            'per_unit_price_measure': '100g',
        }
        result = cleaner._get_standardized_unit_price_info(price_data)
        assert result['unit_of_measure'] == '1kg'
        assert result['unit_price'] == pytest.approx(15.00)

    def test_per_100ml_converted_to_per_1l(self, cleaner):
        price_data = {
            'per_unit_price_value': 0.50,
            'per_unit_price_measure': '100ml',
        }
        result = cleaner._get_standardized_unit_price_info(price_data)
        assert result['unit_of_measure'] == '1l'
        assert result['unit_price'] == pytest.approx(5.00)

    def test_per_1kg_normalizes_correctly(self, cleaner):
        price_data = {
            'per_unit_price_value': 8.00,
            'per_unit_price_measure': '1kg',
        }
        result = cleaner._get_standardized_unit_price_info(price_data)
        assert result['unit_of_measure'] == '1kg'
        assert result['unit_price'] == pytest.approx(8.00)

    def test_per_1l_normalizes_correctly(self, cleaner):
        price_data = {
            'per_unit_price_value': 2.50,
            'per_unit_price_measure': '1l',
        }
        result = cleaner._get_standardized_unit_price_info(price_data)
        assert result['unit_of_measure'] == '1l'
        assert result['unit_price'] == pytest.approx(2.50)

    def test_no_price_data_returns_none(self, cleaner):
        result = cleaner._get_standardized_unit_price_info({})
        assert result['unit_price'] is None
        assert result['unit_of_measure'] is None


class TestIsValidProduct:
    def test_none_product_is_invalid(self, cleaner):
        assert cleaner._is_valid_product(None) is False

    def test_empty_dict_is_valid(self, cleaner):
        # Base implementation only checks not None
        assert cleaner._is_valid_product({}) is True

    def test_non_empty_dict_is_valid(self, cleaner):
        assert cleaner._is_valid_product({'id': '1'}) is True
