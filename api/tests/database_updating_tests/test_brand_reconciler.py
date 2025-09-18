from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.database_updating_classes.brand_reconciler import BrandReconciler
from products.models import ProductBrand
from products.tests.test_helpers.model_factories import ProductBrandFactory, ProductFactory

class BrandReconcilerTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.reconciler = BrandReconciler(self.mock_command)

    @patch('api.database_updating_classes.brand_reconciler.open')
    def test_run_merges_brands(self, mock_open):
        # 1. Arrange
        # Mock the translation table
        translation_table_content = "BRAND_NAME_TRANSLATIONS = {\n    'duplicate-brand': 'canonical-brand'\n}"
        mock_open.return_value.__enter__.return_value.read.return_value = translation_table_content

        # Create mock brands and products
        canonical_brand = ProductBrandFactory(name='Canonical Brand', normalized_name='canonical-brand')
        duplicate_brand = ProductBrandFactory(name='Duplicate Brand', normalized_name='duplicate-brand')
        product_to_move = ProductFactory(brand=duplicate_brand)

        # 2. Act
        self.reconciler.run()

        # 3. Assert
        # Check that the product has been moved to the canonical brand
        product_to_move.refresh_from_db()
        self.assertEqual(product_to_move.brand, canonical_brand)

        # Check that the duplicate brand has been deleted
        self.assertFalse(ProductBrand.objects.filter(id=duplicate_brand.id).exists())

        # Check that the canonical brand has been updated with the duplicate's variations
        canonical_brand.refresh_from_db()
        self.assertIn(duplicate_brand.name, canonical_brand.name_variations)
        self.assertIn(duplicate_brand.normalized_name, canonical_brand.normalized_name_variations)
