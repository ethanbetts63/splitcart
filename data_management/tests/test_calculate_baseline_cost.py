from django.test import TestCase
from data_management.utils.cart_optimization.calculate_baseline_cost import calculate_baseline_cost

class CalculateBaselineCostTest(TestCase):
    def test_calculate_baseline_cost(self):
        # 1. Setup
        # Create a list of price slots. The new baseline logic calculates the
        # average price for each slot and sums them up.
        price_slots = [
            [
                {'product_id': 1, 'store_id': 101, 'price': 10.00},
                {'product_id': 1, 'store_id': 102, 'price': 11.00},
            ],
            [
                {'product_id': 2, 'store_id': 102, 'price': 20.00},
            ],
            [
                {'product_id': 3, 'store_id': 101, 'price': 30.00},
                {'product_id': 3, 'store_id': 103, 'price': 31.00},
            ]
        ]

        # Expected Logic:
        # Slot 1 Average: (10.00 + 11.00) / 2 = 10.50
        # Slot 2 Average: 20.00 / 1 = 20.00
        # Slot 3 Average: (30.00 + 31.00) / 2 = 30.50
        # Total Baseline Cost = 10.50 + 20.00 + 30.50 = 61.00

        # 2. Execute
        baseline_cost = calculate_baseline_cost(price_slots)

        # 3. Assert
        self.assertEqual(baseline_cost, 61.00)