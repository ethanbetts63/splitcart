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


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSchedulerView:
    """
    Uses transaction=True + reset_sequences=True so each test gets a fully
    flushed database with pk sequences reset to 1, preventing any cross-test
    contamination from the scheduler view's store.save() call.
    """

    def test_priority_1_unscraped_store_is_selected(self, api_client):
        scraped_store = StoreFactory(last_scraped=timezone.now())
        unscraped_store = StoreFactory(last_scraped=None)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == unscraped_store.pk

    def test_priority_2_flagged_store_is_selected(self, api_client):
        """A flagged store is chosen over a standard stale store."""
        stale_store = StoreFactory(last_scraped=timezone.now() - timedelta(days=10))
        priority_store = StoreFactory(
            last_scraped=timezone.now() - timedelta(days=5),
            needs_rescraping=True,
        )

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == priority_store.pk

    def test_unscraped_takes_precedence_over_flagged(self, api_client):
        """An unscraped store (Priority 1) is chosen over a flagged store (Priority 2)."""
        priority_store = StoreFactory(
            last_scraped=timezone.now() - timedelta(days=5),
            needs_rescraping=True,
        )
        unscraped_store = StoreFactory(last_scraped=None)

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == unscraped_store.pk

    def test_priority_3_oldest_scraped_store_is_selected(self, api_client):
        """The store with the oldest last_scraped timestamp is chosen when no others are available."""
        newly_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=1))
        oldest_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=20))
        middle_scraped = StoreFactory(last_scraped=timezone.now() - timedelta(days=5))

        url = reverse('scheduler-next-candidate')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['pk'] == oldest_scraped.pk
