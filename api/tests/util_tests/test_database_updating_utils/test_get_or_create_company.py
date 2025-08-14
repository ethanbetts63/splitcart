from django.test import TestCase
from companies.models import Company
from api.utils.database_updating_utils.get_or_create_company import get_or_create_company

class GetOrCreateCompanyTest(TestCase):

    def test_create_new_company(self):
        """Test that a new company is created if it doesn't exist."""
        company, created = get_or_create_company("New Company")
        self.assertTrue(created)
        self.assertEqual(company.name, "New Company")
        self.assertEqual(Company.objects.count(), 1)

    def test_get_existing_company(self):
        """Test that an existing company is retrieved."""
        Company.objects.create(name="Existing Company")
        company, created = get_or_create_company("Existing Company")
        self.assertFalse(created)
        self.assertEqual(company.name, "Existing Company")
        self.assertEqual(Company.objects.count(), 1)

    def test_get_existing_company_case_insensitive(self):
        """Test that an existing company is retrieved case-insensitively."""
        Company.objects.create(name="CaseInsensitive")
        company, created = get_or_create_company("caseinsensitive")
        self.assertFalse(created)
        self.assertEqual(company.name, "CaseInsensitive")
        self.assertEqual(Company.objects.count(), 1)

    def test_create_company_with_different_case(self):
        """Test that a new company is created with title case if name is different case."""
        company, created = get_or_create_company("another company")
        self.assertTrue(created)
        self.assertEqual(company.name, "Another Company")
        self.assertEqual(Company.objects.count(), 1)
