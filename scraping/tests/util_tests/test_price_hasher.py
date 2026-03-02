import pytest
from decimal import Decimal
from scraping.utils.product_scraping_utils.price_hasher import generate_price_hash


class TestGeneratePriceHash:
    def _base_data(self, **overrides):
        data = {
            'price_current': 2.50,
            'price_was': None,
            'unit_price': None,
            'unit_of_measure': None,
            'per_unit_price_string': None,
            'is_on_special': False,
        }
        data.update(overrides)
        return data

    def test_same_data_produces_same_hash(self):
        data = self._base_data(price_current=2.50)
        assert generate_price_hash(data) == generate_price_hash(data)

    def test_different_price_produces_different_hash(self):
        data1 = self._base_data(price_current=2.50)
        data2 = self._base_data(price_current=3.00)
        assert generate_price_hash(data1) != generate_price_hash(data2)

    def test_different_special_flag_produces_different_hash(self):
        data1 = self._base_data(is_on_special=False)
        data2 = self._base_data(is_on_special=True)
        assert generate_price_hash(data1) != generate_price_hash(data2)

    def test_decimal_fields_are_handled(self):
        data = self._base_data(price_current=Decimal('2.50'))
        result = generate_price_hash(data)
        assert isinstance(result, str)
        assert len(result) == 32

    def test_returns_32_char_hex_string(self):
        result = generate_price_hash(self._base_data())
        assert len(result) == 32
        assert all(c in '0123456789abcdef' for c in result)

    def test_empty_dict_produces_valid_hash(self):
        result = generate_price_hash({})
        assert isinstance(result, str)
        assert len(result) == 32

    def test_extra_keys_are_ignored(self):
        data1 = self._base_data()
        data2 = self._base_data()
        data2['irrelevant_key'] = 'some_value'
        assert generate_price_hash(data1) == generate_price_hash(data2)

    def test_unit_price_string_affects_hash(self):
        data1 = self._base_data(per_unit_price_string='$1.25 per 100g')
        data2 = self._base_data(per_unit_price_string='$2.50 per 100g')
        assert generate_price_hash(data1) != generate_price_hash(data2)
