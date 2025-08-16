import time
from django.test import TestCase
from products.models import Price
from products.tests.test_helpers.model_factories import PriceFactory, ProductFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class PriceModelTest(TestCase):

    def test_price_creation(self):
        """Test that a price can be created with all fields."""
        price = PriceFactory()
        self.assertIsNotNone(price.id)
        self.assertIsNotNone(price.product)
        self.assertIsNotNone(price.store)
        self.assertIsNotNone(price.store_product_id)
        self.assertTrue(price.price > 0)
        self.assertIsNotNone(price.scraped_at)

    def test_price_str_representation(self):
        """Test the string representation of the price."""
        store = StoreFactory(name="TestStore")
        product = ProductFactory(name="TestProduct")
        price = PriceFactory(store=store, product=product, price=10.50)
        price_str = str(price)
        self.assertIn("TestProduct", price_str)
        self.assertIn("TestStore", price_str)
        self.assertIn("$10.5", price_str)

    def test_ordering(self):
        """Test that prices are ordered by scraped_at in descending order."""
        price1 = PriceFactory()
        time.sleep(0.01) # Ensure scraped_at is different
        price2 = PriceFactory()
        prices = Price.objects.all()
        self.assertEqual(prices[0], price2)
        self.assertEqual(prices[1], price1)

    def test_nullable_fields(self):
        """Test that fields that can be null are correctly handled."""
        price = PriceFactory(was_price=None, unit_price=None, unit_of_measure=None)
        self.assertIsNone(price.was_price)
        self.assertIsNone(price.unit_price)
        self.assertIsNone(price.unit_of_measure)

    def test_default_values(self):
        """Test the default values for boolean fields."""
        product = ProductFactory()
        store = StoreFactory()
        price = Price.objects.create(product=product, store=store, store_product_id="123", price=10.0)
        self.assertFalse(price.is_on_special)
        self.assertTrue(price.is_available)
        self.assertTrue(price.is_active)
