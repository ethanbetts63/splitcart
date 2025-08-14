from django.test import TestCase
from django.db.utils import IntegrityError
from companies.models import Store
from companies.tests.test_helpers.model_factories import StoreFactory, CompanyFactory

class StoreModelTest(TestCase):

    def test_store_creation(self):
        """Test that a store can be created."""
        store = StoreFactory()
        self.assertIsNotNone(store.id)
        self.assertIsNotNone(store.name)
        self.assertIsNotNone(store.company)
        self.assertIsNotNone(store.store_id)

    def test_store_str_representation(self):
        """Test the string representation of the store."""
        company = CompanyFactory(name="Test Company")
        store = StoreFactory(name="Test Store", company=company)
        self.assertEqual(str(store), "Test Store (Test Company)")

    def test_unique_together_constraint(self):
        """Test that company and store_id are unique together."""
        company = CompanyFactory()
        store_id = "12345"
        StoreFactory(company=company, store_id=store_id)
        with self.assertRaises(IntegrityError):
            StoreFactory(company=company, store_id=store_id)

    def test_default_values(self):
        """Test the default value of is_active."""
        store = StoreFactory()
        self.assertTrue(store.is_active)

    def test_nullable_and_blankable_fields(self):
        """Test that nullable and blankable fields can be saved as None or empty."""
        store = StoreFactory(
            division=None,
            phone_number="",
            latitude=None,
            longitude=None,
            trading_hours=None,
            is_trading=None
        )
        self.assertIsNone(store.division)
        self.assertEqual(store.phone_number, "")
        self.assertIsNone(store.latitude)
        self.assertIsNone(store.longitude)
        self.assertIsNone(store.trading_hours)
        self.assertIsNone(store.is_trading)