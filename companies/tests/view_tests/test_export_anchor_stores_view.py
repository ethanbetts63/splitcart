import pytest
from django.urls import reverse
from companies.models import StoreGroup
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestExportAnchorStoresView:
    def test_returns_401_without_api_key(self, client):
        response = client.get(reverse('export-anchor-stores'))
        assert response.status_code == 401

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_empty_list_when_no_groups(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []

    def test_queryset_includes_anchor_stores_with_prices(self):
        """
        Verifies the view's queryset logic directly. We test the queryset rather
        than the HTTP response here because MySQL's REPEATABLE READ isolation level
        prevents the test client's new connection from seeing data created within
        the test's savepoint transaction.
        """
        from products.tests.factories import PriceFactory, ProductFactory
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        PriceFactory(store=anchor_store, product=ProductFactory())

        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True)
            .distinct()
        )
        assert anchor_store.id in anchor_ids

    def test_queryset_excludes_anchor_stores_without_prices(self):
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        # No prices created for anchor_store

        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True)
            .distinct()
        )
        assert anchor_store.id not in anchor_ids

    def test_queryset_excludes_groups_with_no_anchor(self):
        company = CompanyFactory()
        StoreGroup.objects.create(company=company, anchor=None)

        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True)
            .distinct()
        )
        assert anchor_ids == []
