"""`POST /api/auth/login/` -- credentials, and the cart that comes with them.

`CustomLoginSerializer` exists for one reason beyond dj-rest-auth's own: it
accepts an `anonymous_id` and hands the signed-out shopper's cart to the account
they just proved they own. `_docs/convergence/auth-migration.md` deletes this
class. These tests say what the replacement has to keep doing; the behaviour
itself is pinned independently in
`users/tests/util_tests/test_session_merger.py`.
"""

import pytest
from django.urls import reverse

from users.models import Cart, CartItem
from users.serializers.bounds import FIELD_MAX
from users.tests.factories import CartFactory, CartItemFactory, TEST_PASSWORD

ANONYMOUS_ID = 'c31b0e44-0000-4000-8000-000000000003'


def _login(api_client, user, **extra):
    payload = {'email': user.email, 'password': TEST_PASSWORD}
    payload.update(extra)
    return api_client.post(reverse('rest_login'), payload, format='json')


@pytest.mark.django_db
class TestLogin:
    def test_correct_credentials_return_a_token(self, api_client, user):
        response = _login(api_client, user)

        assert response.status_code == 200, response.content
        assert response.json()['key']

    def test_a_wrong_password_is_rejected(self, api_client, user):
        response = api_client.post(
            reverse('rest_login'),
            {'email': user.email, 'password': 'not-the-password'},
            format='json',
        )

        assert response.status_code == 400
        assert 'key' not in response.json()

    def test_an_unknown_email_is_rejected(self, api_client):
        response = api_client.post(
            reverse('rest_login'),
            {'email': 'nobody@example.com', 'password': TEST_PASSWORD},
            format='json',
        )

        assert response.status_code == 400

    def test_a_missing_password_is_rejected(self, api_client, user):
        response = api_client.post(
            reverse('rest_login'), {'email': user.email}, format='json'
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestAnonymousCartMergeOnLogin:
    def test_anonymous_cart_merges_into_user_cart_on_login(self, api_client, user):
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        item = CartItemFactory(cart=anon_cart, quantity=2)

        response = _login(api_client, user, anonymous_id=ANONYMOUS_ID)

        assert response.status_code == 200, response.content
        merged = Cart.objects.get(user=user, is_active=True)
        assert [(i.product_id, i.quantity) for i in merged.items.all()] == [
            (item.product_id, 2)
        ]
        assert not Cart.objects.filter(pk=anon_cart.pk).exists()

    def test_logging_in_without_an_anonymous_id_creates_no_cart(self, api_client, user):
        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        response = _login(api_client, user)

        assert response.status_code == 200, response.content
        assert not Cart.objects.filter(user=user).exists()

    def test_an_unknown_anonymous_id_does_not_block_the_login(self, api_client, user):
        response = _login(api_client, user, anonymous_id=ANONYMOUS_ID)

        assert response.status_code == 200, response.content

    def test_a_failed_login_does_not_hand_over_the_cart(self, api_client, user):
        """The merge is a reward for proving the account is yours.

        `validate()` calls the merge after `super().validate()`, so a rejected
        password must never reach it -- otherwise anyone who knows an email
        address can graft a cart of their choosing onto that account.
        """
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        response = api_client.post(
            reverse('rest_login'),
            {
                'email': user.email,
                'password': 'not-the-password',
                'anonymous_id': ANONYMOUS_ID,
            },
            format='json',
        )

        assert response.status_code == 400
        assert not Cart.objects.filter(user=user).exists()
        anon_cart.refresh_from_db()
        assert anon_cart.is_active is True
        assert CartItem.objects.filter(cart=anon_cart).count() == 1

    def test_a_malformed_anonymous_id_is_a_400_not_a_500(self, api_client, user):
        """The field is a `UUIDField`, and the merge reads the raw request body.

        Without the declared field, `Cart.objects.get(anonymous_id=...)` would
        take whatever arrived.
        """
        response = _login(api_client, user, anonymous_id='not-a-uuid')

        assert response.status_code == 400
        assert 'anonymous_id' in response.json()

    def test_a_null_anonymous_id_is_accepted(self, api_client, user):
        """The frontend sends `null` when the browser has no stored ID."""
        response = _login(api_client, user, anonymous_id=None)

        assert response.status_code == 200, response.content


@pytest.mark.django_db
class TestLoginBounds:
    """`/api/auth/login/` is unauthenticated and runs the hasher on request.

    dj-rest-auth leaves `email`, `username` and `password` unbounded, so before
    these ceilings a single anonymous request could hand PBKDF2 a megabyte.
    The bounds come from a field kind, not a number -- see
    `users/serializers/bounds.py`.
    """

    def test_a_password_at_the_ceiling_still_reaches_the_authenticator(
        self, api_client, user
    ):
        """At the limit the request is processed and merely fails to match.

        A 400 naming `password` would mean the bound itself rejected it.
        """
        response = api_client.post(
            reverse('rest_login'),
            {'email': user.email, 'password': 'x' * FIELD_MAX['password']},
            format='json',
        )

        assert response.status_code == 400
        assert 'password' not in response.json()
        assert 'non_field_errors' in response.json()

    def test_a_password_over_the_ceiling_is_refused_before_hashing(
        self, api_client, user
    ):
        response = api_client.post(
            reverse('rest_login'),
            {'email': user.email, 'password': 'x' * (FIELD_MAX['password'] + 1)},
            format='json',
        )

        assert response.status_code == 400
        assert 'password' in response.json()

    def test_an_over_long_email_is_refused(self, api_client):
        local_part = 'e' * (FIELD_MAX['email'] + 1 - len('@example.com'))
        response = api_client.post(
            reverse('rest_login'),
            {'email': f'{local_part}@example.com', 'password': TEST_PASSWORD},
            format='json',
        )

        assert response.status_code == 400
        assert 'email' in response.json()

    def test_an_over_long_username_is_refused(self, api_client):
        """dj-rest-auth's other spelling of the same identifier."""
        response = api_client.post(
            reverse('rest_login'),
            {'username': 'u' * (FIELD_MAX['email'] + 1), 'password': TEST_PASSWORD},
            format='json',
        )

        assert response.status_code == 400
        assert 'username' in response.json()
