import factory
from factory.django import DjangoModelFactory
from products.models import Product, Price
from companies.tests.test_helpers.model_factories import StoreFactory, CategoryFactory

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    brand = factory.Faker('company')
    size = factory.Faker('word')
    barcode = factory.Faker('ean')
    category = factory.SubFactory(CategoryFactory)

class PriceFactory(DjangoModelFactory):
    class Meta:
        model = Price

    product = factory.SubFactory(ProductFactory)
    store = factory.SubFactory(StoreFactory)
    store_product_id = factory.Faker('uuid4')
    price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    was_price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    unit_price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    unit_of_measure = factory.Faker('word')
    is_on_special = factory.Faker('boolean')
    is_available = factory.Faker('boolean')
    url = factory.Faker('url')
