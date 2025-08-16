from django.test import TestCase
from companies.tests.test_helpers.model_factories import StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from api.utils.database_updating_utils.deactivate_product_price import deactivate_product_price

class DeactivateProductPriceTest(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.store = StoreFactory()
        self.price1 = PriceFactory(product=self.product, store=self.store, is_active=True)
        self.price2 = PriceFactory(product=self.product, store=self.store, is_active=True)
        self.price3 = PriceFactory(product=self.product, store=self.store, is_active=False)

    def test_deactivate_product_price(self):
        num_deactivated = deactivate_product_price(self.product, self.store)

        self.assertEqual(num_deactivated, 2)
        self.price1.refresh_from_db()
        self.price2.refresh_from_db()
        self.price3.refresh_from_db()
        self.assertFalse(self.price1.is_active)
        self.assertFalse(self.price2.is_active)
        self.assertFalse(self.price3.is_active) # Should remain false
