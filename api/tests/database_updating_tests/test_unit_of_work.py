from django.test import TestCase
from unittest.mock import Mock, patch

from api.database_updating_classes.unit_of_work import UnitOfWork
from products.models import Product, Price
from companies.models import Store

# Correcting the import path based on user feedback
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class UnitOfWorkTests(TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.mock_command = Mock()
        self.uow = UnitOfWork(self.mock_command)
        self.store = StoreFactory()

    def test_add_new_product(self):
        """Test that a new product is correctly added to the processing list."""
        product_instance = ProductFactory.build() # Build a non-persistent instance
        product_details = {'price_current': 10.0, 'product_id_store': '12345'}
        
        self.uow.add_new_product(product_instance, product_details)
        
        self.assertEqual(len(self.uow.new_products_to_process), 1)
        self.assertEqual(self.uow.new_products_to_process[0][0], product_instance)
        self.assertEqual(self.uow.new_products_to_process[0][1], product_details)

    def test_add_price(self):
        """Test that a price record is correctly added to the creation list."""
        from datetime import date
        product = ProductFactory() # Create a persistent instance to link the price to
        product_details = {'price_current': 12.50, 'product_id_store': '67890', 'scraped_date': date.today().isoformat()}

        self.uow.add_price(product, self.store, product_details)

        self.assertEqual(len(self.uow.prices_to_create), 1)
        price_record = self.uow.prices_to_create[0]
        self.assertIsInstance(price_record, Price)
        self.assertEqual(price_record.product, product)
        self.assertEqual(price_record.store, self.store)
        self.assertEqual(price_record.price, 12.50)
        self.assertEqual(price_record.sku, '67890')

    def test_add_price_does_not_add_if_price_is_none_or_zero(self):
        """Test that a price record is not created if the price is None or 0."""
        from datetime import date
        product = ProductFactory()
        
        # Test with None
        product_details_none = {'price_current': None, 'product_id_store': '111', 'scraped_date': date.today().isoformat()}
        self.uow.add_price(product, self.store, product_details_none)
        self.assertEqual(len(self.uow.prices_to_create), 0)

        # Test with 0
        product_details_zero = {'price_current': 0, 'product_id_store': '222', 'scraped_date': date.today().isoformat()}
        self.uow.add_price(product, self.store, product_details_zero)
        self.assertEqual(len(self.uow.prices_to_create), 0)

    def test_add_for_update(self):
        """Test that a product is correctly added to the update list."""
        product = ProductFactory()
        self.uow.add_for_update(product)
        
        self.assertEqual(len(self.uow.products_to_update), 1)
        self.assertEqual(self.uow.products_to_update[0], product)

    def test_add_for_update_deduplicates(self):
        """Test that the same product is not added to the update list multiple times."""
        product = ProductFactory()
        self.uow.add_for_update(product)
        self.uow.add_for_update(product) # Add the same instance again

        self.assertEqual(len(self.uow.products_to_update), 1)

    def test_commit_creates_objects_in_database(self):
        """An integration test to ensure commit actually creates products and prices."""
        # 1. Setup initial state
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        
        existing_product = ProductFactory()
        # Create a price with a different date and price to avoid unique key collision
        PriceFactory(product=existing_product, store=self.store, scraped_date=yesterday, price=99.99)

        initial_product_count = Product.objects.count()
        initial_price_count = Price.objects.count()

        # 2. Add work to the UoW
        # A new price for the existing product
        existing_product_details = {'price_current': 20.0, 'product_id_store': 'existing-sku', 'scraped_date': date.today().isoformat()}
        self.uow.add_price(existing_product, self.store, existing_product_details)

        # A new product
        new_product_instance = ProductFactory.build(barcode='111', normalized_name_brand_size='new-item-1l')
        new_product_details = {'price_current': 10.0, 'product_id_store': 'new-sku', 'scraped_date': date.today().isoformat()}
        self.uow.add_new_product(new_product_instance, new_product_details)

        # 3. Call commit with real data
        mock_consolidated_data = {}
        mock_product_cache = {}
        mock_resolver = Mock()
        mock_resolver.barcode_cache = {}
        mock_resolver.normalized_string_cache = {}

        self.uow.commit(mock_consolidated_data, mock_product_cache, mock_resolver, self.store)

        # 4. Assert database state
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        self.assertEqual(Price.objects.count(), initial_price_count + 2)

    def test_internal_deduplication_of_new_products(self):
        """Test the _deduplicate_new_products method directly."""
        # 1. Setup a mock resolver with cached items
        mock_resolver = Mock()
        mock_resolver.barcode_cache = {'1234567890123': 1} # Existing barcode
        mock_resolver.normalized_string_cache = {'item-a-1l': 2} # Existing normalized string

        # 2. Add products to the UoW
        # This one should be filtered out (duplicate barcode)
        p1 = ProductFactory.build(barcode='1234567890123', normalized_name_brand_size='item-b-1l')
        self.uow.add_new_product(p1, {})

        # This one should be filtered out (duplicate normalized string)
        p2 = ProductFactory.build(barcode='999', normalized_name_brand_size='item-a-1l')
        self.uow.add_new_product(p2, {})

        # This one is unique and should be kept
        p3 = ProductFactory.build(barcode='111', normalized_name_brand_size='item-c-1l')
        self.uow.add_new_product(p3, {})

        # 3. Call the internal method
        unique_products = self.uow._deduplicate_new_products(mock_resolver)

        # 4. Assert
        self.assertEqual(len(unique_products), 1)
        self.assertEqual(unique_products[0][0], p3)

    @patch('api.database_updating_classes.unit_of_work.Product.objects.bulk_update')
    def test_commit_flow(self, mock_product_update):
        """Test the main commit logic, ensuring objects are created."""
        from datetime import date
        initial_product_count = Product.objects.count()
        initial_price_count = Price.objects.count()

        # 1. Setup mock objects required for commit
        mock_resolver = Mock()
        mock_resolver.barcode_cache = {}
        mock_resolver.normalized_string_cache = {}
        mock_consolidated_data = []
        mock_product_cache = {}

        # 2. Add items to the UoW
        # A new product
        new_product_instance = ProductFactory.build(id=None, barcode='111', normalized_name_brand_size='new-item-1l')
        new_product_details = {'price_current': 10.0, 'product_id_store': 'new-sku', 'scraped_date': date.today().isoformat()}
        self.uow.add_new_product(new_product_instance, new_product_details)

        # An existing product to update
        existing_product = ProductFactory()
        self.uow.add_for_update(existing_product)

        # A price for an existing product
        self.uow.add_price(existing_product, self.store, {'price_current': 20.0, 'product_id_store': 'existing-sku', 'scraped_date': date.today().isoformat()})

        # 3. Call commit
        self.uow.commit(mock_consolidated_data, mock_product_cache, mock_resolver, self.store)

        # 4. Assert that the objects were created
        self.assertEqual(Product.objects.count(), initial_product_count + 2) # +1 for existing_product, +1 for new_product_instance
        self.assertEqual(Price.objects.count(), initial_price_count + 2)
        mock_product_update.assert_called_once_with([existing_product], ['barcode', 'url', 'image_url', 'description', 'country_of_origin', 'ingredients', 'has_no_coles_barcode', 'name_variations', 'normalized_name_brand_size_variations', 'sizes'], batch_size=500)