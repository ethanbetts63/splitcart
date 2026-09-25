import factory
from factory.django import DjangoModelFactory

from users.models import Cart
from .user_factory import UserFactory


class CartFactory(DjangoModelFactory):
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Cart {n}')
    is_active = False
