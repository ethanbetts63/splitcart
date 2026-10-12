"""`POST /api/token/` -- credentials, and the cart that comes with them.

The session is `freetheplatform.auth`'s and its own suite covers cookies,
lockout and the identical failure answer. What splitcart adds in front of it is
in `users/views/auth_views.py`: a bound on the body before anything is hashed,
and the signed-out shopper's cart handed to the account they just proved they
own. The merge itself is pinned in `users/tests/util_tests/test_session_merger.py`.
"""

import pytest
from django.urls import reverse
from freetheplatform.security.bounds import FIELD_MAX

from users.models import Cart, CartItem
from users.tests.factories import CartFactory, CartItemFactory, TEST_PASSWORD
from users.tests.sessions import ACCESS_COOKIE, REFRESH_COOKIE

ANONYMOUS_ID = 'c31b0e44-0000-4000-8000-000000000003'


def _login(api_client, email, password=TEST_PASSWORD, **extra):
    payload = {'email': email, 'password': password}
    payload.update(extra)
    return api_client.post(reverse('login'), payload, format='json')


@pytest.mark.django_db
class TestLogin:
    def test_correct_credentials_set_the_session_cookies(self, api_client, user):
        response = _login(api_client, user.email)

        assert response.status_code == 200, response.content
        assert response.cookies[ACCESS_COOKIE]['httponly']
        assert response.cookies[REFRESH_COOKIE]['httponly']

    def test_no_token_is_ever_in_the_body(self, api_client, user):
        """A token in a response body is one script away from someone else."""
        body = _login(api_client, user.email).json()

        assert body['email'] == user.email
        assert not any('token' in key or key in ('key', 'access', 'refresh') for key in body)

    def test_the_address_is_matched_whatever_its_case(self, api_client, user):
        response = _login(api_client, user.email.upper())

        assert response.status_code == 200, response.content

    def test_a_wrong_password_and_an_unknown_address_answer_alike(self, api_client, user):
        """Two answers would be a way of finding out who has an account."""
        wrong = _login(api_client, user.email, password='not-the-password')
        unknown = _login(api_client, 'nobody@example.com')

        assert wrong.status_code == unknown.status_code == 401
        assert wrong.json() == unknown.json()
        assert ACCESS_COOKIE not in wrong.cookies

    def test_a_missing_password_is_rejected(self, api_client, user):
        response = api_client.post(reverse('login'), {'email': user.email}, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestAnonymousCartMergeOnLogin:
    def test_anonymous_cart_merges_into_user_cart_on_login(self, api_client, user):
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        item = CartItemFactory(cart=anon_cart, quantity=2)

        response = _login(api_client, user.email, anonymous_id=ANONYMOUS_ID)

        assert response.status_code == 200, response.content
        merged = Cart.objects.get(user=user, is_active=True)
        assert [(i.product_id, i.quantity) for i in merged.items.all()] == [
            (item.product_id, 2)
        ]
        assert not Cart.objects.filter(pk=anon_cart.pk).exists()

    def test_logging_in_without_an_anonymous_id_creates_no_cart(self, api_client, user):
        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        response = _login(api_client, user.email)

        assert response.status_code == 200, response.content
        assert not Cart.objects.filter(user=user).exists()

    def test_an_unknown_anonymous_id_does_not_block_the_login(self, api_client, user):
        response = _login(api_client, user.email, anonymous_id=ANONYMOUS_ID)

        assert response.status_code == 200, response.content

    def test_a_failed_login_does_not_hand_over_the_cart(self, api_client, user):
        """The merge is a reward for proving the account is yours.

        Otherwise anyone who knows an email address can graft a cart of their
        choosing onto that account.
        """
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        response = _login(
            api_client, user.email, password='not-the-password', anonymous_id=ANONYMOUS_ID
        )

        assert response.status_code == 401
        assert not Cart.objects.filter(user=user).exists()
        anon_cart.refresh_from_db()
        assert anon_cart.is_active is True
        assert CartItem.objects.filter(cart=anon_cart).count() == 1

    def test_a_merge_that_fails_does_not_refuse_the_login(
        self, api_client, user, monkeypatch
    ):
        """The cart is a convenience; the account is the shopper's. A failed
        merge rolls back and leaves both carts as they were."""
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        def fails(*args, **kwargs):
            raise RuntimeError('the database went away mid-merge')

        monkeypatch.setattr(Cart.objects, 'create', fails)
        response = _login(api_client, user.email, anonymous_id=ANONYMOUS_ID)
        monkeypatch.undo()

        assert response.status_code == 200, response.content
        anon_cart.refresh_from_db()
        assert anon_cart.is_active is True

    def test_a_malformed_anonymous_id_is_a_400_not_a_500(self, api_client, user):
        response = _login(api_client, user.email, anonymous_id='not-a-uuid')

        assert response.status_code == 400
        assert 'anonymous_id' in response.json()

    def test_a_null_anonymous_id_is_accepted(self, api_client, user):
        """The frontend sends `null` when the browser has no stored ID."""
        response = _login(api_client, user.email, anonymous_id=None)

        assert response.status_code == 200, response.content


@pytest.mark.django_db
class TestLoginBounds:
    """Login is unauthenticated and runs the hasher on request, so the body is
    bounded by field kind before the package's view sees it."""

    def test_a_password_at_the_ceiling_still_reaches_the_authenticator(
        self, api_client, user
    ):
        """At the limit the request is processed and merely fails to match."""
        response = _login(api_client, user.email, password='x' * FIELD_MAX['password'])

        assert response.status_code == 401

    def test_a_password_over_the_ceiling_is_refused_before_hashing(self, api_client, user):
        response = _login(api_client, user.email, password='x' * (FIELD_MAX['password'] + 1))

        assert response.status_code == 400
        assert 'password' in response.json()

    def test_an_over_long_email_is_refused(self, api_client):
        local_part = 'e' * (FIELD_MAX['email'] + 1 - len('@example.com'))

        response = _login(api_client, f'{local_part}@example.com')

        assert response.status_code == 400
        assert 'email' in response.json()
