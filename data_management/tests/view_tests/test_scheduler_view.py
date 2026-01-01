import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from companies.models import Store
from companies.tests.factories import StoreFactory
from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def api_client(monkeypatch):
    """Provides an API client with the necessary internal API key set."""
    API_KEY = "test-internal-api-key"
    monkeypatch.setenv('INTERNAL_API_KEY', API_KEY)
    client = APIClient()
    client.credentials(HTTP_X_INTERNAL_API_KEY=API_KEY)
    return client

@pytest.mark.django_db(transaction=True)
class TestSchedulerView:
    def test_priority_1_unscraped_store_is_selected(self, api_client):
        """
        Tests that a store that has never been scraped is chosen first.
        """
        scraped_store = StoreFactory(last_scraped=timezone.now())
        unscraped_store = StoreFactory(last_scraped=None)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == unscraped_store.pk

    def test_priority_1_selects_lowest_pk_among_unscraped(self, api_client):
        """
        Tests that among multiple unscraped stores, the one with the lowest primary key is chosen.
        """
        # Create stores out of order to ensure pk is the deciding factor
        store3 = StoreFactory(last_scraped=None)
        store2 = StoreFactory(last_scraped=None)
        first_store_created = StoreFactory(last_scraped=None)
        
        # Re-fetch to get assigned PKs
        first_store_created.refresh_from_db()
        store2.refresh_from_db()
        store3.refresh_from_db()
        
        lowest_pk_store = min([first_store_created, store2, store3], key=lambda s: s.pk)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == lowest_pk_store.pk
        
    def test_priority_2_flagged_store_is_selected(self, api_client):
        """
        Tests that a flagged store is chosen over a standard stale store.
        """
        stale_store = StoreFactory(last_scraped=timezone.now() - timedelta(days=10))
        priority_store = StoreFactory(last_scraped=timezone.now() - timedelta(days=5), needs_rescraping=True)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == priority_store.pk

    def test_unscraped_takes_precedence_over_flagged(self, api_client):
        """
        Tests that an unscraped store (Priority 1) is chosen over a flagged store (Priority 2).
        """
        priority_store = StoreFactory(last_scraped=timezone.now() - timedelta(days=5), needs_rescraping=True)
        unscraped_store = StoreFactory(last_scraped=None)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == unscraped_store.pk

    def test_priority_3_oldest_scraped_store_is_selected(self, api_client):
        """
        Tests that the store with the oldest 'last_scraped' timestamp is chosen when no others are available.
        """
        newly_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=1))
        oldest_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=20))
        middle_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=5))

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == oldest_scraped.pk