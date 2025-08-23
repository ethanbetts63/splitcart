from django.test import TestCase
from unittest.mock import Mock
from decimal import Decimal
from products.models import Product, Price
from companies.models import Store
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory, StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory
from api.utils.database_updating_utils.batch_create_prices import batch_create_prices
import os
from django.conf import settings

class TestBatchCreatePrices(TestCase):

    def setUp(self):
        self.company = CompanyFactory()
        self.division = DivisionFactory(company=self.company)
        self.store1 = StoreFactory(company=self.company, division=self.division, store_id="store1")
        self.store2 = StoreFactory(company=self.company, division=self.division, store_id="store2")

        self.product1 = ProductFactory()
        self.product2 = ProductFactory()

        self.product_cache = {
            "key1": self.product1,
            "key2": self.product2
        }

        self.consolidated_data = {
            "key1": {
                "price_history": [
                    {"store_id": "store1", "price": 1.00, "is_on_special": False, "is_available": True},
                    {"store_id": "store2", "price": 1.10, "is_on_special": True, "is_available": True}
                ]
            },
            "key2": {
                "price_history": [
                    {"store_id": "store1", "price": 2.00, "is_on_special": False, "is_available": False}
                ]
            }
        }

        self.mock_command = Mock()
        self.mock_command.stdout = Mock()
        self.mock_command.style = Mock()
        self.mock_command.style.SQL_FIELD = lambda x: x
        self.mock_command.style.SUCCESS = lambda x: x
        self.mock_command.style.WARNING = lambda x: x

    def test_batch_create_prices_success(self):
        batch_create_prices(self.mock_command, self.consolidated_data, self.product_cache)

        self.assertEqual(Price.objects.count(), 3)

        price1 = Price.objects.get(product=self.product1, store=self.store1)
        self.assertEqual(price1.price, Decimal('1.00'))
        self.assertFalse(price1.is_on_special)
        self.assertTrue(price1.is_available)

        price2 = Price.objects.get(product=self.product1, store=self.store2)
        self.assertEqual(price2.price, Decimal('1.10'))
        self.assertTrue(price2.is_on_special)
        self.assertTrue(price2.is_available)

        price3 = Price.objects.get(product=self.product2, store=self.store1)
        self.assertEqual(price3.price, Decimal('2.00'))
        self.assertFalse(price3.is_on_special)
        self.assertFalse(price3.is_available)

    def test_batch_create_prices_skip_missing_product(self):
        self.consolidated_data['key3'] = {
            "price_history": [
                {"store_id": "store1", "price": 3.00}
            ]
        }

        problem_products_file = os.path.join(settings.BASE_DIR, 'api', 'data', 'problem_products.txt')
        if os.path.exists(problem_products_file):
            os.remove(problem_products_file)

        batch_create_prices(self.mock_command, self.consolidated_data, self.product_cache)

        self.assertEqual(Price.objects.count(), 3)
        self.assertTrue(os.path.exists(problem_products_file))

        with open(problem_products_file, 'r') as f:
            content = f.read()
            self.assertIn("key3", content)

    def test_batch_create_prices_skip_missing_store(self):
        self.consolidated_data['key1']['price_history'].append(
            {"store_id": "store3", "price": 4.00}
        )

        batch_create_prices(self.mock_command, self.consolidated_data, self.product_cache)

        self.assertEqual(Price.objects.count(), 3)
