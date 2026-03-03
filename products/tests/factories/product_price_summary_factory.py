import factory
from factory.django import DjangoModelFactory
from products.models import ProductPriceSummary
from .product_factory import ProductFactory


class ProductPriceSummaryFactory(DjangoModelFactory):
    class Meta:
        model = ProductPriceSummary

    product = factory.SubFactory(ProductFactory)
    min_price = factory.LazyAttribute(lambda _: 2.00)
    max_price = factory.LazyAttribute(lambda _: 4.00)
    company_count = 2
    iga_store_count = 0
    best_possible_discount = 50
