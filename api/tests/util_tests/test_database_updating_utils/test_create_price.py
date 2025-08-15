from django.test import TestCase
from products.models import Price
from companies.tests.test_helpers.model_factories import StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory
from api.utils.database_updating_utils.create_price import create_price

class CreatePriceTest(TestCase):

    def setUp(self):
        self.product = ProductFactory()
        self.store = StoreFactory()

    def test_create_price_basic(self):
        """Test basic price creation with all required fields."""
        price_data = {
            "product_id_store": "prod123",
            "price_current": 10.50,
            "price_was": 12.00,
            "price_unit": 5.25,
            "unit_of_measure": "100g",
            "is_on_special": True,
            "is_available": True,
        }
        price = create_price(price_data, self.product, self.store)
        
        self.assertIsNotNone(price)
        self.assertEqual(price.product, self.product)
        self.assertEqual(price.store, self.store)
        self.assertEqual(price.store_product_id, "prod123")
        self.assertEqual(price.price, 10.50)
        self.assertEqual(price.was_price, 12.00)
        self.assertEqual(price.unit_price, 5.25)
        self.assertEqual(price.unit_of_measure, "100g")
        self.assertTrue(price.is_on_special)
        self.assertTrue(price.is_available)
        self.assertTrue(price.is_active) # Should always be True for new prices
        self.assertIsNotNone(price.scraped_at)

    def test_create_price_fallback_to_was_price(self):
        """Test that price_current falls back to price_was if current is None."""
        price_data = {
            "product_id_store": "prod456",
            "price_current": None,
            "price_was": 15.00
        }
        price = create_price(price_data, self.product, self.store)
        self.assertIsNotNone(price)
        self.assertEqual(price.price, 15.00)
        self.assertEqual(price.was_price, 15.00)

    def test_create_price_no_price_data(self):
        """Test that no price record is created if both current and was prices are missing."""
        price_data = {
            "product_id_store": "prod789",
            "price_current": None,
            "price_was": None
        }
        price = create_price(price_data, self.product, self.store)
        self.assertIsNone(price)

    def test_create_price_default_booleans(self):
        """Test default values for is_on_special and is_available."""
        price_data = {
            "product_id_store": "prod101",
            "price_current": 5.00
            # is_on_special and is_available are not provided
        }
        price = create_price(price_data, self.product, self.store)
        self.assertFalse(price.is_on_special)
        self.assertTrue(price.is_available)

    def test_create_price_with_zero_price(self):
        """Test that a price of zero can be created."""
        price_data = {
            "product_id_store": "prod000",
            "price_current": 0.00
        }
        price = create_price(price_data, self.product, self.store)
        self.assertIsNotNone(price)
        self.assertEqual(price.price, 0.00)
