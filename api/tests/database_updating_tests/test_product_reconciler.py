
import os
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock, patch

from api.database_updating_classes.product_reconciler import ProductReconciler
from products.models import Product, Price
from companies.models import Store
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class ProductReconcilerTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.store = StoreFactory()
        self.reconciler = ProductReconciler(self.mock_command)
        # Create a temporary file for logging
        self.temp_log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8')
        self.reconciler.log_file = self.temp_log_file.name

    def tearDown(self):
        self.temp_log_file.close()
        os.unlink(self.temp_log_file.name)

    def test_merge_enriches_canonical_product(self):
        """Test that a canonical product is enriched with data from a duplicate."""
        canonical = ProductFactory(
            name='Canonical Item',
            url=None, # Field to be enriched
            name_variations=['var1']
        )
        duplicate = ProductFactory(
            name='Duplicate Item',
            url='http://example.com',
            name_variations=['var2']
        )
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        with patch('api.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        canonical.refresh_from_db()
        self.assertEqual(canonical.url, 'http://example.com')
        self.assertIn('var1', canonical.name_variations)
        self.assertIn('var2', canonical.name_variations)
        self.assertFalse(Product.objects.filter(id=duplicate.id).exists())

    def test_merge_moves_and_deletes_prices(self):
        """Test that prices are correctly moved or deleted during a merge."""
        from datetime import date, timedelta
        canonical = ProductFactory(name='Canonical Item B')
        duplicate = ProductFactory(name='Duplicate Item B')
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        # Price that should be moved
        p1 = PriceFactory(product=duplicate, store=self.store, scraped_date=date.today())
        # Price that should be deleted (same date as canonical's price)
        p2 = PriceFactory(product=duplicate, store=self.store, scraped_date=date.today() - timedelta(days=1))
        # Canonical's original price
        p3 = PriceFactory(product=canonical, store=self.store, scraped_date=date.today() - timedelta(days=1))

        print(f"P1 date: {p1.scraped_date}")
        print(f"P2 date: {p2.scraped_date}")
        print(f"P3 date: {p3.scraped_date}")

        self.assertEqual(Price.objects.count(), 3)

        with patch('api.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        self.assertEqual(Price.objects.count(), 2)
        self.assertEqual(canonical.prices.count(), 2)
        self.assertFalse(Product.objects.filter(id=duplicate.id).exists())

    @patch('api.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', {})
    def test_run_with_empty_translation_table(self):
        """Test that no action is taken if the translation table is empty."""
        ProductFactory.create_batch(5)
        initial_product_count = Product.objects.count()

        self.reconciler.run()

        self.assertEqual(Product.objects.count(), initial_product_count)

    def test_logging_of_merge_action(self):
        """Test that merge actions are correctly logged to the file."""
        canonical = ProductFactory(name='Canonical C')
        duplicate = ProductFactory(name='Duplicate C')
        translations = {duplicate.normalized_name_brand_size: canonical.normalized_name_brand_size}

        with patch('api.database_updating_classes.product_reconciler.PRODUCT_NAME_TRANSLATIONS', translations):
            self.reconciler.run()

        self.temp_log_file.seek(0)
        log_content = self.temp_log_file.read()
        self.assertIn("Merging duplicate into canonical", log_content)
        self.assertIn(canonical.name, log_content)
        self.assertIn(duplicate.name, log_content)
