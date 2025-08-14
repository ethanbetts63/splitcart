from django.test import TestCase
from django.db.utils import IntegrityError
from companies.tests.test_helpers.model_factories import CompanyFactory

class CompanyModelTest(TestCase):

    def test_company_creation(self):
        """Test that a company can be created."""
        company = CompanyFactory()
        self.assertIsNotNone(company.id)
        self.assertIsNotNone(company.name)

    def test_company_str_representation(self):
        """Test the string representation of the company."""
        company = CompanyFactory(name="Test Company")
        self.assertEqual(str(company), "Test Company")

    def test_name_unique_constraint(self):
        """Test that the name field is unique."""
        CompanyFactory(name="Unique Company")
        with self.assertRaises(IntegrityError):
            CompanyFactory(name="Unique Company")
