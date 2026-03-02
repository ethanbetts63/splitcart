import pytest
from scraping.utils.product_scraping_utils.size_parser import parse_size



class TestParseSize:
    def test_grams(self):
        assert parse_size('500g') == (500.0, 'g')

    def test_kilograms_converts_to_grams(self):
        assert parse_size('1kg') == (1000.0, 'g')

    def test_fractional_kilograms(self):
        value, unit = parse_size('0.11kg')
        assert unit == 'g'
        assert value == pytest.approx(110.0)

    def test_millilitres(self):
        assert parse_size('250ml') == (250.0, 'ml')

    def test_litres_converts_to_millilitres(self):
        assert parse_size('1.5l') == (1500.0, 'ml')

    def test_one_litre(self):
        assert parse_size('1l') == (1000.0, 'ml')

    def test_pack(self):
        assert parse_size('6pk') == (6.0, 'pk')

    def test_each(self):
        assert parse_size('1ea') == (1.0, 'ea')

    def test_unknown_unit_returns_none(self):
        assert parse_size('500oz') is None

    def test_no_unit_returns_none(self):
        assert parse_size('500') is None

    def test_empty_string_returns_none(self):
        assert parse_size('') is None

    def test_just_text_returns_none(self):
        assert parse_size('abc') is None

    def test_large_value(self):
        result = parse_size('2000g')
        assert result == (2000.0, 'g')

    def test_decimal_grams(self):
        result = parse_size('1.5g')
        assert result == (1.5, 'g')
