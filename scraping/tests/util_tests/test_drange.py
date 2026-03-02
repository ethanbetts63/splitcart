import pytest
from scraping.utils.shop_scraping_utils.drange import drange


class TestDrange:
    def test_integer_steps(self):
        result = list(drange(1, 3, 1))
        assert result == [1, 2, 3]

    def test_float_steps(self):
        result = list(drange(0, 1, 0.5))
        assert pytest.approx(result) == [0, 0.5, 1.0]

    def test_single_value_range(self):
        result = list(drange(5, 5, 1))
        assert result == [5]

    def test_empty_range_start_exceeds_stop(self):
        result = list(drange(10, 5, 1))
        assert result == []

    def test_start_stop_step_produces_correct_count(self):
        result = list(drange(-2, 2, 1))
        assert result == [-2, -1, 0, 1, 2]
