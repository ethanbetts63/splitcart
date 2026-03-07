from data_management.utils.cart_optimization.calculate_best_single_store import calculate_best_single_store


def _opt(product_id, store_id, store_name, price, company_name='Coles', store_address='123 St'):
    return {
        'product_id': product_id,
        'store_id': store_id,
        'store_name': store_name,
        'company_name': company_name,
        'store_address': store_address,
        'price': price,
        'unit_price': price,
        'quantity': 1,
        'product_name': f'Product {product_id}',
        'brand': None,
        'size': '500g',
        'image_url': None,
    }


class TestCalculateBestSingleStore:
    def test_empty_slots_returns_none(self):
        assert calculate_best_single_store([], []) is None

    def test_single_store_is_returned(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_store(slots, original_cart)
        assert result is not None
        assert 'Store A' in result['shopping_plan']

    def test_store_with_more_products_wins(self):
        slots = [
            [_opt(1, 10, 'Store A', 5.00), _opt(1, 20, 'Store B', 5.00)],
            [_opt(2, 10, 'Store A', 3.00)],  # only Store A has product 2
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_store(slots, original_cart)
        assert 'Store A' in result['shopping_plan']
        assert result['items_found_count'] == 2

    def test_tie_in_coverage_picks_cheaper_store(self):
        # Both stores cover both products; Store B is cheaper
        slots = [
            [_opt(1, 10, 'Store A', 5.00), _opt(1, 20, 'Store B', 3.00)],
            [_opt(2, 10, 'Store A', 4.00), _opt(2, 20, 'Store B', 2.00)],
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_store(slots, original_cart)
        assert 'Store B' in result['shopping_plan']

    def test_result_contains_expected_keys(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_store(slots, original_cart)
        assert set(result.keys()) == {
            'max_stores', 'optimized_cost', 'savings',
            'shopping_plan', 'items_found_count', 'total_items_in_cart'
        }

    def test_max_stores_is_always_one(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_store(slots, original_cart)
        assert result['max_stores'] == 1

    def test_total_items_in_cart_reflects_original_cart_length(self):
        slots = [[_opt(1, 10, 'Store A', 5.00)]]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_store(slots, original_cart)
        assert result['total_items_in_cart'] == 2

    def test_optimized_cost_is_sum_of_cheapest_options(self):
        # Store A: product 1 at $5, product 2 at $4 (both cheapest for A)
        slots = [
            [_opt(1, 10, 'Store A', 5.00)],
            [_opt(2, 10, 'Store A', 4.00)],
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_store(slots, original_cart)
        assert result['optimized_cost'] == 9.00
