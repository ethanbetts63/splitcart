
from django.test import TestCase
from data_management.utils.cart_optimization.calculate_optimized_cost import calculate_optimized_cost

class CalculateOptimizedCostTest(TestCase):
    def test_calculate_optimized_cost_multiple_slots(self):
        # 1. Setup
        # Create a list of price slots that mimics the output of build_price_slots
        # This represents a cart with 2 items, each available at 2 stores.
        price_slots = [
            [
                {'product_id': 1, 'product_name': 'Product A', 'brand': 'Brand X', 'store_id': 101, 'store_name': 'Store 1', 'price': 10.00, 'quantity': 1},
                {'product_id': 1, 'product_name': 'Product A', 'brand': 'Brand X', 'store_id': 102, 'store_name': 'Store 2', 'price': 11.00, 'quantity': 1},
            ],
            [
                {'product_id': 2, 'product_name': 'Product B', 'brand': 'Brand Y', 'store_id': 101, 'store_name': 'Store 1', 'price': 20.00, 'quantity': 1},
                {'product_id': 2, 'product_name': 'Product B', 'brand': 'Brand Y', 'store_id': 102, 'store_name': 'Store 2', 'price': 21.00, 'quantity': 1},
            ]
        ]
        max_stores = 2

        # 2. Execute
        optimized_cost, shopping_plan, _ = calculate_optimized_cost(price_slots, max_stores)

        # 3. Assert
        # The shopping plan should contain items from both slots.
        # The optimal solution should be Product A from Store 1 and Product B from Store 1.
        self.assertIsNotNone(shopping_plan)
        self.assertEqual(optimized_cost, 30.00)

        # Check that the shopping plan contains 2 items in total
        total_items = sum(len(items) for items in shopping_plan.values())
        self.assertEqual(total_items, 2)

        # Check the specific items in the plan
        self.assertEqual(len(shopping_plan['Store 1']), 2)
        self.assertEqual(len(shopping_plan['Store 2']), 0)
        self.assertEqual(shopping_plan['Store 1'][0]['product'], 'Brand X Product A')
        self.assertEqual(shopping_plan['Store 1'][1]['product'], 'Brand Y Product B')
