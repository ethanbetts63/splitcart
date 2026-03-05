import pytest
from django.urls import reverse
from companies.tests.factories import CompanyFactory, StoreFactory, DivisionFactory


@pytest.mark.django_db
class TestExportStoresView:
    def test_returns_403_without_api_key(self, client):
        response = client.get(reverse('export-stores'))
        assert response.status_code == 403

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_all_stores(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        StoreFactory.create_batch(3)
        response = client.get(reverse('export-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert len(data) == 3

    def test_response_contains_expected_fields(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        StoreFactory()
        response = client.get(reverse('export-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert set(data[0].keys()) == {'id', 'company', 'division', 'latitude', 'longitude'}

    def test_company_field_is_company_name(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        company = CompanyFactory(name='Aldi')
        StoreFactory(company=company)
        response = client.get(reverse('export-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert data[0]['company'] == 'Aldi'

    def test_returns_empty_list_when_no_stores(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []
