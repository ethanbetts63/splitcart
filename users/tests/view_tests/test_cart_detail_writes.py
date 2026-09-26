"""`PUT` and `PATCH /api/carts/<pk>/` -- the two handlers nobody counted.

`CartViewSet` is a `ModelViewSet`, so the router gives `carts/<pk>/` four verbs,
not one. `test_cart_viewset.py` covers `GET` and `DELETE`, and the five
`@action`s have a file each. `PUT` and `PATCH` had nothing: they are the only
operations on the viewset with no override in the class -- no `perform_update`,
no per-action `permission_classes` -- which is exactly why they were read past.
`_docs/convergence/auth-migration.md` counted nine operations where there are
eleven, and these are the two missing.

Nothing in `frontend/src/services/cart.api.ts` calls either. That makes them
less likely to be noticed breaking, not less part of the contract: they are
routed, they write, and they are governed by the same queryset that keeps one
shopper out of another's cart. If the migration changes how a caller is
identified, this is where the breakage would be silent.

The interesting half is what they may *not* change. `CartSerializer` names
`id`, `name`, `items`, `created_at` and `updated_at`, and only `name` is
writable -- so ownership, activeness and the cart's identity cannot be posted.
Those are assertions, not comments, below.
"""

import uuid

import pytest
from django.urls import reverse

from users.models import Cart
from users.tests.factories import CartFactory, CartItemFactory


def _detail(cart):
    return reverse('cart-detail', kwargs={'pk': str(cart.id)})


@pytest.mark.django_db
class TestRenamingThroughTheDetailRoute:
    def test_a_user_can_rename_the_cart_they_own(self, auth_client, user):
        cart = CartFactory(user=user, name='Weekly shop')

        response = auth_client.patch(_detail(cart), {'name': 'Party'}, format='json')

        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.name == 'Party'

    def test_a_replacement_that_names_nothing_does_not_blank_the_name(
        self, auth_client, user
    ):
        """`Cart.name` carries a model default, so the serializer makes it
        optional and a bodiless `PUT` is a no-op rather than a replacement. The
        contract that matters is the one asserted: a cart the shopper can still
        tell apart from every other. Worth pinning because the obvious reading
        of `PUT` is destructive and this one is not."""
        cart = CartFactory(user=user, name='Weekly shop')

        response = auth_client.put(_detail(cart), {}, format='json')

        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.name == 'Weekly shop'

    def test_a_cart_cannot_be_left_with_a_blank_name(self, auth_client, user):
        cart = CartFactory(user=user, name='Weekly shop')

        response = auth_client.patch(_detail(cart), {'name': ''}, format='json')

        assert response.status_code == 400, response.content
        cart.refresh_from_db()
        assert cart.name == 'Weekly shop'

    def test_an_anonymous_browser_can_rename_the_cart_it_owns(
        self, anonymous_client, anonymous_id
    ):
        """Unlike `POST /api/carts/rename/`, which refuses a signed-out browser
        outright. The detail route carries `IsAuthenticatedOrAnonymous`, so a
        signed-out shopper renames its one cart here and not there. Recorded
        because a migration that unified the two would change an answer a
        caller can see."""
        cart = CartFactory(user=None, anonymous_id=anonymous_id, is_active=True)

        response = anonymous_client.patch(
            _detail(cart), {'name': 'My list'}, format='json'
        )

        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.name == 'My list'


@pytest.mark.django_db
class TestWhoMayWriteToACart:
    def test_another_users_cart_cannot_be_written_to(self, auth_client, other_user):
        theirs = CartFactory(user=other_user, name='Theirs')

        response = auth_client.patch(_detail(theirs), {'name': 'Mine'}, format='json')

        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.name == 'Theirs'

    def test_an_anonymous_browser_cannot_write_to_an_account_cart(
        self, anonymous_client, user
    ):
        theirs = CartFactory(user=user, name='Theirs')

        response = anonymous_client.patch(
            _detail(theirs), {'name': 'Mine'}, format='json'
        )

        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.name == 'Theirs'

    def test_another_browsers_cart_cannot_be_written_to(self, anonymous_client):
        theirs = CartFactory(
            user=None, anonymous_id=str(uuid.uuid4()), is_active=True, name='Theirs'
        )

        response = anonymous_client.patch(
            _detail(theirs), {'name': 'Mine'}, format='json'
        )

        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.name == 'Theirs'

    def test_a_malformed_cart_id_in_the_path_is_a_404_not_a_500(self, auth_client):
        response = auth_client.patch(
            reverse('cart-detail', kwargs={'pk': 'not-a-uuid'}),
            {'name': 'Mine'},
            format='json',
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestWhatAWriteMayNotChange:
    """The fields a caller can name in the body but must not be able to move."""

    def test_a_caller_cannot_hand_their_cart_to_another_account(
        self, auth_client, user, other_user
    ):
        cart = CartFactory(user=user, name='Weekly shop')

        response = auth_client.patch(
            _detail(cart), {'name': 'Weekly shop', 'user': other_user.pk}, format='json'
        )

        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.user_id == user.pk

    def test_a_caller_cannot_claim_a_cart_by_posting_an_anonymous_id(
        self, anonymous_client, anonymous_id, user
    ):
        theirs = CartFactory(user=user, name='Theirs')

        response = anonymous_client.patch(
            _detail(theirs), {'name': 'Mine', 'anonymous_id': anonymous_id}, format='json'
        )

        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.user_id == user.pk
        assert theirs.anonymous_id is None

    def test_which_cart_is_active_is_not_settable_here(self, auth_client, user):
        """`switch-active` is the route that does this, and it is the one that
        stands the previous cart down inside a transaction. A write here that
        set `is_active` would leave two active carts and trip the database's
        own `unique_active_user_cart`."""
        active = CartFactory(user=user, name='Active', is_active=True)
        idle = CartFactory(user=user, name='Idle', is_active=False)

        response = auth_client.patch(
            _detail(idle), {'name': 'Idle', 'is_active': True}, format='json'
        )

        assert response.status_code == 200, response.content
        idle.refresh_from_db()
        active.refresh_from_db()
        assert idle.is_active is False
        assert active.is_active is True

    def test_a_cart_cannot_be_given_a_different_id(self, auth_client, user):
        """The id is what the frontend stores and every later call quotes."""
        cart = CartFactory(user=user, name='Weekly shop')
        original = cart.id

        response = auth_client.patch(
            _detail(cart), {'name': 'Weekly shop', 'id': str(uuid.uuid4())}, format='json'
        )

        assert response.status_code == 200, response.content
        assert Cart.objects.get(pk=original).name == 'Weekly shop'

    def test_the_lines_of_a_cart_are_not_rewritable_here(self, auth_client, user):
        """Items move through `sync`, which validates every line and bounds how
        many there may be. A `PATCH` that accepted `items` would be that
        endpoint without any of its checks."""
        cart = CartFactory(user=user, name='Weekly shop')
        item = CartItemFactory(cart=cart, quantity=2)

        response = auth_client.patch(
            _detail(cart),
            {'name': 'Weekly shop', 'items': []},
            format='json',
        )

        assert response.status_code == 200, response.content
        item.refresh_from_db()
        assert item.quantity == 2
        assert cart.items.count() == 1
