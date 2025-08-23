import unittest
from unittest.mock import MagicMock
from django.test import TestCase
from products.models import Product
from api.utils.database_updating_utils.batch_create_new_products import batch_create_new_products
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory, DivisionFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory

class BatchCreateNewProductsTest(TestCase):
    def setUp(self):
        # Mock the command object
        self.mock_command = MagicMock()
        self.mock_command.stdout.write = MagicMock()

        # Create some initial data
        self.company = CompanyFactory.create(name="Test Company")
        self.division = DivisionFactory.create(company=self.company)
        self.store1 = StoreFactory.create(company=self.company, division=self.division, store_id=1, store_name="Test Store 1")
        self.store2 = StoreFactory.create(company=self.company, division=self.division, store_id=2, store_name="Test Store 2")

        # Product 1: Has a barcode
        self.product1 = ProductFactory.create(
            barcode="1111111111111",
            name="Barcode Product",
            brand="Brand A",
            normalized_name_brand_size="barcode product-brand a-1kg"
        )

        # Product 2: Has a store-specific product ID
        self.product2 = ProductFactory.create(
            name="Store ID Product",
            brand="Brand B",
            normalized_name_brand_size="store id product-brand b-500g"
        )
        PriceFactory.create(
            product=self.product2,
            store=self.store1,
            store_product_id="PROD002"
        )

        # Product 3: To be matched by normalized string
        self.product3 = ProductFactory.create(
            name="Normalized String Product",
            brand="Brand C",
            normalized_name_brand_size="normalized string product-brand c-250ml"
        )

        # Consolidated data for testing
        self.consolidated_data = {
            # --- Data that should match existing products ---
            "match_barcode": {
                "product_details": {
                    "name": "Barcode Product",
                    "brand": "Brand A",
                    "barcode": "1111111111111",
                    "normalized_name_brand_size": "barcode product-brand a-1kg"
                },
                "price_history": [{"store_id": 1}]
            },
            "match_store_id": {
                "product_details": {
                    "name": "Store ID Product",
                    "brand": "Brand B",
                    "store_product_id": "PROD002",
                    "normalized_name_brand_size": "store id product-brand b-500g"
                },
                "price_history": [{"store_id": 1}]
            },
            "match_norm_string": {
                "product_details": {
                    "name": "Normalized String Product",
                    "brand": "Brand C",
                    "normalized_name_brand_size": "normalized string product-brand c-250ml"
                },
                "price_history": [{"store_id": 2}]
            },
            # --- Data for new products ---
            "new_product_1": {
                "product_details": {
                    "name": "New Product 1",
                    "brand": "Brand D",
                    "normalized_name_brand_size": "new product 1-brand d-1l"
                },
                "price_history": [{"store_id": 1}]
            },
            "new_product_2": {
                "product_details": {
                    "name": "New Product 2",
                    "brand": "Brand E",
                    "barcode": "2222222222222",
                    "normalized_name_brand_size": "new product 2-brand e-2kg"
                },
                "price_history": [{"store_id": 2}]
            },
            # --- Duplicate new product (should only be created once) ---
            "duplicate_new_product": {
                "product_details": {
                    "name": "New Product 1", # Same as new_product_1
                    "brand": "Brand D",
                    "normalized_name_brand_size": "new product 1-brand d-1l"
                },
                "price_history": [{"store_id": 2}]
            }
        }

    def test_batch_create_new_products(self):
        # Ensure we start with 3 products
        self.assertEqual(Product.objects.count(), 3)

        print(f"Initial product count: {Product.objects.count()}")
        product_lookup_cache = batch_create_new_products(self.mock_command, self.consolidated_data)
        print(f"Final product count: {Product.objects.count()}")
        print(f"Product lookup cache: {product_lookup_cache}")

        # --- Assertions ---

        # 1. Check the product count after running
        # We expect 2 new products to be created (new_product_1 and new_product_2)
        self.assertEqual(Product.objects.count(), 5)

        # 2. Check the returned lookup cache
        self.assertEqual(len(product_lookup_cache), 6)
        self.assertEqual(product_lookup_cache["match_barcode"], self.product1)
        self.assertEqual(product_lookup_cache["match_store_id"], self.product2)
        self.assertEqual(product_lookup_cache["match_norm_string"], self.product3)

        # 3. Verify the newly created products
        new_product_1 = Product.objects.get(normalized_name_brand_size="new product 1-brand d-1l")
        new_product_2 = Product.objects.get(barcode="2222222222222")

        self.assertEqual(product_lookup_cache["new_product_1"], new_product_1)
        self.assertEqual(product_lookup_cache["new_product_2"], new_product_2)
        self.assertEqual(product_lookup_cache["duplicate_new_product"], new_product_1) # Should point to the same product

        # 4. Check the attributes of a newly created product
        self.assertEqual(new_product_1.name, "New Product 1")
        self.assertEqual(new_product_1.brand, "Brand D")

        # 5. Check that the mock command's stdout was called
        self.mock_command.stdout.write.assert_called()