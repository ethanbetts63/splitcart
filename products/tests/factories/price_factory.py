import datetime
import factory
from decimal import Decimal
from factory.django import DjangoModelFactory
from products.models import Price
from companies.tests.factories import StoreFactory
from .product_factory import ProductFactory


class PriceFactory(DjangoModelFactory):
    class Meta:
        model = Price

    product = factory.SubFactory(ProductFactory)
    store = factory.SubFactory(StoreFactory)
    scraped_date = factory.LazyFunction(datetime.date.today)
    price = factory.LazyAttribute(lambda _: Decimal('5.00'))
    is_on_special = False
