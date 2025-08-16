from django.test import TestCase
from splitcart_concept import calculate_single_store_costs, find_cheapest_combination

class SplitcartConceptTest(TestCase):
    def test_calculate_single_store_costs(self):
        shopping_list = ["Apple", "Banana", "Orange"]
        all_store_data = {
            "stores": [
                {
                    "name": "Store A",
                    "products": [
                        {"name": "Apple", "price": 1.0},
                        {"name": "Banana", "price": 0.5},
                        {"name": "Orange", "price": 0.75}
                    ]
                },
                {
                    "name": "Store B",
                    "products": [
                        {"name": "Apple", "price": 1.2},
                        {"name": "Banana", "price": 0.4},
                        {"name": "Grape", "price": 2.0} # Missing Orange
                    ]
                },
                {
                    "name": "Store C",
                    "products": [
                        {"name": "Apple", "price": 0.9},
                        {"name": "Banana", "price": 0.6},
                        {"name": "Orange", "price": 0.8}
                    ]
                }
            ]
        }

        expected_costs = {
            "Store A": 2.25,
            "Store C": 2.3
        }

        actual_costs = calculate_single_store_costs(shopping_list, all_store_data)
        self.assertEqual(actual_costs, expected_costs)

    def test_calculate_single_store_costs_empty_shopping_list(self):
        shopping_list = []
        all_store_data = {
            "stores": [
                {
                    "name": "Store A",
                    "products": [
                        {"name": "Apple", "price": 1.0}
                    ]
                }
            ]
        }
        expected_costs = {"Store A": 0}
        actual_costs = calculate_single_store_costs(shopping_list, all_store_data)
        self.assertEqual(actual_costs, expected_costs)

    def test_calculate_single_store_costs_no_stores(self):
        shopping_list = ["Apple"]
        all_store_data = {"stores": []}
        expected_costs = {}
        actual_costs = calculate_single_store_costs(shopping_list, all_store_data)
        self.assertEqual(actual_costs, expected_costs)

    def test_calculate_single_store_costs_no_matching_products(self):
        shopping_list = ["Mango"]
        all_store_data = {
            "stores": [
                {
                    "name": "Store A",
                    "products": [
                        {"name": "Apple", "price": 1.0}
                    ]
                }
            ]
        }
        expected_costs = {}
        actual_costs = calculate_single_store_costs(shopping_list, all_store_data)
        self.assertEqual(actual_costs, expected_costs)
