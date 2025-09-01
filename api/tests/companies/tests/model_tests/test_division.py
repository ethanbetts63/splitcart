from django.test import TestCase
from django.db.utils import IntegrityError
from companies.tests.test_helpers.model_factories import DivisionFactory, CompanyFactory

class DivisionModelTest(TestCase):

    def test_division_creation(self):
        """Test that a division can be created."""
        division = DivisionFactory()
        self.assertIsNotNone(division.id)
        self.assertIsNotNone(division.name)
        self.assertIsNotNone(division.company)

    def test_division_str_representation(self):
        """Test the string representation of the division."""
        company = CompanyFactory(name="Test Company")
        division = DivisionFactory(name="Test Division", company=company)
        self.assertEqual(str(division), "Test Division (Test Company)")

    def test_unique_together_constraint(self):
        """Test that name and company are unique together."""
        company = CompanyFactory()
        DivisionFactory(name="Unique Division", company=company)
        with self.assertRaises(IntegrityError):
            DivisionFactory(name="Unique Division", company=company)

    def test_nullable_fields(self):
        """Test that fields that can be null are correctly handled."""
        division = DivisionFactory(external_id=None, store_finder_id=None)
        self.assertIsNone(division.external_id)
        self.assertIsNone(division.store_finder_id)
