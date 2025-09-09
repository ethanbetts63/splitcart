from django.test import TestCase
from unittest.mock import Mock

from api.database_updating_classes.brand_manager import BrandManager
from products.models import ProductBrand
from products.tests.test_helpers.model_factories import ProductBrandFactory

class BrandManagerTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SUCCESS = lambda x: x
        self.brand_manager = BrandManager(self.mock_command)

    def test_init(self):
        """Test that the BrandManager initializes with an empty cache and update set."""
        self.assertEqual(self.brand_manager.brand_cache, {})
        self.assertEqual(self.brand_manager.brands_to_update, set())

    def test_process_brand_new_creates_in_db_and_cache(self):
        """Test that a new brand is created in the DB and added to the cache."""
        self.assertEqual(ProductBrand.objects.count(), 0)
        self.brand_manager.process_brand(brand_name='Test Brand', normalized_brand_name='test-brand')
        
        # It should be in the database and the cache
        self.assertEqual(ProductBrand.objects.count(), 1)
        self.assertIn('test-brand', self.brand_manager.brand_cache)
        self.assertEqual(self.brand_manager.brand_cache['test-brand'].name, 'Test Brand')

    def test_process_brand_duplicate_uses_cache_and_db(self):
        """Test that a duplicate brand (by normalized name) is fetched, not created."""
        # Create it once
        self.brand_manager.process_brand(brand_name='First Brand', normalized_brand_name='test-brand')
        self.assertEqual(ProductBrand.objects.count(), 1)
        
        # Process a variation
        self.brand_manager.process_brand(brand_name='Second Brand', normalized_brand_name='test-brand')
        
        # Should not create a new DB entry
        self.assertEqual(ProductBrand.objects.count(), 1)
        
        # The cache should hold the original object
        self.assertEqual(self.brand_manager.brand_cache['test-brand'].name, 'First Brand')

    def test_process_brand_empty_or_none_is_ignored(self):
        """Test that empty or None brand names are ignored."""
        self.brand_manager.process_brand(brand_name='', normalized_brand_name='')
        self.brand_manager.process_brand(brand_name=None, normalized_brand_name=None)
        self.brand_manager.process_brand(brand_name='A Brand', normalized_brand_name=None)
        self.brand_manager.process_brand(brand_name=None, normalized_brand_name='a-brand')
        
        self.assertEqual(self.brand_manager.brand_cache, {})
        self.assertEqual(ProductBrand.objects.count(), 0)

    def test_process_brand_adds_name_variation(self):
        """Test that a new name variation for an existing brand is recorded."""
        # Start with an existing brand
        brand = ProductBrandFactory(name='Canonical Brand', normalized_name='canonical-brand', name_variations=[])
        self.brand_manager.brand_cache = {'canonical-brand': brand}
        
        # Process a product with a different name but same normalized name
        self.brand_manager.process_brand(brand_name='A Different Brand Name', normalized_brand_name='canonical-brand')
        
        # Check that the variation was added to the object and queued for update
        self.assertIn('A Different Brand Name', brand.name_variations)
        self.assertIn(brand, self.brand_manager.brands_to_update)

    def test_commit_updates_name_variations(self):
        """Test that commit saves name variation changes to the database."""
        brand = ProductBrandFactory(name='Canonical Brand', normalized_name='canonical-brand', name_variations=[])
        self.brand_manager.brand_cache = {'canonical-brand': brand}
        
        # Add a variation
        self.brand_manager.process_brand(brand_name='Variation Name', normalized_brand_name='canonical-brand')
        
        # The variation is staged but not yet saved
        self.assertIn('Variation Name', self.brand_manager.brands_to_update.copy().pop().name_variations)
        
        # Commit the changes
        self.brand_manager.commit()
        
        # Now check the database
        brand.refresh_from_db()
        self.assertIn('Variation Name', brand.name_variations)
        
        # The update set should be clear
        self.assertEqual(self.brand_manager.brands_to_update, set())

    def test_commit_no_changes(self):
        """Test that commit does nothing when there are no changes."""
        ProductBrandFactory(name='Existing Brand', normalized_name='existing-brand')
        self.assertEqual(ProductBrand.objects.count(), 1)

        # Process a brand that doesn't create a variation
        self.brand_manager.process_brand(brand_name='Existing Brand', normalized_brand_name='existing-brand')
        
        # There should be nothing to update
        self.assertEqual(self.brand_manager.brands_to_update, set())
        
        # Commit should run without error
        self.brand_manager.commit()
        self.assertEqual(ProductBrand.objects.count(), 1)