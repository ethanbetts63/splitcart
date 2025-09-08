from django.test import TestCase
from unittest.mock import Mock

from api.database_updating_classes.brand_manager import BrandManager
from products.models import ProductBrand
from products.tests.test_helpers.model_factories import ProductBrandFactory

class BrandManagerTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.brand_manager = BrandManager(self.mock_command)

    def test_init(self):
        """Test that the BrandManager initializes with an empty dictionary."""
        self.assertEqual(self.brand_manager.processed_brands, {})

    def test_process_brand_new(self):
        """Test that a new brand is added to the processed_brands dictionary."""
        self.brand_manager.process_brand(brand_name='Test Brand', normalized_brand_name='test-brand')
        self.assertEqual(self.brand_manager.processed_brands, {'test-brand': 'Test Brand'})

    def test_process_brand_duplicate(self):
        """Test that a duplicate brand (by normalized name) is not added."""
        self.brand_manager.process_brand(brand_name='First Brand', normalized_brand_name='test-brand')
        self.brand_manager.process_brand(brand_name='Second Brand', normalized_brand_name='test-brand')
        self.assertEqual(self.brand_manager.processed_brands, {'test-brand': 'First Brand'})

    def test_process_brand_empty_or_none(self):
        """Test that empty or None brand names are ignored."""
        self.brand_manager.process_brand(brand_name='', normalized_brand_name='')
        self.brand_manager.process_brand(brand_name=None, normalized_brand_name=None)
        self.brand_manager.process_brand(brand_name='A Brand', normalized_brand_name=None)
        self.brand_manager.process_brand(brand_name=None, normalized_brand_name='a-brand')
        self.assertEqual(self.brand_manager.processed_brands, {})

    def test_commit_new_brands(self):
        """Test that commit creates new brand objects in the database."""
        self.brand_manager.process_brand(brand_name='New Brand 1', normalized_brand_name='new-brand-1')
        self.brand_manager.process_brand(brand_name='New Brand 2', normalized_brand_name='new-brand-2')
        
        self.assertEqual(ProductBrand.objects.count(), 0)
        self.brand_manager.commit()
        self.assertEqual(ProductBrand.objects.count(), 2)

        brand1 = ProductBrand.objects.get(normalized_name='new-brand-1')
        brand2 = ProductBrand.objects.get(normalized_name='new-brand-2')
        self.assertEqual(brand1.name, 'New Brand 1')
        self.assertEqual(brand2.name, 'New Brand 2')

    def test_commit_existing_brands(self):
        """Test that commit does not create duplicates for existing brands."""
        ProductBrandFactory(name='Existing Brand', normalized_name='existing-brand')
        self.assertEqual(ProductBrand.objects.count(), 1)

        self.brand_manager.process_brand(brand_name='Existing Brand', normalized_brand_name='existing-brand')
        self.brand_manager.commit()

        self.assertEqual(ProductBrand.objects.count(), 1)

    def test_commit_mixed_brands(self):
        """Test that commit handles a mix of new and existing brands correctly."""
        ProductBrandFactory(name='Existing Brand', normalized_name='existing-brand')
        self.assertEqual(ProductBrand.objects.count(), 1)

        self.brand_manager.process_brand(brand_name='Existing Brand', normalized_brand_name='existing-brand')
        self.brand_manager.process_brand(brand_name='New Brand', normalized_brand_name='new-brand')
        self.brand_manager.commit()

        self.assertEqual(ProductBrand.objects.count(), 2)
        self.assertTrue(ProductBrand.objects.filter(normalized_name='new-brand').exists())

    def test_commit_no_brands(self):
        """Test that commit handles the case where no brands were processed."""
        self.assertEqual(ProductBrand.objects.count(), 0)
        self.brand_manager.commit()
        self.assertEqual(ProductBrand.objects.count(), 0)
