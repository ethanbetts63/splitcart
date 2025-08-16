from django.test import TestCase
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from api.utils.substitution_utils.get_woolworths_product_store_ids import get_woolworths_product_store_ids
from products.models import Price # Import Price model to query existing objects

class GetWoolworthsProductStoreIdsTest(TestCase):
    def setUp(self):
        self.woolworths = CompanyFactory(name='Woolworths')
        self.coles = CompanyFactory(name='Coles')

        self.woolworths_store = StoreFactory(company=self.woolworths)
        self.coles_store = StoreFactory(company=self.coles)

        self.product1 = ProductFactory()
        self.product2 = ProductFactory()
        self.product3 = ProductFactory()

        # Woolworths products
        PriceFactory(product=self.product1, store=self.woolworths_store, store_product_id='ww1', is_active=True)
        PriceFactory(product=self.product2, store=self.woolworths_store, store_product_id='ww2', is_active=True)
        # Inactive Woolworths product
        PriceFactory(product=self.product3, store=self.woolworths_store, store_product_id='ww3', is_active=False)
        # Duplicate store_product_id for Woolworths (should still be unique in result)
        PriceFactory(product=self.product1, store=self.woolworths_store, store_product_id='ww1', is_active=True)

        # Coles product
        PriceFactory(product=self.product1, store=self.coles_store, store_product_id='coles1', is_active=True)

    def test_get_woolworths_product_store_ids(self):
        product_ids = get_woolworths_product_store_ids()
        self.assertEqual(product_ids, {'ww1', 'ww2'})

    def test_get_woolworths_product_store_ids_no_woolworths_company(self):
        # Delete related prices first
        Price.objects.filter(store=self.woolworths_store).delete()
        # Delete related stores first
        self.woolworths_store.delete()
        # Delete Woolworths company to simulate it not existing
        self.woolworths.delete()
        product_ids = get_woolworths_product_store_ids()
        self.assertEqual(product_ids, set())

    def test_get_woolworths_product_store_ids_no_active_products(self):
        # Update existing Woolworths prices to be inactive
        Price.objects.filter(store=self.woolworths_store).update(is_active=False)
        product_ids = get_woolworths_product_store_ids()
        self.assertEqual(product_ids, set())
