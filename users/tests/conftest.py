"""Fixtures for the `users` suite.

Cache clearing and the bare `api_client` moved to the repository-root
`conftest.py` when the other apps started needing them too; what stays here is
the part that is specific to this app's idea of "signed in".
"""

import uuid

import pytest
from rest_framework.test import APIClient

from users.tests.factories import UserFactory
from users.tests.sessions import client_for


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(db, user):
    """A client authenticated the way the live frontend authenticates."""
    return client_for(user)


@pytest.fixture
def other_user(db):
    """A second account, for the cross-user boundary tests.

    Named for what it is for: every cart route is asked whether this account can
    reach the first one's rows, and a fixture called `user_two` would not say
    why it exists.
    """
    return UserFactory()


@pytest.fixture
def anonymous_id():
    """The ID a signed-out browser carries.

    `config.middleware.AnonymousUserMiddleware` mints one per request when the
    header and cookie are both absent, so a test that wants the *same* shopper
    across two requests has to supply it.
    """
    return str(uuid.uuid4())


@pytest.fixture
def anonymous_client(db, anonymous_id):
    """A signed-out client that keeps one anonymous ID across requests."""
    client = APIClient()
    client.credentials(HTTP_X_ANONYMOUS_ID=anonymous_id)
    return client
