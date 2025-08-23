
from django.test import TestCase
from companies.models import Store
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory

class GetOrCreateStoreTest(TestCase):
    def setUp(self):
        self.company = CompanyFactory.create()
        self.division = DivisionFactory.create(company=self.company)
        self.store_data = {
            'store_name': 'Test Store',
            'state': 'NSW',
            'postcode': '2000',
        }

    def test_create_new_store(self):
        self.assertEqual(Store.objects.count(), 0)
        store, created = get_or_create_store(self.company, self.division, "S001", self.store_data)

        self.assertTrue(created)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(store.store_name, 'Test Store')
        self.assertEqual(store.state, 'NSW')

    def test_update_existing_store(self):
        # First, create the store
        get_or_create_store(self.company, self.division, "S001", self.store_data)
        self.assertEqual(Store.objects.count(), 1)

        # Now, update it
        updated_store_data = {
            'store_name': 'Updated Test Store',
            'state': 'VIC',
        }
        store, created = get_or_create_store(self.company, self.division, "S001", updated_store_data)

        self.assertFalse(created)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(store.store_name, 'Updated Test Store')
        self.assertEqual(store.state, 'VIC')
        # Check that the postcode is not overwritten with None
        self.assertEqual(store.postcode, '2000')
