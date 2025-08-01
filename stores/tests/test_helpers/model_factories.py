import factory
from factory.django import DjangoModelFactory
from stores.models import Store, Category

class StoreFactory(DjangoModelFactory):
    class Meta:
        model = Store

    name = factory.Faker('company')
    base_url = factory.LazyAttribute(lambda obj: f"https://www.{obj.name.lower().replace(' ', '')}.com.au")

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: f"{obj.name.lower()}-slug")
    store_category_id = factory.Faker('uuid4')
    parent = None
    store = factory.SubFactory(StoreFactory)
