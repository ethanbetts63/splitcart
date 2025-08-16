from django.test import TestCase
from companies.tests.test_helpers.model_factories import CompanyFactory
from api.utils.management_utils.get_company_by_name import get_company_by_name

class GetCompanyByNameTest(TestCase):
    def setUp(self):
        self.company = CompanyFactory(name='Test Company')

    def test_get_company_by_name_exists(self):
        company = get_company_by_name('Test Company')
        self.assertEqual(company, self.company)

    def test_get_company_by_name_does_not_exist(self):
        company = get_company_by_name('Non Existent Company')
        self.assertIsNone(company)
