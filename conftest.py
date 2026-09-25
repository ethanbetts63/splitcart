"""Fixtures every app's tests can see.

`_docs/TESTING.md` claimed this file existed for a long time before it did. It
holds the things that would otherwise be copied into each app's own
`conftest.py` and then quietly disagree: a DRF client, a request builder for
serializer context, cache hygiene between tests, and a guard against a
half-built test database.

Two of freethedesk's fixtures are deliberately absent, for the same reason.

freethedesk holds an OS lock for the length of a run, because every pytest
process in that repository shares one MySQL test database and a second run's
DROP/CREATE pulls the tables out from under the first. It also refuses to start
against a test database missing tables, because a cancelled run leaves one
behind and the next run inherits it.

Both failure modes need a database that outlives the process. splitcart's is
in-memory SQLite, built inside the process that uses it and gone when it exits
(see `settings_test`), so concurrent runs cannot reach each other's tables and
there is nothing to inherit. A lock would serialise runs for nothing, and a
schema guard would have to be switched off to let `pytest <a file with no
database tests>` run at all -- pytest-django builds no database for a session
whose collected tests never ask for one.

Running with `SPLITCART_TEST_DB=mysql` reintroduces the shared database and
both failure modes with it. When someone has the grant to do that, this is
where freethedesk's two fixtures belong.
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
