import factory
from factory.django import DjangoModelFactory
from products.models import Product
from .product_brand_factory import ProductBrandFactory


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ('normalized_name_brand_size',)

    name = factory.Sequence(lambda n: f'Product {n}')
    brand = factory.SubFactory(ProductBrandFactory)
    normalized_name_brand_size = factory.Sequence(lambda n: f'product{n}')
    size = '500g'
    sizes = factory.LazyFunction(list)
    brand_name_company_pairs = factory.LazyFunction(list)
