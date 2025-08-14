from django.test import TestCase
from companies.models import Division
from companies.tests.test_helpers.model_factories import CompanyFactory
from api.utils.database_updating_utils.get_or_create_division import get_or_create_division

class GetOrCreateDivisionTest(TestCase):

    def test_create_new_division(self):
        """Test that a new division is created if it doesn't exist."""
        company = CompanyFactory()
        division, created = get_or_create_division(company, "New Division", "ext123", "sf456")
        self.assertTrue(created)
        self.assertEqual(division.name, "New Division")
        self.assertEqual(division.company, company)
        self.assertEqual(division.external_id, "ext123")
        self.assertEqual(division.store_finder_id, "sf456")
        self.assertEqual(Division.objects.count(), 1)

    def test_get_existing_division(self):
        """Test that an existing division is retrieved."""
        company = CompanyFactory()
        Division.objects.create(company=company, name="Existing Division", external_id="old_ext", store_finder_id="old_sf")
        division, created = get_or_create_division(company, "Existing Division", "new_ext", "new_sf")
        self.assertFalse(created)
        self.assertEqual(division.name, "Existing Division")
        self.assertEqual(division.company, company)
        self.assertEqual(division.external_id, "old_ext") # Should not be updated
        self.assertEqual(division.store_finder_id, "old_sf") # Should not be updated
        self.assertEqual(Division.objects.count(), 1)

    def test_create_division_without_optional_ids(self):
        """Test creating a division without external_id or store_finder_id."""
        company = CompanyFactory()
        division, created = get_or_create_division(company, "Division No IDs")
        self.assertTrue(created)
        self.assertEqual(division.name, "Division No IDs")
        self.assertIsNone(division.external_id)
        self.assertIsNone(division.store_finder_id)

    def test_get_existing_division_with_different_optional_ids(self):
        """Test retrieving existing division when optional IDs are different in call."""
        company = CompanyFactory()
        Division.objects.create(company=company, name="Existing Div 2", external_id="ext_val", store_finder_id="sf_val")
        division, created = get_or_create_division(company, "Existing Div 2", "different_ext", "different_sf")
        self.assertFalse(created)
        self.assertEqual(division.external_id, "ext_val") # Should remain original
        self.assertEqual(division.store_finder_id, "sf_val") # Should remain original
