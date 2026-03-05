import pytest
from companies.serializers.company_serializer import CompanySerializer
from companies.tests.factories import CompanyFactory


@pytest.mark.django_db
class TestCompanySerializer:
    def test_contains_expected_fields(self):
        company = CompanyFactory()
        serializer = CompanySerializer(company)
        assert set(serializer.data.keys()) == {'id', 'name'}

    def test_name_field_value(self):
        company = CompanyFactory(name='Coles')
        serializer = CompanySerializer(company)
        assert serializer.data['name'] == 'Coles'

    def test_id_field_matches_pk(self):
        company = CompanyFactory()
        serializer = CompanySerializer(company)
        assert serializer.data['id'] == company.pk
