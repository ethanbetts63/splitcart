from django.test import TestCase
from products.models import Price
from companies.tests.test_helpers.model_factories import StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from api.utils.database_updating_utils.deactivate_store_prices import deactivate_prices_for_store

class DeactivatePricesForStoreTest(TestCase):

    def setUp(self):
        self.store1 = StoreFactory()
        self.store2 = StoreFactory()
        self.product1 = ProductFactory()
        self.product2 = ProductFactory()

        # Prices for store1
        self.price1_store1_active = PriceFactory(store=self.store1, product=self.product1, is_active=True)
        self.price2_store1_active = PriceFactory(store=self.store1, product=self.product2, is_active=True)
        self.price3_store1_inactive = PriceFactory(store=self.store1, product=self.product1, is_active=False)

        # Prices for store2
        self.price1_store2_active = PriceFactory(store=self.store2, product=self.product1, is_active=True)

    def test_deactivates_only_active_prices_for_given_store(self):
        """Test that only active prices for the specified store are deactivated."""
        deactivated_count = deactivate_prices_for_store(self.store1)
        
        self.assertEqual(deactivated_count, 2)
        
        # Check store1 prices
        self.price1_store1_active.refresh_from_db()
        self.price2_store1_active.refresh_from_db()
        self.price3_store1_inactive.refresh_from_db()
        
        self.assertFalse(self.price1_store1_active.is_active)
        self.assertFalse(self.price2_store1_active.is_active)
        self.assertFalse(self.price3_store1_inactive.is_active) # Should remain False

        # Check store2 prices (should remain active)
        self.price1_store2_active.refresh_from_db()
        self.assertTrue(self.price1_store2_active.is_active)

    def test_returns_correct_count_of_deactivated_prices(self):
        """Test that the function returns the correct count of deactivated prices."""
        deactivated_count = deactivate_prices_for_store(self.store1)
        self.assertEqual(deactivated_count, 2)

    def test_no_deactivation_if_no_active_prices(self):
        """Test that no prices are deactivated if there are no active prices for the store."""
        store_no_active_prices = StoreFactory()
        PriceFactory(store=store_no_active_prices, product=self.product1, is_active=False)
        
        deactivated_count = deactivate_prices_for_store(store_no_active_prices)
        self.assertEqual(deactivated_count, 0)

    def test_no_deactivation_if_store_has_no_prices(self):
        """Test that no prices are deactivated if the store has no prices at all."""
        empty_store = StoreFactory()
        deactivated_count = deactivate_prices_for_store(empty_store)
        self.assertEqual(deactivated_count, 0)
