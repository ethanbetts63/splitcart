from django.test import TestCase
from unittest.mock import Mock

from data_management.database_updating_classes.product_resolver import ProductResolver
from products.models import Product, Price
from companies.models import Store, Company

from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory, ProductBrandFactory, PriceRecordFactory
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory

class ProductResolverTests(TestCase):

    def setUp(self):
        """Set up a realistic database state for the resolver to cache."""
        self.mock_command = Mock()
        self.company = CompanyFactory(name="Test Company")
        self.store1 = StoreFactory(company=self.company, store_id="store:1")
        self.store2 = StoreFactory(company=self.company, store_id="store:2")
        self.brand = ProductBrandFactory(name="brand")

        # Product 1: Let the model generate the normalized string
        self.p1 = ProductFactory(
            name='item a', brand=self.brand, size='1l', barcode='111'
        )
        PriceFactory(price_record=PriceRecordFactory(product=self.p1), store=self.store1, sku='sku111')

        # Product 2
        self.p2 = ProductFactory(
            name='item b', brand=self.brand, size='2l', barcode=None
        )
        PriceFactory(price_record=PriceRecordFactory(product=self.p2), store=self.store1, sku='sku222')

        # Product 3
        self.p3 = ProductFactory(
            name='item c', brand=self.brand, size='3l', barcode='333'
        )
        PriceFactory(price_record=PriceRecordFactory(product=self.p3), store=self.store2, sku='sku333')
        
        # Product 4
        self.p4 = ProductFactory(
            name='item d', brand=self.brand, size='4l', barcode=None
        )
        
        # This resolver is for store1 context
        self.resolver = ProductResolver(self.mock_command, self.company, self.store1)

    def test_cache_building(self):
        """Test that all caches are built correctly on initialization."""
        # Assert: Check contents of each cache
        self.assertEqual(len(self.resolver.barcode_cache), 2)
        self.assertIn('111', self.resolver.barcode_cache)
        self.assertEqual(self.resolver.barcode_cache['111'], self.p1)

        self.assertEqual(len(self.resolver.normalized_string_cache), 4)
        # Use the actual, auto-generated value from the model
        self.assertIn(self.p1.normalized_name_brand_size, self.resolver.normalized_string_cache)
        self.assertEqual(self.resolver.normalized_string_cache[self.p1.normalized_name_brand_size], self.p1)

        self.assertEqual(len(self.resolver.store_cache), 2)
        self.assertIn('store:1', self.resolver.store_cache)

        self.assertEqual(len(self.resolver.sku_cache), 2)
        self.assertIn('sku111', self.resolver.sku_cache)
        self.assertEqual(self.resolver.sku_cache['sku111'], self.p1)

    def test_add_new_product_to_cache(self):
        """Test that a new product can be added to the caches dynamically."""
        initial_barcode_count = len(self.resolver.barcode_cache)
        initial_norm_str_count = len(self.resolver.normalized_string_cache)

        # For a non-persistent instance, we can set the attribute directly for the test
        new_product = ProductFactory.build(
            brand=self.brand,
            barcode='999',
            normalized_name_brand_size='new-item-9l'
        )

        self.resolver.add_new_product_to_cache(new_product)

        self.assertEqual(len(self.resolver.barcode_cache), initial_barcode_count + 1)
        self.assertEqual(len(self.resolver.normalized_string_cache), initial_norm_str_count + 1)
        self.assertIn('999', self.resolver.barcode_cache)
        self.assertIn('new-item-9l', self.resolver.normalized_string_cache)

    def test_find_match_tier_1_barcode(self):
        """Find a match using the highest priority: barcode."""
        product_details = {'barcode': '111'}
        match = self.resolver.find_match(product_details, [])
        self.assertEqual(match, self.p1)

    def test_find_match_tier_2_sku(self):
        """Find a match using the second priority: store-specific SKU."""
        product_details = {'barcode': None, 'sku': 'sku222'}
        match = self.resolver.find_match(product_details, [])
        self.assertEqual(match, self.p2)

    def test_find_match_tier_3_normalized_string(self):
        """Find a match using the third priority: normalized string."""
        # Use the actual, auto-generated value
        product_details = {'barcode': None, 'sku': None, 'normalized_name_brand_size': self.p4.normalized_name_brand_size}
        match = self.resolver.find_match(product_details, [])
        self.assertEqual(match, self.p4)

    def test_find_match_no_match(self):
        """Test that None is returned when no match is found."""
        product_details = {'barcode': '000', 'sku': 'sku000', 'normalized_name_brand_size': 'item-z-0l'}
        match = self.resolver.find_match(product_details, [])
        self.assertIsNone(match)

    def test_find_match_priority_barcode_over_sku(self):
        """Test that barcode (Tier 1) is prioritized over SKU (Tier 2)."""
        product_details = {'barcode': '333', 'sku': 'sku111'}
        match = self.resolver.find_match(product_details, [])
        self.assertEqual(match, self.p3)

    def test_find_match_priority_sku_over_normalized_string(self):
        """Test that SKU (Tier 2) is prioritized over normalized string (Tier 3)."""
        # Use the actual, auto-generated value for p1
        product_details = {'barcode': None, 'sku': 'sku222', 'normalized_name_brand_size': self.p1.normalized_name_brand_size}
        match = self.resolver.find_match(product_details, [])
        self.assertEqual(match, self.p2)