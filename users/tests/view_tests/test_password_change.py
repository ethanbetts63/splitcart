"""`POST /api/password/change/` -- the package's view, held to splitcart's validators.

Both of `security-standard.md` §3's requirements that dj-rest-auth's version
missed now hold, and are asserted below rather than recorded as owed: the
current password is required, and a change ends every other session.
"""

import pytest
from django.urls import reverse

from users.tests.factories import TEST_PASSWORD
from users.tests.sessions import REFRESH_COOKIE, client_for

NEW_PASSWORD = 'plausible-replacement-91'


def _change(client, **extra):
    payload = {'current_password': TEST_PASSWORD, 'new_password': NEW_PASSWORD}
    payload.update(extra)
    return client.post(reverse('ftp_auth:password-change'), payload, format='json')


@pytest.mark.django_db
class TestChangingAPassword:
    def test_a_signed_in_account_can_set_a_new_password(self, auth_client, user):
        response = _change(auth_client)

        assert response.status_code == 200, response.content
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_the_previous_password_stops_opening_the_account(self, api_client, auth_client, user):
        _change(auth_client)

        response = api_client.post(
            reverse('login'), {'email': user.email, 'password': TEST_PASSWORD}, format='json'
        )

        assert response.status_code == 401, response.content

    def test_a_signed_out_browser_cannot_change_anybodys_password(self, api_client, user):
        response = _change(api_client)

        assert response.status_code == 401, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_a_password_too_weak_for_the_validators_is_refused(self, auth_client, user):
        """`AUTH_PASSWORD_VALIDATORS` applies here as well as at registration,
        or the weak password nobody could sign up with is one change away."""
        response = _change(auth_client, new_password='12345678')

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_an_over_long_password_is_refused_before_hashing(self, auth_client, user):
        response = _change(auth_client, new_password='a' * 129)

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)


@pytest.mark.django_db
class TestWhatTheStandardWants:
    def test_changing_a_password_requires_proving_you_know_the_current_one(
        self, auth_client, user
    ):
        """Otherwise a stolen session takes the account rather than reading it."""
        response = _change(auth_client, current_password='not-the-password')

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_changing_a_password_ends_the_sessions_that_preceded_it(self, user):
        elsewhere = client_for(user)
        here = client_for(user)

        _change(here)

        assert elsewhere.post(reverse('ftp_auth:refresh')).status_code == 401

    def test_the_browser_it_was_changed_in_stays_signed_in(self, user):
        here = client_for(user)

        response = _change(here)

        assert response.cookies[REFRESH_COOKIE].value
        assert here.post(reverse('ftp_auth:refresh')).status_code == 200
