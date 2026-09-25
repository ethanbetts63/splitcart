import pytest
from django.core.cache import caches
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Throttle counters are process-local and would otherwise leak between tests.

    Without this, a test that posts to a 5/minute endpoint fails depending on
    what ran before it -- which is the kind of order dependence that gets a
    whole file marked flaky and then skipped.
    """
    caches['throttling'].clear()
    yield
    caches['throttling'].clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(db, user):
    """A client authenticated the way the live frontend authenticates."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client
