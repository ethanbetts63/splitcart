
from django.test import TestCase
from data_management.utils.cart_optimization.calculate_baseline_cost import calculate_baseline_cost
from companies.tests.test_helpers.model_factories import StoreFactory

class CalculateBaselineCostTest(TestCase):
    def test_calculate_baseline_cost(self):
        # 1. Setup
        # Create stores
        store1 = StoreFactory(id=101, store_name='Store 1')
        store2 = StoreFactory(id=102, store_name='Store 2')
        store3 = StoreFactory(id=103, store_name='Store 3')
        stores = [store1, store2, store3]

        # Create a list of price slots
        # Product 1: Cheaper at Store 1
        # Product 2: Only at Store 2
        # Product 3: Cheaper at Store 1
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
        # Store 1 stocks 2 items (Product 1, Product 3)
        # Store 2 stocks 2 items (Product 1, Product 2)
        # Store 3 stocks 1 item (Product 3)
        # Best main stores are Store 1 and Store 2.
        # Baseline from Store 1: (Price 1 at S1) + (Price 3 at S1) + (Forced trip for Price 2 from S2) = 10 + 30 + 20 = 60
        # Baseline from Store 2: (Price 1 at S2) + (Price 2 at S2) + (Forced trip for Price 3 from S1) = 11 + 20 + 30 = 61
        # The minimum baseline cost should be 60.

        # 2. Execute
        baseline_cost = calculate_baseline_cost(price_slots, stores)

        # 3. Assert
        self.assertEqual(baseline_cost, 60)
