from django.test import TestCase
from companies.tests.test_helpers.model_factories import CompanyFactory, StoreFactory
from api.utils.management_utils.get_active_stores_for_company import get_active_stores_for_company

class GetActiveStoresForCompanyTest(TestCase):
    def setUp(self):
        self.company1 = CompanyFactory(name='Company A')
        self.company2 = CompanyFactory(name='Company B')

        self.store1_c1 = StoreFactory(company=self.company1, store_name='Store 1 C1', is_active=True)
        self.store2_c1 = StoreFactory(company=self.company1, store_name='Store 2 C1', is_active=False)
        self.store3_c1 = StoreFactory(company=self.company1, store_name='Store 3 C1', is_active=True)
        self.store1_c2 = StoreFactory(company=self.company2, store_name='Store 1 C2', is_active=True)

    def test_get_active_stores_for_company_with_active_stores(self):
        active_stores = get_active_stores_for_company(self.company1)
        self.assertIsNotNone(active_stores)
        self.assertEqual(active_stores.count(), 2)
        self.assertIn(self.store1_c1, active_stores)
        self.assertIn(self.store3_c1, active_stores)
        self.assertNotIn(self.store2_c1, active_stores)

    def test_get_active_stores_for_company_no_active_stores(self):
        company_no_active = CompanyFactory(name='Company C')
        StoreFactory(company=company_no_active, name='Store 1 C3', is_active=False)
        StoreFactory(company=company_no_active, name='Store 2 C3', is_active=False)

        active_stores = get_active_stores_for_company(company_no_active)
        self.assertIsNone(active_stores)

    def test_get_active_stores_for_company_no_stores_at_all(self):
        company_no_stores = CompanyFactory(name='Company D')
        active_stores = get_active_stores_for_company(company_no_stores)
        self.assertIsNone(active_stores)
