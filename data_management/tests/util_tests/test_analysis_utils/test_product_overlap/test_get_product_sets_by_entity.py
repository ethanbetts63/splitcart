from django.test import TestCase
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory, PriceRecordFactory
from data_management.utils.analysis_utils.product_overlap.get_product_sets_by_entity import get_product_sets_by_entity

class GetProductSetsByEntityTest(TestCase):
    def setUp(self):
        self.company1 = CompanyFactory(name='Company A')
        self.company2 = CompanyFactory(name='Company B')

        self.store1_c1 = StoreFactory(company=self.company1, name='Store 1 C1')
        self.store2_c1 = StoreFactory(company=self.company1, name='Store 2 C1')
        self.store1_c2 = StoreFactory(company=self.company2, name='Store 1 C2')

        self.product1 = ProductFactory()
        self.product2 = ProductFactory()
        self.product3 = ProductFactory()

        PriceFactory(price_record=PriceRecordFactory(product=self.product1), store=self.store1_c1)
        PriceFactory(price_record=PriceRecordFactory(product=self.product1), store=self.store1_c2)
        PriceFactory(price_record=PriceRecordFactory(product=self.product2), store=self.store1_c1)
        PriceFactory(price_record=PriceRecordFactory(product=self.product3), store=self.store2_c1)

    def test_get_product_sets_by_company(self):
        entity_products = get_product_sets_by_entity(entity_type='company')

        self.assertEqual(len(entity_products), 2)
        self.assertEqual(entity_products['Company A'], {self.product1.id, self.product2.id, self.product3.id})
        self.assertEqual(entity_products['Company B'], {self.product1.id})

    def test_get_product_sets_by_store_for_company_a(self):
        entity_products = get_product_sets_by_entity(entity_type='store', company_name='Company A')

        self.assertEqual(len(entity_products), 2)
        self.assertEqual(entity_products['Store 1 C1'], {self.product1.id, self.product2.id})
        self.assertEqual(entity_products['Store 2 C1'], {self.product3.id})

    def test_get_product_sets_by_store_for_company__b(self):
        entity_products = get_product_sets_by_entity(entity_type='store', company_name='Company B')

        self.assertEqual(len(entity_products), 1)
        self.assertEqual(entity_products['Store 1 C2'], {self.product1.id})

    def test_get_product_sets_by_store_no_company(self):
        with self.assertRaises(ValueError):
            get_product_sets_by_entity(entity_type='store')

    def test_get_product_sets_by_store_invalid_company(self):
        entity_products = get_product_sets_by_entity(entity_type='store', company_name='Invalid Company')
        self.assertEqual(len(entity_products), 0)