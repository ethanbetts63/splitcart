import factory
from factory.django import DjangoModelFactory
from products.models import ProductSubstitution
from .product_factory import ProductFactory


class ProductSubstitutionFactory(DjangoModelFactory):
    class Meta:
        model = ProductSubstitution

    product_a = factory.SubFactory(ProductFactory)
    product_b = factory.SubFactory(ProductFactory)
    level = 'LVL3'
    score = 0.85
