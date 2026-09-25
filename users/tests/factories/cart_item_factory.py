import factory
from factory.django import DjangoModelFactory

from products.tests.factories import ProductFactory
from users.models import CartItem
from .cart_factory import CartFactory


class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
