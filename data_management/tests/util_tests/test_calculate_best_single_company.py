from data_management.utils.cart_optimization.calculate_best_single_company import calculate_best_single_company


def _opt(product_id, company_id, company_name, price):
    return {
        'product_id': product_id,
        'company_id': company_id,
        'company_name': company_name,
        'price': price,
        'unit_price': price,
        'quantity': 1,
        'product_name': f'Product {product_id}',
        'brand': None,
        'size': '500g',
        'image_url': None,
    }


class TestCalculateBestSingleCompany:
    def test_empty_slots_returns_none(self):
        assert calculate_best_single_company([], []) is None

    def test_single_company_is_returned(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_company(slots, original_cart)
        assert result is not None
        assert 'Company A' in result['shopping_plan']

    def test_company_with_more_products_wins(self):
        slots = [
            [_opt(1, 10, 'Company A', 5.00), _opt(1, 20, 'Company B', 5.00)],
            [_opt(2, 10, 'Company A', 3.00)],
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_company(slots, original_cart)
        assert 'Company A' in result['shopping_plan']
        assert result['items_found_count'] == 2

    def test_tie_in_coverage_picks_cheaper_company(self):
        slots = [
            [_opt(1, 10, 'Company A', 5.00), _opt(1, 20, 'Company B', 3.00)],
            [_opt(2, 10, 'Company A', 4.00), _opt(2, 20, 'Company B', 2.00)],
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_company(slots, original_cart)
        assert 'Company B' in result['shopping_plan']

    def test_result_contains_expected_keys(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_company(slots, original_cart)
        assert set(result.keys()) == {
            'max_companies', 'optimized_cost', 'savings',
            'shopping_plan', 'items_found_count', 'total_items_in_cart'
        }

    def test_max_companies_is_always_one(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        original_cart = [[{'product_id': 1}]]
        result = calculate_best_single_company(slots, original_cart)
        assert result['max_companies'] == 1

    def test_total_items_in_cart_reflects_original_cart_length(self):
        slots = [[_opt(1, 10, 'Company A', 5.00)]]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_company(slots, original_cart)
        assert result['total_items_in_cart'] == 2

    def test_optimized_cost_is_sum_of_cheapest_options(self):
        slots = [
            [_opt(1, 10, 'Company A', 5.00)],
            [_opt(2, 10, 'Company A', 4.00)],
        ]
        original_cart = [[{'product_id': 1}], [{'product_id': 2}]]
        result = calculate_best_single_company(slots, original_cart)
        assert result['optimized_cost'] == 9.00
