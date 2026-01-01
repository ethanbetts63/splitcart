import factory
from factory.django import DjangoModelFactory
from companies.models import Company

class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company
        django_get_or_create = ('name',)

    name = factory.Faker('company')
    image_url_template = factory.LazyAttribute(
        lambda o: f"https://cdn.example.com/{o.name.lower()}/{{sku}}.jpg"
    )
