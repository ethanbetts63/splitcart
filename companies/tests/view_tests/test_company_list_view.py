import pytest
from django.urls import reverse
from companies.tests.factories import CompanyFactory


@pytest.mark.django_db
class TestCompanyListView:
    def test_returns_401_without_api_key(self, client):
        response = client.get(reverse('export-companies'))
        assert response.status_code == 401

    def test_returns_401_with_wrong_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'correct-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='wrong-key')
        assert response.status_code == 401

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_paginated_response_structure(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-companies'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert 'count' in data
        assert 'results' in data
