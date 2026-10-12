"""`POST /api/token/logout/` and `GET /api/me/` -- the session half of auth.

Both are `freetheplatform.auth`'s views, routed as they come. These are the
assertions splitcart relied on before the move and still relies on: logging out
revokes rather than forgets, and the account endpoint answers only with its
caller's own non-secret facts.
"""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from users.tests.factories import TEST_PASSWORD
from users.tests.sessions import ACCESS_COOKIE, REFRESH_COOKIE, client_for


@pytest.mark.django_db
class TestLoggingOut:
    def test_logging_out_revokes_the_refresh_token_the_caller_held(self, user):
        """Not "the browser forgets it" -- the server stops accepting it."""
        client = client_for(user)
        refresh = client.cookies[REFRESH_COOKIE].value

        response = client.post(reverse('ftp_auth:logout'))

        assert response.status_code == 200, response.content
        assert BlacklistedToken.objects.filter(token__token=refresh).exists()

    def test_a_revoked_refresh_token_no_longer_renews_the_session(self, user):
        """The half that matters to somebody who captured the cookie."""
        client = client_for(user)
        refresh = client.cookies[REFRESH_COOKIE].value
        client.post(reverse('ftp_auth:logout'))

        client.cookies[REFRESH_COOKIE] = refresh
        response = client.post(reverse('ftp_auth:refresh'))

        assert response.status_code == 401, response.content

    def test_logging_out_clears_both_cookies(self, user):
        response = client_for(user).post(reverse('ftp_auth:logout'))

        assert response.cookies[ACCESS_COOKIE].value == ''
        assert response.cookies[REFRESH_COOKIE].value == ''

    def test_logging_out_of_one_account_leaves_the_others_signed_in(self, user, other_user):
        mine = client_for(user)
        theirs = client_for(other_user)

        mine.post(reverse('ftp_auth:logout'))

        assert theirs.get(reverse('ftp_auth:profile')).status_code == 200

    def test_logging_out_without_a_session_is_not_an_error(self, api_client):
        """A browser whose cookies already expired still posts here on sign-out."""
        response = api_client.post(reverse('ftp_auth:logout'))

        assert response.status_code == 200, response.content

    def test_signing_someone_out_is_not_something_a_link_can_do(self, user):
        """A GET logout is a session ended by an `<img>` tag on any page."""
        client = client_for(user)

        response = client.get(reverse('ftp_auth:logout'))

        assert response.status_code == 405, response.content
        assert client.get(reverse('ftp_auth:profile')).status_code == 200


@pytest.mark.django_db
class TestTheAccountEndpoint:
    """`GET /api/me/` is how the frontend asks who it is signed in as."""

    def test_a_signed_out_browser_is_refused(self, api_client):
        response = api_client.get(reverse('ftp_auth:profile'))

        assert response.status_code == 401, response.content

    def test_it_answers_with_the_callers_own_address(self, user):
        response = client_for(user).get(reverse('ftp_auth:profile'))

        assert response.status_code == 200, response.content
        assert response.json()['email'] == user.email

    def test_it_does_not_hand_back_anything_secret(self, user):
        body = client_for(user).get(reverse('ftp_auth:profile')).json()

        assert not any('password' in key and key != 'must_change_password' for key in body)
        assert 'is_staff' not in body

    def test_nothing_can_be_written_through_it(self, api_client, user):
        """The address is the account name and the unique key; the password is
        the credential. Neither may change on this route."""
        client = client_for(user)
        original = user.email

        for method in (client.patch, client.put, client.post):
            response = method(
                reverse('ftp_auth:profile'),
                {'email': 'somebody-elses@example.com', 'password': 'hunter2'},
                format='json',
            )
            assert response.status_code == 405, response.content

        user.refresh_from_db()
        assert user.email == original
        assert user.check_password(TEST_PASSWORD)
