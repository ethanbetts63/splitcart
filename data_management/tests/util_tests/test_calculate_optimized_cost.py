from data_management.utils.cart_optimization.calculate_optimized_cost import calculate_optimized_cost


def _opt(product_id, store_id, store_name, price, quantity=1, company_name='Coles', store_address='123 St'):
    return {
        'product_id': product_id,
        'store_id': store_id,
        'store_name': store_name,
        'company_name': company_name,
        'store_address': store_address,
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
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        cost, plan, _ = calculate_optimized_cost(slots, max_stores=1)
        assert cost == 5.00

    def test_picks_cheapest_option_across_stores(self):
        slots = [[
            _opt(1, 10, 'Store A', 8.00),
            _opt(1, 20, 'Store B', 3.00),
        ]]
        cost, plan, _ = calculate_optimized_cost(slots, max_stores=2)
        assert abs(cost - 3.00) < 0.01

    def test_max_stores_constraint_respected(self):
        # Two slots, two stores. max_stores=1 forces picking one store.
        # Store A has product 1 at $5, Store B has product 2 at $2.
        # Store A also has product 2 at $3; Store B also has product 1 at $6.
        # With max_stores=1, cheapest single store is Store A: 5+3=8
        slots = [
            [_opt(1, 10, 'Store A', 5.00), _opt(1, 20, 'Store B', 6.00)],
            [_opt(2, 10, 'Store A', 3.00), _opt(2, 20, 'Store B', 2.00)],
        ]
        cost, plan, _ = calculate_optimized_cost(slots, max_stores=1)
        # Both products must come from one store
        store_names_used = [name for name, data in plan.items() if data['items']]
        assert len(store_names_used) == 1

    def test_returns_shopping_plan_with_items(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        _, plan, _ = calculate_optimized_cost(slots, max_stores=1)
        assert 'Store A' in plan
        assert len(plan['Store A']['items']) == 1

    def test_plan_item_contains_expected_fields(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        _, plan, _ = calculate_optimized_cost(slots, max_stores=1)
        item = plan['Store A']['items'][0]
        assert set(item.keys()) == {'product_name', 'brand', 'size', 'price', 'quantity', 'image_url'}

    def test_infeasible_returns_none_triple(self):
        # max_stores=0 makes it infeasible
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        cost, plan, choices = calculate_optimized_cost(slots, max_stores=0)
        assert cost is None
        assert plan is None
        assert choices is None

    def test_splits_across_two_stores_when_beneficial(self):
        # Store A cheapest for product 1, Store B cheapest for product 2
        # With max_stores=2 the solver should use both
        slots = [
            [_opt(1, 10, 'Store A', 2.00), _opt(1, 20, 'Store B', 9.00)],
            [_opt(2, 10, 'Store A', 9.00), _opt(2, 20, 'Store B', 2.00)],
        ]
        cost, plan, _ = calculate_optimized_cost(slots, max_stores=2)
        assert abs(cost - 4.00) < 0.01
