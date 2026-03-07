from decimal import Decimal
from data_management.utils.price_comparer import PriceComparer


class TestPriceComparer:
    def setup_method(self):
        self.comparer = PriceComparer(overlap_threshold=0.98)

    def test_empty_map_a_returns_false(self):
        assert self.comparer.compare({}, {1: Decimal('2.00')}) is False

    def test_empty_map_b_returns_false(self):
        assert self.comparer.compare({1: Decimal('2.00')}, {}) is False

    def test_both_empty_returns_false(self):
        assert self.comparer.compare({}, {}) is False

    def test_no_common_products_returns_false(self):
        assert self.comparer.compare({1: Decimal('2.00')}, {2: Decimal('2.00')}) is False

    def test_perfect_match_returns_true(self):
        prices = {1: Decimal('2.00'), 2: Decimal('3.50'), 3: Decimal('1.00')}
        assert self.comparer.compare(prices, prices.copy()) is True

    def test_below_threshold_returns_false(self):
        a = {i: Decimal('2.00') for i in range(100)}
        b = {i: Decimal('2.00') for i in range(100)}
        b[0] = Decimal('9.99')  # 99/100 = 0.99 → below 0.98? No, 0.99 >= 0.98 → True
        # To get below 0.98, change 3 values → 97/100 = 0.97
        b[1] = Decimal('9.99')
        b[2] = Decimal('9.99')
        assert self.comparer.compare(a, b) is False

    def test_exactly_at_threshold_returns_true(self):
        # 98 out of 100 matching = exactly 0.98
        a = {i: Decimal('2.00') for i in range(100)}
        b = {i: Decimal('2.00') for i in range(100)}
        b[0] = Decimal('9.99')
        b[1] = Decimal('9.99')
        assert self.comparer.compare(a, b) is True

    def test_only_common_products_are_compared(self):
        # Store A has products 1, 2, 3 all at $2
        # Store B has products 1, 2 at $2 and product 4 at $9 (not in A)
        a = {1: Decimal('2.00'), 2: Decimal('2.00'), 3: Decimal('2.00')}
        b = {1: Decimal('2.00'), 2: Decimal('2.00'), 4: Decimal('9.00')}
        # Common: 1 and 2, both match → 100% → True
        assert self.comparer.compare(a, b) is True

    def test_custom_lower_threshold(self):
        comparer = PriceComparer(overlap_threshold=0.5)
        a = {1: Decimal('2.00'), 2: Decimal('3.00')}
        b = {1: Decimal('2.00'), 2: Decimal('9.00')}
        # 1/2 = 0.5 → exactly at threshold → True
        assert comparer.compare(a, b) is True

    def test_single_matching_product(self):
        a = {1: Decimal('5.00')}
        b = {1: Decimal('5.00')}
        assert self.comparer.compare(a, b) is True

    def test_single_non_matching_product(self):
        a = {1: Decimal('5.00')}
        b = {1: Decimal('6.00')}
        assert self.comparer.compare(a, b) is False
