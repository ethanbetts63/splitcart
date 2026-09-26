"""`POST /api/auth/password/change/` -- routed, throttled, and half-built.

`users/urls.py` shadows dj-rest-auth's view to give it a `password_change`
scope, so the route is real and anyone holding a token may call it. What it
actually does was never checked against
[`security-standard.md`](../../../../freetheplatform/_docs/security-standard.md)
§3, and two of that section's requirements are missing. Both are recorded below
as `xfail(strict=True)` rather than as passing assertions of today's answer:

- **the current password is not required.** dj-rest-auth removes its own
  `old_password` field unless `OLD_PASSWORD_FIELD_ENABLED` is set, and
  `config/settings.py`'s `REST_AUTH` does not set it. A stolen token therefore
  takes the account, rather than merely reading it -- the owner's password is
  replaced without the attacker ever knowing it.
- **the change does not end other sessions.** `LOGOUT_ON_PASSWORD_CHANGE` is
  likewise unset, so every token issued before the change keeps working.
  Changing a password after a suspected compromise does not evict anybody.

Each is one key in `REST_AUTH`, and both arrive by default with
`freetheplatform.auth` -- which is why they are AU-3's to close and not this
row's. `LOGOUT_ON_PASSWORD_CHANGE` in particular cannot land alone: the
frontend stores its token in `localStorage` and would carry on presenting a
revoked one.

The strict marks mean these fail loudly the day the behaviour is fixed, so the
note above has to be removed with it rather than quietly outliving it. The same
device is used in `test_password_reset.py`, for the same reason.
"""

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token

from users.tests.factories import TEST_PASSWORD

NEW_PASSWORD = 'plausible-replacement-91'


@pytest.fixture
def signed_in(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


def _change(client, **extra):
    payload = {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD}
    payload.update(extra)
    return client.post(reverse('rest_password_change'), payload, format='json')


@pytest.mark.django_db
class TestChangingAPassword:
    def test_a_signed_in_account_can_set_a_new_password(self, signed_in, user):
        response = _change(signed_in)

        assert response.status_code == 200, response.content
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_the_previous_password_stops_opening_the_account(
        self, api_client, signed_in, user
    ):
        _change(signed_in)

        api_client.credentials()
        response = api_client.post(
            reverse('rest_login'),
            {'email': user.email, 'password': TEST_PASSWORD},
            format='json',
        )

        assert response.status_code == 400, response.content

    def test_a_signed_out_browser_cannot_change_anybodys_password(
        self, api_client, user
    ):
        response = _change(api_client)

        assert response.status_code == 401, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_a_mismatched_confirmation_leaves_the_password_alone(
        self, signed_in, user
    ):
        response = _change(signed_in, new_password2='something-else-entirely')

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_a_password_too_weak_for_the_validators_is_refused(
        self, signed_in, user
    ):
        """`AUTH_PASSWORD_VALIDATORS` has to apply here as well as at
        registration, or the weak password nobody could sign up with is one
        change away."""
        response = _change(signed_in, new_password1='12345678', new_password2='12345678')

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    def test_an_over_long_password_is_refused_before_hashing(
        self, signed_in, user
    ):
        """Same reason as every other password field on the site: the hasher is
        deliberately expensive, so the length it is handed is a cost bound."""
        enormous = 'a' * 129

        response = _change(signed_in, new_password1=enormous, new_password2=enormous)

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)


@pytest.mark.django_db
class TestWhatTheStandardStillWants:
    """Two requirements of `security-standard.md` §3 that this endpoint does not
    meet. See the module docstring; both are AU-3's."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "REST_AUTH['OLD_PASSWORD_FIELD_ENABLED'] is unset, so dj-rest-auth "
            "drops the old_password field entirely and a stolen token can "
            "replace the account's password without knowing it."
        ),
    )
    def test_changing_a_password_requires_proving_you_know_the_current_one(
        self, signed_in, user
    ):
        response = _change(signed_in)

        assert response.status_code == 400, response.content
        user.refresh_from_db()
        assert user.check_password(TEST_PASSWORD)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "REST_AUTH['LOGOUT_ON_PASSWORD_CHANGE'] is unset, so every token "
            "issued before the change keeps working and a password change "
            "evicts nobody."
        ),
    )
    def test_changing_a_password_ends_the_sessions_that_preceded_it(
        self, signed_in, user
    ):
        stale = Token.objects.get(user=user).key

        _change(signed_in)

        assert not Token.objects.filter(key=stale).exists()
