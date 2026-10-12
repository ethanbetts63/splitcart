"""The cart survives signing in -- by either door, through the URL only.

There are two ways into an account and both have to keep the cart the browser
already filled: `users.views.auth_views.LoginView`, in front of the shared
package's login, and `RegisterView`. The merge has already been lost once by
exactly this route -- it hung off login alone, so signing up silently dropped
the cart -- and it survived the move off dj-rest-auth because this file names
no serializer, method or module.

`view_tests/test_login.py` and `serializer_tests/test_register_serializer.py`
cover each door. `util_tests/test_session_merger.py` covers the merge as a
function. What neither layer can say is that **the two doors agree**, which is
the property that failed last time. So this file drives both through
`reverse()` and asserts against the HTTP answer and the database.

The end-to-end assertion is the first one: fill a cart signed out, go through a
door, and ask `GET /api/carts/active/` with the cookies that door set. That is
the sentence the product actually promises.

A property worth stating rather than asserting: the anonymous ID is a bearer
identifier. Whoever presents it gets the cart it names, and the cart is moved
rather than copied, so presenting somebody else's takes it from them. There is
no binding between the ID and the browser that minted it, it is delivered in a
JS-readable cookie (`config.middleware.AnonymousUserMiddleware` sets
`httponly=False`), and it is accepted from an `X-Anonymous-ID` header with no
check at all. That is a design property of the current model, recorded in the
convergence plan, and not something to freeze in an assertion. What is asserted
below is the boundary that must hold either way: a cart under a *different* ID
is not touched.
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.models import Cart
from users.tests.factories import CartFactory, CartItemFactory, TEST_PASSWORD, UserFactory

EMAIL = 'returning-shopper@example.com'


class _Login:
    """The shopper already has an account."""

    name = 'login'
    accepted = 200

    def __init__(self, client):
        self.client = client
        UserFactory(email=EMAIL)

    def enter(self, **extra):
        payload = {'email': EMAIL, 'password': TEST_PASSWORD}
        payload.update(extra)
        return self.client.post(reverse('login'), payload, format='json')


class _Registration:
    """The shopper is creating one."""

    name = 'registration'
    accepted = 201

    def __init__(self, client):
        self.client = client

    def enter(self, **extra):
        payload = {
            'email': EMAIL,
            'full_name': 'Returning Shopper',
            'password1': TEST_PASSWORD,
            'password2': TEST_PASSWORD,
        }
        payload.update(extra)
        return self.client.post(reverse('register'), payload, format='json')


@pytest.fixture(params=[_Login, _Registration], ids=['login', 'registration'])
def door(request, api_client, db):
    """One of the two ways a shopper becomes signed in."""
    return request.param(api_client)


def _account():
    return get_user_model().objects.get(email=EMAIL)


@pytest.fixture
def signed_out_cart(db):
    """A cart a browser filled before it had an account."""
    anonymous_id = str(uuid.uuid4())
    cart = CartFactory(
        user=None, anonymous_id=anonymous_id, is_active=True, name='Anonymous Cart'
    )
    CartItemFactory(cart=cart, quantity=3)
    return cart


@pytest.mark.django_db
class TestTheCartFollowsTheShopper:
    def test_the_cart_built_signed_out_is_the_one_the_account_opens_with(
        self, api_client, door, signed_out_cart
    ):
        """The whole promise, stated end to end: fill a cart signed out, go in,
        and ask the account what its cart is."""
        item = signed_out_cart.items.get()

        response = door.enter(anonymous_id=signed_out_cart.anonymous_id)
        assert response.status_code == door.accepted, response.content

        # The door set the session cookies on this client; nothing is copied
        # out of the body, because nothing is in it.
        active = api_client.get(reverse('cart-active'))

        assert active.status_code == 200, active.content
        assert [
            (line['product']['id'], line['quantity']) for line in active.json()['items']
        ] == [(item.product_id, 3)]

    def test_the_signed_out_cart_is_not_left_behind_under_the_old_identifier(
        self, door, signed_out_cart
    ):
        """It moves, it is not copied. A shopper who signs out again must not
        find a second copy of the same list waiting."""
        response = door.enter(anonymous_id=signed_out_cart.anonymous_id)
        assert response.status_code == door.accepted, response.content

        assert not Cart.objects.filter(pk=signed_out_cart.pk).exists()
        assert not Cart.objects.filter(
            anonymous_id=signed_out_cart.anonymous_id
        ).exists()

    def test_the_account_is_left_with_exactly_one_active_cart(
        self, door, signed_out_cart
    ):
        """`unique_active_user_cart` is a database constraint. Two active carts
        is not a confusing screen, it is the next write failing."""
        response = door.enter(anonymous_id=signed_out_cart.anonymous_id)
        assert response.status_code == door.accepted, response.content

        assert Cart.objects.filter(user=_account(), is_active=True).count() == 1

    def test_going_in_without_an_identifier_does_not_invent_a_cart(self, door):
        """A shopper with nothing in the cart gets nothing, at both doors. The
        cart is created on first use by `GET /api/carts/active/`, not here."""
        response = door.enter()
        assert response.status_code == door.accepted, response.content

        assert not Cart.objects.filter(user=_account()).exists()

    def test_an_identifier_naming_no_cart_does_not_hold_the_door_shut(self, door):
        """The browser's stored ID outlives the cart it once named. Signing in
        has to work anyway; this used to be a 500."""
        response = door.enter(anonymous_id=str(uuid.uuid4()))

        assert response.status_code == door.accepted, response.content

    def test_a_malformed_identifier_is_a_400_not_a_500(self, door):
        response = door.enter(anonymous_id='not-a-uuid')

        assert response.status_code == 400, response.content
        assert 'anonymous_id' in response.json()


@pytest.mark.django_db
class TestTheBoundaryBetweenBrowsers:
    def test_a_cart_under_a_different_identifier_is_not_touched(
        self, door, signed_out_cart
    ):
        """The ID is the only thing separating one signed-out shopper from
        another, so signing in must reach exactly the one cart it names."""
        someone_else = CartFactory(
            user=None,
            anonymous_id=str(uuid.uuid4()),
            is_active=True,
            name='Anonymous Cart',
        )
        CartItemFactory(cart=someone_else)

        response = door.enter(anonymous_id=signed_out_cart.anonymous_id)
        assert response.status_code == door.accepted, response.content

        someone_else.refresh_from_db()
        assert someone_else.user_id is None
        assert someone_else.is_active is True
        assert someone_else.items.count() == 1


@pytest.mark.django_db
class TestTheTwoDoorsAgree:
    """The asymmetry that has already cost this product a cart once."""

    def test_an_identifier_in_a_different_letter_case_still_finds_the_cart(
        self, door, signed_out_cart
    ):
        """A UUID is the same UUID in either case, and both doors declare the
        field as a `UUIDField`, so both accept the upper-case spelling.

        Login used to read the raw string as posted while registration read the
        validated value, so only registration then found the cart. Both now pass
        the merger the canonical `uuid.UUID`, and this holds them to it.
        """
        response = door.enter(anonymous_id=signed_out_cart.anonymous_id.upper())
        assert response.status_code == door.accepted, response.content

        assert Cart.objects.filter(user=_account(), is_active=True).exists()
        assert not Cart.objects.filter(pk=signed_out_cart.pk).exists()
