import time
import datetime
from django.test import TestCase
from products.models import Price
from products.tests.test_helpers.model_factories import PriceFactory, ProductFactory, PriceRecordFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class PriceModelTest(TestCase):

    def test_price_creation(self):
        """Test that a price can be created with all fields."""
        price = PriceFactory()
        self.assertIsNotNone(price.id)
        self.assertIsNotNone(price.price_record)
        self.assertIsNotNone(price.store)
        self.assertIsNotNone(price.sku)
        self.assertIsNotNone(price.price_record.price)
        self.assertIsNotNone(price.scraped_date)

    def test_price_str_representation(self):
        """Test the string representation of the price."""
        store = StoreFactory(store_name="TestStore")
        product = ProductFactory(name="TestProduct")
        price_record = PriceRecordFactory(product=product, price=10.50)
        price = PriceFactory(store=store, price_record=price_record)
        price_str = str(price)
        self.assertIn("TestProduct", price_str)
        self.assertIn("TestStore", price_str)
        self.assertIn(f"on {price.scraped_date}", price_str)

    def test_nullable_fields(self):
        """Test that fields that can be null are correctly handled."""
        price_record = PriceRecordFactory(was_price=None, unit_price=None, unit_of_measure=None)
        price = PriceFactory(price_record=price_record)
        self.assertIsNone(price.price_record.was_price)
        self.assertIsNone(price.price_record.unit_price)
        self.assertIsNone(price.price_record.unit_of_measure)

    def test_default_values(self):
        """Test the default values for boolean fields."""
        product = ProductFactory()
        store = StoreFactory(store_name="DefaultStore")
        price_record = PriceRecordFactory(product=product, price=10.0, is_on_special=False)
        price = Price.objects.create(price_record=price_record, store=store, sku="123", scraped_date=datetime.date.today())
        self.assertFalse(price.price_record.is_on_special)
        self.assertIsNone(price.is_available)
        self.assertTrue(price.is_active)