import time
from django.test import TestCase
from products.tests.test_helpers.model_factories import PriceFactory, ProductFactory
from stores.tests.test_helpers.model_factories import StoreFactory

class PriceModelTest(TestCase):

    def test_price_creation(self):
        price = PriceFactory()
        self.assertIsNotNone(price.id)
        self.assertTrue(price.price > 0)
        self.assertIsNotNone(price.scraped_at)

    def test_price_str_representation(self):
        store = StoreFactory(name="TestStore")
        product = ProductFactory(name="TestProduct")
        price = PriceFactory(store=store, product=product, price=10.50)
        self.assertIn("TestProduct at TestStore for $10.50", str(price).replace("10.5", "10.50"))

    def test_ordering(self):
        price1 = PriceFactory()
        time.sleep(0.01)
        price2 = PriceFactory()
        self.assertTrue(price1.scraped_at < price2.scraped_at)

    def test_nullable_fields(self):
        price = PriceFactory(was_price=None, unit_price=None, unit_of_measure=None, url=None)
        self.assertIsNone(price.was_price)
        self.assertIsNone(price.unit_price)
        self.assertIsNone(price.unit_of_measure)
        self.assertIsNone(price.url)