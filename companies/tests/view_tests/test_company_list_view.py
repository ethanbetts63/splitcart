import pytest
from django.urls import reverse
from companies.tests.factories import CompanyFactory


@pytest.mark.django_db
class TestCompanyListView:
    def test_returns_403_without_api_key(self, client):
        response = client.get(reverse('export-companies'))
        assert response.status_code == 403

    def test_returns_403_with_wrong_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'correct-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='wrong-key')
        assert response.status_code == 403

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_all_companies(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        CompanyFactory.create_batch(3)
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert len(data) == 3

    def test_response_contains_id_and_name_fields(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        CompanyFactory(name='Coles')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert data[0]['name'] == 'Coles'
        assert 'id' in data[0]

    def test_returns_empty_list_when_no_companies(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []
