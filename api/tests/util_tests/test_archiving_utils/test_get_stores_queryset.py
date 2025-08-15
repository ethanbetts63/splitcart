
from django.test import TestCase
from api.utils.archiving_utils.get_stores_queryset import get_stores_queryset
from companies.tests.test_helpers.model_factories import StoreFactory, CompanyFactory

class GetStoresQuerysetTest(TestCase):
    def test_get_stores_queryset_no_filter(self):
        company = CompanyFactory(name='Test Company')
        store1 = StoreFactory(company=company, is_active=True)
        store2 = StoreFactory(company=company, is_active=True)
        StoreFactory(is_active=False)  # Inactive store

        queryset = get_stores_queryset()

        self.assertEqual(queryset.count(), 2)
        self.assertIn(store1, queryset)
        self.assertIn(store2, queryset)

    def test_get_stores_queryset_with_company_slug_filter(self):
        company1 = CompanyFactory(name='CompanyA')
        company2 = CompanyFactory(name='CompanyB')
        store1 = StoreFactory(company=company1, is_active=True)
        StoreFactory(company=company2, is_active=True)

        queryset = get_stores_queryset(company_slug='companya')

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), store1)

    def test_get_stores_queryset_with_store_id_filter(self):
        store1 = StoreFactory(store_id='123', is_active=True)
        StoreFactory(store_id='456', is_active=True)

        queryset = get_stores_queryset(store_id='123')

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), store1)
