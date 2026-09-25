"""Validation regressions for `CartViewSet`'s custom actions.

Every one of these actions used to read `request.data.get(...)` straight into a
model field or a bulk write. `rename` assigned `cart.name` with no check of any
kind, and a `cart_id` that was not a UUID reached the ORM as a raw string.
"""

import uuid

import pytest
from django.urls import reverse
from rest_framework.response import Response

from users.models import Cart
from users.serializers.cart_action_serializers import (
    CART_NAME_MAX_LENGTH,
    MAX_ITEM_QUANTITY,
    MAX_SYNC_ITEMS,
)
from users.tests.factories import CartFactory, CartItemFactory


@pytest.mark.django_db
class TestCartRename:
    def test_renames_a_cart(self, auth_client, user):
        cart = CartFactory(user=user, name='Before')
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': str(cart.id), 'new_name': 'After'},
            format='json',
        )
        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.name == 'After'

    def test_name_at_the_column_width_is_accepted(self, auth_client, user):
        cart = CartFactory(user=user)
        name = 'n' * CART_NAME_MAX_LENGTH
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': str(cart.id), 'new_name': name},
            format='json',
        )
        assert response.status_code == 200, response.content
        cart.refresh_from_db()
        assert cart.name == name

    def test_over_long_name_is_rejected_and_nothing_is_written(self, auth_client, user):
        cart = CartFactory(user=user, name='Before')
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': str(cart.id), 'new_name': 'n' * (CART_NAME_MAX_LENGTH + 1)},
            format='json',
        )
        assert response.status_code == 400
        assert 'new_name' in response.json()['errors']
        cart.refresh_from_db()
        assert cart.name == 'Before'

    def test_blank_name_is_rejected(self, auth_client, user):
        cart = CartFactory(user=user, name='Before')
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': str(cart.id), 'new_name': '   '},
            format='json',
        )
        assert response.status_code == 400
        cart.refresh_from_db()
        assert cart.name == 'Before'

    def test_missing_fields_keep_the_error_key_callers_read(self, auth_client):
        response = auth_client.post(reverse('cart-rename'), {}, format='json')
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_malformed_cart_id_is_a_400_not_a_500(self, auth_client):
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': 'not-a-uuid', 'new_name': 'After'},
            format='json',
        )
        assert response.status_code == 400
        assert 'cart_id' in response.json()['errors']

    def test_cannot_rename_another_users_cart(self, auth_client):
        other = CartFactory(name='Theirs')
        response = auth_client.post(
            reverse('cart-rename'),
            {'cart_id': str(other.id), 'new_name': 'Mine now'},
            format='json',
        )
        assert response.status_code == 404
        other.refresh_from_db()
        assert other.name == 'Theirs'


@pytest.mark.django_db
class TestCartSwitchActive:
    def test_switches_the_active_cart(self, auth_client, user):
        active = CartFactory(user=user, is_active=True)
        other = CartFactory(user=user, is_active=False)
        response = auth_client.post(
            reverse('cart-switch-active'), {'cart_id': str(other.id)}, format='json'
        )
        assert response.status_code == 200, response.content
        assert Cart.objects.get(pk=other.pk).is_active is True
        assert Cart.objects.get(pk=active.pk).is_active is False

    def test_missing_cart_id_is_rejected(self, auth_client):
        response = auth_client.post(reverse('cart-switch-active'), {}, format='json')
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_malformed_cart_id_is_a_400_not_a_500(self, auth_client):
        response = auth_client.post(
            reverse('cart-switch-active'), {'cart_id': 'not-a-uuid'}, format='json'
        )
        assert response.status_code == 400

    def test_unknown_cart_id_is_a_404(self, auth_client):
        response = auth_client.post(
            reverse('cart-switch-active'), {'cart_id': str(uuid.uuid4())}, format='json'
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestCartSync:
    def test_syncs_quantities(self, auth_client, user):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=1)
        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': item.product_id, 'quantity': 3}],
            },
            format='json',
        )
        assert response.status_code == 200, response.content
        item.refresh_from_db()
        assert item.quantity == 3

    def test_items_must_be_a_list(self, auth_client, user):
        cart = CartFactory(user=user)
        response = auth_client.post(
            reverse('cart-sync'),
            {'cart_id': str(cart.id), 'items': 'everything'},
            format='json',
        )
        assert response.status_code == 400
        assert 'items' in response.json()['errors']

    def test_quantity_must_be_a_positive_integer(self, auth_client, user):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=2)
        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': item.product_id, 'quantity': 0}],
            },
            format='json',
        )
        assert response.status_code == 400
        item.refresh_from_db()
        assert item.quantity == 2

    def test_quantity_is_bounded_above(self, auth_client, user):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=2)
        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [
                    {'product_id': item.product_id, 'quantity': MAX_ITEM_QUANTITY + 1}
                ],
            },
            format='json',
        )
        assert response.status_code == 400
        item.refresh_from_db()
        assert item.quantity == 2

    def test_quantity_of_the_wrong_type_is_rejected(self, auth_client, user):
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, quantity=2)
        response = auth_client.post(
            reverse('cart-sync'),
            {
                'cart_id': str(cart.id),
                'items': [{'product_id': item.product_id, 'quantity': 'three'}],
            },
            format='json',
        )
        assert response.status_code == 400
        item.refresh_from_db()
        assert item.quantity == 2

    def test_missing_product_id_is_rejected(self, auth_client, user):
        cart = CartFactory(user=user)
        response = auth_client.post(
            reverse('cart-sync'),
            {'cart_id': str(cart.id), 'items': [{'quantity': 1}]},
            format='json',
        )
        assert response.status_code == 400

    def test_item_list_is_bounded(self, auth_client, user):
        cart = CartFactory(user=user)
        items = [
            {'product_id': n + 1, 'quantity': 1} for n in range(MAX_SYNC_ITEMS + 1)
        ]
        response = auth_client.post(
            reverse('cart-sync'),
            {'cart_id': str(cart.id), 'items': items},
            format='json',
        )
        assert response.status_code == 400
        assert 'items' in response.json()['errors']

    def test_missing_cart_id_is_rejected(self, auth_client):
        response = auth_client.post(
            reverse('cart-sync'), {'items': []}, format='json'
        )
        assert response.status_code == 400
        assert 'cart_id' in response.json()['errors']

    def test_cannot_sync_another_users_cart(self, auth_client):
        other = CartFactory()
        response = auth_client.post(
            reverse('cart-sync'),
            {'cart_id': str(other.id), 'items': []},
            format='json',
        )
        assert response.status_code == 400
        assert 'cart_id' in response.json()


@pytest.mark.django_db
class TestCartOptimize:
    def test_options_must_be_a_list_of_integers(self, auth_client, user):
        cart = CartFactory(user=user)
        response = auth_client.post(
            reverse('cart-optimize', kwargs={'pk': str(cart.id)}),
            {'max_companies_options': 'all of them'},
            format='json',
        )
        assert response.status_code == 400
        assert 'max_companies_options' in response.json()['errors']

    def test_option_count_is_bounded(self, auth_client, user):
        cart = CartFactory(user=user)
        response = auth_client.post(
            reverse('cart-optimize', kwargs={'pk': str(cart.id)}),
            {'max_companies_options': list(range(1, 40))},
            format='json',
        )
        assert response.status_code == 400

    def test_empty_body_uses_the_default_options(self, auth_client, user, monkeypatch):
        """The field is optional, and its default has to reach the optimiser."""
        cart = CartFactory(user=user)
        seen = {}

        def fake_optimization(cart_obj, max_company_options):
            seen['options'] = max_company_options
            return Response({'ok': True})

        monkeypatch.setattr(
            'users.views.cart_viewset.run_cart_optimization', fake_optimization
        )
        response = auth_client.post(
            reverse('cart-optimize', kwargs={'pk': str(cart.id)}), {}, format='json'
        )
        assert response.status_code == 200, response.content
        assert seen['options'] == [2, 3, 4]
