import pytest
from django.db import IntegrityError
from companies.models import Division
from companies.tests.factories import CompanyFactory, DivisionFactory


@pytest.mark.django_db
class TestDivisionModel:
    def test_str_returns_name_and_company(self):
        company = CompanyFactory(name='Coles')
        division = DivisionFactory(name='Coles Supermarkets', company=company)
        assert str(division) == 'Coles Supermarkets (Coles)'

    def test_name_unique_within_company(self):
        company = CompanyFactory()
        Division.objects.create(name='Metro', company=company)
        with pytest.raises(IntegrityError):
            Division.objects.create(name='Metro', company=company)

    def test_same_name_allowed_in_different_companies(self):
        company_a = CompanyFactory()
        company_b = CompanyFactory()
        Division.objects.create(name='Metro', company=company_a)
        Division.objects.create(name='Metro', company=company_b)  # should not raise

    def test_external_id_uniqueness_enforced(self):
        company = CompanyFactory()
        Division.objects.create(name='Division A', company=company, external_id='unique-ext-id')
        with pytest.raises(IntegrityError):
            Division.objects.create(name='Division B', company=company, external_id='unique-ext-id')

    def test_external_id_nullable(self):
        company = CompanyFactory()
        division = Division.objects.create(name='No External ID', company=company)
        assert division.external_id is None

    def test_store_finder_id_nullable(self):
        company = CompanyFactory()
        division = Division.objects.create(name='No Finder ID', company=company)
        assert division.store_finder_id is None
