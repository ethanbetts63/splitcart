import factory
from factory.django import DjangoModelFactory
from products.models import ProductBrand


class ProductBrandFactory(DjangoModelFactory):
    class Meta:
        model = ProductBrand
        django_get_or_create = ('normalized_name',)

    name = factory.Faker('company')
    normalized_name = factory.Sequence(lambda n: f'brand{n}')
    name_variations = factory.LazyFunction(list)
    normalized_name_variations = factory.LazyFunction(list)
