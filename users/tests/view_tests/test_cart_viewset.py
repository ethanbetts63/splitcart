"""`/api/carts/` -- who can see and change which cart.

The validation of each custom action's request body lives in
`test_cart_viewset_actions.py`. This file covers the other half: the ownership
boundary. Every route here is reachable by three kinds of caller -- a signed-in
account, a signed-out browser carrying an anonymous ID, and a caller carrying
neither -- and the queryset is the only thing keeping them apart.
"""

import uuid

import pytest
from django.urls import reverse

from users.models import Cart, CartItem
from users.tests.factories import CartFactory, CartItemFactory


def _detail(cart):
    return reverse('cart-detail', kwargs={'pk': str(cart.id)})


@pytest.mark.django_db
class TestCartListing:
    def test_a_user_sees_only_their_own_carts(self, auth_client, user, other_user):
        mine = CartFactory(user=user, name='Mine')
        CartFactory(user=other_user, name='Theirs')

        response = auth_client.get(reverse('cart-list'))

        assert response.status_code == 200, response.content
        ids = [row['id'] for row in response.json()['results']]
        assert ids == [str(mine.id)]

    def test_a_user_does_not_see_anonymous_carts(self, auth_client, user):
        CartFactory(user=None, anonymous_id=str(uuid.uuid4()), is_active=True)

        response = auth_client.get(reverse('cart-list'))

        assert response.json()['results'] == []

    def test_an_anonymous_browser_sees_only_its_own_carts(
        self, anonymous_client, anonymous_id, user
    ):
        mine = CartFactory(user=None, anonymous_id=anonymous_id)
        CartFactory(user=None, anonymous_id=str(uuid.uuid4()))
        CartFactory(user=user)

        response = anonymous_client.get(reverse('cart-list'))

        assert response.status_code == 200, response.content
        ids = [row['id'] for row in response.json()['results']]
        assert ids == [str(mine.id)]

    def test_a_caller_with_no_identity_at_all_sees_nothing(self, api_client, user):
        """The middleware mints a fresh ID per request, so this is a new shopper
        every time -- not a way to read someone else's list."""
        CartFactory(user=user)
        CartFactory(user=None, anonymous_id=str(uuid.uuid4()))

        response = api_client.get(reverse('cart-list'))

        assert response.status_code == 200, response.content
        assert response.json()['results'] == []


@pytest.mark.django_db
class TestCartRetrieval:
    def test_a_user_can_read_their_own_cart(self, auth_client, user):
        cart = CartFactory(user=user, name='Mine')

        response = auth_client.get(_detail(cart))

        assert response.status_code == 200, response.content
        assert response.json()['name'] == 'Mine'

    def test_another_users_cart_is_not_found(self, auth_client, other_user):
        cart = CartFactory(user=other_user)

        assert auth_client.get(_detail(cart)).status_code == 404

    def test_an_anonymous_cart_is_not_readable_by_an_account(self, auth_client):
        cart = CartFactory(user=None, anonymous_id=str(uuid.uuid4()))

        assert auth_client.get(_detail(cart)).status_code == 404

    def test_an_account_cart_is_not_readable_by_an_anonymous_browser(
        self, anonymous_client, user
    ):
        cart = CartFactory(user=user)

        assert anonymous_client.get(_detail(cart)).status_code == 404

    def test_another_browsers_anonymous_cart_is_not_found(self, anonymous_client):
        cart = CartFactory(user=None, anonymous_id=str(uuid.uuid4()))

        assert anonymous_client.get(_detail(cart)).status_code == 404


@pytest.mark.django_db
class TestCartCreation:
    def test_a_new_cart_belongs_to_the_caller_and_becomes_active(
        self, auth_client, user
    ):
        response = auth_client.post(reverse('cart-list'), {}, format='json')

        assert response.status_code == 201, response.content
        cart = Cart.objects.get(pk=response.json()['id'])
        assert cart.user == user
        assert cart.is_active is True

    def test_creating_a_cart_stands_the_previous_one_down(self, auth_client, user):
        previous = CartFactory(user=user, is_active=True)

        auth_client.post(reverse('cart-list'), {}, format='json')

        previous.refresh_from_db()
        assert previous.is_active is False
        assert Cart.objects.filter(user=user, is_active=True).count() == 1

    def test_a_second_cart_gets_a_name_that_does_not_clash(self, auth_client, user):
        """`unique_user_cart_name` is a database constraint, so a repeated
        default name is an IntegrityError rather than a duplicate row."""
        first = auth_client.post(reverse('cart-list'), {}, format='json')
        second = auth_client.post(reverse('cart-list'), {}, format='json')

        assert second.status_code == 201, second.content
        assert first.json()['name'] == 'Shopping List'
        assert second.json()['name'] == 'Shopping List #1'

    def test_an_anonymous_browser_can_create_its_own_cart(
        self, anonymous_client, anonymous_id
    ):
        response = anonymous_client.post(reverse('cart-list'), {}, format='json')

        assert response.status_code == 201, response.content
        cart = Cart.objects.get(pk=response.json()['id'])
        assert cart.user_id is None
        assert cart.anonymous_id == anonymous_id

    def test_a_caller_cannot_choose_which_account_owns_the_cart(
        self, auth_client, user, other_user
    ):
        """`user` is not a writable field, and `perform_create` overrides it."""
        response = auth_client.post(
            reverse('cart-list'), {'user': other_user.pk}, format='json'
        )

        assert response.status_code == 201, response.content
        assert Cart.objects.get(pk=response.json()['id']).user == user


@pytest.mark.django_db
class TestCartDeletion:
    def test_a_user_can_delete_their_own_cart(self, auth_client, user):
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart)

        response = auth_client.delete(_detail(cart))

        assert response.status_code == 204
        assert not Cart.objects.filter(pk=cart.pk).exists()
        assert not CartItem.objects.filter(cart_id=cart.pk).exists()

    def test_another_users_cart_cannot_be_deleted(self, auth_client, other_user):
        cart = CartFactory(user=other_user)

        response = auth_client.delete(_detail(cart))

        assert response.status_code == 404
        assert Cart.objects.filter(pk=cart.pk).exists()

    def test_an_anonymous_browser_cannot_delete_an_account_cart(
        self, anonymous_client, user
    ):
        cart = CartFactory(user=user)

        response = anonymous_client.delete(_detail(cart))

        assert response.status_code == 404
        assert Cart.objects.filter(pk=cart.pk).exists()


@pytest.mark.django_db
class TestActiveCart:
    def test_the_first_call_creates_the_active_cart(self, auth_client, user):
        response = auth_client.get(reverse('cart-active'))

        assert response.status_code == 200, response.content
        assert Cart.objects.get(user=user, is_active=True)

    def test_asking_twice_returns_the_same_cart(self, auth_client):
        first = auth_client.get(reverse('cart-active')).json()['id']
        second = auth_client.get(reverse('cart-active')).json()['id']

        assert first == second
        assert Cart.objects.count() == 1

    def test_an_existing_active_cart_is_returned_with_its_items(
        self, auth_client, user
    ):
        cart = CartFactory(user=user, is_active=True)
        CartItemFactory(cart=cart, quantity=3)

        response = auth_client.get(reverse('cart-active'))

        assert response.json()['id'] == str(cart.id)
        assert [i['quantity'] for i in response.json()['items']] == [3]

    def test_an_inactive_cart_is_not_offered_as_the_active_one(
        self, auth_client, user
    ):
        stale = CartFactory(user=user, is_active=False)

        response = auth_client.get(reverse('cart-active'))

        assert response.json()['id'] != str(stale.id)

    def test_an_anonymous_browser_keeps_one_active_cart(
        self, anonymous_client, anonymous_id
    ):
        first = anonymous_client.get(reverse('cart-active')).json()['id']
        second = anonymous_client.get(reverse('cart-active')).json()['id']

        assert first == second
        cart = Cart.objects.get(pk=first)
        assert cart.anonymous_id == anonymous_id
        assert cart.user_id is None


@pytest.mark.django_db
class TestResponsesAreNotSharedBetweenCallers:
    """One shopper's cart must never be served to another.

    `config.settings` installs Django's whole-site cache middleware
    (`UpdateCacheMiddleware` / `FetchFromCacheMiddleware`). It stores any 200
    answering a GET under a key built from the URL and the response's `Vary`
    headers -- and token authentication never touches the session, so no
    `Vary: Cookie` is ever added. Every caller asking for `/api/carts/active/`
    therefore computed the same cache key.

    These failed before `never_cache` was put on the viewset: the second caller
    was handed the first one's cart, by name and with its contents, for the
    length of the cache timeout.
    """

    def test_two_accounts_do_not_see_each_others_active_cart(
        self, auth_client, user, other_user
    ):
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient

        CartFactory(user=user, is_active=True, name='Mine')
        CartFactory(user=other_user, is_active=True, name='Theirs')
        their_client = APIClient()
        token, _ = Token.objects.get_or_create(user=other_user)
        their_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        mine = auth_client.get(reverse('cart-active'))
        theirs = their_client.get(reverse('cart-active'))

        assert mine.json()['name'] == 'Mine'
        assert theirs.json()['name'] == 'Theirs'

    def test_a_signed_out_browser_does_not_inherit_an_accounts_cart(
        self, auth_client, anonymous_client, user
    ):
        CartFactory(user=user, is_active=True, name='Mine')

        signed_in = auth_client.get(reverse('cart-active')).json()['id']
        signed_out = anonymous_client.get(reverse('cart-active')).json()['id']

        assert signed_in != signed_out

    def test_two_browsers_do_not_share_an_active_cart(
        self, anonymous_client, api_client
    ):
        mine = anonymous_client.get(reverse('cart-active')).json()['id']
        theirs = api_client.get(reverse('cart-active')).json()['id']

        assert mine != theirs

    def test_the_cart_list_is_not_shared_either(
        self, auth_client, user, other_user
    ):
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient

        CartFactory(user=user, name='Mine')
        CartFactory(user=other_user, name='Theirs')
        their_client = APIClient()
        token, _ = Token.objects.get_or_create(user=other_user)
        their_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        auth_client.get(reverse('cart-list'))
        theirs = their_client.get(reverse('cart-list'))

        assert [row['name'] for row in theirs.json()['results']] == ['Theirs']

    def test_the_signed_in_account_endpoint_is_not_shared(
        self, auth_client, user, other_user
    ):
        """`GET /api/auth/user/` answers with the caller's email address."""
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient

        their_client = APIClient()
        token, _ = Token.objects.get_or_create(user=other_user)
        their_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        mine = auth_client.get(reverse('rest_user_details'))
        theirs = their_client.get(reverse('rest_user_details'))

        assert mine.json()['email'] == user.email
        assert theirs.json()['email'] == other_user.email


@pytest.mark.django_db
class TestActionsThatRequireAnAccount:
    """`rename` and `switch-active` are the two actions an anonymous browser may
    not call at all. Both change which of several carts is in play, and a
    signed-out shopper has exactly one."""

    def test_rename_refuses_an_anonymous_browser(self, anonymous_client, user):
        cart = CartFactory(user=user)

        response = anonymous_client.post(
            reverse('cart-rename'),
            {'cart_id': str(cart.id), 'new_name': 'Mine now'},
            format='json',
        )

        assert response.status_code in (401, 403)
        cart.refresh_from_db()
        assert cart.name != 'Mine now'

    def test_switch_active_refuses_an_anonymous_browser(self, anonymous_client, user):
        cart = CartFactory(user=user, is_active=False)

        response = anonymous_client.post(
            reverse('cart-switch-active'), {'cart_id': str(cart.id)}, format='json'
        )

        assert response.status_code in (401, 403)
        cart.refresh_from_db()
        assert cart.is_active is False

    def test_switch_active_cannot_claim_another_users_cart(
        self, auth_client, other_user
    ):
        cart = CartFactory(user=other_user, is_active=False)

        response = auth_client.post(
            reverse('cart-switch-active'), {'cart_id': str(cart.id)}, format='json'
        )

        assert response.status_code == 404
        cart.refresh_from_db()
        assert cart.is_active is False


@pytest.mark.django_db
class TestSyncOwnership:
    def test_sync_writes_only_to_the_callers_cart(self, auth_client, user):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=1)

        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': item.product_id, 'quantity': 5}],
            },
            format='json',
        )

        assert response.status_code == 200, response.content
        item.refresh_from_db()
        assert item.quantity == 5

    def test_sync_removes_lines_the_client_dropped(self, auth_client, user):
        cart = CartFactory(user=user)
        kept = CartItemFactory(cart=cart)
        dropped = CartItemFactory(cart=cart)

        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': kept.product_id, 'quantity': 1}],
            },
            format='json',
        )

        assert response.status_code == 200, response.content
        assert CartItem.objects.filter(pk=kept.pk).exists()
        assert not CartItem.objects.filter(pk=dropped.pk).exists()

    def test_syncing_the_same_body_twice_changes_nothing_the_second_time(
        self, auth_client, user
    ):
        """The client re-sends its whole cart on every change, so a retry after a
        dropped response must not double the rows."""
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=1)
        body = {
            'cart_id': str(cart.id),
            'items': [{'product_id': item.product_id, 'quantity': 2}],
        }

        first = auth_client.post(reverse('cart-sync'), body, format='json')
        second = auth_client.post(reverse('cart-sync'), body, format='json')

        assert first.json()['items'] == second.json()['items']
        assert CartItem.objects.filter(cart=cart).count() == 1

    def test_an_unknown_product_is_rejected_and_nothing_is_written(
        self, auth_client, user
    ):
        cart = CartFactory(user=user)
        existing = CartItemFactory(cart=cart, quantity=1)

        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [
                    {'product_id': existing.product_id, 'quantity': 9},
                    {'product_id': 10**8, 'quantity': 1},
                ],
            },
            format='json',
        )

        assert response.status_code == 400
        existing.refresh_from_db()
        assert existing.quantity == 1

    def test_an_anonymous_browser_cannot_sync_an_account_cart(
        self, anonymous_client, user
    ):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=1)

        response = anonymous_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': item.product_id, 'quantity': 99}],
            },
            format='json',
        )

        assert response.status_code == 400
        item.refresh_from_db()
        assert item.quantity == 1


@pytest.mark.django_db
class TestOptimizeOwnership:
    def test_optimizing_another_users_cart_is_not_found(self, auth_client, other_user):
        cart = CartFactory(user=other_user)

        response = auth_client.post(
            reverse('cart-optimize', kwargs={'pk': str(cart.id)}), {}, format='json'
        )

        assert response.status_code == 404

    def test_optimizing_an_anonymous_cart_from_an_account_is_not_found(
        self, auth_client
    ):
        cart = CartFactory(user=None, anonymous_id=str(uuid.uuid4()))

        response = auth_client.post(
            reverse('cart-optimize', kwargs={'pk': str(cart.id)}), {}, format='json'
        )

        assert response.status_code == 404
