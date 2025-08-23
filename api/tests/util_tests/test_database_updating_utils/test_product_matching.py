from django.test import TestCase
from unittest.mock import Mock
from products.models import Product
from companies.models.store import Store
from products.tests.test_helpers.model_factories import ProductFactory
from companies.tests.test_helpers.model_factories import StoreFactory, CompanyFactory, DivisionFactory
from api.utils.database_updating_utils.batch_create_new_products import batch_create_new_products
from products.models.price import Price
from api.utils.normalization_utils.get_normalized_string import get_normalized_string

class TestProductMatching(TestCase):

    def setUp(self):
        self.company = CompanyFactory()
        self.division = DivisionFactory(company=self.company)
        self.store1 = StoreFactory(company=self.company, division=self.division, store_id="store1")

        self.existing_product_barcode = ProductFactory(barcode="123456789")
        self.existing_product_barcode.save()

        self.existing_product_spid = ProductFactory()
        self.existing_product_spid.save()
        Price.objects.create(product=self.existing_product_spid, store=self.store1, store_product_id="spid1", price=1.0)

        self.existing_product_norm = ProductFactory(
            name="Test Product",
            brand="TestBrand",
            sizes=["1kg"]
        )
        self.existing_product_norm.save()

        self.mock_command = Mock()
        self.mock_command.stdout = Mock()
        self.mock_command.style.SQL_FIELD = lambda x: x
        self.mock_command.style.SUCCESS = lambda x: x

    def test_product_matching_and_creation(self):
        consolidated_data = {
            "key_barcode": {
                "product_details": {"barcode": "123456789", "name": "Barcode Product"},
                "price_history": [{"store_id": "store1", "price": 1.0}]
            },
            "key_spid": {
                "product_details": {"store_product_id": "spid1", "name": "SPID Product"},
                "price_history": [{"store_id": "store1", "price": 1.0}]
            },
            "key_norm": {
                "product_details": {"name": "Test Product", "brand": "TestBrand", "sizes": ["1kg"]},
                "price_history": [{"store_id": "store1", "price": 1.0}]
            },
            "key_new": {
                "product_details": {"name": "New Product", "brand": "NewBrand", "sizes": ["500g"], "barcode": "987654321"},
                "price_history": [{"store_id": "store1", "price": 1.0}]
            }
        }

        # Add normalized strings to the test data
        for key, data in consolidated_data.items():
            product_details = data['product_details']
            product_details['normalized_name_brand_size'] = get_normalized_string(product_details, product_details.get('sizes', []))

        product_lookup_cache = batch_create_new_products(self.mock_command, consolidated_data)

        # Assertions
        self.assertEqual(len(product_lookup_cache), 4)
        self.assertEqual(product_lookup_cache["key_barcode"], self.existing_product_barcode)
        self.assertEqual(product_lookup_cache["key_spid"], self.existing_product_spid)
        self.assertEqual(product_lookup_cache["key_norm"], self.existing_product_norm)
        self.assertIn("key_new", product_lookup_cache)

        # Check if the new product was created
        self.assertTrue(Product.objects.filter(barcode="987654321").exists())
        new_product = Product.objects.get(barcode="987654321")
        self.assertEqual(product_lookup_cache["key_new"], new_product)