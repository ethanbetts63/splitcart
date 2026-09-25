"""What `/api/carts/` actually puts on the wire.

The cart serializers are the response contract three frontend screens read, and
they are also the boundary that decides what a shopper is *not* told about their
own row. `user`, `anonymous_id` and `is_active` are all columns on `Cart`, and
none of them is in `fields`.
"""

import pytest

from users.serializers.cart_item_serializer import CartItemSerializer
from users.serializers.cart_serializer import CartSerializer
from users.serializers.cart_substitution_serializer import CartSubstitutionSerializer
from users.tests.factories import (
    CartFactory,
    CartItemFactory,
    CartSubstitutionFactory,
)


@pytest.mark.django_db
class TestCartSerializer:
    def test_it_reports_the_cart_and_its_lines(self, user):
        cart = CartFactory(user=user, name='Weekly shop')
        CartItemFactory(cart=cart, quantity=2)

        data = CartSerializer(cart).data

        assert data['id'] == str(cart.id)
        assert data['name'] == 'Weekly shop'
        assert [line['quantity'] for line in data['items']] == [2]

    def test_it_does_not_report_who_owns_the_cart(self, user):
        """The owner is settled by the queryset, and repeating it in the body
        would put another shopper's anonymous ID one bug away from a response."""
        data = CartSerializer(CartFactory(user=user)).data

        assert 'user' not in data
        assert 'anonymous_id' not in data

    def test_an_empty_cart_reports_an_empty_list_not_null(self, user):
        """The frontend maps over this without a guard."""
        assert CartSerializer(CartFactory(user=user)).data['items'] == []

    def test_the_name_is_writable_and_the_timestamps_are_not(self, user):
        fields = CartSerializer().fields

        assert not fields['name'].read_only
        assert fields['created_at'].read_only
        assert fields['updated_at'].read_only


@pytest.mark.django_db
class TestCartItemSerializer:
    def test_the_line_carries_the_whole_product_not_just_its_id(self, user):
        """The cart screen renders a price per supermarket from this, so a bare
        primary key would cost it one request per line."""
        item = CartItemFactory(cart=CartFactory(user=user))

        data = CartItemSerializer(item).data

        assert data['product']['id'] == item.product.id
        assert data['product']['name'] == item.product.name
        assert 'prices' in data['product']

    def test_substitutes_are_reported_under_the_line_they_replace(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))
        substitution = CartSubstitutionFactory(
            original_cart_item=item, is_approved=True
        )

        data = CartItemSerializer(item).data

        assert [s['id'] for s in data['substitutions']] == [str(substitution.id)]
        assert data['substitutions'][0]['is_approved'] is True

    def test_a_line_with_no_substitutes_reports_an_empty_list(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))

        assert CartItemSerializer(item).data['substitutions'] == []


@pytest.mark.django_db
class TestCartSubstitutionSerializer:
    def test_it_carries_the_substitute_product_and_its_approval(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))
        substitution = CartSubstitutionFactory(
            original_cart_item=item, quantity=2, is_approved=True
        )

        data = CartSubstitutionSerializer(substitution).data

        assert data['substituted_product']['id'] == (
            substitution.substituted_product.id
        )
        assert data['quantity'] == 2
        assert data['is_approved'] is True
        assert data['original_cart_item'] == item.id

    def test_the_substitute_product_is_not_writable(self, user):
        """Which product may stand in for which is decided by the pipeline's
        substitute matching, never by the client."""
        assert CartSubstitutionSerializer().fields['substituted_product'].read_only
