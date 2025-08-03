from django.test import TestCase
from django.db.utils import IntegrityError
from companies.tests.test_helpers.model_factories import StoreFactory

class StoreModelTest(TestCase):

    def test_store_creation(self):
        store = StoreFactory()
        self.assertIsNotNone(store.id)
        self.assertIsNotNone(store.name)
        self.assertIsNotNone(store.base_url)

    def test_store_str_representation(self):
        store = StoreFactory(name="Test Store")
        self.assertEqual(str(store), "Test Store")

    def test_name_is_unique(self):
        StoreFactory(name="Unique Store")
        with self.assertRaises(IntegrityError):
            StoreFactory(name="Unique Store")
