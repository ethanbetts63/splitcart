"""`POST /api/auth/logout/` and `GET /api/auth/user/` -- the session half of auth.

Neither route has a local subclass beyond a throttle scope, which is why
neither had a test: nothing in this repository looked like it owned them. Both
are routed, both are reachable, and
[`_docs/convergence/auth-migration.md`](../../../_docs/convergence/auth-migration.md)
replaces both. These are the assertions the replacement has to keep satisfying.

One correction belongs here, because it is the reason the tests below are
worth their space. The migration plan says logout "does not log out" and that
"the server-side token row is never revoked". The *endpoint* does revoke: the
`Token` row is deleted and the credential is refused on the very next request,
which is asserted below and was verified before this file was written. What
never happens is the call -- `frontend/src/context/AuthContext.tsx` clears
`localStorage` and posts nothing at all. So server-side revocation is existing
backend behaviour the migration must preserve, and the gap is on the frontend
(AU-4), not here.

What remains true of the plan's account: the token has no expiry and is not
rotated on login. Those are deliberately not pinned -- the migration exists to
change them, and a test asserting today's answer would have to be deleted to
land AU-3.
"""

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.tests.factories import TEST_PASSWORD


def _client_for(user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.mark.django_db
class TestLoggingOut:
    def test_logging_out_revokes_the_credential_the_caller_presented(
        self, api_client, user
    ):
        """Not "the client forgets it" -- the server stops accepting it."""
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.post(reverse('rest_logout'))

        assert response.status_code == 200, response.content
        assert not Token.objects.filter(key=token.key).exists()

    def test_a_revoked_credential_no_longer_opens_the_account(
        self, api_client, user
    ):
        """The half that matters to somebody who captured the token."""
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        api_client.post(reverse('rest_logout'))

        response = api_client.get(reverse('rest_user_details'))

        assert response.status_code == 401, response.content

    def test_logging_out_of_one_account_leaves_the_others_signed_in(
        self, user, other_user
    ):
        mine = _client_for(user)
        theirs_token, _ = Token.objects.get_or_create(user=other_user)

        mine.post(reverse('rest_logout'))

        assert Token.objects.filter(key=theirs_token.key).exists()

    def test_logging_out_without_a_credential_is_not_an_error(self, api_client):
        """A browser whose stored token has already been revoked still posts
        here on sign-out. Answering 401 would make an ordinary sign-out look
        like a failure to the caller."""
        response = api_client.post(reverse('rest_logout'))

        assert response.status_code == 200, response.content

    def test_signing_someone_out_is_not_something_a_link_can_do(
        self, api_client, user
    ):
        """A GET logout is a credential revoked by an `<img>` tag on any page
        the shopper visits. It has to be a POST."""
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = api_client.get(reverse('rest_logout'))

        assert response.status_code == 405, response.content
        assert Token.objects.filter(key=token.key).exists()


@pytest.mark.django_db
class TestTheAccountEndpoint:
    """`GET /api/auth/user/` is how a caller asks who it is signed in as."""

    def test_a_signed_out_browser_is_refused(self, api_client):
        response = api_client.get(reverse('rest_user_details'))

        assert response.status_code == 401, response.content

    def test_it_answers_with_the_callers_own_address(self, user):
        response = _client_for(user).get(reverse('rest_user_details'))

        assert response.status_code == 200, response.content
        assert response.json()['email'] == user.email

    def test_it_does_not_hand_back_anything_secret(self, user):
        """Whatever fields the serializer grows, the hash is never one of
        them."""
        body = _client_for(user).get(reverse('rest_user_details')).json()

        assert 'password' not in body
        assert not any('password' in key for key in body)

    def test_the_account_address_cannot_be_changed_through_it(self, user):
        """The address is the account name and the unique key. Taking a new one
        here would let a caller walk onto an address it has not proved it
        holds."""
        client = _client_for(user)
        original = user.email

        response = client.patch(
            reverse('rest_user_details'),
            {'email': 'somebody-elses@example.com'},
            format='json',
        )

        assert response.status_code == 200, response.content
        user.refresh_from_db()
        assert user.email == original

    def test_a_password_the_endpoint_never_accepted_still_works(
        self, api_client, user
    ):
        """Nothing on this route may quietly reset a credential. Stated as a
        login, because that is where the damage would show."""
        _client_for(user).patch(
            reverse('rest_user_details'), {'password': 'hunter2'}, format='json'
        )

        response = api_client.post(
            reverse('rest_login'),
            {'email': user.email, 'password': TEST_PASSWORD},
            format='json',
        )

        assert response.status_code == 200, response.content
