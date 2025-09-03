
import os
import json
import shutil
import tempfile
from django.test import TestCase
from unittest.mock import Mock, MagicMock

from api.database_updating_classes.product_updater import ProductUpdater
from products.models import Product, Price
from companies.models import Store, Company

from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory

class ProductUpdaterTests(TestCase):

    def setUp(self):
        """Set up a temporary directory for archives and initial database state."""
        self.mock_command = MagicMock()
        self.archive_path = tempfile.mkdtemp()

        self.company = CompanyFactory(name="Test Company")
        self.store = StoreFactory(company=self.company, store_id="store_123")

        # Existing product in the database
        self.existing_product = ProductFactory(
            name='Existing Item',
            brand='Brand A',
            size='500g',
            barcode='1234567890123',
            normalized_name_brand_size='existing-item-brand-a-500g'
        )
        PriceFactory(product=self.existing_product, store=self.store, price=10.00)

        # Create a dummy archive file
        self.company_archive_path = os.path.join(self.archive_path, self.company.name.lower())
        os.makedirs(self.company_archive_path)
        
        archive_data = {
            "metadata": {"store_id": "store_123"},
            "products": [
                {
                    "name": "Existing Item",
                    "brand": "Brand A",
                    "normalized_name_brand_size": "existing-item-brand-a-500g",
                    "price_history": [
                        {"price": 12.00, "scraped_at": "2025-09-03T12:00:00Z", "sku": "sku001"}
                    ]
                },
                {
                    "name": "New Item",
                    "brand": "Brand B",
                    "normalized_name_brand_size": "new-item-brand-b-250g",
                    "sizes": ["250g"],
                    "price_history": [
                        {"price": 5.50, "scraped_at": "2025-09-03T12:00:00Z", "sku": "sku002"}
                    ]
                }
            ]
        }
        
        with open(os.path.join(self.company_archive_path, 'store_123.json'), 'w') as f:
            json.dump(archive_data, f)

        self.updater = ProductUpdater(self.mock_command, self.archive_path)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.archive_path)

    def test_run_updates_and_creates_products(self):
        """Test the full run method to ensure it updates and creates products correctly."""
        initial_product_count = Product.objects.count()
        initial_price_count = Price.objects.count()

        self.updater.run()

        # Check that a new product was created
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        new_product = Product.objects.get(normalized_name_brand_size='new-item-brand-b-250g')
        self.assertEqual(new_product.name, 'New Item')

        # Check that prices were added
        # One for the new product, one for the existing product's new price
        self.assertEqual(Price.objects.count(), initial_price_count + 2)

        # Check that the existing product has a new price
        existing_product_prices = Price.objects.filter(product=self.existing_product).order_by('-price')
        self.assertEqual(existing_product_prices.count(), 2)
        self.assertEqual(existing_product_prices.first().price, 12.00)
        
        # Check that the new product has a price
        new_product_prices = Price.objects.filter(product=new_product)
        self.assertEqual(new_product_prices.count(), 1)
        self.assertEqual(new_product_prices.first().price, 5.50)

