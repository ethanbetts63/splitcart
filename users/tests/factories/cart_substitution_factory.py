import factory
from factory.django import DjangoModelFactory

from products.tests.factories import ProductFactory
from users.models import CartSubstitution
from .cart_item_factory import CartItemFactory


class CartSubstitutionFactory(DjangoModelFactory):
    class Meta:
        model = CartSubstitution

    original_cart_item = factory.SubFactory(CartItemFactory)
    substituted_product = factory.SubFactory(ProductFactory)
    quantity = 1
    is_approved = False
