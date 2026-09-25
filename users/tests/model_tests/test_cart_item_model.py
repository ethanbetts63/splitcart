"""`CartItem` and `CartSubstitution` -- one line per product, one swap per line.

Both carry a `unique_together`, and both are written in bulk by
`CartViewSet.sync`, which is the path a duplicate would arrive on.
"""

import pytest
from django.db import IntegrityError, transaction

from users.models import CartItem, CartSubstitution
from users.tests.factories import (
    CartFactory,
    CartItemFactory,
    CartSubstitutionFactory,
)
from products.tests.factories import ProductFactory


@pytest.mark.django_db
class TestCartItem:
    def test_a_product_appears_once_per_cart(self, user):
        cart = CartFactory(user=user)
        product = ProductFactory()
        CartItemFactory(cart=cart, product=product)

        with pytest.raises(IntegrityError), transaction.atomic():
            CartItem.objects.create(cart=cart, product=product, quantity=1)

    def test_the_same_product_may_be_in_two_carts(self, user):
        product = ProductFactory()
        CartItemFactory(cart=CartFactory(user=user, name='A'), product=product)

        assert CartItemFactory(cart=CartFactory(user=user, name='B'), product=product).pk

    def test_quantity_defaults_to_one(self, user):
        cart = CartFactory(user=user)

        item = CartItem.objects.create(cart=cart, product=ProductFactory())

        assert item.quantity == 1

    def test_an_item_describes_itself_by_quantity_product_and_cart(self, user):
        cart = CartFactory(user=user, name='Weekly shop')
        item = CartItemFactory(cart=cart, quantity=2)

        assert str(item) == f'2 x {item.product.name} in Weekly shop'


@pytest.mark.django_db
class TestCartSubstitution:
    def test_one_substitute_per_product_per_line(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))
        substitute = ProductFactory()
        CartSubstitutionFactory(original_cart_item=item, substituted_product=substitute)

        with pytest.raises(IntegrityError), transaction.atomic():
            CartSubstitution.objects.create(
                original_cart_item=item, substituted_product=substitute
            )

    def test_a_line_may_be_offered_several_different_substitutes(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))

        CartSubstitutionFactory(original_cart_item=item)
        CartSubstitutionFactory(original_cart_item=item)

        assert item.chosen_substitutions.count() == 2

    def test_a_substitute_starts_unapproved(self, user):
        """Nothing is swapped into a shopper's cart until they say so."""
        item = CartItemFactory(cart=CartFactory(user=user))

        substitution = CartSubstitution.objects.create(
            original_cart_item=item, substituted_product=ProductFactory()
        )

        assert substitution.is_approved is False

    def test_deleting_the_line_removes_its_substitutes(self, user):
        item = CartItemFactory(cart=CartFactory(user=user))
        CartSubstitutionFactory(original_cart_item=item)

        item.delete()

        assert CartSubstitution.objects.count() == 0

    def test_deleting_the_cart_removes_the_substitutes_too(self, user):
        cart = CartFactory(user=user)
        CartSubstitutionFactory(original_cart_item=CartItemFactory(cart=cart))

        cart.delete()

        assert CartSubstitution.objects.count() == 0
