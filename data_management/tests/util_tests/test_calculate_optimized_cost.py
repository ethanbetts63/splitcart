from data_management.utils.cart_optimization.calculate_optimized_cost import calculate_optimized_cost


def _opt(product_id, company_id, company_name, price, quantity=1):
    return {
        'product_id': product_id,
        'company_id': company_id,
        'company_name': company_name,
        'price': price,
        'unit_price': price,
        'quantity': quantity,
        'product_name': f'Product {product_id}',
        'brand': None,
        'size': '500g',
        'image_url': None,
    }


class TestCalculateOptimizedCost:
    def test_single_slot_single_option_returns_that_price(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        cost, plan, _ = calculate_optimized_cost(slots, max_companies=1)
        assert cost == 5.00

    def test_picks_cheapest_option_across_companies(self):
        slots = [[
            _opt(1, 10, 'Company A', 8.00),
            _opt(1, 20, 'Company B', 3.00),
        ]]
        cost, plan, _ = calculate_optimized_cost(slots, max_companies=2)
        assert abs(cost - 3.00) < 0.01

    def test_max_companies_constraint_respected(self):
        slots = [
            [_opt(1, 10, 'Company A', 5.00), _opt(1, 20, 'Company B', 6.00)],
            [_opt(2, 10, 'Company A', 3.00), _opt(2, 20, 'Company B', 2.00)],
        ]
        cost, plan, _ = calculate_optimized_cost(slots, max_companies=1)
        company_names_used = [name for name, data in plan.items() if data['items']]
        assert len(company_names_used) == 1

    def test_returns_shopping_plan_with_items(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        _, plan, _ = calculate_optimized_cost(slots, max_companies=1)
        assert 'Company A' in plan
        assert len(plan['Company A']['items']) == 1

    def test_plan_item_contains_expected_fields(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        _, plan, _ = calculate_optimized_cost(slots, max_companies=1)
        item = plan['Company A']['items'][0]
        assert set(item.keys()) == {'product_name', 'brand', 'size', 'price', 'quantity', 'image_url'}

    def test_infeasible_returns_none_triple(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        cost, plan, choices = calculate_optimized_cost(slots, max_companies=0)
        assert cost is None
        assert plan is None
        assert choices is None

    def test_splits_across_two_companies_when_beneficial(self):
        slots = [
            [_opt(1, 10, 'Company A', 2.00), _opt(1, 20, 'Company B', 9.00)],
            [_opt(2, 10, 'Company A', 9.00), _opt(2, 20, 'Company B', 2.00)],
        ]
        cost, plan, _ = calculate_optimized_cost(slots, max_companies=2)
        assert abs(cost - 4.00) < 0.01
