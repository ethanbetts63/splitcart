from django.test import TestCase
from unittest.mock import Mock
from products.models import Product, Price
from companies.models import Store
from products.tests.test_helpers.model_factories import ProductFactory
from companies.tests.test_helpers.model_factories import StoreFactory, CompanyFactory, DivisionFactory
from api.database_updating_classes.product_resolver import ProductResolver
from api.database_updating_classes.unit_of_work import UnitOfWork
from api.utils.product_normalizer import ProductNormalizer

class TestProductMatchingAndCreation(TestCase):

    def setUp(self):
        self.company = CompanyFactory()
        self.division = DivisionFactory(company=self.company)
        self.store1 = StoreFactory(company=self.company, division=self.division, store_id="store1")

        self.existing_product_barcode = ProductFactory(barcode="123456789")

        self.existing_product_spid = ProductFactory()
        # The Price model now generates its own normalized_key, so we don't set it manually
        # We also need to provide a scraped_date
        from datetime import date
        Price.objects.create(product=self.existing_product_spid, store=self.store1, sku="spid1", price=1.0, scraped_date=date.today())

        self.existing_product_norm = ProductFactory(
            name="Test Product",
            brand="TestBrand",
            size="1kg"
        )

        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SQL_FIELD = lambda x: x
        self.mock_command.style.SUCCESS = lambda x: x
        self.mock_command.style.ERROR = lambda x: x

    def test_product_matching_and_creation_flow(self):
        # This test replicates the core logic of UpdateOrchestrator._process_consolidated_data
        # to test the interaction between ProductResolver and UnitOfWork.
        
        # 1. Setup
        resolver = ProductResolver(self.mock_command, self.company, self.store1)
        unit_of_work = UnitOfWork(self.mock_command)
        product_cache = {}

        consolidated_data = {
            # Match via barcode
            "key_barcode": {
                "product": {"barcode": "123456789", "name": "Barcode Product", "price_current": 1.0, "scraped_date": "2025-01-01"},
                "metadata": {"company": self.company.name, "store_id": self.store1.store_id}
            },
            # Match via store product id (sku)
            "key_spid": {
                "product": {"product_id_store": "spid1", "name": "SPID Product", "price_current": 1.0, "scraped_date": "2025-01-01"},
                "metadata": {"company": self.company.name, "store_id": self.store1.store_id}
            },
            # Match via normalized string
            "key_norm": {
                "product": {"name": "Test Product", "brand": "TestBrand", "size": "1kg", "price_current": 1.0, "scraped_date": "2025-01-01"},
                "metadata": {"company": self.company.name, "store_id": self.store1.store_id}
            },
            # A new product that should be created
            "key_new": {
                "product": {"name": "New Product", "brand": "NewBrand", "size": "500g", "barcode": "987654321", "price_current": 1.0, "scraped_date": "2025-01-01"},
                "metadata": {"company": self.company.name, "store_id": self.store1.store_id}
            }
        }

        # Add normalized strings to the test data
        for key, data in consolidated_data.items():
            normalizer = ProductNormalizer(data['product'])
            data['product']['normalized_name_brand_size'] = normalizer.get_normalized_string()

        # 2. Processing Logic (from UpdateOrchestrator._process_consolidated_data)
        for key, data in consolidated_data.items():
            product_details = data['product']
            existing_product = resolver.find_match(product_details, [])

            if existing_product:
                product_cache[key] = existing_product
                unit_of_work.add_for_update(existing_product)
                unit_of_work.add_price(existing_product, self.store1, product_details)
            else:
                new_product = Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand'),
                    barcode=product_details.get('barcode'),
                    normalized_name_brand_size=product_details.get('normalized_name_brand_size')
                )
                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product, product_details)
        
        # 3. Commit changes
        unit_of_work.commit(consolidated_data, product_cache, resolver, self.store1)

        # 4. Assertions
        print(f"Product cache keys: {list(product_cache.keys())}")
        # self.assertEqual(len(product_cache), 4)
        self.assertEqual(product_cache["key_barcode"], self.existing_product_barcode)
        self.assertEqual(product_cache["key_spid"], self.existing_product_spid)
        self.assertEqual(product_cache["key_norm"].name, self.existing_product_norm.name) # Compare by attribute as they are different instances
        self.assertIn("key_new", product_cache)

        # Check if the new product was created in the database
        self.assertTrue(Product.objects.filter(barcode="987654321").exists())
        new_product_from_db = Product.objects.get(barcode="987654321")
        self.assertEqual(product_cache["key_new"], new_product_from_db)
