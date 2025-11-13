
import os
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock, patch

from data_management.database_updating_classes.product_updating.post_processing.product_reconciler import ProductReconciler
from products.models import Product, Price
from companies.models import Store
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory, ProductBrandFactory, PriceRecordFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class ProductReconcilerTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.store = StoreFactory()
        self.brand = ProductBrandFactory(name="brand")
        self.reconciler = ProductReconciler(self.mock_command)

    def test_merge_enriches_canonical_product(self):
        """Test that a canonical product is enriched with data from a duplicate."""
        canonical = ProductFactory(
            name='Canonical Item',
            brand=self.brand,
            url=None, # Field to be enriched
            name_variations=['var1']
        )
        duplicate = ProductFactory(
            name='Duplicate Item',
            brand=self.brand,
            url='http://example.com',
            name_variations=['var2']
        )
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        with patch('data_management.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        canonical.refresh_from_db()
        self.assertEqual(canonical.url, 'http://example.com')
        self.assertIn('var1', canonical.name_variations)
        self.assertIn('var2', canonical.name_variations)
        self.assertFalse(Product.objects.filter(id=duplicate.id).exists())

    def test_merge_moves_and_deletes_prices(self):
        """Test that prices are correctly moved or deleted during a merge."""
        from datetime import date, timedelta
        canonical = ProductFactory(name='Canonical Item B', brand=self.brand)
        duplicate = ProductFactory(name='Duplicate Item B', brand=self.brand)
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        # Price that should be moved
        PriceFactory(price_record=PriceRecordFactory(product=duplicate), store=self.store, scraped_date=date.today())
        # Price that should be deleted (same date as canonical's price)
        PriceFactory(price_record=PriceRecordFactory(product=duplicate), store=self.store, scraped_date=date.today() - timedelta(days=1))
        # Canonical's original price
        PriceFactory(price_record=PriceRecordFactory(product=canonical), store=self.store, scraped_date=date.today() - timedelta(days=1))

        self.assertEqual(Price.objects.count(), 3)

        with patch('data_management.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        self.assertEqual(Price.objects.count(), 2)
        self.assertEqual(Price.objects.filter(price_record__product=canonical).count(), 2)
        self.assertFalse(Product.objects.filter(id=duplicate.id).exists())

    @patch('data_management.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', {})
    def test_run_with_empty_translation_table(self):
        """Test that no action is taken if the translation table is empty."""
        ProductFactory.create_batch(5, brand=self.brand)
        initial_product_count = Product.objects.count()

        self.reconciler.run()

        self.assertEqual(Product.objects.count(), initial_product_count)

    def test_logging_of_merge_action(self):
        """Test that merge actions are correctly logged to the command output."""
        canonical = ProductFactory(name='Canonical C', brand=self.brand)
        duplicate = ProductFactory(name='Duplicate C', brand=self.brand)
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        with patch('data_management.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        expected_log = f"  - Merging '{duplicate.name}' into '{canonical.name}'"
        self.mock_command.stdout.write.assert_any_call(expected_log)
