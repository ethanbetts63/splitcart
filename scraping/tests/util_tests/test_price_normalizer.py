import pytest
from scraping.utils.product_scraping_utils.price_normalizer import PriceNormalizer


class TestGetNormalizedKey:
    def test_key_with_both_ids(self):
        pn = PriceNormalizer({'product_id': 42, 'group_id': 7})
        assert pn.get_normalized_key() == '42-7'

    def test_key_without_product_id_returns_none(self):
        pn = PriceNormalizer({'group_id': 7})
        assert pn.get_normalized_key() is None

    def test_key_without_group_id_returns_none(self):
        pn = PriceNormalizer({'product_id': 42})
        assert pn.get_normalized_key() is None

    def test_empty_dict_returns_none(self):
        pn = PriceNormalizer({})
        assert pn.get_normalized_key() is None


class TestGetNormalizedUnitPrice:
    def test_from_numeric_value(self):
        pn = PriceNormalizer({'per_unit_price_value': 1.50})
        assert pn.get_normalized_unit_price() == 1.50

    def test_from_string_with_dollar_sign(self):
        pn = PriceNormalizer({'per_unit_price_string': '$1.68 per 100g'})
        assert pn.get_normalized_unit_price() == 1.68

    def test_numeric_value_takes_priority_over_string(self):
        pn = PriceNormalizer({
            'per_unit_price_value': 2.00,
            'per_unit_price_string': '$1.68 per 100g'
        })
        assert pn.get_normalized_unit_price() == 2.00

    def test_no_data_returns_none(self):
        pn = PriceNormalizer({})
        assert pn.get_normalized_unit_price() is None

    def test_empty_string_returns_none(self):
        pn = PriceNormalizer({'per_unit_price_string': ''})
        assert pn.get_normalized_unit_price() is None

    def test_string_without_number_returns_none(self):
        pn = PriceNormalizer({'per_unit_price_string': 'per kg'})
        assert pn.get_normalized_unit_price() is None


class TestGetNormalizedUnitMeasure:
    def test_from_measure_field_grams(self):
        pn = PriceNormalizer({'per_unit_price_measure': '100g'})
        assert pn.get_normalized_unit_measure() == ('g', 100.0)

    def test_from_measure_field_kg(self):
        pn = PriceNormalizer({'per_unit_price_measure': '1kg'})
        assert pn.get_normalized_unit_measure() == ('kg', 1.0)

    def test_from_measure_field_litres(self):
        pn = PriceNormalizer({'per_unit_price_measure': '1l'})
        result = pn.get_normalized_unit_measure()
        assert result is not None
        unit, qty = result
        assert unit == 'l'
        assert qty == 1.0

    def test_from_string_field(self):
        pn = PriceNormalizer({'per_unit_price_string': '$1.68 per 100g'})
        result = pn.get_normalized_unit_measure()
        assert result == ('g', 100.0)

    def test_price_stripped_before_unit_search(self):
        # "$3.35 per 1l" — without stripping $3.35, the leading number would be
        # misread as the quantity instead of the price
        pn = PriceNormalizer({'per_unit_price_string': '$3.35 per 1l'})
        result = pn.get_normalized_unit_measure()
        assert result is not None
        unit, qty = result
        assert unit == 'l'
        assert qty == 1.0

    def test_measure_field_prioritized_over_string(self):
        pn = PriceNormalizer({
            'per_unit_price_measure': '1kg',
            'per_unit_price_string': '$1.68 per 100g'
        })
        unit, qty = pn.get_normalized_unit_measure()
        assert unit == 'kg'
        assert qty == 1.0

    def test_no_data_returns_none(self):
        pn = PriceNormalizer({})
        assert pn.get_normalized_unit_measure() is None

    def test_each_unit(self):
        pn = PriceNormalizer({'per_unit_price_measure': '1ea'})
        result = pn.get_normalized_unit_measure()
        assert result is not None
        unit, _ = result
        assert unit == 'each'
