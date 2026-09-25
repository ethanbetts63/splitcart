"""Fixtures every app's tests can see.

`_docs/TESTING.md` claimed this file existed for a long time before it did. It
holds the things that would otherwise be copied into each app's own
`conftest.py` and then quietly disagree: a DRF client, a request builder for
serializer context, cache hygiene between tests, and a guard against a
half-built test database.

There is no test-run lock here, unlike freethedesk's. It exists there because
every pytest process in that repository shares one MySQL test database, so a
second run's DROP/CREATE pulls the tables out from under the first. splitcart's
test database is in-memory SQLite (see `settings_test`), created inside the
process that uses it, so concurrent runs cannot reach each other's tables. A
lock would serialise runs for nothing. Running with `SPLITCART_TEST_DB=mysql`
does reintroduce the shared database, and a lock with it -- when someone has
the grant to do that, this is where it goes.
"""

import pytest
from django.core.cache import caches
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate


@pytest.fixture(autouse=True)
def empty_caches():
    """No test inherits another's throttle history or cached page.

    Throttle counters live in the `throttling` cache and the whole-site page
    cache lives in the default one. Neither is touched by the per-test database
    rollback, so without this a test that logs in fails because five earlier
    ones already spent the login rate -- and it fails only in a full run, which
    is the worst way to find out.
    """
    for cache in caches.all(initialized_only=False):
        cache.clear()
    yield
    for cache in caches.all(initialized_only=False):
        cache.clear()


@pytest.fixture
def api_client():
    """A DRF ``APIClient``.

    pytest-django's built-in ``client`` is a plain Django test client, which
    speaks sessions. Every authenticated route here is DRF token auth, so tests
    that need to authenticate need this one.
    """
    return APIClient()


@pytest.fixture
def drf_request_factory():
    """Build an authenticated ``rest_framework.request.Request``.

    Serializers that resolve the current user need a request in their context.
    Building one by hand in every test is repetitive, so this does it once::

        def test_my_serializer(drf_request_factory):
            request = drf_request_factory(user=UserFactory())
            serializer = MySerializer(data={...}, context={'request': request})
    """

    def _build(user=None):
        request = APIRequestFactory().get('/')
        if user is not None:
            force_authenticate(request, user=user)
            request.user = user
        return request

    return _build


@pytest.fixture(scope='session', autouse=True)
def _complete_test_schema(django_db_setup, django_db_blocker):
    """Refuse to run against a half-built test database.

    A run cancelled partway through creation leaves one behind, and the next run
    inherits it: single tests pass because they touch the few tables that exist,
    while the suite fails in hundreds of places that all read like a code
    regression. This turns that into one sentence naming the cause.
    """
    from django.apps import apps
    from django.db import connection

    with django_db_blocker.unblock():
        existing = set(connection.introspection.table_names())

    missing = sorted(
        model._meta.db_table
        for model in apps.get_models()
        if model._meta.managed and model._meta.db_table not in existing
    )
    if missing:
        pytest.exit(
            f'The test database is missing {len(missing)} table(s), starting with '
            f'{missing[0]}. It was most likely left half-built by a cancelled or '
            'concurrent run. Re-run with --create-db.',
            returncode=1,
        )
