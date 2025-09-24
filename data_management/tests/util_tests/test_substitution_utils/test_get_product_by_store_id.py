from django.test import TestCase
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory, PriceRecordFactory
from companies.tests.test_helpers.model_factories import StoreFactory
from data_management.utils.substitution_utils.get_product_by_store_id import get_product_by_store_id

class GetProductByStoreIdTest(TestCase):
    def setUp(self):
        self.store = StoreFactory()
        self.product1 = ProductFactory()
        self.product2 = ProductFactory()
        self.price1 = PriceFactory(price_record=PriceRecordFactory(product=self.product1), store=self.store, sku='prod123', is_active=True)
        self.price2 = PriceFactory(price_record=PriceRecordFactory(product=self.product2), store=self.store, sku='prod456', is_active=True)

    def test_get_product_by_store_id_exists(self):
        product = get_product_by_store_id('prod123')
        self.assertEqual(product, self.product1)

    def test_get_product_by_store_id_not_exists(self):
        product = get_product_by_store_id('nonexistent')
        self.assertIsNone(product)

    def test_get_product_by_store_id_multiple_objects_returned(self):
        # Create another active price for the same sku
        PriceFactory(price_record=PriceRecordFactory(product=self.product1), store=self.store, sku='prod123', is_active=True)
        product = get_product_by_store_id('prod123')
        self.assertIsNone(product)

    def test_get_product_by_store_id_inactive_price(self):
        PriceFactory(price_record=PriceRecordFactory(product=self.product1), store=self.store, sku='prod789', is_active=False)
        product = get_product_by_store_id('prod789')
        self.assertIsNone(product)
