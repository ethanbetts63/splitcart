from data_management.utils.cart_optimization.calculate_baseline_cost import calculate_baseline_cost


def _opt(price):
    return {'price': price}


class TestCalculateBaselineCost:
    def test_empty_slots_returns_zero(self):
        assert calculate_baseline_cost([]) == 0

    def test_single_slot_single_option(self):
        slots = [[_opt(5.00)]]
        assert calculate_baseline_cost(slots) == 5.00

    def test_single_slot_multiple_options_returns_average(self):
        # average of 2.00 and 4.00 = 3.00
        slots = [[_opt(2.00), _opt(4.00)]]
        assert calculate_baseline_cost(slots) == 3.00

    def test_multiple_slots_sums_averages(self):
        # slot 1 avg = 3.00, slot 2 avg = 6.00 → total = 9.00
        slots = [
            [_opt(2.00), _opt(4.00)],
            [_opt(6.00)],
        ]
        assert calculate_baseline_cost(slots) == 9.00

    def test_three_options_average(self):
        # (3 + 6 + 9) / 3 = 6.0
        slots = [[_opt(3.00), _opt(6.00), _opt(9.00)]]
        assert calculate_baseline_cost(slots) == 6.00

    def test_single_zero_price(self):
        slots = [[_opt(0.00)]]
        assert calculate_baseline_cost(slots) == 0.00
